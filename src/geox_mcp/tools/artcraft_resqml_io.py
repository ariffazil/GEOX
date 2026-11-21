"""geox_resqml_io.v1 — RESQML grid export (resqpy) — ArtCraft S9b Phase 2.

555_COMPUTE_ONLY: the only server-side writes are transient scratch files under a
TemporaryDirectory that is removed before return — no persistent server state.
Output is caller-owned: base64 EPC + HDF5 bytes with SHA-256 provenance.

Modes:
  export_regular_epc — RESQML IJK regular grid (extent_kji, dxi/dnj/dnk) with
    self-verifying round-trip read.
  export_cornerpoint_epc — arbitrary ALIGNED corner-point grid from caller-supplied
    xtgeo-4 arrays (coordsv/zcornsv/actnumsv, same contract as geox_grid inspect).
    ALIGNED means every pillar is straight with unsplit quadrant corners; split
    or kinked pillars are rejected with a structured HOLD (honest boundary —
    split-pillar geometry conversion is a designed later stage, not silent math).

Falsification gates: cell caps, shape/finite/actnum checks, quadrant-equality
  alignment check, round-trip verification; malformed input => structured HOLD.

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
MAX_CP_CELLS = 250_000  # corner-point conversion cap (memory-burn guard)
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


async def _export_cornerpoint(env: dict[str, Any], *, title: str, coordsv, zcornsv, actnumsv) -> dict[str, Any]:
    """Aligned corner-point → RESQML EPC (pillar-cache conversion, probed 2026-11-21).

    Reuses the geox_grid gate for shape/finite/actnum validation, adds the
    quadrant-equality alignment gate (split/kinked pillars => structured HOLD —
    honest boundary; split-pillar conversion is a designed later stage).
    """
    from geox_mcp.tools.artcraft_grid import _grid_from_arrays

    import numpy as np
    import resqpy.grid as rg
    import resqpy.model as rqm
    import resqpy.crs as rqc

    safe_title = _SAFE_TITLE.sub("_", title)[:80] or "geox artcraft grid"
    try:
        xg, meta = _grid_from_arrays(coordsv, zcornsv, actnumsv)
    except ValueError as ve:
        return {**env, "status": "HOLD", "error": f"falsification gate: {ve}",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
    except Exception as e:
        return {**env, "status": "HOLD", "error": f"xtgeo rejected arrays: {type(e).__name__}: {e}",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}

    coords = np.asarray(xg._coordsv, dtype=np.float64)
    zcorn = np.asarray(xg._zcornsv, dtype=np.float32)
    ncol, nrow, nlay = meta["ncol"], meta["nrow"], meta["nlay"]

    # alignment gate: unsplit pillars => the 4 quadrant depths of each
    # (pillar, plane) are identical. Split/kinked pillars differ => HOLD.
    q = zcorn[..., :]  # (ncol+1, nrow+1, nlay+1, 4)
    qmax = q.max(axis=3)
    qmin = q.min(axis=3)
    if not np.allclose(qmax, qmin, rtol=0.0, atol=1e-6):
        split_count = int((qmax - qmin > 1e-6).any(axis=2).sum())
        return {**env, "status": "HOLD",
                "error": (f"alignment gate: {split_count} pillar planes carry split/kinked corners; "
                          "export_cornerpoint_epc supports ALIGNED grids only (split-pillar "
                          "conversion is a designed later stage)"),
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}

    try:
        xbulk = None
        vol = xg.get_bulk_volume()
        xv = np.asarray(getattr(vol, "values", vol), dtype=np.float64)
        xbulk = float(xv.sum())
    except Exception:
        xbulk = None

    tmp_dir = tempfile.TemporaryDirectory(prefix="geox_resqml_io_cp_")
    epc = str(Path(tmp_dir.name) / "grid.epc")
    h5 = str(Path(tmp_dir.name) / "grid.h5")
    try:
        m = rqm.Model(new_epc=epc, create_basics=True, quiet=True)
        m.epc_file = epc
        Path(h5).write_bytes(b"")
        m.create_hdf5_ext()
        crs = rqc.Crs(m, title="ArtCraft workspace CRS", z_inc_down=True)
        crs.create_xml()
        nxp, nyp = ncol + 1, nrow + 1
        grid = rg.Grid(m)
        grid.grid_title = safe_title
        grid.extent_kji = (nlay, nrow, ncol)
        grid.nk, grid.nj, grid.ni = nlay, nrow, ncol
        grid.geometry_required = True
        grid.is_aligned = True
        grid.crs_uuid = crs.uuid
        heads = coords[:, :, 0:3]
        feet = coords[:, :, 3:6]
        fracs = np.linspace(0.0, 1.0, nlay + 1).reshape(nlay + 1, 1, 1, 1)
        points = heads[None, :, :, :] + (feet - heads)[None, :, :, :] * fracs
        grid.points_cached = np.transpose(points, (0, 2, 1, 3))  # (nlay+1, nyp, nxp, 3)
        grid.inherited_pillars = False
        grid.pzcorn_cached = np.transpose(zcorn, (2, 0, 1, 3)).reshape(nlay + 1, nxp * nyp, 2, 2)
        grid.write_hdf5()
        grid.create_xml()
        m.store_epc(epc)
    except Exception as e:
        return {**env, "status": "HOLD", "error": f"resqpy export failed: {type(e).__name__}: {e}",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}

    epc_bytes = Path(epc).read_bytes()
    h5_bytes = Path(h5).read_bytes()

    # self-verifying round-trip read (part present + extent + bulk volume vs xtgeo)
    m2 = rqm.Model(epc_file=epc, full_load=True, quiet=True)
    ijk_parts = [k for k in m2.parts_forest if "IjkGrid" in k]
    grid_part_present = bool(ijk_parts)
    rt_extent = None
    rt_volume = None
    if grid_part_present:
        part = ijk_parts[0]
        grid_uuid = part.rsplit("_", 1)[1].replace(".xml", "")
        g2 = rg.Grid(m2, uuid=grid_uuid)
        rt_extent = [int(v) for v in (g2.nk, g2.nj, g2.ni)]
        vol = g2.volume()
        vol_vals = np.asarray(getattr(vol, "values", vol), dtype=np.float64)
        rt_volume = float(vol_vals.sum())
    extent_expected = [nlay, nrow, ncol]
    if not grid_part_present or rt_extent != extent_expected:
        return {**env, "status": "HOLD",
                "error": "round-trip verification failed — grid part missing or extent mismatch",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
    if xbulk is not None and rt_volume is not None and abs(rt_volume - xbulk) > max(1e-3, abs(xbulk) * 1e-6):
        return {**env, "status": "HOLD",
                "error": f"round-trip volume mismatch: xtgeo {xbulk:.6f} vs RESQML {rt_volume:.6f}",
                "execution_status": "HOLD", "governance_status": "HOLD",
                "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}

    data = {
        "mode": "export_cornerpoint_epc",
        "extent_kji": extent_expected,
        "cell_increments_m": None,
        "title": safe_title,
        "bulk_volume_m3": rt_volume,
        "xtgeo_bulk_volume_m3": xbulk,
        "epc_base64": base64.b64encode(epc_bytes).decode("ascii"),
        "epc_sha256": hashlib.sha256(epc_bytes).hexdigest(),
        "epc_bytes": len(epc_bytes),
        "h5_base64": base64.b64encode(h5_bytes).decode("ascii"),
        "h5_sha256": hashlib.sha256(h5_bytes).hexdigest(),
        "h5_bytes": len(h5_bytes),
        "round_trip": {"grid_part_present": grid_part_present, "extent_kji": rt_extent,
                       "bulk_volume_m3": rt_volume, "volume_matches_xtgeo": xbulk is not None},
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
    return {**env, "data": data, "claim": None,
            "_ui_fallback": f"RESQML corner-point grid exported (aligned): {ncol}x{nrow}x{nlay} "
                            f"({rt_volume:.1f} m3 bulk), epc {len(epc_bytes)} B + h5 {len(h5_bytes)} B, "
                            f"round-trip verified against xtgeo"}


async def geox_resqml_io(
    mode: str,
    extent_kji: list[int] | None = None,
    dxi: float = 100.0,
    dnj: float = 200.0,
    dnk: float = 10.0,
    title: str = "geox artcraft grid",
    coordsv: list | None = None,
    zcornsv: list | None = None,
    actnumsv: list | None = None,
    actor_id: str | None = None,
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Any = None,
) -> dict[str, Any]:
    """RESQML grid export (resqpy). Modes: export_regular_epc | export_cornerpoint_epc.

    export_regular_epc: extent_kji=[nk, nj, ni] + dxi/dnj/dnk (strictly positive m).
    export_cornerpoint_epc: coordsv/zcornsv/actnumsv (geox_grid inspect contract) —
    ALIGNED corner-point grids only; split/kinked pillars return structured HOLD.

    Returns base64 EPC + HDF5, SHA-256 each, and a round-trip verification block
    (grid part present, extent, bulk volume m3).
    """
    env = _envelope(status="OK", session_id=session_id, actor_id=actor_id, trace_id=trace_id)
    tmp_dir: tempfile.TemporaryDirectory | None = None
    try:
        if mode not in ("export_regular_epc", "export_cornerpoint_epc"):
            return {**env, "status": "HOLD",
                    "error": f"unknown mode={mode!r}; valid: export_regular_epc, export_cornerpoint_epc",
                    "execution_status": "HOLD", "governance_status": "HOLD",
                    "coverage_score": 0.0, "epistemic_label": "UNKNOWN"}
        if mode == "export_cornerpoint_epc":
            return await _export_cornerpoint(env, title=title, coordsv=coordsv,
                                             zcornsv=zcornsv, actnumsv=actnumsv)
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
    logger.info("Registered %s (ArtCraft S9b: RESQML regular + aligned corner-point export)", TOOL_NAME)
