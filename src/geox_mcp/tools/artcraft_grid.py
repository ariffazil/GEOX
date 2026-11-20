"""geox_grid.v1 — Corner-point grid compute (xtgeo) — ArtCraft S9b Phase 1.

555_COMPUTE_ONLY: pure functions on caller-supplied arrays; no server state is
read or mutated, no filesystem access. Deterministic; safe under anon rate limits.

Modes:
  inspect — validate caller-supplied corner-point arrays (coordsv / zcornsv /
            actnumsv, xtgeo 4.x gridded shapes); report dims, active-cell count,
            geometric bulk volume.
  box     — deterministic synthetic box grid descriptor (dims only; no arrays
            returned — for pipeline wiring and tests).

Falsification gates:
  - dimension cap: ncol*nrow*nlay <= 250_000 (memory-burn guard)
  - exact shape validation for every array (xtgeo 4.x gridded shapes)
  - finite-value check on coordsv/zcornsv (NaN/inf => structured HOLD)
  - actnumsv restricted to {0, 1}
Malformed input => structured HOLD envelope (never a silent pass, never a crash).

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("geox.artcraft_grid")

TOOL_NAME = "geox_grid"

MAX_CELLS = 250_000
_DOMAIN = "earth.structure"


def _envelope(*, status: str, session_id: str | None, actor_id: str | None, trace_id: str | None,
              error: str | None = None) -> dict[str, Any]:
    ok = status == "OK"
    return {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id,
        "session_id": session_id,
        "trace_id": trace_id,
        "status": status,
        "execution_status": "OK" if ok else "HOLD",
        "artifact_status": "READY" if ok else "DRAFT",
        "governance_status": "QUALIFIED" if ok else "HOLD",
        "coverage_score": 1.0 if ok else 0.0,
        "epistemic_label": "DER" if ok else "UNKNOWN",
        "evidence_refs": [],
        "error": error,
        "_ui_fallback": (
            "corner-point grid computed: dims ok, see data block" if ok
            else f"HOLD — {error}"
        ),
    }


def _grid_from_arrays(coordsv: Any, zcornsv: Any, actnumsv: Any) -> tuple[Any, dict[str, Any]]:
    import numpy as np
    import xtgeo

    coords = np.asarray(coordsv, dtype=np.float64)
    zcorn = np.asarray(zcornsv, dtype=np.float64)
    act = np.asarray(actnumsv)
    if coords.ndim != 3 or coords.shape[2] != 6:
        raise ValueError(f"coordsv must have shape (ncol+1, nrow+1, 6); got {coords.shape}")
    if zcorn.ndim != 4 or zcorn.shape[3] != 4:
        raise ValueError(f"zcornsv must be 4D with 4 corners per plane; got {zcorn.shape}")
    if act.ndim != 3:
        raise ValueError(f"actnumsv must be 3D (ncol, nrow, nlay); got {act.shape}")
    ncol, nrow, nlay = act.shape  # actnum carries the exact cell dims
    if coords.shape[0] != ncol + 1 or coords.shape[1] != nrow + 1:
        raise ValueError(
            f"coordsv shape mismatch: leading dims must be (ncol+1, nrow+1)=({ncol + 1}, {nrow + 1}); got {coords.shape[:2]}")
    if zcorn.shape[3] != 4 or zcorn.size != (ncol + 1) * (nrow + 1) * (nlay + 1) * 4:
        raise ValueError(
            f"zcornsv shape mismatch: expected xtgeo-4 padded layout sized "
            f"(ncol+1)*(nrow+1)*(nlay+1)*4 = {(ncol + 1) * (nrow + 1) * (nlay + 1) * 4}; got shape {zcorn.shape}")
    if ncol * nrow * nlay > MAX_CELLS:
        raise ValueError(f"cell count {ncol * nrow * nlay} exceeds cap {MAX_CELLS}")
    if not np.isfinite(coords).all():
        raise ValueError("coordsv contains NaN/inf")
    if not np.isfinite(zcorn).all():
        raise ValueError("zcornsv contains NaN/inf")
    if not np.isin(act, (0, 1)).all():
        raise ValueError("actnumsv must contain only 0/1")
    grid = xtgeo.Grid(coords, zcorn.astype(np.float32), act.astype(np.int32))
    meta = {"ncol": ncol, "nrow": nrow, "nlay": nlay}
    return grid, meta


async def geox_grid(
    mode: str,
    dims: list[int] | None = None,
    coordsv: list | None = None,
    zcornsv: list | None = None,
    actnumsv: list | None = None,
    actor_id: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Any = None,
) -> dict[str, Any]:
    """Corner-point grid compute (xtgeo). Modes: inspect | box.

    inspect: coordsv (ncol+1, nrow+1, 6), zcornsv 4D (4 corners per plane, size
    = ncol*nrow*(nlay+1)*4 per xtgeo-4 layout), actnumsv (ncol, nrow, nlay) —
    nested lists. Reports dims, active-cell count, geometric bulk volume (m3).
    box: dims=[ni, nj, nk] — deterministic synthetic grid descriptor.
    """
    env = _envelope(status="OK", session_id=session_id, actor_id=actor_id, trace_id=trace_id)
    try:
        import numpy as np
        import xtgeo

        if mode not in ("inspect", "box"):
            return {**env, "status": "HOLD", "error": f"unknown mode={mode!r}; valid: inspect, box",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}

        if mode == "box":
            if not dims or len(dims) != 3 or any((not isinstance(v, int)) or v < 1 for v in dims):
                return {**env, "status": "HOLD", "error": "box mode requires dims=[ni, nj, nk] positive ints",
                        "execution_status": "HOLD", "governance_status": "HOLD",
                        "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
            ni, nj, nk = dims
            if ni * nj * nk > MAX_CELLS:
                return {**env, "status": "HOLD",
                        "error": f"cell count {ni * nj * nk} exceeds cap {MAX_CELLS}",
                        "execution_status": "HOLD", "governance_status": "HOLD",
                        "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
            g = xtgeo.create_box_grid((ni, nj, nk))
            act = np.asarray(g.actnum_array)
            return {**env,
                    "data": {"mode": "box", "ncol": ni, "nrow": nj, "nlay": nk,
                             "total_cells": ni * nj * nk, "active_cells": int(act.sum()),
                             "computed_at": datetime.now(timezone.utc).isoformat()},
                    "claim": None,
                    "_ui_fallback": f"synthetic box grid {ni}x{nj}x{nk}: "
                                    f"{int(act.sum())}/{ni * nj * nk} active cells"}

        if coordsv is None or zcornsv is None or actnumsv is None:
            return {**env, "status": "HOLD",
                    "error": "inspect mode requires coordsv, zcornsv and actnumsv",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        try:
            grid, meta = _grid_from_arrays(coordsv, zcornsv, actnumsv)
        except ValueError as ve:
            return {**env, "status": "HOLD", "error": f"falsification gate: {ve}",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        except Exception as e:  # xtgeo structural rejection (zcorn ordering etc.)
            return {**env, "status": "HOLD", "error": f"xtgeo rejected arrays: {type(e).__name__}: {e}",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        act = np.asarray(grid.actnum_array)
        try:
            vol = grid.get_bulk_volume()
            vals = np.asarray(getattr(vol, "values", vol), dtype=np.float64)
            bulk = float(vals.sum())
        except Exception:
            bulk = None
        return {**env,
                "data": {"mode": "inspect", **meta,
                         "total_cells": meta["ncol"] * meta["nrow"] * meta["nlay"],
                         "active_cells": int(act.sum()),
                         "bulk_volume_m3": bulk,
                         "computed_at": datetime.now(timezone.utc).isoformat()},
                "claim": None,
                "_ui_fallback": f"corner-point grid {meta['ncol']}x{meta['nrow']}x{meta['nlay']}: "
                                f"{int(act.sum())} active cells"
                                + (f", bulk {bulk:.1f} m3" if bulk is not None else "")}
    except Exception as e:
        logger.exception("geox_grid unhandled")
        return {**env, "status": "HOLD", "error": f"unhandled: {type(e).__name__}: {e}",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}


def register_with_mcp(mcp: Any, annotations: dict[str, Any] | None = None) -> None:
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    if annotations is None:
        try:
            from geox_mcp.server import _geox_annotations
            annotations = _geox_annotations(TOOL_NAME)
        except Exception:
            annotations = {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_grid)
    logger.info("Registered %s (ArtCraft S9b: xtgeo corner-point compute)", TOOL_NAME)
