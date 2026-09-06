"""
MCP Apps Bridge — SEP-1865 compliance for GEOX visual tools.

Adds _meta.ui.resourceUri to tool responses so any MCP Apps Host
(e.g., Claude Desktop, mcp-ui client, GEOX React GUI) can render
interactive UI alongside tool results.

Standard: https://modelcontextprotocol.io/extensions/apps/overview
SEP-1865: https://modelcontextprotocol.io/seps/1865-mcp-apps-interactive-user-interfaces-for-mcp
mcp-ui:   https://github.com/MCP-UI-Org/mcp-ui

PR1 (2026-07-23): resources/read serves real on-disk HTML (or mcp-ui externalUrl
wire format), never stub placeholders. html_path is authoritative for MCP hosts.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("geox.tools.mcp_apps_bridge")

try:
    from mcp_ui_server import UIMetadataKey, create_ui_resource

    _MCP_UI_SERVER_AVAILABLE = True
except ImportError:
    _MCP_UI_SERVER_AVAILABLE = False

# Repo root: src/geox_mcp/tools/mcp_apps_bridge.py → parents[3] = /root/GEOX
GEOX_ROOT = Path(__file__).resolve().parents[3]

# Minimum bytes for a host-usable rawHtml MCP App (stubs are ~65–310B)
_MIN_HOST_HTML_BYTES = 1024

# ── GEOX MCP Apps Registry ───────────────────────────────────────────────────
# html_path: repo-relative path to single-file (or self-contained) HTML for
# resources/read. Prefer apps/ and static/gui sources over "Open in cockpit" stubs.
# external_url: optional cockpit deep-link (metadata / progressive enhancement).
# resource_type: rawHtml (embed file) | externalUrl (mcp-ui iframeUrl only if no file).

GEOX_APPS: dict[str, dict[str, Any]] = {
    "well_desk": {
        "uri": "ui://geox/well-desk",
        "title": "GEOX WellDesk",
        "description": "1D well log viewer with petrophysics, formation tops, and physics9 integration",
        "widget_description": "Interactive well log viewer showing depth-based curves (GR, resistivity, density, sonic), formation tops, and petrophysical analysis. Ingest LAS files, run QC, compute porosity/saturation, and visualize results.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        # p0-viz: self-contained host bridge (ui/initialize + tool-result hydrate).
        # Full multi-file index.html needs sibling scripts — breaks in MCP iframe.
        "html_path": "apps/well-desk/p0-viz.html",
        "external_url": "https://geox.arif-fazil.com/apps/well-desk/",
    },
    "seismic_vision": {
        "uri": "ui://geox/seismic-vision",
        "title": "GEOX Seismic Vision",
        "description": "2D/3D seismic viewer with inline/xline, horizon picking, and attribute analysis",
        "widget_description": "Interactive seismic viewer for 2D sections and 3D volumes. Pick horizons, interpret faults, compute attributes (RMS, coherence, sweetness), and run well ties with synthetic seismograms.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "static/gui/seismic_viewer/index.html",
        "external_url": "https://geox.arif-fazil.com/cockpit/seismic_viewer/",
    },
    "earth_volume": {
        "uri": "ui://geox/earth-volume",
        "title": "GEOX Earth Volume",
        "description": "3D subsurface volume renderer with Cesium globe integration",
        "widget_description": "3D subsurface visualization with Cesium globe. Explore geological models, deep time paleogeography, GemPy implicit models, and subsurface property volumes.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/earth-volume/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/earth-volume/",
    },
    "judge_console": {
        "uri": "ui://geox/judge-console",
        "title": "GEOX Judge Console",
        "description": "888 Judge deliberation console with claim review and falsification tracking",
        "widget_description": "Constitutional judgment console for geological claims. Review evidence, track falsification results (K001-K007 filters), scan for contradictions, and render SEAL/HOLD/VOID verdicts.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/judge-console/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/judge-console/",
    },
    "geoprobe": {
        "uri": "ui://geox/geoprobe",
        "title": "GEOX GeoProbe",
        "description": "Multi-dimensional prospect evaluation with risk, volumetrics, and economics",
        "widget_description": "Prospect evaluation dashboard. Assess geological risk (trap, reservoir, seal, charge, timing), compute P10/P50/P90 volumetrics, estimate probability of success, and bridge to WEALTH for economic analysis.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/prospect-ui/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/prospect-ui/",
    },
    "basin_explorer": {
        "uri": "ui://geox/basin-explorer",
        "title": "GEOX Basin Explorer",
        "description": "Interactive basin analysis with maps, cross-sections, and stratigraphic columns",
        "widget_description": "Basin analysis dashboard. Explore stratigraphy, subsidence history, thermal maturity, sediment mass balance, and petroleum systems. Includes backstripping, sequence stratigraphy, and deep-time reconstructions.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "static/gui/basin_explorer/index.html",
        "external_url": "https://geox.arif-fazil.com/cockpit/basin_explorer/",
    },
    "earth_map": {
        "uri": "ui://geox/earth-map",
        "title": "GEOX Earth Map",
        "description": "Interactive geological map with layer discovery, scene planning, preview rendering, and governed export. 4-verb chain: list→plan→render→export.",
        "widget_description": "Interactive geological map. Discover map layers by bounding box, compose scenes, preview rendered maps, and export governed map packages with provenance. Supports coordinate transforms and spatial indexing.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/workbench-v1.html",
        "external_url": "https://geox.arif-fazil.com/earth",
    },
    "prospect_studio": {
        "uri": "ui://geox/prospect-studio",
        "title": "GEOX Prospect Studio",
        "description": "Prospect evaluation with structure, closures, risk, and volume analysis",
        "widget_description": "Prospect evaluation workspace. Define structural closures, assess trap integrity, compute volumetrics with uncertainty (P10/P50/P90), and evaluate risk factors for exploration decision-making.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/prospect-ui/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/prospect-ui/",
    },
    "risk_console": {
        "uri": "ui://geox/risk-console",
        "title": "GEOX Risk Console",
        "description": "Decision log, evidence review, hold queue, and export for governed decisions",
        "widget_description": "Risk and evidence console. Review claim evidence, track HOLD queues, scan for contradictions across geological claims, and prepare governed decision packages with audit trails.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/judge-console/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/judge-console/",
    },
    "visual_hub": {
        "uri": "ui://geox/visual-hub",
        "title": "GEOX Visual Output Hub",
        "description": "5-in-1 visual dashboard: WellDesk 1D + SeisVis 2D + CubeProbe 3D + TimeLapse 4D + PhysicCore",
        "widget_description": "Unified visualization dashboard combining well logs, seismic sections, 3D volumes, deep-time views, and petrophysical core analysis in a single interactive workspace.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/geox-mcp-visual/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/geox-mcp-visual/",
    },
    "gravmag_studio": {
        "uri": "ui://geox/gravmag-studio",
        "title": "GEOX GravMag Studio",
        "description": "Gravity/magnetics studio — preview heatmaps and field interpretation",
        "widget_description": "Gravity and magnetics interpretation studio. Visualize potential field data, forward-model subsurface bodies, and interpret basin structure from gravity/magnetic anomalies.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "src/geox_mcp/ui/static/gravmag_studio.html",
        "external_url": "https://geox.arif-fazil.com/apps/geox-mcp-visual/",
    },
    "workspace_v1": {
        "uri": "ui://geox/workspace-v1",
        "title": "GEOX Workspace",
        "description": "Persistent basin/play/well workspace context viewer",
        "widget_description": "Persistent geological workspace. View and manage current basin, play, well, and prospect context across tools. Maintains state so multi-step analyses stay coherent.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/workbench-v1.html",
        "external_url": "https://geox.arif-fazil.com/apps/workbench-v1.html",
    },
    "workbench_v1": {
        "uri": "ui://geox/workbench-v1",
        "title": "GEOX Workbench",
        "description": "Map/workbench shell for earth map tools",
        "widget_description": "General-purpose earth intelligence workbench. Render geological maps, select features to inspect properties, view provenance and epistemic labels, and interact with GEOX tool results visually.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/workbench-v1.html",
        "external_url": "https://geox.arif-fazil.com/apps/workbench-v1.html",
    },
    "prospect_ui": {
        "uri": "ui://geox/prospect-ui",
        "title": "GEOX Prospect UI",
        "description": "Prospect evaluation UI (alias of Prospect Studio shell)",
        "widget_description": "Prospect evaluation interface. Quick-access view for prospect screening, risk assessment, and volumetric calculations with uncertainty quantification.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/prospect-ui/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/prospect-ui/",
    },
    "analog_digitizer": {
        "uri": "ui://geox/analog-digitizer",
        "title": "GEOX Analog Digitizer",
        "description": "Dark-data well log curve extraction — manual point-picking with LAS export",
        "widget_description": "Digitize legacy paper well logs. Manually pick curve points from scanned log images and export as standard LAS files for use in modern petrophysical analysis.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/analog-digitizer/index.html",
        "external_url": "https://geox.arif-fazil.com/apps/analog-digitizer/",
    },
    "well_witness": {
        "uri": "ui://geox/well-witness",
        "title": "GEOX Well Witness",
        "description": "Consolidated well analysis pipeline: ingest → petrophysics → interactive view with provenance chain",
        "widget_description": "End-to-end well analysis pipeline. Ingest LAS files, run petrophysical computations (Vsh, porosity, Sw, net pay), QC the results, and visualize everything with full provenance tracking.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/well-witness.html",
        "external_url": "https://geox.arif-fazil.com/apps/well-witness.html",
    },
    "catalog": {
        "uri": "ui://geox/catalog",
        "title": "GEOX Skills Catalog",
        "description": "Searchable registry of 44 earth intelligence skills across 11 domains",
        "widget_description": "Searchable catalog of GEOX earth intelligence capabilities. Browse 33 tools across well, seismic, basin, map, prospect, and governance domains. Discover available analyses and their input/output schemas.",
        "render_mode": "panel",
        "mime_type": "text/html;profile=mcp-app",
        "resource_type": "rawHtml",
        "html_path": "apps/site/catalog.html",
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


def resolve_html_path(app: dict[str, Any]) -> Path | None:
    """Resolve on-disk HTML for an app entry. Returns None if missing."""
    rel = app.get("html_path")
    if not rel:
        return None
    path = GEOX_ROOT / rel
    return path if path.is_file() else None


def load_app_html(app_id: str, *, min_bytes: int = _MIN_HOST_HTML_BYTES) -> str:
    """Load host-usable HTML for an app. Raises if no real content available.

    Preference order:
      1. html_path on disk (rawHtml)
      2. mcp-ui externalUrl resource text (only if resource_type=externalUrl)
      3. Fail loud — never return a stub <h1> placeholder
    """
    app = GEOX_APPS.get(app_id)
    if not app:
        raise KeyError(f"Unknown GEOX app_id: '{app_id}'")

    path = resolve_html_path(app)
    if path is not None:
        html = path.read_text(encoding="utf-8")
        if len(html) < min_bytes:
            raise ValueError(f"App '{app_id}' HTML at {path} is too small ({len(html)}B < {min_bytes}B) — refuse stub")
        return html

    # No local file: only acceptable if explicitly externalUrl with cockpit URL
    if app.get("resource_type") == "externalUrl" and app.get("external_url"):
        # mcp-ui hosts that understand externalUrl get iframeUrl via create_app_resource.
        # For resources/read (string body), emit a minimal self-contained launcher that
        # still exceeds stub quality: full HTML document with immediate redirect + link.
        url = app["external_url"]
        title = app["title"]
        return (
            "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta http-equiv='refresh' content='0;url={url}'>"
            f"<title>{title}</title>"
            f"<style>body{{font-family:system-ui;background:#0a0a0f;color:#e8e8f0;"
            f"display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}"
            f"a{{color:#00d4aa}}</style></head><body>"
            f"<p>{title} — opening external cockpit. "
            f"<a href='{url}' target='_blank' rel='noopener'>Open manually</a></p>"
            f"<script>try{{window.top.location.href={url!r}}}catch(e){{"
            f"window.location.href={url!r}}}</script>"
            f"</body></html>"
        )

    raise FileNotFoundError(f"App '{app_id}' has no html_path file under {GEOX_ROOT} and is not externalUrl")


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
    # ── H1 P0.1: 25 additional outputSchema definitions ─────────────────────
    # Well family
    "geox_well_ingest": {
        "type": "object",
        "properties": {
            "well_id": {"type": "string", "description": "Canonical well identifier"},
            "curves_loaded": {"type": "array", "items": {"type": "string"}, "description": "Loaded log curve mnemonics"},
            "depth_range_m": {"type": "object", "description": "{top, base} depth range in metres"},
            "format": {"type": "string", "description": "Source format (LAS, DLIS, SEG-Y)"},
            "qc_flags": {"type": "array", "description": "Quality control findings"},
        },
    },
    "geox_well_desk": {
        "type": "object",
        "properties": {
            "well_id": {"type": "string"},
            "curves": {"type": "object", "description": "Rendered curve data by depth"},
            "tops": {"type": "object", "description": "Formation tops {name: depth_md}"},
            "panel_image": {"type": "string", "description": "Base64-encoded well panel image"},
            "interpretation_notes": {"type": "array", "description": "Interpretation annotations"},
        },
    },
    "geox_well_qc": {
        "type": "object",
        "properties": {
            "artifact_ref": {"type": "string"},
            "qc_mode": {"type": "string"},
            "checks": {"type": "array", "items": {"type": "object"}, "description": "QC check results"},
            "pass_count": {"type": "integer"},
            "fail_count": {"type": "integer"},
            "warn_count": {"type": "integer"},
        },
    },
    "geox_lem_predict": {
        "type": "object",
        "properties": {
            "target_depth_m": {"type": "number"},
            "predicted_properties": {"type": "object", "description": "Predicted rock properties (porosity, Sw, lithology)"},
            "method": {"type": "string", "description": "Physics-prior or ML mode used"},
            "basin_context": {"type": "string"},
        },
    },
    # Seismic family
    "geox_seismic_ingest": {
        "type": "object",
        "properties": {
            "volume_ref": {"type": "string", "description": "Canonical volume identifier"},
            "format": {"type": "string", "description": "Source format (SEG-Y, ZGY, VDS)"},
            "headers": {"type": "object", "description": "Binary + textual header summary"},
            "geometry": {
                "type": "object",
                "description": "{n_inlines, n_xlines, n_samples, sample_rate_ms, inline_range, xline_range}",
            },
            "qc_flags": {"type": "array", "description": "Ingest QC findings"},
        },
    },
    "geox_seismic_interpret": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "description": "Interpretation mode (horizon_contrast, fault_sticks, volume_frame, etc.)"},
            "horizons": {"type": "array", "description": "Picked horizon geometries"},
            "faults": {"type": "array", "description": "Picked fault geometries"},
            "gates": {
                "type": "object",
                "description": "Physics gate results {horizon, fault, structure, thermal} with PASS|WARN|KILL|UNMEASURED",
            },
            "receipt_hash": {"type": "string", "description": "Content hash of interpretation artifact"},
            "candidates": {"type": "integer", "description": "Number of competing interpretation candidates"},
        },
    },
    # Basin family
    "geox_basin_backstrip": {
        "type": "object",
        "properties": {
            "well_ref": {"type": "string"},
            "tectonic_subsidence": {"type": "array", "description": "Tectonic subsidence vs time"},
            "total_subsidence": {"type": "array", "description": "Total subsidence vs time"},
            "reconstructions": {"type": "object", "description": "Per-model reconstruction results"},
            "uncertainty_realizations": {"type": "integer"},
        },
    },
    "geox_sediment_mass_balance": {
        "type": "object",
        "properties": {
            "basin_name": {"type": "string"},
            "source_eroded_km3": {"type": "number"},
            "preserved_km3": {"type": "number"},
            "bypassed_km3": {"type": "number"},
            "dissolved_km3": {"type": "number"},
            "routing_efficiency": {"type": "number"},
            "mass_closure_pct": {"type": "number", "description": "Percent mass balance closure"},
        },
    },
    "geox_thermal_maturity_history": {
        "type": "object",
        "properties": {
            "well_ref": {"type": "string"},
            "vitrinite_reflectance": {"type": "array", "description": "EasyRo vs depth"},
            "tti": {"type": "array", "description": "Time-Temperature Index vs depth"},
            "oil_window": {"type": "object", "description": "{top_m, base_m} for oil generation window"},
            "gas_window": {"type": "object", "description": "{top_m, base_m} for gas generation window"},
        },
    },
    "geox_sequence": {
        "type": "object",
        "properties": {
            "mode": {"type": "string"},
            "correlation_panels": {"type": "array", "description": "Multi-well correlation panels"},
            "sequence_boundaries": {"type": "array", "description": "Identified sequence boundaries"},
            "systems_tracts": {"type": "object", "description": "LST/TST/HST assignments"},
            "biostratigraphic_markers": {"type": "array"},
        },
    },
    # Map family
    "geox_map_layers_list": {
        "type": "object",
        "properties": {
            "layers": {"type": "array", "items": {"type": "object"}, "description": "Available map layers with spatial extents"},
            "bbox": {"type": "array", "description": "Query bounding box [min_lon, min_lat, max_lon, max_lat]"},
            "crs": {"type": "string", "description": "Coordinate reference system"},
        },
    },
    "geox_map_scene_plan": {
        "type": "object",
        "properties": {
            "scene_id": {"type": "string"},
            "layers": {"type": "array", "items": {"type": "object"}, "description": "Composed layer stack"},
            "bbox": {"type": "array"},
            "style_profile": {"type": "string"},
            "annotations": {"type": "array"},
        },
    },
    "geox_map_render_preview": {
        "type": "object",
        "properties": {
            "scene_id": {"type": "string"},
            "preview_url": {"type": "string", "description": "Rendered preview image URL"},
            "width_px": {"type": "integer"},
            "height_px": {"type": "integer"},
            "format": {"type": "string"},
        },
    },
    "geox_map_export_package": {
        "type": "object",
        "properties": {
            "scene_plan_id": {"type": "string"},
            "export_formats": {"type": "array", "items": {"type": "string"}},
            "package_path": {"type": "string"},
            "provenance_included": {"type": "boolean"},
            "content_hash": {"type": "string"},
        },
    },
    # Governance / evidence family
    "geox_evidence": {
        "type": "object",
        "properties": {
            "evidence_id": {"type": "string"},
            "claim_id": {"type": "string"},
            "epistemic_label": {"type": "string", "description": "OBS / DER / INT / SPEC"},
            "evidence_type": {"type": "string", "description": "supporting / contradicting / missing"},
            "source_citation": {"type": "object"},
            "forbidden_uses": {"type": "array"},
        },
    },
    "geox_contradiction_scan": {
        "type": "object",
        "properties": {
            "claim_text": {"type": "string"},
            "contradictions": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Detected contradictions with types and severity",
            },
            "overall_verdict": {"type": "string", "description": "CLEAN / FLAGGED / FATAL"},
            "severity_counts": {"type": "object", "description": "{FATAL, HIGH, MEDIUM, LOW} counts"},
        },
    },
    "geox_claim_graph_evaluate": {
        "type": "object",
        "properties": {
            "claims": {"type": "array", "items": {"type": "object"}},
            "edges": {"type": "array", "items": {"type": "object"}},
            "propagated_verdicts": {"type": "object", "description": "Per-claim propagated verdicts"},
            "cascade_failures": {"type": "array", "description": "Claims that failed due to dependency failure"},
        },
    },
    # Earth / geophysics family
    "geox_deep_time_state": {
        "type": "object",
        "properties": {
            "age_ma": {"type": "number", "description": "Target age in millions of years"},
            "paleogeography": {"type": "object", "description": "Plate positions, coastlines, topography"},
            "climate_state": {"type": "object", "description": "CO2, temperature, sea level, ice volume"},
            "ocean_chemistry": {"type": "object", "description": "pH, oxygenation, carbonate saturation"},
            "biosphere": {"type": "object", "description": "Key fossils, extinction events, diversity"},
        },
    },
    "geox_geomechanics": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "description": "derive_moduli / blockspace / coord_transform"},
            "stress_polygon_vertices": {
                "type": "object",
                "description": "A(hydrostatic), B(normal), C(strike-slip), D(reverse) limits",
            },
            "sv_mpa": {"type": "number", "description": "Vertical stress (MPa)"},
            "friction_coefficient": {"type": "number"},
            "moduli": {"type": "object", "description": "K, G, E, nu, AI derived from physics state"},
        },
    },
    "geox_gravmag_studio": {
        "type": "object",
        "properties": {
            "survey_type": {"type": "string", "description": "gravity / magnetic"},
            "forward_model": {"type": "object", "description": "Forward modelled response at survey points"},
            "prism_bodies": {"type": "array", "description": "Subsurface prism body definitions"},
            "fit_residual_rms": {"type": "number"},
        },
    },
    "geox_subsurface_model": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "description": "joint_inversion / gravity_forward / magnetic_forward / MT_forward"},
            "inverted_model": {"type": "object", "description": "Inverted property volumes"},
            "forward_response": {"type": "object", "description": "Computed forward response"},
            "iterations": {"type": "integer"},
            "misfit": {"type": "number"},
        },
    },
    "geox_to_wealth_bridge": {
        "type": "object",
        "properties": {
            "prospect_ref": {"type": "string"},
            "npv_usd": {"type": "number"},
            "irr": {"type": "number"},
            "breakeven_usd": {"type": "number"},
            "score_kernel_input": {"type": "object", "description": "WEALTH score_kernel formatted input"},
            "epistemic_source": {"type": "string"},
        },
    },
    # Visual family
    "geox_visual_understand": {
        "type": "object",
        "properties": {
            "image_path": {"type": "string"},
            "mode": {"type": "string"},
            "patterns_detected": {"type": "array", "items": {"type": "object"}, "description": "Detected geological patterns"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    },
    "geox_visual_generate_hypotheses": {
        "type": "object",
        "properties": {
            "hypotheses": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Generated competing geological hypotheses",
            },
            "discontinuity_gap": {"type": "object", "description": "The seismic discontinuity gap being bridged"},
            "count": {"type": "integer", "description": "Number of hypotheses generated"},
        },
    },
    # Meta / status family
    "geox_surface_status": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "healthy / degraded / down"},
            "surface_version": {"type": "string"},
            "public_count": {"type": "integer"},
            "public_count_target": {"type": "integer"},
            "canonical_tools": {"type": "array", "items": {"type": "string"}},
            "verdict": {"type": "string"},
        },
    },
    "geox_workspace": {
        "type": "object",
        "properties": {
            "mode": {"type": "string"},
            "basin": {"type": "string"},
            "play": {"type": "string"},
            "well_id": {"type": "string"},
            "prospect_ref": {"type": "string"},
            "history": {"type": "array", "description": "Workspace state history"},
        },
    },
    "geox_well_view": {
        "type": "object",
        "properties": {
            "well_id": {"type": "string", "description": "Well identifier"},
            "source_uri": {"type": "string", "description": "LAS file path"},
            "curves": {
                "type": "object",
                "description": "Curve data: {GR: [...], RES: [...], DT: [...], RHOB: [...], NPHI: [...]}",
            },
            "depths": {"type": "array", "items": {"type": "number"}, "description": "Depth array (metres)"},
            "meta": {"type": "object", "description": "Well metadata: start_md, stop_md, null_value, curves_loaded"},
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

    meta: dict[str, Any] = {
        "_meta": {
            "ui": {
                "resourceUri": uri,
                "title": app["title"],
                "renderMode": app["render_mode"],
                "mimeType": app["mime_type"],
                "domain": "https://geox.arif-fazil.com",
                "csp": {
                    "connectDomains": ["geox.arif-fazil.com", "macrostrat.org"],
                    "resourceDomains": [
                        "geox.arif-fazil.com",
                        "unpkg.com",
                        "tile.openstreetmap.org",
                        "cdn.jsdelivr.net",
                        "cdn.plot.ly",
                    ],
                },
                # SEP-973: Additional tool metadata
                "annotations": {
                    "audience": ["geoscientist", "interpreter"],
                    "priority": 0.8,
                },
            },
            "openai/outputTemplate": uri,
            "openai/toolInvocation/invoking": f"Rendering {app['title']}...",
            "openai/toolInvocation/invoked": f"{app['title']} ready",
            "openai/widgetCSP": {
                "connect_domains": ["geox.arif-fazil.com", "macrostrat.org"],
                "resource_domains": [
                    "geox.arif-fazil.com",
                    "unpkg.com",
                    "tile.openstreetmap.org",
                    "cdn.jsdelivr.net",
                    "cdn.plot.ly",
                ],
                "redirect_domains": ["geox.arif-fazil.com"],
            },
        }
    }
    if app.get("widget_description"):
        meta["_meta"]["openai/widgetDescription"] = app["widget_description"]
    return meta


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


def ui_meta(app_id: str, params: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    """Flat meta dict for ToolResult.meta (not nested under _meta)."""
    block = mcp_apps_resource(app_id, params).get("_meta", {})
    if extra:
        block = {**block, **extra}
    return block


def ui_tool_result(
    *,
    app_id: str,
    text: str,
    structured: dict[str, Any],
    params: dict[str, Any] | None = None,
    is_error: bool = False,
    extra_meta: dict[str, Any] | None = None,
) -> Any:
    """Build a 3-channel MCP Apps ToolResult for host iframe hydrate.

    Channels:
      content            — short text for model / non-UI hosts
      structured_content — widget props (no secrets, no dense raw dumps)
      meta               — ui.resourceUri + openai/* aliases + optional extra

    Returns ToolResult when fastmcp is available; otherwise a plain dict
    with content/structuredContent/_meta keys for tests/offline.
    """
    try:
        from fastmcp.tools import ToolResult
        from mcp.types import TextContent
    except ImportError:  # pragma: no cover
        payload = {
            "content": [{"type": "text", "text": text}],
            "structuredContent": structured,
            "_meta": ui_meta(app_id, params, **(extra_meta or {})),
            "isError": is_error,
        }
        return payload

    # 3-channel truth law: error state must never carry false-success text
    _FALSE_SUCCESS = ("complete", "ready", "loaded", "success")
    if is_error and any(w in text.lower() for w in _FALSE_SUCCESS):
        text = "[GEOX ERROR] Tool execution failed — check structuredContent for details."

    meta = ui_meta(app_id, params, **(extra_meta or {}))
    return ToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=structured,
        meta=meta,
        is_error=is_error,
    )


def wrap_as_ui_tool_result(
    result: Any,
    *,
    app_id: str,
    text: str | None = None,
    params: dict[str, Any] | None = None,
    structured_override: dict[str, Any] | None = None,
) -> Any:
    """Wrap a dict or ToolResult so it always carries 3-channel UI binding.

    - dict → new ToolResult
    - ToolResult → clone with UI meta merged; structured_content preserved
    - other → wrap under {"data": result}
    """
    try:
        from fastmcp.tools import ToolResult
        from mcp.types import TextContent
    except ImportError:  # pragma: no cover
        if isinstance(result, dict):
            sc = structured_override or result
            summary = text or result.get("message") or result.get("status") or f"{app_id} result"
            return ui_tool_result(app_id=app_id, text=str(summary), structured=sc, params=params)
        return ui_tool_result(
            app_id=app_id,
            text=text or f"{app_id} result",
            structured=structured_override or {"data": result},
            params=params,
        )

    if isinstance(result, ToolResult):
        sc = structured_override or result.structured_content or {}
        if not isinstance(sc, dict):
            sc = {"data": sc}
        content = result.content
        if text is not None:
            content = [TextContent(type="text", text=text)]
        elif not content:
            content = [TextContent(type="text", text=f"{app_id} ready")]
        meta = dict(result.meta or {})
        meta.update(ui_meta(app_id, params))
        return ToolResult(
            content=content,
            structured_content=sc,
            meta=meta,
            is_error=bool(result.is_error),
        )

    if isinstance(result, dict):
        sc = structured_override or {
            k: v for k, v in result.items() if not str(k).startswith("_") and k not in ("content", "structuredContent", "_meta")
        }
        summary = text
        if summary is None:
            summary = (
                result.get("content_text")
                or result.get("message")
                or result.get("status")
                or f"{app_id}: ok={result.get('ok', result.get('status', 'done'))}"
            )
        try:
            from geox_mcp.result_truth import result_is_error

            _is_err = result_is_error(result)
        except Exception:
            _is_err = bool(
                result.get("isError")
                or result.get("is_error")
                or result.get("ok") is False
                or result.get("status") in ("INVALID", "NOT_FOUND", "ERROR")
                or result.get("execution_status") in ("ERROR", "FAILED")
                or (isinstance(result.get("primary_artifact"), dict) and result["primary_artifact"].get("status") == "ERROR")
            )
        return ui_tool_result(
            app_id=app_id,
            text=str(summary),
            structured=sc,
            params=params,
            is_error=_is_err,
        )

    return ui_tool_result(
        app_id=app_id,
        text=text or f"{app_id} result",
        structured=structured_override or {"data": result},
        params=params,
    )


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
    "visual_hub": "geox_visual_understand",
    "catalog": "geox_surface_status",
    # Batch F: former zero-bound actives
    "gravmag_studio": "geox_gravmag_studio",
    "workspace_v1": "geox_workspace",
    "workbench_v1": "geox_map_layers_list",
    "prospect_ui": "geox_prospect",
    "well_witness": "geox_petrophysics",
    "analog_digitizer": "geox_well_ingest",
}

# H1 P0: Additional tool-to-app assignments for tools without their own app
# Each entry maps tool_name → app_id (the GEOX_APPS key to use for UI)
_tool_app_fallback: dict[str, str] = {
    # Well tools → WellDesk
    "geox_well_ingest": "well_desk",
    "geox_well_desk": "well_desk",
    "geox_well_qc": "well_desk",  # P0 2026-07-24: only public tool previously unbound
    "geox_well_desurvey": "well_desk",
    "geox_lem_predict": "well_desk",  # PR3: LEM → Well Witness
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
    # Batch F: gravmag owns dedicated studio (was geoprobe — F601 dup fixed 2026-07-24)
    "geox_gravmag_studio": "gravmag_studio",
    # H2: Workspace tool → dedicated workspace shell (Batch F)
    "geox_workspace": "workspace_v1",
    # Bridge → Prospect Studio
    "geox_to_wealth_bridge": "geoprobe",
    # PR3: visual cognition → visual hub
    "geox_visual_understand": "visual_hub",
    "geox_visual_generate_hypotheses": "visual_hub",
    "geox_surface_status": "catalog",
    # P1: tools added post-PR3 — safe fallback binding
    "geox_well_view": "well_desk",
    "geox_geological_model_generate": "earth_volume",
    "geox_gempy_implicit_3d": "earth_volume",
    "geox_h3_spatial_index": "earth_map",
    "geox_lancedb_embed_store": "visual_hub",
    "geox_stac_discover": "earth_map",
    "geox_dde_reason": "basin_explorer",
}


def compact_structured_for_ui(
    result: Any,
    *,
    tool: str,
    app_id: str,
    keys: list[str] | None = None,
    max_str: int = 500,
    max_list: int = 20,
) -> dict[str, Any]:
    """Build a compact structuredContent payload safe for host iframes + model context.

    Drops dense arrays and truncates long strings. Never invents geology.
    """
    base: dict[str, Any] = {"tool": tool, "ok": True}
    if not isinstance(result, dict):
        base["data_type"] = type(result).__name__
        return base

    # C1 FIX (2026-08-26): look inside primary_artifact for preferred keys.
    # get_standard_envelope wraps domain data as primary_artifact, but the
    # prefer list expects keys at top level. Check both levels.
    source = result
    _pa = result.get("primary_artifact")
    if isinstance(_pa, dict):
        source = _pa

    prefer = keys or [
        "status",
        "mode",
        "verdict",
        "claim_id",
        "claim_text",
        "basin_name",
        "well_id",
        "message",
        "band",
        "epistemic",
        "truth_class",
        "filters_run",
        "filters_passed",
        "filters_failed",
        "summary",
        "pos",
        "risk",
        "net_pay",
        "contradictions",
        "error",
        "error_class",
        "ok",
        # 2026-09-06: evidence-contract keys must survive UI compact or
        # postcondition treats a real Malay Basin profile as FALSE_SUCCESS.
        "observed",
        "derived",
        "interpreted",
        "process_hypotheses",
        "play_fairways",
        "unit_count",
        "coverage",
        "sample_units",
        "centroid",
        "stratigraphic_range_ma",
        "stress_polygon",
        "stress_polygon_vertices",
        "moduli",
        "sv_mpa",
        "layers",
        "layer_count",
        "arc",
        "plate_setting",
        "gplates",
    ]
    for k in prefer:
        if k not in source:
            continue
        v = source[k]
        if isinstance(v, str) and len(v) > max_str:
            base[k] = v[:max_str] + "…"
        elif isinstance(v, list) and len(v) > max_list:
            base[k] = v[:max_list]
            base[f"{k}_truncated"] = True
            base[f"{k}_total"] = len(v)
        elif isinstance(v, dict) and json_dumps_len(v) > 4000:
            # keep only shallow keys
            base[k] = {sk: sv for sk, sv in list(v.items())[:15] if not isinstance(sv, (list, dict))}
            base[f"{k}_compacted"] = True
        else:
            base[k] = v

    # 2026-09-06 F2: never stamp ok:true on an error envelope. Previous code
    # only checked `ok is False`, so get_standard_envelope(ERROR) + error
    # string inside primary_artifact was compacted as SUCCESS-with-empty.
    try:
        from geox_mcp.result_truth import result_is_error, truthy_error

        if result_is_error(result) or result_is_error(source):
            base["ok"] = False
        elif truthy_error(result.get("error")) or truthy_error(source.get("error")):
            base["ok"] = False
    except Exception:
        if result.get("ok") is False or source.get("ok") is False:
            base["ok"] = False
        if result.get("error") or source.get("error"):
            base["ok"] = False
        if result.get("execution_status") in ("ERROR", "FAILED", "REJECTED"):
            base["ok"] = False
        if result.get("status") in ("INVALID", "ERROR", "FAILED", "NOT_FOUND"):
            base["ok"] = False
    if "error" not in base:
        err = source.get("error") or result.get("error")
        if err:
            base["error"] = err
    base.setdefault("ui", {"resourceUri": GEOX_APPS.get(app_id, {}).get("uri", f"ui://geox/{app_id}")})
    return base


def json_dumps_len(obj: Any) -> int:
    try:
        import json as _json

        return len(_json.dumps(obj, default=str))
    except Exception:
        return 0


def get_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Get the SEP-2106 outputSchema for a GEOX tool."""
    return TOOL_OUTPUT_SCHEMAS.get(tool_name)


def create_app_resource(app_id: str, html_content: str | None = None) -> dict[str, Any]:
    """Create a SEP-1865 MCP Apps UI resource.

    Args:
        app_id: Key from GEOX_APPS registry
        html_content: Optional HTML override. If None, loads from html_path on disk.

    Returns:
        UIResource-compatible dict for tools/call response content array.
        Falls back to a hand-built dict if the mcp-ui-server SDK is unavailable.
    """
    app = GEOX_APPS.get(app_id)
    if not app:
        raise KeyError(f"Unknown GEOX app_id: '{app_id}' in GEOX_APPS registry")

    if html_content is None:
        html_content = load_app_html(app_id)

    resource_type = (
        "externalUrl" if (app.get("external_url") and resolve_html_path(app) is None and html_content is None) else "rawHtml"
    )

    try:
        # Prefer on-disk HTML even if marked externalUrl historically
        if html_content is None and resolve_html_path(app) is not None:
            html_content = load_app_html(app_id)
            resource_type = "rawHtml"

        if resource_type == "externalUrl" and app.get("external_url"):
            payload: dict[str, Any] = {
                "uri": app["uri"],
                "content": {"type": "externalUrl", "iframeUrl": app["external_url"]},
                "encoding": "text",
            }
            text = (
                "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
                f"<meta http-equiv='refresh' content='0;url={app['external_url']}'>"
                f"<title>{app['title']}</title></head><body>"
                f"<p>{app['title']} — opening external cockpit. "
                f"<a href='{app['external_url']}' target='_blank' rel='noopener'>Open manually</a></p>"
                f"</body></html>"
            )
        else:
            if html_content is None:
                html_content = load_app_html(app_id)
            payload = {
                "uri": app["uri"],
                "content": {"type": "rawHtml", "htmlString": html_content},
                "encoding": "text",
            }
            text = html_content

        if _MCP_UI_SERVER_AVAILABLE:
            try:
                resource = create_ui_resource(payload)
                return {
                    "type": "resource",
                    "resource": {
                        "uri": resource.resource.uri,
                        "mimeType": resource.resource.mimeType,
                        "text": resource.resource.text,
                    },
                }
            except Exception as exc:
                logger.warning("mcp-ui-server create_ui_resource failed for %s: %s; using fallback", app_id, exc)

        # Fallback: hand-built SEP-1865 resource dict (no SDK required)
        return {
            "type": "resource",
            "resource": {
                "uri": app["uri"],
                "mimeType": app.get("mime_type", "text/html;profile=mcp-app"),
                "text": text,
            },
        }
    except Exception as exc:
        logger.error("Failed to create UI resource for app '%s' (%s): %s", app_id, app.get("uri"), exc)
        raise ValueError(f"Failed to create UI resource for app '{app_id}' ({app.get('uri')}): {exc}") from exc


def _resource_already_registered(mcp: Any, uri: str) -> bool:
    """True if FastMCP local provider already has this resource URI."""
    local = getattr(mcp, "_local_provider", None)
    if local is None:
        return False
    comps = getattr(local, "_components", {}) or {}
    return f"resource:{uri}@" in comps


def register_mcp_apps_resources(mcp: Any) -> None:
    """Register all GEOX_APPS UI resources with real on-disk HTML.

    Hosts call resources/read(ui://geox/...) and must receive host-usable HTML
    (≥1KB), not stub placeholders. FastMCP overwrites on re-register, so this
    runs last in create_app() and is the authority for GEOX_APPS URIs.
    """
    try:
        from fastmcp.apps import AppConfig, ResourceCSP

        default_csp = ResourceCSP(
            connect_domains=["geox.arif-fazil.com", "macrostrat.org"],
            resource_domains=[
                "geox.arif-fazil.com",
                "unpkg.com",
                "tile.openstreetmap.org",
                "cdn.jsdelivr.net",
                "cdn.plot.ly",
            ],
        )
    except ImportError:
        AppConfig = None
        default_csp = None

    registered = 0
    skipped = 0
    failed = 0

    for app_id, app in GEOX_APPS.items():
        uri = app["uri"]
        title = app["title"]
        desc = app["description"]
        mime_type = app.get("mime_type", "text/html;profile=mcp-app")

        # Fail closed at boot if primary apps lack real HTML
        try:
            # Validate content exists (read once at register time for boot check)
            _boot_html = load_app_html(app_id)
        except Exception as exc:
            failed += 1
            logger.error("MCP App '%s' (%s) has no host-usable HTML: %s", app_id, uri, exc)
            continue

        def _make_file_handler(bound_app_id: str, bound_title: str = title, bound_desc: str = desc):
            async def _handler() -> str:
                # Re-read from disk each call so HTML edits apply without restart
                return load_app_html(bound_app_id)

            _handler.__name__ = f"geox_ui_{bound_app_id}"
            _handler.__doc__ = f"{bound_title} — {bound_desc}"
            return _handler

        kwargs: dict[str, Any] = {
            "name": title,
            "description": f"{title} — {desc} (html_path={app.get('html_path')})",
            "mime_type": mime_type,
        }
        if AppConfig and default_csp:
            kwargs["app"] = AppConfig(prefers_border=True, csp=default_csp)

        already = _resource_already_registered(mcp, uri)
        try:
            # Always (re)register so GEOX_APPS html_path wins over earlier stubs.
            # FastMCP logs "Component already exists" then overwrites — expected.
            mcp.resource(uri, **kwargs)(_make_file_handler(app_id))
            registered += 1
            if already:
                logger.info(
                    "MCP App resource re-bound to real HTML: %s (%dB from %s)",
                    uri,
                    len(_boot_html),
                    app.get("html_path"),
                )
            else:
                logger.info(
                    "MCP App resource registered: %s (%dB from %s)",
                    uri,
                    len(_boot_html),
                    app.get("html_path"),
                )
        except Exception as e:
            skipped += 1
            logger.warning("Resource %s registration failed: %s", uri, e)

    logger.info(
        "Registered GEOX MCP Apps UI resources (ok=%d skipped=%d failed=%d total=%d)",
        registered,
        skipped,
        failed,
        len(GEOX_APPS),
    )
    if failed:
        logger.warning(
            "PR1: %d GEOX_APPS entries missing host-usable HTML — fix html_path before claiming GUI READY",
            failed,
        )


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

    def _inject_widget_meta(comp: Any, app_info: dict[str, Any], uri: str) -> None:
        """Inject ChatGPT widget metadata into a tool component's meta dict."""
        comp.meta["ui"] = {
            "resourceUri": uri,
            "title": app_info["title"],
            "renderMode": app_info["render_mode"],
            "mimeType": app_info["mime_type"],
            "domain": "https://geox.arif-fazil.com",
        }
        comp.meta["openai/outputTemplate"] = uri
        comp.meta["openai/toolInvocation/invoking"] = f"Rendering {app_info['title']}..."
        comp.meta["openai/toolInvocation/invoked"] = f"{app_info['title']} ready"
        comp.meta["openai/widgetCSP"] = {
            "connect_domains": ["geox.arif-fazil.com", "macrostrat.org"],
            "resource_domains": [
                "geox.arif-fazil.com",
                "unpkg.com",
                "tile.openstreetmap.org",
                "cdn.jsdelivr.net",
                "cdn.plot.ly",
            ],
            "redirect_domains": ["geox.arif-fazil.com"],
        }
        wd = app_info.get("widget_description")
        if wd:
            comp.meta["openai/widgetDescription"] = wd

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
            _inject_widget_meta(comp, app_info, uri)
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
                _inject_widget_meta(comp, app_info, uri)
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
