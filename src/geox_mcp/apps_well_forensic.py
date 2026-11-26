"""SEP-1865 MCP App registration for ui://geox/well-forensic-desk.html (FastMCP 4.1.4)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from geox.forensics.well_pda import geox_well_pda

APP_URI = "ui://geox/well-forensic-desk.html"
APP_MIME = "text/html;profile=mcp-app"
APP_HTML_PATH = Path(__file__).resolve().parents[2] / "ui-apps" / "well-forensic-desk" / "index.html"


def register_well_forensic_app(mcp: Any) -> None:
    """Register SEP-1865 single-file MCP App resource and {} entrypoint tool."""

    @mcp.resource(APP_URI, mime_type=APP_MIME, meta={"ui": {"prefersBorder": False}})
    def well_forensic_desk_resource() -> str:
        return APP_HTML_PATH.read_text(encoding="utf-8")

    @mcp.tool(
        name="geox_well_pda",
        meta={
            "ui": {"resourceUri": APP_URI},
            "com.google.antigravity/ui": {
                "entrypoints": [
                    {"type": "aux_pane", "title": "Well Forensic Desk"},
                    {"type": "global", "title": "GEOX Pre-Flight QC"},
                ]
            },
        },
    )
    def geox_well_pda_tool(mode: str = "all", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Subsurface Pre-Flight Auditor (accepts {} empty arguments for default dashboard)."""
        return geox_well_pda(mode=mode, payload=payload)
