"""
geox_basin — Unified Basin Intelligence (Phase 2.5)
══════════════════════════════════════════════════════
Absorbs: geox_basin_profile, geox_basin_resolve, geox_query_intake,
         geox_query_macrostrat, geox_deep_time_state, geox_emag2_ingest,
         geox_icgem_models, geox_map_context_scene, geox_sts

Modes: profile, resolve, macrostrat, deep_time, emag2, icgem, intake, scene, sts

Phase 2.5 STS: basin = state machine over space and time, not horizon stack.
Diachroneity default. Reality loop engine.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import math
from typing import Any, Literal


def _model_spread(results: dict[str, dict[str, Any]]) -> float:
    """Compute spatial spread (km) between plate model reconstructions."""
    if len(results) < 2:
        return 0.0
    lats = [r["paleo_lat"] for r in results.values()]
    lons = [r["paleo_lon"] for r in results.values()]
    avg_lat = sum(lats) / len(lats)
    km_per_deg = 111.32
    dlat = (max(lats) - min(lats)) * km_per_deg
    dlon = (max(lons) - min(lons)) * km_per_deg * math.cos(math.radians(avg_lat))
    return round(math.sqrt(dlat**2 + dlon**2), 1)


async def geox_basin(
    mode: Literal[
        "profile", "resolve", "macrostrat", "deep_time", "emag2", "icgem", "intake", "scene", "sts", "reconstruct", "rift"
    ] = "profile",
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
    # P0+P1 tectonic kernel parameters (2026-07-03)
    reconstruct_mode: str = "position",
    model: str = "Merdith2021",
    models: list[str] | None = None,
    rift_mode: str = "full",
    beta: float | None = None,
    crust_initial_km: float | None = None,
    crust_current_km: float | None = None,
    time_since_rift_ma: float = 0.0,
    subsidence_rate_mm_yr: float | None = None,
) -> dict[str, Any]:
    """Unified basin intelligence — profiles, resolution, deep time, spatial context, STS state machine.

    Modes:
      profile    - Basin overview, petroleum system, stratigraphy, play fairway, risk
      resolve    - Resolve basin name to canonical ID and bounding box
      macrostrat - Macrostrat API (units, columns, lithologies, strat names, intervals, fossils, map)
      deep_time  - Deep Time State Vector (13 fields, ICS Chart v2024/12)
      emag2      - EMAG2v3 global magnetic anomaly grid
      icgem      - ICGEM gravity field models
      intake     - Natural-language query intake routing
      scene      - Spatial bbox context, CRS checks, causal scene rendering
      sts        - State Transition Surface engine. Basin = state machine, not horizon stack.
                   Sub-modes: graph, add_node, add_sts, translate, contrast, example.
                   Diachroneity default. Reality loop: observe→hypothesize→test→contrast→loop.
    """
    kwargs = locals().copy()
    if mode == "resolve":
        from geox_mcp.tools.basin import geox_basin_resolve as _impl

        return await _impl(name=kwargs.get("name", kwargs.get("basin_name", "")))

    if mode == "macrostrat":
        from geox_mcp.tools.compat import geox_query_macrostrat as _impl

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

    # ── sts — State Transition Surface engine (Phase 2.5) ──────────────────
    if mode == "sts":
        from geox_mcp.tools.sts import geox_sts as _impl

        return await _impl(
            graph_id=kwargs.get("name", kwargs.get("basin_name", "default")),
            mode=kwargs.get("sts_mode", "graph"),
            node_name=kwargs.get("node_name", ""),
            node_states=kwargs.get("node_states"),
            node_bbox=kwargs.get("node_bbox"),
            node_description=kwargs.get("node_description", ""),
            parent_basin_id=kwargs.get("parent_basin_id", ""),
            basin_node_id=kwargs.get("basin_node_id", ""),
            from_state=kwargs.get("from_state", ""),
            to_state=kwargs.get("to_state", ""),
            evidence_types=kwargs.get("evidence_types"),
            age_min_ma=kwargs.get("age_min_ma"),
            age_max_ma=kwargs.get("age_max_ma"),
            diachroneity_class=kwargs.get("diachroneity_class", "strongly_diachronous"),
            translation_schemes=kwargs.get("translation_schemes"),
            sts_confidence=kwargs.get("sts_confidence", "MED"),
            token=kwargs.get("token", ""),
            from_scheme=kwargs.get("from_scheme", ""),
            to_scheme=kwargs.get("to_scheme", ""),
            translation_id=kwargs.get("translation_id", "layang_layang"),
            sts_a_id=kwargs.get("sts_a_id", ""),
            sts_b_id=kwargs.get("sts_b_id", ""),
            contrast_metric=kwargs.get("contrast_metric", "age_Myr"),
            contrast_threshold=kwargs.get("contrast_threshold", 5.0),
            contrast_delta=kwargs.get("contrast_delta", 0.0),
            graph_name=kwargs.get("graph_name", ""),
            basin_ref_id=kwargs.get("basin_ref_id", ""),
        )

    # ── reconstruct — GPlates plate tectonic reconstruction (P0, 2026-07-03) ──
    if mode == "reconstruct":
        from geox_core.io.gplates_fetcher import (
            GPlatesFetcher,
            PlateVelocityRequest,
            ReconstructionRequest,
        )

        fetcher = GPlatesFetcher()
        _sub_mode = reconstruct_mode
        _lat = float(lat or 6.0)
        _lng = float(lng or 117.0)
        _age = float(age_ma or 23.0)
        _model = model or "Merdith2021"

        if _sub_mode == "velocity":
            v = fetcher.velocity(
                PlateVelocityRequest(
                    latitude=_lat,
                    longitude=_lng,
                    age_ma=_age,
                    model=_model,
                )
            )
            return {
                "ok": v.ok,
                "mode": v.mode,
                "velocity_cm_yr": v.velocity_cm_yr,
                "azimuth_deg": v.azimuth_deg,
                "plate_id": v.plate_id,
                "age_ma": v.age_ma,
                "model": v.model,
                "note": v.note,
                "citation": v.citation,
            }

        if _sub_mode == "multi":
            _models = models or ["Merdith2021", "Muller2019", "Seton2012"]
            results: dict[str, dict[str, Any]] = {}
            for m in _models:
                r = fetcher.reconstruct(
                    ReconstructionRequest(
                        latitude=_lat,
                        longitude=_lng,
                        age_ma=_age,
                        model=m,
                    )
                )
                if r.reconstructed_lat is not None and r.reconstructed_lon is not None:
                    results[m] = {
                        "paleo_lat": round(r.reconstructed_lat, 4),
                        "paleo_lon": round(r.reconstructed_lon, 4),
                        "plate_id": r.plate_id,
                        "mode": r.mode,
                    }
            spread_km = _model_spread(results)
            return {
                "ok": True,
                "mode": "gws_multi_model",
                "reconstructions": results,
                "model_spread_km": spread_km,
                "age_ma": _age,
                "note": f"{len(results)} models returned data",
                "citation": "Multi-model ensemble via GWS gws.gplates.org",
            }

        # Default: single point reconstruction
        r = fetcher.reconstruct(
            ReconstructionRequest(
                latitude=_lat,
                longitude=_lng,
                age_ma=_age,
                model=_model,
            )
        )
        return {
            "ok": r.ok,
            "mode": r.mode,
            "paleo_lat": r.reconstructed_lat,
            "paleo_lon": r.reconstructed_lon,
            "plate_id": r.plate_id,
            "age_ma": r.age_ma,
            "model": r.model,
            "note": r.note,
            "citation": r.citation,
        }

    # ── rift — McKenzie rift kinematics (P1, 2026-07-03) ──
    if mode == "rift":
        from geox_core.skills.subsurface.rift_kinematics import (
            compute_beta,
            compute_rift_kinematics,
        )
        from geox_core.skills.subsurface.sts_rift_bridge import (
            compute_basin_state_sequence,
        )

        # Direct β or parse from thickness
        if beta is not None:
            _beta = float(beta)
        else:
            _ti = float(crust_initial_km or 30.0)
            _tc = float(crust_current_km or 8.0)
            _beta = compute_beta(_ti, _tc)

        if rift_mode == "beta":
            return {"ok": True, "mode": "beta_only", "beta": round(_beta, 2)}

        _t_ma = float(time_since_rift_ma or 0.0)
        _sr = float(subsidence_rate_mm_yr) if subsidence_rate_mm_yr is not None else None

        if rift_mode == "sequence":
            seq = compute_basin_state_sequence(
                beta=_beta,
                time_since_rift_ma=_t_ma,
                subsidence_rate_mm_yr=_sr,
            )
            return {"ok": True, "mode": "basin_state_sequence", **seq}

        # Default: full kinematics
        rk = compute_rift_kinematics(
            crust_thickness_initial_km=float(crust_initial_km or 30.0),
            crust_thickness_current_km=float(crust_current_km or 8.0),
            time_since_rift_ma=_t_ma,
            subsidence_rate_mm_yr=_sr,
        )
        return {
            "ok": True,
            "mode": "rift_kinematics",
            "beta": rk.beta,
            "initial_subsidence_km": rk.initial_subsidence_km,
            "thermal_subsidence_km": rk.thermal_subsidence_km,
            "total_subsidence_km": rk.total_subsidence_km,
            "crust_thinning_factor": rk.crust_thinning_factor,
            "rift_phase": rk.rift_phase.value,
            "confidence": rk.confidence,
            "epistemic_label": rk.epistemic_label,
            "alternative_phases": [a.value for a in rk.alternative_phases],
            "evidence_gaps": rk.evidence_gaps,
            "note": rk.note,
        }

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
