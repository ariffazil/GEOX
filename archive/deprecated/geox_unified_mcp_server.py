"""
GEOX Unified MCP Server Shim
DITEMPA BUKAN DIBERI

Canonical server: geox_mcp.server
This shim maintains backward compatibility.
"""

from geox_mcp.server import mcp

def main():
    """Run the GEOX MCP server."""
    import uvicorn
    port = int(os.environ.get("PORT", 8081))
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=port)

__all__ = ["mcp", "main"]