from typing import Any

from fastmcp import FastMCP


def register_ui_applets(mcp: FastMCP) -> None:
    @mcp.tool(name="geox_applet_crossplot")
    async def geox_applet_crossplot(well_id: str) -> dict[str, Any]:
        """
        Phase 1 MCP Apps proof-of-concept.
        Returns a sandboxed iframe dashboard for Vp/Rho/GR cross-plots using _meta.ui.resourceUri.
        """
        # The tool response conforms to SEP-1865:
        # It provides text for legacy clients, and _meta.ui for capable hosts.
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Cross-plot for well {well_id} generated. See the interactive panel."
                }
            ],
            "_meta": {
                "ui": {
                    "resourceUri": f"ui://geox/crossplot?well_id={well_id}",
                    "presentation": "panel"
                }
            }
        }
