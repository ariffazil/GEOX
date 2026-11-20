"""
GEOX Basin Panel — MCP App test server (FastMCP Python)

Usage:
  python3 server.py              # HTTP (port 3001, streamable HTTP)
  python3 server.py --stdio      # stdio (for basic-host or direct debugging)

DITEMPA BUKAN DIBERI
"""

import json, os, sys, asyncio
from pathlib import Path

from fastmcp import FastMCP

DIST_DIR = Path(__file__).parent / "dist"
BASIN_HTML = DIST_DIR / "basin-panel.html"

# ── Sample basin data (mirrors GEOX geox_basin profile output) ──
BASIN_SAMPLE = {
    "execution_status": "SUCCESS",
    "tool_class": "reason",
    "governance_status": "QUALIFY",
    "artifact_status": "DRAFT",
    "claim_tag": "HYPOTHESIS",
    "claim_state": "INTERPRETED",
    "uncertainty": "Moderate",
    "primary_artifact": {
        "mode": "overview",
        "basin_name": "Sabah Basin",
        "claim_strictness": "screen",
        "observed": {"tectonic_setting": "Passive margin", "basin_type": "Forearc"},
        "derived": {"area_km2": 45000, "sediment_thickness_m": 8000},
        "interpreted": {"hydrocarbon_kitchen": "Deep", "migration_pathway": "Vertical"},
        "play_fairways": [
            {"name": "Deepwater Clastics", "pos": "0.25", "volume": "2.5 Bboe"},
            {"name": "Carbonate Buildup", "pos": "0.15", "volume": "1.2 Bboe"},
            {"name": "Fractured Basement", "pos": "0.10", "volume": "0.8 Bboe"},
        ],
        "risk_register": [
            {
                "name": "Source rock presence",
                "severity": "medium",
                "description": "Uncertain lateral extent of Oligocene shales",
            },
            {
                "name": "Trap integrity",
                "severity": "high",
                "description": "Late-stage fault reactivation may breach seals",
            },
            {
                "name": "Reservoir quality",
                "severity": "low",
                "description": "Expected porosity >20% based on offset wells",
            },
        ],
        "contradictions": [
            "Heat flow measurements conflict with modelled maturation history"
        ],
        "missing_evidence": ["2D seismic coverage insufficient in northern portion"],
        "next_best_actions": [
            {
                "tool": "geox_basin_resolve",
                "reason": "Audit coordinates against known boundary",
            },
            {
                "tool": "geox_seismic_compute",
                "reason": "Run attribute analysis on available 2D lines",
            },
        ],
    },
    "provenance": {
        "tool_name": "geox_basin_profile",
        "tool_version": "v2026.07.06",
        "domain_law": "NATURAL_LAW",
        "geox_version": "v2026.07.06",
        "contract_epoch": "2026-07-06-GEOX-PHASE31-RSI-PIPELINE",
    },
    "apex": {
        "G": 0.72,
        "verdict": "SEAL",
        "gates": {
            "amanah": {"pass": True, "score": 1.0},
            "humility": {"pass": True, "score": 1.0},
            "signal": {"pass": True, "score": 0.8},
            "authority": {"pass": True, "score": 0.85},
            "sovereign": {"pass": True, "score": 1.0},
        },
    },
}


def create_server() -> FastMCP:
    """Create the FastMCP server with basin panel tool + resource."""

    server = FastMCP("GEOX Basin Panel Server")
    resource_uri = "ui://geox/basin-panel.html"

    # ── Register tool with _meta.ui.resourceUri ──
    @server.tool(
        name="geox_basin",
        description="Interactive earth intelligence panel for basin analysis. "
        "Returns structured basin data. "
        "Non-Apps clients receive JSON text; "
        "Apps clients also render an interactive map UI.",
        meta={"ui": {"resourceUri": resource_uri}},
    )
    def basin_tool(name: str = "Sabah Basin", mode: str = "profile") -> str:
        """Analyse basin and return structured data.
        Args:
            name: Basin name to analyse
            mode: Analysis mode (profile, overview)
        Returns:
            JSON string of basin profile data
        """
        return json.dumps(BASIN_SAMPLE, indent=2)

    # ── Register ui:// resource serving bundled HTML ──
    @server.resource(
        uri=resource_uri,
        name="GEOX Basin Panel",
        description="Interactive basin analysis UI with play fairways, "
        "risk register, contradictions, and governance metrics",
        mime_type="text/html;profile=mcp-app",
    )
    def basin_html() -> str:
        if not BASIN_HTML.exists():
            return (
                "<html><body><h1>Not built</h1>"
                "<p>Run <code>npm run build</code> first.</p></body></html>"
            )
        return BASIN_HTML.read_text("utf-8")

    return server


if __name__ == "__main__":
    server = create_server()

    if "--stdio" in sys.argv:
        print("Starting in stdio mode...", file=sys.stderr)
        server.run(transport="stdio")
    else:
        port = int(os.environ.get("PORT", "3001"))
        print(
            f"Starting MCP App server on http://localhost:{port}/mcp ...",
            file=sys.stderr,
        )
        server.run(transport="sse", host="0.0.0.0", port=port)
