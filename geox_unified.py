import os
import logging
import sys
import argparse
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

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

async def health_handler(request):
    return JSONResponse({
        "status": "healthy",
        "service": "geox-unified",
        "version": GEOX_VERSION,
        "profile": GEOX_PROFILE,
        "dimensions": ENABLED_DIMENSIONS,
        "seal": GEOX_SEAL
    })

def create_app():
    # Build the MCP Starlette app for SSE/HTTP
    # Note: FastMCP.http_app is the standard way to get a Starlette app
    mcp_app = mcp.http_app(transport="sse") # Use SSE as default for web
    
    # Custom routes for health etc.
    custom_routes = [
        Route("/health", health_handler, methods=["GET"]),
        Route("/health/details", health_handler, methods=["GET"]), # Alias for details
    ]
    
    # Combine or wrap? Starlette allows mounting.
    main_app = Starlette(routes=custom_routes)
    main_app.mount("/mcp", mcp_app)
    # Also mount root to MCP app? Or to health?
    # Let's mount health at root too if nothing else matches
    
    return main_app

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
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
        uvicorn.run(app, host=args.host, port=args.port)
