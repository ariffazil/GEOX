"""
geox_seismic_horizon_track.v1 — Seed-based 3D horizon auto-tracker.

Per the GEOX Seismic Interpretation Forge Package Slice 1 Step 5 + Step 7.
Given a 3D seismic amplitude volume + seed points + phase event (peak/trough/zero),
auto-propagate to produce a SurfaceMesh with per-vertex confidence.

The output geometry is what the rest of GEOX consumes:
- This is the bridge that turns "yes for PNG trace" into "yes for SEG-Y track"
- Output SurfaceMesh is registered as geox://artifact/horizon-* artifact

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import Any, Literal

import numpy as np
from scipy.ndimage import gaussian_filter1d

from geox.seismic.attributes import dip as gst_dip_module
from geox.seismic.contracts import SurfaceMesh

logger = logging.getLogger("geox.seismic_horizon_track")

TOOL_NAME = "geox_seismic_horizon_track"


def _find_peak_in_window(
    trace: np.ndarray, center_idx: int, half_window: int, phase_event: str
) -> tuple[int, float]:
    """Find the peak/trough/zero crossing closest to center within the window.

    Returns: (sample_index, confidence) where confidence ∈ [0, 1] is the
    normalized peak amplitude at that sample relative to the trace max.
    """
    n = len(trace)
    lo = max(0, center_idx - half_window)
    hi = min(n, center_idx + half_window + 1)
    if lo >= hi:
        return center_idx, 0.0
    segment = trace[lo:hi]

    if phase_event == "peak":
        idx_local = int(np.argmax(segment))
    elif phase_event == "trough":
        idx_local = int(np.argmin(segment))
    elif phase_event == "zero":
        # Zero crossing: find sign change closest to center
        center_local = center_idx - lo
        for d in range(0, len(segment) - 1):
            for offset in (0, -1, 1, -2, 2):
                j = center_local + offset + d
                if 0 <= j < len(segment) - 1:
                    if segment[j] * segment[j + 1] <= 0:
                        idx_local = j
                        break
            else:
                continue
            break
        else:
            return center_idx, 0.0
    else:
        return center_idx, 0.0

    sample_idx = lo + idx_local
    amplitude = float(trace[sample_idx])
    max_abs = float(np.max(np.abs(trace))) + 1e-12
    confidence = min(1.0, abs(amplitude) / max_abs)
    return sample_idx, confidence


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_horizon_track(
    volume: list[list[list[float]]] | None = None,
    seeds: list[tuple[int, int, int]] | None = None,
    phase_event: Literal["peak", "trough", "zero"] = "peak",
    half_window: int = 10,
    smoothing_sigma: float = 0.0,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Any = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Auto-track a horizon through a 3D seismic volume.

    Parameters
    ----------
    volume : 3D nested list
        Inline-major order: [iline][xline][sample].
    seeds : list of (iline, xline, sample) tuples
        Seed points (≥3 recommended).
    phase_event : str
        "peak" / "trough" / "zero" — what event to track.
    half_window : int
        Half-width of the search window (samples) along the trace.
    smoothing_sigma : float
        Gaussian smoothing sigma along the tracked horizon (samples).

    Returns
    -------
    dict with:
      - status: OK | HOLD
      - data: SurfaceMesh artifact (vertices + faces + confidence + alt_paths + stopped)
      - provenance: parameters + stats
      - claim: null (this is auto-tracking, not a geological claim)
    """
    if volume is None:
        return _envelope(
            status="HOLD",
            error="volume (3D nested list) required; volume_ref path is HOLD per Canon #0",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
    if not seeds or len(seeds) < 1:
        return _envelope(
            status="HOLD",
            error="at least one seed required",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    arr = np.asarray(volume, dtype=np.float64)
    if arr.ndim != 3:
        return _envelope(
            status="HOLD",
            error=f"volume must be 3D, got {arr.ndim}D with shape {arr.shape}",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Optional smoothing on input
    if smoothing_sigma > 0:
        arr_smooth = gaussian_filter1d(arr, sigma=smoothing_sigma, axis=-1)
    else:
        arr_smooth = arr

    # Build tracks per seed column (each seed = one trace column to track)
    # The horizon is a surface, so we need a 2D grid of (x, y) positions with one z each
    n_iline, n_xline, n_sample = arr.shape
    seeds_set = set((s[0], s[1]) for s in seeds)

    # Map (iline, xline) -> sample + confidence
    # Start from seeds; expand to all iline/xline columns via connected-component or sweep
    tracked: dict[tuple[int, int], tuple[int, float]] = {}
    stopped: list[dict[str, Any]] = []

    # First, process seed columns
    for s in seeds:
        i, x, k = int(s[0]), int(s[1]), int(s[2])
        if not (0 <= i < n_iline and 0 <= x < n_xline and 0 <= k < n_sample):
            continue
        trace = arr_smooth[i, x, :]
        sample_idx, conf = _find_peak_in_window(trace, k, half_window, phase_event)
        tracked[(i, x)] = (sample_idx, conf)

    # Expand via nearest-neighbor propagation from seeds to all (i, x) pairs
    # Simple flood-fill: BFS from seed positions
    from collections import deque
    queue = deque(tracked.keys())
    while queue:
        i, x = queue.popleft()
        # Propagate to 4 neighbors (cross-axes only)
        for di, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nx = i + di, x + dx
            if not (0 <= ni < n_iline and 0 <= nx < n_xline):
                continue
            if (ni, nx) in tracked:
                continue
            # Use neighbor's sample as search center
            center_k = tracked[(i, x)][0]
            trace = arr_smooth[ni, nx, :]
            sample_idx, conf = _find_peak_in_window(trace, center_k, half_window, phase_event)
            # If the search failed (no clear peak), mark as stopped
            if conf < 0.05:
                stopped.append({
                    "region": {"iline": ni, "xline": nx},
                    "reason": "low_confidence",
                })
                continue
            tracked[(ni, nx)] = (sample_idx, conf)
            queue.append((ni, nx))

    # Build SurfaceMesh from tracked grid
    vertices_3d = []
    confidence = []
    for (i, x) in sorted(tracked.keys()):
        k, c = tracked[(i, x)]
        vertices_3d.append((float(i), float(x), float(k)))
        confidence.append(float(c))

    if len(vertices_3d) < 3:
        return _envelope(
            status="HOLD",
            error=f"insufficient vertices tracked: {len(vertices_3d)} (need >= 3 for mesh)",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Build faces: triangulate the (i, x) grid via simple row-strip
    # Map (i, x) -> vertex index
    idx_map: dict[tuple[int, int], int] = {(int(v[0]), int(v[1])): i for i, v in enumerate(vertices_3d)}
    faces: list[tuple[int, int, int]] = []
    # Group by iline
    by_iline: dict[int, list[tuple[int, int]]] = {}
    for (i, x) in idx_map.keys():
        by_iline.setdefault(i, []).append((x, idx_map[(i, x)]))
    sorted_ilines = sorted(by_iline.keys())
    for i_idx in range(len(sorted_ilines) - 1):
        i_a = sorted_ilines[i_idx]
        i_b = sorted_ilines[i_idx + 1]
        for (x_a, v_a) in by_iline[i_a]:
            for (x_b, v_b) in by_iline[i_b]:
                if abs(x_b - x_a) == 1:
                    faces.append((v_a, v_b, v_a))
                    break

    artifact_id = f"geox://artifact/horizon-tracked-{len(tracked)}-vertices"

    mesh = SurfaceMesh(
        mesh_id=artifact_id,
        coordinate_frame="INLINE_XLINE_TIME",
        vertices=vertices_3d,
        faces=faces,
        confidence=confidence,
        alternative_paths=None,
        stopped_regions=stopped if stopped else None,
        operation=f"horizon_track(seeds={len(seeds)}, phase={phase_event}, half_window={half_window})",
        created_by=actor_id,
    )

    provenance = {
        "n_seeds": len(seeds),
        "phase_event": phase_event,
        "half_window": half_window,
        "smoothing_sigma": smoothing_sigma,
        "n_vertices": len(vertices_3d),
        "n_faces": len(faces),
        "n_stopped_regions": len(stopped),
        "volume_shape": list(arr.shape),
        "issued_by": actor_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "OBSERVATION",
        "claim_ceiling": "HYPOTHESIS",
    }

    return {
        **_envelope(
            status="OK",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        ),
        "data": mesh.model_dump(mode="json"),
        "provenance": provenance,
        "claim": None,
    }


def _envelope(
    *,
    status: str,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    env = {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id or "kimi-code/FI-008",
        "session_id": session_id,
        "trace_id": trace_id,
        "execution_status": "OK" if status == "OK" else "HOLD",
        "artifact_status": "READY" if status == "OK" else "DRAFT",
        "governance_status": "QUALIFIED" if status == "OK" else "HOLD",
    }
    if status == "OK":
        return {**env, "status": "OK", "claim": None}
    return {**env, "status": status, "error": error, "hold_reason": error, "claim": None}


def register_with_mcp(mcp: Any) -> None:
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_horizon_track)
    logger.info("Registered %s (seed-based 3D tracker)", TOOL_NAME)
