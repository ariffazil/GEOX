from __future__ import annotations

from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX CANONICAL — Phase 2 Clean Architecture (2026-06-22)
# 15 tools. Mode-based consolidation. Evidence-only. Physics-9 governed.
# DITEMPA BUKAN DIBERI — Forged, Not Given.
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_PUBLIC_TOOLS: list[str] = [
    # ── WELL DOMAIN (4 tools) ──────────────────────────────────────────────────
    "geox_well_ingest",          # 1. LAS, SEG-Y, DST, deviation, tops ingest
    "geox_well_qc",              # 2. QC: depth, curves, completeness, FJIS
    "geox_petrophysics",         # 3. Vsh, porosity, Sw, perm, net pay, LEM
    "geox_sequence",             # 4. Sequence stratigraphy, correlation

    # ── SEISMIC DOMAIN (4 tools) ───────────────────────────────────────────────
    "geox_seismic_ingest",       # 5. SEG-Y I/O, header inspection
    "geox_seismic_compute",      # 6. Synthetic, well-tie, AVO, attributes, inversion
    "geox_seismic_interpret",    # 7. Horizon contrast, faults, frames, blend
    "geox_vision",               # 8. VLM inference, audit, calibration, perceptual

    # ── MODEL DOMAIN (2 tools) ─────────────────────────────────────────────────
    "geox_subsurface_model",     # 9. Joint inversion, gravity/mag, MT forward
    "geox_geomechanics",         # 10. K/G/E/ν, coordinate transform, blockspace

    # ── BASIN DOMAIN (1 tool) ──────────────────────────────────────────────────
    "geox_basin",                # 11. Profile, resolve, macrostrat, deep time, scene

    # ── GOVERNANCE DOMAIN (2 tools) ────────────────────────────────────────────
    "geox_claim",                # 12. Create, validate, challenge, seal, attach
    "geox_evidence",             # 13. Discover, synthesize, abduct, contradict, literature

    # ── EVALUATION DOMAIN (1 tool) ─────────────────────────────────────────────
    "geox_prospect",             # 14. Volumetrics, POS, EVOI, risk assessment

    # ── DOCTRINE DOMAIN (1 tool) ───────────────────────────────────────────────
    "geox_doctrine",             # 15. Anti-Beautiful-One, assumptions, Gödel, guards
]

# Backward-compat: old tool names available for 1 release cycle
# Format: "old_name"  # → new_name
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
# These compat names will be removed in Phase 4. 

GEOX_TOOL_MANIFEST: list[dict[str, Any]] = [
    # ── PHASE 2 CLEAN ARCHITECTURE (15 tools, 4 lanes) ─────────────────────────

    # ── WELL DOMAIN (4 tools) ──────────────────────────────────────────────────
    {"name": "geox_well_ingest", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_well_qc", "axis": "verify", "lane": "evidence", "expose": True},
    {"name": "geox_petrophysics", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_sequence", "axis": "reason", "lane": "reasoning", "expose": True},

    # ── SEISMIC DOMAIN (4 tools) ───────────────────────────────────────────────
    {"name": "geox_seismic_ingest", "axis": "observe", "lane": "evidence", "expose": True},
    {"name": "geox_seismic_compute", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_seismic_interpret", "axis": "reason", "lane": "reasoning", "expose": True},
    {"name": "geox_vision", "axis": "reason", "lane": "reasoning", "expose": True},

    # ── MODEL DOMAIN (2 tools) ─────────────────────────────────────────────────
    {"name": "geox_subsurface_model", "axis": "reason", "lane": "judgment", "expose": True},
    {"name": "geox_geomechanics", "axis": "compute", "lane": "reasoning", "expose": True},

    # ── BASIN DOMAIN (1 tool) ──────────────────────────────────────────────────
    {"name": "geox_basin", "axis": "reason", "lane": "discovery", "expose": True},

    # ── GOVERNANCE DOMAIN (2 tools) ────────────────────────────────────────────
    {"name": "geox_claim", "axis": "reason", "lane": "judgment", "expose": True},
    {"name": "geox_evidence", "axis": "reason", "lane": "evidence", "expose": True},

    # ── EVALUATION DOMAIN (1 tool) ─────────────────────────────────────────────
    {"name": "geox_prospect", "axis": "reason", "lane": "judgment", "expose": True},

    # ── DOCTRINE DOMAIN (1 tool) ───────────────────────────────────────────────
    {"name": "geox_doctrine", "axis": "verify", "lane": "judgment", "expose": True},
]

# Legacy aliases — REMOVED Phase 1 Clean Slate (2026-06-22)
# All 29 aliases killed. Use canonical tool names directly.
LEGACY_ALIAS_MAP: dict[str, str] = {}
