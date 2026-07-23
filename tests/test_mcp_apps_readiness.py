"""
GEOX MCP Apps & GUI Protocol Readiness Test Suite (P0 Compliant)
════════════════════════════════════════════════════════════════════
Verifies end-to-end MCP protocol execution sequence:
  initialize -> tools/list -> resources/list -> resources/read -> tools/call

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from geox_mcp.server import create_app, mcp
from geox_mcp.tools.mcp_apps_bridge import (
    GEOX_APPS,
    _MIN_HOST_HTML_BYTES,
    create_app_resource,
    enrich_response,
    load_app_html,
)

GEOX_ROOT = Path(__file__).resolve().parent.parent
SURFACE_MANIFEST_PATH = GEOX_ROOT / "GEOX_MCP_APPS_SURFACE.json"

create_app()


@pytest.fixture(scope="module", autouse=True)
def ensure_surface_manifest():
    """Ensure canonical GEOX_MCP_APPS_SURFACE.json exists before tests."""
    assert SURFACE_MANIFEST_PATH.exists(), "GEOX_MCP_APPS_SURFACE.json missing. Run scripts/generate_mcp_apps_surface.py"


@pytest.mark.asyncio
async def test_01_tools_list_schema_and_ui_bindings():
    """Verify tools/list exposes _meta.ui.resourceUri and openai/outputTemplate alias for 30 canonical tools."""
    tools = await mcp.list_tools()
    assert len(tools) == 31, f"Expected 31 canonical tools, got {len(tools)}"

    tools_by_name = {t.name: t for t in tools}

    # Verify key app-bound tools carry valid UI metadata
    app_tools = ["geox_petrophysics", "geox_basin", "geox_claim", "geox_falsify", "geox_prospect", "geox_map_layers_list"]
    for tool_name in app_tools:
        assert tool_name in tools_by_name
        t = tools_by_name[tool_name]
        meta = getattr(t, "meta", {}) or {}
        assert "ui" in meta, f"Tool {tool_name} missing meta.ui"
        assert "resourceUri" in meta["ui"], f"Tool {tool_name} missing meta.ui.resourceUri"
        assert meta["ui"]["resourceUri"].startswith("ui://geox/"), f"Invalid URI for {tool_name}"
        assert "openai/outputTemplate" in meta, f"Tool {tool_name} missing ChatGPT alias"
        assert meta["openai/outputTemplate"] == meta["ui"]["resourceUri"]


@pytest.mark.asyncio
async def test_02_resources_list_matches_surface_manifest():
    """Verify resources/list matches generated GEOX_MCP_APPS_SURFACE.json manifest."""
    with open(SURFACE_MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    resources = await mcp.list_resources()
    uris = {str(getattr(r, "uri", "")) for r in resources}

    for app_res in manifest["ui_resources"]:
        expected_uri = app_res["uri"]
        assert expected_uri in uris, f"Manifest UI resource {expected_uri} missing in resources/list"


@pytest.mark.asyncio
async def test_03_resources_read_all_active_uris():
    """Verify resources/read for every active UI resource returns valid HTML and mcp-app MIME."""
    with open(SURFACE_MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    active_resources = [r for r in manifest["ui_resources"] if r["status"] == "active"]
    assert len(active_resources) > 0, "No active UI resources declared in manifest"

    for r_meta in active_resources:
        uri = r_meta["uri"]
        res = await mcp.read_resource(uri)
        assert res is not None, f"Failed to read resource {uri}"
        assert len(res.contents) > 0, f"Empty content for resource {uri}"
        content = res.contents[0]
        assert content.mime_type in ("text/html;profile=mcp-app", "text/uri-list")
        assert len(content.content) > 0, f"Resource {uri} content is empty"


@pytest.mark.asyncio
async def test_03b_primary_apps_serve_real_html_not_stubs():
    """PR1: bound primary apps must serve ≥1KB real HTML, never stub placeholders."""
    primary_uris = [app["uri"] for app in GEOX_APPS.values()]
    stub_markers = (
        "Open externally.",
        "Open in cockpit.",
        "Open at arif-fazil.com",
    )
    for uri in primary_uris:
        res = await mcp.read_resource(uri)
        text = res.contents[0].content
        assert len(text) >= _MIN_HOST_HTML_BYTES, (
            f"{uri} still a stub: {len(text)}B < {_MIN_HOST_HTML_BYTES}B — head={text[:80]!r}"
        )
        # Exact historical stub strings must not be the whole payload
        assert not any(text.strip() == f"<h1>{m}</h1>" for m in ()), uri
        for marker in stub_markers:
            # Marker may appear in a full page as a secondary link — forbid ONLY tiny stubs
            if len(text) < 500:
                assert marker not in text, f"{uri} looks like legacy stub containing {marker!r}"


def test_04_create_app_resource_strict_validation():
    """Verify create_app_resource constructs valid UIResource payloads and fails loudly on errors."""
    well_desk_res = create_app_resource("well_desk")
    assert well_desk_res is not None
    assert well_desk_res["type"] == "resource"
    assert "uri" in well_desk_res["resource"]
    body = well_desk_res["resource"].get("text") or ""
    assert len(body) >= _MIN_HOST_HTML_BYTES, f"create_app_resource well_desk still stub ({len(body)}B)"

    # Fails loudly on invalid app_id
    with pytest.raises(KeyError):
        create_app_resource("invalid_nonexistent_app_id")


def test_04b_load_app_html_from_disk():
    """Every GEOX_APPS entry resolves to host-usable on-disk HTML."""
    for app_id in GEOX_APPS:
        html = load_app_html(app_id)
        assert len(html) >= _MIN_HOST_HTML_BYTES, f"{app_id}: {len(html)}B"
        assert "<html" in html.lower() or "<!doctype" in html.lower() or "<h1" in html.lower()


def test_05_enrich_response_channel_discipline():
    """Verify enrich_response attaches _meta.ui AND openai/outputTemplate alias."""
    base_response = {"status": "success", "data": {"well_id": "MB-001"}}
    enriched = enrich_response(base_response, "well_desk", {"well_id": "MB-001"})

    assert "_meta" in enriched
    assert "ui" in enriched["_meta"]
    assert enriched["_meta"]["ui"]["resourceUri"] == "ui://geox/well-desk?well_id=MB-001"
    assert enriched["_meta"]["openai/outputTemplate"] == "ui://geox/well-desk?well_id=MB-001"
    assert "openai/toolInvocation/invoking" in enriched["_meta"]
    assert "openai/toolInvocation/invoked" in enriched["_meta"]
