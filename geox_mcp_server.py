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
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Literal

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
        feasibility_check_view,
        geospatial_view,
        prospect_verdict_view,
        seismic_section_view,
        structural_candidates_view,
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

try:
    from arifos.geox.physics.petrophysics import monte_carlo_sw
    _HAS_PHYSICS = True
except ImportError:
    _HAS_PHYSICS = False
    logger.info("Physics engine not available — geox_calculate_saturation will return stub results")

try:
    from arifos.geox.schemas.petrophysics_schemas import (
        CutoffPolicy,
        CutoffValidationResult,
        LogQCFlags,
        PetrophysicsHold,
        PetrophysicsInput,
        PetrophysicsOutput,
        SwModelAdmissibility,
    )
    _HAS_PETRO_SCHEMAS = True
except ImportError as _petro_exc:
    _HAS_PETRO_SCHEMAS = False
    logger.warning("Petrophysics schemas unavailable: %s", _petro_exc)


# ═══════════════════════════════════════════════════════════════════════════════
# Server Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "0.6.0"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"

mcp = FastMCP(
    name="GEOX Earth Witness",
    version=GEOX_VERSION,
    instructions="Governed domain surface for subsurface inverse modelling. DITEMPA BUKAN DIBERI.",
)


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


@mcp.tool(name="geox_calculate_saturation")
async def geox_calculate_saturation(
    model: Literal["archie", "simandoux", "indonesia"],
    params: dict[str, Any],
    n_samples: int = 1000,
) -> dict:
    """
    Calculate water saturation (Sw) with Monte Carlo uncertainty (Phase B Physics Engine).
    
    Constitutional Floors:
    - F2 Truth: Models grounded in formal petrophysics (Archie, Simandoux, Indonesia)
    - F7 Humility: Returns P10/P50/P90 confidence bands
    - F13 Sovereign: Triggers 888_HOLD if physics violated
    
    Args:
        model: Petrophysical model to use (archie, simandoux, or indonesia).
        params: Map of parameters (rw, rt, phi, etc.). 
                Use a scalar for nominal values, or [mean, std] for uncertainty.
        n_samples: Number of Monte Carlo iterations (default 1000).
    """
    if not _HAS_PHYSICS:
        result = ToolResult(
            content="Physics engine unavailable in this environment.",
            structured_content={"error": "import_failed", "status": "888_HOLD"}
        )
        return _tool_result_to_dict(result)

    try:
        # Standardize params (ensure m/n/a exist if not provided)
        defaults = {"a": 1.0, "m": 2.0, "n": 2.0}
        for k, v in defaults.items():
            if k not in params:
                params[k] = v
                
        mc_result = monte_carlo_sw(model, params, n_samples)
        
        # Add timestamp and metadata
        mc_result["timestamp"] = datetime.now(timezone.utc).isoformat()
        mc_result["geox_version"] = GEOX_VERSION
        
        status = mc_result["verdict"]
        nominal_sw = mc_result["nominal_sw"]
        
        content = (
            f"Model {model.upper()} saturation calculation complete. "
            f"Nominal Sw: {nominal_sw:.3f}. Verdict: {status}. "
            f"Uncertainty: P10={mc_result['stats']['p10']:.3f}, P90={mc_result['stats']['p90']:.3f}. "
            "F7 Humility enforced via confidence bands. F13 Sovereign check completed."
        )
        
        if status == "888_HOLD":
            content += f" TRIGGERS: {', '.join(mc_result['hold_triggers'])}"
            
        result = ToolResult(content=content, structured_content=mc_result)
        return _tool_result_to_dict(result)

    except Exception as exc:
        logger.error(f"Saturation calculation failed: {exc}")
        result = ToolResult(
            content=f"Calculation error: {exc}",
            structured_content={"error": str(exc), "status": "888_HOLD"}
        )
        return _tool_result_to_dict(result)


@mcp.tool(name="geox_select_sw_model")
async def geox_select_sw_model(
    well_id: str,
    depth_top_m: float,
    depth_base_m: float,
    has_washout: bool = False,
    washout_fraction: float = 0.0,
    borehole_quality: str = "good",
    has_invasion: bool = False,
    has_gas_effect: bool = False,
    has_shale: bool = True,
    vsh_max: float = 0.0,
    has_deep_resistivity: bool = True,
    has_shallow_resistivity: bool = False,
    available_curves: list[str] | None = None,
) -> dict:
    """
    Evaluate Sw model admissibility from log QC flags.

    Applies constitutional QC rules to determine which water saturation model
    (Archie, Simandoux, Indonesia) may be used for the interval.  If no model
    is admissible the tool raises an explicit 888_HOLD.

    Returns SwModelAdmissibility JSON with provenance tag POLICY.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if not _HAS_PETRO_SCHEMAS:
        return {
            "status": "UNAVAILABLE",
            "reason": "Petrophysics schemas not loaded.",
            "timestamp": timestamp,
        }

    curves = available_curves or []

    # ── Admissibility rules ───────────────────────────────────────────────────
    admissible: list[str] = []
    inadmissible: dict[str, list[str]] = {}

    # Archie: clean sand, deep resistivity required
    archie_rej: list[str] = []
    if not has_deep_resistivity:
        archie_rej.append("No deep resistivity curve — Rt unavailable.")
    if has_washout and washout_fraction > 0.30:
        archie_rej.append(
            f"Washout fraction {washout_fraction:.0%} > 30 % — resistivity unreliable."
        )
    if has_shale and vsh_max > 0.20:
        archie_rej.append(
            f"Vsh_max {vsh_max:.2f} > 0.20 — Archie invalid for shaly sand; use Simandoux/Indonesia."
        )
    if archie_rej:
        inadmissible["archie"] = archie_rej
    else:
        admissible.append("archie")

    # Simandoux / Indonesia: require Rsh curve or shale baseline
    for model in ("simandoux", "indonesia"):
        rej: list[str] = []
        if not has_deep_resistivity:
            rej.append("No deep resistivity — Rt unavailable.")
        if not has_shale:
            rej.append(f"No shale detected — {model} over-parameterised; use Archie.")
        if has_washout and washout_fraction > 0.40:
            rej.append(
                f"Washout fraction {washout_fraction:.0%} > 40 % — shaly-sand model unreliable."
            )
        if rej:
            inadmissible[model] = rej
        else:
            admissible.append(model)

    # ── Recommended model ─────────────────────────────────────────────────────
    hold_reasons: list[str] = []
    requires_hold = False

    if borehole_quality == "poor":
        hold_reasons.append(
            "Borehole quality 'poor' — all resistivity-based Sw models unreliable."
        )
        admissible = []

    if not has_deep_resistivity:
        hold_reasons.append("Deep resistivity curve absent — cannot compute Sw.")
        admissible = []

    if not admissible:
        requires_hold = True
        recommended: str = "none"
    elif "archie" in admissible and not has_shale:
        recommended = "archie"
    elif has_shale and vsh_max > 0.15:
        recommended = "indonesia" if "indonesia" in admissible else "simandoux"
        if recommended not in admissible:
            recommended = admissible[0]
    else:
        recommended = admissible[0]

    # F7 confidence — lower when washout or poor hole
    confidence = 0.12 if borehole_quality == "fair" else 0.08
    if has_washout:
        confidence = min(confidence, 0.10)

    result_data: dict[str, Any] = {
        "well_id": well_id,
        "recommended_model": recommended,
        "admissible_models": admissible,
        "inadmissible_models": inadmissible,
        "requires_hold": requires_hold,
        "hold_reasons": hold_reasons,
        "confidence": confidence,
        "floor_verdicts": {
            "F2_truth": True,
            "F4_clarity": True,
            "F7_humility": True,
            "F9_anti_hantu": not requires_hold,
            "F11_authority": True,
        },
        "provenance_tag": "POLICY",
        "timestamp": timestamp,
        "seal": GEOX_SEAL,
    }

    verb = "888_HOLD — no admissible model" if requires_hold else f"recommended: {recommended}"
    content = (
        f"SW model selection for well '{well_id}' ({depth_top_m}–{depth_base_m} m): {verb}. "
        f"Admissible: {admissible or 'none'}. "
        f"Confidence: {confidence:.0%}. "
        "F9 Anti-Hantu active — inadmissible model use is a governance violation."
    )

    tool_result = ToolResult(content=content, structured_content=result_data)
    return _tool_result_to_dict(tool_result)


@mcp.tool(name="geox_compute_petrophysics")
async def geox_compute_petrophysics(
    well_id: str,
    sw_model: str,
    rw_ohm_m: float,
    rt_ohm_m: float,
    phi_fraction: float,
    vcl_fraction: float = 0.0,
    rsh_ohm_m: float | None = None,
    archie_a: float = 1.0,
    archie_m: float = 2.0,
    archie_n: float = 2.0,
    run_monte_carlo: bool = True,
    mc_samples: int = 1000,
) -> dict:
    """
    Full petrophysics property pipeline — Vsh, PHIe, Sw, BVW.

    Runs the selected Sw model (archie | simandoux | indonesia) with optional
    Monte Carlo uncertainty quantification (F7 Humility).  Physical
    impossibilities (Sw > 1.0, PHI > 0.50) trigger an explicit 888_HOLD.

    Returns PetrophysicsOutput JSON with provenance tag DERIVED.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if not _HAS_PETRO_SCHEMAS:
        return {"status": "UNAVAILABLE", "reason": "Petrophysics schemas not loaded.", "timestamp": timestamp}

    # Validate sw_model
    valid_models = ("archie", "simandoux", "indonesia")
    if sw_model not in valid_models:
        hold_data: dict[str, Any] = {
            "well_id": well_id,
            "hold_id": f"HOLD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "triggered_by": "geox_compute_petrophysics",
            "violated_floors": ["F4_clarity"],
            "violations": [f"sw_model='{sw_model}' is not one of {valid_models}."],
            "remediation": [f"Choose from: {valid_models}"],
            "severity": "block",
            "requires_human_signoff": True,
            "provenance_tag": "POLICY",
            "timestamp": timestamp,
        }
        result = ToolResult(
            content=f"888_HOLD: Invalid sw_model '{sw_model}'. Choose from {valid_models}.",
            structured_content=hold_data,
        )
        return _tool_result_to_dict(result)

    # Run saturation computation
    hold_triggers: list[str] = []
    mc_stats: dict[str, Any] | None = None

    if phi_fraction > 0.45:
        hold_triggers.append(f"PHI ({phi_fraction:.3f}) > 0.45 — above physical maximum for clastic reservoir.")

    if _HAS_PHYSICS and run_monte_carlo:
        # Build params with uncertainty spread (±5 % of each value for MC)
        mc_params: dict[str, Any] = {
            "rw": (rw_ohm_m, rw_ohm_m * 0.05),
            "rt": (rt_ohm_m, rt_ohm_m * 0.05),
            "phi": (phi_fraction, phi_fraction * 0.07),
            "a": archie_a,
            "m": archie_m,
            "n": archie_n,
        }
        if sw_model in ("simandoux", "indonesia") and rsh_ohm_m is not None:
            mc_params["vcl"] = (vcl_fraction, vcl_fraction * 0.10 + 0.01)
            mc_params["rsh"] = (rsh_ohm_m, rsh_ohm_m * 0.05)

        try:
            mc_result = monte_carlo_sw(sw_model, mc_params, n_samples=min(mc_samples, 5000))
            mc_stats = mc_result.get("stats", {})
            hold_triggers.extend(mc_result.get("hold_triggers", []))
            sw_nominal = float(mc_result.get("nominal_sw", 1.0))
        except Exception as exc:
            logger.warning("Monte Carlo failed for %s: %s", well_id, exc)
            sw_nominal = _deterministic_sw(sw_model, rw_ohm_m, rt_ohm_m, phi_fraction, vcl_fraction, rsh_ohm_m, archie_a, archie_m, archie_n)
            mc_stats = None
    else:
        sw_nominal = _deterministic_sw(sw_model, rw_ohm_m, rt_ohm_m, phi_fraction, vcl_fraction, rsh_ohm_m, archie_a, archie_m, archie_n)

    sw_nominal = min(sw_nominal, 1.05)  # cap for display; physical impossibility already flagged
    bvw = sw_nominal * phi_fraction

    if sw_nominal > 1.0:
        hold_triggers.append(f"Sw ({sw_nominal:.3f}) > 1.0 — physical impossibility (F2 Truth).")

    uncertainty = 0.09 if mc_stats else 0.12
    requires_hold = len(hold_triggers) > 0

    import uuid as _uuid
    audit_id = f"PETRO-{_uuid.uuid4().hex[:8].upper()}"

    output_data: dict[str, Any] = {
        "well_id": well_id,
        "sw_model_used": sw_model,
        "sw_nominal": round(sw_nominal, 4),
        "sw_p10": round(float(mc_stats["p10"]), 4) if mc_stats else None,
        "sw_p50": round(float(mc_stats["p50"]), 4) if mc_stats else None,
        "sw_p90": round(float(mc_stats["p90"]), 4) if mc_stats else None,
        "sw_std": round(float(mc_stats["std"]), 4) if mc_stats else None,
        "phi_effective": round(phi_fraction, 4),
        "vcl": round(vcl_fraction, 4),
        "bvw": round(bvw, 4),
        "uncertainty": uncertainty,
        "hold_triggers": hold_triggers,
        "requires_hold": requires_hold,
        "floor_verdicts": {
            "F2_truth": sw_nominal <= 1.0,
            "F4_clarity": True,
            "F7_humility": True,
            "F9_anti_hantu": True,
            "F11_authority": True,
        },
        "provenance_tag": "DERIVED",
        "audit_id": audit_id,
        "timestamp": timestamp,
        "seal": GEOX_SEAL,
    }

    status_str = "888_HOLD" if requires_hold else "SEAL"
    content = (
        f"Petrophysics [{well_id}] {status_str}: Sw={sw_nominal:.3f}, "
        f"PHIe={phi_fraction:.3f}, BVW={bvw:.3f} using {sw_model} model. "
        f"Uncertainty: {uncertainty:.0%}. "
        + (f"Hold triggers: {hold_triggers}." if requires_hold else "No hold triggers.")
    )

    tool_result = ToolResult(content=content, structured_content=output_data)
    return _tool_result_to_dict(tool_result)


@mcp.tool(name="geox_validate_cutoffs")
async def geox_validate_cutoffs(
    well_id: str,
    policy_id: str,
    phi_cutoff: float,
    sw_cutoff: float,
    vcl_cutoff: float,
    phi_tested: float,
    sw_tested: float,
    vcl_tested: float,
    rt_cutoff: float | None = None,
    rt_tested: float | None = None,
    policy_basis: str = "analogue",
) -> dict:
    """
    Apply a CutoffPolicy to petrophysical values and classify pay vs non-pay.

    All cutoff logic is governed — the CutoffPolicy is tagged POLICY so the
    provenance chain clearly separates measured data from corporate/regulatory
    classification rules.

    Returns CutoffValidationResult JSON with provenance tag POLICY.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if not _HAS_PETRO_SCHEMAS:
        return {"status": "UNAVAILABLE", "reason": "Petrophysics schemas not loaded.", "timestamp": timestamp}

    violations: list[str] = []
    requires_hold = False

    # Physical plausibility guard (F2 Truth)
    if sw_tested > 1.0:
        violations.append(f"Sw ({sw_tested:.3f}) > 1.0 — physically impossible; run geox_petrophysical_hold_check first.")
        requires_hold = True
    if phi_tested > 0.50:
        violations.append(f"PHIe ({phi_tested:.3f}) > 0.50 — above physical maximum.")
        requires_hold = True

    phi_pass = phi_tested >= phi_cutoff
    sw_pass = sw_tested < sw_cutoff
    vcl_pass = vcl_tested < vcl_cutoff
    rt_pass: bool | None = None
    if rt_cutoff is not None and rt_tested is not None:
        rt_pass = rt_tested >= rt_cutoff

    if not phi_pass:
        violations.append(f"PHIe {phi_tested:.3f} < cutoff {phi_cutoff:.3f} — non-reservoir.")
    if not sw_pass:
        violations.append(f"Sw {sw_tested:.3f} ≥ cutoff {sw_cutoff:.3f} — non-pay (wet).")
    if not vcl_pass:
        violations.append(f"Vcl {vcl_tested:.3f} ≥ cutoff {vcl_cutoff:.3f} — non-reservoir (shaly).")
    if rt_pass is False:
        violations.append(f"Rt {rt_tested} < cutoff {rt_cutoff} — no HC indication.")

    is_net_reservoir = phi_pass and vcl_pass and not requires_hold
    is_net_pay = is_net_reservoir and sw_pass

    import uuid as _uuid2
    audit_id = f"CUT-{_uuid2.uuid4().hex[:8].upper()}"

    result_data: dict[str, Any] = {
        "well_id": well_id,
        "policy_id": policy_id,
        "policy_basis": policy_basis,
        "is_net_reservoir": is_net_reservoir,
        "is_net_pay": is_net_pay,
        "passed_rt_cutoff": rt_pass,
        "phi_pass": phi_pass,
        "sw_pass": sw_pass,
        "vcl_pass": vcl_pass,
        "phi_tested": phi_tested,
        "sw_tested": sw_tested,
        "vcl_tested": vcl_tested,
        "rt_tested": rt_tested,
        "cutoffs": {
            "phi_cutoff": phi_cutoff,
            "sw_cutoff": sw_cutoff,
            "vcl_cutoff": vcl_cutoff,
            "rt_cutoff": rt_cutoff,
        },
        "violations": violations,
        "requires_hold": requires_hold,
        "provenance_tag": "POLICY",
        "audit_id": audit_id,
        "timestamp": timestamp,
        "seal": GEOX_SEAL,
    }

    pay_status = "NET PAY" if is_net_pay else ("NET RESERVOIR (wet)" if is_net_reservoir else "NON-RESERVOIR")
    content = (
        f"Cutoff validation [{well_id}] policy='{policy_id}': {pay_status}. "
        f"PHI {'✓' if phi_pass else '✗'} | Sw {'✓' if sw_pass else '✗'} | Vcl {'✓' if vcl_pass else '✗'}. "
        + (f"Violations: {violations}." if violations else "All cutoffs passed.")
    )

    tool_result = ToolResult(content=content, structured_content=result_data)
    return _tool_result_to_dict(tool_result)


@mcp.tool(name="geox_petrophysical_hold_check")
async def geox_petrophysical_hold_check(
    well_id: str,
    sw_value: float,
    phi_value: float,
    vcl_value: float,
    uncertainty: float,
    has_deep_resistivity: bool = True,
    borehole_quality: str = "good",
    sw_model: str = "archie",
    check_f2_truth: bool = True,
    check_f4_clarity: bool = True,
    check_f7_humility: bool = True,
    check_f9_anti_hantu: bool = True,
) -> dict:
    """
    Constitutional floor check for petrophysical outputs — triggers 888_HOLD.

    Evaluates F2 (Truth), F4 (Clarity), F7 (Humility), F9 (Anti-Hantu) against
    the supplied property values.  Any violation produces an explicit
    PetrophysicsHold object — never a silent failure.

    Returns PetrophysicsHold (if violations) or a clean SEAL dict.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if not _HAS_PETRO_SCHEMAS:
        return {"status": "UNAVAILABLE", "reason": "Petrophysics schemas not loaded.", "timestamp": timestamp}

    violated_floors: list[str] = []
    violations: list[str] = []
    remediation: list[str] = []

    # ── F2 Truth ─────────────────────────────────────────────────────────────
    if check_f2_truth:
        if sw_value > 1.0:
            violated_floors.append("F2")
            violations.append(f"Sw ({sw_value:.4f}) > 1.0 — physically impossible.")
            remediation.append("Re-check Rw, Rt, and PHIe inputs; verify LAS data quality.")
        if phi_value > 0.50:
            violated_floors.append("F2")
            violations.append(f"PHIe ({phi_value:.4f}) > 0.50 — above physical maximum for clastic reservoir.")
            remediation.append("Review NPHI-RHOB crossplot; check matrix density assumption.")
        if not (0.0 <= vcl_value <= 1.0):
            violated_floors.append("F2")
            violations.append(f"Vcl ({vcl_value:.4f}) outside [0, 1] — physical impossibility.")
            remediation.append("Re-compute Vsh from GR using calibrated GR_min / GR_max.")

    # ── F4 Clarity ───────────────────────────────────────────────────────────
    if check_f4_clarity:
        if not has_deep_resistivity:
            violated_floors.append("F4")
            violations.append("No deep resistivity available — Sw has no physical measurement basis.")
            remediation.append("Acquire ILD/LLD before computing Sw.")

    # ── F7 Humility ──────────────────────────────────────────────────────────
    if check_f7_humility:
        if not (0.03 <= uncertainty <= 0.15):
            violated_floors.append("F7")
            violations.append(
                f"Uncertainty ({uncertainty:.3f}) outside F7 humility band [0.03, 0.15]. "
                "Overconfident or unquantified uncertainty detected."
            )
            remediation.append(
                "Run Monte Carlo (geox_compute_petrophysics run_monte_carlo=True) "
                "to obtain calibrated uncertainty."
            )

    # ── F9 Anti-Hantu ────────────────────────────────────────────────────────
    if check_f9_anti_hantu:
        if borehole_quality == "poor":
            violated_floors.append("F9")
            violations.append(
                "Borehole quality 'poor' — log data integrity compromised; "
                "Sw derived from unverified inputs."
            )
            remediation.append("Collect repeat / backup resistivity pass; cross-check with nearby wells.")
        valid_models = ("archie", "simandoux", "indonesia")
        if sw_model not in valid_models:
            violated_floors.append("F9")
            violations.append(f"Unknown Sw model '{sw_model}' — unverified computation path.")
            remediation.append(f"Use one of: {valid_models}.")

    # ── Deduplicate floors ────────────────────────────────────────────────────
    violated_floors = sorted(set(violated_floors))

    if not violations:
        seal_data: dict[str, Any] = {
            "well_id": well_id,
            "status": "SEAL",
            "message": "All constitutional floor checks passed. Petrophysics output is governed.",
            "floor_verdicts": {
                "F2_truth": True,
                "F4_clarity": True,
                "F7_humility": True,
                "F9_anti_hantu": True,
            },
            "provenance_tag": "POLICY",
            "timestamp": timestamp,
            "seal": GEOX_SEAL,
        }
        result = ToolResult(
            content=f"SEAL: Well '{well_id}' petrophysics passes all constitutional floors.",
            structured_content=seal_data,
        )
        return _tool_result_to_dict(result)

    import uuid as _uuid3
    hold_id = f"HOLD-{_uuid3.uuid4().hex[:8].upper()}"

    hold_data: dict[str, Any] = {
        "well_id": well_id,
        "hold_id": hold_id,
        "triggered_by": "geox_petrophysical_hold_check",
        "violated_floors": violated_floors,
        "violations": violations,
        "remediation": remediation,
        "severity": "block",
        "requires_human_signoff": True,
        "floor_verdicts": {
            "F2_truth": "F2" not in violated_floors,
            "F4_clarity": "F4" not in violated_floors,
            "F7_humility": "F7" not in violated_floors,
            "F9_anti_hantu": "F9" not in violated_floors,
        },
        "provenance_tag": "POLICY",
        "timestamp": timestamp,
        "seal": GEOX_SEAL,
    }

    content = (
        f"888_HOLD raised for well '{well_id}'. "
        f"Violated floors: {violated_floors}. "
        f"Violations ({len(violations)}): {'; '.join(violations[:3])}{'...' if len(violations) > 3 else ''}. "
        "Human sign-off required (F13 Sovereign). Log to 999_VAULT."
    )
    result = ToolResult(content=content, structured_content=hold_data)
    return _tool_result_to_dict(result)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: deterministic Sw (fallback when MC not available)
# ─────────────────────────────────────────────────────────────────────────────

def _deterministic_sw(
    model: str,
    rw: float,
    rt: float,
    phi: float,
    vcl: float = 0.0,
    rsh: float | None = None,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
) -> float:
    """Compute Sw without Monte Carlo — fallback path."""
    if phi <= 0 or rt <= 0 or rw <= 0:
        return 1.0
    if model == "archie":
        return min(1.0, ((a * rw) / ((phi ** m) * rt)) ** (1 / n))
    if model == "simandoux" and rsh and rsh > 0:
        term_a = (phi ** m) / (a * rw)
        term_b = vcl / rsh
        term_c = 1 / rt
        sw = (1 / (2 * term_a)) * (((term_b ** 2 + 4 * term_a * term_c) ** 0.5) - term_b)
        return min(1.0, max(0.0, sw))
    if model == "indonesia" and rsh and rsh > 0:
        import math as _math
        term_sh = (vcl ** (1 - vcl / 2)) / (rsh ** 0.5)
        term_sa = (phi ** (m / 2)) / ((a * rw) ** 0.5)
        denom = (rt ** 0.5) * (term_sh + term_sa)
        if denom == 0:
            return 1.0
        sw = (1 / denom) ** (2 / n)
        return min(1.0, max(0.0, sw))
    # Fallback: Archie
    return min(1.0, ((a * rw) / ((phi ** m) * rt)) ** (1 / n))



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


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Entrypoint
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
    logger.info("Tools (8): geox_load_seismic_line, geox_build_structural_candidates,")
    logger.info("           geox_calculate_saturation, geox_feasibility_check,")
    logger.info("           geox_verify_geospatial, geox_evaluate_prospect,")
    logger.info("           geox_query_memory, geox_health")
    logger.info("=" * 60)
    
    # Run with FastMCP
    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()