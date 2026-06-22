from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX CANONICAL PUBLIC TOOLS — Contract Mirror
# SOT: src/geox_mcp/registry.py
# Phase 2 Clean Architecture (2026-06-22): 15 mode-consolidated tools
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: list[str] = [
    # ── WELL DOMAIN (4 tools) ──
    "geox_well_ingest",
    "geox_well_qc",
    "geox_petrophysics",
    "geox_sequence",
    # ── SEISMIC DOMAIN (4 tools) ──
    "geox_seismic_ingest",
    "geox_seismic_compute",
    "geox_seismic_interpret",
    "geox_vision",
    # ── MODEL DOMAIN (2 tools) ──
    "geox_subsurface_model",
    "geox_geomechanics",
    # ── BASIN DOMAIN (1 tool) ──
    "geox_basin",
    # ── GOVERNANCE DOMAIN (2 tools) ──
    "geox_claim",
    "geox_evidence",
    # ── EVALUATION DOMAIN (1 tool) ──
    "geox_prospect",
    # ── DOCTRINE DOMAIN (1 tool) ──
    "geox_doctrine",
]

# Backward-compat names (Phase 2 transition — removed in Phase 4)
CANONICAL_COMPAT_TOOLS: list[str] = [
    "geox_data_ingest_bundle", "geox_data_qc_bundle", "geox_dst_ingest_test",
    "geox_header_inspect", "geox_las_inspect", "geox_seismic_segy_inspect",
    "geox_evidence_discover", "geox_subsurface_generate_candidates",
    "geox_subsurface_verify_integrity", "geox_sequence_interpret",
    "geox_evidence_reason", "geox_prospect_evaluate", "geox_map_context_scene",
    "geox_horizon_contrast_surface", "geox_coord_transform_tool",
    "geox_blockspace_resolution_tool", "geox_volume_frame_tool",
    "geox_seismic_compute_attribute_tool", "geox_fault_stick_ingest_tool",
    "geox_attribute_registry_list_tool", "geox_blend_volume_tool",
    "geox_segy_export_tool", "geox_claim_create", "geox_claim_validate",
    "geox_claim_challenge", "geox_evidence_attach", "geox_claim_seal",
    "geox_basin_resolve", "geox_basin_profile", "geox_query_intake",
    "geox_abstraction_guard", "geox_literature_ingest",
    "geox_vision_perceptual_inventory", "geox_vision_minimax_inference",
    "geox_vision_calibrate", "geox_vision_audit", "geox_query_macrostrat",
    "geox_doctrine_assumption_register", "geox_doctrine_anti_beautiful_one",
    "geox_doctrine_godel_review", "geox_prithvi_eo_inference",
    "geox_gravity_magnetic_forward", "geox_emag2_ingest", "geox_icgem_models",
    "geox_joint_inversion", "geox_mt_forward", "geox_biostrat_constraint",
    "geox_seismic_inversion", "geox_lem_predict", "geox_deep_time_state",
]

# Legacy aliases — REMOVED Phase 1 (2026-06-22)
LEGACY_ALIAS_MAP: dict[str, str] = {}
