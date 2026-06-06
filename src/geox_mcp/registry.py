from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX WITNESS CORE — v2026.05.22
# 10 tools. Physics-9 foundation. No interpretation. No narrative.
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: list[str] = [
    # Data witnessing
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_dst_ingest_test",
    "geox_header_inspect",
    "geox_evidence_discover",
    "geox_report_to_workflow",
    # Physics-9 domain engines
    "geox_subsurface_generate_candidates",
    "geox_subsurface_verify_integrity",
    # Unified seismic physics
    "geox_seismic_compute",
    # Unified sequence stratigraphy
    "geox_sequence_interpret",
    # Unified evidence reasoning
    "geox_evidence_reason",
    # Prospect evaluation with governance
    "geox_prospect_evaluate",
    # Spatial context
    "geox_map_context_scene",
    # Machine-checkable truth
    "geox_system_registry_status",
    # Horizon contrast surface (ToAC-as-Attention pipeline)
    "geox_horizon_contrast_surface",
    # paleoscan_python v2.0.0 forge — coordinate & image substrate
    "geox_coord_transform_tool",
    "geox_blockspace_resolution_tool",
    "geox_volume_frame_tool",
    "geox_seismic_compute_attribute_tool",
    "geox_fault_stick_ingest_tool",
    "geox_attribute_registry_list_tool",
    # paleoscan_python v2.0.0 forge — blending + export
    "geox_blend_volume_tool",
    "geox_segy_export_tool",
    # H5: Claim Engine
    "geox_claim_create",
    "geox_claim_validate",
    "geox_claim_challenge",
    "geox_evidence_attach",
    "geox_claim_seal",
    # Basin & Metaphor guards
    "geox_basin_resolve",
    "geox_basin_profile",
    "geox_query_intake",
    "geox_abstraction_guard",
    "geox_literature_ingest",
]

GEOX_TOOL_MANIFEST: list[dict[str, Any]] = [
    {"name": "geox_data_ingest_bundle", "axis": "observe", "expose": True},
    {"name": "geox_data_qc_bundle", "axis": "verify", "expose": True},
    {"name": "geox_dst_ingest_test", "axis": "observe", "expose": True},
    {"name": "geox_header_inspect", "axis": "verify", "expose": True},
    {"name": "geox_evidence_discover", "axis": "observe", "expose": True},
    {"name": "geox_report_to_workflow", "axis": "reason", "expose": True},
    {"name": "geox_subsurface_generate_candidates", "axis": "reason", "expose": True},
    {"name": "geox_subsurface_verify_integrity", "axis": "verify", "expose": True},
    {"name": "geox_seismic_compute", "axis": "reason", "expose": True},
    {"name": "geox_sequence_interpret", "axis": "reason", "expose": True},
    {"name": "geox_evidence_reason", "axis": "reason", "expose": True},
    {"name": "geox_prospect_evaluate", "axis": "reason", "expose": True},
    {"name": "geox_map_context_scene", "axis": "observe", "expose": True},
    {"name": "geox_system_registry_status", "axis": "observe", "expose": True},
    {"name": "geox_horizon_contrast_surface", "axis": "reason", "expose": True},
    # paleoscan_python v2.0.0 forge
    {"name": "geox_coord_transform_tool", "axis": "compute", "expose": True},
    {"name": "geox_blockspace_resolution_tool", "axis": "compute", "expose": True},
    {"name": "geox_volume_frame_tool", "axis": "observe", "expose": True},
    {"name": "geox_seismic_compute_attribute_tool", "axis": "reason", "expose": True},
    {"name": "geox_fault_stick_ingest_tool", "axis": "observe", "expose": True},
    {"name": "geox_attribute_registry_list_tool", "axis": "observe", "expose": True},
    # paleoscan_python v2.0.0 forge — blending + export
    {"name": "geox_blend_volume_tool", "axis": "compute", "expose": True},
    {"name": "geox_segy_export_tool", "axis": "observe", "expose": True},
    # H5: Claim Engine
    {"name": "geox_claim_create", "axis": "reason", "expose": True},
    {"name": "geox_claim_validate", "axis": "verify", "expose": True},
    {"name": "geox_claim_challenge", "axis": "reason", "expose": True},
    {"name": "geox_evidence_attach", "axis": "verify", "expose": True},
    {"name": "geox_claim_seal", "axis": "reason", "expose": True},
    # Basin & Metaphor guards
    {"name": "geox_basin_resolve", "axis": "observe", "expose": True},
    {"name": "geox_basin_profile", "axis": "reason", "expose": True},
    {"name": "geox_query_intake", "axis": "observe", "expose": True},
    {"name": "geox_abstraction_guard", "axis": "verify", "expose": True},
    {"name": "geox_literature_ingest", "axis": "observe", "expose": True},
]

# Legacy aliases — hidden by default (GEOX_SHOW_LEGACY_ALIASES)
LEGACY_ALIAS_MAP: dict[str, str] = {
    "geox_deviation_survey_inspect": "geox_header_inspect",
    "geox_tops_inspect": "geox_header_inspect",
    "geox_seismic_inspect": "geox_header_inspect",
    "geox_ingest_bundle": "geox_data_ingest_bundle",
    "geox_qc_bundle": "geox_data_qc_bundle",
    "geox_subsurface_candidates": "geox_subsurface_generate_candidates",
    "geox_petrophysics": "geox_subsurface_generate_candidates",
    "geox_seismic_tie": "geox_seismic_compute",
    "geox_well_tie": "geox_seismic_compute",
    "geox_td_anchor": "geox_seismic_compute",
    "geox_forward_model": "geox_seismic_compute",
    "geox_anomalous_contrast": "geox_seismic_compute",
    "geox_ac_detector": "geox_seismic_compute",
    "geox_seismic_analyze_volume": "geox_seismic_compute",
    "geox_sequence_stratigraphy": "geox_sequence_interpret",
    "geox_well_compute_gr_bins": "geox_sequence_interpret",
    "geox_well_build_packages": "geox_sequence_interpret",
    "geox_well_infer_seq_strat": "geox_sequence_interpret",
    "geox_well_analyze_sequence": "geox_sequence_interpret",
    "geox_stratigraphy_run_pipeline": "geox_sequence_interpret",
    "geox_stratigraphy_preview_config": "geox_sequence_interpret",
    "geox_section_interpret_correlation": "geox_sequence_interpret",
    "geox_evidence_summarize_cross": "geox_evidence_reason",
    "geox_process_abduction": "geox_evidence_reason",
    "geox_evidence_contradiction_scan": "geox_evidence_reason",
    "geox_prospect_judge_preview": "geox_prospect_evaluate",
    "geox_prospect_judge_seal": "geox_prospect_evaluate",
    "geox_prospect_judge_verdict": "geox_prospect_evaluate",
    "geox_task_ingest_las_batch": "geox_data_ingest_bundle",
    "geox_task_metabolize_basin": "geox_subsurface_generate_candidates",
    "geox_registry": "geox_system_registry_status",
}
