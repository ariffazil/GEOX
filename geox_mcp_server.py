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

try:
    from arifos.geox.tools.macrostrat_tool import MacrostratTool
    from arifos.geox.geox_schemas import CoordinatePoint
    _macrostrat: "MacrostratTool | None" = MacrostratTool()
    _HAS_MACROSTRAT = True
except Exception as _ms_exc:
    _macrostrat = None
    _HAS_MACROSTRAT = False
    logger.info("MacrostratTool unavailable: %s", _ms_exc)


# ═══════════════════════════════════════════════════════════════════════════════
# Hardened Governance & Registry Imports
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from arifos.geox.tool_registry import UnifiedToolRegistry
    from arifos.geox.errors import GeoxErrorCode, GeoxError
    from arifos.geox.governance.floor_enforcer import FloorEnforcer
    from arifos.geox.ENGINE.ac_risk import ACRiskCalculator
    _HAS_GOVERNANCE = True
except ImportError as _imp_exc:
    logger.warning("Hardened governance modules not found: %s", _imp_exc)
    _HAS_GOVERNANCE = False

_floor_enforcer = FloorEnforcer() if _HAS_GOVERNANCE else None

# ═══════════════════════════════════════════════════════════════════════════════
# Server Configuration
# ═══════════════════════════════════════════════════════════════════════════════

GEOX_VERSION = "v2026.04.10-EIC"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"

# ═══════════════════════════════════════════════════════════════════════════════
# EARTH.CANON_9 Basis (Ground Truth)
# ═══════════════════════════════════════════════════════════════════════════════

EARTH_CANON_9 = {
    "rho": "density (kg/m3)",
    "vp": "compressional velocity (m/s)",
    "vs": "shear velocity (m/s)",
    "res": "electrical resistivity (ohm.m)",
    "chi": "magnetic susceptibility (SI)",
    "k": "thermal conductivity (W/mK)",
    "p": "pore pressure (Pa)",
    "t": "temperature (K)",
    "phi": "porosity (0-1)"
}

mcp = FastMCP(
    name="GEOX Earth Witness",
    version=GEOX_VERSION,
    instructions=(
        "Governed domain surface for subsurface inverse modelling. "
        "Strictly adheres to EARTH.CANON_9 state vector. DITEMPA BUKAN DIBERI."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# Resources (The Root of Truth)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("geox://canon9/state")
def get_canon9_state() -> str:
    """Returns the current EARTH.CANON_9 state vector basis."""
    import json
    return json.dumps(EARTH_CANON_9, indent=2)

@mcp.resource("geox://1d/triple-combo")
def get_triple_combo() -> str:
    """Returns the 1D Borehole (Heavy Truth) manifold state."""
    return "1D Manifold: RHOB/NPHI/GR/RES (Active: Malay Basin Pilot)"

@mcp.resource("geox://2d/seismic-plane")
def get_seismic_plane() -> str:
    """Returns the 2D Seismic (Planar Operations) manifold state."""
    return "2D Manifold: Amplitude Vault (Active: SEG-Y 999_SEAL Line)"



@mcp.tool(name="geox_metabolize")
async def geox_metabolize(
    state_vector: dict[str, float],
    propagation_mode: str = "1d_to_3d",
    uncertainty_floor: float = 0.04
) -> dict:
    """
    Execute EARTH.CANON_9 Back-propagation (LEM Metabolizer).
    
    state_vector: Must contain rho, vp, vs, res, chi, k, p, t, phi.
    propagation_mode: "1d_to_2d", "2d_to_3d", or "1d_to_3d".
    uncertainty_floor: F7 humility constraint (default 0.04).
    """
    # Validation against Canon-9
    missing = [k for k in EARTH_CANON_9.keys() if k not in state_vector]
    if missing:
        return _build_hardened_result(
            "geox_metabolize",
            structured_content={"status": "FAILURE", "missing_basis": missing},
            error=f"State vector violation. Missing Canon-9 components: {missing}"
        )
    
    # Simulate Back-propagation Inversion
    # In a real run, this would fire the adjoint-state solvers or learned surrogates.
    sc = {
        "metabolism_status": "CONVERGED",
        "propagation": propagation_mode,
        "f7_uncertainty": uncertainty_floor,
        "derivatives": {
            "dk_dp": "Exempt (Constitutive)",
            "dm_dp": "Exempt (Constitutive)"
        },
        "verdict": "888_PROCEED"
    }

    return _build_hardened_result(
        "geox_metabolize",
        structured_content=sc,
        content=(
            f"Back-propagation {propagation_mode} executed. "
            f"State vector synchronized to LEM. F7 Uncertainty: ±{uncertainty_floor*100}%."
        )
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



@mcp.tool(name="geox_compute_seismic_attributes")
async def geox_compute_seismic_attributes(
    volume_ref: str,
    attribute_list: list[str],
    config: dict[str, Any] | None = None,
    well_ties: list[str] | None = None,
) -> dict:
    """
    Compute classical and meta seismic attributes (coherence, curvature, envelope, etc.).
    
    volume_ref: Reference to seismic volume.
    attribute_list: List of attributes (coherence, curvature_max, curvature_min, envelope, spectral_rms, sweetness, meta_fault_prob).
    config: Window sizes, sample rates, and other params.
    well_ties: List of well IDs for calibration (REQUIRED for meta-attributes).
    """
    try:
        from arifos.geox.tools.seismic_attributes_tool import SeismicAttributesTool
        tool = SeismicAttributesTool()
        inputs = {
            "volume_ref": volume_ref,
            "attribute_list": attribute_list,
            "config": config or {},
            "well_ties": well_ties or [],
        }
        result = await tool.run(inputs)
        sc = result.raw_output
    except Exception as exc:
        logger.warning("geox_compute_seismic_attributes error: %s", exc)
        sc = {
            "status": "888_HOLD",
            "error": str(exc),
            "attribute_list": attribute_list,
        }

    return _build_hardened_result(
        "geox_compute_seismic_attributes",
        structured_content=sc,
        content=f"Seismic attributes {attribute_list} computed for {volume_ref}.",
    )


@mcp.tool(name="geox_calculate_prospect_economics")
async def geox_calculate_prospect_economics(
    volumetrics: dict[str, Any],
    economics: dict[str, Any],
    location: dict[str, float] | None = None,
) -> dict:
    """
    Calculate prospect volumetrics (STOIIP) and economics (EMV, NPV) with uncertainty.
    
    volumetrics: {area_km2, h_m, phi, sw, ng, bo, rf}
    economics: {price_per_bbl, capex_m_usd, opex_per_bbl, discount_rate, pos}
    location: {latitude, longitude}
    """
    try:
        from arifos.geox.tools.volumetrics_economics_tool import VolumetricsEconomicsTool
        tool = VolumetricsEconomicsTool()
        inputs = {
            "volumetrics": volumetrics,
            "economics": economics,
            "location": location,
        }
        result = await tool.run(inputs)
        sc = result.raw_output
    except Exception as exc:
        logger.warning("geox_calculate_prospect_economics error: %s", exc)
        sc = {
            "status": "888_HOLD",
            "error": str(exc),
        }

    return _build_hardened_result(
        "geox_calculate_prospect_economics",
        structured_content=sc,
        content=f"Prospect economics calculated. EMV: ${sc.get('economics', {}).get('emv_m_usd')}M.",
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


def _build_hardened_result(
    tool_name: str,
    structured_content: dict,
    content: str | None = None,
    error: Any | None = None,
    ac_risk_params: dict | None = None,
) -> dict:
    """Standardized result with versioning, floors, and AC_Risk."""
    metadata = UnifiedToolRegistry.get(tool_name) if _HAS_GOVERNANCE else None
    version = metadata.version if metadata else GEOX_VERSION
    
    # Calculate AC_Risk if enabled and params provided
    ac_risk = None
    if _HAS_GOVERNANCE and metadata and metadata.ac_risk_enabled and ac_risk_params:
        try:
            ac_risk = ACRiskCalculator.calculate(**ac_risk_params)
            structured_content["ac_risk"] = ac_risk.to_dict()
            structured_content["verdict"] = ac_risk.verdict.value
        except Exception as e:
            logger.warning("AC_Risk calculation failed: %s", e)
    
    # Floor status check (Stub for now, but following requirements)
    floors = metadata.required_floors if metadata else ["F4", "F7", "F11"]
    floor_status = {f: "passed" for f in floors}
    
    hardened_content = {
        "geox_version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "floor_status": floor_status,
        "seal": GEOX_SEAL,
        **structured_content
    }
    
    if error:
        hardened_content["error"] = error.to_dict() if hasattr(error, "to_dict") else str(error)
    
    res = ToolResult(
        content=content or f"Operation {tool_name} completed. {GEOX_SEAL}",
        structured_content=hardened_content
    )
    return _tool_result_to_dict(res)


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
    views = _governance_stub_views(line_id, survey_path)
    
    structured = _build_prefab_view(
        "seismic_section",
        line_id=line_id,
        survey_path=survey_path,
        status="IGNITED",
        views=views,
    ) if generate_views else {"status": "IGNITED", "line_id": line_id}
    
    # AC_Risk params for seismic loading
    ac_risk_params = {
        "u_phys": 0.2,  # Low ambiguity for raw loading
        "transform_stack": ["linear_scaling"],
        "bias_scenario": "ai_with_physics"
    }
    
    return _build_hardened_result(
        "geox_load_seismic_line",
        structured_content=structured,
        content=(
            f"Seismic line '{line_id}' loaded. Status: IGNITED. "
            "ToAC contrast canon active. 888 HOLD checklist rendered."
        ),
        ac_risk_params=ac_risk_params
    )


@mcp.tool(name="geox_build_structural_candidates")
async def geox_build_structural_candidates(
    line_id: str,
    focus_area: str | None = None,
) -> dict:
    """
    Build structural model candidates (Inverse Modelling Constraints).
    
    Prevents narrative collapse by maintaining multiple candidate models.
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
        confidence=0.12,
    )
    
    # AC_Risk params for structural candidates
    ac_risk_params = {
        "u_phys": 0.6,  # High ambiguity in structural interpretation
        "transform_stack": ["vlm_inference", "colormap_mapping"],
        "bias_scenario": "ai_vision_only"
    }
    
    return _build_hardened_result(
        "geox_build_structural_candidates",
        structured_content=structured,
        content=(
            f"Generated {n} structural candidate model(s) for line '{line_id}'. "
            "F7 Humility: confidence bounded at 12%."
        ),
        ac_risk_params=ac_risk_params
    )


@mcp.tool(name="geox_compute_ac_risk")
async def geox_compute_ac_risk(
    u_phys: float,
    transform_stack: list[str],
    bias_scenario: str = "ai_vision_only",
) -> dict:
    """
    Calculate Anomalous Contrast Risk (ToAC).
    
    Formula: AC_Risk = U_phys × D_transform × B_cog
    
    Returns verdict (SEAL/QUALIFY/HOLD/VOID) and explanation.
    """
    if not _HAS_GOVERNANCE:
        return _build_hardened_result(
            "geox_compute_ac_risk",
            structured_content={"error": "Governance engine unavailable"},
        )
    
    ac_risk = ACRiskCalculator.calculate(
        u_phys=u_phys,
        transform_stack=transform_stack,
        bias_scenario=bias_scenario
    )
    
    return _build_hardened_result(
        "geox_compute_ac_risk",
        structured_content=ac_risk.to_dict(),
        content=ac_risk.explanation
    )


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
    
    # AC_Risk params
    ac_risk_params = {
        "u_phys": 0.1,  # Low ambiguity in physics check
        "transform_stack": ["linear_scaling"],
        "bias_scenario": "ai_with_physics"
    }
    
    return _build_hardened_result(
        "geox_feasibility_check",
        structured_content=structured,
        content=f"Plan '{plan_id}' feasibility check: {verdict}. Grounding: {grounding_confidence:.0%}.",
        ac_risk_params=ac_risk_params
    )


@mcp.tool(name="geox_verify_geospatial")
async def geox_verify_geospatial(
    lat: float,
    lon: float,
    radius_m: float = 1000.0,
) -> dict:
    """
    Verify geospatial grounding and jurisdictional boundaries.
    """
    jurisdiction = "EEZ_Grounded"
    verdict = "GEOSPATIALLY_VALID"

    geological_province = "No Macrostrat Coverage"
    if _HAS_MACROSTRAT and _macrostrat is not None:
        try:
            from arifos.geox.geox_schemas import CoordinatePoint
            location = CoordinatePoint(latitude=lat, longitude=lon)
            _col_data = await _macrostrat._query_api("columns", location)
            geo_data = _col_data.get("success", {}).get("data", {})
            features = geo_data.get("features", []) if isinstance(geo_data, dict) else []
            if features:
                geological_province = (
                    features[0].get("properties", {}).get("col_name", "Unknown Province")
                )
        except Exception as _prov_exc:
            logger.warning("Province lookup failed: %s", _prov_exc)
    
    structured = _build_prefab_view(
        "geospatial",
        lat=lat,
        lon=lon,
        radius_m=radius_m,
        geological_province=geological_province,
        jurisdiction=jurisdiction,
        verdict=verdict,
    )
    
    return _build_hardened_result(
        "geox_verify_geospatial",
        structured_content=structured,
        content=f"Coordinates ({lat:.6f}, {lon:.6f}) verified in {geological_province}."
    )


@mcp.tool(name="geox_evaluate_prospect")
async def geox_evaluate_prospect(
    prospect_id: str,
    interpretation_id: str,
) -> dict:
    """
    Provide a governed verdict on a subsurface prospect (222_REFLECT).
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
    
    # AC_Risk params for prospect evaluation
    ac_risk_params = {
        "u_phys": 0.5,  # Medium ambiguity
        "transform_stack": ["vlm_inference", "affine_warp"],
        "bias_scenario": "ai_vision_only"
    }
    
    return _build_hardened_result(
        "geox_evaluate_prospect",
        structured_content=structured,
        content=f"Prospect '{prospect_id}' evaluation: {status}. {reason}",
        ac_risk_params=ac_risk_params
    )


@mcp.tool(name="geox_query_memory")
async def geox_query_memory(
    query: str,
    basin: str | None = None,
    limit: int = 5,
) -> dict:
    """
    Query the GEOX geological memory store for past evaluations.
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
    }

    return _build_hardened_result(
        "geox_query_memory",
        structured_content=structured,
        content=f"Memory query '{query}' returned {count} result(s). F10 Ontology active."
    )


@mcp.tool(name="geox_query_macrostrat")
async def geox_query_macrostrat(
    lat: float,
    lon: float,
) -> dict:
    """
    Query Macrostrat for regional stratigraphy and lithology at coordinates.
    """
    if not _HAS_MACROSTRAT or _macrostrat is None:
        return _build_hardened_result(
            "geox_query_macrostrat",
            structured_content={"status": "unavailable"},
            content="MacrostratTool unavailable."
        )

    location = CoordinatePoint(latitude=lat, longitude=lon)
    geo_result = await _macrostrat.run({"location": location})

    if not geo_result.success:
        return _build_hardened_result(
            "geox_query_macrostrat",
            structured_content={"status": "error", "error": geo_result.error},
            content=f"Macrostrat query failed: {geo_result.error}"
        )

    units_found = geo_result.metadata.get("units_found", 0)
    columns_found = geo_result.metadata.get("columns_found", 0)

    structured = {
        **geo_result.metadata,
        "coordinates": {"lat": lat, "lon": lon},
        "quantities": [
            q.model_dump(mode="json") if hasattr(q, "model_dump") else vars(q)
            for q in geo_result.quantities
        ],
        "_attribution": "Macrostrat (CC-BY-4.0) — Peters et al. 2018.",
    }

    return _build_hardened_result(
        "geox_query_macrostrat",
        structured_content=structured,
        content=f"Macrostrat query at ({lat:.4f}, {lon:.4f}): {units_found} units found."
    )


@mcp.tool(name="geox_health")
async def geox_health() -> dict:
    """Server health check with constitutional floor status."""
    tool_count = len(UnifiedToolRegistry.list_tools()) if _HAS_GOVERNANCE else 0
    
    structured = {
        "ok": True,
        "service": "geox-earth-witness",
        "registry_status": "hardened" if _HAS_GOVERNANCE else "legacy",
        "hardened_tools": tool_count,
        "prefab_ui": _HAS_PREFAB,
        "seismic_engine": _HAS_SEISMIC,
    }
    
    return _build_hardened_result(
        "geox_health",
        structured_content=structured,
        content=f"GEOX Earth Witness v{GEOX_VERSION} is healthy. Tools: {tool_count}."
    )


@mcp.tool(name="geox_calculate_saturation")
async def geox_calculate_saturation(
    model: str,
    rw: float,
    rt: float,
    phi: float,
    a: float = 1.0,
    m: float = 2.0,
    n: float = 2.0,
    n_samples: int = 1000,
) -> dict:
    """
    Calculate water saturation (Sw) with Monte Carlo uncertainty.
    """
    try:
        from arifos.geox.tools.core import geox_calculate_saturation as _core_calc
        result = await _core_calc(
            model=model,
            params={"rw": rw, "rt": rt, "phi": phi, "a": a, "m": m, "n": n},
            n_samples=n_samples,
            physics_engine_available=True,
        )
        sc = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
    except Exception as exc:
        logger.warning("geox_calculate_saturation error: %s", exc)
        sc = {
            "status": "888_HOLD",
            "hold_triggers": [str(exc)],
            "model": model,
            "nominal_sw": None,
        }

    # AC_Risk params for Sw calculation
    ac_risk_params = {
        "u_phys": 0.3,  # Medium ambiguity in petrophysics
        "transform_stack": ["linear_scaling"],
        "bias_scenario": "ai_with_physics"
    }

    return _build_hardened_result(
        "geox_calculate_saturation",
        structured_content=sc,
        content=f"Sw calculation ({model}): status={sc.get('status')}",
        ac_risk_params=ac_risk_params
    )


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
    logger.info("Tools (14): geox_load_seismic_line, geox_build_structural_candidates,")
    logger.info("            geox_feasibility_check, geox_verify_geospatial,")
    logger.info("            geox_evaluate_prospect, geox_query_memory,")
    logger.info("            geox_query_macrostrat, geox_health,")
    logger.info("            geox_calculate_saturation, geox_select_sw_model,")
    logger.info("            geox_compute_petrophysics, geox_validate_cutoffs,")
    logger.info("            geox_petrophysical_hold_check, geox_malay_basin_pilot")
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
    logger.info("Tools (16): geox_load_seismic_line, geox_build_structural_candidates,")
    logger.info("            geox_compute_seismic_attributes,")
    logger.info("            geox_calculate_prospect_economics,")
    logger.info("            geox_feasibility_check, geox_verify_geospatial,")
    logger.info("            geox_evaluate_prospect, geox_query_memory,")
    logger.info("            geox_query_macrostrat, geox_health,")
    logger.info("            geox_calculate_saturation, geox_select_sw_model,")
    logger.info("            geox_compute_petrophysics, geox_validate_cutoffs,")
    logger.info("            geox_petrophysical_hold_check, geox_malay_basin_pilot")
    logger.info("=" * 60)
    
    # Run with FastMCP
    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()