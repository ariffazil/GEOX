from __future__ import annotations

DEPRECATED_SINCE = "2026-05-01"
REMOVAL_CONDITION = "Remove after manifest+llms+runtime parity passes for one release epoch (Target: 2026-06-01)"

LEGACY_ALIAS_MAP = {
    # health / registry
    "geox_health": "geox_system_registry_status",
    "geox_health_check": "geox_system_registry_status",
    "geox_capabilities": "geox_system_registry_status",
    "geox_registry": "geox_system_registry_status",
    "geox_list_skills": "geox_system_registry_status",
    "geox_skill_metadata": "geox_system_registry_status",
    
    # ingest / QC
    "geox_well_load_bundle": "geox_data_ingest_bundle",
    "geox_well_ingest_bundle": "geox_data_ingest_bundle",
    "geox_seismic_load_line": "geox_data_ingest_bundle",
    "geox_seismic_load_volume": "geox_data_ingest_bundle",
    "geox_earth3d_load_volume": "geox_data_ingest_bundle",
    "geox_well_qc_logs": "geox_data_qc_bundle",
    "geox_map_verify_coordinates": "geox_data_qc_bundle",
    "geox_verify_geospatial": "geox_data_qc_bundle",
    
    # generate / verify
    "geox_well_compute_petrophysics": "geox_subsurface_generate_candidates",
    "geox_well_petrophysics_candidates": "geox_subsurface_generate_candidates",
    "geox_earth3d_model_geometries": "geox_subsurface_generate_candidates",
    "geox_build_structural_candidates": "geox_subsurface_generate_candidates",
    "geox_section_compute_flattening": "geox_subsurface_generate_candidates",
    "geox_well_verify_petrophysics": "geox_subsurface_verify_integrity",
    "geox_earth3d_verify_structural_integrity": "geox_subsurface_verify_integrity",
    "geox_section_verify_correlation": "geox_subsurface_verify_integrity",
    
    # seismic / section / map / time
    "geox_seismic_compute_attribute": "geox_seismic_analyze_volume",
    "geox_seismic_render_slice": "geox_seismic_analyze_volume",
    "geox_section_interpret_strata": "geox_section_interpret_correlation",
    "geox_map_get_context_summary": "geox_map_context_scene",
    "geox_map_render_scene": "geox_map_context_scene",
    "geox_map_render_scene_context": "geox_map_context_scene",
    "geox_time4d_verify_timing": "geox_time4d_analyze_system",
    "geox_time4d_simulate_burial": "geox_time4d_analyze_system",
    
    # prospect / cross / history
    "geox_evaluate_prospect": "geox_prospect_evaluate",
    "geox_cross_summarize_evidence": "geox_evidence_summarize_cross",
    "geox_prospect_audit_history": "geox_history_audit",

    # dotted legacy aliases
    "geox_well.compute_petrophysics": "geox_subsurface_generate_candidates",
    "geox_prospect.evaluate": "geox_prospect_evaluate",
    "geox_map.render_scene_context": "geox_map_context_scene",
    "geox_dashboard.open": "geox_system_registry_status",

    # smithery.yaml legacy entries (2026-05-01 consolidation)
    "geox_load_seismic_line": "geox_data_ingest_bundle",
    "geox_compute_petrophysics": "geox_subsurface_generate_candidates",
    "geox_petrophysical_hold_check": "geox_subsurface_verify_integrity",
    "geox_validate_cutoffs": "geox_subsurface_verify_integrity",
    "geox_feasibility_check": "geox_prospect_evaluate",
    "geox_query_memory": "geox_system_registry_status",
    "geox_select_sw_model": "geox_subsurface_generate_candidates",
}

def get_alias_metadata(old_name: str, new_name: str) -> dict:
    """Standard deprecation envelope for the alias bridge."""
    return {
        "_meta": {
            "deprecation": {
                "status": "DEPRECATED_ALIAS",
                "legacy_name": old_name,
                "canonical_name": new_name,
                "deprecated_since": DEPRECATED_SINCE,
                "removal_condition": REMOVAL_CONDITION,
                "message": f"Tool '{old_name}' is aliased to '{new_name}'. Update calling contract by 2026-06-01."
            }
        }
    }
