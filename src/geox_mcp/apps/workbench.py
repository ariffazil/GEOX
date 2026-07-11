"""
GEOX MCP Apps Workbench — One fixed View for all visual tools.

Architecture:
  - One ui://geox/workbench-v1.html resource (fixed, no dynamic params)
  - All 6+ visual tools point to this single View via AppConfig(resource_uri=...)
  - Host calls any visual tool → tools/list metadata shows ui.resourceUri →
    Host opens sandboxed iframe → workbench receives tool-input notification →
    Workbench renders the appropriate panel based on which tool was called

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP

logger = logging.getLogger("geox.apps.workbench")

WORKBENCH_URI = "ui://geox/workbench-v1.html"
WORKBENCH_URI_READABLE = "geox://apps/workbench-v1.html"
WORKBENCH_FILE = Path(__file__).resolve().parent.parent.parent.parent / "apps" / "workbench-v1.html"

# ── Tools that trigger the workbench View ──────────────────────────────────────
# When the LLM calls any of these tools, the Host reads ui.resourceUri from
# the tool's annotations (in tools/list) and opens the workbench iframe.
GEOX_UI_TOOLS: tuple[str, ...] = (
    # Map & context
    "geox_map_context_scene",
    # Seismic volume & attribute
    "geox_volume_get_frame_tool",
    "geox_seismic_compute_attribute_tool",
    # Horizon interpretation
    "geox_horizon_contrast_surface",
    # Subsurface candidates
    "geox_subsurface_generate_candidates",
    # Prospect evaluation
    "geox_prospect_evaluate",
)

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
