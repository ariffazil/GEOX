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
    """LLM-optimized tool discovery metadata."""
    name: str
    description: str
    use_when: str
    do_not_use_when: str
    keywords: list[str]
    examples: list[str]
    domain: str
    modes: list[str] | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DISCOVERY REGISTRY — 15 Canonical GEOX Tools
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_DISCOVERY: dict[str, ToolDiscovery] = {

    # ── WELL DOMAIN ────────────────────────────────────────────────────────────

    "geox_well_ingest": ToolDiscovery(
        name="geox_well_ingest",
        description="Load well log data from LAS, SEG-Y, DST, deviation, or tops files. Auto-detects format.",
        use_when="User provides a LAS file, well log, DST data, deviation survey, or stratigraphic tops. Keywords: 'load well', 'ingest LAS', 'read well log', 'import DST', 'parse SEG-Y for well data'.",
        do_not_use_when="User wants to analyze seismic volumes (not well data), or wants QC checks on already-loaded data.",
        keywords=["las", "well log", "dst", "deviation", "tops", "ingest", "load", "import", "parse", "well data"],
        examples=[
            "Load this LAS file: /data/wells/A-1.las",
            "Ingest DST data from the B-2 well",
            "Read the deviation survey for well C-3",
            "Import stratigraphic tops from CSV",
        ],
        domain="well",
        modes=["las", "segy", "seismic", "deviation", "tops", "dst", "checkshot", "auto"],
    ),

    "geox_well_qc": ToolDiscovery(
        name="geox_well_qc",
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
    ),

    "geox_petrophysics": ToolDiscovery(
        name="geox_petrophysics",
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
    ),

    "geox_sequence": ToolDiscovery(
        name="geox_sequence",
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
    ),

    # ── SEISMIC DOMAIN ─────────────────────────────────────────────────────────

    "geox_seismic_ingest": ToolDiscovery(
        name="geox_seismic_ingest",
        description="Load and inspect seismic data: SEG-Y headers, trace counts, sample intervals, volume metadata.",
        use_when="User provides a SEG-Y file or wants to inspect seismic data headers. Keywords: 'load seismic', 'SEG-Y', 'inspect headers', 'seismic metadata'.",
        do_not_use_when="User wants to compute seismic attributes or interpret horizons (use geox_seismic_compute or geox_seismic_interpret).",
        keywords=["segy", "seismic", "ingest", "load", "headers", "traces", "metadata", "volume"],
        examples=[
            "Load this SEG-Y file: /data/seismic/line_001.sgy",
            "Inspect the SEG-Y headers",
            "How many traces are in this volume?",
            "What's the sample interval?",
        ],
        domain="seismic",
        modes=["inspect_segy", "export_segy", "inspect_seismic_meta"],
    ),

    "geox_seismic_compute": ToolDiscovery(
        name="geox_seismic_compute",
        description="Seismic computation: synthetics, well ties, AVO analysis, attributes, seismic inversion.",
        use_when="User wants to compute seismic properties, create synthetics, tie wells to seismic, or analyze AVO. Keywords: 'synthetic', 'well tie', 'AVO', 'attribute', 'inversion', 'RMS amplitude'.",
        do_not_use_when="User wants to load seismic data (use geox_seismic_ingest) or interpret horizons/faults (use geox_seismic_interpret).",
        keywords=["synthetic", "well tie", "avo", "attribute", "inversion", "rms", "variance", "sweetness", "impedance"],
        examples=[
            "Create a synthetic seismogram for well A-1",
            "Tie well A-1 to the seismic volume",
            "Compute RMS amplitude attribute",
            "Run AVO analysis on this CDP gather",
        ],
        domain="seismic",
        modes=["synthetic", "well_tie", "time_depth_anchor", "anomalous_contrast", "attribute", "inversion"],
    ),

    "geox_seismic_interpret": ToolDiscovery(
        name="geox_seismic_interpret",
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
    ),

    "geox_vision": ToolDiscovery(
        name="geox_vision",
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
    ),

    # ── MODEL DOMAIN ───────────────────────────────────────────────────────────

    "geox_subsurface_model": ToolDiscovery(
        name="geox_subsurface_model",
        description="Multi-physics subsurface modeling: joint inversion, gravity/magnetic forward modeling, MT/CSEM forward modeling.",
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
    ),

    "geox_geomechanics": ToolDiscovery(
        name="geox_geomechanics",
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
    ),

    # ── BASIN DOMAIN ───────────────────────────────────────────────────────────

    "geox_basin": ToolDiscovery(
        name="geox_basin",
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
    ),

    # ── GOVERNANCE DOMAIN ──────────────────────────────────────────────────────

    "geox_claim": ToolDiscovery(
        name="geox_claim",
        description="Geological claim lifecycle: create, validate, challenge, seal, attach evidence. Structured interpretation claims.",
        use_when="User wants to make a geological interpretation claim, validate existing claims, or attach evidence. Keywords: 'claim', 'interpretation', 'validate', 'challenge', 'seal'.",
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
    ),

    "geox_evidence": ToolDiscovery(
        name="geox_evidence",
        description="Evidence discovery and synthesis: search corpus, cross-domain synthesis, hypothesis generation, contradiction scanning.",
        use_when="User wants to find evidence, synthesize across domains, generate hypotheses, or check for contradictions. Keywords: 'evidence', 'synthesize', 'hypothesis', 'contradict', 'literature'.",
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
    ),

    # ── EVALUATION DOMAIN ──────────────────────────────────────────────────────

    "geox_prospect": ToolDiscovery(
        name="geox_prospect",
        description="Prospect evaluation: volumetrics, probability of success (POS), expected value of information (EVOI), risk assessment.",
        use_when="User wants to evaluate a hydrocarbon prospect, compute volumetrics, or assess drilling risk. Keywords: 'prospect', 'volumetrics', 'POS', 'EVOI', 'risk', 'STOIIP'.",
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
    ),

    # ── DOCTRINE DOMAIN ────────────────────────────────────────────────────────

    "geox_doctrine": ToolDiscovery(
        name="geox_doctrine",
        description="Constitutional doctrine enforcement: Anti-Beautiful-One audit, assumption registration, Gödel review, abstraction guards.",
        use_when="User wants to audit interpretation quality, register assumptions, check for over-abstraction, or run constitutional reviews. Keywords: 'audit', 'assumption', 'Gödel', 'doctrine', 'guard'.",
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
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DISCOVERY API
# ═══════════════════════════════════════════════════════════════════════════════

def get_tool_discovery(tool_name: str) -> ToolDiscovery | None:
    """Get discovery metadata for a tool."""
    return TOOL_DISCOVERY.get(tool_name)


def get_all_discoveries() -> dict[str, ToolDiscovery]:
    """Get all tool discovery metadata."""
    return TOOL_DISCOVERY.copy()


def find_tools_by_keyword(keyword: str) -> list[ToolDiscovery]:
    """Find tools matching a keyword."""
    keyword_lower = keyword.lower()
    return [
        td for td in TOOL_DISCOVERY.values()
        if keyword_lower in td.keywords
        or keyword_lower in td.description.lower()
        or keyword_lower in td.use_when.lower()
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
{chr(10).join(f'  - {ex}' for ex in td.examples)}{modes_str}"""


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
    """Return tool discovery as MCP resource for LLMs."""
    return {
        "uri": "geox://tools/discovery",
        "name": "GEOX Tool Discovery",
        "description": "Quick reference for selecting the correct GEOX tool. Use this when unsure which tool to call.",
        "mimeType": "application/json",
        "text": {
            "tools": [
                {
                    "name": td.name,
                    "domain": td.domain,
                    "description": td.description,
                    "use_when": td.use_when,
                    "do_not_use_when": td.do_not_use_when,
                    "keywords": td.keywords,
                    "examples": td.examples,
                    "modes": td.modes,
                }
                for td in TOOL_DISCOVERY.values()
            ]
        }
    }
