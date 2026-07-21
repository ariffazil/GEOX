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

import logging
from typing import Any

logger = logging.getLogger("geox.tools.mcp_apps_bridge")

try:
    from mcp_ui_server import UIMetadataKey, create_ui_resource

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
        "external_url": "https://geox.arif-fazil.com/cockpit/well_context_desk/",
        "html_fallback": "<h1>GEOX WellDesk</h1><p>1D well log viewer. Open externally.</p>",
    },
    "seismic_vision": {
        "uri": "ui://geox/seismic-vision",
        "title": "GEOX Seismic Vision",
        "description": "2D/3D seismic viewer with inline/xline, horizon picking, and attribute analysis",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",  # Cesium 3D — too heavy for rawHtml
        "external_url": "https://geox.arif-fazil.com/cockpit/seismic_viewer/",
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
        "external_url": "https://geox.arif-fazil.com/cockpit/basin_explorer/",
        "html_fallback": "<h1>GEOX Basin Explorer</h1><p>Interactive basin maps. Open in cockpit.</p>",
    },
    "earth_map": {
        "uri": "ui://geox/earth-map",
        "title": "GEOX Earth Map",
        "description": "Interactive geological map with layer discovery, scene planning, preview rendering, and governed export. 4-verb chain: list→plan→render→export.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",
        "external_url": "https://geox.arif-fazil.com/earth",
        "html_fallback": "<h1>GEOX Earth Map</h1><p>Interactive globe with Macrostrat geology, plate boundaries, and live earthquakes. Open at arif-fazil.com/earth.</p>",
    },
    "prospect_studio": {
        "uri": "ui://geox/prospect-studio",
        "title": "GEOX Prospect Studio",
        "description": "Prospect evaluation with structure, closures, risk, and volume analysis",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",
        "external_url": "https://geox.arif-fazil.com/apps/prospect-ui/",
        "html_fallback": "<h1>GEOX Prospect Studio</h1><p>Prospect evaluation dashboard. Open in cockpit.</p>",
    },
    "risk_console": {
        "uri": "ui://geox/risk-console",
        "title": "GEOX Risk Console",
        "description": "Decision log, evidence review, hold queue, and export for governed decisions",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "externalUrl",
        "external_url": "https://geox.arif-fazil.com/apps/judge-console/",
        "html_fallback": "<h1>GEOX Risk Console</h1><p>Claim/evidence review dashboard with 888_HOLD gating. Open in cockpit.</p>",
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
                "count": {"type": "integer", "description": "Total number of skills"},
            },
        },
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
            "interpreted": {
                "type": "object",
                "description": "INT-class: play fairways, risk register, petroleum system elements",
            },
            "contradictions": {"type": "array", "description": "Detected contradictions in basin model"},
        },
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
            "truth_class": {"type": "string", "enum": ["OBS", "DER", "INT", "SPEC"]},
        },
    },
    "geox_falsify": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["SURVIVED", "FALSIFIED", "INCONCLUSIVE"]},
            "filters_run": {"type": "integer"},
            "filters_passed": {"type": "integer"},
            "filters_failed": {"type": "integer"},
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "filter_id": {"type": "string"},
                        "filter_name": {"type": "string"},
                        "verdict": {"type": "string"},
                        "findings": {"type": "array"},
                    },
                },
            },
        },
    },
    "geox_prospect": {
        "type": "object",
        "properties": {
            "prospect_ref": {"type": "string"},
            "volumetrics": {"type": "object", "description": "P10/P50/P90 volume estimates"},
            "risk": {"type": "object", "description": "Geological risk factors (trap, reservoir, seal, charge, timing)"},
            "pos": {"type": "number", "description": "Probability of Success"},
            "evoi": {"type": "number", "description": "Expected Value of Information"},
        },
    },
    "geox_petrophysics": {
        "type": "object",
        "properties": {
            "vsh": {"type": "array", "description": "Volume of shale log"},
            "porosity": {"type": "array", "description": "Effective porosity log"},
            "sw": {"type": "array", "description": "Water saturation log"},
            "net_pay": {"type": "object", "description": "Net pay summary: gross, net, N:G ratio"},
        },
    },
    "geox_seismic_compute": {
        "type": "object",
        "properties": {
            "synthetic_trace": {"type": "array", "description": "Synthetic seismogram amplitudes"},
            "well_tie_correlation": {"type": "number", "description": "Cross-correlation coefficient"},
            "time_depth_table": {"type": "array", "description": "T-D pairs"},
            "attributes": {"type": "object", "description": "Computed seismic attributes"},
        },
    },
    "geox_list_apps": {
        "type": "object",
        "properties": {
            "apps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "app_id": {"type": "string"},
                        "uri": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
            "count": {"type": "integer"},
            "standard": {"type": "string", "const": "SEP-1865"},
        },
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
            },
            "openai/outputTemplate": uri,
            "openai/toolInvocation/invoking": f"Rendering {app['title']}...",
            "openai/toolInvocation/invoked": f"{app['title']} ready",
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
            "resource_type": app.get("resource_type", "rawHtml"),
            "mime_type": app["mime_type"],
        }
        # Include outputSchema if defined for this app's associated tool
        tool_name = _app_to_tool.get(app_id)
        if tool_name and tool_name in TOOL_OUTPUT_SCHEMAS:
            entry["outputSchema"] = TOOL_OUTPUT_SCHEMAS[tool_name]
        apps_list.append(entry)
    return apps_list


# Map app IDs to their primary tool names
# H1 P0: Extended to cover all registered apps + additional tools
_app_to_tool: dict[str, str] = {
    # Core visual tools (original 7)
    "well_desk": "geox_petrophysics",
    "seismic_vision": "geox_seismic_compute",
    "earth_volume": "geox_seismic_compute",
    "judge_console": "geox_falsify",
    "geoprobe": "geox_prospect",
    "basin_explorer": "geox_basin",
    "earth_map": "geox_map_layers_list",
    "prospect_studio": "geox_prospect",
    "risk_console": "geox_claim",
    # H1 P0: Map remaining apps to their primary tools
    "visual_hub": "geox_surface_status",
    "catalog": "geox_surface_status",
}

# H1 P0: Additional tool-to-app assignments for tools without their own app
# Each entry maps tool_name → app_id (the GEOX_APPS key to use for UI)
_tool_app_fallback: dict[str, str] = {
    # Well tools → WellDesk
    "geox_well_ingest": "well_desk",
    "geox_well_desk": "well_desk",
    "geox_well_desurvey": "well_desk",
    # Seismic tools → Seismic Vision
    "geox_seismic_ingest": "seismic_vision",
    "geox_seismic_interpret": "seismic_vision",
    # Basin tools → Basin Explorer
    "geox_basin_backstrip": "basin_explorer",
    "geox_sediment_mass_balance": "basin_explorer",
    "geox_thermal_maturity_history": "basin_explorer",
    "geox_deep_time_state": "earth_volume",
    # Sequence → Basin Explorer
    "geox_sequence": "basin_explorer",
    # Map chain → Earth Map
    "geox_map_scene_plan": "earth_map",
    "geox_map_render_preview": "earth_map",
    "geox_map_export_package": "earth_map",
    # Evidence → Judge Console
    "geox_evidence": "judge_console",
    "geox_contradiction_scan": "judge_console",
    "geox_claim_graph_evaluate": "risk_console",
    # Geomechanics & modeling → GeoProbe
    "geox_geomechanics": "geoprobe",
    "geox_subsurface_model": "earth_volume",
    "geox_gravmag_studio": "geoprobe",
    # H2: Workspace tool → Visual Hub
    "geox_workspace": "visual_hub",
    # Bridge → Prospect Studio
    "geox_to_wealth_bridge": "geoprobe",
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
        raise KeyError(f"Unknown GEOX app_id: '{app_id}' in GEOX_APPS registry")

    resource_type = app.get("resource_type", "rawHtml")

    try:
        if resource_type == "externalUrl":
            # Heavy apps (Cesium, MapLibre) — use external URL to avoid embedding 5-20MB
            resource = create_ui_resource(
                {
                    "uri": app["uri"],
                    "content": {"type": "externalUrl", "iframeUrl": app["external_url"]},
                    "encoding": "text",
                }
            )
        else:
            # Lightweight apps — embed HTML directly
            if html_content is None:
                html_content = app.get("html_fallback", f"<h1>{app['title']}</h1><p>{app['description']}</p>")
            resource = create_ui_resource(
                {
                    "uri": app["uri"],
                    "content": {"type": "rawHtml", "htmlString": html_content},
                    "encoding": "text",
                }
            )

        return {
            "type": "resource",
            "resource": {
                "uri": resource.resource.uri,
                "mimeType": resource.resource.mimeType,
                "text": resource.resource.text,
            },
        }
    except Exception as exc:
        logger.error("Failed to create UI resource for app '%s' (%s): %s", app_id, app.get("uri"), exc)
        raise ValueError(f"Failed to create UI resource for app '{app_id}' ({app.get('uri')}): {exc}") from exc


def register_mcp_apps_resources(mcp: Any) -> None:
    """Register all GEOX_APPS UI resources on the FastMCP server instance.

    Ensures resources/read for any ui://geox/* app URI returns valid HTML or external URL
    resource with text/html;profile=mcp-app MIME type.
    """
    try:
        from fastmcp.apps import AppConfig, ResourceCSP

        default_csp = ResourceCSP(
            connect_domains=["geox.arif-fazil.com", "macrostrat.org"],
            resource_domains=["geox.arif-fazil.com", "unpkg.com", "tile.openstreetmap.org", "cdn.jsdelivr.net"],
        )
    except ImportError:
        AppConfig = None
        default_csp = None

    for app_id, app in GEOX_APPS.items():
        uri = app["uri"]
        title = app["title"]
        desc = app["description"]
        mime_type = app.get("mime_type", "text/html;profile=mcp-app")
        ext_url = app.get("external_url", "")
        html_fallback = app.get(
            "html_fallback",
            f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{title}</title></head><body><h1>{title}</h1><p>{desc}</p><p><a href='{ext_url}'>Open {title}</a></p></body></html>",
        )

        def _make_handler(content: str):
            async def _handler() -> str:
                return content

            return _handler

        kwargs: dict[str, Any] = {
            "name": title,
            "description": f"{title} — {desc}",
            "mime_type": mime_type,
        }
        if AppConfig and default_csp:
            kwargs["app"] = AppConfig(prefers_border=True, csp=default_csp)

        try:
            mcp.resource(uri, **kwargs)(_make_handler(html_fallback))
        except Exception as e:
            logger.debug("Resource %s already registered or skipped: %s", uri, e)

    logger.info("Registered GEOX MCP Apps UI resources (%d total in registry)", len(GEOX_APPS))


def enrich_mcp_tools_with_apps(mcp: Any) -> None:
    """Enrich registered FastMCP tool definitions with _meta.ui and openai/outputTemplate.

    Ensures tools/list exposes _meta.ui.resourceUri for all GEOX MCP Apps across
    the main server and all mounted sub-servers.
    """
    providers = list(getattr(mcp, "providers", []))
    local_p = getattr(mcp, "_local_provider", None)
    if local_p and local_p not in providers:
        providers.insert(0, local_p)

    all_components: dict[str, Any] = {}
    for p in providers:
        comps = getattr(p, "_components", {})
        if isinstance(comps, dict):
            all_components.update(comps)
        sub_server = getattr(p, "server", None)
        if sub_server:
            sub_comps = getattr(getattr(sub_server, "_local_provider", None), "_components", {})
            if isinstance(sub_comps, dict):
                all_components.update(sub_comps)

    count = 0
    # First: enrich tools explicitly mapped in _app_to_tool
    for app_id, tool_name in _app_to_tool.items():
        key = f"tool:{tool_name}@"
        if key in all_components:
            comp = all_components[key]
            app_info = GEOX_APPS.get(app_id)
            if not app_info:
                continue
            uri = app_info["uri"]
            if not hasattr(comp, "meta") or comp.meta is None:
                comp.meta = {}
            comp.meta["ui"] = {
                "resourceUri": uri,
                "title": app_info["title"],
                "renderMode": app_info["render_mode"],
                "mimeType": app_info["mime_type"],
            }
            comp.meta["openai/outputTemplate"] = uri
            comp.meta["openai/toolInvocation/invoking"] = f"Rendering {app_info['title']}..."
            comp.meta["openai/toolInvocation/invoked"] = f"{app_info['title']} ready"
            count += 1

    # H1 P0: Enrich tools via fallback mapping (every tool gets a visual landing zone)
    for tool_name, app_id in _tool_app_fallback.items():
        key = f"tool:{tool_name}@"
        if key in all_components and key not in {f"tool:{t}@" for t in _app_to_tool.values()}:
            comp = all_components[key]
            app_info = GEOX_APPS.get(app_id)
            if not app_info:
                continue
            uri = app_info["uri"]
            if not hasattr(comp, "meta") or comp.meta is None:
                comp.meta = {}
            if "ui" not in comp.meta:  # Don't overwrite explicit mappings
                comp.meta["ui"] = {
                    "resourceUri": uri,
                    "title": app_info["title"],
                    "renderMode": app_info["render_mode"],
                    "mimeType": app_info["mime_type"],
                }
                comp.meta["openai/outputTemplate"] = uri
                comp.meta["openai/toolInvocation/invoking"] = f"Rendering {app_info['title']}..."
                comp.meta["openai/toolInvocation/invoked"] = f"{app_info['title']} ready"
                count += 1

    # Second: also scan all registered components across all providers/sub-servers
    for key, comp in all_components.items():
        if key.startswith("tool:"):
            ui_uri = None
            if hasattr(comp, "app") and comp.app and getattr(comp.app, "resource_uri", None):
                ui_uri = comp.app.resource_uri
            elif hasattr(comp, "meta") and isinstance(comp.meta, dict) and "ui" in comp.meta:
                ui_uri = comp.meta["ui"].get("resourceUri")
            elif hasattr(comp, "annotations") and comp.annotations and getattr(comp.annotations, "ui", None):
                ui_info = comp.annotations.ui
                if isinstance(ui_info, dict):
                    ui_uri = ui_info.get("resourceUri")
                elif hasattr(ui_info, "resourceUri"):
                    ui_uri = ui_info.resourceUri

            if ui_uri:
                if not hasattr(comp, "meta") or comp.meta is None:
                    comp.meta = {}
                if "ui" not in comp.meta:
                    comp.meta["ui"] = {"resourceUri": ui_uri}
                comp.meta["openai/outputTemplate"] = ui_uri
                comp.meta.setdefault("openai/toolInvocation/invoking", "Rendering interactive UI...")
                comp.meta.setdefault("openai/toolInvocation/invoked", "UI ready")

    logger.info("Enriched %d tools with MCP Apps UI metadata", count)
