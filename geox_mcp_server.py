#!/usr/bin/env python3
"""
GEOX MCP Server Entry Point
═════════════════════════════════════════════════════════════════════════════════

FastMCP 3.x deployment entrypoint.
Mounts FastMCP on /mcp with Starlette middleware for auth.
Adds /health, /ready, / routes.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GEOX_PKG_PATH = os.path.join(SCRIPT_DIR, "geox")
if os.path.isdir(GEOX_PKG_PATH):
    PYTHONPATH = SCRIPT_DIR
else:
    GEOX_ROOT = os.path.dirname(SCRIPT_DIR)
    if os.path.isdir(os.path.join(GEOX_ROOT, "geox")):
        PYTHONPATH = GEOX_ROOT
    else:
        PYTHONPATH = SCRIPT_DIR

os.environ["PYTHONPATH"] = PYTHONPATH
sys.path.insert(0, PYTHONPATH)

from geox.geox_mcp.fastmcp_server import mcp

# FastMCP 3.x — http_app() returns Starlette app with /mcp already mounted
app = mcp.http_app()

# Mandatory Bearer token auth — GEOX_SECRET_TOKEN must be set
_secret = os.environ.get("GEOX_SECRET_TOKEN", "")

# F1 Amanah / F13 Sovereign: Fail closed if secret is missing
if not _secret:
    import logging
    _logger = logging.getLogger("geox.mcp")
    _logger.critical("F1_HALT: GEOX_SECRET_TOKEN is not set — server refusing all MCP requests")


async def health(request):
    from starlette.responses import JSONResponse
    tool_count = 0
    try:
        from geox.geox_mcp.fastmcp_server import mcp
        tools = mcp.list_tools()
        tool_count = len(tools) if hasattr(tools, '__len__') else 0
    except Exception:
        pass
    return JSONResponse({"status": "ok", "seal": "DITEMPA BUKAN DIBERI", "service": "geox-mcp", "tool_count": tool_count})


async def ready(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ready"})


async def root(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "service": "GEOX MCP Server",
        "version": "0.1.0",
        "seal": "DITEMPA BUKAN DIBERI",
        "endpoints": ["/health", "/ready", "/mcp"],
    })


# Add routes to Starlette app (app is a Starlette instance from mcp.http_app())
app.add_route("/health", health, methods=["GET"])
app.add_route("/ready", ready, methods=["GET"])
app.add_route("/", root, methods=["GET"])


async def auth_dispatch(request, call_next):
    from starlette.responses import JSONResponse

    # Public routes — no auth required
    if request.url.path in ("/health", "/healthz", "/ready", "/"):
        return await call_next(request)

    # MCP endpoint — require Bearer token (mandatory, fail closed)
    if request.url.path.startswith("/mcp"):
        auth = request.headers.get("authorization", "")
        # F1: No secret configured → unconditional rejection
        if not _secret:
            return JSONResponse(
                status_code=503,
                content={"error": "F1_HALT: GEOX_SECRET_TOKEN not configured — MCP unavailable"},
            )
        if auth != f"Bearer {_secret}":
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    return await call_next(request)

from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(BaseHTTPMiddleware, dispatch=auth_dispatch)
print("Bearer token auth: ENABLED" if _secret else "Bearer token auth: F1_HALT — GEOX_SECRET_TOKEN not set")


from starlette.responses import PlainTextResponse, JSONResponse, FileResponse

_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


async def robots_txt(request):
    path = os.path.join(_STATIC, "robots.txt")
    if os.path.exists(path):
        return PlainTextResponse(open(path).read())
    return JSONResponse({"error": "not found"}, status_code=404)


async def llms_txt(request):
    path = os.path.join(_STATIC, "llms.txt")
    if os.path.exists(path):
        return PlainTextResponse(open(path).read())
    return JSONResponse({"error": "not found"}, status_code=404)


async def well_known_agent(request):
    path = os.path.join(_STATIC, ".well-known", "agent.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/json")
    return JSONResponse({"error": "not found"}, status_code=404)


async def well_known_arifos(request):
    path = os.path.join(_STATIC, ".well-known", "arifos.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/json")
    return JSONResponse({"error": "not found"}, status_code=404)


# Add discovery routes
app.add_route("/robots.txt", robots_txt, methods=["GET"])
app.add_route("/llms.txt", llms_txt, methods=["GET"])
app.add_route("/.well-known/agent.json", well_known_agent, methods=["GET"])
app.add_route("/.well-known/arifos.json", well_known_arifos, methods=["GET"])

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8081))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"Starting GEOX MCP Server on {host}:{port}")
    print(f"PYTHONPATH={os.environ.get('PYTHONPATH')}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        proxy_headers=True,
    )
