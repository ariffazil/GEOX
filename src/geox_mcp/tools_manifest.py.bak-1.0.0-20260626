"""
geox_mcp/tools_manifest.py — P1 CRITICAL
DITEMPA BUKAN DIBERI — External surface is law, not suggestion.

Canonical external surface for GEOX MCP.
Only these 16 tools are visible to external MCP clients (AAA, ART, Copilot, etc.)

MEMBRANE RULE:
  - Internal adapter names NEVER appear in tool_id
  - Library names (harmonica, pygeopressure, devito, pylops, simpeg, etc.) NEVER surface
  - External tool_id format: domain_verb (e.g. gravity.get_bouguer_anomaly)
  - For the 16 canonical names: use the geox_* prefix as registered in server.py

Version: 1.0.0 (locked 2026-06-26)
Lock authority: GEOX_PHASE2_EPOCH = 2026-06-22
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ─── Domain Verb IDs (external-facing) ──────────────────────────────────────────
#
# These are the domain-verb aliases for the 16 canonical tools.
# MCP clients can call either the canonical name (geox_*) or the domain_verb alias.
# The domain_verb alias is the preferred external-facing ID.
#
# Format: domain_verb → canonical MCP tool name
# The MCP tool name (geox_*) is what's registered in server.py @mcp.tool decorator.
# The domain_verb is the public-facing name for external agents.

DOMAIN_VERB_TOOLS: dict[str, str] = {
    # ── WELL DOMAIN (4) ─────────────────────────────────────────────────────
    "well.load_logs": "geox_well_ingest",
    "well.check_quality": "geox_well_qc",
    "well.derive_petrophysics": "geox_petrophysics",
    "well.correlate": "geox_sequence",
    # ── SEISMIC DOMAIN (4) ────────────────────────────────────────────────────
    "seismic.load_volume": "geox_seismic_ingest",
    "seismic.compute": "geox_seismic_compute",
    "seismic.interpret": "geox_seismic_interpret",
    "seismic.analyze_vision": "geox_vision",
    # ── MODEL DOMAIN (2) ──────────────────────────────────────────────────────
    "model.joint_inversion": "geox_subsurface_model",
    "model.mechanics": "geox_geomechanics",
    # ── BASIN DOMAIN (2) ──────────────────────────────────────────────────────
    "basin.profile": "geox_basin",
    "basin.deep_time": "geox_deep_time_state",
    # ── INTERNAL PLUMBING (4) ─────────────────────────────────────────────────
    "govern.claim": "geox_claim",
    "govern.evidence": "geox_evidence",
    "govern.prospect": "geox_prospect",
    "govern.doctrine": "geox_doctrine",
}


# ─── Canonical Tool Registry ──────────────────────────────────────────────────


@dataclass(frozen=True)
class CanonicalTool:
    """
    One entry per canonical GEOX tool.

    Fields:
      mcp_tool_name: The @mcp.tool(name="...") registered in server.py
      domain_verb: Preferred external-facing alias (domain.verb format)
      domain: One of well | seismic | model | basin | govern
      description: One-line description for external agents
      use_when: When to call this tool (for LLM tool selection)
      internal_backing: Which internal adapters/functions produce this tool's output
      acrisk: ACRisk level (QUALIFY | ADVISORY | HOLD | BLOCK)
      888_hold: True if this tool requires Arif release before autonomous use
      modes: Available operation modes (if mode-based)
    """

    mcp_tool_name: str
    domain_verb: str
    domain: str
    description: str
    use_when: str
    internal_backing: list[str] = field(default_factory=list)
    acrisk: str = "QUALIFY"
    is_888_hold: bool = False
    modes: list[str] | None = None


CANONICAL_TOOLS: dict[str, CanonicalTool] = {
    # ══════════════════════════════════════════════════════════════════════════════
    # SURFACE-FACING — 12 tools (what the world sees)
    # ══════════════════════════════════════════════════════════════════════════════
    # ── WELL DOMAIN ───────────────────────────────────────────────────────────
    "geox_well_ingest": CanonicalTool(
        mcp_tool_name="geox_well_ingest",
        domain_verb="well.load_logs",
        domain="well",
        description="Load and parse well log data from LAS, SEG-Y, DST, deviation surveys, and stratigraphic tops.",
        use_when="User provides a LAS file, well log, DST data, deviation survey, or stratigraphic tops for loading.",
        internal_backing=["welly.Well", "lasio.LASFile", "segysapioclient.SEGYReader"],
        acrisk="QUALIFY",
        is_888_hold=False,
        modes=["las", "segy", "deviation", "tops", "dst", "checkshot", "auto"],
    ),
    "geox_well_qc": CanonicalTool(
        mcp_tool_name="geox_well_qc",
        domain_verb="well.check_quality",
        domain="well",
        description="Quality-control check for depth consistency, curve completeness, log quality flags, and FJIS standards.",
        use_when="User wants to verify well log quality, check depth gaps, validate curve coverage, or run FJIS checks.",
        internal_backing=["geox_core.engines.well.qc_engine.QCHandler"],
        acrisk="QUALIFY",
        is_888_hold=False,
        modes=["depth", "curves", "completeness", "fjis"],
    ),
    "geox_petrophysics": CanonicalTool(
        mcp_tool_name="geox_petrophysics",
        domain_verb="well.derive_petrophysics",
        domain="well",
        description="Compute Vsh (shale volume), porosity (density-neutron), Sw (water saturation), permeability, net pay, and LEM using bound transforms. Requires QC-verified inputs.",
        use_when="User wants to derive porosity, water saturation, shale volume, or permeability from raw well logs.",
        internal_backing=["bruges_adapter.BrugesAdapter", "geox_core.engines.petrophysics.transforms"],
        acrisk="ADVISORY",
        is_888_hold=False,  # ADVISORY — surface result but note calibration status
        modes=["vsh", "porosity", "sw", "perm", "net_pay", "lem"],
    ),
    "geox_sequence": CanonicalTool(
        mcp_tool_name="geox_sequence",
        domain_verb="well.correlate",
        domain="well",
        description="Sequence stratigraphic correlation: gamma ray cutoff, para-sequence stacking, wireline motif analysis, and depositional environment interpretation.",
        use_when="User wants to interpret stratigraphic sequences, correlate wells, or identify parasequence boundaries from wireline logs.",
        internal_backing=["geox_core.engines.stratigraphy.sequence_engine.SequenceEngine"],
        acrisk="ADVISORY",
        is_888_hold=False,
        modes=["correlation", "stacking", "motif", "depo_environment"],
    ),
    # ── SEISMIC DOMAIN ─────────────────────────────────────────────────────────
    "geox_seismic_ingest": CanonicalTool(
        mcp_tool_name="geox_seismic_ingest",
        domain_verb="seismic.load_volume",
        domain="seismic",
        description="Ingest and inspect SEG-Y seismic volumes: header inspection, geometry assignment, trace statistics.",
        use_when="User provides a SEG-Y file for loading, header inspection, or geometry verification.",
        internal_backing=["obspy.io.segy.segyio.SEGYFile", "geox_core.engines.seismic.segy_inspector"],
        acrisk="QUALIFY",
        is_888_hold=False,
        modes=["header_inspect", "geometry_assign", "trace_stats"],
    ),
    "geox_seismic_compute": CanonicalTool(
        mcp_tool_name="geox_seismic_compute",
        domain_verb="seismic.compute",
        domain="seismic",
        description="Seismic physics engine: synthetic seismogram (Devito FD), well-tie (cross-correlation), AVO/AVA (Aki-Richards, Fatti), time-depth anchoring (checkshot-only, Law 5), anomalous contrast detection, seismic attributes.",
        use_when="User wants to compute synthetic seismograms, run well-ties, calculate AVO gradients, extract seismic attributes, or detect anomalous amplitude contrasts.",
        internal_backing=[
            "devito_adapter.DevitoAdapter",
            "bruges_adapter.BrugesAdapter",  # AVO
            "pylops_adapter.PyLOPSAdapter",  # inversion
            "geox_core.engines.seismic.attribute_engine",
        ],
        acrisk="ADVISORY",
        is_888_hold=False,
        modes=["synthetic", "well_tie", "time_depth_anchor", "anomalous_contrast", "attribute"],
    ),
    "geox_seismic_interpret": CanonicalTool(
        mcp_tool_name="geox_seismic_interpret",
        domain_verb="seismic.interpret",
        domain="seismic",
        description="Seismic interpretation: horizon contrast analysis, fault stick interpretation, blend/fusion of seismic volumes, frame-based structural interpretation.",
        use_when="User wants to map horizons, interpret faults, blend seismic volumes, or generate structural frames.",
        internal_backing=["geox_core.engines.seismic.horizon_engine", "geox_core.engines.seismic.fault_engine"],
        acrisk="ADVISORY",
        is_888_hold=False,
        modes=["horizon_contrast", "fault_stick", "blend", "frames"],
    ),
    "geox_vision": CanonicalTool(
        mcp_tool_name="geox_vision",
        domain_verb="seismic.analyze_vision",
        domain="seismic",
        description="VLM inference on seismic sections and maps: perception audit, calibration, and domain-adapted geological labeling.",
        use_when="User wants to run a vision model on seismic images for geological feature detection, or audit a VLM perception result.",
        internal_backing=["geox_core.engines.vision.vlm_inference", "minimax_code.understand_image"],
        acrisk="ADVISORY",
        is_888_hold=False,
        modes=["perceptual_audit", "calibration", "labeling"],
    ),
    # ── MODEL DOMAIN ───────────────────────────────────────────────────────────
    "geox_subsurface_model": CanonicalTool(
        mcp_tool_name="geox_subsurface_model",
        domain_verb="model.joint_inversion",
        domain="model",
        description="Joint inversion and physics-based subsurface modeling: gravity+magnetics joint inversion (SimPEG), EM/Magnetotelluric 1D (SimPEG MT), co-registered with seismic velocity.",
        use_when="User wants to run joint gravity-magnetics inversion, MT 1D, or integrate potential field data with seismic velocity models.",
        internal_backing=[
            "simpeg_adapter.SimPEGAdapter",  # gravity, magnetics, MT
            "pygimli_adapter.PyGIMLIAdapter",  # ERT/TEM/DC
            "gempy_adapter.GemPyAdapter",  # 3D stratigraphic geomodel
            "loopstructural_adapter.LoopStructuralAdapter",  # fault/fold geometry
        ],
        acrisk="HOLD",  # SimPEG MT → pore pressure is 888_HOLD gated
        is_888_hold=True,
        modes=["gravity", "magnetics", "mt_1d", "joint_grav_mag", "ert", "tem", "dc_sounding"],
    ),
    "geox_geomechanics": CanonicalTool(
        mcp_tool_name="geox_geomechanics",
        domain_verb="model.mechanics",
        domain="model",
        description="Geomechanical computation: K (bulk modulus), G (shear modulus), E (Young's modulus), ν (Poisson's ratio), AI (acoustic impedance) from Vp/Vs/rho. Coordinate transforms and blockspace mapping.",
        use_when="User wants to compute elastic moduli from sonic and density logs, or transform coordinates between depth domains.",
        internal_backing=["bruges_adapter.BrugesAdapter"],
        acrisk="QUALIFY",
        is_888_hold=False,
        modes=["elastic_moduli", "ai", "coord_transform", "blockspace"],
    ),
    # ── BASIN DOMAIN ───────────────────────────────────────────────────────────
    "geox_basin": CanonicalTool(
        mcp_tool_name="geox_basin",
        domain_verb="basin.profile",
        domain="basin",
        description="Basin profiling: plate reconstruction (GPlately), paleo-coordinate transform, plate velocity, Macrostrat unit query, EMAG2 magnetic anomaly, GEBCO bathymetry, scene context.",
        use_when="User wants to reconstruct plate positions at a past geological time, query bathymetry/topography, get magnetic declination, or profile a basin's stratigraphic architecture.",
        internal_backing=[
            "gplately_adapter.GPlatelyAdapter",  # plate reconstruction
            "harmonica_adapter.HarmonICAdapter",  # gravity forward + EMAG2
            "gempy_adapter.GemPyAdapter",  # 3D stratigraphic model
            "geox_core.engines.basin.macrostrat_client",
            "geox_core.engines.basin.gebco_fetcher",  # GEBCO bathymetry
            "geox_core.engines.basin.emag2_fetcher",  # EMAG2 magnetics
        ],
        acrisk="QUALIFY",
        is_888_hold=False,
        modes=["profile", "resolve", "macrostrat_units", "macrostrat_columns", "scene"],
    ),
    "geox_deep_time_state": CanonicalTool(
        mcp_tool_name="geox_deep_time_state",
        domain_verb="basin.deep_time",
        domain="basin",
        description="Earth State Vector at any geological age: plate polygons, basin architecture, paleobathymetry, heat flow, subsidence history for a given deep time.",
        use_when="User wants to know the plate configuration, basin architecture, or thermal state at a specific geological age (e.g. 50 Ma, 100 Ma, 250 Ma).",
        internal_backing=[
            "gplately_adapter.GPlatelyAdapter",
            "geox_core.engines.basin.deep_time_engine.DeepTimeState",
        ],
        acrisk="ADVISORY",
        is_888_hold=False,
        modes=["plate_polygons", "basin_architecture", "paleobathymetry", "heat_flow", "subsidence"],
    ),
    # ══════════════════════════════════════════════════════════════════════════════
    # INTERNAL PLUMBING — 4 tools (federation governance, not for generic external agents)
    # ══════════════════════════════════════════════════════════════════════════════
    "geox_claim": CanonicalTool(
        mcp_tool_name="geox_claim",
        domain_verb="govern.claim",
        domain="govern",
        description="[INTERNAL] Create, validate, challenge, seal, or attach geological claims. Governs the evidence chain.",
        use_when="Internal federation use only. For creating or managing geological claim records with full epistemic lineage.",
        internal_backing=["geox_core.engines.governance.claim_engine.ClaimEngine"],
        acrisk="HOLD",
        is_888_hold=True,
        modes=["create", "validate", "challenge", "seal", "attach"],
    ),
    "geox_evidence": CanonicalTool(
        mcp_tool_name="geox_evidence",
        domain_verb="govern.evidence",
        domain="govern",
        description="[INTERNAL] Discover, synthesize, abduct, or contradict geological evidence. Manages the evidence corpus.",
        use_when="Internal federation use only. For evidence synthesis, literature review, or contradiction scanning.",
        internal_backing=["geox_core.engines.governance.evidence_engine.EvidenceEngine"],
        acrisk="HOLD",
        is_888_hold=True,
        modes=["discover", "synthesize", "abduct", "contradict", "literature"],
    ),
    "geox_prospect": CanonicalTool(
        mcp_tool_name="geox_prospect",
        domain_verb="govern.prospect",
        domain="govern",
        description="[INTERNAL] Prospect volumetric computation: STOIIP, GIP, POS, EVOI, risk-weighted decision support.",
        use_when="Internal federation use only. For prospect screening, volumetric estimation, and EVOI computation.",
        internal_backing=["geox_core.engines.governance.prospect_engine.ProspectEngine"],
        acrisk="HOLD",
        is_888_hold=True,
        modes=["screen", "volumetric", "evoi", "risk_assessment"],
    ),
    "geox_doctrine": CanonicalTool(
        mcp_tool_name="geox_doctrine",
        domain_verb="govern.doctrine",
        domain="govern",
        description="[INTERNAL] Anti-Beautiful-One audit, Gödel guards, assumption register, and constitutional doctrine enforcement for GEOX operations.",
        use_when="Internal federation use only. For doctrine audits, assumption lineage tracking, and anti-hallucination guards.",
        internal_backing=["geox_core.engines.governance.doctrine_engine.DoctrineEngine"],
        acrisk="HOLD",
        is_888_hold=True,
        modes=["anti_beautiful_one", "godel_review", "assumption_register", "guard"],
    ),
}


# ─── Helpers ───────────────────────────────────────────────────────────────────


def get_canonical_tool(tool_name: str) -> CanonicalTool | None:
    """Resolve a tool name (canonical or domain_verb alias) to its CanonicalTool entry."""
    return CANONICAL_TOOLS.get(tool_name)


def get_domain_verb_alias(mcp_tool_name: str) -> str | None:
    """Get the domain_verb alias for a canonical MCP tool name."""
    for dv, mcp in DOMAIN_VERB_TOOLS.items():
        if mcp == mcp_tool_name:
            return dv
    return None


def is_surface_tool(tool_name: str) -> bool:
    """True if this tool is surface-facing (not internal govern plumbing)."""
    tool = get_canonical_tool(tool_name)
    if tool is None:
        return False
    return tool.domain != "govern"


def requires_888_hold(tool_name: str) -> bool:
    """True if this tool requires Arif release before autonomous use."""
    tool = get_canonical_tool(tool_name)
    if tool is None:
        return False
    return tool.is_888_hold


def get_internal_backing(tool_name: str) -> list[str]:
    """Return the list of internal adapters/functions that back this tool."""
    tool = get_canonical_tool(tool_name)
    if tool is None:
        return []
    return tool.internal_backing


def list_surface_tools() -> list[str]:
    """Return all surface-facing tool names (12 tools)."""
    return [name for name, tool in CANONICAL_TOOLS.items() if tool.domain != "govern"]


def list_internal_tools() -> list[str]:
    """Return all internal govern tool names (4 tools)."""
    return [name for name, tool in CANONICAL_TOOLS.items() if tool.domain == "govern"]


def list_domain_verb_aliases() -> dict[str, str]:
    """Return mapping of domain_verb → mcp_tool_name for all 16 tools."""
    return dict(DOMAIN_VERB_TOOLS)


# ─── Version Lock ─────────────────────────────────────────────────────────────

TOOLS_MANIFEST_VERSION = "1.0.0"
TOOLS_MANIFEST_EPOCH = "2026-06-26"
TOOLS_MANIFEST_STATUS = "LOCKED"

"""
Version history:
  1.0.0 (2026-06-26) — Initial locked manifest. 16 canonical tools.
                          Replaces ad-hoc tool registration as source of truth.
                          DOMAIN_VERB_TOOLS provides external aliases.
                          internal_backing shows which adapters produce each tool's output.

DITEMPA BUKAN DIBERI — The manifest is law. Only 16 tools are canonical.
"""
