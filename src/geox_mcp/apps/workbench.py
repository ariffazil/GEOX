"""
GEOX MCP Apps Workbench — interactive map view for visual tools.

Architecture:
  - ui://geox/workbench-v1.html — interactive map + feature selection
  - ui://geox/workspace-v1.html — read-only workspace (registered in ui/resources.py)
  - Each tool declares its own ui.resourceUri in tools_manifest.yaml
  - Host reads ui.resourceUri from tools/list → opens sandboxed iframe →
    iframe receives tool-result via postMessage → renders accordingly

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP
from geox_mcp.surface_manifest import ui_tool_names

logger = logging.getLogger("geox.apps.workbench")

# ── Resource URIs ─────────────────────────────────────────────────────────────
WORKBENCH_URI = "ui://geox/workbench-v1.html"
WORKBENCH_URI_READABLE = "geox://apps/workbench-v1.html"
WORKBENCH_FILE = Path(__file__).resolve().parent.parent.parent.parent / "apps" / "workbench-v1.html"

# ── Tools that trigger the workbench View ──────────────────────────────────────
# When the LLM calls any of these tools, the Host reads ui.resourceUri from
# the tool's annotations (in tools/list) and opens the workbench iframe.
# Note: geox_map_context_scene uses the workspace (ui/resources.py), not workbench.
GEOX_UI_TOOLS: tuple[str, ...] = tuple(ui_tool_names())

# ── AppConfig per tool ────────────────────────────────────────────────────────
# Injected into tools/list metadata AND into tool call responses.
GEOX_UI_APPS: dict[str, AppConfig] = {
    name: AppConfig(
        resourceUri=WORKBENCH_URI,
        visibility=["model", "app"],
    )
    for name in GEOX_UI_TOOLS
}


def register_workbench(mcp: FastMCP) -> None:
    """Register the workbench HTML resource on the FastMCP server.

    The resource is served at ui://geox/workbench-v1.html with
    MIME type text/html;profile=mcp-app so MCP Apps hosts (ChatGPT,
    Claude, Copilot) render it as a sandboxed iframe.

    The workspace resource (ui://geox/workspace-v1.html) is registered
    separately in ui/resources.py.
    """
    if not WORKBENCH_FILE.exists():
        logger.warning(f"Workbench HTML not found at {WORKBENCH_FILE}. MCP App View will not be available.")
        return

    @mcp.resource(
        WORKBENCH_URI,
        description=(
            "GEOX Earth Workbench — interactive map, seismic, and basin visualization. "
            "Open this resource as a sandboxed iframe for the full GEOX GUI. "
            "Receives tool-input/tool-result notifications from the Host."
        ),
        mime_type="text/html;profile=mcp-app",
        app=AppConfig(
            prefers_border=False,
            csp=ResourceCSP(
                connect_domains=["geox.arif-fazil.com", "macrostrat.org"],
                resource_domains=[
                    "geox.arif-fazil.com",
                    "unpkg.com",  # MapLibre GL JS + CSS
                    "tile.openstreetmap.org",  # OSM raster tiles
                ],
            ),
        ),
    )
    async def geox_workbench() -> str:
        return WORKBENCH_FILE.read_text(encoding="utf-8")

    # Also register on readable URI for resources/read access (Fix HOLD-2026-07-11)
    @mcp.resource(
        WORKBENCH_URI_READABLE,
        description=(
            "GEOX Earth Workbench — readable variant for resources/read access. Same content as ui://geox/workbench-v1.html."
        ),
        mime_type="text/html;profile=mcp-app",
    )
    async def geox_workbench_readable() -> str:
        return WORKBENCH_FILE.read_text(encoding="utf-8")

    logger.info(f"MCP App View registered: {WORKBENCH_URI} + readable ({len(GEOX_UI_TOOLS)} tools bound)")
