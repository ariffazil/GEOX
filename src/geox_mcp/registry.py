from __future__ import annotations

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
    # New macrostrat modes accessible via geox_basin_profile
    # macrostrat_lithologies, macrostrat_strat_names, macrostrat_intervals,
    # macrostrat_fossils, macrostrat_geologic_map, macrostrat_cache_warm
    # ── W2-W4 FORGE — Doctrine layer (Gap X Assumption Lineage + Gap 3 Anti-Beautiful-One + Gap 5 Gödel Wall) ──
    "geox_doctrine_assumption_register",
    "geox_doctrine_anti_beautiful_one",
    "geox_doctrine_godel_review",
    # ── W5-W8 FORGE — Phase A first wave: Foundation model as backing engine (Prithvi-EO-2.0 NASA/IBM) ──
    "geox_prithvi_eo_inference",
    # ── W9-W12 FORGE — Phase B first wave: Nonseismic geophysics (gravity/magnetic + open data) ──
    "geox_gravity_magnetic_forward",
    "geox_emag2_ingest",
    "geox_icgem_models",
    # ── W13+ FORGE — Phase C: Multi-physics Earth Witness (joint inversion + CSEM/MT + biostrat) ──
    "geox_joint_inversion",
    "geox_mt_forward",
    "geox_biostrat_constraint",
    # ── W13+ FORGE — Phase C: Seismic Inversion (coloured / model-based / PINN) ──
    "geox_seismic_inversion",
    "geox_geomechanics",
    "geox_well_decision_class",
    "geox_wealth_feed",
    # ── W14+ FORGE 2026-06-21: GEOX-LEM inference (substrate live, weights pending GPU + 888) ──
    "geox_lem_predict",
    # ── W15+ FORGE 2026-06-22: Deep Time Physics Context (governed Earth State Vector) ──
    "geox_deep_time_state",
] 

GEOX_TOOL_MANIFEST: list[dict[str, Any]] = [
    # ── DISCOVERY LANE (6 tools) ── max_action_class: OBSERVE, no lease required
    {"name": "geox_system_registry_status", "axis": "observe", "lane": "discovery", "expose": True},
    {"name": "geox_attribute_registry_list_tool", "axis": "observe", "lane": "discovery", "expose": True},
    {"name": "geox_basin_resolve", "axis": "observe", "lane": "discovery", "expose": True},
    {"name": "geox_query_intake", "axis": "observe", "lane": "discovery", "expose": True},
    {"name": "geox_query_macrostrat", "axis": "observe", "lane": "discovery", "expose": True},
    # W9-W12 — open-data registry lookup (Phase B first wave)
    {"name": "geox_icgem_models", "axis": "observe", "lane": "discovery", "expose": True},

    # ── EVIDENCE LANE (14 tools) ── max_action_class: ANALYZE, no lease required
    {"name": "geox_data_ingest_bundle", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_data_qc_bundle", "axis": "verify", "lane": "evidence", "expose": True},
    {"name": "geox_dst_ingest_test", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_header_inspect", "axis": "verify", "lane": "evidence", "expose": True},
    {"name": "geox_las_inspect", "axis": "verify", "lane": "evidence", "expose": True},
    {"name": "geox_seismic_segy_inspect", "axis": "verify", "lane": "evidence", "expose": True},
    {"name": "geox_evidence_discover", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_evidence_attach", "axis": "verify", "lane": "evidence", "expose": True},
    {"name": "geox_literature_ingest", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_fault_stick_ingest_tool", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_volume_frame_tool", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_vision_perceptual_inventory", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_vision_calibrate", "axis": "verify", "lane": "evidence", "expose": True},
    # W9-W12 — EMAG2v3 global magnetic anomaly grid ingest (Phase B first wave)
    {"name": "geox_emag2_ingest", "axis": "observe", "lane": "evidence", "expose": True},

    # ── REASONING LANE (19 tools) ── max_action_class: ANALYZE, lease + session required
    {"name": "geox_subsurface_generate_candidates", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_subsurface_verify_integrity", "axis": "verify", "lane": "reasoning", "expose": True},
    {"name": "geox_seismic_compute", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_seismic_compute_attribute_tool", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_sequence_interpret", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_evidence_reason", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_prospect_evaluate", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_map_context_scene", "axis": "observe", "lane": "reasoning", "expose": True},
    {"name": "geox_horizon_contrast_surface", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_coord_transform_tool", "axis": "compute", "lane": "reasoning", "expose": True},
    {"name": "geox_blockspace_resolution_tool", "axis": "compute", "lane": "reasoning", "expose": True},
    {"name": "geox_blend_volume_tool", "axis": "compute", "lane": "reasoning", "expose": True},
    {"name": "geox_basin_profile", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_vision_minimax_inference", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_vision_audit", "axis": "verify", "lane": "reasoning", "expose": True},
    {"name": "geox_report_to_workflow", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_abstraction_guard", "axis": "verify", "lane": "reasoning", "expose": True},
    # W5-W8 — Prithvi-EO-2.0 NASA/IBM foundation model (Phase A first wave)
    {"name": "geox_prithvi_eo_inference", "axis": "reason", "lane": "reasoning", "expose": True},
    # W14+ FORGE 2026-06-21: GEOX-LEM substrate (live inference path; weights pending)
    {"name": "geox_lem_predict", "axis": "reason", "lane": "reasoning", "expose": True},
    # W9-W12 — Gravity + Magnetic forward model via HarmonIC (Phase B first wave)
    {"name": "geox_gravity_magnetic_forward", "axis": "compute", "lane": "reasoning", "expose": True},
    # W13+ — Phase C: Seismic Inversion (coloured / model-based / PINN)
    {"name": "geox_seismic_inversion", "axis": "reason", "lane": "reasoning", "expose": True},
    # W13+ — Phase C: MT 1D forward model
    {"name": "geox_mt_forward", "axis": "compute", "lane": "reasoning", "expose": True},
    # W13+ — Phase C: Biostratigraphic zonation constraint
    {"name": "geox_biostrat_constraint", "axis": "reason", "lane": "reasoning", "expose": True},
    # W15+ — Deep Time Physics Context (governed Earth State Vector)
    {"name": "geox_deep_time_state", "axis": "reason", "lane": "reasoning", "expose": True},

    # ── JUDGMENT LANE (9 tools) ── GOVERNED, lease + session + arifOS judge required
    {"name": "geox_claim_create", "axis": "reason", "lane": "judgment", "expose": True},
    {"name": "geox_claim_validate", "axis": "verify", "lane": "judgment", "expose": True},
    {"name": "geox_claim_challenge", "axis": "reason", "lane": "judgment", "expose": True},
    {"name": "geox_claim_seal", "axis": "reason", "lane": "judgment", "expose": True},
    {"name": "geox_segy_export_tool", "axis": "observe", "lane": "judgment", "expose": True},
    # W2-W4 — Doctrine layer (Gap X Assumption Lineage + Gap 3 Anti-Beautiful-One + Gap 5 Gödel Wall)
    {"name": "geox_doctrine_assumption_register", "axis": "verify", "lane": "judgment", "expose": True},
    {"name": "geox_doctrine_anti_beautiful_one", "axis": "verify", "lane": "judgment", "expose": True},
    {"name": "geox_doctrine_godel_review", "axis": "verify", "lane": "judgment", "expose": True},
    # W13+ — Phase C: Joint multi-physics inversion (GOVERNED — requires judge)
    {"name": "geox_joint_inversion", "axis": "reason", "lane": "judgment", "expose": True},
    # W13+ — Geomechanics (K, G, E, ν)
    {"name": "geox_geomechanics", "axis": "compute", "lane": "reasoning", "expose": True},
    # W13+ — WELL → GEOX operator readiness gate
    {"name": "geox_well_decision_class", "axis": "verify", "lane": "judgment", "expose": True},
    # W13+ — GEOX → WEALTH STOIIP + ranking feed
    {"name": "geox_wealth_feed", "axis": "reason", "lane": "judgment", "expose": True},
]

# Legacy aliases — hidden by default (GEOX_SHOW_LEGACY_ALIASES)
LEGACY_ALIAS_MAP: dict[str, str] = {
    "geox_deviation_survey_inspect": "geox_header_inspect",
    "geox_tops_inspect": "geox_header_inspect",
    "geox_seismic_inspect": "geox_header_inspect",
    # geox_las_inspect and geox_seismic_segy_inspect are now canonical (directly registered)
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
    "geox_registry": "geox_system_registry_status",
    # geox_query_macrostrat is now a first-class canonical tool (not an alias)
}
