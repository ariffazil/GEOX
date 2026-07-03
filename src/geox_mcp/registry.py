from __future__ import annotations

from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX CANONICAL TOOLS — Phase 2.7 Clean Architecture (2026-07-03)
# 38 canonical tools (34 surface + 4 internal). 49 backward-compat aliases.
# Mode-based consolidation. Evidence-only. Physics-9 governed.
# ═══════════════════════════════════════════════════════════════════════════════
#
# SURFACE-FACING (41 tools):
#   What external agents (AAA, ART, Copilot, any MCP client) call to get
#   Earth data or run subsurface analysis. These are the "public API" of GEOX.
#   Organized by domain: 5 well + 4 stratigraphy + 4 seismic + 2 model + 6 basin + 1 atlas +
#   4 earth map + 1 federation + 1 safety + 12 EGS + 1 contrast = 41.
#   Phase 2.7 (2026-07-03): +1 geox_biostrat_parse, +1 geox_biostrat_nn_age,
#   +1 geox_biostrat_ruling_check — biostratigraphy parsing + age + contradiction.
#   Phase 3.0 (2026-07-03): +3 geox_simulate_accommodation/surfaces/sequences —
#   physics-first stratigraphy engines. The extinction event.
#
# INTERNAL PLUMBING (4 tools):
#   Governance, claims, evidence chains, doctrine. Federation constitutional
#   machinery. Used by arifOS 888_JUDGE and internal workflows.
#
#   Total canonical = 45. Live runtime reports canonical_tools=45.
#   49 backward-compat aliases accepted by middleware (scheduled removal 2026-07-30).
#   Any change requires 888_HOLD per geox/AGENTS.md.
#
# Phase 2.1 (2026-06-28): added geox_well_desurvey (3D wellbore geometry).
#   Action card: forge_work/GEOX-ADAPT-001-r1.md.
#   F13 SOVEREIGN ratified by Arif 2026-06-28.
# Phase 2.4 (2026-07-02): added geox_map_export_package (governed export + PROV sidecar).
#   Completes map verb chain: discover → plan → render → export.
#
# DITEMPA BUKAN DIBERI — Forged, Not Given.
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# SURFACE-FACING TOOLS — Earth Data + Subsurface Analysis (34 tools)
# ─────────────────────────────────────────────────────────────────────────────
#
# What these do: query the planet, analyze subsurface data, return evidence.
# Who calls them: AAA cockpit, ART, Copilot, any MCP client.
# Count: 41 (5 well + 4 stratigraphy + 4 seismic + 2 model + 3 basin + 1 atlas + 4 earth map + 1 federation + 1 safety + 12 EGS + 1 contrast)
#
SURFACE_TOOLS: list[str] = [
    # ── WELL DOMAIN (5) ────────────────────────────────────────────────────────
    "geox_well_ingest",  # LAS, SEG-Y, DST, deviation, tops ingest
    "geox_well_qc",  # QC: depth, curves, completeness, FJIS
    "geox_well_desurvey",  # Phase 2.1 (2026-06-28): 3D wellbore geometry (TVD/X/Y/TVDSS) from deviation survey. wellpathpy mincurve + tan, CRS transform, ACRisk envelope.
    "geox_petrophysics",  # Vsh, porosity, Sw, perm, net pay, LEM
    "geox_sequence",  # [DEPRECATED] Sequence stratigraphy — taxonomy-first. Use geox_simulate_accommodation + geox_simulate_surfaces + geox_simulate_sequences for physics-first.
    # ── PHYSICS-FIRST STRATIGRAPHY (3) — Phase 3.0 (2026-07-03) ────────────────
    # The extinction event: replaces LST/TST/HST taxonomy with physics simulation.
    # Surfaces and sequences EMERGE from accommodation + eustasy + sediment routing.
    "geox_simulate_accommodation",  # Subsidence + eustasy + sediment loading → accommodation through time
    "geox_simulate_surfaces",  # Erosion/flooding/MFS/truncation surfaces from accommodation physics
    "geox_simulate_sequences",  # Sequences emerge from surfaces + stacking patterns (not LST/TST/HST)
    "geox_simulate_routing",  # Sediment routing: source→sink, delta lobes, fans, bypass/deposition
    # ── SEISMIC DOMAIN (4) ─────────────────────────────────────────────────────
    "geox_seismic_ingest",  # SEG-Y I/O, header inspection
    "geox_seismic_compute",  # Synthetic, well-tie, AVO, attributes, inversion
    "geox_seismic_interpret",  # Horizon contrast, faults, frames, blend
    "geox_vision",  # VLM inference, audit, calibration, perceptual
    # ── MODEL DOMAIN (2) ───────────────────────────────────────────────────────
    "geox_subsurface_model",  # Joint inversion, gravity/mag, MT forward
    "geox_geomechanics",  # K/G/E/ν, coordinate transform, blockspace
    # ── BASIN DOMAIN (6) ───────────────────────────────────────────────────────
    "geox_basin",  # Profile, resolve, macrostrat, scene
    "geox_deep_time_state",  # Earth State Vector at any geological age
    "geox_biostrat_parse",  # Phase 2.7: NN zone parser + GDE mapper + lithology classifier. Multi-zone extraction.
    "geox_biostrat_nn_age",  # Phase 2.7: NN zone age resolution with calibration metadata. Not a radiometric age.
    "geox_biostrat_ruling_check",  # Phase 2.7: Contradiction detector (facies veto, reworking, multi-discipline convergence).
    "geox_biostrat_falsify",  # Phase 2.7: 8-gate Popperian falsification engine. Any FALSIFIED → overall FALSIFIED.
    "geox_macrostrat_calibrate",  # Phase 2.8: Merge relative biostrat with Macrostrat absolute ages. Biostrat→Ma bridge.
    "geox_atlas",  # Point-in-country + land/water classifier. Natural Earth 10m GeoJSON.
    # ── EARTH MAP SURFACE (4) — Phase 2.4 (2026-07-02) ─────────────────────────
    # Layer registry + scene planning + cached preview rendering + governed export.
    # Architecture: tools compute, resources carry data. Truth-class gated.
    "geox_map_layers_list",  # Discover available layers for a bbox + theme
    "geox_map_scene_plan",  # Deterministic render recipe (no image yet)
    "geox_map_render_preview",  # Cheap static PNG preview with caching
    "geox_map_export_package",  # Governed export with PROV sidecar, STAC catalog, GeoPackage
    # ── FEDERATION DISCOVERY (1) ───────────────────────────────────────────────
    # GAP-1 fix (2026-06-27): Federation-standard registry probe.
    # Any MCP client can call this. Returns the 18 real tools, not the 31 ghosts.
    "geox_surface_status",
    # ── CIVILIZATIONAL SAFETY GATE (1) — Phase 2.5 (2026-07-02) ────────────────
    # Forbidden-claims scanner: every tool output can be checked against a
    # canonical list of claims that GEOX must never assert without evidence.
    # F13 SOVEREIGN: list is not modifiable by agents.
    "geox_forbidden_claims_scan",
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
    "geox_egs_seismic_compute",  # DEPRECATED: use geox_seismic_compute (unified engine with 6 modes)
    "geox_egs_rock_physics",
    "geox_egs_data_qc_bundle",
    "geox_egs_scenario_audit",
    # ── UNIVERSAL ANOMALOUS CONTRAST DETECTOR (1) — Phase 2.6 (2026-07-03) ──────
    # Theory of Anomalous Contrast (ToAC) generalized across all seven dimensions.
    # Mass, Energy, Time, Absence contrast detection + cross-dimensional audit.
    # Pattern: predict → observe → contrast → classify → report.
    # A-FORGE 888_HOLD approved 2026-07-03 by F13 SOVEREIGN.
    "geox_contrast_detect",
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
# CANONICAL PUBLIC TOOLS — Union of surface + internal (40 total)
# ─────────────────────────────────────────────────────────────────────────────
#
# This is the single source of truth for the MCP server invariant check.
# Surface tools are what the world sees. Internal tools are federation plumbing.
# Live runtime reports canonical_tools=45; do not change without 888_HOLD.
#
CANONICAL_PUBLIC_TOOLS: list[str] = SURFACE_TOOLS + INTERNAL_TOOLS


# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPAT — old tool names, 1 release cycle
# ─────────────────────────────────────────────────────────────────────────────
#
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  STRIKE 3 — DEPRECATION ANNOUNCEMENT (2026-06-30)                          ║
# ║                                                                             ║
# ║  These 49 backward-compat aliases are scheduled for REMOVAL after           ║
# ║  2026-07-30. They are accepted by GeoxGovernanceMiddleware.on_call_tool()   ║
# ║  but HIDDEN from tools/list (filtered by on_list_tools).                    ║
# ║                                                                             ║
# ║  Routing mechanism:                                                         ║
# ║    1. These are actual FastMCP tool registrations from sub-servers          ║
# ║       (witness, paleoscan, claims, vision) mounted via mcp.mount().         ║
# ⑄    2. _prune_mcp_surface() keeps them because they are in SACRED_SURFACE.  ║
# ║    3. GeoxGovernanceMiddleware._EXECUTABLE_SURFACE (geox_middleware.py:84)  ║
# ║       = canonical_public ∪ canonical_compat → accepts both on call_tool.   ║
# ║    4. GeoxGovernanceMiddleware.on_list_tools() (geox_middleware.py:115)     ║
# ║       filters to _PUBLIC_SURFACE only → compat are hidden from tools/list.  ║
# ║    5. Lane assignment (organ_governance.py:_load_lane_map()) maps each      ║
# ║       alias to discovery/evidence/reasoning/judgment so lane enforcement    ║
# ║       does not over-require session/lease on read-only aliases.             ║
# ║                                                                             ║
# ║  Migration: clients should switch to canonical tool names. See              ║
# ║  CANONICAL_COMPAT_MIGRATION.md in this directory for alias→canonical map.   ║
# ║                                                                             ║
# ║  ⚠️  KNOWN GAPS (Strike 3 audit):                                          ║
# ║      3 aliases lack explicit lane map entries in organ_governance.py:       ║
# ║        - geox_dst_ingest_test    → defaults to "reasoning" (too strict)    ║
# ║        - geox_sequence_interpret → defaults to "reasoning" (too strict)    ║
# ║        - geox_evidence_reason    → defaults to "reasoning" (too strict)    ║
# ║      These fall back to "reasoning" lane which unnecessarily requires       ║
# ║      session_id. FIXED in organ_governance.py (Strike 3 patch).             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
#
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
    "geox_system_registry_status",  # legacy alias → geox_surface_status (canonical)
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
    # ── MAP EXPORT DOMAIN (1) — Phase 2.4 (2026-07-02) ────────────────────────
    {
        "name": "geox_map_export_package",
        "domain": "earth.map",
        "axis": "compute",
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
    # ── ATLAS DOMAIN (1) — Phase 2.5 (2026-07-02) ─────────────────────────────
    {
        "name": "geox_atlas",
        "domain": "earth.atlas",
        "axis": "observe",
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
    # ── CIVILIZATIONAL SAFETY GATE (1) — Phase 2.5 (2026-07-02) ───────────────
    {
        "name": "geox_forbidden_claims_scan",
        "domain": "earth.governance",
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
