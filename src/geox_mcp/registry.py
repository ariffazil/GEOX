from __future__ import annotations

from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX CANONICAL TOOLS — Phase 2 Clean Architecture (2026-06-22)
# 18 tools (Phase 2.1, 2026-06-28). Mode-based consolidation. Evidence-only.
# Physics-9 governed.
# ═══════════════════════════════════════════════════════════════════════════════
#
# SURFACE-FACING (14 tools):
#   What external agents (AAA, ART, Copilot, any MCP client) call to get
#   Earth data or run subsurface analysis. These are the "public API" of GEOX.
#
# INTERNAL PLUMBING (4 tools):
#   Governance, claims, evidence chains, doctrine. Federation constitutional
#   machinery. Used by arifOS 888_JUDGE and internal workflows.
#
#   Total canonical = 30. Live runtime reports canonical_tools=30.
#   Any change requires 888_HOLD per geox/AGENTS.md.
#
# Phase 2.1 (2026-06-28): added geox_well_desurvey (3D wellbore geometry).
#   Action card: forge_work/GEOX-ADAPT-001-r1.md.
#   F13 SOVEREIGN ratified by Arif 2026-06-28.
#
# DITEMPA BUKAN DIBERI — Forged, Not Given.
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# SURFACE-FACING TOOLS — Earth Data + Subsurface Analysis (14 tools)
# ─────────────────────────────────────────────────────────────────────────────
#
# What these do: query the planet, analyze subsurface data, return evidence.
# Who calls them: AAA cockpit, ART, Copilot, any MCP client.
# Count: 14 (13 earth tools + 1 federation discovery tool)
#
SURFACE_TOOLS: list[str] = [
    # ── WELL DOMAIN (5) ────────────────────────────────────────────────────────
    "geox_well_ingest",  # LAS, SEG-Y, DST, deviation, tops ingest
    "geox_well_qc",  # QC: depth, curves, completeness, FJIS
    "geox_well_desurvey",  # Phase 2.1 (2026-06-28): 3D wellbore geometry (TVD/X/Y/TVDSS) from deviation survey. wellpathpy mincurve + tan, CRS transform, ACRisk envelope.
    "geox_petrophysics",  # Vsh, porosity, Sw, perm, net pay, LEM
    "geox_sequence",  # Sequence stratigraphy, correlation
    # ── SEISMIC DOMAIN (4) ─────────────────────────────────────────────────────
    "geox_seismic_ingest",  # SEG-Y I/O, header inspection
    "geox_seismic_compute",  # Synthetic, well-tie, AVO, attributes, inversion
    "geox_seismic_interpret",  # Horizon contrast, faults, frames, blend
    "geox_vision",  # VLM inference, audit, calibration, perceptual
    # ── MODEL DOMAIN (2) ───────────────────────────────────────────────────────
    "geox_subsurface_model",  # Joint inversion, gravity/mag, MT forward
    "geox_geomechanics",  # K/G/E/ν, coordinate transform, blockspace
    # ── BASIN DOMAIN (2) ───────────────────────────────────────────────────────
    "geox_basin",  # Profile, resolve, macrostrat, scene
    "geox_deep_time_state",  # Earth State Vector at any geological age
    # ── FEDERATION DISCOVERY (1) ───────────────────────────────────────────────
    # GAP-1 fix (2026-06-27): Federation-standard registry probe.
    # Any MCP client can call this. Returns the 18 real tools, not the 31 ghosts.
    "geox_surface_status",
    # ── EGS (Earth Grounding System) — 12 tools (2026-06-28) ─────────────────────
    # Typed earth graph, uncertainty algebra, claim/evidence lifecycle.
    # "Language models consume EGS; they do not replace it."
    "geox_egs_query_entity",
    "geox_egs_query_claim",
    "geox_egs_query_uncertainty",
    "geox_egs_query_provenance",
    "geox_egs_claim_create",
    "geox_egs_claim_challenge",
    "geox_egs_evidence_attach",
    "geox_egs_evidence_reason",
    "geox_egs_seismic_compute",
    "geox_egs_rock_physics",
    "geox_egs_data_qc_bundle",
    "geox_egs_scenario_audit",
]


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL PLUMBING — Governance, Claims, Doctrine (4 tools)
# ─────────────────────────────────────────────────────────────────────────────
#
# What these do: constitutional machinery. Claims, evidence chains, judgment,
#   epistemic guards. Used by arifOS 888_JUDGE and federation workflows.
# Who calls them: arifOS kernel, 888_JUDGE, internal federation a2a.
# Count: 4
#
INTERNAL_TOOLS: list[str] = [
    "geox_claim",  # Create, validate, challenge, seal, attach claims
    "geox_evidence",  # Discover, synthesize, abduct, contradict, literature
    "geox_prospect",  # Volumetrics, POS, EVOI, risk assessment (judgment-gated)
    "geox_doctrine",  # Anti-Beautiful-One, assumptions, Gödel, guards
]


# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL PUBLIC TOOLS — Union of surface + internal (18 total)
# ─────────────────────────────────────────────────────────────────────────────
#
# This is the single source of truth for the MCP server invariant check.
# Surface tools are what the world sees. Internal tools are federation plumbing.
# Live runtime reports canonical_tools=18; do not change without 888_HOLD.
#
CANONICAL_PUBLIC_TOOLS: list[str] = SURFACE_TOOLS + INTERNAL_TOOLS


# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT — old tool names, 1 release cycle
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL_COMPAT_TOOLS: list[str] = [
    "geox_data_ingest_bundle",
    "geox_data_qc_bundle",
    "geox_dst_ingest_test",
    "geox_header_inspect",
    "geox_las_inspect",
    "geox_seismic_segy_inspect",
    "geox_evidence_discover",
    "geox_subsurface_generate_candidates",
    "geox_subsurface_verify_integrity",
    "geox_sequence_interpret",
    "geox_evidence_reason",
    "geox_prospect_evaluate",
    "geox_map_context_scene",
    "geox_horizon_contrast_surface",
    "geox_coord_transform_tool",
    "geox_blockspace_resolution_tool",
    "geox_volume_frame_tool",
    "geox_seismic_compute_attribute_tool",
    "geox_fault_stick_ingest_tool",
    "geox_attribute_registry_list_tool",
    "geox_blend_volume_tool",
    "geox_segy_export_tool",
    "geox_claim_create",
    "geox_claim_validate",
    "geox_claim_challenge",
    "geox_evidence_attach",
    "geox_claim_seal",
    "geox_basin_resolve",
    "geox_basin_profile",
    "geox_query_intake",
    "geox_abstraction_guard",
    "geox_literature_ingest",
    "geox_vision_perceptual_inventory",
    "geox_vision_minimax_inference",
    "geox_vision_calibrate",
    "geox_vision_audit",
    "geox_query_macrostrat",
    "geox_doctrine_assumption_register",
    "geox_doctrine_anti_beautiful_one",
    "geox_doctrine_godel_review",
    "geox_prithvi_eo_inference",
    "geox_gravity_magnetic_forward",
    "geox_emag2_ingest",
    "geox_icgem_models",
    "geox_joint_inversion",
    "geox_mt_forward",
    "geox_biostrat_constraint",
    "geox_seismic_inversion",
    "geox_lem_predict",
]


# ─────────────────────────────────────────────────────────────────────────────
# TOOL MANIFEST — metadata for MCP server
# Single source of truth for domain, lane, axis, and affordance metadata.
# Structured source replaces hardcoded inline dict in server.py geox_surface_status.
# ─────────────────────────────────────────────────────────────────────────────
GEOX_TOOL_MANIFEST: list[dict[str, Any]] = [
    # ── WELL DOMAIN (3) ───────────────────────────────────────────────────────
    {
        "name": "geox_well_ingest",
        "domain": "earth.well",
        "axis": "observe",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {"name": "geox_well_qc", "domain": "earth.well", "axis": "verify", "lane": "evidence", "expose": True, "face": "surface"},
    {
        "name": "geox_well_desurvey",
        "domain": "earth.well",
        "axis": "compute",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },  # Phase 2.1 (2026-06-28)
    # ── PETROPHYSICS DOMAIN (1) ───────────────────────────────────────────────
    {
        "name": "geox_petrophysics",
        "domain": "earth.petrophysics",
        "axis": "reason",
        "lane": "reasoning",
        "expose": True,
        "face": "surface",
    },
    # ── STRATIGRAPHY DOMAIN (1) ────────────────────────────────────────────────
    {
        "name": "geox_sequence",
        "domain": "earth.stratigraphy",
        "axis": "reason",
        "lane": "reasoning",
        "expose": True,
        "face": "surface",
    },
    # ── SEISMIC DOMAIN (3) ────────────────────────────────────────────────────
    {
        "name": "geox_seismic_ingest",
        "domain": "earth.seismic",
        "axis": "observe",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_seismic_compute",
        "domain": "earth.seismic",
        "axis": "reason",
        "lane": "reasoning",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_seismic_interpret",
        "domain": "earth.seismic",
        "axis": "reason",
        "lane": "reasoning",
        "expose": True,
        "face": "surface",
    },
    # ── PERCEPTION DOMAIN (1) ─────────────────────────────────────────────────
    {
        "name": "geox_vision",
        "domain": "earth.perception",
        "axis": "reason",
        "lane": "reasoning",
        "expose": True,
        "face": "surface",
    },
    # ── MODEL DOMAIN (1) ─────────────────────────────────────────────────────
    {
        "name": "geox_subsurface_model",
        "domain": "earth.model",
        "axis": "reason",
        "lane": "judgment",
        "expose": True,
        "face": "surface",
    },
    # ── MECHANICS DOMAIN (1) ─────────────────────────────────────────────────
    {
        "name": "geox_geomechanics",
        "domain": "earth.mechanics",
        "axis": "compute",
        "lane": "reasoning",
        "expose": True,
        "face": "surface",
    },
    # ── BASIN DOMAIN (1) ─────────────────────────────────────────────────────
    {"name": "geox_basin", "domain": "earth.basin", "axis": "reason", "lane": "discovery", "expose": True, "face": "surface"},
    # ── DEEP TIME DOMAIN (1) ─────────────────────────────────────────────────
    {
        "name": "geox_deep_time_state",
        "domain": "earth.deep_time",
        "axis": "reason",
        "lane": "discovery",
        "expose": True,
        "face": "surface",
    },
    # ── GENERAL DISCOVERY (1) ─────────────────────────────────────────────────
    {
        "name": "geox_surface_status",
        "domain": "earth.general",
        "axis": "verify",
        "lane": "discovery",
        "expose": True,
        "face": "surface",
    },
    # ── GOVERNANCE DOMAIN (4) ─────────────────────────────────────────────────
    {
        "name": "geox_claim",
        "domain": "governance.claims",
        "axis": "reason",
        "lane": "judgment",
        "expose": True,
        "face": "internal",
    },
    {
        "name": "geox_evidence",
        "domain": "governance.evidence",
        "axis": "reason",
        "lane": "evidence",
        "expose": True,
        "face": "internal",
    },
    {
        "name": "geox_prospect",
        "domain": "governance.prospect",
        "axis": "reason",
        "lane": "judgment",
        "expose": True,
        "face": "internal",
    },
    {
        "name": "geox_doctrine",
        "domain": "governance.doctrine",
        "axis": "verify",
        "lane": "discovery",
        "expose": True,
        "face": "internal",
    },
    # ── EGS (Earth Grounding System) — 12 tools (2026-06-28) ─────────────────
    # Typed earth graph, uncertainty algebra, claim/evidence lifecycle.
    # "Language models consume EGS; they do not replace it."
    # Query tools → discovery lane (pure reads, no session needed).
    # Claim/evidence tools → evidence lane.
    # Compute tools → evidence lane (bounded transforms, not full reasoning).
    {
        "name": "geox_egs_query_entity",
        "domain": "earth.governance",
        "axis": "observe",
        "lane": "discovery",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_query_claim",
        "domain": "earth.governance",
        "axis": "observe",
        "lane": "discovery",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_query_uncertainty",
        "domain": "earth.governance",
        "axis": "observe",
        "lane": "discovery",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_query_provenance",
        "domain": "earth.governance",
        "axis": "observe",
        "lane": "discovery",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_claim_create",
        "domain": "earth.governance",
        "axis": "reason",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_claim_challenge",
        "domain": "earth.governance",
        "axis": "reason",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_evidence_attach",
        "domain": "earth.governance",
        "axis": "reason",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_evidence_reason",
        "domain": "earth.governance",
        "axis": "reason",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_seismic_compute",
        "domain": "earth.seismic",
        "axis": "compute",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_rock_physics",
        "domain": "earth.petrophysics",
        "axis": "compute",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_data_qc_bundle",
        "domain": "earth.general",
        "axis": "verify",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
    {
        "name": "geox_egs_scenario_audit",
        "domain": "earth.governance",
        "axis": "verify",
        "lane": "evidence",
        "expose": True,
        "face": "surface",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — built from manifest, single source of truth
# ─────────────────────────────────────────────────────────────────────────────


def get_tool_domain(tool_name: str) -> str:
    """Return the domain for a tool from the manifest. Falls back to earth.general."""
    for entry in GEOX_TOOL_MANIFEST:
        if entry["name"] == tool_name:
            return entry.get("domain", "earth.general")
    return "earth.general"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def surface_tool_count() -> int:
    """Number of surface-facing tools (what the world sees)."""
    return len(SURFACE_TOOLS)


def internal_tool_count() -> int:
    """Number of internal plumbing tools (governance machinery)."""
    return len(INTERNAL_TOOLS)


def is_surface_tool(name: str) -> bool:
    """Check if a tool is surface-facing."""
    return name in SURFACE_TOOLS


def is_internal_tool(name: str) -> bool:
    """Check if a tool is internal plumbing."""
    return name in INTERNAL_TOOLS


# Legacy aliases — REMOVED Phase 1 Clean Slate (2026-06-22)
LEGACY_ALIAS_MAP: dict[str, str] = {}
