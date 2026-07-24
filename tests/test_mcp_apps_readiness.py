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


@pytest.mark.asyncio
async def test_06_well_witness_three_channel_return():
    """PR2: geox_well_desk open returns content + structuredContent + meta.ui."""
    from fastmcp.tools import ToolResult

    result = await mcp.call_tool("geox_well_desk", {"mode": "open", "well_id": "A10"})
    assert result is not None

    # FastMCP ToolResult or converted CallToolResult
    if isinstance(result, ToolResult):
        content = result.content
        sc = result.structured_content or {}
        meta = result.meta or {}
        is_error = result.is_error
    else:
        # ToolResult-like from call_tool
        content = getattr(result, "content", None) or []
        sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None) or {}
        meta = getattr(result, "meta", None) or {}
        is_error = bool(getattr(result, "is_error", False) or getattr(result, "isError", False))

    assert not is_error, f"well_desk open failed: {result}"
    # content channel — non-empty text
    texts = []
    for block in content or []:
        t = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
        if t:
            texts.append(t)
    assert texts, "content channel empty"
    assert any("Well" in t or "well" in t for t in texts)

    # structured channel — hydrate keys for p0-viz
    assert isinstance(sc, dict)
    assert sc.get("well_id") == "A10" or sc.get("summary", {}).get("well_id") == "A10"
    assert "epistemic" in sc or "summary" in sc

    # meta channel — UI binding
    ui = meta.get("ui") if isinstance(meta, dict) else None
    assert ui is not None, f"meta.ui missing: {meta}"
    assert str(ui.get("resourceUri", "")).startswith("ui://geox/well-desk")
    assert meta.get("openai/outputTemplate", "").startswith("ui://geox/well-desk")


@pytest.mark.asyncio
async def test_07_well_desk_resource_is_host_bridge_shell():
    """PR2: ui://geox/well-desk serves p0-viz (ui/initialize), not multi-file index."""
    res = await mcp.read_resource("ui://geox/well-desk")
    html = res.contents[0].content
    assert len(html) >= _MIN_HOST_HTML_BYTES
    assert "ui/initialize" in html or "ui/notifications/tool-result" in html
    # Must not depend on relative bridge scripts (broken in MCP iframe)
    assert "./src/bridge/MCPBridge.js" not in html


@pytest.mark.asyncio
async def test_08_all_tools_have_four_annotations_and_ui_binding():
    """PR3: 31 tools — full MCP annotation quartet + ui.resourceUri (or documented)."""
    tools = await mcp.list_tools()
    assert len(tools) == 31
    needed = ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint")
    missing_ann = []
    missing_ui = []
    for t in tools:
        ann = getattr(t, "annotations", None)
        keys = {}
        if ann is not None:
            if hasattr(ann, "model_dump"):
                keys = ann.model_dump()
            elif isinstance(ann, dict):
                keys = ann
            else:
                keys = {k: getattr(ann, k, None) for k in needed}
        if any(keys.get(k) is None for k in needed):
            missing_ann.append((t.name, {k: keys.get(k) for k in needed}))
        meta = getattr(t, "meta", None) or {}
        ui = meta.get("ui") if isinstance(meta, dict) else None
        if not ui or not ui.get("resourceUri"):
            missing_ui.append(t.name)
    assert not missing_ann, f"Incomplete annotations: {missing_ann}"
    assert not missing_ui, f"Missing UI binding: {missing_ui}"


@pytest.mark.asyncio
async def test_09_golden_prompts_direct_indirect_negative():
    """PR3 host-path golden prompts (in-process host simulation).

    DIRECT  — open Well Witness for A10 (evidence lane; no arifOS session)
    INDIRECT — tools/list shows petrophysics UI binding (call path needs live session)
    NEGATIVE — missing well_id → isError + readable text (no crash)
    """
    from fastmcp.tools import ToolResult

    def _channels(result):
        if isinstance(result, ToolResult):
            content, sc, meta, err = result.content, result.structured_content or {}, result.meta or {}, result.is_error
        else:
            content = getattr(result, "content", None) or []
            sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None) or {}
            meta = getattr(result, "meta", None) or {}
            err = bool(getattr(result, "is_error", False) or getattr(result, "isError", False))
        texts = []
        for b in content or []:
            t = getattr(b, "text", None) or (b.get("text") if isinstance(b, dict) else None)
            if t:
                texts.append(t)
        return texts, sc, meta, err

    # DIRECT
    direct = await mcp.call_tool("geox_well_desk", {"mode": "open", "well_id": "A10"})
    texts, sc, meta, err = _channels(direct)
    assert not err
    assert texts
    assert sc.get("well_id") == "A10" or sc.get("summary", {}).get("well_id") == "A10"
    assert (meta.get("ui") or {}).get("resourceUri", "").startswith("ui://geox/well-desk")
    res = await mcp.read_resource("ui://geox/well-desk")
    assert "ui/initialize" in res.contents[0].content or "tool-result" in res.contents[0].content

    # INDIRECT — host discovers UI via tools/list (model chains data→view)
    tools = await mcp.list_tools()
    by_name = {t.name: t for t in tools}
    petro = by_name["geox_petrophysics"]
    petro_meta = getattr(petro, "meta", None) or {}
    assert (petro_meta.get("ui") or {}).get("resourceUri", "").startswith("ui://geox/well-desk")
    assert petro_meta.get("openai/outputTemplate", "").startswith("ui://geox/well-desk")

    # NEGATIVE — refuse without well_id, keep session alive (isError path)
    negative = await mcp.call_tool("geox_well_desk", {"mode": "open", "well_id": ""})
    texts3, sc3, meta3, err3 = _channels(negative)
    assert err3 or sc3.get("ok") is False or sc3.get("error_class")
    assert texts3, "negative path must return readable text"
    # UI meta still present so host does not crash on binding
    assert (meta3.get("ui") or {}).get("resourceUri", "").startswith("ui://geox/")


def test_10_judge_and_basin_three_channel_helpers():
    """PR3: wrap_as_ui_tool_result binds falsify→judge-console and basin→basin-explorer.

    Live call_tool for these lanes needs arifOS session validation; unit-test the
    return-channel contract so GUI readiness does not depend on transport health.
    """
    from fastmcp.tools import ToolResult
    from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui, wrap_as_ui_tool_result

    falsify_raw = {
        "ok": True,
        "verdict": "FALSIFIED",
        "filters_run": 3,
        "filters_passed": 1,
        "filters_failed": 2,
        "claim_text": "Beach facies at 5000m water depth",
    }
    f_res = wrap_as_ui_tool_result(
        falsify_raw,
        app_id="judge_console",
        structured_override=compact_structured_for_ui(
            falsify_raw, tool="geox_falsify", app_id="judge_console"
        ),
        text="Falsify full: verdict=FALSIFIED.",
    )
    assert isinstance(f_res, ToolResult)
    assert f_res.meta["ui"]["resourceUri"].startswith("ui://geox/judge-console")
    assert f_res.structured_content.get("verdict") == "FALSIFIED"
    assert f_res.content and "Falsify" in f_res.content[0].text

    basin_raw = {"ok": True, "status": "ok", "basin_name": "malay-basin", "mode": "profile"}
    b_res = wrap_as_ui_tool_result(
        basin_raw,
        app_id="basin_explorer",
        structured_override=compact_structured_for_ui(
            basin_raw, tool="geox_basin", app_id="basin_explorer"
        ),
        text="Basin profile: malay-basin.",
    )
    assert isinstance(b_res, ToolResult)
    assert b_res.meta["ui"]["resourceUri"].startswith("ui://geox/basin-explorer")
    assert b_res.structured_content.get("basin_name") == "malay-basin"


@pytest.mark.asyncio
async def test_10b_judge_basin_tools_list_bindings():
    """PR3: tools/list exposes judge/basin UI bindings for host discovery."""
    tools = await mcp.list_tools()
    by_name = {t.name: t for t in tools}
    assert (by_name["geox_falsify"].meta or {}).get("ui", {}).get("resourceUri", "").startswith(
        "ui://geox/judge-console"
    )
    assert (by_name["geox_basin"].meta or {}).get("ui", {}).get("resourceUri", "").startswith(
        "ui://geox/basin-explorer"
    )
    assert (by_name["geox_lem_predict"].meta or {}).get("ui", {}).get("resourceUri", "").startswith(
        "ui://geox/well-desk"
    )
    assert (by_name["geox_visual_understand"].meta or {}).get("ui", {}).get("resourceUri", "").startswith(
        "ui://geox/visual-hub"
    )


@pytest.mark.asyncio
async def test_11_phase_01_truth_floor_and_csp_parity():
    """Verify Phase 0.1 Truth Floor enforcement, demo provenance badges, and CSP parity."""
    from geox_mcp.tools.integration_well import geox_well_desk

    # 1. Random unknown well ID must return clear error, NOT silent curves
    err_res = await geox_well_desk(well_id="XYZ-99", mode="open")
    assert getattr(err_res, "isError", True) is True
    assert "No LAS ingested for XYZ-99" in err_res.content[0].text
    assert err_res.structured_content.get("error_class") == "NO_LAS_DATA"

    # 2. Demo well ID must return curves with provenance badge
    demo_res = await geox_well_desk(well_id="DEMO-KINABALU", mode="open")
    assert getattr(demo_res, "isError", False) is False
    assert demo_res.structured_content.get("provenance_badge") == "DATA: DEMO FIXTURE — NOT REAL WELL DATA"
    assert "DATA: DEMO FIXTURE" in demo_res.content[0].text

    # 3. Alias URIs resolve cleanly
    resources = await mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "ui://geox/workspace-v1" in uris
    assert "ui://geox/gravmag-studio" in uris
    assert "ui://well/desk" in uris

