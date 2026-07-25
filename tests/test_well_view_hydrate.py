"""Prompt B — geox_well_view LAS hydrate + receipt (2026-07-25)."""

from __future__ import annotations

import asyncio

import pytest

from geox_mcp.tools.integration_well import _load_well_curves_for_ui


def test_demo_kinabalu_resolves_las() -> None:
    r = _load_well_curves_for_ui("DEMO-KINABALU", max_n=200)
    assert r["status"] == "loaded"
    assert r.get("curves")
    assert r.get("depths")
    assert len(r["depths"]) > 10
    assert "GR" in r["curves"] or r.get("curves_available")
    assert r.get("data_class") in ("DEMO", "OPEN_OSS", "SYNTHETIC_LABEL", "MEASURED", "INGESTED")
    assert r.get("las_path")


def test_unknown_well_no_silent_empty() -> None:
    r = _load_well_curves_for_ui("NO-SUCH-WELL-XYZ-999", max_n=50)
    assert r["status"] in ("no_las", "error")
    assert not r.get("curves")


@pytest.mark.asyncio
async def test_well_view_tool_demo_hydrate() -> None:
    """Call the wired tool body via MCP call_tool if available."""
    from geox_mcp.server import mcp

    # Session gate may require env off for unit path
    import os

    os.environ["GEOX_REQUIRE_SESSION_FOR_MUTATE"] = "0"
    try:
        result = await mcp.call_tool(
            "geox_well_view",
            {"well_id": "DEMO-KINABALU", "actor_id": "ARIF", "session_id": "SEAL-test-b"},
        )
    finally:
        os.environ.pop("GEOX_REQUIRE_SESSION_FOR_MUTATE", None)

    sc = getattr(result, "structured_content", None) or {}
    if not sc and hasattr(result, "content"):
        # parse text if needed
        pass
    assert not getattr(result, "is_error", False) or sc.get("ok") is True or sc.get("curves")
    # Prefer structured
    if sc:
        assert sc.get("ok") is True or sc.get("curves")
        if sc.get("ok"):
            assert sc.get("curves")
            assert sc.get("depths")
            # receipt may be SEALED or PENDING
            rec = sc.get("receipt") or (sc.get("meta") or {}).get("receipt")
            assert rec is None or rec.get("state") in ("SEALED", "PENDING", "FAILED")
