"""
GEOX MCP Server - Updated with Floors-hash endpoint
Adds F1-F13 version hash to health for federation router verification.
"""

import argparse
import os
import hashlib
from datetime import datetime
from typing import Any, cast

from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

# Tools
from arifos.geox.tools.seismic.seismic_single_line_tool import SeismicSingleLineTool

# Prefab UI Views (Forge 2)
from arifos.geox.apps.prefab_views import (
    feasibility_check_view,
    geospatial_view,
    prospect_verdict_view,
    seismic_section_view,
    structural_candidates_view,
)

# ═══════════════════════════════════════════════════════════════════════════════
# F1-F13 CONSTITUTIONAL CANON — Floors Version
# ═══════════════════════════════════════════════════════════════════════════════

FLOORS_CANON = {
    "F1": "AMANAH — Reversibility",
    "F2": "TRUTH — Evidence required",
    "F3": "TRI_WITNESS — W³ ≥ 0.95",
    "F4": "CLARITY — Entropy ↓",
    "F5": "COHERENCE — Paradox-free",
    "F6": "BOUNDED — Scope locked",
    "F7": "DIGNITY — Agent respect",
    "F8": "SVERD — Sovereign limits",
    "F9": "PROGRESS — Capability growth",
    "F10": "REFLECTION — Self-audit",
    "F11": "CONTINUITY — Auth continuity",
    "F12": "DEFENSE — No injection",
    "F13": "SOVEREIGN — 888_HOLD required",
}

FLOORS_VERSION = hashlib.sha256(str(sorted(FLOORS_CANON.items())).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Server Initialisation
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="GEOX Earth Witness",
    instructions="Governed domain surface for subsurface inverse modelling.",
    version="0.4.3",
)


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


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH ENDPOINTS — With Floors-hash for federation verification
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> PlainTextResponse:
    """Minimal health endpoint for HTTP deployments and CI smoke tests."""
    return PlainTextResponse("OK")


@mcp.custom_route("/health/details", methods=["GET"])
async def health_details(_: Request) -> JSONResponse:
    """Structured health payload for deployment probes — includes Floors-hash."""
    return JSONResponse(
        {
            "ok": True,
            "service": "geox-earth-witness",
            "version": "0.4.3",
            "mode": "governance-engine",
            "forge": "Forge-2-Apps",
            "engine_runtime": "stubbed",
            "timestamp": datetime.utcnow().isoformat(),
            # Federation verification — router checks this hash
            "floors_hash": FLOORS_VERSION,
            "floors_count": len(FLOORS_CANON),
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tools — Forge 2: app=True on every tool
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_load_seismic_line", app=True)
async def geox_load_seismic_line(
    line_id: str,
    survey_path: str = "default_survey",
) -> ToolResult:
    """Load a seismic line from a survey and return section with annotations."""
    return await SeismicSingleLineTool().execute(line_id=line_id, survey_path=survey_path)


@mcp.tool(name="geox_interpret_line", app=True)
async def geox_interpret_line(
    line_id: str,
    interpretation: str,
    survey_path: str = "default_survey",
) -> ToolResult:
    """Interpret a seismic line with a structural hypothesis."""
    tool = SeismicSingleLineTool()
    result = await tool.execute(line_id=line_id, survey_path=survey_path)
    candidates = _interpretation_to_candidates(result)
    return ToolResult(
        text=f"Interpretation '{interpretation}' applied to line {line_id}. "
        f"Generated {len(candidates)} candidates.",
        app_view=prospect_verdict_view(candidates),
    )


@mcp.tool(name="geox_check_feasibility", app=True)
async def geox_check_feasibility(
    prospect_name: str,
    depth_estimate_m: float,
    area_km2: float,
) -> ToolResult:
    """Check geological feasibility of a prospect."""
    return ToolResult(
        text=f"Feasibility check for {prospect_name}: "
        f"depth={depth_estimate_m}m, area={area_km2}km²",
        app_view=feasibility_view(prospect_name, depth_estimate_m, area_km2),
    )


@mcp.tool(name="geox_geospatial_query", app=True)
async def geox_geospatial_query(
    lat: float,
    lon: float,
    radius_km: float = 10.0,
) -> ToolResult:
    """Query geological data for a geographic location."""
    return ToolResult(
        text=f"Geospatial query: ({lat}, {lon}) radius {radius_km}km",
        app_view=geospatial_view(lat, lon, radius_km),
    )


@mcp.tool(name="geox_structural_candidates", app=True)
async def geox_structural_candidates(
    line_id: str,
    min_confidence: float = 0.7,
) -> ToolResult:
    """Get structural candidates above confidence threshold."""
    tool = SeismicSingleLineTool()
    result = await tool.execute(line_id=line_id)
    candidates = _interpretation_to_candidates(result)
    filtered = [c for c in candidates if c.get("confidence", 0) >= min_confidence]
    return ToolResult(
        text=f"Found {len(filtered)} structural candidates above {min_confidence} confidence.",
        app_view=structural_candidates_view(filtered),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# A2A ENVELOPE SCHEMA — For federation router
# ═══════════════════════════════════════════════════════════════════════════════

A2A_SCHEMA = """
{
  "context_id": "uuid — case/session identifier",
  "governance_level": {
    "floors_hash": "sha256[0:16] — F1-F13 version",
    "floors_count": 13,
    "omega": 0.04,  // Uncertainty band
    "eval_gates": ["F1", "F2", "F3", "F13"]
  },
  "telemetry": {
    "dS": -0.5,       // Entropy delta
    "peace2": 1.2,   // Peace index
    "kappa_r": 0.96, // Recall quality
    "echoDebt": 0.07,
    "shadow": 0.05,
    "confidence": 0.93,
    "psi_le": 1.05,
    "verdict": "Alive|SABAR|888_HOLD"
  },
  "witness": {
    "human": 1.0,
    "ai": 0.95,
    "earth": 0.9
  },
  "qdf": 0.91
}
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GEOX MCP Server")
    parser.add_argument("--port", type=int, default=8081, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(mcp.app, host=args.host, port=args.port, log_level="info")