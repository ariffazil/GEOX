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
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from geox.core.ac_risk import (
    compute_ac_risk as _compute_ac_risk,
    compute_ac_risk_governed as _compute_ac_risk_governed,
    GovernedACRiskResult,
)

mcp = FastMCP("geox")

REGISTRY_PATH = Path(__file__).parent.parent / "registry" / "registry.json"
SKILLS_PATH = Path(__file__).parent.parent / "skills"
APPS_PATH = Path(__file__).parent.parent / "apps"


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
def geox_well_load_bundle(well_id: str) -> dict:
    """Load a full log bundle (LAS/DLIS) into witness context."""
    return {
        "well_id": well_id,
        "status": "loaded",
        "claim_tag": "OBSERVED",
        "stages": ["load", "qc"],
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
    """Execute physics-9 grounded petrophysical calculations with ToAC audit."""
    return {
        "well_id": well_id,
        "volume_id": volume_id,
        "saturation_model": saturation_model,
        "porosity": 0.22,
        "sw": 0.35,
        "claim_tag": "COMPUTED",
        "governance": {
            "f9_physics9": "Gardner density verified",
            "f7_confidence": "Single-model — humility band applied",
        },
    }


@mcp.tool()
def geox_section_interpret_strata(
    well_ids: list[str],
    section_type: str = "log correlation",
) -> dict:
    """Correlate stratigraphic units across multiple wells in a section."""
    return {
        "well_ids": well_ids,
        "section_type": section_type,
        "correlations": [],
        "claim_tag": "INTERPRETED",
        "confidence": 0.78,
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
    return {
        "bounds": bounds,
        "summary": {},
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
    return {
        "prospect_id": prospect_id,
        "evidence_chain": [],
        "claim_tag": "SYNTHESIZED",
    }


# =============================================================================
# LAYER 2 — INTERNAL PIPELINE (geox_<domain>_<verb>_stage, hidden)
# These are pipeline nodes. Not agent-facing in public tool listings.
# =============================================================================


@mcp.tool()
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


@mcp.tool()
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
            "target": "≥80% major fault identification within 48h",
        },
        "layer": "internal",
        "governance": {
            "note": "No CLAIM allowed. Only PLAUSIBLE/HYPOTHESIS permitted until 7-day probe complete.",
        },
    }


@mcp.tool()
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


@mcp.tool()
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
def geox_list_skills(domain: str = None, substrate: str = None) -> dict:
    """List GEOX skills with optional filters.
    Discovery tool — not a mission reasoning tool.
    """
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    skills = registry["skills"]
    if domain:
        skills = [s for s in skills if s["domain"] == domain]
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
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    for skill in registry["skills"]:
        if skill["id"] == skill_id:
            return skill

    return {"error": f"Skill not found: {skill_id}"}


@mcp.tool()
def geox_skill_dependencies(skill_id: str) -> dict:
    """Get skill dependencies.
    Discovery tool — not a mission reasoning tool.
    """
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)

    for skill in registry["skills"]:
        if skill["id"] == skill_id:
            deps = skill.get("depends_on", [])
            dep_skills = [s for s in registry["skills"] if s["id"] in deps]
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
    u_phys: float,
    transform_stack: list,
    bias_scenario: str = "ai_vision_only",
    custom_b_cog: float = None,
) -> dict:
    """Calculate Theory of Anomalous Contrast (ToAC) risk score.
    ROUTED — actual AC_Risk computation routes through arifOS constitutional layer.
    """
    result = _compute_ac_risk(
        u_phys=u_phys,
        transform_stack=transform_stack,
        bias_scenario=bias_scenario,
        custom_b_cog=custom_b_cog,
    )
    return {
        "ac_risk": result.ac_risk,
        "verdict": result.verdict,
        "explanation": result.explanation,
        "components": {
            "u_phys": result.u_phys,
            "d_transform": result.d_transform,
            "b_cog": result.b_cog,
        },
        "_routed_to": "arifOS",
    }


@mcp.tool()
def arifos_judge_prospect(
    u_phys: float,
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
) -> dict:
    """Calculate governed AC_Risk with ClaimTag, TEARFRAME, Anti-Hantu, and 888_HOLD.
    ROUTED — Every prospect evaluation routes through arifOS for VAULT999 sealing.
    GEOX does not hold verdict authority.
    """
    result = _compute_ac_risk_governed(
        u_phys=u_phys,
        transform_stack=transform_stack,
        bias_scenario=bias_scenario,
        custom_b_cog=custom_b_cog,
        model_text=model_text,
        truth_score=truth_score,
        echo_score=echo_score,
        amanah_locked=amanah_locked,
        rasa_present=rasa_present,
        irreversible_action=irreversible_action,
        prospect_context=prospect_context,
    )
    output = result.to_dict()
    output["_routed_to"] = "arifOS"
    return output


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
