"""
GEOX Control Plane — FastMCP Server

Canonical entrypoint for Horizon/FastMCP Cloud deployments.
This is the CONTROL PLANE — it routes requests but does not execute calculations.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import os
import logging
import sys
import argparse
import json
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from datetime import datetime, timezone
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONTRACT IMPORTS (Single Source of Truth)
# ═══════════════════════════════════════════════════════════════════════════════

from contracts import (
    Dimension,
    Verdict,
    SEAL,
    CONSTITUTIONAL_FLOORS,
    CANONICAL_TOOLS,
)
from contracts.parity import get_runtime_tools, runtime_supports_tool

# ═══════════════════════════════════════════════════════════════════════════════
# CONTROL PLANE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.control_plane")

GEOX_VERSION = "2.0.0-DIMENSION-NATIVE"
GEOX_SEAL = SEAL
GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")

mcp = FastMCP(
    name="GEOX",
    on_duplicate="error",
)

# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE GATING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DIMENSION_GATES = {
    "core": ["physics", "map"],
    "vps": ["prospect", "well", "earth3d", "map", "cross"],
    "full": ["prospect", "well", "section", "earth3d", "time4d", "physics", "map", "cross"]
}

ENABLED_DIMENSIONS = DIMENSION_GATES.get(GEOX_PROFILE, ["physics", "map"])

# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSION REGISTRIES BOOTSTRAP
# ═══════════════════════════════════════════════════════════════════════════════

sys.path.append(os.getcwd())

def bootstrap_registries():
    """Bootstrap dimension registries through control plane."""
    registry_map = {
        "prospect": "registries.prospect",
        "well": "registries.well",
        "section": "registries.section",
        "earth3d": "registries.earth3d",
        "time4d": "registries.time4d",
        "physics": "registries.physics",
        "map": "registries.map",
        "cross": "registries.cross"
    }

    for dim in ENABLED_DIMENSIONS:
        if dim in registry_map:
            module_name = registry_map[dim]
            try:
                import importlib
                module = importlib.import_module(module_name)
                func_name = f"register_{dim}_tools"
                if hasattr(module, func_name):
                    register_func = getattr(module, func_name)
                    register_func(mcp, profile=GEOX_PROFILE)
                    logger.info(f"Registered {dim.upper()} tools via control plane")
            except Exception as e:
                logger.error(f"Failed to bootstrap {dim} registry: {e}")

bootstrap_registries()

# ═══════════════════════════════════════════════════════════════════════════════
# CORE RESOURCES & PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("physics9://materials_atlas")
async def get_geox_materials() -> str:
    """Return the RATLAS materials atlas."""
    if os.path.exists("geox_atlas_99_materials.csv"):
        with open("geox_atlas_99_materials.csv", "r") as f:
            return f.read()
    return "Error: RATLAS csv missing."

@mcp.resource("geox://profile/status")
async def get_profile_status() -> dict:
    """Return current profile status."""
    return {
        "profile": GEOX_PROFILE,
        "enabled_dimensions": ENABLED_DIMENSIONS,
        "version": GEOX_VERSION,
        "seal": GEOX_SEAL,
        "available_tools": get_runtime_tools("fastmcp"),
    }

@mcp.prompt(name="SOVEREIGN_GEOX_SYSTEM_PROMPT")
def geox_system_prompt() -> str:
    """Return the sovereign system prompt."""
    return "You are GEOX, a sovereign subsurface governance coprocessor."

# ═══════════════════════════════════════════════════════════════════════════════
# REST BRIDGE & HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

def build_status_payload() -> dict:
    """Build the canonical status payload."""
    return {
        "status": "healthy",
        "service": "geox-control-plane",
        "version": GEOX_VERSION,
        "profile": GEOX_PROFILE,
        "enabled_dimensions": ENABLED_DIMENSIONS,
        "seal": GEOX_SEAL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "constitutional_floors": {f: "active" for f in CONSTITUTIONAL_FLOORS},
    }


async def health_handler(request):
    """Simple health check."""
    return PlainTextResponse("OK")


async def profile_handler(request):
    """Profile information endpoint."""
    return JSONResponse(
        {
            "profile": GEOX_PROFILE,
            "enabled_dimensions": ENABLED_DIMENSIONS,
            "version": GEOX_VERSION,
            "seal": GEOX_SEAL,
        }
    )


async def health_details_handler(request):
    """Detailed health check with constitutional status."""
    payload = build_status_payload()
    payload["ok"] = True
    payload["constitutional_floors"] = {f: "active" for f in CONSTITUTIONAL_FLOORS}
    return JSONResponse(payload)


def jsonrpc_result(response_id: Any, result: dict[str, Any]) -> JSONResponse:
    """Build JSON-RPC result response."""
    return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": result})


def jsonrpc_error(response_id: Any, code: int, message: str) -> JSONResponse:
    """Build JSON-RPC error response."""
    return JSONResponse(
        {"jsonrpc": "2.0", "id": response_id, "error": {"code": code, "message": message}}
    )


def wrap_legacy_content(payload: dict[str, Any]) -> dict[str, Any]:
    """Wrap legacy content for JSON-RPC."""
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, separators=(",", ":")),
            }
        ]
    }


def infer_geological_province(lat: float | None, lon: float | None) -> str:
    """Infer geological province from coordinates."""
    if lat is None or lon is None:
        return "Unknown"
    if 1.0 <= lat <= 8.0 and 108.0 <= lon <= 119.0:
        return "Brunei Shelf"
    return "Regional Basin Context"


async def run_legacy_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Run a legacy tool through the control plane."""
    if name == "geox_health":
        return {"success": True, "data": build_status_payload()}

    # Check if tool is supported by this runtime
    if not runtime_supports_tool("fastmcp", name):
        return {"success": False, "error": f"Tool {name} not supported by FastMCP runtime"}

    mapped_arguments = dict(arguments)
    if name == "geox_verify_geospatial" and {"lat", "lon"} <= mapped_arguments.keys():
        lat = float(mapped_arguments["lat"])
        lon = float(mapped_arguments["lon"])
        mapped_arguments = {"x": lon, "y": lat, "epsg": int(mapped_arguments.get("epsg", 4326))}
    else:
        lat = lon = None

    tool_result = await mcp.call_tool(name, mapped_arguments)
    data = getattr(tool_result, "structured_content", None)
    if not isinstance(data, dict):
        content = getattr(tool_result, "content", [])
        if content:
            data = json.loads(content[0].text)
        else:
            data = {}

    if name == "geox_verify_geospatial":
        data = {
            **data,
            "geological_province": data.get(
                "geological_province",
                infer_geological_province(lat, lon),
            ),
        }

    return {"success": True, "data": data}


async def legacy_mcp_handler(request):
    """Handle legacy MCP JSON-RPC requests."""
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return jsonrpc_error(None, -32700, "Parse error")

    response_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params", {})

    if method == "initialize":
        return jsonrpc_result(
            response_id,
            {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "GEOX", "version": GEOX_VERSION},
            },
        )

    if method == "tools/list":
        tools = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.parameters,
            }
            for tool in await mcp.list_tools()
        ]
        if not any(tool["name"] == "geox_health" for tool in tools):
            tools.append(
                {
                    "name": "geox_health",
                    "description": "Return GEOX server health and profile state.",
                    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
                }
            )
        return jsonrpc_result(response_id, {"tools": tools})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str):
            return jsonrpc_error(response_id, -32602, "Tool name is required")
        try:
            result_payload = await run_legacy_tool(name, arguments)
        except Exception as exc:
            return jsonrpc_error(response_id, -32603, str(exc))
        return jsonrpc_result(response_id, wrap_legacy_content(result_payload))

    return jsonrpc_error(response_id, -32601, f"Unsupported method: {method}")


async def legacy_mcp_head_handler(request):
    """Handle HEAD requests for MCP."""
    return PlainTextResponse("")


def create_app():
    """Create the Starlette application."""
    mcp_app = mcp.http_app(path="/mcp", transport="streamable-http")
    custom_routes = [
        Route("/health", health_handler, methods=["GET"]),
        Route("/health/details", health_details_handler, methods=["GET"]),
        Route("/profile", profile_handler, methods=["GET"]),
        Route("/mcp", legacy_mcp_handler, methods=["POST"]),
        Route("/mcp/", legacy_mcp_head_handler, methods=["HEAD"]),
    ]

    return Starlette(
        routes=[*custom_routes, Mount("/", mcp_app)],
        lifespan=getattr(mcp_app, "lifespan", None),
    )


def main() -> None:
    """Main entrypoint."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mode", choices=["mcp", "bridge"], default="bridge")
    args = parser.parse_args()

    if args.mode == "mcp":
        logger.info("Starting control plane in standalone MCP mode (stdio)")
        mcp.run()
    else:
        logger.info(f"Starting control plane in BRIDGE mode on {args.host}:{args.port}")
        app = create_app()
        uvicorn.run(app, host=args.host, port=args.port, proxy_headers=True, forwarded_allow_ips="*")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
