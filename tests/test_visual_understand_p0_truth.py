"""P0: visual_understand must HOLD without VLM — never invent structure (F2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from geox_mcp.tools.seismic_vision_ai import geox_visual_understand


def test_no_backend_holds_not_fabricates():
    img = Path("/root/GEOX/geox/seismic/rsi/seismic_section.jpg")
    assert img.is_file()
    r = geox_visual_understand(str(img), mode="full", vlm_client_callback=None)
    assert r.get("status") == "HOLD"
    assert r.get("error") == "NO_PERCEPTION_BACKEND"
    assert "discontinuities" not in r or not r.get("discontinuities")
    assert "417" not in str(r.get("discontinuities", []))
    assert r.get("local_verdict") == "QUALIFIED_CANDIDATE"
    assert r.get("seal_authority") == "arifOS_only"
    assert r.get("image_hash")


def test_missing_file_hold():
    r = geox_visual_understand("/tmp/does_not_exist_seismic_xyz.jpg")
    assert r.get("status") in ("HOLD", "VOID")
    assert r.get("ok") is False


@pytest.mark.asyncio
async def test_mcp_schema_accepts_image_path():
    from geox_mcp.server import create_app, mcp

    create_app()
    tools = await mcp.list_tools()
    t = next(x for x in tools if x.name == "geox_visual_understand")
    import json

    raw = json.dumps(
        {"desc": t.description, "params": str(getattr(t, "parameters", None)), "schema": getattr(t, "inputSchema", None)},
        default=str,
    )
    assert "image_path" in raw
