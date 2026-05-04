from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX SOVEREIGN 13 — CANONICAL PUBLIC TOOLS
# The official, fixed set of 13 tools exposed on the public MCP surface.
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: List[str] = [
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_subsurface_generate_candidates",
    "geox_subsurface_verify_integrity",
    "geox_seismic_analyze_volume",
    "geox_section_interpret_correlation",
    "geox_map_context_scene",
    "geox_time4d_analyze_system",
    "geox_prospect_evaluate",
    "geox_prospect_judge_verdict",
    "geox_evidence_summarize_cross",
    "geox_system_registry_status",
    "geox_history_audit",
]

# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY ALIAS MAP — Deprecated tools and their canonical replacements.
# This ensures backward compatibility for one epoch, as per audit.
# ═══════════════════════════════════════════════════════════════════════════════

LEGACY_ALIAS_MAP: Dict[str, str] = {
    "geox_file_upload_import": "geox_data_ingest_bundle",
    "geox_dashboard.open": "geox_system_registry_status",
    # Add other legacy aliases as identified in TOOL_CONSOLIDATION_MAP.md
    # PROSPECT aliases
    "geox_evaluate_prospect": "geox_prospect_evaluate",
    "geox_prospect_build_structural_candidates": "geox_subsurface_generate_candidates",
    "geox_build_structural_candidates": "geox_subsurface_generate_candidates",
    "prospect_feasibility_check": "geox_prospect_evaluate",
    "geox_feasibility_check": "geox_prospect_evaluate",
    # WELL aliases
    "well_load_log_bundle": "geox_data_ingest_bundle",
    "geox_well_qc_logs": "geox_data_qc_bundle",
    "geox_qc_logs": "geox_data_qc_bundle",
    "geox_well_validate_cutoffs": "geox_subsurface_generate_candidates", # or specific QC if one exists
    "geox_validate_cutoffs": "geox_subsurface_generate_candidates",
    "geox_well_select_sw_model": "geox_subsurface_generate_candidates",
    "geox_select_sw_model": "geox_subsurface_generate_candidates",
    "geox_well_compute_petrophysics": "geox_subsurface_generate_candidates",
    "geox_compute_petrophysics": "geox_subsurface_generate_candidates",
    "well_petrophysical_check": "geox_subsurface_verify_integrity",
    "geox_petrophysical_hold_check": "geox_subsurface_verify_integrity",
    # SECTION aliases
    "geox_section_interpret_strata": "geox_section_interpret_correlation",
    "geox_interpret_strata": "geox_section_interpret_correlation",
    "geox_section_observe_well_correlation": "geox_section_interpret_correlation",
    "geox_observe_well_correlation": "geox_section_interpret_correlation",
    "geox_section_synthesize_profile": "geox_section_interpret_correlation",
    "geox_synthesize_profile": "geox_section_interpret_correlation",
    # EARTH3D aliases
    "geox_earth3d_load_volume": "geox_seismic_analyze_volume", # assuming load_volume is part of seismic analyze
    "geox_load_seismic_volume": "geox_seismic_analyze_volume",
    "geox_earth3d_interpret_horizons": "geox_seismic_analyze_volume",
    "geox_interpret_horizons": "geox_seismic_analyze_volume",
    "geox_earth3d_model_geometries": "geox_subsurface_generate_candidates",
    "geox_model_geometries": "geox_subsurface_generate_candidates",
    "geox_earth3d_verify_structural_integrity": "geox_subsurface_verify_integrity",
    "geox_verify_integrity": "geox_subsurface_verify_integrity",
    # TIME4D aliases
    "geox_time4d_simulate_burial": "geox_time4d_analyze_system",
    "geox_simulate_burial": "geox_time4d_analyze_system",
    "geox_time4d_reconstruct_paleo": "geox_time4d_analyze_system",
    "geox_reconstruct_paleo": "geox_time4d_analyze_system",
    "geox_time4d_verify_timing": "geox_time4d_analyze_system",
    "geox_verify_timing": "geox_time4d_analyze_system",
    # MAP aliases
    "geox_map_verify_coordinates": "geox_map_context_scene",
    "geox_verify_geospatial": "geox_map_context_scene",
    "geox_map_get_context_summary": "geox_map_context_scene",
    "geox_get_context_summary": "geox_map_context_scene",
    "geox_map_render_scene_context": "geox_map_context_scene",
    "geox_render_scene_context": "geox_map_context_scene",
    "geox_map_synthesize_causal_scene": "geox_map_context_scene",
    "geox_synthesize_causal_scene": "geox_map_context_scene",
    "geox_map_earth_signals": "geox_map_context_scene",
    "geox_earth_signals": "geox_map_context_scene",
    "geox_map_project_well": "geox_map_context_scene",
    "geox_project_well_trajectory": "geox_map_context_scene",
    "geox_map_transform_coordinates": "geox_map_context_scene",
    "geox_transform_coordinates": "geox_map_context_scene",
    # PHYSICS aliases
    "geox_physics_judge_verdict": "geox_prospect_judge_verdict",
    "geox_judge_verdict": "geox_prospect_judge_verdict",
    "geox_physics_validate_operation": "geox_subsurface_verify_integrity",
    "geox_validate_operation": "geox_subsurface_verify_integrity",
    "geox_physics_audit_hold_breach": "geox_history_audit",
    "geox_audit_hold_breach": "geox_history_audit",
    "geox_physics_verify_physics": "geox_subsurface_verify_integrity",
    "geox_verify_physics": "geox_subsurface_verify_integrity",
    "geox_verify_canon": "geox_subsurface_verify_integrity",
    "geox_physics_compute_stoiip": "geox_prospect_evaluate",
    "geox_compute_stoiip": "geox_prospect_evaluate",
    "geox_physics_fetch_authoritative_state": "geox_system_registry_status",
    "geox_fetch_authoritative_state": "geox_system_registry_status",
    "geox_physics_acp_register": "geox_system_registry_status", # placeholder
    "acp_register_agent": "geox_system_registry_status",
    "geox_physics_acp_submit": "geox_prospect_judge_verdict", # placeholder
    "acp_submit_proposal": "geox_prospect_judge_verdict",
    "geox_physics_acp_check_convergence": "geox_system_registry_status", # placeholder
    "acp_check_convergence": "geox_system_registry_status",
    "geox_physics_acp_grant_seal": "geox_prospect_judge_verdict", # placeholder
    "acp_grant_seal": "geox_prospect_judge_verdict",
    "geox_physics_acp_status": "geox_system_registry_status", # placeholder
    "acp_get_status": "geox_system_registry_status",
    # CROSS aliases
    "geox_cross_evidence_list": "geox_evidence_summarize_cross",
    "geox_search_evidence": "geox_evidence_summarize_cross",
    "geox_evidence_list": "geox_evidence_summarize_cross",
    "geox_cross_evidence_get": "geox_evidence_summarize_cross",
    "geox_get_evidence_details": "geox_evidence_summarize_cross",
    "geox_evidence_get": "geox_evidence_summarize_cross",
    "geox_cross_dimension_list": "geox_system_registry_status",
    "geox_dimension_list": "geox_system_registry_status",
    "geox_get_tools_registry": "geox_system_registry_status", # UI compatibility
    "geox_cross_health": "geox_system_registry_status",
}

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX SERVER CAPABILITIES — As per MCP 2025-11-25 spec.
# These capabilities are advertised in the MCP initialize handshake.
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_CAPABILITIES: Dict[str, Any] = {
    "resources": {
        "subscribe": False,     # Deferred to Sprint 3 — notification pipeline not yet implemented
        "listChanged": False,   # Static resource catalog; no runtime additions
    },
    "tools": {
        "listChanged": True,    # Dimension registries load dynamically
    },
    "prompts": {
        "listChanged": False,   # 6 static workflow prompts
    },
    "logging": {},              # MCP logging capability — emits notifications/message
}
