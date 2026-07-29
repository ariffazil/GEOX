"""
GEOX Tool Discovery — LLM-Optimized Tool Selection
═══════════════════════════════════════════════════

Provides clear "use when" guidance for LLMs to select the correct GEOX tool.
Each tool entry includes:
  - description: What the tool does (1-2 sentences)
  - use_when: Clear trigger phrases for LLMs
  - do_not_use_when: When NOT to use this tool
  - keywords: Search terms for discovery
  - examples: Example queries that should trigger this tool

DITEMPA BUKAN DIBERI — Discovered, not guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolDiscovery:
    """LLM-optimized tool discovery metadata — canonical 16 tools only."""

    name: str
    domain_verb: str  # external-facing alias, e.g. gravity.get_bouguer_anomaly
    description: str
    use_when: str
    do_not_use_when: str
    keywords: list[str]
    examples: list[str]
    domain: str
    modes: list[str] | None = None
    acrisk: str = "QUALIFY"  # QUALIFY | ADVISORY | HOLD | BLOCK
    is_888_hold: bool = False  # True = requires Arif release before autonomous use


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DISCOVERY REGISTRY — 16 Canonical GEOX Tools (LOCKED 2026-06-26)
# Sourced from: tools_manifest.py::CANONICAL_TOOLS
# External aliases from: tools_manifest.py::DOMAIN_VERB_TOOLS
# This registry is the LLM-optimized discovery layer.
# MCP list_tools is filtered to these 16 only (see server.py membrane).
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_DISCOVERY: dict[str, ToolDiscovery] = {
    # ── WELL DOMAIN ────────────────────────────────────────────────────────────
    "geox_well_ingest": ToolDiscovery(
        name="geox_well_ingest",
        domain_verb="well.load_logs",
        description="Load well log data from LAS, SEG-Y, DST, deviation, or tops files. Auto-detects format.",
        use_when="User provides a LAS file, well log, DST data, deviation survey, or stratigraphic tops for loading.",
        do_not_use_when="User wants to analyze seismic volumes (not well data), or wants QC checks on already-loaded data.",
        keywords=["las", "well log", "dst", "deviation", "tops", "ingest", "load", "import", "parse", "well data"],
        examples=[
            "Load this LAS file: /data/wells/A-1.las",
            "Ingest DST data from the B-2 well",
            "Read the deviation survey for well C-3",
            "Import stratigraphic tops from CSV",
        ],
        domain="well",
        modes=["las", "segy", "deviation", "tops", "dst", "checkshot", "auto"],
        acrisk="QUALIFY",
        is_888_hold=False,
    ),
    "geox_well_qc": ToolDiscovery(
        name="geox_well_qc",
        domain_verb="well.check_quality",
        description="Quality control checks on well data: depth monotonicity, null percentages, physical range checks, curve completeness.",
        use_when="User wants to validate well data quality, check for gaps, verify depth ordering, or assess curve completeness. Keywords: 'QC', 'quality check', 'validate well', 'check depths', 'null percentage'.",
        do_not_use_when="User wants to load new data (use geox_well_ingest) or compute petrophysical properties.",
        keywords=["qc", "quality", "validate", "check", "depth", "monotonicity", "null", "completeness", "range"],
        examples=[
            "Run QC on the A-1 well data",
            "Check if depths are monotonic",
            "What's the null percentage for GR?",
            "Validate curve ranges for well B-2",
        ],
        domain="well",
        modes=["full", "header", "curves", "depth", "completeness", "feature_info"],
        acrisk="QUALIFY",
        is_888_hold=False,
    ),
    "geox_petrophysics": ToolDiscovery(
        name="geox_petrophysics",
        domain_verb="well.derive_petrophysics",
        description="Compute petrophysical properties: Vsh, porosity, Sw, permeability, net pay. Includes LEM physics-prior inference.",
        use_when="User wants to calculate rock properties from well logs. Keywords: 'porosity', 'water saturation', 'Vsh', 'net pay', 'permeability', 'petrophysics', 'rock physics'.",
        do_not_use_when="User wants to load data (use geox_well_ingest), run QC (use geox_well_qc), or analyze seismic (use geox_seismic_compute).",
        keywords=["porosity", "sw", "vsh", "permeability", "net pay", "petrophysics", "rock physics", "lem", "archie"],
        examples=[
            "Calculate porosity from density log",
            "Compute water saturation using Archie's equation",
            "Determine net pay for the reservoir zone",
            "Run LEM inference on well A-1",
        ],
        domain="well",
        modes=["generate", "verify", "lem_inference", "stoip_feed"],
        acrisk="ADVISORY",
        is_888_hold=False,
    ),
    "geox_sequence": ToolDiscovery(
        name="geox_sequence",
        domain_verb="well.correlate",
        description="Sequence stratigraphy analysis: GR binning, parasequence packages, systems tract inference, well correlation.",
        use_when="User wants to interpret stratigraphic sequences, correlate wells, or identify depositional cycles. Keywords: 'sequence stratigraphy', 'parasequence', 'systems tract', 'correlation', 'GR motif'.",
        do_not_use_when="User wants basic well data loading or petrophysical calculations.",
        keywords=["sequence", "stratigraphy", "parasequence", "systems tract", "correlation", "gr motif", "depositional"],
        examples=[
            "Run sequence stratigraphy on well A-1",
            "Correlate wells A-1, B-2, and C-3",
            "Identify parasequence packages in the GR log",
            "What systems tract is this interval?",
        ],
        domain="well",
        modes=["single_well", "project", "preview", "section_correlation"],
        acrisk="ADVISORY",
        is_888_hold=False,
    ),
    # ── SEISMIC DOMAIN ─────────────────────────────────────────────────────────
    "geox_seismic_ingest": ToolDiscovery(
        name="geox_seismic_ingest",
        domain_verb="seismic.load_volume",
        description="Load and inspect seismic data: SEG-Y headers, trace counts, sample intervals, volume metadata.",
        use_when="User provides a SEG-Y file or wants to inspect seismic data headers. Keywords: 'load seismic', 'SEG-Y', 'inspect headers', 'seismic metadata'.",
        do_not_use_when="User wants to compute seismic attributes or interpret horizons/faults (use geox_seismic_compute or geox_seismic_interpret).",
        keywords=["segy", "seismic", "ingest", "load", "headers", "traces", "metadata", "volume"],
        examples=[
            "Load this SEG-Y file: /data/seismic/line_001.sgy",
            "Inspect the SEG-Y headers",
            "How many traces are in this volume?",
            "What's the sample interval?",
        ],
        domain="seismic",
        modes=["inspect_segy", "export_segy", "inspect_seismic_meta"],
        acrisk="QUALIFY",
        is_888_hold=False,
    ),
    "geox_seismic_compute": ToolDiscovery(
        name="geox_seismic_compute",
        domain_verb="seismic.compute",
        description="Seismic computation: synthetics, well ties, AVO analysis, attributes, seismic inversion. Time-depth anchoring uses checkshot data only.",
        use_when="User wants to compute seismic properties, create synthetics, tie wells to seismic, or analyze AVO. Keywords: 'synthetic', 'well tie', 'AVO', 'attribute', 'inversion', 'RMS amplitude'. For time-depth: checkshot only (single path).",
        do_not_use_when="User wants to load seismic data (use geox_seismic_ingest) or interpret horizons/faults (use geox_seismic_interpret).",
        keywords=["synthetic", "well tie", "avo", "attribute", "inversion", "rms", "variance", "sweetness", "impedance"],
        examples=[
            "Create a synthetic seismogram for well A-1",
            "Tie well A-1 to the seismic volume",
            "Compute RMS amplitude attribute",
            "Run AVO analysis on this CDP gather",
        ],
        domain="seismic",
        modes=[
            "synthetic",
            "well_tie",
            "time_depth_anchor",
            "anomalous_contrast",
            "attribute",
            "inversion",
            "tie_preflight",
            "tie_receipt",
            "wavelet_extract",
            "mistie_rms",
            "time_depth_calibrate",
        ],
        acrisk="ADVISORY",
        is_888_hold=False,
    ),
    "geox_seismic_interpret": ToolDiscovery(
        name="geox_seismic_interpret",
        domain_verb="seismic.interpret",
        description="Seismic interpretation: horizon detection, fault picking, volume blending, frame extraction.",
        use_when="User wants to interpret seismic data — pick horizons, identify faults, blend volumes, or extract frames. Keywords: 'horizon', 'fault', 'blend', 'interpret', 'pick'.",
        do_not_use_when="User wants to compute seismic properties (use geox_seismic_compute) or load data (use geox_seismic_ingest).",
        keywords=["horizon", "fault", "blend", "interpret", "pick", "contrast", "frame", "inline", "crossline"],
        examples=[
            "Detect horizons in this seismic volume",
            "Pick fault sticks from the interpretation",
            "Blend two seismic volumes with alpha blending",
            "Extract inline 1500 from the volume",
        ],
        domain="seismic",
        modes=["horizon_contrast", "fault_sticks", "volume_frame", "blend"],
        acrisk="ADVISORY",
        is_888_hold=False,
    ),
    "geox_vision": ToolDiscovery(
        name="geox_vision",
        domain_verb="seismic.analyze_vision",
        description="Vision-based seismic interpretation using VLMs: analyze seismic images, audit interpretations, calibrate models.",
        use_when="User has a seismic section image and wants AI interpretation, or wants to audit/calibrate vision models. Keywords: 'VLM', 'image interpretation', 'seismic image', 'vision', 'MiniMax'.",
        do_not_use_when="User has raw seismic data (use geox_seismic_compute) or wants traditional interpretation (use geox_seismic_interpret).",
        keywords=["vlm", "vision", "image", "minimax", "interpret", "audit", "calibrate", "perceptual"],
        examples=[
            "Interpret this seismic section image",
            "What structural features do you see?",
            "Audit the VLM interpretation quality",
            "Calibrate the vision model against synthetic data",
        ],
        domain="seismic",
        modes=["infer_minimax", "infer_mimo", "audit", "calibrate", "perceptual"],
        acrisk="ADVISORY",
        is_888_hold=False,
    ),
    # ── MODEL DOMAIN ───────────────────────────────────────────────────────────
    "geox_subsurface_model": ToolDiscovery(
        name="geox_subsurface_model",
        domain_verb="model.joint_inversion",
        description="Multi-physics subsurface modeling: joint inversion, gravity/magnetic forward modeling, MT/CSEM forward modeling. ⚠️ SimPEG MT → pore pressure requires 888_HOLD.",
        use_when="User wants to fuse multiple geophysical datasets, model gravity/mag anomalies, or compute MT responses. Keywords: 'joint inversion', 'gravity', 'magnetic', 'MT', 'CSEM', 'forward model'.",
        do_not_use_when="User wants seismic-only analysis (use geox_seismic_compute) or petrophysics (use geox_petrophysics).",
        keywords=["joint inversion", "gravity", "magnetic", "mt", "csem", "forward model", "subsurface", "multi-physics"],
        examples=[
            "Run joint inversion on gravity and seismic data",
            "Forward model the gravity response of this structure",
            "Compute MT apparent resistivity for a 1D model",
            "Fuse well logs and seismic for a subsurface model",
        ],
        domain="model",
        modes=["joint_inversion", "gravity_magnetic", "mt_forward"],
        acrisk="HOLD",
        is_888_hold=True,
    ),
    "geox_geomechanics": ToolDiscovery(
        name="geox_geomechanics",
        domain_verb="model.mechanics",
        description="Geomechanical analysis: elastic moduli (K, G, E, ν), coordinate transforms, block resolution.",
        use_when="User wants to compute rock mechanical properties, transform coordinates, or resolve block geometry. Keywords: 'elastic moduli', 'Youngs modulus', 'Poisson ratio', 'coordinate transform', 'blockspace'.",
        do_not_use_when="User wants petrophysical properties like porosity or saturation (use geox_petrophysics).",
        keywords=["geomechanics", "elastic", "moduli", "youngs", "poisson", "coordinate", "transform", "blockspace"],
        examples=[
            "Compute elastic moduli from well logs",
            "What's the Young's modulus at 2000m?",
            "Transform coordinates from UTM to lat/lon",
            "Resolve block dimensions from survey geometry",
        ],
        domain="model",
        modes=["derive_moduli", "blockspace", "coord_transform"],
        acrisk="QUALIFY",
        is_888_hold=False,
    ),
    # ── BASIN DOMAIN ───────────────────────────────────────────────────────────
    "geox_basin": ToolDiscovery(
        name="geox_basin",
        domain_verb="basin.profile",
        description="Basin intelligence: profiles, resolution, deep time state, Macrostrat API, spatial context, scene rendering.",
        use_when="User asks about a basin's geology, stratigraphy, location, or wants to resolve a basin name. Keywords: 'basin', 'stratigraphy', 'Macrostrat', 'deep time', 'geological history'.",
        do_not_use_when="User wants to analyze specific well or seismic data (use domain-specific tools).",
        keywords=["basin", "stratigraphy", "macrostrat", "deep time", "geological", "profile", "resolve", "scene"],
        examples=[
            "Tell me about the Malay Basin",
            "What's the stratigraphy of the Taranaki Basin?",
            "Resolve 'Gulf of Mexico' to canonical ID",
            "What geological period is this interval?",
        ],
        domain="basin",
        modes=["profile", "resolve", "macrostrat", "deep_time", "emag2", "icgem", "intake", "scene"],
        acrisk="QUALIFY",
        is_888_hold=False,
    ),
    "geox_deep_time_state": ToolDiscovery(
        name="geox_deep_time_state",
        domain_verb="basin.deep_time",
        description="Earth State Vector at any geological age: plate polygons, basin architecture, paleobathymetry, heat flow, subsidence history. Query by age (Ma), period name, or natural language.",
        use_when="User wants to know the plate configuration, basin architecture, or thermal state at a specific geological age. Keywords: 'deep time', 'plate reconstruction', 'paleobathymetry', 'subsidence', 'Jurassic', 'Cretaceous'.",
        do_not_use_when="User wants to analyze present-day data (use geox_basin for modern basin profiling).",
        keywords=[
            "deep time",
            "plate reconstruction",
            "paleobathymetry",
            "subsidence",
            "heat flow",
            "Ma",
            "geological age",
            "paleogeography",
        ],
        examples=[
            "What's the plate configuration at 100 Ma?",
            "Show the paleobathymetry of the Tethys Ocean at 50 Ma",
            "Compute subsidence history for the North Sea basin",
            "What was the heat flow in the Malay Basin during the Miocene?",
        ],
        domain="basin",
        modes=["plate_polygons", "basin_architecture", "paleobathymetry", "heat_flow", "subsidence"],
        acrisk="ADVISORY",
        is_888_hold=False,
    ),
    # ── GOVERNANCE DOMAIN ──────────────────────────────────────────────────────
    "geox_claim": ToolDiscovery(
        name="geox_claim",
        domain_verb="govern.claim",
        description="[INTERNAL] Geological claim lifecycle: create, validate, challenge, seal, attach evidence. Structured interpretation claims.",
        use_when="Internal federation use only. For creating or managing geological claim records with full epistemic lineage.",
        do_not_use_when="User wants to gather evidence (use geox_evidence) or evaluate prospects (use geox_prospect).",
        keywords=["claim", "interpretation", "validate", "challenge", "seal", "evidence", "attach"],
        examples=[
            "Create a claim that this is a stratigraphic trap",
            "Validate the reservoir quality claim",
            "Challenge the seal integrity interpretation",
            "Attach well log evidence to this claim",
        ],
        domain="governance",
        modes=["create", "validate", "challenge", "seal", "attach_evidence"],
        acrisk="HOLD",
        is_888_hold=True,
    ),
    "geox_evidence": ToolDiscovery(
        name="geox_evidence",
        domain_verb="govern.evidence",
        description="[INTERNAL] Evidence discovery and synthesis: search corpus, cross-domain synthesis, hypothesis generation, contradiction scanning.",
        use_when="Internal federation use only. For evidence synthesis, literature review, or contradiction scanning.",
        do_not_use_when="User wants to create formal claims (use geox_claim) or evaluate prospects (use geox_prospect).",
        keywords=["evidence", "synthesize", "hypothesis", "contradict", "literature", "discover", "abduct"],
        examples=[
            "Find evidence for a marine depositional environment",
            "Synthesize well and seismic evidence",
            "Generate competing hypotheses for this structure",
            "Check for contradictions in the interpretation",
        ],
        domain="governance",
        modes=["discover", "synthesize", "abduct", "contradict", "spatial_block", "ingest_literature"],
        acrisk="HOLD",
        is_888_hold=True,
    ),
    # ── EVALUATION DOMAIN ──────────────────────────────────────────────────────
    "geox_prospect": ToolDiscovery(
        name="geox_prospect",
        domain_verb="govern.prospect",
        description="[INTERNAL] Prospect evaluation: volumetrics, probability of success (POS), expected value of information (EVOI), risk assessment.",
        use_when="Internal federation use only. For prospect screening, volumetric estimation, and EVOI computation.",
        do_not_use_when="User wants to gather evidence (use geox_evidence) or make interpretation claims (use geox_claim).",
        keywords=["prospect", "volumetrics", "pos", "evoi", "risk", "stoiip", "hcpv", "evaluate"],
        examples=[
            "Evaluate the prospect at this location",
            "Compute STOIIP for the reservoir",
            "What's the probability of success?",
            "Should we drill this prospect?",
        ],
        domain="evaluation",
        modes=["screen", "appraise", "develop"],
        acrisk="HOLD",
        is_888_hold=True,
    ),
    # ── DOCTRINE DOMAIN ────────────────────────────────────────────────────────
    "geox_doctrine": ToolDiscovery(
        name="geox_doctrine",
        domain_verb="govern.doctrine",
        description="[INTERNAL] Constitutional doctrine enforcement: Anti-Beautiful-One audit, assumption registration, Gödel review, abstraction guards.",
        use_when="Internal federation use only. For doctrine audits, assumption lineage tracking, and anti-hallucination guards.",
        do_not_use_when="User wants to gather evidence or make claims (use domain-specific tools).",
        keywords=["doctrine", "audit", "assumption", "godel", "guard", "beautiful one", "abstraction"],
        examples=[
            "Audit this interpretation for the Beautiful One fallacy",
            "Register this assumption in the doctrine lineage",
            "Run a Gödel review on this claim",
            "Check if this question is too abstract for GEOX",
        ],
        domain="doctrine",
        modes=["anti_beautiful_one", "assumption_register", "godel_review", "abstraction_guard", "biostrat", "prithvi_eo"],
        acrisk="HOLD",
        is_888_hold=True,
    ),
    # ── GEOLOGICAL MODEL DOMAIN ──────────────────────────────────────────────────
    "geox_geological_model_generate": ToolDiscovery(
        name="geox_geological_model_generate",
        domain_verb="subsurface.generate_model",
        description="Deterministic 2D geological cross-section renderer. Generates stratigraphic cross-sections from structural parameters (dip angle, fault throw, strata thicknesses) using matplotlib. F2: physics-constrained, computed output — NOT AI-generated imagery.",
        use_when="You need a visual geological cross-section from structured parameters (depth, dip, fault throw, layer sequence).",
        do_not_use_when="You need real Earth data (use geox_basin with macrostrat modes) or 3D block models (Phase 2).",
        keywords=["cross-section", "geological model", "strata", "fault", "dip", "render", "matplotlib", "subsurface"],
        examples=[
            "Render a cross-section with 7 layers, 30° dip, and a 150m fault throw",
            "Generate a geological section 5km wide, 3km deep with alternating sandstone/shale layers",
            "Plot a velocity model from well log layer velocities",
        ],
        domain="earth.subsurface",
        modes=["cross_section"],
        acrisk="QUALIFY",
        is_888_hold=False,
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DISCOVERY API
# ═══════════════════════════════════════════════════════════════════════════════

CANONICAL_TOOL_NAMES: frozenset[str] = frozenset(
    [
        # Surface (12)
        "geox_well_ingest",
        "geox_well_qc",
        "geox_petrophysics",
        "geox_sequence",
        "geox_seismic_ingest",
        "geox_seismic_compute",
        "geox_seismic_interpret",
        "geox_vision",
        "geox_subsurface_model",
        "geox_geomechanics",
        "geox_basin",
        "geox_deep_time_state",
        # Internal (4)
        "geox_claim",
        "geox_evidence",
        "geox_prospect",
        "geox_doctrine",
    ]
)


def get_tool_discovery(tool_name: str) -> ToolDiscovery | None:
    """Get discovery metadata for a tool (canonical 16 only)."""
    if tool_name not in CANONICAL_TOOL_NAMES:
        return None
    return TOOL_DISCOVERY.get(tool_name)


def get_all_discoveries() -> dict[str, ToolDiscovery]:
    """Get all tool discovery metadata (canonical 16 only)."""
    return {k: v for k, v in TOOL_DISCOVERY.items() if k in CANONICAL_TOOL_NAMES}


def list_canonical_tools() -> list[str]:
    """Return all 16 canonical tool names."""
    return sorted(CANONICAL_TOOL_NAMES)


def is_canonical_tool(tool_name: str) -> bool:
    """True if this tool is one of the 16 canonical tools."""
    return tool_name in CANONICAL_TOOL_NAMES


def find_tools_by_keyword(keyword: str) -> list[ToolDiscovery]:
    """Find tools matching a keyword."""
    keyword_lower = keyword.lower()
    return [
        td
        for td in TOOL_DISCOVERY.values()
        if keyword_lower in td.keywords or keyword_lower in td.description.lower() or keyword_lower in td.use_when.lower()
    ]


def find_tools_by_query(query: str) -> list[ToolDiscovery]:
    """Find tools matching a natural language query."""
    query_lower = query.lower()
    matches = []
    for td in TOOL_DISCOVERY.values():
        # Check keywords
        if any(kw in query_lower for kw in td.keywords):
            matches.append(td)
            continue
        # Check examples
        if any(ex.lower() in query_lower for ex in td.examples):
            matches.append(td)
            continue
        # Check use_when
        if any(word in query_lower for word in td.use_when.lower().split()):
            matches.append(td)
    return matches


def format_discovery_for_llm(tool_name: str) -> str:
    """Format discovery metadata as LLM-friendly text."""
    td = TOOL_DISCOVERY.get(tool_name)
    if not td:
        return f"Tool '{tool_name}' not found in discovery registry."

    modes_str = ""
    if td.modes:
        modes_str = f"\n  Modes: {', '.join(td.modes)}"

    return f"""Tool: {td.name}
Domain: {td.domain}
Description: {td.description}
Use when: {td.use_when}
Do NOT use when: {td.do_not_use_when}
Examples:
{chr(10).join(f"  - {ex}" for ex in td.examples)}{modes_str}"""


def format_all_discoveries_for_llm() -> str:
    """Format all discoveries as LLM-friendly text."""
    sections = {}
    for td in TOOL_DISCOVERY.values():
        sections.setdefault(td.domain, []).append(td)

    result = "GEOX Tools — Quick Reference\n"
    result += "=" * 50 + "\n\n"

    for domain, tools in sorted(sections.items()):
        result += f"【{domain.upper()} DOMAIN】\n"
        for td in tools:
            result += f"\n  {td.name}\n"
            result += f"    {td.description}\n"
            result += f"    Use when: {td.use_when[:100]}...\n"
        result += "\n"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# MCP RESOURCE — Tool Discovery
# ═══════════════════════════════════════════════════════════════════════════════


def get_tool_discovery_resource() -> dict[str, Any]:
    """Return tool discovery as MCP resource for LLMs (canonical 16 only)."""
    return {
        "uri": "geox://tools/discovery",
        "name": "GEOX Tool Discovery — 16 Canonical Tools",
        "description": "Quick reference for selecting the correct GEOX tool. Use this when unsure which tool to call. Only canonical 16 tools are available.",
        "mimeType": "application/json",
        "text": {
            "canonical_count": len(CANONICAL_TOOL_NAMES),
            "tools": [
                {
                    "name": td.name,
                    "domain_verb": td.domain_verb,
                    "domain": td.domain,
                    "description": td.description,
                    "use_when": td.use_when,
                    "do_not_use_when": td.do_not_use_when,
                    "keywords": td.keywords,
                    "examples": td.examples,
                    "modes": td.modes,
                    "acrisk": td.acrisk,
                    "is_888_hold": td.is_888_hold,
                }
                for td in get_all_discoveries().values()
            ],
        },
    }
