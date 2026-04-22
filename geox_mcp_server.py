"""
GEOX MCP Server — Backward-Compatible Entry Point
DITEMPA BUKAN DIBERI

Canonical server: geox_mcp.server
"""

from __future__ import annotations

import os
import uvicorn

# Import the canonical server's MCP instance
from geox_mcp.server import mcp

def main():
    """Run the GEOX MCP server."""
    port = int(os.environ.get("PORT", 8081))
    app = mcp.streamable_http_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        proxy_headers=True,
    )

if __name__ == "__main__":
    main()