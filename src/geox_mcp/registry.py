from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX WITNESS CORE — v2026.05.22
# 10 tools. Physics-9 foundation. No interpretation. No narrative.
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: List[str] = [
    # Data witnessing
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_dst_ingest_test",
    "geox_las_inspect",
    "geox_seismic_inspect",
    "geox_deviation_survey_inspect",
    "geox_tops_inspect",
    "geox_seismic_segy_inspect",
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
]

GEOX_TOOL_MANIFEST: List[Dict[str, Any]] = [
    {"name": "geox_data_ingest_bundle", "axis": "observe", "expose": True},
    {"name": "geox_data_qc_bundle", "axis": "verify", "expose": True},
    {"name": "geox_dst_ingest_test", "axis": "observe", "expose": True},
    {"name": "geox_las_inspect", "axis": "verify", "expose": True},
    {"name": "geox_seismic_inspect", "axis": "verify", "expose": True},
    {"name": "geox_deviation_survey_inspect", "axis": "verify", "expose": True},
    {"name": "geox_tops_inspect", "axis": "verify", "expose": True},
    {"name": "geox_seismic_segy_inspect", "axis": "verify", "expose": True},
    {"name": "geox_subsurface_generate_candidates", "axis": "reason", "expose": True},
    {"name": "geox_subsurface_verify_integrity", "axis": "verify", "expose": True},
    {"name": "geox_seismic_compute", "axis": "reason", "expose": True},
    {"name": "geox_sequence_interpret", "axis": "reason", "expose": True},
    {"name": "geox_evidence_reason", "axis": "reason", "expose": True},
    {"name": "geox_prospect_evaluate", "axis": "reason", "expose": True},
    {"name": "geox_map_context_scene", "axis": "observe", "expose": True},
    {"name": "geox_system_registry_status", "axis": "observe", "expose": True},
]

# Legacy aliases — hidden by default (GEOX_SHOW_LEGACY_ALIASES)
LEGACY_ALIAS_MAP: Dict[str, str] = {
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
