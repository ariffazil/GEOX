"""
geox_basin — Unified Basin Intelligence (Phase 2)
══════════════════════════════════════════════════
Absorbs: geox_basin_profile, geox_basin_resolve, geox_query_intake,
         geox_query_macrostrat, geox_deep_time_state, geox_emag2_ingest,
         geox_icgem_models, geox_map_context_scene

Modes: profile, resolve, macrostrat, deep_time, emag2, icgem, intake, scene

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations
from typing import Any, Literal

async def geox_basin(
    mode: Literal["profile", "resolve", "macrostrat", "deep_time", "emag2", "icgem", "intake", "scene"] = "profile",
    name: str = "",
    basin_name: str = "",
    macrostrat_mode: str = "macrostrat_units",
    lat: float | None = None,
    lng: float | None = None,
    age_ma: float | None = None,
    age_top_ma: float | None = None,
    age_bot_ma: float | None = None,
    period: str | None = None,
    query: str | None = None,
    include_pending_datasets: bool = True,
    force: bool = False,
    intent: str = "general",
    bbox: list[float] | None = None,
    scene_mode: str = "bbox_context",
    crs: str = "EPSG:4326",
    vp_slice_inline: dict[str, Any] | None = None,
    profile_mode: str = "overview",
    claim_strictness: str = "screen",
    evidence_refs: list[str] | None = None,
    include_missing_evidence: bool = True,
) -> dict[str, Any]:
    """Unified basin intelligence — profiles, resolution, deep time, spatial context.

    Modes:
      profile    - Basin overview, petroleum system, stratigraphy, play fairway, risk
      resolve    - Resolve basin name to canonical ID and bounding box
      macrostrat - Macrostrat API (units, columns, lithologies, strat names, intervals, fossils, map)
      deep_time  - Deep Time State Vector (13 fields, ICS Chart v2024/12)
      emag2      - EMAG2v3 global magnetic anomaly grid
      icgem      - ICGEM gravity field models
      intake     - Natural-language query intake routing
      scene      - Spatial bbox context, CRS checks, causal scene rendering
    """
    kwargs = locals().copy()
    if mode == "resolve":
        from geox_mcp.tools.basin import geox_basin_resolve as _impl
        return await _impl(name=kwargs.get("name", kwargs.get("basin_name", "")))

    if mode == "macrostrat":
        from geox_mcp.tools.basin import geox_query_macrostrat as _impl
        return await _impl(
            basin_name=kwargs.get("basin_name", ""),
            mode=kwargs.get("macrostrat_mode", "macrostrat_units"),
            lat=kwargs.get("lat"),
            lng=kwargs.get("lng"),
        )

    if mode == "deep_time":
        from geox_mcp.tools.deep_time_state import geox_deep_time_state as _impl
        return await _impl(
            age_ma=kwargs.get("age_ma"),
            age_top_ma=kwargs.get("age_top_ma"),
            age_bot_ma=kwargs.get("age_bot_ma"),
            period=kwargs.get("period"),
            query=kwargs.get("query"),
            include_pending_datasets=kwargs.get("include_pending_datasets", True),
        )

    if mode == "emag2":
        from geox_mcp.tools.geophysics_nonseismic import geox_emag2_ingest as _impl
        return await _impl(force=kwargs.get("force", False))

    if mode == "icgem":
        from geox_mcp.tools.geophysics_nonseismic import geox_icgem_models as _impl
        return await _impl()

    if mode == "intake":
        from geox_mcp.tools.basin import geox_query_intake as _impl
        return await _impl(
            query=kwargs.get("query", ""),
            intent=kwargs.get("intent", "general"),
        )

    if mode == "scene":
        from geox_mcp.tools.map_context import geox_map_context_scene as _impl
        return await _impl(
            bbox=kwargs.get("bbox", [0, 0, 1, 1]),
            mode=kwargs.get("scene_mode", "bbox_context"),
            crs=kwargs.get("crs", "EPSG:4326"),
            vp_slice_inline=kwargs.get("vp_slice_inline"),
        )

    # Default: profile
    from geox_mcp.tools.basin import geox_basin_profile as _impl
    return await _impl(
        basin_name=kwargs.get("basin_name", ""),
        mode=kwargs.get("profile_mode", "overview"),
        claim_strictness=kwargs.get("claim_strictness", "screen"),
        evidence_refs=kwargs.get("evidence_refs"),
        include_missing_evidence=kwargs.get("include_missing_evidence", True),
        lat=kwargs.get("lat"),
        lng=kwargs.get("lng"),
    )
