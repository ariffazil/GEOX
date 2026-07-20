"""
GEOX MCP Apps & GUI Readiness Test Suite
═════════════════════════════════════════
Verifies compliance with SEP-1865 (MCP Apps specification), @mcp-ui standard,
and ChatGPT outputTemplate compatibility alias under arifOS governance.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import pytest
from geox_mcp.server import create_app, mcp
from geox_mcp.tools.mcp_apps_bridge import (
    GEOX_APPS,
    _app_to_tool,
    create_app_resource,
    enrich_response,
    mcp_apps_resource,
)

create_app()


@pytest.mark.asyncio
async def test_ui_tools_list_has_meta_binding():
    """Verify tools/list exposes _meta.ui.resourceUri and openai/outputTemplate alias."""
    tools = await mcp.list_tools()
    tools_by_name = {t.name: t for t in tools}

    for app_id, tool_name in _app_to_tool.items():
        assert tool_name in tools_by_name, f"Tool {tool_name} bound to app {app_id} missing in list_tools"
        t = tools_by_name[tool_name]
        meta = getattr(t, "meta", {}) or {}
        assert "ui" in meta, f"Tool {tool_name} missing meta.ui"
        assert "resourceUri" in meta["ui"], f"Tool {tool_name} missing meta.ui.resourceUri"
        assert meta["ui"]["resourceUri"].startswith("ui://geox/"), f"Invalid URI for {tool_name}"
        assert "openai/outputTemplate" in meta, f"Tool {tool_name} missing ChatGPT openai/outputTemplate alias"
        assert meta["openai/outputTemplate"] == meta["ui"]["resourceUri"]


@pytest.mark.asyncio
async def test_ui_resources_list_and_read():
    """Verify resources/list returns ui:// resources and resources/read serves valid mcp-app HTML."""
    resources = await mcp.list_resources()
    uris = {str(getattr(r, "uri", "")) for r in resources}

    # Verify key UI URIs are registered
    expected_uris = [
        "ui://geox/well-desk",
        "ui://geox/basin-explorer",
        "ui://geox/judge-console",
        "ui://geox/workbench-v1.html",
        "ui://geox/workspace-v1.html",
    ]
    for uri in expected_uris:
        assert uri in uris, f"Expected UI resource {uri} not in resources/list"

    # Verify reading well-desk resource returns text/html;profile=mcp-app or text/uri-list
    res = await mcp.read_resource("ui://geox/well-desk")
    assert len(res.contents) > 0
    content = res.contents[0]
    assert content.mime_type in ("text/html;profile=mcp-app", "text/uri-list")
    assert len(content.content) > 0


def test_create_app_resource_external_and_raw():
    """Verify create_app_resource constructs valid UIResource payloads for external and raw apps."""
    well_desk_res = create_app_resource("well_desk")
    assert well_desk_res is not None
    assert well_desk_res["type"] == "resource"
    assert "uri" in well_desk_res["resource"]

    judge_res = create_app_resource("judge_console")
    assert judge_res is not None
    assert judge_res["type"] == "resource"


def test_enrich_response_adds_chatgpt_template_alias():
    """Verify enrich_response attaches _meta.ui AND openai/outputTemplate alias."""
    base_response = {"status": "success", "data": {"well_id": "MB-001"}}
    enriched = enrich_response(base_response, "well_desk", {"well_id": "MB-001"})

    assert "_meta" in enriched
    assert "ui" in enriched["_meta"]
    assert enriched["_meta"]["ui"]["resourceUri"] == "ui://geox/well-desk?well_id=MB-001"
    assert enriched["_meta"]["openai/outputTemplate"] == "ui://geox/well-desk?well_id=MB-001"
    assert "openai/toolInvocation/invoking" in enriched["_meta"]
    assert "openai/toolInvocation/invoked" in enriched["_meta"]


def test_geox_apps_registry_integrity():
    """Verify all GEOX_APPS entries carry required SEP-1865 fields."""
    for app_id, app in GEOX_APPS.items():
        assert "uri" in app, f"App {app_id} missing uri"
        assert app["uri"].startswith("ui://geox/"), f"App {app_id} uri must start with ui://geox/"
        assert "title" in app, f"App {app_id} missing title"
        assert "render_mode" in app, f"App {app_id} missing render_mode"
        assert app["mime_type"] == "text/html;profile=mcp-app", f"App {app_id} invalid mime_type"
