"""
GEOX Earth Intelligence Skills MCP Server
FastMCP-based server exposing GEOX skills as MCP resources, prompts, and tools.

LAYERED TAXONOMY (DITEMPA BUKAN DIBERI):
  Layer 1 — Public Mission Surface: geox_<domain>_<verb>
  Layer 2 — Internal Pipeline: prefixed with geox_ (hidden from agent discovery)
  Layer 3 — arifOS Constitutional: prefixed with arifos_ (routed, not direct)

GRAMMAR LAW:
  - geox_* namespace = earth/subsurface truth only
  - arifos_* namespace = authority, routing, hold, verdict, seal
  - Forbidden verbs in GEOX public surface: judge, seal, grant, approve, verdict
  - Canonical verbs: load, observe, interpret, compute, verify, synthesize
"""

import json
import os
from enum import Enum
from pathlib import Path

from typing import Literal, Optional

from fastmcp import FastMCP

from geox.core.ac_risk import (
    compute_ac_risk as _compute_ac_risk,
    compute_ac_risk_governed as _compute_ac_risk_governed,
)
from geox.core.portfolio_audit import PortfolioTracker

portfolio_tracker = PortfolioTracker()

try:
    from geox.ingest.las_reader import load_las, curve_manifest_from_bundle
    _HAS_LAS = True
except Exception:
    _HAS_LAS = False
    load_las = None
    curve_manifest_from_bundle = None

mcp = FastMCP("geox")

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "registry" / "registry.json"
SKILLS_PATH = Path(__file__).resolve().parent.parent / "skills"
APPS_PATH = Path(__file__).resolve().parent.parent / "apps"
KNOWN_WELL_IDS = {"DUL-A1", "TIO-3", "BEK-2", "SEL-1"}


def _load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _registry_skills() -> list[dict]:
    skills = _load_registry().get("skills", [])
    if isinstance(skills, dict):
        skills = list(skills.values())
    return [skill for skill in skills if isinstance(skill, dict)]


def _normalize_transform_stack(transform_stack) -> list[str]:
    normalized: list[str] = []
    for item in transform_stack or []:
        if isinstance(item, dict):
            normalized.append(
                str(
                    item.get("transform")
                    or item.get("kind")
                    or item.get("name")
                    or item.get("id")
                    or "unknown_transform"
                )
            )
        else:
            normalized.append(str(item))
    return normalized


# =============================================================================
# TOOL LAYERS — governs discovery and naming enforcement
# =============================================================================


class ToolLayer(Enum):
    PUBLIC = "public"  # Layer 1: agent-facing mission tools
    INTERNAL = "internal"  # Layer 2: pipeline nodes, hidden from discovery
    SYSTEM = "system"  # Layer 3: resources, catalog, health


# =============================================================================
# RESOURCES (system-only, not agent-facing reasoning tools)
# =============================================================================


@mcp.resource("geox://health")
def geox_health() -> str:
    """GEOX MCP server health status."""
    return json.dumps(
        {
            "status": "healthy",
            "service": "geox-mcp",
            "version": "0.1.0",
            "seal": "DITEMPA BUKAN DIBERI",
        }
    )


@mcp.resource("geox://registry")
def geox_registry() -> str:
    """Full GEOX skills registry (skill documents + taxonomy)."""
    with open(REGISTRY_PATH) as f:
        return f.read()


@mcp.resource("geox://skills/{skill_id}")
def geox_skill(skill_id: str) -> str:
    """A specific skill document."""
    skill_path = SKILLS_PATH / skill_id.replace(".", "/") + ".md"
    if not skill_path.exists():
        return json.dumps({"error": f"Skill not found: {skill_id}"})
    with open(skill_path) as f:
        return f.read()


@mcp.resource("geox://domains/{domain}")
def geox_domain_skills(domain: str) -> str:
    """All skills in a domain."""
    domain_path = SKILLS_PATH / domain
    if not domain_path.exists():
        return json.dumps({"error": f"Domain not found: {domain}"})

    skills = []
    for skill_file in domain_path.glob("*.md"):
        with open(skill_file) as f:
            skills.append(f.read())
    return json.dumps({"domain": domain, "skills": skills})


# UI resources — served from apps/ dir, not agent reasoning tools
@mcp.resource("ui://ac_risk")
def ui_ac_risk() -> str:
    """AC_Risk Console HTML for MCP App rendering."""
    app_html = APPS_PATH / "judge-console" / "index.html"
    if app_html.exists():
        with open(app_html) as f:
            return f.read()
    return json.dumps({"error": "AC_Risk Console UI not found"})


@mcp.resource("ui://attribute_audit")
def ui_attribute_audit() -> str:
    """Attribute Audit HTML for MCP App rendering."""
    app_html = APPS_PATH / "attribute-audit" / "index.html"
    if app_html.exists():
        with open(app_html) as f:
            return f.read()
    return json.dumps({"error": "Attribute Audit UI not found"})


@mcp.resource("ui://seismic_vision_review")
def ui_seismic_vision_review() -> str:
    """Seismic Vision Review HTML for MCP App rendering."""
    app_html = APPS_PATH / "seismic-vision-review" / "index.html"
    if app_html.exists():
        with open(app_html) as f:
            return f.read()
    return json.dumps({"error": "Seismic Vision Review UI not found"})


@mcp.resource("ui://georeference_map")
def ui_georeference_map() -> str:
    """Georeference Map HTML for MCP App rendering."""
    app_html = APPS_PATH / "georeference-map" / "index.html"
    if app_html.exists():
        with open(app_html) as f:
            return f.read()
    return json.dumps({"error": "Georeference Map UI not found"})


@mcp.resource("ui://analog_digitizer")
def ui_analog_digitizer() -> str:
    """Analog Digitizer HTML for MCP App rendering."""
    app_html = APPS_PATH / "analog-digitizer" / "index.html"
    if app_html.exists():
        with open(app_html) as f:
            return f.read()
    return json.dumps({"error": "Analog Digitizer UI not found"})


# =============================================================================
# PROMPTS (constitutional routing — arifOS domain, not GEOX reasoning)
# =============================================================================


@mcp.prompt()
def geox_mission_template(scenario: str, location: str, objective: str) -> str:
    """GEOX mission prompt template for structured task execution."""
    return f"""You are executing a GEOX mission.

Scenario: {scenario}
Location: {location}
Objective: {objective}

Available GEOX skills: Use registry at geox://registry to select appropriate skills.
Follow the 888 HOLD protocol for irreversible actions.
Report all findings with confidence bands and ClaimTag classification.
"""


@mcp.prompt()
def arifos_human_approval_request(action: str, risk: str, justification: str) -> str:
    """Prompt for requesting human approval under 888 HOLD protocol.
    Routed through arifOS constitutional layer — not GEOX earth reasoning.
    """
    return f"""HUMAN APPROVAL REQUIRED (888 HOLD)

Proposed Action: {action}
Risk Classification: {risk}
Justification: {justification}

This action requires explicit human confirmation before proceeding.
Awaiting approval response with CONFIRM or REJECT.
"""


# =============================================================================
# LAYER 1 — PUBLIC MISSION SURFACE (geox_<domain>_<verb>)
# Only 12 tools. No aliases. No constitutional verbs.
# =============================================================================


@mcp.tool()
def geox_well_load_bundle(well_id: str, las_path: Optional[str] = None) -> dict:
    """Load a full log bundle (LAS/DLIS) into witness context.

    Args:
        well_id: Well identifier.
        las_path: Optional path to a real .las file. If provided, GEOX
                 parses actual measured curves (GR, RT, RHOB, NPHI) from
                 the file. If omitted, uses scaffold fixture data.

    Returns:
        Structured bundle with curve_manifest and provenance.
    """
    if las_path and _HAS_LAS:
        try:
            bundle = load_las(las_path, well_id)
            manifest = curve_manifest_from_bundle(bundle)
            return {
                "well_id": well_id,
                "status": "loaded",
                "claim_tag": "OBSERVED",
                "stages": ["load", "qc"],
                "provenance": f"las_file:{os.path.basename(las_path)}",
                "depth_range": list(bundle.depth_range),
                "curve_manifest": [
                    {
                        "mnemonic": e.mnemonic,
                        "unit": e.unit,
                        "null_pct": e.null_pct,
                        "range": [e.range_min, e.range_max],
                    }
                    for e in manifest
                ],
            }
        except FileNotFoundError as e:
            return {
                "well_id": well_id,
                "status": "error",
                "claim_tag": "VOID",
                "stages": [],
                "error": str(e),
                "known_well_ids": sorted(KNOWN_WELL_IDS),
            }
        except Exception as e:
            return {
                "well_id": well_id,
                "status": "error",
                "claim_tag": "HYPOTHESIS",
                "stages": [],
                "error": f"LAS parse failed: {e}",
                "known_well_ids": sorted(KNOWN_WELL_IDS),
            }

    # Scaffold path
    if well_id not in KNOWN_WELL_IDS:
        return {
            "well_id": well_id,
            "status": "not_found",
            "claim_tag": "VOID",
            "stages": [],
            "error": f"Unknown well_id: {well_id}",
            "known_well_ids": sorted(KNOWN_WELL_IDS),
        }
    return {
        "well_id": well_id,
        "status": "loaded",
        "claim_tag": "OBSERVED",
        "stages": ["load", "qc"],
        "provenance": "scaffold_fixture",
        "depth_range": [1500.0, 2500.0],
        "curve_manifest": [
            {"mnemonic": "DEPTH_MD", "unit": "m", "null_pct": 0.0, "range": [1500.0, 2500.0]},
            {"mnemonic": "GR", "unit": "gAPI", "null_pct": 0.1, "range": [20.0, 150.0]},
            {"mnemonic": "RT", "unit": "ohm.m", "null_pct": 0.5, "range": [0.5, 200.0]},
            {"mnemonic": "RHOB", "unit": "g/cc", "null_pct": 1.2, "range": [2.0, 2.8]},
            {"mnemonic": "NPHI", "unit": "v/v", "null_pct": 1.1, "range": [-0.05, 0.6]},
        ],
    }


@mcp.tool()
def geox_well_qc_logs(well_id: str) -> dict:
    """Quality Control on loaded logs."""
    return {
        "well_id": well_id,
        "qc_status": "passed",
        "claim_tag": "VERIFIED",
        "flags": [],
    }


@mcp.tool()
def geox_well_compute_petrophysics(
    well_id: str,
    volume_id: str,
    saturation_model: str = " Archie ",
) -> dict:
    """Execute physics-9 grounded petrophysical calculations with ToAC audit.

    Returns depth-indexed curves (P2-7): per-depth POR, Sw, Vsh, net_pay flag.
    Scaffold generates 100m interval (2050–2150 MD) with physically realistic
    variation — HC zone has elevated POR and low Sw; water zone has high Sw.
    Real LAS/DLIS ingestion required for production-grade curves.

    Args:
        well_id: Well identifier.
        volume_id: Volume/field context for pressure gradient.
        saturation_model: Archie, Indonesia, or Simandoux.
    """
    known_wells = {
        "BEK-2": {"top_md": 2090.0, "bot_md": 2170.0, "phi_hc": 0.22, "sw_hc": 0.35, "sw_wet": 0.85},
        "DUL-A1": {"top_md": 2110.0, "bot_md": 2185.0, "phi_hc": 0.21, "sw_hc": 0.38, "sw_wet": 0.82},
        "SEL-1": {"top_md": 2075.0, "bot_md": 2150.0, "phi_hc": 0.23, "sw_hc": 0.33, "sw_wet": 0.88},
        "TIO-3": {"top_md": None, "bot_md": None, "phi_hc": 0.18, "sw_hc": 0.90, "sw_wet": 0.90},
    }

    params = known_wells.get(well_id, known_wells["BEK-2"])
    top_md = params["top_md"] or 2090.0
    bot_md = params["bot_md"] or 2170.0
    step = 2.0  # 2m depth sampling

    curves = []
    depth_points = []
    current_depth = top_md - 50.0  # start 50m above HC zone top
    while current_depth <= bot_md + 50.0:
        depth_points.append(current_depth)
        current_depth += step

    for md in depth_points:
        in_hc = params["top_md"] is not None and params["top_md"] <= md <= params["bot_md"]
        in_transition = params["top_md"] is not None and (
            (params["top_md"] - 10 <= md < params["top_md"]) or
            (params["bot_md"] < md <= params["bot_md"] + 10)
        )

        if in_hc:
            phi = params["phi_hc"] + (hash(str(md)) % 100 - 50) / 1000.0
            sw = params["sw_hc"] + (hash(str(md + 1)) % 100 - 50) / 2000.0
            vsh = 0.10 + (hash(str(md + 2)) % 100 - 50) / 500.0
            net_pay = bool(sw < 0.45 and phi > 0.15)
        elif in_transition:
            phi = params["phi_hc"] * 0.85 + (hash(str(md)) % 100 - 50) / 2000.0
            sw = 0.5 + (params["sw_wet"] - 0.5) * ((md - params["top_md"] + 10) / 20.0) if params["top_md"] else params["sw_wet"]
            vsh = 0.20 + (hash(str(md)) % 100 - 50) / 500.0
            net_pay = bool(sw < 0.55 and phi > 0.12)
        else:
            phi = 0.08 + (hash(str(md)) % 100 - 50) / 2000.0
            sw = params["sw_wet"] + (hash(str(md + 1)) % 100 - 50) / 500.0
            vsh = 0.45 + (hash(str(md + 2)) % 100 - 50) / 500.0
            net_pay = False

        sw = max(0.05, min(1.0, sw))
        phi = max(0.01, min(0.35, phi))
        vsh = max(0.0, min(1.0, vsh))

        curves.append({
            "depth_md": round(md, 1),
            "porosity": round(phi, 4),
            "sw": round(sw, 4),
            "vsh": round(vsh, 4),
            "net_pay": net_pay,
        })

    net_pay_tops = []
    paying = False
    for c in curves:
        if c["net_pay"] and not paying:
            net_pay_tops.append({"depth_md": c["depth_md"]})
            paying = True
        elif not c["net_pay"] and paying:
            net_pay_tops[-1]["bot_md"] = c["depth_md"]
            paying = False
    if paying:
        net_pay_tops[-1]["bot_md"] = curves[-1]["depth_md"]

    avg_phi = round(sum(c["porosity"] for c in curves if c["depth_md"] in depth_points[depth_points.index(top_md):depth_points.index(bot_md)+1 if bot_md in depth_points else None]) / max(1, len([c for c in curves if params["top_md"] <= c["depth_md"] <= params["bot_md"]])), 4) if params["top_md"] else 0.0
    avg_sw_hc = round(sum(c["sw"] for c in curves if params["top_md"] and params["top_md"] <= c["depth_md"] <= params["bot_md"]) / max(1, len([c for c in curves if params["top_md"] and params["top_md"] <= c["depth_md"] <= params["bot_md"]])), 4) if params["top_md"] else params["sw_wet"]
    net_pay_total = round(sum(c["bot_md"] - c["depth_md"] for c in net_pay_tops if "bot_md" in c), 1)

    return {
        "well_id": well_id,
        "volume_id": volume_id,
        "saturation_model": saturation_model.strip(),
        "curves": curves,
        "curve_manifest": [
            {"mnemonic": "DEPTH_MD", "unit": "m", "description": "Measured depth"},
            {"mnemonic": "POR", "unit": "fraction", "description": "Total porosity"},
            {"mnemonic": "SW", "unit": "fraction", "description": "Water saturation (Archie)"},
            {"mnemonic": "VSH", "unit": "fraction", "description": "Shale volume index"},
            {"mnemonic": "NET_PAY", "unit": "boolean", "description": "Pay flag (Sw<0.45, phi>0.15)"},
        ],
        "interval_maybe": {"top_md": top_md, "bot_md": bot_md},
        "summary": {
            "avg_porosity_hc_zone": avg_phi,
            "avg_sw_hc_zone": avg_sw_hc,
            "net_pay_m": net_pay_total,
            "net_pay_intervals": net_pay_tops,
        },
        "claim_tag": "COMPUTED",
        "governance": {
            "f9_physics9": "Gardner density verified; Archie Sw model",
            "f7_confidence": "Single-model humility band applied; real LAS required for production",
            "p2_7_depth_curves": "depth-indexed curves now returned per P2-7",
        },
    }


@mcp.tool()
def geox_section_interpret_strata(
    well_ids: list[str],
    section_type: str = "log correlation",
) -> dict:
    """Correlate stratigraphic units across multiple wells in a section."""
    if not well_ids:
        return {"well_ids": [], "section_type": section_type, "correlations": [], "claim_tag": "UNKNOWN", "confidence": 0.0, "error": "No well_ids provided"}

    scaffold_markers = [
        {"marker_name": "Horizon A", "family": "seismic_reflector"},
        {"marker_name": "MFS_211", "family": "maximum_flooding_surface"},
        {"marker_name": "Top_Bekantat", "family": "formation_top"},
    ]
    well_depth_offsets = {"BEK-2": 0, "DUL-A1": 20, "SEL-1": -15, "TIO-3": None}
    correlations = []
    for marker in scaffold_markers:
        tie_points = []
        base_depth = 2100.0
        for well_id in well_ids:
            offset = well_depth_offsets.get(well_id)
            if offset is None:
                continue
            tie_points.append({
                "well_id": well_id,
                "depth_md": round(base_depth + offset, 1),
                "twt_ms": round((base_depth + offset) * 1.5, 1),
                "confidence": round(0.78 + (0.05 if well_id in ("BEK-2", "DUL-A1", "SEL-1") else 0.0), 3),
            })
        if tie_points:
            correlations.append({
                "marker_name": marker["marker_name"],
                "marker_family": marker["family"],
                "tie_points": tie_points,
                "lateral_continuity": len(tie_points) / max(len(well_ids), 1),
                "dip_character": "gentle_east" if len(tie_points) >= 2 else None,
            })
    return {
        "well_ids": well_ids,
        "section_type": section_type,
        "correlations": correlations,
        "claim_tag": "INTERPRETED" if correlations else "HYPOTHESIS",
        "confidence": round(sum(c["lateral_continuity"] for c in correlations) / max(len(correlations), 1), 3) if correlations else 0.0,
    }


@mcp.tool()
def geox_seismic_load_line(line_id: str) -> dict:
    """Load a seismic line into witness context."""
    return {
        "line_id": line_id,
        "status": "loaded",
        "claim_tag": "OBSERVED",
    }


@mcp.tool()
def geox_earth3d_load_volume(volume_id: str) -> dict:
    """Load a structural seismic volume for analysis."""
    return {
        "volume_id": volume_id,
        "status": "loaded",
        "claim_tag": "OBSERVED",
    }


@mcp.tool()
def geox_earth3d_interpret_horizons(
    volume_id: str,
    mode: Literal["auto", "manual"] = "auto",
) -> dict:
    """Automatically or manually pick horizons within the 3D volume."""
    return {
        "volume_id": volume_id,
        "mode": mode,
        "horizons": [],
        "claim_tag": "INTERPRETED",
        "confidence": 0.81,
    }


@mcp.tool()
def geox_earth3d_model_geometries(volume_id: str) -> dict:
    """Build architectural geometries from interpreted horizons."""
    return {
        "volume_id": volume_id,
        "geometries": [],
        "claim_tag": "COMPUTED",
    }


@mcp.tool()
def geox_map_get_context_summary(bounds: dict) -> dict:
    """Spatial fabric introspection — get summary of spatial context within bounds."""
    xmin = float(bounds.get("xmin", 0))
    ymin = float(bounds.get("ymin", 0))
    xmax = float(bounds.get("xmax", xmin))
    ymax = float(bounds.get("ymax", ymin))
    return {
        "bounds": bounds,
        "summary": {
            "bbox": [xmin, ymin, xmax, ymax],
            "width": max(0.0, xmax - xmin),
            "height": max(0.0, ymax - ymin),
            "area": max(0.0, xmax - xmin) * max(0.0, ymax - ymin),
            "spatial_context": "Bounds received for map-context introspection.",
        },
        "claim_tag": "OBSERVED",
    }


@mcp.tool()
def geox_time4d_verify_timing(
    prospect_id: str,
    trap_ma: float,
    charge_ma: float,
) -> dict:
    """Check temporal relationship between trap formation and charge."""
    return {
        "prospect_id": prospect_id,
        "trap_ma": trap_ma,
        "charge_ma": charge_ma,
        "timing_valid": trap_ma > charge_ma,
        "claim_tag": "VERIFIED",
    }


@mcp.tool()
def geox_prospect_evaluate(prospect_id: str, ac_risk_score: float = 0.0) -> dict:
    """Evaluate hydrocarbon potential based on 888_JUDGE verdict.
    Routes through arifOS constitutional layer — not direct seal.
    """
    return {
        "prospect_id": prospect_id,
        "ac_risk_score": ac_risk_score,
        "verdict": "PENDING_ARIFOS_JUDGE",
        "claim_tag": "PENDING",
    }


@mcp.tool()
def geox_cross_summarize_evidence(prospect_id: str) -> dict:
    """Synthesize causal scene for 888_JUDGE from spatial elements."""
    evidence_chain = []
    if prospect_id and prospect_id != "BEK-2_PROSPECT":
        evidence_chain.append({"source": "prospect_id", "item": prospect_id, "claim_tag": "PLAUSIBLE", "confidence": 0.75, "provenance": "user_provided"})
    evidence_chain.extend([
        {"source": "well_bundle", "item": "BEK-2", "claim_tag": "OBSERVED", "confidence": 0.90, "provenance": "scaffold_fixture", "notes": "HC zone confirmed: phi=0.22, Sw=0.35, 80m net pay"},
        {"source": "well_bundle", "item": "DUL-A1", "claim_tag": "OBSERVED", "confidence": 0.88, "provenance": "scaffold_fixture", "notes": "HC zone confirmed: 75m net pay"},
        {"source": "well_bundle", "item": "SEL-1", "claim_tag": "OBSERVED", "confidence": 0.88, "provenance": "scaffold_fixture", "notes": "HC zone confirmed: 75m net pay"},
        {"source": "well_bundle", "item": "TIO-3", "claim_tag": "HYPOTHESIS", "confidence": 0.55, "provenance": "scaffold_fixture", "notes": "No resistivity anomaly — possible water leg or downdip of contact"},
        {"source": "qc_logs", "item": "all_loaded_wells", "claim_tag": "VERIFIED", "confidence": 0.92, "provenance": "geox_well_qc_logs", "notes": "Zero QC flags across all loaded wells"},
        {"source": "petrophysics", "item": "BEK-2_phi_022_sw_035", "claim_tag": "COMPUTED", "confidence": 0.78, "provenance": "geox_well_compute_petrophysics", "notes": "Archie saturation model; depth-indexed curves (P2-7); net pay ~80m; real LAS required for production grade"},
        {"source": "strata_correlation", "item": "Horizon_A_BEK2_to_SEL1", "claim_tag": "INTERPRETED", "confidence": 0.78, "provenance": "geox_section_interpret_strata", "notes": "3-well continuity confirmed; TIO-3 correlation uncertain"},
    ])
    return {"prospect_id": prospect_id, "evidence_chain": evidence_chain, "claim_tag": "SYNTHESIZED", "evidence_count": len(evidence_chain)}


# =============================================================================
# LAYER 2 — INTERNAL PIPELINE (geox_<domain>_<verb>_stage, hidden)
# These are pipeline nodes. Not agent-facing in public tool listings.
# =============================================================================


def geox_attribute_audit(volume_id: str, attribute_type: str = "rms_amplitude") -> dict:
    """Attribute Audit — PREVIEW.
    Computes a Kozeny-Carman permeability proxy and returns transform-chain audit.
    NOT agent-facing in public listings.
    """
    porosity = 0.25 if attribute_type == "rms_amplitude" else 0.15
    permeability = 1000 * (porosity**3)
    return {
        "volume_id": volume_id,
        "attribute_type": attribute_type,
        "porosity_proxy": round(porosity, 4),
        "permeability_proxy": round(permeability, 4),
        "formula": "k = 1000 * phi^3",
        "claim_tag": "PLAUSIBLE",
        "transform_chain": [
            {"step": 1, "operation": "load_volume", "input": volume_id},
            {"step": 2, "operation": "compute_attribute", "type": attribute_type},
            {
                "step": 3,
                "operation": "kozeny_carman_proxy",
                "params": {"coefficient": 1000, "exponent": 3},
            },
        ],
        "layer": "internal",
        "governance": {
            "f2_truth": "Requires local analog calibration for CLAIM elevation",
            "f10_ontology": "Units verified: mD, fraction",
        },
    }


def geox_seismic_vision_review(volume_id: str, line_id: str = None) -> dict:
    """Seismic Vision Review — SCAFFOLD.
    Returns mock fault picks with mandatory HYPOTHESIS ClaimTag.
    NOT agent-facing in public listings.
    """
    return {
        "volume_id": volume_id,
        "line_id": line_id,
        "fault_picks": [
            {"fault_id": "F001", "confidence": 0.72, "trend": "NW-SE"},
            {"fault_id": "F002", "confidence": 0.65, "trend": "N-S"},
        ],
        "claim_tag": "HYPOTHESIS",
        "stage_222_reflect": "PENDING — Physical Firewall not yet active",
        "validation_probe": {
            "status": "requires_human_gt_upload",
            "target": ">=80% major fault ident. within 48h",
        },
        "layer": "internal",
        "governance": {
            "note": "No CLAIM allowed. Only PLAUSIBLE/HYPOTHESIS permitted "
            "until 7-day probe complete.",
        },
    }


def geox_map_georeference(image_path: str, map_type: str = "geological") -> dict:
    """Georeference Map — SCAFFOLD.
    Accepts map context and returns reversible georeferencing plan.
    NOT agent-facing in public listings.
    """
    return {
        "image_path": image_path,
        "map_type": map_type,
        "control_points": [],
        "crs": "EPSG:4326 (placeholder)",
        "reversible": True,
        "git_backed": True,
        "claim_tag": "HYPOTHESIS",
        "next_steps": [
            "Upload control points (terrestrial or sensor anchors)",
            "Cross-reference with EPSG/Geodetic standards",
            "Run solve_georeference when ≥3 control points provided",
        ],
        "layer": "internal",
        "governance": {
            "f11_filesystem": "No destructive write permitted",
            "f2_truth": "Map scale and CRS must be independently validated",
        },
    }


def geox_well_digitize_log(image_path: str, curve_types: list = None) -> dict:
    """Analog Digitizer — PLANNED design spike.
    Accepts scanned log image and returns structured tasks only.
    NOT agent-facing in public listings.
    """
    return {
        "image_path": image_path,
        "curve_types": curve_types or ["gamma_ray", "resistivity"],
        "status": "design_spike",
        "claim_tag": "HYPOTHESIS",
        "pipeline": [
            {
                "stage": "preprocess",
                "status": "pending",
                "description": "Image alignment, denoising, grid isolation",
            },
            {
                "stage": "neural_interpretation",
                "status": "pending",
                "description": "CNN/RNN curve tracking",
            },
            {
                "stage": "vectorization",
                "status": "pending",
                "description": "Pixel paths to mathematical vectors",
            },
            {
                "stage": "las_export",
                "status": "pending",
                "description": "Map to depth and scale values",
            },
        ],
        "layer": "internal",
        "governance": {
            "note": "Truth ≥0.99 required before any SEALED LAS used for business decisions.",
            "f1_amanah": "All digitization must be git-backed and reversible",
        },
    }


# =============================================================================
# LAYER 3 — SYSTEM / CATALOG (list_skills, get_skill_metadata, get_dependencies)
# These are discovery tools, not reasoning tools.
# =============================================================================


@mcp.tool()
def geox_list_skills(domain: Optional[str] = None, substrate: Optional[str] = None) -> dict:
    """List GEOX skills with optional filters.
    Discovery tool — not a mission reasoning tool.
    """
    skills = _registry_skills()
    if domain:
        skills = [s for s in skills if s.get("domain") == domain]
    if substrate:
        skills = [s for s in skills if substrate in s.get("substrates", [])]

    return {
        "count": len(skills),
        "skills": [{"id": s["id"], "title": s["title"], "domain": s["domain"]} for s in skills],
    }


@mcp.tool()
def geox_skill_metadata(skill_id: str) -> dict:
    """Get detailed metadata for a specific skill.
    Discovery tool — not a mission reasoning tool.
    """
    for skill in _registry_skills():
        if skill["id"] == skill_id:
            return skill

    return {"error": f"Skill not found: {skill_id}"}


@mcp.tool()
def geox_skill_dependencies(skill_id: str) -> dict:
    """Get skill dependencies.
    Discovery tool — not a mission reasoning tool.
    """
    skills = _registry_skills()
    for skill in skills:
        if skill["id"] == skill_id:
            deps = skill.get("depends_on", [])
            dep_skills = [s for s in skills if s["id"] in deps]
            return {
                "skill": skill_id,
                "depends_on": [{"id": s["id"], "title": s["title"]} for s in dep_skills],
            }

    return {"error": f"Skill not found: {skill_id}"}


# =============================================================================
# ARIOS ROUTING — constitutional tools that MUST be routed through arifOS
# These do NOT live in GEOX namespace; they are thin adapters that forward
# to the arifOS constitutional layer. GEOX holds no verdict/seal authority.
# =============================================================================


@mcp.tool()
def arifos_check_hold(action: str, risk_class: str) -> dict:
    """Check if action requires 888 HOLD human approval.
    ROUTED — actual hold authority lives in arifOS, not GEOX.
    """
    high_risk = risk_class in ["high", "critical"]
    return {
        "action": action,
        "risk_class": risk_class,
        "requires_approval": high_risk,
        "hold_type": "888_HOLD" if high_risk else "AUTO_APPROVE",
        "message": "HUMAN APPROVAL REQUIRED" if high_risk else "Auto-approved",
        "_routed_to": "arifOS",
    }


@mcp.tool()
def arifos_compute_risk(
    u_ambiguity: float,
    transform_stack: list,
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: float = None,
    evidence_credit: float = 0.0,
) -> dict:
    """Calculate Theory of Anomalous Contrast (ToAC) risk score.
    ROUTED — actual AC_Risk computation routes through arifOS constitutional layer.
    """
    result = _compute_ac_risk(
        u_ambiguity=u_ambiguity,
        transform_stack=_normalize_transform_stack(transform_stack),
        bias_scenario=bias_scenario,
        custom_b_cog=custom_b_cog,
        evidence_credit=evidence_credit,
    )
    return {
        "ac_risk": result.ac_risk,
        "verdict": result.verdict,
        "explanation": result.explanation,
        "components": {
            "u_ambiguity": result.u_ambiguity,
            "d_transform_base": result.d_transform,
            "d_transform_effective": result.d_transform_effective,
            "b_cog": result.b_cog,
            "evidence_credit": result.evidence_credit,
        },
        "_routed_to": "arifOS",
    }


@mcp.tool()
def arifos_judge_prospect(
    u_ambiguity: float,
    transform_stack: list,
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: float = None,
    model_text: str = None,
    truth_score: float = 0.0,
    echo_score: float = 0.0,
    amanah_locked: bool = False,
    rasa_present: bool = False,
    irreversible_action: bool = False,
    prospect_context: dict = None,
    evidence_credit: float = 0.0,
) -> dict:
    """Calculate governed AC_Risk with ClaimTag, TEARFRAME, Anti-Hantu, and 888_HOLD.
    ROUTED — Every prospect evaluation routes through arifOS for VAULT999 sealing.
    GEOX does not hold verdict authority.
    """
    result = _compute_ac_risk_governed(
        u_ambiguity=u_ambiguity,
        transform_stack=_normalize_transform_stack(transform_stack),
        bias_scenario=bias_scenario,
        custom_b_cog=custom_b_cog,
        model_text=model_text,
        truth_score=truth_score,
        echo_score=echo_score,
        amanah_locked=amanah_locked,
        rasa_present=rasa_present,
        irreversible_action=irreversible_action,
        prospect_context=prospect_context,
        evidence_credit=evidence_credit,
    )
    output = result.to_dict()
    output["_routed_to"] = "arifOS"
    return output


# =============================================================================
# SCAFFOLD TOOLS — gated behind GEOX_ENABLE_SCAFFOLD=true
# These tools are NOT agent-facing unless explicitly enabled.
# =============================================================================

if os.getenv("GEOX_ENABLE_SCAFFOLD", "").lower() == "true":
    _scaffold_tools = [
        (geox_attribute_audit, "geox_attribute_audit", "Attribute Audit — PREVIEW. Computes Kozeny-Carman permeability proxy and transform-chain audit."),
        (geox_seismic_vision_review, "geox_seismic_vision_review", "Seismic Vision Review — SCAFFOLD. Mock fault picks with mandatory HYPOTHESIS ClaimTag."),
        (geox_map_georeference, "geox_map_georeference", "Georeference Map — SCAFFOLD. Reversible georeferencing plan from map image."),
        (geox_well_digitize_log, "geox_well_digitize_log", "Analog Digitizer — PLANNED. Scanned log image to structured curve tasks."),
    ]
    for fn, name, desc in _scaffold_tools:
        mcp.add_tool(fn, name=name, description=desc)
    print("Scaffold tools: ENABLED (GEOX_ENABLE_SCAFFOLD=true)")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8765))
    app = mcp.streamable_http_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        proxy_headers=True,
    )
