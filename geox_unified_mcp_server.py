"""
Legacy Entrypoint Shim.
The actual FastMCP control plane server has moved to control_plane/fastmcp/server.py.
This shim ensures existing GitHub Actions / MCP ecosystem wiring doesn't break.
"""
from control_plane.fastmcp.server import main
if __name__ == "__main__":
    main()
