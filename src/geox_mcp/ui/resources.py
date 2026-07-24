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


def _uri_registered(mcp: FastMCP, uri: str) -> bool:
    local = getattr(mcp, "_local_provider", None)
    comps = getattr(local, "_components", {}) if local else {}
    return f"resource:{uri}@" in comps


GEOX_RESOURCE_CSP = ResourceCSP(
    connect_domains=["geox.arif-fazil.com", "macrostrat.org"],
    resource_domains=[
        "geox.arif-fazil.com",
        "unpkg.com",
        "tile.openstreetmap.org",
        "cdn.jsdelivr.net",
        "cdn.plot.ly",
    ],
)


def register_workspace_resource(mcp: FastMCP) -> None:
    """Register the read-only GEOX workspace widget resource (idempotent)."""
    if not WORKSPACE_FILE.exists():
        logger.warning("Workspace HTML not found at %s", WORKSPACE_FILE)
        return

    if _uri_registered(mcp, WORKSPACE_URI):
        logger.debug("Workspace resource already registered: %s — skip", WORKSPACE_URI)
        return

    html = WORKSPACE_FILE.read_text(encoding="utf-8")

    @mcp.resource(
        WORKSPACE_URI,
        description="GEOX Workspace v1 — read-only governed evidence viewer.",
        mime_type=WORKSPACE_MIME,
        app=AppConfig(
            prefers_border=True,
            csp=GEOX_RESOURCE_CSP,
        ),
    )
    async def geox_workspace_v1() -> str:
        return html

    if not _uri_registered(mcp, WORKSPACE_READABLE_URI):
        # Plain text/html — NOT profile=mcp-app. MCPJam/OpenAI "Listed UI
        # Resources Valid" treats any mcp-app MIME as a UI resource and then
        # requires the ui:// scheme. This geox:// alias is a content mirror
        # only; the real MCP App is WORKSPACE_URI (ui://...).
        @mcp.resource(
            WORKSPACE_READABLE_URI,
            description="Readable alias for GEOX Workspace v1 (content mirror; MCP App is ui://geox/workspace-v1.html).",
            mime_type="text/html",
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

    if _uri_registered(mcp, GRAVMAG_STUDIO_URI):
        logger.debug("GravMag Studio already registered: %s — skip", GRAVMAG_STUDIO_URI)
        return

    html = GRAVMAG_STUDIO_FILE.read_text(encoding="utf-8")

    @mcp.resource(
        GRAVMAG_STUDIO_URI,
        description=("GEOX GravMag Studio v0.1 — forward-only Canvas2D heatmap renderer. Hosted by geox_gravmag_studio_open."),
        mime_type=GRAVMAG_STUDIO_MIME,
        app=AppConfig(
            prefers_border=True,
            csp=GEOX_RESOURCE_CSP,
        ),
    )
    async def geox_gravmag_studio_v1() -> str:
        return html

    logger.info("GravMag Studio resource registered: %s", GRAVMAG_STUDIO_URI)


def register_alias_resources(mcp: FastMCP) -> None:
    """Register exact alias URIs (without .html and ui://well/desk) for zero-friction client resolution."""
    aliases = [
        ("ui://geox/workspace-v1", WORKSPACE_FILE, WORKSPACE_MIME, "GEOX Workspace v1 alias (without .html extension)"),
        (
            "ui://geox/gravmag-studio",
            GRAVMAG_STUDIO_FILE,
            GRAVMAG_STUDIO_MIME,
            "GEOX GravMag Studio alias (without .html extension)",
        ),
        ("ui://well/desk", WORKSPACE_FILE, WORKSPACE_MIME, "Well Desk alias (mirrored from GEOX WellDesk)"),
    ]
    for uri, filepath, mime, desc in aliases:
        if filepath.exists() and not _uri_registered(mcp, uri):
            html = filepath.read_text(encoding="utf-8")

            def _make_handler(content: str):
                async def _alias_handler() -> str:
                    return content

                return _alias_handler

            mcp.resource(
                uri,
                description=desc,
                mime_type=mime,
                app=AppConfig(
                    prefers_border=True,
                    csp=GEOX_RESOURCE_CSP,
                ),
            )(_make_handler(html))


def register_all_ui_resources(mcp: FastMCP) -> None:
    """Register every GEOX UI resource — workspace + GravMag Studio + URI aliases."""
    register_workspace_resource(mcp)
    register_gravmag_studio_resource(mcp)
    register_alias_resources(mcp)
