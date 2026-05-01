"""
GEOX Unified MCP Server — Sovereign 13 Kernel
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import os
import logging
import sys
import json
import uvicorn
import argparse
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from datetime import datetime, timezone
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Unified Server Configuration
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox.unified")

# [MANDATORY] FAIL-CLOSED AUTH
_geox_secret = os.getenv("GEOX_SECRET_TOKEN", "")
if not _geox_secret:
    _fallback = os.getenv("FASTMCP_INSPECT_TOKEN", "")
    if _fallback:
        GEOX_SECRET_TOKEN = _fallback
        logger.warning("F1 inspection bypass active — using FASTMCP_INSPECT_TOKEN")
    else:
        logger.critical("F1_AMANAH_BREACH: GEOX_SECRET_TOKEN is missing. Aborting startup to prevent fail-open exposure.")
        sys.exit(1)
else:
    GEOX_SECRET_TOKEN = _geox_secret

GEOX_VERSION = "v2026.05.01"
GEOX_SEAL = "DITEMPA BUKAN DIBERI"
GEOX_PROFILE = os.getenv("GEOX_PROFILE", "full")
GEOX_HOST = os.getenv("GEOX_HOST", os.getenv("HOST", "0.0.0.0"))
GEOX_PORT = int(os.getenv("GEOX_PORT", os.getenv("PORT", "8081")))

mcp = FastMCP(
    name="GEOX",
    version=GEOX_VERSION,
    instructions="""Canonical GEOX Registry & MCP App Control Plane (Sovereign 13).
    DITEMPA BUKAN DIBERI — One Sovereign Kernel.
    """,
)

# ═══════════════════════════════════════════════════════════════════════════════
# SOVEREIGN 13 BOOTSTRAP
# ═══════════════════════════════════════════════════════════════════════════════

sys.path.append(os.getcwd())

def bootstrap_registries():
    """Initializes the Sovereign 13 tool surface and alias bridge."""
    try:
        from contracts.tools.unified_13 import register_unified_tools
        from compatibility.legacy_aliases import LEGACY_ALIAS_MAP
        register_unified_tools(mcp, profile=GEOX_PROFILE)
        logger.info(f"Sovereign 13 tool surface: IGNITED (13 Tools, {len(LEGACY_ALIAS_MAP)} Aliases)")
    except Exception as e:
        logger.critical(f"Failed to bootstrap Sovereign 13 registry: {e}")
        sys.exit(1)

bootstrap_registries()

# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS HARDENING
# ═══════════════════════════════════════════════════════════════════════════════

def build_status_payload() -> dict:
    from compatibility.legacy_aliases import LEGACY_ALIAS_MAP
    return {
        "status": "ok",
        "service": "geox-mcp-kernel",
        "version": GEOX_VERSION,
        "contract_epoch": "2026-05-01",
        "canonical_tools": 13,
        "legacy_aliases": len(LEGACY_ALIAS_MAP),
        "auth_mode": "fail_closed",
        "profile": GEOX_PROFILE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seal": GEOX_SEAL
    }

async def health_handler(request):
    """Liveness check."""
    return JSONResponse({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

async def ready_handler(request):
    """Readiness check: Ensure registry is loaded."""
    return JSONResponse(build_status_payload())

async def status_handler(request):
    """Full contract status."""
    return JSONResponse(build_status_payload())

# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY BRIDGE & RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("geox://registry/apps")
async def list_geox_apps() -> list[dict]:
    """Return the list of dashboard-ready GEOX applications from manifests."""
    manifest_dir = "control_plane/fastmcp/manifests"
    apps = []
    if os.path.exists(manifest_dir):
        for filename in os.listdir(manifest_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(manifest_dir, filename), "r") as f:
                        apps.append(json.load(f))
                except Exception as e:
                    logger.error(f"Failed to load manifest {filename}: {e}")
    return apps

async def run_legacy_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool_result = await mcp.call_tool(name, arguments)
    return {"success": True, "data": tool_result.content[0].text if tool_result.content else {}}

async def legacy_mcp_handler(request):
    """Unified handler for MCP legacy/health probes and tool calls."""
    if request.method == "GET":
        return JSONResponse({
            "mcp": "GEOX",
            "kernel": "Sovereign 13",
            "version": GEOX_VERSION,
            "status": "active",
            "transport": "streamable-http",
            "note": "Use POST for JSON-RPC tool calls"
        })

    try:
        payload = await request.json()
    except:
        return JSONResponse({"error": "Parse error (empty or invalid JSON)"}, status_code=400)
    
    method = payload.get("method")
    params = payload.get("params", {})
    response_id = payload.get("id")

    if method == "tools/list":
        tools = [{"name": t.name, "description": t.description} for t in await mcp.list_tools()]
        return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": {"tools": tools}})
    
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        result = await run_legacy_tool(name, args)
        return JSONResponse({"jsonrpc": "2.0", "id": response_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}})

    return JSONResponse({"error": "Method not found"}, status_code=404)

# ═══════════════════════════════════════════════════════════════════════════════
# APP CREATION & ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

def create_app():
    mcp_app = mcp.http_app(path="/mcp/stream", transport="streamable-http")
    return Starlette(
        routes=[
            Route("/health", health_handler, methods=["GET"]),
            Route("/ready", ready_handler, methods=["GET"]),
            Route("/status", status_handler, methods=["GET"]),
            Route("/mcp", legacy_mcp_handler, methods=["GET", "POST"]),
            Mount("/", mcp_app)
        ],
        lifespan=getattr(mcp_app, "lifespan", None),
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=GEOX_HOST)
    parser.add_argument("--port", type=int, default=GEOX_PORT)
    args = parser.parse_args()
    
    app = create_app()
    logger.info(f"GEOX Sovereign 13 Kernel starting on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
