"""
MCP Apps Bridge — SEP-1865 compliance for GEOX visual tools.

Adds _meta.ui.resourceUri to tool responses so any MCP Apps Host
(e.g., Claude Desktop, mcp-ui client, GEOX React GUI) can render
interactive UI alongside tool results.

Standard: https://modelcontextprotocol.io/extensions/apps/overview
SEP-1865: https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp
mcp-ui:   https://github.com/MCP-UI-Org/mcp-ui

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
from typing import Any

try:
    from mcp_ui_server import create_ui_resource, UIMetadataKey
    _MCP_UI_SERVER_AVAILABLE = True
except ImportError:
    _MCP_UI_SERVER_AVAILABLE = False

# ── GEOX MCP Apps Registry ───────────────────────────────────────────────────

GEOX_APPS: dict[str, dict[str, Any]] = {
    "well_desk": {
        "uri": "ui://geox/well-desk",
        "title": "GEOX WellDesk",
        "description": "1D well log viewer with petrophysics, formation tops, and physics9 integration",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",  # Streamlit app — served externally
        "external_url": "https://geox.arif-fazil.com/apps/well-desk/",
        "html_fallback": "<h1>GEOX WellDesk</h1><p>1D well log viewer. Open externally.</p>",
    },
    "seismic_vision": {
        "uri": "ui://geox/seismic-vision",
        "title": "GEOX Seismic Vision",
        "description": "2D/3D seismic viewer with inline/xline, horizon picking, and attribute analysis",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",  # Cesium 3D — too heavy for rawHtml
        "external_url": "https://geox.arif-fazil.com/gui/seismic_viewer/",
        "html_fallback": "<h1>GEOX Seismic Vision</h1><p>2D/3D seismic viewer. Open in cockpit.</p>",
    },
    "earth_volume": {
        "uri": "ui://geox/earth-volume",
        "title": "GEOX Earth Volume",
        "description": "3D subsurface volume renderer with Cesium globe integration",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",  # 3D volumes — too heavy
        "external_url": "https://geox.arif-fazil.com/apps/earth-volume/",
        "html_fallback": "<h1>GEOX Earth Volume</h1><p>3D subsurface renderer. Open in cockpit.</p>",
    },
    "judge_console": {
        "uri": "ui://geox/judge-console",
        "title": "GEOX Judge Console",
        "description": "888 Judge deliberation console with claim review and falsification tracking",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",  # Lightweight — fine as rawHtml
        "external_url": "https://geox.arif-fazil.com/apps/judge-console/",
    },
    "geoprobe": {
        "uri": "ui://geox/geoprobe",
        "title": "GEOX GeoProbe",
        "description": "Multi-dimensional prospect evaluation with risk, volumetrics, and economics",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",  # Heavy dashboards
        "external_url": "https://geox.arif-fazil.com/apps/prospect-ui/",
        "html_fallback": "<h1>GEOX GeoProbe</h1><p>Prospect evaluation dashboard. Open in cockpit.</p>",
    },
    "basin_explorer": {
        "uri": "ui://geox/basin-explorer",
        "title": "GEOX Basin Explorer",
        "description": "Interactive basin analysis with maps, cross-sections, and stratigraphic columns",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",  # MapLibre + D3 — heavy
        "external_url": "https://geox.arif-fazil.com/gui/basin_explorer/",
        "html_fallback": "<h1>GEOX Basin Explorer</h1><p>Interactive basin maps. Open in cockpit.</p>",
    },
    "visual_hub": {
        "uri": "ui://geox/visual-hub",
        "title": "GEOX Visual Output Hub",
        "description": "5-in-1 visual dashboard: WellDesk 1D + SeisVis 2D + CubeProbe 3D + TimeLapse 4D + PhysicCore",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",  # Hub — lightweight index
        "external_url": "https://geox.arif-fazil.com/apps/geox-mcp-visual/",
    },
    "catalog": {
        "uri": "ui://geox/catalog",
        "title": "GEOX Skills Catalog",
        "description": "Searchable registry of 44 earth intelligence skills across 11 domains",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",  # Lightweight
        "external_url": "https://geox.arif-fazil.com/apps/site/catalog.html",
        # SEP-2106: JSON Schema 2020-12 outputSchema for MCP-UI host discovery
        "outputSchema": {
            "type": "object",
            "properties": {
                "skills": {"type": "array", "description": "List of registered earth intelligence skills"},
                "domains": {"type": "array", "description": "List of skill domains"},
                "count": {"type": "integer", "description": "Total number of skills"}
            }
        }
    },
}

# ── Tool Output Schemas (SEP-2106) ──────────────────────────────────────────────

TOOL_OUTPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "geox_basin": {
        "type": "object",
        "properties": {
            "basin_name": {"type": "string", "description": "Basin name"},
            "observed": {"type": "object", "description": "OBS-class evidence: stratigraphy, heat flow, structural style"},
            "derived": {"type": "object", "description": "DER-class: subsidence curves, thermal maturity, mass balance"},
            "interpreted": {"type": "object", "description": "INT-class: play fairways, risk register, petroleum system elements"},
            "contradictions": {"type": "array", "description": "Detected contradictions in basin model"}
        }
    },
    "geox_claim": {
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "claim_text": {"type": "string"},
            "verdict": {"type": "string", "enum": ["SURVIVED", "FALSIFIED", "INCONCLUSIVE"]},
            "filters_run": {"type": "integer"},
            "filters_passed": {"type": "integer"},
            "filters_failed": {"type": "integer"},
            "truth_class": {"type": "string", "enum": ["OBS", "DER", "INT", "SPEC"]}
        }
    },
    "geox_falsify": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["SURVIVED", "FALSIFIED", "INCONCLUSIVE"]},
            "filters_run": {"type": "integer"},
            "filters_passed": {"type": "integer"},
            "filters_failed": {"type": "integer"},
            "results": {"type": "array", "items": {"type": "object", "properties": {
                "filter_id": {"type": "string"},
                "filter_name": {"type": "string"},
                "verdict": {"type": "string"},
                "findings": {"type": "array"}
            }}}
        }
    },
    "geox_prospect": {
        "type": "object",
        "properties": {
            "prospect_ref": {"type": "string"},
            "volumetrics": {"type": "object", "description": "P10/P50/P90 volume estimates"},
            "risk": {"type": "object", "description": "Geological risk factors (trap, reservoir, seal, charge, timing)"},
            "pos": {"type": "number", "description": "Probability of Success"},
            "evoi": {"type": "number", "description": "Expected Value of Information"}
        }
    },
    "geox_petrophysics": {
        "type": "object",
        "properties": {
            "vsh": {"type": "array", "description": "Volume of shale log"},
            "porosity": {"type": "array", "description": "Effective porosity log"},
            "sw": {"type": "array", "description": "Water saturation log"},
            "net_pay": {"type": "object", "description": "Net pay summary: gross, net, N:G ratio"}
        }
    },
    "geox_seismic_compute": {
        "type": "object",
        "properties": {
            "synthetic_trace": {"type": "array", "description": "Synthetic seismogram amplitudes"},
            "well_tie_correlation": {"type": "number", "description": "Cross-correlation coefficient"},
            "time_depth_table": {"type": "array", "description": "T-D pairs"},
            "attributes": {"type": "object", "description": "Computed seismic attributes"}
        }
    },
    "geox_list_apps": {
        "type": "object",
        "properties": {
            "apps": {"type": "array", "items": {"type": "object", "properties": {
                "app_id": {"type": "string"},
                "uri": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"}
            }}},
            "count": {"type": "integer"},
            "standard": {"type": "string", "const": "SEP-1865"}
        }
    },
}


def mcp_apps_resource(app_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a SEP-1865-compliant _meta.ui.resourceUri block for a GEOX app.

    Args:
        app_id: Key from GEOX_APPS registry (e.g. 'well_desk', 'seismic_vision')
        params: Optional query parameters to append to the resource URI

    Returns:
        Dict with _meta.ui structure per SEP-1865 / MCP Apps standard
    """
    app = GEOX_APPS.get(app_id)
    if not app:
        return {}

    uri = app["uri"]
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        uri = f"{uri}?{query}"

    return {
        "_meta": {
            "ui": {
                "resourceUri": uri,
                "title": app["title"],
                "renderMode": app["render_mode"],
                "mimeType": app["mime_type"],
                # SEP-973: Additional tool metadata
                "annotations": {
                    "audience": ["geoscientist", "interpreter"],
                    "priority": 0.8,
                },
            }
        }
    }


def enrich_response(response: dict[str, Any], app_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Add _meta.ui to an existing tool response dict.

    Usage in a tool handler:
        result = await do_computation(...)
        return enrich_response(result, 'well_desk', {'well_id': well_id})
    """
    meta = mcp_apps_resource(app_id, params)
    if meta:
        response.update(meta)
    return response


def list_apps() -> list[dict[str, Any]]:
    """Return all registered GEOX MCP Apps for discovery by hosts."""
    apps_list = []
    for app_id, app in GEOX_APPS.items():
        entry = {
            "app_id": app_id,
            "uri": app["uri"],
            "title": app["title"],
            "description": app["description"],
            "external_url": app["external_url"],
            "mime_type": app["mime_type"],
        }
        # Include outputSchema if defined for this app's associated tool
        tool_name = _app_to_tool.get(app_id)
        if tool_name and tool_name in TOOL_OUTPUT_SCHEMAS:
            entry["outputSchema"] = TOOL_OUTPUT_SCHEMAS[tool_name]
        apps_list.append(entry)
    return apps_list


# Map app IDs to their primary tool names
_app_to_tool: dict[str, str] = {
    "well_desk": "geox_petrophysics",
    "seismic_vision": "geox_seismic_compute",
    "earth_volume": "geox_seismic_compute",
    "judge_console": "geox_falsify",
    "geoprobe": "geox_prospect",
    "basin_explorer": "geox_basin",
}


def get_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Get the SEP-2106 outputSchema for a GEOX tool."""
    return TOOL_OUTPUT_SCHEMAS.get(tool_name)


def create_app_resource(app_id: str, html_content: str | None = None) -> dict[str, Any] | None:
    """Create a SEP-1865 MCP Apps UI resource using mcp-ui-server SDK.

    Args:
        app_id: Key from GEOX_APPS registry
        html_content: Optional HTML content for rawHtml apps. Ignored for externalUrl apps.

    Returns:
        UIResource-compatible dict for tools/call response content array, or None if SDK unavailable.
    """
    if not _MCP_UI_SERVER_AVAILABLE:
        return None

    app = GEOX_APPS.get(app_id)
    if not app:
        return None

    resource_type = app.get("resource_type", "rawHtml")

    try:
        if resource_type == "externalUrl":
            # Heavy apps (Cesium, MapLibre) — use external URL to avoid embedding 5-20MB
            resource = create_ui_resource({
                "uri": app["uri"],
                "content": {"type": "externalUrl", "externalUrl": app["external_url"]},
                "encoding": "text",
            })
        else:
            # Lightweight apps — embed HTML directly
            if html_content is None:
                html_content = app.get("html_fallback", f"<h1>{app['title']}</h1><p>{app['description']}</p>")
            resource = create_ui_resource({
                "uri": app["uri"],
                "content": {"type": "rawHtml", "htmlString": html_content},
                "encoding": "text",
            })

        return {
            "type": "resource",
            "resource": {
                "uri": resource.resource.uri,
                "mimeType": resource.resource.mimeType,
                "text": resource.resource.text,
            },
        }
    except Exception:
        return None
