from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX CANONICAL PUBLIC TOOLS
# SOT: src/geox_mcp/registry.py
# Last verified: 2026-06-21
# 54 canonical tools (W2-W13+ FORGE). Physics-9 foundation. Evidence-only.
# +14 from W2-W13+: 3 doctrine + 1 Prithvi + 1 gravity/mag + 2 open data
# + 3 multi-physics (joint inversion + CSEM/MT + biostrat) + 1 PINN
# + 3 integration (geomechanics + WELL decision_class + WEALTH feed).
# F13 SOVEREIGN authorized expansion (AGENTS.md §Authority).
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: list[str] = [
    # Data witnessing
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_dst_ingest_test",
    "geox_header_inspect",
    "geox_las_inspect",
    "geox_seismic_segy_inspect",
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
    # Vision V1 (Layer 1) — 4 tools, forged 2026-06-07
    "geox_vision_perceptual_inventory",
    "geox_vision_minimax_inference",
    "geox_vision_calibrate",
    "geox_vision_audit",
    # Macrostrat — dedicated client (replaces thin proxy alias)
    "geox_query_macrostrat",
    # ── W2-W4 FORGE — Doctrine layer ──
    "geox_doctrine_assumption_register",
    "geox_doctrine_anti_beautiful_one",
    "geox_doctrine_godel_review",
    # ── W5-W8 FORGE — Phase A first wave: Foundation model as backing engine ──
    "geox_prithvi_eo_inference",
    # ── W9-W12 FORGE — Phase B first wave: Nonseismic geophysics + open data ──
    "geox_gravity_magnetic_forward",
    "geox_emag2_ingest",
    "geox_icgem_models",
    # ── W13+ FORGE — Phase C: Multi-physics Earth Witness ──
    "geox_joint_inversion",
    "geox_mt_forward",
    "geox_biostrat_constraint",
    "geox_seismic_inversion",  # 1D post-stack PINN-style seismic inversion
    "geox_geomechanics",        # K, G, E, ν from Physics9State
    "geox_well_decision_class", # WELL → GEOX operator readiness gate (C1-C5)
    "geox_wealth_feed",         # GEOX → WEALTH STOIIP + ranking + verdict
]

GEOX_TOOL_MANIFEST: list[dict[str, str]] = [
    {"name": "geox_data_ingest_bundle", "axis": "observe", "expose": "True"},
    {"name": "geox_data_qc_bundle", "axis": "verify", "expose": "True"},
    {"name": "geox_dst_ingest_test", "axis": "observe", "expose": "True"},
    {"name": "geox_header_inspect", "axis": "verify", "expose": "True"},
    {"name": "geox_las_inspect", "axis": "verify", "expose": "True"},
    {"name": "geox_seismic_segy_inspect", "axis": "verify", "expose": "True"},
    {"name": "geox_evidence_discover", "axis": "observe", "expose": "True"},
    {"name": "geox_report_to_workflow", "axis": "reason", "expose": "True"},
    {"name": "geox_subsurface_generate_candidates", "axis": "reason", "expose": "True"},
    {"name": "geox_subsurface_verify_integrity", "axis": "verify", "expose": "True"},
    {"name": "geox_seismic_compute", "axis": "reason", "expose": "True"},
    {"name": "geox_sequence_interpret", "axis": "reason", "expose": "True"},
    {"name": "geox_evidence_reason", "axis": "reason", "expose": "True"},
    {"name": "geox_prospect_evaluate", "axis": "reason", "expose": "True"},
    {"name": "geox_map_context_scene", "axis": "observe", "expose": "True"},
    {"name": "geox_system_registry_status", "axis": "observe", "expose": "True"},
    {"name": "geox_horizon_contrast_surface", "axis": "reason", "expose": "True"},
    {"name": "geox_coord_transform_tool", "axis": "compute", "expose": "True"},
    {"name": "geox_blockspace_resolution_tool", "axis": "compute", "expose": "True"},
    {"name": "geox_volume_frame_tool", "axis": "observe", "expose": "True"},
    {"name": "geox_seismic_compute_attribute_tool", "axis": "reason", "expose": "True"},
    {"name": "geox_fault_stick_ingest_tool", "axis": "observe", "expose": "True"},
    {"name": "geox_attribute_registry_list_tool", "axis": "observe", "expose": "True"},
    {"name": "geox_blend_volume_tool", "axis": "compute", "expose": "True"},
    {"name": "geox_segy_export_tool", "axis": "observe", "expose": "True"},
    {"name": "geox_claim_create", "axis": "reason", "expose": "True"},
    {"name": "geox_claim_validate", "axis": "verify", "expose": "True"},
    {"name": "geox_claim_challenge", "axis": "reason", "expose": "True"},
    {"name": "geox_evidence_attach", "axis": "verify", "expose": "True"},
    {"name": "geox_claim_seal", "axis": "reason", "expose": "True"},
    {"name": "geox_basin_resolve", "axis": "observe", "expose": "True"},
    {"name": "geox_basin_profile", "axis": "reason", "expose": "True"},
    {"name": "geox_query_intake", "axis": "observe", "expose": "True"},
    {"name": "geox_abstraction_guard", "axis": "verify", "expose": "True"},
    {"name": "geox_literature_ingest", "axis": "observe", "expose": "True"},
    {"name": "geox_vision_perceptual_inventory", "axis": "observe", "expose": "True"},
    {"name": "geox_vision_minimax_inference", "axis": "reason", "expose": "True"},
    {"name": "geox_vision_calibrate", "axis": "verify", "expose": "True"},
    {"name": "geox_vision_audit", "axis": "verify", "expose": "True"},
    {"name": "geox_query_macrostrat", "axis": "observe", "expose": "True"},
    # W2-W4 — Doctrine layer
    {"name": "geox_doctrine_assumption_register", "axis": "verify", "expose": "True"},
    {"name": "geox_doctrine_anti_beautiful_one", "axis": "verify", "expose": "True"},
    {"name": "geox_doctrine_godel_review", "axis": "verify", "expose": "True"},
    # W5-W8 — Phase A
    {"name": "geox_prithvi_eo_inference", "axis": "reason", "expose": "True"},
    # W9-W12 — Phase B
    {"name": "geox_gravity_magnetic_forward", "axis": "compute", "expose": "True"},
    {"name": "geox_emag2_ingest", "axis": "observe", "expose": "True"},
    {"name": "geox_icgem_models", "axis": "observe", "expose": "True"},
    # W13+ — Multi-physics
    {"name": "geox_joint_inversion", "axis": "reason", "expose": "True"},
    {"name": "geox_mt_forward", "axis": "compute", "expose": "True"},
    {"name": "geox_biostrat_constraint", "axis": "verify", "expose": "True"},
    {"name": "geox_seismic_inversion", "axis": "reason", "expose": "True"},
    {"name": "geox_geomechanics", "axis": "compute", "expose": "True"},
    {"name": "geox_well_decision_class", "axis": "verify", "expose": "True"},
    {"name": "geox_wealth_feed", "axis": "reason", "expose": "True"},
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
    "geox_history_audit": "geox_system_registry_status",
}
