import base64
import json
import os
from pathlib import Path

import pytest

from geox_mcp.tools_wiring import register_tools_on


# Create a mock MCP server/registry for testing
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name, **kwargs):
        def decorator(func):
            self.tools[name] = func
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


def test_well_desk_publish(mcp_registry):
    # 1. Create a dummy base64 PNG
    dummy_png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    image_base64 = base64.b64encode(dummy_png_bytes).decode("utf-8")

    metadata = {
        "well_id": "TEST-WELL-1",
        "porosity": "0.22",
        "sw": "0.35",
        "vsh": "0.12",
        "fluid": "brine",
    }

    # 2. Invoke the tool
    publish_tool = mcp_registry.tools["geox_well_desk_publish"]
    result = _run_async(
        publish_tool(
            well_id="TEST-WELL-1",
            image_base64=image_base64,
            metadata=metadata,
            session_id="test_session",
            actor_id="ARIF",
            trace_id="test_trace",
        )
    )

    # 3. Assertions
    assert result["ok"] is True
    assert "seal_token" in result
    assert result["well_id"] == "TEST-WELL-1"

    # Clean up output files if they were created
    filepath = Path(result["filepath"])
    assert filepath.exists()
    filepath.unlink()


def test_render_well_panel(mcp_registry):
    # Invoke the well-panel renderer
    render_tool = mcp_registry.tools["geox_render_well_panel"]
    result = _run_async(
        render_tool(
            well_id="BEK-2",
            depth_top=3000.0,
            depth_base=3100.0,
            session_id="test_session",
            actor_id="ARIF",
            trace_id="test_trace",
        )
    )

    # Assertions
    assert result["ok"] is True
    assert "seal_token" in result
    assert result["well_id"] == "BEK-2"

    # Validate tEXt chunk in saved PNG
    filepath = Path(result["filepath"])
    assert filepath.exists()

    # Read the file and search for metadata keywords to prove PIL PNGInfo injection succeeded
    content = filepath.read_bytes()
    assert b"provenance" in content
    assert b"scaffold" in content

    # Clean up output files
    filepath.unlink()
