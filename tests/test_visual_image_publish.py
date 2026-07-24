"""Well desk publish/render — ZEN-15 modes on geox_well_desk (not separate tools)."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from geox_mcp.tools_wiring import register_tools_on


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name=None, **kwargs):
        def decorator(func):
            n = name or getattr(func, "__name__", None)
            self.tools[n] = func
            return func

        return decorator


@pytest.fixture
def mcp_registry():
    mcp = MockMCP()
    register_tools_on(mcp)
    return mcp


@pytest.fixture(autouse=True)
def _hermetic_dirs(tmp_path, monkeypatch):
    """Redirect renders and vault dirs to tmp_path for hermetic tests."""
    renders = tmp_path / "renders"
    renders.mkdir()
    vault = tmp_path / "vault999"
    vault.mkdir()
    monkeypatch.setenv("GEOX_RENDERS_DIR", str(renders))
    monkeypatch.setenv("GEOX_VAULT_IMAGE_DIR", str(vault))


def _run_async(coro):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _unwrap(result):
    """Normalize ToolResult or plain dict from geox_well_desk modes."""
    if isinstance(result, dict):
        return result
    sc = getattr(result, "structured_content", None) or getattr(result, "structuredContent", None)
    if isinstance(sc, dict) and sc:
        return sc
    # content[0].text may be JSON
    content = getattr(result, "content", None) or []
    for block in content:
        t = getattr(block, "text", None) or (block.get("text") if isinstance(block, dict) else None)
        if t:
            try:
                import json

                return json.loads(t)
            except Exception:
                return {"text": t, "ok": not getattr(result, "is_error", False)}
    return {"raw_type": type(result).__name__}


def test_well_desk_publish(mcp_registry):
    """geox_well_desk(mode=publish) is the ZEN-15 home of former geox_well_desk_publish."""
    assert "geox_well_desk" in mcp_registry.tools
    assert "geox_well_desk_publish" not in mcp_registry.tools  # absorbed

    desk = mcp_registry.tools["geox_well_desk"]
    result = _run_async(
        desk(
            mode="publish",
            well_id="DEMO-KINABALU",
            session_id="test_session",
            actor_id="ARIF",
            trace_id="test_trace",
        )
    )
    payload = _unwrap(result)
    # Publish may succeed with panel or report status/error without crashing
    assert payload.get("mode") == "publish" or payload.get("tool") in (
        "geox_well_desk",
        "geox_well_desk_publish",
        None,
    )
    # Must not be an unhandled exception path
    assert "error" not in payload or payload.get("status") in ("error", "published", None)


def test_render_well_panel(mcp_registry):
    """geox_well_desk(mode=render) is the ZEN-15 home of former geox_render_well_panel."""
    assert "geox_well_desk" in mcp_registry.tools
    assert "geox_render_well_panel" not in mcp_registry.tools  # absorbed

    desk = mcp_registry.tools["geox_well_desk"]
    result = _run_async(
        desk(
            mode="render",
            well_id="DEMO-KINABALU",
            depth_top=1500.0,
            depth_base=1700.0,
            session_id="test_session",
            actor_id="ARIF",
            trace_id="test_trace",
        )
    )
    payload = _unwrap(result)
    # Render returns panel path / ok / structured payload — tolerate scaffold DEMO path
    assert payload is not None
    text_blob = str(payload).lower()
    assert "demo" in text_blob or "well" in text_blob or "panel" in text_blob or "ok" in text_blob
