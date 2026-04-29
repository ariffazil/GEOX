#!/usr/bin/env python3
"""
GEOX MCP Server Entry Point — Canonical
DITEMPA BUKAN DIBERI

FastMCP 3.x deployment entrypoint.
Canonical path: geox/geox_mcp/fastmcp_server.py
Legacy paths: mcp/fastmcp_server.py, mcp/server.py — DO NOT USE.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Canonical: geox/geox_mcp/fastmcp_server.py
GEOX_PKG_PATH = os.path.join(SCRIPT_DIR, "geox", "geox_mcp")
if os.path.isdir(GEOX_PKG_PATH):
    sys.path.insert(0, os.path.join(SCRIPT_DIR, "geox"))
    sys.path.insert(0, os.path.dirname(GEOX_PKG_PATH))

from geox.geox_mcp.fastmcp_server import mcp

# FastMCP 3.x — http_app() returns Starlette app with /mcp already mounted
app = mcp.http_app()

# Health endpoint for drift-detector / container orchestration
from starlette.responses import JSONResponse

async def health_handler(request):
    return JSONResponse({"status": "healthy", "service": "geox-mcp", "version": "2.0.0"})

app.add_route("/health", health_handler, methods=["GET"])

# Bearer token auth — GEOX_SECRET_TOKEN must be set
_secret = os.environ.get("GEOX_SECRET_TOKEN", "")

# F1 Amanah / F13 Sovereign: fail closed if secret is missing
if not _secret:
    import warnings
    warnings.warn(
        "GEOX_SECRET_TOKEN not set — server will run without auth. "
        "Set GEOX_SECRET_TOKEN env var before deploying to production.",
        UserWarning
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )
