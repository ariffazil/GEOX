"""SEP-1865 MCP App registration for ui://geox/well-forensic-desk.html (FastMCP 4.1.4)."""
from __future__ import annotations

from importlib import resources as _resources
from pathlib import Path
from typing import Any

from geox.envelope import compact_envelope
from geox.forensics.well_audit import run_well_forensic_audit
from geox.forensics.well_pda import geox_well_pda

APP_URI = "ui://geox/well-forensic-desk.html"
APP_MIME = "text/html;profile=mcp-app"
_BASE = Path(__file__).resolve().parents[2] / "ui-apps" / "well-forensic-desk"
APP_DIST_HTML = _BASE / "dist" / "index.html"
APP_PACKAGED_HTML = Path(__file__).resolve().parent / "ui_apps" / "well_forensic_desk.html"
APP_HTML_PATH = APP_PACKAGED_HTML if APP_PACKAGED_HTML.exists() else APP_DIST_HTML


def read_well_forensic_html() -> str:
    """Read the bundled single-file HTML from wheel package data (works from any cwd)."""
    try:
        pkg_file = _resources.files("geox_mcp.ui_apps").joinpath("well_forensic_desk.html")
        return pkg_file.read_text(encoding="utf-8")
    except Exception:
        return APP_HTML_PATH.read_text(encoding="utf-8")


def register_well_forensic_app(mcp: Any) -> None:
    """Register SEP-1865 single-file MCP App resource and {} entrypoint tool."""

    @mcp.resource(APP_URI, mime_type=APP_MIME, meta={"ui": {"prefersBorder": False}})
    def well_forensic_desk_resource() -> str:
        return read_well_forensic_html()

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
    def geox_well_pda_tool(
        mode: str = "all",
        pack_dir: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Subsurface Pre-Flight Auditor (accepts {} empty arguments for default dashboard)."""
        m = mode.strip().lower()
        if m in ("forensic_audit", "forensic_slice") and pack_dir:
            return run_well_forensic_audit(pack_dir, mode=m)
        if m == "triage_decision":
            dec = (payload or {}).get("decision", "FLAG_REVIEW")
            well = (payload or {}).get("well", "UNKNOWN")
            return compact_envelope(
                tool="geox_well_pda",
                verdict="RECORDED",
                epistemic="OBS",
                summary=f"Recorded geologist triage decision {dec} for {well}.",
                data={"well": well, "decision": dec},
                artifact_uri=APP_URI,
            )
        return geox_well_pda(mode=mode, payload=payload)
