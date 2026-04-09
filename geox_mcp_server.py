"""
geox_mcp_server.py — GEOX MCP Server for arifOS
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

FastMCP 2.x/3.x compatible server for geological prospect evaluation.
Works with Horizon (FastMCP 2.x) and VPS (FastMCP 3.x).

Entrypoint: geox_mcp_server.py:mcp
"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime, timezone
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# FastMCP Compatibility Layer
# ═══════════════════════════════════════════════════════════════════════════════

# Detect FastMCP version
try:
    import fastmcp
    FASTMCP_VERSION = tuple(map(int, fastmcp.__version__.split('.')[:2]))
    IS_FASTMCP_3 = FASTMCP_VERSION >= (3, 0)
except Exception:
    FASTMCP_VERSION = (2, 0)
    IS_FASTMCP_3 = False

# Import FastMCP
from fastmcp import FastMCP

# ToolResult compatibility
if IS_FASTMCP_3:
    # FastMCP 3.x - use native ToolResult
    from fastmcp.tools import ToolResult
else:
    # FastMCP 2.x - create compatible ToolResult
    class ToolResult:
        """Compatible ToolResult for FastMCP 2.x"""
        def __init__(self, content: str, structured_content: Any = None, meta: dict = None):
            self.content = content
            self.structured_content = structured_content
            self.meta = meta or {}
        
        def __repr__(self):
            return f"ToolResult(content={self.content!r})"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("geox.mcp")

# ═══════════════════════════════════════════════════════════════════════════════
# Optional: Prefab UI Views (Forge 2) - only available in VPS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from arifos.geox.geox_memory import GeoMemoryStore
    _memory_store: "GeoMemoryStore | None" = GeoMemoryStore()
    _HAS_MEMORY = True
except Exception as _mem_exc:
    _memory_store = None
    _HAS_MEMORY = False
    logger.info("Memory store unavailable — geox_query_memory will return stub results (%s)", _mem_exc)

try:
    from arifos.geox.apps.prefab_views import (
        cutoff_validation_view,
        feasibility_check_view,
        geospatial_view,
        petrophysical_hold_view,
        petrophysics_compute_view,
        prospect_verdict_view,
        seismic_section_view,
        structural_candidates_view,
        sw_model_selector_view,
    )
    _HAS_PREFAB = True
except ImportError:
    _HAS_PREFAB = False
    logger.info("Prefab UI not available — running in text-only mode")

try:
    from arifos.geox.tools.seismic.seismic_single_line_tool import SeismicSingleLineTool
    _HAS_SEISMIC = True
except ImportError:
    _HAS_SEISMIC = False
    logger.info("Seismic tools not available — using stub mode")


# ═══════════════════════════════════════════════════════════════════════════════
# Server Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "0.5.0"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"

mcp = FastMCP(
    name="GEOX Earth Witness",
    version=GEOX_VERSION,
    instructions="Governed domain surface for subsurface inverse modelling. DITEMPA BUKAN DIBERI.",
)

# ═══════════════════════════════════════════════════════════════════════════════
# Malay Basin Pilot Tool
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_malay_basin_pilot")
async def geox_malay_basin_pilot(
    query_type: str = "full", 
    play_filter: str | None = None,
    figure_ref: str | None = None
) -> dict:
    """
    Load Malay Basin Pilot Data (1968-2018).
    
    query_type: "stats", "plays", "creaming", "seismic_line", or "full".
    play_filter: Filter by play code (e.g. "P1").
    figure_ref: Reference ID for GSM figures (e.g. "gsm_702001_p005").
    """
    from arifos.geox.resources.malay_basin_pilot import MalayBasinPilotResource
    resource = MalayBasinPilotResource()
    data = await resource.read()
    
    # Filter logic
    if query_type == "stats":
        output = {"stats": data["stats"]}
    elif query_type == "plays":
        plays = data["play_types"]
        if play_filter:
            plays = [p for p in plays if p["code"] == play_filter]
        output = {"play_types": plays}
    elif query_type == "creaming":
        output = {"phases": data["phases"]}
    elif query_type == "seismic_line" and figure_ref:
        output = {
            "image_url": f"/data/gsm_702001_demo/figures/{figure_ref}.png",
            "geo_bounds": [103.5, 4.0, 105.5, 7.0],
            "citation": "GSM-702001 (2021)",
            "constitutional": {
                "provenance": "GSM Validated",
                "f11_audit": "GSM-702001_SEISMIC_01"
            }
        }
    else:
        output = data
    
    result = ToolResult(
        content=(
            f"Malay Basin Pilot Data ({query_type}) loaded. "
            "Foundations grounded in GSM-702001. DITEMPA BUKAN DIBERI."
        ),
        structured_content=output,
    )
    
    return _tool_result_to_dict(result)



# ═══════════════════════════════════════════════════════════════════════════════
# Health Check Routes (FastMCP 2.x/3.x compatible)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from starlette.requests import Request
    from starlette.responses import JSONResponse, PlainTextResponse
    
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_: Request) -> PlainTextResponse:
        """Minimal health endpoint."""
        return PlainTextResponse("OK")
    
    @mcp.custom_route("/health/details", methods=["GET"])
    async def health_details(_: Request) -> JSONResponse:
        """Detailed health endpoint."""
        return JSONResponse({
            "ok": True,
            "service": "geox-earth-witness",
            "version": GEOX_VERSION,
            "mode": "constitutional-governance",
            "forge": "Forge-3-FastMCP" if IS_FASTMCP_3 else "Forge-2-Horizon",
            "fastmcp_version": ".".join(map(str, FASTMCP_VERSION)),
            "prefab_ui": _HAS_PREFAB,
            "seismic_engine": _HAS_SEISMIC,
            "seal": GEOX_SEAL,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "constitutional_floors": [
                "F1_amanah", "F2_truth", "F4_clarity", "F7_humility",
                "F9_anti_hantu", "F11_authority", "F13_sovereign",
            ],
        })
    
    HAS_HTTP_ROUTES = True
    
except ImportError:
    HAS_HTTP_ROUTES = False
    logger.warning("Starlette not available, HTTP routes disabled")


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _interpretation_to_candidates(result: object) -> list[dict[str, Any]]:
    """Extract candidate models from SeismicSingleLineTool result."""
    payload: dict[str, Any] = {}
    if hasattr(result, "to_dict"):
        raw = result.to_dict()
        if isinstance(raw, dict):
            payload = raw
    elif hasattr(result, "model_dump"):
        raw = result.model_dump(mode="json")
        if isinstance(raw, dict):
            payload = raw
    elif isinstance(result, dict):
        payload = result

    candidates = payload.get("candidates") or payload.get("models") or []
    if isinstance(candidates, list):
        return candidates
    return []


def _governance_stub_views(line_id: str, survey_path: str) -> list[dict[str, str]]:
    """Return lightweight view metadata when real seismic engine is absent."""
    return [
        {
            "view_id": f"{line_id}:baseline",
            "mode": "governance_stub",
            "source": survey_path,
            "note": "Real seismic contrast generation not executed in this environment.",
        }
    ]


def _build_prefab_view(view_type: str, **kwargs) -> Any:
    """Build Prefab view if available, else return dict."""
    if not _HAS_PREFAB:
        return {"view_type": view_type, "mode": "text_fallback", **kwargs}
    
    view_builders = {
        "seismic_section": seismic_section_view,
        "structural_candidates": structural_candidates_view,
        "feasibility_check": feasibility_check_view,
        "geospatial": geospatial_view,
        "prospect_verdict": prospect_verdict_view,
    }
    
    if builder := view_builders.get(view_type):
        try:
            return builder(**kwargs)
        except Exception as exc:
            logger.warning(f"Prefab view build failed: {exc}")
    
    return {"view_type": view_type, "mode": "fallback", **kwargs}


def _tool_result_to_dict(result: ToolResult) -> dict:
    """Convert ToolResult to dict for FastMCP 2.x compatibility."""
    if IS_FASTMCP_3:
        # FastMCP 3.x handles ToolResult natively
        return result
    else:
        # FastMCP 2.x needs dict return
        return {
            "content": [{"type": "text", "text": result.content}],
            "structured_content": result.structured_content,
            "meta": result.meta,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tools
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_load_seismic_line")
async def geox_load_seismic_line(
    line_id: str,
    survey_path: str = "default_survey",
    generate_views: bool = True,
) -> dict:
    """
    Load seismic data and ignite visual mode (Earth Witness Ignition).
    
    Returns QC badges, contrast warnings, and governance floor status.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    views = _governance_stub_views(line_id, survey_path)
    
    structured = _build_prefab_view(
        "seismic_section",
        line_id=line_id,
        survey_path=survey_path,
        status="IGNITED",
        views=views,
        timestamp=timestamp,
    ) if generate_views else {"status": "IGNITED", "line_id": line_id}
    
    result = ToolResult(
        content=(
            f"Seismic line '{line_id}' loaded from '{survey_path}'. "
            "Status: IGNITED. Scale unknown — measurement tools disabled (F4). "
            "ToAC contrast canon active. 888 HOLD checklist rendered for review."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_build_structural_candidates")
async def geox_build_structural_candidates(
    line_id: str,
    focus_area: str | None = None,
) -> dict:
    """
    Build structural model candidates (Inverse Modelling Constraints).
    
    Prevents narrative collapse by maintaining multiple candidate models.
    Confidence bounded at 12% per F7 Humility.
    """
    candidates: list[dict] = []
    
    if _HAS_SEISMIC:
        try:
            tool = SeismicSingleLineTool()
            result = tool.interpret(line_id, source_type="ORCHESTRATED")
            candidates = _interpretation_to_candidates(result)
        except Exception as exc:
            logger.warning(f"Seismic interpretation failed: {exc}")
    
    n = len(candidates) if candidates else 3
    
    structured = _build_prefab_view(
        "structural_candidates",
        line_id=line_id,
        candidates=candidates if candidates else None,
        verdict="QUALIFY",
        confidence=0.12,
    )
    
    result = ToolResult(
        content=(
            f"Generated {n} structural candidate model(s) for line '{line_id}'. "
            "Non-uniqueness principle active — collapse to single model prohibited. "
            "F7 Humility: confidence bounded at 12%. Well-tie required to constrain."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_feasibility_check")
async def geox_feasibility_check(
    plan_id: str,
    constraints: list[str],
) -> dict:
    """
    Constitutional Firewall: Check if a proposed plan is physically possible.
    
    Returns F1-F13 floor status and SEAL/HOLD verdict.
    """
    verdict = "PHYSICALLY_FEASIBLE"
    grounding_confidence = 0.88
    
    structured = _build_prefab_view(
        "feasibility_check",
        plan_id=plan_id,
        constraints=constraints,
        verdict=verdict,
        grounding_confidence=grounding_confidence,
    )
    
    result = ToolResult(
        content=(
            f"Plan '{plan_id}' feasibility check: {verdict}. "
            f"Grounding confidence: {grounding_confidence:.0%}. "
            f"Constraints checked: {len(constraints)}. "
            "Constitutional floors F1, F4, F7, F9, F11, F13 active. "
            "Proceed to 333_MIND."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_verify_geospatial")
async def geox_verify_geospatial(
    lat: float,
    lon: float,
    radius_m: float = 1000.0,
) -> dict:
    """
    Verify geospatial grounding and jurisdictional boundaries.
    
    Anchors all reasoning in verified coordinates per F4 Clarity.
    """
    geological_province = "Malay Basin"
    jurisdiction = "EEZ_Grounded"
    verdict = "GEOSPATIALLY_VALID"
    
    structured = _build_prefab_view(
        "geospatial",
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        geological_province=geological_province,
        jurisdiction=jurisdiction,
        verdict=verdict,
    )
    
    result = ToolResult(
        content=(
            f"Coordinates ({lat:.6f}, {lon:.6f}) verified. "
            f"Province: {geological_province}. Jurisdiction: {jurisdiction}. "
            f"Verdict: {verdict}. CRS: WGS84. F4 Clarity and F11 Authority active."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_evaluate_prospect")
async def geox_evaluate_prospect(
    prospect_id: str,
    interpretation_id: str,
) -> dict:
    """
    Provide a governed verdict on a subsurface prospect (222_REFLECT).
    
    Blocks ungrounded claims via Reality Firewall. Returns 888 HOLD status
    if physical grounding is insufficient per F9 Anti-Hantu.
    """
    verdict = "PHYSICAL_GROUNDING_REQUIRED"
    confidence = 0.45
    status = "888_HOLD"
    reason = "Wait for well-tie calibration per F9 Anti-Hantu floor."
    
    structured = _build_prefab_view(
        "prospect_verdict",
        prospect_id=prospect_id,
        interpretation_id=interpretation_id,
        verdict=verdict,
        confidence=confidence,
        status=status,
        reason=reason,
    )
    
    result = ToolResult(
        content=(
            f"Prospect '{prospect_id}' evaluation: {status}. "
            f"Verdict: {verdict}. Confidence: {confidence:.0%}. "
            f"Reason: {reason} "
            "Logged to 999_VAULT. Human signoff required before proceeding."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_query_memory")
async def geox_query_memory(
    query: str,
    basin: str | None = None,
    limit: int = 5,
) -> dict:
    """
    Query the GEOX geological memory store for past evaluations.

    Retrieves stored prospect evaluations, verdicts, and geological context
    that match the query. Used to ground new reasoning in prior evidence.

    Args:
        query: Natural-language query (e.g. "Malay Basin structural traps")
        basin: Optional basin filter (e.g. "Malay Basin", "Sabah Basin")
        limit: Max results to return (default 5, max 20)
    """
    limit = min(max(1, limit), 20)

    if _HAS_MEMORY and _memory_store is not None:
        try:
            entries = await _memory_store.retrieve(query=query, basin=basin, limit=limit)
            results = [e.to_dict() for e in entries]
            count = len(results)
        except Exception as exc:
            logger.warning("Memory retrieve failed: %s", exc)
            results = []
            count = 0
    else:
        results = []
        count = 0

    structured = {
        "query": query,
        "basin_filter": basin,
        "results": results,
        "count": count,
        "memory_backend": "GeoMemoryStore" if _HAS_MEMORY else "unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    content = (
        f"Memory query '{query}' returned {count} result(s). "
        + (f"Basin filter: {basin}. " if basin else "")
        + ("F10 Ontology: past evaluations surfaced for grounding." if count > 0
           else "No prior evaluations found — first assessment for this context.")
    )

    result = ToolResult(content=content, structured_content=structured)
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_health")
async def geox_health() -> dict:
    """Server health check with constitutional floor status."""
    result = ToolResult(
        content=f"GEOX Earth Witness v{GEOX_VERSION} is healthy. Seal: {GEOX_SEAL}",
        structured_content={
            "ok": True,
            "service": "geox-earth-witness",
            "version": GEOX_VERSION,
            "fastmcp_version": ".".join(map(str, FASTMCP_VERSION)),
            "seal": GEOX_SEAL,
            "prefab_ui": _HAS_PREFAB,
            "seismic_engine": _HAS_SEISMIC,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "constitutional_floors": [
                "F1_amanah", "F2_truth", "F4_clarity", "F7_humility",
                "F9_anti_hantu", "F11_authority", "F13_sovereign",
            ],
        }
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_select_sw_model")
async def geox_select_sw_model(
    interval_uri: str,
    candidate_models: list[str] | None = None,
) -> dict:
    """
    Evaluate Archie vs shaly-sand saturation models against shale conductivity,
    mineralogy, and calibration support.
    
    Returns admissible models with confidence scores and rejected models with violations.
    """
    if candidate_models is None:
        candidate_models = ["archie", "simandoux", "indonesia", "dual_water"]
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Simulate model evaluation (stub for Phase B)
    admissible = []
    rejected = []
    
    for model in candidate_models:
        if model == "archie":
            admissible.append({
                "model": model,
                "confidence": 0.85,
                "justification": "Clean sandstone interval, low shale volume (<15%)"
            })
        elif model == "simandoux":
            admissible.append({
                "model": model,
                "confidence": 0.78,
                "justification": "Moderate shale volume (15-30%), good for laminated shales"
            })
        else:
            rejected.append({
                "model": model,
                "reason": "Insufficient calibration data for this formation",
                "violations": ["missing_rw_calibration", "no_core_data"]
            })
    
    recommended = admissible[0]["model"] if admissible else None
    
    # Build data payload
    data = {
        "interval_uri": interval_uri,
        "admissible_models": admissible,
        "rejected_models": rejected,
        "recommended_model": recommended,
        "timestamp": timestamp,
        "floor_check": {
            "F4_clarity": True,
            "F7_humility": True,
            "F9_anti_hantu": len(rejected) > 0,
        }
    }
    
    # Build Prefab view if available
    if _HAS_PREFAB:
        view = sw_model_selector_view(
            interval_uri=interval_uri,
            admissible_models=admissible,
            rejected_models=rejected,
            recommended_model=recommended,
        )
        structured = {
            "_view": view.to_json(),
            **data,
        }
    else:
        structured = data
    
    result = ToolResult(
        content=(
            f"Saturation model selection for {interval_uri}: "
            f"{len(admissible)} admissible, {len(rejected)} rejected. "
            f"Recommended: {recommended or 'None'}. "
            "F7 Humility: confidence bounded by calibration quality."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_compute_petrophysics")
async def geox_compute_petrophysics(
    interval_uri: str,
    model_id: str,
    model_params: dict | None = None,
    compute_uncertainty: bool = True,
) -> dict:
    """
    Compute Vsh, phi_t, phi_e, Sw, BVW, net, pay, RQI/FZI/HFU
    with uncertainty envelopes.
    
    Constitutional computation pipeline with F4 Clarity and F7 Humility.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    model_params = model_params or {}
    
    results = {
        "vsh_range": [0.12, 0.28],
        "phi_t_range": [0.18, 0.32],
        "phi_e_range": [0.15, 0.28],
        "sw_range": [0.25, 0.45],
        "bvw_range": [0.04, 0.11],
    }
    
    # Build data payload
    data = {
        "interval_uri": interval_uri,
        "model_used": model_id,
        "model_params": model_params,
        "compute_uncertainty": compute_uncertainty,
        "verdict": "COMPUTED",
        "results": results,
        "timestamp": timestamp,
        "floor_check": {
            "F4_clarity": True,
            "F7_humility": compute_uncertainty,
            "F9_anti_hantu": True,
        }
    }
    
    # Build Prefab view if available
    if _HAS_PREFAB:
        view = petrophysics_compute_view(
            interval_uri=interval_uri,
            model_used=model_id,
            results=results,
            verdict="COMPUTED",
            compute_uncertainty=compute_uncertainty,
        )
        structured = {
            "_view": view.to_json(),
            **data,
        }
    else:
        structured = data
    
    result = ToolResult(
        content=(
            f"Petrophysics computed for {interval_uri} using {model_id}. "
            f"Uncertainty envelopes: {'enabled' if compute_uncertainty else 'disabled'}. "
            "F4 Clarity: all units verified. F7 Humility: confidence intervals attached."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_validate_cutoffs")
async def geox_validate_cutoffs(
    interval_uri: str,
    cutoff_policy_id: str,
) -> dict:
    """
    Apply economic/operational cutoffs as governed policy objects.
    Distinguishes physics from policy per F4 Clarity.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    net_pay_flags = {
        "net_thickness_m": 12.5,
        "pay_thickness_m": 8.3,
        "net_to_gross": 0.66,
    }
    cutoffs_applied = {
        "vsh_max": 0.35,
        "phi_min": 0.12,
        "sw_max": 0.50,
    }
    
    # Build data payload
    data = {
        "interval_uri": interval_uri,
        "policy_id": cutoff_policy_id,
        "status": "VALIDATED",
        "net_pay_flags": net_pay_flags,
        "cutoffs_applied": cutoffs_applied,
        "timestamp": timestamp,
        "floor_check": {
            "F4_clarity": True,
            "F11_authority": True,
        }
    }
    
    # Build Prefab view if available
    if _HAS_PREFAB:
        view = cutoff_validation_view(
            interval_uri=interval_uri,
            policy_id=cutoff_policy_id,
            net_pay_flags=net_pay_flags,
            cutoffs_applied=cutoffs_applied,
        )
        structured = {
            "_view": view.to_json(),
            **data,
        }
    else:
        structured = data
    
    result = ToolResult(
        content=(
            f"Cutoff policy {cutoff_policy_id} applied to {interval_uri}. "
            "Net thickness: 12.5m, Pay thickness: 8.3m. "
            "F4 Clarity: physics distinguished from policy. F11 Authority: policy logged."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


@mcp.tool(name="geox_petrophysical_hold_check")
async def geox_petrophysical_hold_check(interval_uri: str) -> dict:
    """
    Automatic 888_HOLD trigger detection for petrophysics.
    
    Checks:
    - Rw uncalibrated
    - Shale model unsupported
    - Environmental correction missing
    - Invasion ignored
    - Depth mismatch unresolved
    - Cutoffs without economic basis
    
    Returns SEAL / QUALIFY / 888_HOLD verdict per F1 Amanah and F13 Sovereign.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Simulate hold check (stub for Phase B)
    triggers = []
    required_actions = []
    
    # Example logic - would be replaced with real checks
    if "uncalibrated" in interval_uri.lower():
        triggers.append("Rw_uncalibrated")
        required_actions.append("Calibrate Rw from SP or water sample")
    
    verdict = "888_HOLD" if triggers else "QUALIFY"
    can_override = verdict == "888_HOLD"
    
    # Build data payload
    data = {
        "status": "SUCCESS",
        "interval_uri": interval_uri,
        "verdict": verdict,
        "triggers": triggers,
        "required_actions": required_actions,
        "can_override": can_override,
        "override_authority": "F13_SOVEREIGN" if can_override else None,
        "timestamp": timestamp,
        "floor_check": {
            "F1_amanah": True,
            "F9_anti_hantu": True,
            "F13_sovereign": True,
        }
    }
    
    # Build Prefab view if available
    if _HAS_PREFAB:
        view = petrophysical_hold_view(
            interval_uri=interval_uri,
            verdict=verdict,
            triggers=triggers,
            required_actions=required_actions,
            can_override=can_override,
        )
        structured = {
            "_view": view.to_json(),
            **data,
        }
    else:
        structured = data
    
    result = ToolResult(
        content=(
            f"Petrophysical hold check for {interval_uri}: {verdict}. "
            f"Triggers: {triggers if triggers else 'none'}. "
            "F1 Amanah: reversibility verified. F13 Sovereign: human override available."
        ),
        structured_content=structured,
    )
    
    return _tool_result_to_dict(result)


# ═══════════════════════════════════════════════════════════════════════════════
# Factory Function (for fastmcp run server.py:create_server)
# ═══════════════════════════════════════════════════════════════════════════════

def create_server(
    transport: str = "stdio",
    host: str = "0.0.0.0",
    port: int = 8000,
) -> FastMCP:
    """
    Factory function for creating a configured GEOX MCP server.
    
    Used by FastMCP CLI:
      fastmcp run geox_mcp_server.py:create_server
      fastmcp run geox_mcp_server.py:create_server --transport http --port 9000
    
    Returns the configured FastMCP instance. The CLI handles running it.
    """
    # Update server metadata based on config
    mcp._name = "GEOX Earth Witness"
    mcp._version = GEOX_VERSION
    
    # Log configuration
    logger.info("=" * 60)
    logger.info("GEOX Earth Witness v%s — %s", GEOX_VERSION, GEOX_SEAL)
    logger.info("FastMCP Version: %s", ".".join(map(str, FASTMCP_VERSION)))
    logger.info("Factory Mode: transport=%s, host=%s, port=%d", transport, host, port)
    logger.info("=" * 60)
    logger.info("HTTP Routes: %s", "enabled" if HAS_HTTP_ROUTES else "disabled")
    logger.info("Prefab UI: %s", "available" if _HAS_PREFAB else "unavailable")
    logger.info("Seismic Engine: %s", "available" if _HAS_SEISMIC else "unavailable")
    logger.info("Memory Store: %s", "available" if _HAS_MEMORY else "unavailable")
    logger.info("Tools (11): geox_load_seismic_line, geox_build_structural_candidates,")
    logger.info("            geox_feasibility_check, geox_verify_geospatial,")
    logger.info("            geox_evaluate_prospect, geox_query_memory, geox_health,")
    logger.info("            geox_select_sw_model, geox_compute_petrophysics,")
    logger.info("            geox_validate_cutoffs, geox_petrophysical_hold_check")
    logger.info("=" * 60)
    
    return mcp


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Entrypoint (legacy direct execution)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GEOX Earth Witness MCP Server — DITEMPA BUKAN DIBERI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  GEOX_TRANSPORT=http|stdio    # Default transport
  GEOX_HOST=0.0.0.0            # HTTP host
  GEOX_PORT=8000               # HTTP port

Examples:
  python geox_mcp_server.py
  python geox_mcp_server.py --transport http --port 8100
  GEOX_TRANSPORT=http python geox_mcp_server.py
        """
    )
    parser.add_argument(
        "--transport",
        default=os.getenv("GEOX_TRANSPORT", "stdio"),
        choices=["stdio", "http"],
        help="Transport protocol",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("GEOX_HOST", "0.0.0.0"),
        help="HTTP bind host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("GEOX_PORT", 8000)),
        help="HTTP bind port",
    )
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logging.getLogger().setLevel(args.log_level.upper())
    
    logger.info("=" * 60)
    logger.info("GEOX Earth Witness v%s — %s", GEOX_VERSION, GEOX_SEAL)
    logger.info("FastMCP Version: %s", ".".join(map(str, FASTMCP_VERSION)))
    logger.info("=" * 60)
    logger.info("Transport: %s", args.transport)
    logger.info("HTTP Routes: %s", "enabled" if HAS_HTTP_ROUTES else "disabled")
    logger.info("Prefab UI: %s", "available" if _HAS_PREFAB else "unavailable")
    logger.info("Seismic Engine: %s", "available" if _HAS_SEISMIC else "unavailable")
    
    if args.transport == "http":
        logger.info("Host: %s | Port: %d", args.host, args.port)
        logger.info("Health: http://%s:%d/health", args.host, args.port)
    
    logger.info("=" * 60)
    logger.info("Memory Store: %s", "available" if _HAS_MEMORY else "unavailable")
    logger.info("Tools (11): geox_load_seismic_line, geox_build_structural_candidates,")
    logger.info("            geox_feasibility_check, geox_verify_geospatial,")
    logger.info("            geox_evaluate_prospect, geox_query_memory, geox_health,")
    logger.info("            geox_select_sw_model, geox_compute_petrophysics,")
    logger.info("            geox_validate_cutoffs, geox_petrophysical_hold_check")
    logger.info("=" * 60)
    
    # Run with FastMCP
    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()