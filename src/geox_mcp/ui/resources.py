from __future__ import annotations

import logging
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.apps import AppConfig, ResourceCSP

from geox_mcp.surface_manifest import (
    GRAVMAG_STUDIO_MIME,
    GRAVMAG_STUDIO_URI,
    WORKSPACE_MIME,
    WORKSPACE_URI,
)

logger = logging.getLogger("geox.ui.resources")

WORKSPACE_READABLE_URI = "geox://apps/workspace-v1.html"
WORKSPACE_FILE = Path(__file__).with_name("workspace_v1.html")

GRAVMAG_STUDIO_FILE = Path(__file__).with_name("static") / "gravmag_studio.html"


def register_workspace_resource(mcp: FastMCP) -> None:
    """Register the read-only GEOX workspace widget resource."""
    if not WORKSPACE_FILE.exists():
        logger.warning("Workspace HTML not found at %s", WORKSPACE_FILE)
        return

    html = WORKSPACE_FILE.read_text(encoding="utf-8")

    @mcp.resource(
        WORKSPACE_URI,
        description="GEOX Workspace v1 — read-only governed evidence viewer.",
        mime_type=WORKSPACE_MIME,
        app=AppConfig(
            prefers_border=True,
            csp=ResourceCSP(
                connect_domains=[],
                resource_domains=[],
            ),
        ),
    )
    async def geox_workspace_v1() -> str:
        return html

    @mcp.resource(
        WORKSPACE_READABLE_URI,
        description="Readable alias for GEOX Workspace v1.",
        mime_type=WORKSPACE_MIME,
    )
    async def geox_workspace_v1_readable() -> str:
        return html

    logger.info("Workspace resource registered: %s", WORKSPACE_URI)


def register_gravmag_studio_resource(mcp: FastMCP) -> None:
    """Register the GEOX GravMag Studio sandboxed iframe (Stage A — forward only).

    The iframe is a passive Canvas2D heatmap renderer. State is pushed by
    the host via SEP-1865 ``ui/notifications/tool-input`` or ``tool-result``
    postMessage envelopes.
    """
    if not GRAVMAG_STUDIO_FILE.exists():
        logger.warning("GravMag Studio HTML not found at %s", GRAVMAG_STUDIO_FILE)
        return

    html = GRAVMAG_STUDIO_FILE.read_text(encoding="utf-8")

    @mcp.resource(
        GRAVMAG_STUDIO_URI,
        description=(
            "GEOX GravMag Studio v0.1 — forward-only Canvas2D heatmap renderer. "
            "Hosted by geox_gravmag_studio_open."
        ),
        mime_type=GRAVMAG_STUDIO_MIME,
        app=AppConfig(
            prefers_border=True,
            csp=ResourceCSP(
                connect_domains=[],
                resource_domains=[],
            ),
        ),
    )
    async def geox_gravmag_studio_v1() -> str:
        return html

    logger.info("GravMag Studio resource registered: %s", GRAVMAG_STUDIO_URI)


def register_all_ui_resources(mcp: FastMCP) -> None:
    """Register every GEOX UI resource — workspace + GravMag Studio."""
    register_workspace_resource(mcp)
    register_gravmag_studio_resource(mcp)
