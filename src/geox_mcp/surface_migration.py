from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from geox_mcp.registry import LEGACY_ALIAS_TOOLS, LEGACY_SURFACE_TOOLS


@dataclass(frozen=True)
class MigrationRoute:
    tool: str
    mode: str
    arguments: dict[str, Any] = field(default_factory=dict)


def _route(tool: str, mode: str, arguments: dict[str, Any] | None = None, **extra_arguments: Any) -> MigrationRoute:
    payload = dict(arguments or {})
    payload.update(extra_arguments)
    return MigrationRoute(tool=tool, mode=mode, arguments=payload)


LEGACY_SURFACE_ROUTE_MAP: dict[str, MigrationRoute] = {
    "geox_well_ingest": _route("geox_observe", "well_ingest"),
    "geox_well_qc": _route("geox_observe", "well_qc"),
    "geox_well_desurvey": _route("geox_observe", "well_desurvey"),
    "geox_petrophysics": _route("geox_compute", "petrophysics"),
    "geox_sequence": _route("geox_interpret", "sequence"),
    "geox_simulate_accommodation": _route("geox_model", "accommodation"),
    "geox_simulate_surfaces": _route("geox_model", "surfaces"),
    "geox_simulate_sequences": _route("geox_model", "sequences"),
    "geox_simulate_routing": _route("geox_model", "routing"),
    "geox_seismic_ingest": _route("geox_observe", "seismic_ingest"),
    "geox_seismic_compute": _route("geox_compute", "seismic_compute"),
    "geox_seismic_interpret": _route("geox_interpret", "seismic_interpret"),
    "geox_rsi_interpret": _route("geox_interpret", "rsi_interpret"),
    "geox_render_audit": _route("geox_interpret", "render_audit"),
    "geox_physical_reality_interpret": _route("geox_interpret", "physical_reality"),
    "geox_geological_cognition_run": _route("geox_interpret", "geological_cognition_run"),
    "geox_panel_d_render_mcp": _route("geox_interpret", "panel_d_render_mcp"),
    "geox_segy_trace_audit": _route("geox_interpret", "segy_trace_audit"),
    "geox_well_tie_compute": _route("geox_interpret", "well_tie_compute"),
    "geox_3d_model_build": _route("geox_model", "3d_model"),
    "geox_wealth_bridge_run": _route("geox_bridge", "wealth_bridge_run"),
    "geox_vision": _route("geox_interpret", "vision"),
    "geox_subsurface_model": _route("geox_model", "subsurface"),
    "geox_geomechanics": _route("geox_compute", "geomechanics"),
    # geox_basin and geox_deep_time_state have their own FastMCP @mcp.tool() registrations
    # in tools_wiring.py and server.py respectively. Migration routes would intercept
    # and rewrite tool names, breaking the direct registrations. No migration needed.
    # "geox_basin": _route("geox_model", "basin"),
    # "geox_deep_time_state": _route("geox_model", "deep_time"),
    "geox_biostrat_parse": _route("geox_interpret", "biostrat_parse"),
    "geox_biostrat_nn_age": _route("geox_interpret", "biostrat_nn_age"),
    "geox_biostrat_ruling_check": _route("geox_interpret", "biostrat_ruling_check"),
    "geox_biostrat_falsify": _route("geox_interpret", "biostrat_falsify"),
    "geox_macrostrat_calibrate": _route("geox_interpret", "macrostrat_calibrate"),
    # geox_atlas has its own @mcp.tool registration in server.py — no migration needed
    # "geox_atlas": _route("geox_observe", "atlas"),
    "geox_spatial_intersection": _route("geox_spatial", "spatial_intersection"),
    "geox_block_spec": _route("geox_spatial", "block_spec"),
    "geox_map_layers_list": _route("geox_spatial", "map_layers_list"),
    "geox_map_scene_plan": _route("geox_spatial", "map_scene_plan"),
    "geox_map_render_preview": _route("geox_spatial", "map_render_preview"),
    "geox_map_export_package": _route("geox_spatial", "map_export_package"),
    "geox_forbidden_claims_scan": _route("geox_govern", "forbidden_claims_scan"),
    "geox_egs_query_entity": _route("geox_govern", "egs_query_entity"),
    "geox_egs_query_claim": _route("geox_govern", "egs_query_claim"),
    "geox_egs_query_uncertainty": _route("geox_govern", "egs_query_uncertainty"),
    "geox_egs_query_provenance": _route("geox_govern", "egs_query_provenance"),
    "geox_egs_claim_create": _route("geox_govern", "egs_claim_create"),
    "geox_egs_claim_challenge": _route("geox_govern", "egs_claim_challenge"),
    "geox_egs_evidence_attach": _route("geox_govern", "egs_evidence_attach"),
    "geox_egs_evidence_reason": _route("geox_govern", "egs_evidence_reason"),
    "geox_egs_seismic_compute": _route("geox_govern", "egs_seismic_compute"),
    "geox_egs_rock_physics": _route("geox_compute", "rock_physics"),
    "geox_egs_data_qc_bundle": _route("geox_govern", "egs_scenario_audit"),
    "geox_egs_scenario_audit": _route("geox_govern", "egs_scenario_audit"),
    "geox_visual_understand": _route("geox_interpret", "visual_understand"),
    "geox_visual_enhance": _route("geox_interpret", "visual_enhance"),
    "geox_visual_generate_hypotheses": _route("geox_interpret", "visual_generate_hypotheses"),
    "geox_panel_d_render": _route("geox_interpret", "panel_d_render"),
    "geox_panel_d_render_mcp": _route("geox_interpret", "panel_d_render"),
    "geox_render_audit": _route("geox_interpret", "rsi"),
    "geox_rsi_interpret": _route("geox_interpret", "rsi"),
    "geox_segy_audit": _route("geox_interpret", "segy_audit"),
    "geox_segy_trace_audit": _route("geox_interpret", "segy_trace_audit"),
    "geox_3d_model": _route("geox_model", "3d_model"),
    "geox_wealth_consequence": _route("geox_bridge", "wealth_consequence"),
    "geox_seismic_cognition": _route("geox_interpret", "seismic_cognition"),
    "geox_contrast_detect": _route("geox_compute", "contrast_detect"),
    "geox_earthquake_catalog": _route("geox_observe", "earthquake_catalog"),
    "geox_relief_ingest": _route("geox_observe", "relief_ingest"),
    "geox_bathymetry_ingest": _route("geox_observe", "bathymetry_ingest"),
    "geox_heatflow_query": _route("geox_observe", "heatflow_query"),
    "geox_stress_query": _route("geox_observe", "stress_query"),
    "geox_geochem_query": _route("geox_observe", "geochem_query"),
    "geox_plate_reconstruct": _route("geox_observe", "plate_reconstruct"),
    "geox_paleomag_query": _route("geox_observe", "paleomag_query"),
    "geox_gravity_change_query": _route("geox_observe", "gravity_change_query"),
    "geox_gravity_screen": _route("geox_compute", "gravity_screen"),
    "geox_ocean_query": _route("geox_observe", "ocean_query"),
    "geox_erddap_query": _route("geox_observe", "erddap_query"),
    "geox_climate_reanalysis": _route("geox_observe", "climate_reanalysis"),
    "geox_hydrology_query": _route("geox_observe", "hydrology_query"),
    "geox_satellite_catalog": _route("geox_observe", "satellite_catalog"),
    "geox_uk_petroleum_query": _route("geox_observe", "uk_petroleum_query"),
    "geox_geology_map_query": _route("geox_observe", "geology_map_query"),
    "geox_space_weather": _route("geox_observe", "space_weather"),
    "geox_judgment_preflight": _route("geox_bridge", "judgment_preflight"),
}


LEGACY_ALIAS_ROUTE_MAP: dict[str, MigrationRoute] = {
    "geox_data_ingest_bundle": _route("geox_observe", "well_ingest", arguments={"mode": "auto"}),
    "geox_data_qc_bundle": _route("geox_observe", "well_qc"),
    "geox_dst_ingest_test": _route("geox_observe", "well_ingest", arguments={"mode": "dst"}),
    "geox_header_inspect": _route("geox_observe", "well_ingest", arguments={"mode": "header"}),
    "geox_las_inspect": _route("geox_observe", "well_ingest", arguments={"mode": "las"}),
    "geox_seismic_segy_inspect": _route("geox_observe", "seismic_ingest", arguments={"mode": "inspect_segy"}),
    "geox_evidence_discover": _route("geox_govern", "evidence", arguments={"mode": "discover"}),
    "geox_subsurface_generate_candidates": _route("geox_compute", "petrophysics", arguments={"mode": "generate"}),
    "geox_subsurface_verify_integrity": _route("geox_compute", "petrophysics", arguments={"mode": "verify"}),
    "geox_sequence_interpret": _route("geox_interpret", "sequence"),
    "geox_evidence_reason": _route("geox_govern", "evidence", arguments={"mode": "synthesize"}),
    "geox_prospect_evaluate": _route("geox_bridge", "prospect_evaluate"),
    "geox_map_context_scene": _route("geox_spatial", "map_scene"),
    "geox_horizon_contrast_surface": _route("geox_interpret", "seismic_interpret", arguments={"mode": "horizon_contrast"}),
    "geox_coord_transform_tool": _route("geox_compute", "geomechanics", arguments={"mode": "coord_transform"}),
    "geox_blockspace_resolution_tool": _route("geox_compute", "geomechanics", arguments={"mode": "blockspace"}),
    "geox_volume_frame_tool": _route("geox_interpret", "seismic_interpret", arguments={"mode": "volume_frame"}),
    "geox_seismic_compute_attribute_tool": _route("geox_compute", "seismic_compute", arguments={"mode": "attribute"}),
    "geox_fault_stick_ingest_tool": _route("geox_interpret", "seismic_interpret", arguments={"mode": "fault_sticks"}),
    "geox_attribute_registry_list_tool": _route("geox_compute", "seismic_compute", arguments={"mode": "attribute"}),
    "geox_blend_volume_tool": _route("geox_interpret", "seismic_interpret", arguments={"mode": "blend"}),
    "geox_segy_export_tool": _route("geox_observe", "seismic_ingest", arguments={"mode": "export_segy"}),
    "geox_claim_create": _route("geox_govern", "claim", arguments={"mode": "create"}),
    "geox_claim_validate": _route("geox_govern", "claim", arguments={"mode": "validate"}),
    "geox_claim_challenge": _route("geox_govern", "claim", arguments={"mode": "challenge"}),
    "geox_evidence_attach": _route("geox_govern", "claim", arguments={"mode": "attach_evidence"}),
    "geox_claim_seal": _route("geox_govern", "claim", arguments={"mode": "seal"}),
    "geox_basin_resolve": _route("geox_model", "basin", arguments={"mode": "resolve"}),
    "geox_basin_profile": _route("geox_model", "basin", arguments={"mode": "profile"}),
    "geox_query_intake": _route("geox_model", "basin", arguments={"mode": "intake"}),
    "geox_abstraction_guard": _route("geox_govern", "doctrine", arguments={"mode": "abstraction_guard"}),
    "geox_literature_ingest": _route("geox_govern", "evidence", arguments={"mode": "ingest_literature"}),
    "geox_vision_perceptual_inventory": _route("geox_interpret", "vision", arguments={"mode": "perceptual"}),
    "geox_vision_minimax_inference": _route("geox_interpret", "vision", arguments={"mode": "infer_minimax"}),
    "geox_vision_calibrate": _route("geox_interpret", "vision", arguments={"mode": "calibrate"}),
    "geox_vision_audit": _route("geox_interpret", "vision", arguments={"mode": "audit"}),
    "geox_query_macrostrat": _route("geox_model", "basin", arguments={"mode": "macrostrat"}),
    "geox_doctrine_assumption_register": _route("geox_govern", "doctrine", arguments={"mode": "assumption_register"}),
    "geox_doctrine_anti_beautiful_one": _route("geox_govern", "doctrine", arguments={"mode": "anti_beautiful_one"}),
    "geox_doctrine_godel_review": _route("geox_govern", "doctrine", arguments={"mode": "godel_review"}),
    "geox_prithvi_eo_inference": _route("geox_govern", "doctrine", arguments={"mode": "prithvi_eo"}),
    "geox_gravity_magnetic_forward": _route("geox_model", "subsurface", arguments={"mode": "gravity_magnetic"}),
    "geox_emag2_ingest": _route("geox_model", "basin", arguments={"mode": "emag2"}),
    "geox_icgem_models": _route("geox_model", "basin", arguments={"mode": "icgem"}),
    "geox_joint_inversion": _route("geox_model", "subsurface", arguments={"mode": "joint_inversion"}),
    "geox_mt_forward": _route("geox_model", "subsurface", arguments={"mode": "mt_forward"}),
    "geox_biostrat_constraint": _route("geox_govern", "doctrine", arguments={"mode": "biostrat"}),
    "geox_seismic_inversion": _route("geox_interpret", "seismic_inversion"),
    "geox_lem_predict": _route("geox_compute", "petrophysics", arguments={"mode": "lem_inference"}),
    "geox_system_registry_status": _route("geox_surface_status", "registry"),
}


SUPPORTED_TOP_LEVEL_MODES: dict[str, set[str]] = {
    "geox_observe": {
        "well_ingest",
        "well_qc",
        "well_desurvey",
        "seismic_ingest",
        "atlas",
        "earthquake_catalog",
        "relief_ingest",
        "bathymetry_ingest",
        "heatflow_query",
        "stress_query",
        "geochem_query",
        "plate_reconstruct",
        "paleomag_query",
        "gravity_change_query",
        "ocean_query",
        "erddap_query",
        "climate_reanalysis",
        "hydrology_query",
        "satellite_catalog",
        "uk_petroleum_query",
        "geology_map_query",
        "space_weather",
        "deep_time",
        "basin_profile",
        "macrostrat",
        "earth_obs",
        "earth_map",
        "earth_surface",
        "earth_surface_2",
        "dst",
    },
    "geox_compute": {
        "petrophysics",
        "geomechanics",
        "seismic_compute",
        "rock_physics",
        "contrast_detect",
        "gravity_screen",
        "spatial_intersection",
        "block_spec",
        "desurvey",
    },
    "geox_model": {"basin", "accommodation", "surfaces", "sequences", "routing", "3d_model", "subsurface"},
    "geox_interpret": {
        "sequence",
        "seismic_interpret",
        "seismic_inversion",
        "vision",
        "visual_understand",
        "visual_enhance",
        "visual_generate_hypotheses",
        "panel_d_render",
        "panel_d_render_mcp",
        "rsi_interpret",
        "render_audit",
        "physical_reality",
        "geological_cognition_run",
        "cognitive_rank_hypotheses",
        "seismic_cognition",
        "segy_audit",
        "segy_trace_audit",
        "well_tie",
        "well_tie_compute",
        "biostrat_parse",
        "biostrat_nn_age",
        "biostrat_ruling_check",
        "biostrat_falsify",
        "macrostrat_calibrate",
    },
    "geox_spatial": {
        "map_layers_list",
        "map_scene_plan",
        "map_render_preview",
        "map_export_package",
        "spatial_intersection",
        "block_spec",
    },
    "geox_govern": {
        "egs_query_entity",
        "egs_query_claim",
        "egs_query_uncertainty",
        "egs_query_provenance",
        "egs_claim_create",
        "egs_claim_challenge",
        "egs_evidence_attach",
        "egs_evidence_reason",
        "egs_seismic_compute",
        "egs_scenario_audit",
        "egs_data_qc",
        "egs_data_qc_bundle",
        "claim",
        "evidence",
        "prospect",
        "doctrine",
        "forbidden_claims",
        "forbidden_claims_scan",
    },
    "geox_bridge": {"wealth_bridge_run", "wealth_consequence", "prospect", "prospect_evaluate", "judgment_preflight"},
    "geox_surface_status": {"registry", "health"},
}


def all_legacy_routes() -> dict[str, MigrationRoute]:
    return {**LEGACY_SURFACE_ROUTE_MAP, **LEGACY_ALIAS_ROUTE_MAP}


def audit_surface_migration() -> list[str]:
    errors: list[str] = []

    missing_surface = set(LEGACY_SURFACE_TOOLS) - set(LEGACY_SURFACE_ROUTE_MAP)
    missing_alias = set(LEGACY_ALIAS_TOOLS) - set(LEGACY_ALIAS_ROUTE_MAP)
    if missing_surface:
        errors.append(f"missing legacy surface routes: {sorted(missing_surface)}")
    if missing_alias:
        errors.append(f"missing legacy alias routes: {sorted(missing_alias)}")

    for legacy_name, route in all_legacy_routes().items():
        allowed_modes = SUPPORTED_TOP_LEVEL_MODES.get(route.tool)
        if allowed_modes is None:
            errors.append(f"{legacy_name}: unknown target tool {route.tool}")
            continue
        if route.mode not in allowed_modes:
            errors.append(f"{legacy_name}: mode {route.mode} not supported on {route.tool}")

    return errors
