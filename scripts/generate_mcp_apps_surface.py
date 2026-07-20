#!/usr/bin/env python3
"""
GEOX MCP APPS SURFACE GENERATOR (P0 Single Source of Truth)
══════════════════════════════════════════════════════════════
Generates canonical GEOX_MCP_APPS_SURFACE.json directly from
live FastMCP runtime, apps/apps.json, and static asset builds.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any

from geox_mcp.server import create_app, mcp

GEOX_ROOT = Path(__file__).resolve().parent.parent
APPS_JSON_PATH = GEOX_ROOT / "apps" / "apps.json"
OUTPUT_PATH = GEOX_ROOT / "GEOX_MCP_APPS_SURFACE.json"
STATIC_GUI_OUTPUT_PATH = GEOX_ROOT / "static" / "gui" / "GEOX_MCP_APPS_SURFACE.json"


async def main() -> None:
    create_app()

    # Load apps.json definitions if available
    apps_meta: dict[str, Any] = {}
    if APPS_JSON_PATH.exists():
        with open(APPS_JSON_PATH, "r", encoding="utf-8") as f:
            apps_meta = json.load(f)

    apps_by_id = {app["id"]: app for app in apps_meta.get("apps", [])}
    apps_by_uri = {app["uri"]: app for app in apps_meta.get("apps", [])}

    resources = await mcp.list_resources()
    tools = await mcp.list_tools()

    # Build tool-to-UI map
    tool_ui_bindings: dict[str, str] = {}
    for t in tools:
        meta = getattr(t, "meta", {}) or {}
        if "ui" in meta and "resourceUri" in meta["ui"]:
            tool_ui_bindings[t.name] = meta["ui"]["resourceUri"]

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

        # Match app metadata
        app_meta = apps_by_uri.get(uri, {})
        app_id = app_meta.get("id", uri.replace("ui://geox/", "").replace(".html", ""))
        status = app_meta.get("status", "active")
        title = getattr(r, "name", "") or app_meta.get("title", app_id)

        # Bound tools
        bound_tools = [t_name for t_name, u in tool_ui_bindings.items() if u == uri]

        ui_resources_surface.append({
            "id": app_id,
            "uri": uri,
            "title": title,
            "status": status,
            "mime_type": mime_type,
            "content_bytes": content_len,
            "content_hash": content_hash,
            "bound_tools": sorted(bound_tools),
            "csp_domains": ["geox.arif-fazil.com", "macrostrat.org", "tile.openstreetmap.org", "unpkg.com"],
            "component_domains": ["geox.arif-fazil.com"],
            "deprecation_note": app_meta.get("deprecation_note"),
        })

    surface_manifest = {
        "schema_version": "1.0.0",
        "generated_at": asyncio.get_event_loop().time(),
        "organ": "GEOX",
        "total_canonical_tools": len(tools),
        "total_ui_resources": len(ui_resources_surface),
        "active_ui_resources": len([r for r in ui_resources_surface if r["status"] == "active"]),
        "deprecated_ui_resources": len([r for r in ui_resources_surface if r["status"] == "deprecated"]),
        "planned_ui_resources": len([r for r in ui_resources_surface if r["status"] == "planned"]),
        "ui_resources": sorted(ui_resources_surface, key=lambda x: x["uri"]),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(surface_manifest, f, indent=2)

    STATIC_GUI_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATIC_GUI_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(surface_manifest, f, indent=2)

    print(f"✓ Generated canonical GEOX_MCP_APPS_SURFACE.json ({len(ui_resources_surface)} UI resources)")


if __name__ == "__main__":
    asyncio.run(main())
