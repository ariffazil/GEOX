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
# GEOX Unified Dimension-Native Server (v2.0.0)
# DITEMPA BUKAN DIBERI: Dimension-First Ontology
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

GEOX_VERSION = "2.0.0-DIMENSION-NATIVE"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
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
                    logger.info(f"Registered {dim.upper()} tools")
            except Exception as e:
                logger.error(f"Failed to bootstrap {dim} registry: {e}")

bootstrap_registries()

# ═══════════════════════════════════════════════════════════════════════════════
# CORE RESOURCES & PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("physics9://materials_atlas")
async def get_geox_materials() -> str:
    if os.path.exists("geox_atlas_99_materials.csv"):
        with open("geox_atlas_99_materials.csv", "r") as f:
            return f.read()
    return "Error: RATLAS csv missing."

@mcp.resource("geox://profile/status")
async def get_profile_status() -> dict:
    return {
        "profile": GEOX_PROFILE,
        "enabled_dimensions": ENABLED_DIMENSIONS,
        "version": GEOX_VERSION,
        "seal": GEOX_SEAL
    }

@mcp.prompt(name="SOVEREIGN_GEOX_SYSTEM_PROMPT")
def geox_system_prompt() -> str:
    return "You are GEOX, a sovereign subsurface governance coprocessor."

# ═══════════════════════════════════════════════════════════════════════════════
# REST BRIDGE & HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

def build_status_payload() -> dict:
    return {
        "status": "healthy",
        "service": "geox-dimension-native",
        "version": GEOX_VERSION,
        "profile": GEOX_PROFILE,
        "enabled_dimensions": ENABLED_DIMENSIONS,
        "seal": GEOX_SEAL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def health_handler(request):
    return PlainTextResponse("OK")


async def profile_handler(request):
    return JSONResponse(
        {
            "profile": GEOX_PROFILE,
            "enabled_dimensions": ENABLED_DIMENSIONS,
            "version": GEOX_VERSION,
            "seal": GEOX_SEAL,
        }
    )


async def health_details_handler(request):
    payload = build_status_payload()
    payload["ok"] = True
    payload["constitutional_floors"] = {
        "F1": "active",
        "F2": "active",
        "F4": "active",
        "F7": "active",
        "F9": "active",
        "F11": "active",
        "F13": "active",
    }
    return JSONResponse(payload)


def jsonrpc_result(response_id: Any, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": result})


def jsonrpc_error(response_id: Any, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": response_id, "error": {"code": code, "message": message}}
    )


def wrap_legacy_content(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, separators=(",", ":")),
            }
        ]
    }


def infer_geological_province(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "Unknown"
    if 1.0 <= lat <= 8.0 and 108.0 <= lon <= 119.0:
        return "Brunei Shelf"
    return "Regional Basin Context"


async def run_legacy_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "geox_health":
        return {"success": True, "data": build_status_payload()}

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
    return PlainTextResponse("")

def create_app():
    # Create MCP app with different path to avoid conflict with legacy handler
    mcp_app = mcp.http_app(path="/mcp/stream", transport="streamable-http")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--mode", choices=["mcp", "bridge"], default="bridge")
    args = parser.parse_args()

    if args.mode == "mcp":
        logger.info("Starting in standalone MCP mode (stdio)")
        mcp.run()
    else:
        logger.info(f"Starting in BRIDGE mode on {args.host}:{args.port}")
        app = create_app()
        uvicorn.run(app, host=args.host, port=args.port, proxy_headers=True, forwarded_allow_ips="*")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
