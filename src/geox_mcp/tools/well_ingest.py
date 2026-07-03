"""
geox_well_ingest — Unified Well Data Ingestion (Phase 2)
═══════════════════════════════════════════════════════════
Absorbs: geox_data_ingest_bundle, geox_las_inspect, geox_header_inspect,
         geox_seismic_segy_inspect, geox_dst_ingest_test

Modes: las, segy, seismic, deviation, tops, dst, checkshot, auto

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger("geox.well_ingest")


async def geox_well_ingest(
    mode: Literal["las", "segy", "seismic", "deviation", "tops", "dst", "checkshot", "auto"] = "auto",
    # ── LAS / data_ingest_bundle params ──
    source_uri: str | None = None,
    source_type: str = "auto",
    well_id: str | None = None,
    standardize_curves: bool = True,
    normalize_units: bool = True,
    content_base64: str | None = None,
    filename: str | None = None,
    target_dir: str = "/data/geox_las",
    overwrite: bool = False,
    batch_mode: bool = False,
    artifact_refs: list[str] | None = None,
    qc_strict: bool = True,
    source_crs: str = "unknown",
    depth_datum: str | None = None,
    # ── header_inspect params ──
    file_format: str | None = None,
    las_metadata: dict[str, Any] | None = None,
    las_curve_info: list[dict[str, Any]] | None = None,
    segy_metadata: dict[str, Any] | None = None,
    seismic_metadata: dict[str, Any] | None = None,
    deviation_metadata: dict[str, Any] | None = None,
    tops_metadata: dict[str, Any] | None = None,
    # ── DST params ──
    field: str | None = None,
    reservoir_name: str | None = None,
    test_name: str | None = None,
    test_duration_hr: float | None = None,
    main_flow_hr: float | None = None,
    main_buildup_hr: float | None = None,
    choke_size_64ths: float | None = None,
    bhp_psi: float | None = None,
    bht_c: float | None = None,
    whp_psi: float | None = None,
    wht_c: float | None = None,
    gas_rate_mmscfd: float | None = None,
    condensate_rate_stbd: float | None = None,
    water_rate_stbd: float | None = None,
    co2_mol_pct: float | None = None,
    h2s_ppm: float | None = None,
    bsw_pct: float | None = None,
    chloride_ppm: float | None = None,
    wgr_stb_per_mmscf: float | None = None,
    permeability_md_min: float | None = None,
    permeability_md_max: float | None = None,
    skin_min: float | None = None,
    skin_max: float | None = None,
) -> dict[str, Any]:
    """Unified well data ingestion — auto-detect format or specify mode.

    Modes:
      las        - Inspect LAS well log headers
      segy       - Inspect SEG-Y seismic headers
      seismic    - Inspect seismic volume metadata
      deviation  - Inspect deviation survey
      tops       - Inspect stratigraphic tops
      dst        - Structured DST ingestion with derived metrics
      checkshot  - Checkshot/VSP data ingestion
      auto       - Auto-detect format from source_uri extension
    """
    # ── Inspect path: only when caller EXPLICITLY supplies metadata ─────
    # Without metadata, `mode in ("las", "auto") and source_uri` is an
    # INGEST request, not an inspect request. Routing those into
    # geox_las_inspect produced validator reports with no artifact_ref.
    # Fix 2026-07-03: require explicit las_metadata OR las_curve_info to
    # enter the inspect branch. Otherwise fall through to data_ingest_bundle.
    if mode in ("las", "auto") and source_uri and (las_metadata or las_curve_info):
        from geox_mcp.tools.ingestion import geox_las_inspect as _impl

        if mode == "auto" and any(source_uri.lower().endswith(ext) for ext in (".las", ".LAS")):
            return await _impl(las_metadata=las_metadata or {}, las_curve_info=las_curve_info or [])
        elif mode == "las":
            return await _impl(las_metadata=las_metadata or {}, las_curve_info=las_curve_info or [])

    if mode in ("segy", "auto") and segy_metadata:
        from geox_mcp.tools.ingestion import geox_seismic_segy_inspect as _impl

        return await _impl(segy_metadata=segy_metadata)

    if mode == "seismic" and seismic_metadata:
        from geox_mcp.tools.ingestion import geox_seismic_inspect as _impl

        return await _impl(seismic_metadata=seismic_metadata)

    if mode == "deviation" and deviation_metadata:
        from geox_mcp.tools.ingestion import geox_deviation_survey_inspect as _impl

        return await _impl(deviation_metadata=deviation_metadata)

    if mode == "tops" and tops_metadata:
        from geox_mcp.tools.ingestion import geox_tops_inspect as _impl

        return await _impl(tops_metadata=tops_metadata)

    if mode == "header":
        from geox_mcp.tools.ingestion import geox_header_inspect as _impl

        return await _impl(
            file_format=file_format or "las",
            las_metadata=las_metadata,
            las_curve_info=las_curve_info,
            segy_metadata=segy_metadata,
            seismic_metadata=seismic_metadata,
            deviation_metadata=deviation_metadata,
            tops_metadata=tops_metadata,
        )

    if mode == "dst":
        from geox_mcp.tools.dst import geox_dst_ingest_test as _impl

        return await _impl(
            well_id=well_id or "UNKNOWN",
            field=field,
            reservoir_name=reservoir_name,
            test_name=test_name,
            test_duration_hr=test_duration_hr,
            main_flow_hr=main_flow_hr,
            main_buildup_hr=main_buildup_hr,
            choke_size_64ths=choke_size_64ths,
            bhp_psi=bhp_psi,
            bht_c=bht_c,
            whp_psi=whp_psi,
            wht_c=wht_c,
            gas_rate_mmscfd=gas_rate_mmscfd,
            condensate_rate_stbd=condensate_rate_stbd,
            water_rate_stbd=water_rate_stbd,
            co2_mol_pct=co2_mol_pct,
            h2s_ppm=h2s_ppm,
            bsw_pct=bsw_pct,
            chloride_ppm=chloride_ppm,
            wgr_stb_per_mmscf=wgr_stb_per_mmscf,
            permeability_md_min=permeability_md_min,
            permeability_md_max=permeability_md_max,
            skin_min=skin_min,
            skin_max=skin_max,
        )

    # Fallback: full data_ingest_bundle for auto mode with files
    if mode == "auto":
        from geox_mcp.tools.data import geox_data_ingest_bundle as _impl

        return await _impl(
            source_uri=source_uri,
            source_type=source_type,
            well_id=well_id,
            standardize_curves=standardize_curves,
            normalize_units=normalize_units,
            content_base64=content_base64,
            filename=filename,
            target_dir=target_dir,
            overwrite=overwrite,
            batch_mode=batch_mode,
            artifact_refs=artifact_refs,
            qc_strict=qc_strict,
            source_crs=source_crs,
            depth_datum=depth_datum,
        )

    return {
        "status": "INVALID",
        "errors": [f"No valid parameters for mode='{mode}'. Provide the required mode-specific inputs."],
    }
