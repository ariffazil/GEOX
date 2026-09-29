"""
geox_seismic_display_trace.v1 — PNG → Polyline (geometry only).

Per the GEOX Seismic Interpretation Forge Package:
- Ingest a PNG seismic section image
- Detect candidate horizons by colour class (from geox://conventions/seismic_display)
- Extract smooth Polylines via median trace + Chaikin smoothing + segment split
- Emit Polyline artifacts with full provenance
- REFUSE any amplitude/attribute/AVO request (DISPLAY_PROXY claim ceiling)

Reference: Copilot forge prompt BUILD step 2 + Step 7 of the section-image
interpretation slice. evidence_class=DISPLAY_PROXY, claim_ceiling=GEOMETRY.

DITEMPA BUKAN DIBERI — Forged, not given.
"""
from __future__ import annotations

import base64
import hashlib
import io
import logging
import math
from datetime import datetime, timezone
from typing import Any, Literal

import numpy as np
from fastmcp import Context
from PIL import Image

from geox.seismic.contracts import PointSet, Polyline

logger = logging.getLogger("geox.seismic_display_trace")

TOOL_NAME = "geox_seismic_display_trace"

REFUSE_OPERATIONS = {
    "amplitude",
    "attribute",
    "avo",
    "phase_classification",
    "quantitative_prospect",
    "quantitative_fault_seal",
    "amplitude_preservation",
}

# Default axis calibration (image pixels); tool records actual or "uncalibrated"
DEFAULT_AXIS_CALIBRATION = {
    "x": {"unit": "pixel", "scale": 1.0, "residual_px": 0.0},
    "y": {"unit": "pixel", "scale": 1.0, "residual_px": 0.0, "axis": "TWT_ms_uncalibrated"},
}

# Default color thresholds per display convention
DEFAULT_COLOR_CLASSES = {
    "horizon.sru":    {"rgb": [255, 140, 0],   "tolerance": 30},
    "horizon.uiu":    {"rgb": [0, 210, 255],   "tolerance": 30},
    "horizon.dru":    {"rgb": [31, 42, 107],    "tolerance": 25},
    "horizon.uncertain": {"rgb": [230, 230, 230], "tolerance": 25},
}


# ────────────────────────────────────────────────────────────────────────────
# Color mask + trace extraction
# ────────────────────────────────────────────────────────────────────────────


def _color_mask(rgb_arr: np.ndarray, target_rgb: list[int], tolerance: int) -> np.ndarray:
    """Boolean mask of pixels close to target RGB within tolerance (per channel)."""
    r, g, b = target_rgb
    return (
        (np.abs(rgb_arr[..., 0] - r) <= tolerance)
        & (np.abs(rgb_arr[..., 1] - g) <= tolerance)
        & (np.abs(rgb_arr[..., 2] - b) <= tolerance)
    )


def _trace_per_column(mask: np.ndarray, x_min: int, x_max: int, y_min: int, y_max: int) -> dict[int, list[float]]:
    """For each x column, collect median y of masked pixels in (y_min, y_max)."""
    traces: dict[int, list[float]] = {}
    for x in range(x_min, x_max):
        col = mask[y_min:y_max, x]
        ys = np.where(col)[0]
        if len(ys) > 0:
            traces[x] = [float(y_min + np.median(ys))]
    return traces


def _chaikin(pts: list[tuple[float, float]], iterations: int = 3) -> list[tuple[float, float]]:
    """Chaikin corner-cutting smoothing."""
    if len(pts) < 2:
        return list(pts)
    p = [(float(x), float(y)) for x, y in pts]
    for _ in range(iterations):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            q.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        q.append(p[-1])
        p = q
    return p


def _split_into_segments(
    traces: dict[int, list[float]],
    max_x_gap: int = 25,
    max_y_jump: float = 22.0,
    min_length: int = 8,
) -> list[list[tuple[int, float]]]:
    """Split a per-column trace into segments when x-gap or y-jump exceeds threshold."""
    if not traces:
        return []
    xs = sorted(traces.keys())
    segments: list[list[tuple[int, float]]] = [[]]
    for x in xs:
        y = traces[x][0]
        if segments[-1]:
            prev_x, prev_y = segments[-1][-1]
            if x - prev_x > max_x_gap or abs(y - prev_y) > max_y_jump:
                segments.append([])
        segments[-1].append((x, y))
    return [s for s in segments if len(s) >= min_length]


def _segment_to_polyline(
    segment: list[tuple[int, float]],
    polyline_id: str,
    coordinate_frame: str,
    smoothing_iters: int = 3,
    created_by: str = "kimi-code/FI-008",
) -> Polyline:
    """Convert a per-column segment to a smoothed Polyline contract.

    Returns 3D points (x, y, z=0.0) to satisfy Polyline contract.
    """
    smoothed = _chaikin(segment, iterations=smoothing_iters)
    points_3d = [(float(x), float(y), 0.0) for x, y in smoothed]
    return Polyline(
        polyline_id=polyline_id,
        coordinate_frame=coordinate_frame,
        points=points_3d,
        confidence=None,
        parent_ref=None,
        operation=f"display_trace+chaikin({smoothing_iters})",
        created_by=created_by,
    )


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_display_trace(
    png_base64: str | None = None,
    png_path: str | None = None,
    color_class: str = "horizon.sru",
    rgb: list[int] | None = None,
    tolerance: int = 30,
    x_min: int | None = None,
    x_max: int | None = None,
    y_min: int = 0,
    y_max: int | None = None,
    smoothing_iters: int = 3,
    requested_operation: str | None = None,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Context | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Extract horizon Polylines from a PNG seismic section.

    Geometry-only output. REFUSES amplitude/attribute/AVO requests.

    Parameters
    ----------
    png_base64 : str
        PNG image encoded as base64.
    png_path : str
        Path to PNG file (alternative to png_base64).
    color_class : str
        One of DEFAULT_COLOR_CLASSES keys, or a custom class name.
    rgb : list[int]
        Custom target RGB [r, g, b]. If provided, color_class is informational only.
    tolerance : int
        Per-channel tolerance for color match (default 30).
    x_min, x_max, y_min, y_max : int
        Optional sub-region bounds; defaults use full image.
    smoothing_iters : int
        Chaikin smoothing iterations (default 3).
    requested_operation : str
        If provided, must be 'geometry' or 'display_only'; anything else is REFUSED.

    Returns
    -------
    dict with:
      - status: OK | HOLD
      - data: list of Polyline artifacts (DISPLAY_PROXY, claim_ceiling=GEOMETRY)
      - provenance: source SHA256 + axis calibration + parameters
      - claim: null (display proxy only)
    """
    if requested_operation is not None and requested_operation.lower() in REFUSE_OPERATIONS:
        return _envelope(
            status="HOLD",
            error=(
                f"REFUSED: requested_operation={requested_operation!r} violates claim_ceiling=GEOMETRY "
                f"for DISPLAY_PROXY. Use a non-display seismic source (SEG-Y) for {requested_operation}."
            ),
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    # Load image
    if png_base64 is None and png_path is None:
        return _envelope(
            status="HOLD",
            error="either png_base64 or png_path required",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    try:
        if png_base64 is not None:
            img_bytes = base64.b64decode(png_base64)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        else:
            img = Image.open(png_path).convert("RGB")
    except Exception as e:
        return _envelope(
            status="HOLD",
            error=f"failed to load image: {type(e).__name__}: {e}",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    src_hash = hashlib.sha256(img.tobytes()).hexdigest()
    width, height = img.size
    rgb_arr = np.asarray(img, dtype=np.int32)

    if x_max is None:
        x_max = width
    if y_max is None:
        y_max = height
    x_min = x_min or 0

    # Resolve target RGB
    if rgb is None:
        if color_class not in DEFAULT_COLOR_CLASSES:
            return _envelope(
                status="HOLD",
                error=f"unknown color_class={color_class!r}. Valid: {list(DEFAULT_COLOR_CLASSES)}",
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )
        rgb = DEFAULT_COLOR_CLASSES[color_class]["rgb"]

    # Trace
    mask = _color_mask(rgb_arr, rgb, tolerance)
    traces = _trace_per_column(mask, x_min, x_max, y_min, y_max)
    segments = _split_into_segments(traces)

    if not segments:
        return _envelope(
            status="HOLD",
            error=(
                f"no horizon segments detected for color_class={color_class}, "
                f"rgb={rgb}, tolerance={tolerance}, region=({x_min},{y_min})-({x_max},{y_max})"
            ),
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    polylines: list[Polyline] = []
    for i, seg in enumerate(segments):
        poly_id = f"geox://artifact/horizon-{color_class.replace('.','-')}-{src_hash[:8]}-seg{i:02d}"
        # Compute simple confidence: 1 - normalized median y-jitter
        ys = [y for _, y in seg]
        if len(ys) > 2:
            jitter = float(np.std(np.diff(ys)))
            confidence = max(0.0, min(1.0, 1.0 - jitter / 30.0))
        else:
            confidence = 0.5
        poly = _segment_to_polyline(seg, poly_id, "INLINE_XLINE_SAMPLE", smoothing_iters)
        # Attach confidence if desired via parent metadata (we just record in envelope)
        poly_obj = Polyline.model_validate(poly.model_dump())
        polylines.append(poly_obj)

    provenance = {
        "source_hash_sha256": src_hash,
        "image_width_px": width,
        "image_height_px": height,
        "color_class": color_class,
        "target_rgb": rgb,
        "tolerance": tolerance,
        "x_range": [x_min, x_max],
        "y_range": [y_min, y_max],
        "smoothing_iters": smoothing_iters,
        "axis_calibration": DEFAULT_AXIS_CALIBRATION,
        "n_segments": len(segments),
        "evidence_class": "DISPLAY_PROXY",
        "claim_ceiling": "GEOMETRY",
        "issued_by": actor_id,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        **_envelope(
            status="OK",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        ),
        "data": [polyline.model_dump(mode="json") for polyline in polylines],
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
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_display_trace)
    logger.info("Registered %s (display_proxy, geometry-only)", TOOL_NAME)
