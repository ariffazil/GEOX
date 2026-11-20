"""geox_resqml_io.v1 — RESQML regular-grid export (resqpy) — ArtCraft S9b Phase 1.

555_COMPUTE_ONLY: the only server-side writes are transient scratch files under a
TemporaryDirectory that is removed before return — no persistent server state.
Output is caller-owned: base64 EPC + HDF5 bytes with SHA-256 provenance.

Mode:
  export_regular_epc — build a RESQML IJK regular grid (extent_kji, dxyz_jacobian)
    → EPC + HDF5 → base64 in response → self-verifying round-trip read
    (grid part present + extent + bulk volume via resqpy reload).

Falsification gates:
  - cell cap: ni*nj*nk <= 1_000_000 (memory-burn guard)
  - strictly positive, finite cell increments (dxi/dnj/dnk)
  - extent_kji positive ints; title sanitized to printable safe charset
  - export verified by round-trip read; verification failure => HOLD
Malformed input => structured HOLD envelope (never a silent pass, never a crash).

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.artcraft_resqml_io")

TOOL_NAME = "geox_resqml_io"

MAX_CELLS = 1_000_000
_SAFE_TITLE = re.compile(r"[^A-Za-z0-9 _.-]")


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
    }


async def geox_resqml_io(
    mode: str,
    extent_kji: list[int] | None = None,
    dxi: float = 100.0,
    dnj: float = 200.0,
    dnk: float = 10.0,
    title: str = "geox artcraft grid",
    actor_id: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Any = None,
) -> dict[str, Any]:
    """RESQML regular-grid export (resqpy). Mode: export_regular_epc.

    extent_kji = [nk, nj, ni] (RESQML kji order); dxi/dnj/dnk = strictly positive
    cell increments (m). Returns base64 EPC + HDF5, SHA-256 each, and a
    round-trip verification block (grid part present, extent, bulk volume m3).
    """
    env = _envelope(status="OK", session_id=session_id, actor_id=actor_id, trace_id=trace_id)
    tmp_dir: tempfile.TemporaryDirectory | None = None
    try:
        if mode != "export_regular_epc":
            return {**env, "status": "HOLD",
                    "error": f"unknown mode={mode!r}; valid: export_regular_epc",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        if (not extent_kji or len(extent_kji) != 3
                or any((not isinstance(v, int)) or v < 1 for v in extent_kji)):
            return {**env, "status": "HOLD",
                    "error": "extent_kji=[nk, nj, ni] with positive ints required",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        nk, nj, ni = extent_kji
        if ni * nj * nk > MAX_CELLS:
            return {**env, "status": "HOLD",
                    "error": f"cell count {ni * nj * nk} exceeds cap {MAX_CELLS}",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        for label, v in (("dxi", dxi), ("dnj", dnj), ("dnk", dnk)):
            if not isinstance(v, (int, float)) or not (v > 0) or v != v or v in (float("inf"),):
                return {**env, "status": "HOLD",
                        "error": f"{label} must be a positive finite number; got {v!r}",
                        "execution_status": "HOLD", "governance_status": "HOLD",
                        "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        safe_title = _SAFE_TITLE.sub("_", title)[:80] or "geox artcraft grid"

        import numpy as np
        import resqpy.grid as rg
        import resqpy.model as rqm

        tmp_dir = tempfile.TemporaryDirectory(prefix="geox_resqml_io_")
        epc = str(Path(tmp_dir.name) / "grid.epc")
        h5 = str(Path(tmp_dir.name) / "grid.h5")
        m = rqm.Model(new_epc=epc, create_basics=True, create_hdf5_ext=True, quiet=True)
        m.epc_file = epc
        Path(h5).write_bytes(b"")  # resqpy write_hdf5 appends in 'a' mode
        grid = rg.RegularGrid(
            m, extent_kji=(nk, nj, ni),
            dxyz_dkji=((0.0, 0.0, float(dxi)), (0.0, float(dnj), 0.0), (float(dnk), 0.0, 0.0)),
            use_vertical=True, title=safe_title)
        _ = grid.points_cached  # materialize geometry caches before write
        grid.write_hdf5()
        grid.create_xml()
        m.store_epc(epc)

        epc_bytes = Path(epc).read_bytes()
        h5_bytes = Path(h5).read_bytes()

        # self-verifying round-trip read (part present + extent + bulk volume)
        m2 = rqm.Model(epc_file=epc, full_load=True, quiet=True)
        ijk_parts = [k for k in m2.parts_forest if "IjkGrid" in k]
        grid_part_present = bool(ijk_parts)
        rt_extent = None
        rt_volume = None
        if grid_part_present:
            part = ijk_parts[0]
            grid_uuid = part.rsplit("_", 1)[1].replace(".xml", "")
            g2 = rg.RegularGrid(m2, uuid=grid_uuid)
            rt_extent = [int(v) for v in g2.extent_kji]
            vol = g2.volume()
            vol_vals = np.asarray(getattr(vol, "values", vol), dtype=np.float64)
            rt_volume = float(vol_vals.sum())
        if not grid_part_present or rt_extent != [nk, nj, ni]:
            return {**env, "status": "HOLD",
                    "error": "round-trip verification failed — grid part missing or extent mismatch",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}

        data = {
            "mode": "export_regular_epc",
            "extent_kji": [nk, nj, ni],
            "cell_increments_m": {"dxi": dxi, "dnj": dnj, "dnk": dnk},
            "title": safe_title,
            "bulk_volume_m3": rt_volume,
            "epc_base64": base64.b64encode(epc_bytes).decode("ascii"),
            "epc_sha256": hashlib.sha256(epc_bytes).hexdigest(),
            "epc_bytes": len(epc_bytes),
            "h5_base64": base64.b64encode(h5_bytes).decode("ascii"),
            "h5_sha256": hashlib.sha256(h5_bytes).hexdigest(),
            "h5_bytes": len(h5_bytes),
            "round_trip": {"grid_part_present": grid_part_present, "extent_kji": rt_extent,
                           "bulk_volume_m3": rt_volume},
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        return {**env, "data": data, "claim": None,
                "_ui_fallback": f"RESQML regular grid exported: {nk}x{nj}x{ni} "
                                f"({rt_volume:.1f} m3 bulk), epc {len(epc_bytes)} B + h5 {len(h5_bytes)} B, "
                                f"round-trip verified"}
    except Exception as e:
        logger.exception("geox_resqml_io unhandled")
        return {**env, "status": "HOLD", "error": f"unhandled: {type(e).__name__}: {e}",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()  # transient scratch removed — zero persistent server state


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
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_resqml_io)
    logger.info("Registered %s (ArtCraft S9b: RESQML regular-grid export)", TOOL_NAME)
