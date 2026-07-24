#!/usr/bin/env python3
"""
GEOX MCP APPS SURFACE GENERATOR (P0 Single Source of Truth)
══════════════════════════════════════════════════════════════
Generates canonical GEOX_MCP_APPS_SURFACE.json directly from
live FastMCP runtime, apps/apps.json, and static asset builds.

W2 (2026-07-24): Anti-regression for active zero-bound UIs.
  - Tool→UI from live meta.ui.resourceUri
  - Reverse maps from _app_to_tool + _tool_app_fallback (mcp_apps_bridge)
  - URI alias equivalence (.html twin, geox-mcp-visual ↔ visual-hub)
  - apps.json visual_tools as supplemental seeds
  - FAIL CLOSED if any active UI has empty bound_tools

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from geox_mcp.server import create_app, mcp
from geox_mcp.tools.mcp_apps_bridge import (
    GEOX_APPS,
    _app_to_tool,
    _tool_app_fallback,
)

GEOX_ROOT = Path(__file__).resolve().parent.parent
APPS_JSON_PATH = GEOX_ROOT / "apps" / "apps.json"
OUTPUT_PATH = GEOX_ROOT / "GEOX_MCP_APPS_SURFACE.json"
STATIC_GUI_OUTPUT_PATH = GEOX_ROOT / "static" / "gui" / "GEOX_MCP_APPS_SURFACE.json"

# URI aliases that share the same bound tool set (legacy + host twins).
# Keys and values are base URIs (no query string).
_URI_ALIASES: dict[str, str] = {
    # legacy apps.json visual hub id ↔ canonical MCP Apps visual hub
    "ui://geox/geox-mcp-visual": "ui://geox/visual-hub",
    "ui://geox/visual-hub": "ui://geox/visual-hub",
    # .html twins registered by older resource paths
    "ui://geox/gravmag-studio.html": "ui://geox/gravmag-studio",
    "ui://geox/workspace-v1.html": "ui://geox/workspace-v1",
    "ui://geox/workbench-v1.html": "ui://geox/workbench-v1",
    # prospect studio shell shares prospect tools with prospect-ui
    "ui://geox/prospect-studio": "ui://geox/prospect-ui",
}


def _base_uri(uri: str) -> str:
    """Strip query/fragment; keep scheme+path."""
    if not uri:
        return ""
    return uri.split("?", 1)[0].split("#", 1)[0].strip()


def _canonical_uri(uri: str) -> str:
    """Map a resource URI onto its binding-family canonical form."""
    base = _base_uri(uri)
    if base in _URI_ALIASES:
        return _URI_ALIASES[base]
    # strip trailing .html if the non-html form is the bridge canonical
    if base.endswith(".html"):
        stripped = base[: -len(".html")]
        if stripped in {a["uri"] for a in GEOX_APPS.values()}:
            return stripped
        if stripped in _URI_ALIASES:
            return _URI_ALIASES[stripped]
    return base


def _uri_family(uri: str) -> set[str]:
    """All URIs that should share bound_tools with this one."""
    base = _base_uri(uri)
    canon = _canonical_uri(base)
    family = {base, canon}
    # include known aliases that map to same canon
    for alias, target in _URI_ALIASES.items():
        if target == canon or alias == canon or target == base or alias == base:
            family.add(alias)
            family.add(target)
    # html twin
    if not base.endswith(".html"):
        family.add(base + ".html")
    else:
        family.add(base[: -len(".html")])
    if not canon.endswith(".html"):
        family.add(canon + ".html")
    return {u for u in family if u}


def _build_tool_uri_index(tools: list[Any]) -> dict[str, set[str]]:
    """canonical_uri → set(tool_name) from live tool meta + bridge maps."""
    index: dict[str, set[str]] = defaultdict(set)

    # 1) Live meta from tools/list
    for t in tools:
        meta = getattr(t, "meta", {}) or {}
        ui = meta.get("ui") if isinstance(meta, dict) else None
        if not isinstance(ui, dict):
            continue
        uri = ui.get("resourceUri")
        if not uri:
            continue
        index[_canonical_uri(str(uri))].add(t.name)

    # 2) Reverse _app_to_tool: app_id → primary tool → GEOX_APPS uri
    for app_id, tool_name in _app_to_tool.items():
        app = GEOX_APPS.get(app_id)
        if not app:
            continue
        index[_canonical_uri(app["uri"])].add(tool_name)

    # 3) Reverse _tool_app_fallback: tool → app_id → uri
    for tool_name, app_id in _tool_app_fallback.items():
        app = GEOX_APPS.get(app_id)
        if not app:
            continue
        index[_canonical_uri(app["uri"])].add(tool_name)

    return index


def _tools_for_uri(uri: str, index: dict[str, set[str]], apps_visual: dict[str, list[str]]) -> list[str]:
    """Collect bound tools for a resource URI including alias family + apps.json seeds."""
    bound: set[str] = set()
    family = _uri_family(uri)
    for u in family:
        bound |= index.get(_canonical_uri(u), set())
        # direct key hits (in case index has non-canonical keys)
        bound |= index.get(u, set())
        # apps.json visual_tools keyed by exact uri
        bound |= set(apps_visual.get(u, []))
        bound |= set(apps_visual.get(_canonical_uri(u), []))
    return sorted(bound)


async def main() -> int:
    create_app()

    # Load apps.json definitions if available
    apps_meta: dict[str, Any] = {}
    if APPS_JSON_PATH.exists():
        with open(APPS_JSON_PATH, encoding="utf-8") as f:
            apps_meta = json.load(f)

    apps_by_uri = {app["uri"]: app for app in apps_meta.get("apps", []) if "uri" in app}
    apps_visual: dict[str, list[str]] = {
        app["uri"]: list(app.get("visual_tools") or app.get("tools") or [])
        for app in apps_meta.get("apps", [])
        if "uri" in app
    }

    resources = await mcp.list_resources()
    tools = await mcp.list_tools()
    tool_uri_index = _build_tool_uri_index(tools)

    ui_resources_surface: list[dict[str, Any]] = []
    seen_uris: set[str] = set()

    for r in resources:
        uri = str(getattr(r, "uri", ""))
        if not uri.startswith("ui://geox/"):
            continue

        if uri in seen_uris:
            continue
        seen_uris.add(uri)

        # Read resource content & hash
        content_hash = "UNKNOWN"
        mime_type = getattr(r, "mime_type", "text/html;profile=mcp-app")
        content_len = 0
        try:
            res_data = await mcp.read_resource(uri)
            if res_data and res_data.contents:
                raw_content = res_data.contents[0].content
                mime_type = res_data.contents[0].mime_type or mime_type
                content_len = len(raw_content)
                content_hash = "sha256:" + hashlib.sha256(raw_content.encode("utf-8")).hexdigest()[:16]
        except Exception as e:
            content_hash = f"ERROR: {e}"

        # Match app metadata (exact uri first, then canonical)
        app_meta = apps_by_uri.get(uri) or apps_by_uri.get(_canonical_uri(uri), {})
        app_id = app_meta.get("id", uri.replace("ui://geox/", "").replace(".html", ""))
        status = app_meta.get("status", "active")
        title = getattr(r, "name", "") or app_meta.get("title", app_id)

        # Bound tools — live meta + bridge reverse maps + alias family + apps.json
        bound_tools = _tools_for_uri(uri, tool_uri_index, apps_visual)

        ui_resources_surface.append({
            "id": app_id,
            "uri": uri,
            "title": title,
            "status": status,
            "mime_type": mime_type,
            "content_bytes": content_len,
            "content_hash": content_hash,
            "bound_tools": bound_tools,
            "csp_domains": ["geox.arif-fazil.com", "macrostrat.org", "tile.openstreetmap.org", "unpkg.com"],
            "component_domains": ["geox.arif-fazil.com"],
            "deprecation_note": app_meta.get("deprecation_note"),
        })

    # W2 gate: active resources must not be zero-bound
    active_zero = [
        r for r in ui_resources_surface
        if r.get("status") == "active" and not (r.get("bound_tools") or [])
    ]

    surface_manifest = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "organ": "GEOX",
        "total_canonical_tools": len(tools),
        "total_ui_resources": len(ui_resources_surface),
        "active_ui_resources": len([r for r in ui_resources_surface if r["status"] == "active"]),
        "deprecated_ui_resources": len([r for r in ui_resources_surface if r["status"] == "deprecated"]),
        "planned_ui_resources": len([r for r in ui_resources_surface if r["status"] == "planned"]),
        "active_zero_bound": len(active_zero),
        "ui_resources": sorted(ui_resources_surface, key=lambda x: x["uri"]),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(surface_manifest, f, indent=2)
        f.write("\n")

    STATIC_GUI_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_GUI_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(surface_manifest, f, indent=2)
        f.write("\n")

    print(
        f"✓ Generated canonical GEOX_MCP_APPS_SURFACE.json "
        f"({len(ui_resources_surface)} UI resources, active_zero_bound={len(active_zero)})"
    )

    if active_zero:
        print("✗ W2 FAIL: active UI resources with zero bound_tools:", file=sys.stderr)
        for r in active_zero:
            print(f"  - {r['uri']} (id={r.get('id')})", file=sys.stderr)
        print(
            "Fix: extend _app_to_tool / _tool_app_fallback / _URI_ALIASES in "
            "mcp_apps_bridge.py or generate_mcp_apps_surface.py",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
