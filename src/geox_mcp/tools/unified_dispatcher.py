import logging
import inspect
from typing import Any

logger = logging.getLogger("geox.mcp.unified_dispatcher")


async def _call_impl(impl: Any, args: dict[str, Any], session_id: str | None, actor_id: str | None, trace_id: str | None) -> Any:
    from geox_mcp.server import _safe_forward

    # Filter arguments to match target implementation signature
    forwarded = _safe_forward(impl, args, session_id=session_id, actor_id=actor_id, trace_id=trace_id)
    if inspect.iscoroutinefunction(impl):
        return await impl(**forwarded)
    else:
        return impl(**forwarded)


# ── geox_observe ──
async def geox_observe(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Query any earth data.
    Modes: well_ingest, well_qc, well_desurvey, seismic_ingest, atlas, earth_map, earth_obs,
    earth_surface, earth_surface_2, dst, earthquake_catalog, relief_ingest, bathymetry_ingest,
    heatflow_query, stress_query, geochem_query, plate_reconstruct, paleomag_query,
    gravity_change_query, ocean_query, erddap_query, climate_reanalysis, hydrology_query,
    satellite_catalog, uk_petroleum_query, geology_map_query, space_weather.
    """
    args = arguments or {}
    if mode == "well_ingest":
        from geox_mcp.tools.well_ingest import geox_well_ingest

        return await _call_impl(geox_well_ingest, args, session_id, actor_id, trace_id)
    elif mode == "well_qc":
        from geox_mcp.tools.well_qc import geox_well_qc

        return await _call_impl(geox_well_qc, args, session_id, actor_id, trace_id)
    elif mode == "well_desurvey":
        from geox_mcp.tools.well_desurvey import geox_well_desurvey

        return await _call_impl(geox_well_desurvey, args, session_id, actor_id, trace_id)
    elif mode == "seismic_ingest":
        from geox_mcp.tools.seismic_ingest import geox_seismic_ingest

        return await _call_impl(geox_seismic_ingest, args, session_id, actor_id, trace_id)
    elif mode == "atlas":
        from geox_mcp.tools.geox_atlas import geox_atlas

        return await _call_impl(geox_atlas, args, session_id, actor_id, trace_id)
    elif mode == "earthquake_catalog":
        from geox_mcp.tools.earth_surface import geox_earthquake_catalog

        return await _call_impl(geox_earthquake_catalog, args, session_id, actor_id, trace_id)
    elif mode == "relief_ingest":
        from geox_mcp.tools.earth_surface import geox_relief_ingest

        return await _call_impl(geox_relief_ingest, args, session_id, actor_id, trace_id)
    elif mode == "bathymetry_ingest":
        from geox_mcp.tools.earth_surface import geox_bathymetry_ingest

        return await _call_impl(geox_bathymetry_ingest, args, session_id, actor_id, trace_id)
    elif mode == "heatflow_query":
        from geox_mcp.tools.earth_surface_2 import geox_heatflow_query

        return await _call_impl(geox_heatflow_query, args, session_id, actor_id, trace_id)
    elif mode == "stress_query":
        from geox_mcp.tools.earth_surface_2 import geox_stress_query

        return await _call_impl(geox_stress_query, args, session_id, actor_id, trace_id)
    elif mode == "geochem_query":
        from geox_mcp.tools.earth_surface_2 import geox_geochem_query

        return await _call_impl(geox_geochem_query, args, session_id, actor_id, trace_id)
    elif mode == "plate_reconstruct":
        from geox_mcp.tools.earth_surface_2 import geox_plate_reconstruct

        return await _call_impl(geox_plate_reconstruct, args, session_id, actor_id, trace_id)
    elif mode == "paleomag_query":
        from geox_mcp.tools.earth_surface_2 import geox_paleomag_query

        return await _call_impl(geox_paleomag_query, args, session_id, actor_id, trace_id)
    elif mode == "gravity_change_query":
        from geox_mcp.tools.earth_surface_2 import geox_gravity_change_query

        return await _call_impl(geox_gravity_change_query, args, session_id, actor_id, trace_id)
    elif mode == "ocean_query":
        from geox_mcp.tools.earth_surface_2 import geox_ocean_query

        return await _call_impl(geox_ocean_query, args, session_id, actor_id, trace_id)
    elif mode == "erddap_query":
        from geox_mcp.tools.earth_surface_2 import geox_erddap_query

        return await _call_impl(geox_erddap_query, args, session_id, actor_id, trace_id)
    elif mode == "climate_reanalysis":
        from geox_mcp.tools.earth_surface_2 import geox_climate_reanalysis

        return await _call_impl(geox_climate_reanalysis, args, session_id, actor_id, trace_id)
    elif mode == "hydrology_query":
        from geox_mcp.tools.earth_surface_2 import geox_hydrology_query

        return await _call_impl(geox_hydrology_query, args, session_id, actor_id, trace_id)
    elif mode == "satellite_catalog":
        from geox_mcp.tools.earth_surface_2 import geox_satellite_catalog

        return await _call_impl(geox_satellite_catalog, args, session_id, actor_id, trace_id)
    elif mode == "uk_petroleum_query":
        from geox_mcp.tools.earth_surface_2 import geox_uk_petroleum_query

        return await _call_impl(geox_uk_petroleum_query, args, session_id, actor_id, trace_id)
    elif mode == "geology_map_query":
        from geox_mcp.tools.earth_surface_2 import geox_geology_map_query

        return await _call_impl(geox_geology_map_query, args, session_id, actor_id, trace_id)
    elif mode == "space_weather":
        from geox_mcp.tools.earth_surface_2 import geox_space_weather

        return await _call_impl(geox_space_weather, args, session_id, actor_id, trace_id)
    elif mode == "deep_time":
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        return await _call_impl(geox_deep_time_state, args, session_id, actor_id, trace_id)
    elif mode == "basin_profile":
        from geox_mcp.tools.basin_unified import geox_basin

        args.setdefault("mode", "profile")
        return await _call_impl(geox_basin, args, session_id, actor_id, trace_id)
    elif mode == "macrostrat":
        from geox_mcp.tools.basin_unified import geox_basin

        args.setdefault("mode", "macrostrat")
        return await _call_impl(geox_basin, args, session_id, actor_id, trace_id)
    elif mode == "earth_obs":
        from geox_mcp.tools.earth_surface import geox_earth_obs

        return await _call_impl(geox_earth_obs, args, session_id, actor_id, trace_id)
    elif mode == "earth_map":
        from geox_mcp.tools.earth_surface import geox_earth_map

        return await _call_impl(geox_earth_map, args, session_id, actor_id, trace_id)
    elif mode == "earth_surface":
        from geox_mcp.tools.earth_surface import geox_earth_surface

        return await _call_impl(geox_earth_surface, args, session_id, actor_id, trace_id)
    elif mode == "earth_surface_2":
        from geox_mcp.tools.earth_surface_2 import geox_earth_surface_2

        return await _call_impl(geox_earth_surface_2, args, session_id, actor_id, trace_id)
    elif mode == "dst":
        from geox_mcp.tools.earth_surface import geox_dst_ingest_test

        return await _call_impl(geox_dst_ingest_test, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_observe: {mode}")


# ── geox_compute ──
async def geox_compute(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Transform earth data.
    Modes: petrophysics, geomechanics, seismic_compute, seismic_compute_attribute, horizon_contrast, lem
    """
    args = arguments or {}
    if mode == "petrophysics":
        from geox_mcp.tools.petrophysics_unified import geox_petrophysics

        return await _call_impl(geox_petrophysics, args, session_id, actor_id, trace_id)
    elif mode == "geomechanics":
        from geox_mcp.tools.geomechanics_unified import geox_geomechanics

        return await _call_impl(geox_geomechanics, args, session_id, actor_id, trace_id)
    elif mode == "seismic_compute":
        from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute

        return await _call_impl(geox_seismic_compute, args, session_id, actor_id, trace_id)
    elif mode == "seismic_compute_attribute":
        from geox_mcp.tools.seismic_compute_unified import geox_seismic_compute_attribute_tool

        return await _call_impl(geox_seismic_compute_attribute_tool, args, session_id, actor_id, trace_id)
    elif mode == "horizon_contrast":
        from geox_mcp.tools.horizon_contrast import geox_horizon_contrast

        return await _call_impl(geox_horizon_contrast, args, session_id, actor_id, trace_id)
    elif mode == "lem":
        from geox_mcp.tools.lem_predict import geox_lem_predict

        return await _call_impl(geox_lem_predict, args, session_id, actor_id, trace_id)
    elif mode == "contrast_detect":
        from geox_mcp.tools.contrast_detect import contrast_detect

        return await _call_impl(contrast_detect, args, session_id, actor_id, trace_id)
    elif mode == "gravity_screen":
        from geox_core.engines.geophysics.harmonica_adapter import gravity_screen

        return await _call_impl(gravity_screen, args, session_id, actor_id, trace_id)
    elif mode == "rock_physics":
        from geox.egs.tools.compute import geox_egs_rock_physics

        return await _call_impl(geox_egs_rock_physics, args, session_id, actor_id, trace_id)
    elif mode == "spatial_intersection":
        from geox_mcp.tools.geox_spatial_intersection import geox_spatial_intersection

        return await _call_impl(geox_spatial_intersection, args, session_id, actor_id, trace_id)
    elif mode == "block_spec":
        from geox_mcp.tools.geox_block_spec import geox_block_spec

        return await _call_impl(geox_block_spec, args, session_id, actor_id, trace_id)
    elif mode == "desurvey":
        from geox_mcp.tools.well_desurvey import geox_well_desurvey

        return await _call_impl(geox_well_desurvey, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_compute: {mode}")


# ── geox_model ──
async def geox_model(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Simulate earth process.
    Modes: basin, deep_time, simulate_accommodation, simulate_surfaces, simulate_sequences, simulate_routing, 3d_model, 3d_model_build, forward_model_synthetic
    """
    args = arguments or {}
    if mode == "basin":
        from geox_mcp.tools.basin_unified import geox_basin

        return await _call_impl(geox_basin, args, session_id, actor_id, trace_id)
    elif mode == "deep_time":
        from geox_mcp.tools.deep_time_state import geox_deep_time_state

        return await _call_impl(geox_deep_time_state, args, session_id, actor_id, trace_id)
    elif mode == "simulate_accommodation":
        from geox_core.engines.stratigraphy.accommodation import simulate_accommodation

        return await _call_impl(simulate_accommodation, args, session_id, actor_id, trace_id)
    elif mode == "simulate_surfaces":
        from geox_core.engines.stratigraphy.surfaces import simulate_surfaces

        return await _call_impl(simulate_surfaces, args, session_id, actor_id, trace_id)
    elif mode == "simulate_sequences":
        from geox_core.engines.stratigraphy.sequences import simulate_sequences

        return await _call_impl(simulate_sequences, args, session_id, actor_id, trace_id)
    elif mode == "simulate_routing":
        from geox_core.engines.stratigraphy.sediment_routing import simulate_routing

        return await _call_impl(simulate_routing, args, session_id, actor_id, trace_id)
    elif mode == "3d_model":
        from geox_mcp.tools.geox_3d_modeling_gempy_async import geox_3d_model

        return await _call_impl(geox_3d_model, args, session_id, actor_id, trace_id)
    elif mode == "3d_model_build":
        from geox_core.engines.modeling.gempy import build_3d_model

        return await _call_impl(build_3d_model, args, session_id, actor_id, trace_id)
    elif mode == "forward_model_synthetic":
        from geox_mcp.tools.forward_model_synthetic import geox_forward_model_synthetic

        return await _call_impl(geox_forward_model_synthetic, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_model: {mode}")


# ── geox_interpret ──
async def geox_interpret(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Geological cognition.
    Modes: sequence, seismic_interpret, seismic_inversion, seismic_cognition, vision, visual_understand,
    visual_enhance, visual_generate_hypotheses, cognitive_rank_hypotheses, rsi, physical_reality,
    biostrat_parse, biostrat_nn_age, biostrat_ruling_check, biostrat_falsify, well_tie, well_tie_compute,
    macrostrat_calibrate, geological_cognition_run, panel_d_render
    """
    args = arguments or {}
    if mode == "sequence":
        from geox_mcp.tools.sequence_unified import geox_sequence

        return await _call_impl(geox_sequence, args, session_id, actor_id, trace_id)
    elif mode == "seismic_interpret":
        from geox_mcp.tools.seismic_interpret import geox_seismic_interpret

        return await _call_impl(geox_seismic_interpret, args, session_id, actor_id, trace_id)
    elif mode == "seismic_inversion":
        from geox_mcp.tools.seismic_inversion import geox_seismic_inversion

        return await _call_impl(geox_seismic_inversion, args, session_id, actor_id, trace_id)
    elif mode == "seismic_cognition":
        from geox_core.engines.seismic.cognition import run_seismic_cognition

        return await _call_impl(run_seismic_cognition, args, session_id, actor_id, trace_id)
    elif mode == "vision":
        from geox_mcp.tools.vision_unified import geox_vision

        return await _call_impl(geox_vision, args, session_id, actor_id, trace_id)
    elif mode == "visual_understand":
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_understand_async

        return await _call_impl(geox_visual_understand_async, args, session_id, actor_id, trace_id)
    elif mode == "visual_enhance":
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_enhance_async

        return await _call_impl(geox_visual_enhance_async, args, session_id, actor_id, trace_id)
    elif mode == "visual_generate_hypotheses":
        from geox_mcp.tools.seismic_vision_ai_async import geox_visual_generate_hypotheses_async

        return await _call_impl(geox_visual_generate_hypotheses_async, args, session_id, actor_id, trace_id)
    elif mode == "cognitive_rank_hypotheses":
        from geox_mcp.tools.geox_geological_cognition_async import geox_cognitive_rank_hypotheses

        return await _call_impl(geox_cognitive_rank_hypotheses, args, session_id, actor_id, trace_id)
    elif mode == "rsi":
        from geox_mcp.tools.seismic_rsi import geox_rsi_interpret

        return await _call_impl(geox_rsi_interpret, args, session_id, actor_id, trace_id)
    elif mode == "physical_reality":
        from geox_mcp.tools.geox_physical_reality_async import geox_physical_reality_interpret

        return await _call_impl(geox_physical_reality_interpret, args, session_id, actor_id, trace_id)
    elif mode == "biostrat_parse":
        from geox_mcp.tools.biostrat_parse import geox_biostrat_parse

        return await _call_impl(geox_biostrat_parse, args, session_id, actor_id, trace_id)
    elif mode == "biostrat_nn_age":
        from geox_mcp.tools.biostrat_nn_age import geox_biostrat_nn_age

        return await _call_impl(geox_biostrat_nn_age, args, session_id, actor_id, trace_id)
    elif mode == "biostrat_ruling_check":
        from geox_mcp.tools.biostrat_ruling_check import geox_biostrat_ruling_check

        return await _call_impl(geox_biostrat_ruling_check, args, session_id, actor_id, trace_id)
    elif mode == "biostrat_falsify":
        from geox_mcp.tools.biostrat_falsify import geox_biostrat_falsify

        return await _call_impl(geox_biostrat_falsify, args, session_id, actor_id, trace_id)
    elif mode == "well_tie":
        from geox_mcp.tools.geox_well_tie_bruges_async import geox_well_tie

        return await _call_impl(geox_well_tie, args, session_id, actor_id, trace_id)
    elif mode == "well_tie_compute":
        from geox_core.engines.well.tie import compute_well_tie

        return await _call_impl(compute_well_tie, args, session_id, actor_id, trace_id)
    elif mode == "macrostrat_calibrate":
        from geox_mcp.tools.macrostrat_calibrate import geox_macrostrat_calibrate

        return await _call_impl(geox_macrostrat_calibrate, args, session_id, actor_id, trace_id)
    elif mode == "geological_cognition_run":
        from geox_core.engines.geology.cognition import run_geological_cognition

        return await _call_impl(run_geological_cognition, args, session_id, actor_id, trace_id)
    elif mode == "panel_d_render":
        from geox_mcp.tools.seismic_vision_ai_async import geox_panel_d_render_async

        return await _call_impl(geox_panel_d_render_async, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_interpret: {mode}")


# ── geox_spatial ──
async def geox_spatial(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Geometry & maps.
    Modes: spatial_intersection, block_spec, map_layers_list, map_scene_plan, map_render_preview, map_export_package
    """
    args = arguments or {}
    if mode == "spatial_intersection":
        from geox_mcp.tools.spatial_intersection import geox_spatial_intersection

        return await _call_impl(geox_spatial_intersection, args, session_id, actor_id, trace_id)
    elif mode == "block_spec":
        from geox_mcp.tools.block_spec import geox_block_spec

        return await _call_impl(geox_block_spec, args, session_id, actor_id, trace_id)
    elif mode == "map_layers_list":
        from geox_core.engines.mapping.layers import list_layers

        return await _call_impl(list_layers, args, session_id, actor_id, trace_id)
    elif mode == "map_scene_plan":
        from geox_core.engines.mapping.scene import plan_scene

        return await _call_impl(plan_scene, args, session_id, actor_id, trace_id)
    elif mode == "map_render_preview":
        from geox_core.engines.mapping.preview import render_preview

        return await _call_impl(render_preview, args, session_id, actor_id, trace_id)
    elif mode == "map_export_package":
        from geox_core.engines.mapping.export import export_package

        return await _call_impl(export_package, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_spatial: {mode}")


# ── geox_govern ──
async def geox_govern(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Claims & evidence.
    Modes: claim, evidence, doctrine, egs_query_entity, egs_query_claim, egs_query_uncertainty,
    egs_query_provenance, egs_claim_create, egs_claim_challenge, egs_evidence_attach, egs_evidence_reason,
    egs_seismic_compute, egs_scenario_audit, forbidden_claims_scan
    """
    args = arguments or {}
    if mode == "claim":
        from geox_mcp.tools.claim_unified import geox_claim

        return await _call_impl(geox_claim, args, session_id, actor_id, trace_id)
    elif mode == "evidence":
        from geox_mcp.tools.evidence_unified import geox_evidence

        return await _call_impl(geox_evidence, args, session_id, actor_id, trace_id)
    elif mode == "doctrine":
        from geox_mcp.tools.doctrine_unified import geox_doctrine

        return await _call_impl(geox_doctrine, args, session_id, actor_id, trace_id)
    elif mode == "egs_query_entity":
        from geox_core.engines.egs.query import query_entity

        return await _call_impl(query_entity, args, session_id, actor_id, trace_id)
    elif mode == "egs_query_claim":
        from geox_core.engines.egs.query import query_claim

        return await _call_impl(query_claim, args, session_id, actor_id, trace_id)
    elif mode == "egs_query_uncertainty":
        from geox_core.engines.egs.query import query_uncertainty

        return await _call_impl(query_uncertainty, args, session_id, actor_id, trace_id)
    elif mode == "egs_query_provenance":
        from geox_core.engines.egs.query import query_provenance

        return await _call_impl(query_provenance, args, session_id, actor_id, trace_id)
    elif mode == "egs_claim_create":
        from geox_core.engines.egs.claim import create_claim

        return await _call_impl(create_claim, args, session_id, actor_id, trace_id)
    elif mode == "egs_claim_challenge":
        from geox_core.engines.egs.claim import challenge_claim

        return await _call_impl(challenge_claim, args, session_id, actor_id, trace_id)
    elif mode == "egs_evidence_attach":
        from geox_core.engines.egs.evidence import attach_evidence

        return await _call_impl(attach_evidence, args, session_id, actor_id, trace_id)
    elif mode == "egs_evidence_reason":
        from geox_core.engines.egs.evidence import reason_evidence

        return await _call_impl(reason_evidence, args, session_id, actor_id, trace_id)
    elif mode == "egs_seismic_compute":
        from geox_core.engines.egs.seismic import compute_seismic

        return await _call_impl(compute_seismic, args, session_id, actor_id, trace_id)
    elif mode == "egs_scenario_audit":
        from geox_core.engines.egs.scenario import audit_scenario

        return await _call_impl(audit_scenario, args, session_id, actor_id, trace_id)
    elif mode == "forbidden_claims_scan":
        from geox_mcp.tools.forbidden_claims import scan_forbidden_claims

        return await _call_impl(scan_forbidden_claims, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_govern: {mode}")


# ── geox_bridge ──
async def geox_bridge(
    mode: str,
    arguments: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Cross-organ integration.
    Modes: wealth_bridge_run, wealth_consequence, prospect, judgment_preflight
    """
    args = arguments or {}
    if mode == "wealth_bridge_run":
        from geox_core.engines.wealth.bridge import run_wealth_bridge

        return await _call_impl(run_wealth_bridge, args, session_id, actor_id, trace_id)
    elif mode == "wealth_consequence":
        from geox_mcp.tools.geox_wealth_bridge_async import geox_wealth_consequence

        return await _call_impl(geox_wealth_consequence, args, session_id, actor_id, trace_id)
    elif mode == "prospect":
        from geox_mcp.tools.prospect_unified import geox_prospect

        return await _call_impl(geox_prospect, args, session_id, actor_id, trace_id)
    elif mode == "judgment_preflight":
        from geox_core.engines.judgment.preflight import run_preflight

        return await _call_impl(run_preflight, args, session_id, actor_id, trace_id)
    else:
        raise ValueError(f"Unknown mode for geox_bridge: {mode}")
