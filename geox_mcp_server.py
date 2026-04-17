#!/usr/bin/env python3
"""
GEOX MCP Server Entry Point
═════════════════════════════════════════════════════════════════════════════════

FastMCP Cloud deployment entrypoint.
Sets PYTHONPATH correctly for the geox package.
Adds /health endpoint and optional Bearer token auth.

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

app = mcp.streamable_http_app()

# Optional Bearer token auth — set GEOX_SECRET_TOKEN env var to enable
_secret = os.environ.get("GEOX_SECRET_TOKEN", "")


async def verify_token(request):
    if not _secret:
        return None
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {_secret}":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI, Request, HTTPException
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    port = int(os.environ.get("PORT", 8081))
    host = os.environ.get("HOST", "0.0.0.0")

    # Wrap FastMCP app with FastAPI for /health + auth middleware
    api = FastAPI(title="GEOX MCP Server")

    if _secret:

        @api.middleware("http")
        async def auth_middleware(request: Request, call_next):
            if request.url.path in ("/health", "/healthz", "/ready"):
                return await call_next(request)
            if request.url.path.startswith("/mcp"):
                auth = request.headers.get("authorization", "")
                if auth != f"Bearer {_secret}":
                    return JSONResponse(status_code=401, content={"error": "Unauthorized"})
            return await call_next(request)

    @api.get("/health")
    async def health():
        return {"status": "ok", "seal": "DITEMPA BUKAN DIBERI", "service": "geox-mcp"}

    @api.get("/ready")
    async def ready():
        return {"status": "ready"}

    @api.get("/")
    async def root():
        return {
            "service": "GEOX MCP Server",
            "version": "0.1.0",
            "seal": "DITEMPA BUKAN DIBERI",
            "endpoints": ["/health", "/ready", "/mcp"],
        }

    # Mount FastMCP on /mcp
    api.mount("/mcp", app)

    print(f"Starting GEOX MCP Server on {host}:{port}")
    print(f"PYTHONPATH={os.environ.get('PYTHONPATH')}")
    if _secret:
        print("Bearer token auth: ENABLED")

    uvicorn.run(
        api,
        host=host,
        port=port,
        log_level="info",
        proxy_headers=True,
    )
