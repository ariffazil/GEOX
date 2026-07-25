"""P1 Ext_witness stamps + GEOX_REQUIRE_LIVE fail-closed (2026-07-25)."""

from __future__ import annotations

import os

import pytest

from geox_mcp.ext_witness_stamp import (
    RequireLiveError,
    enforce_require_live,
    infer_mode,
    is_ext_witness_ready,
    normalize_mode,
    stamp_and_gate,
    stamp_ext_witness,
)


def test_normalize_mode_aliases() -> None:
    assert normalize_mode("offline") == "offline_stub"
    assert normalize_mode("LIVE") == "live"
    assert normalize_mode(None) == "unknown"


def test_ext_witness_ready_only_live() -> None:
    assert is_ext_witness_ready("live") is True
    assert is_ext_witness_ready("gws_live") is True
    assert is_ext_witness_ready("offline_stub") is False
    assert is_ext_witness_ready("derived") is False
    assert is_ext_witness_ready("unknown") is False


def test_stamp_preserves_offline_stub() -> None:
    r = stamp_ext_witness(
        {"ok": True, "mode": "offline_stub", "note": "stub"},
        tool_name="geox_earthquake_catalog",
    )
    assert r["mode"] == "offline_stub"
    assert r["data_mode"] == "offline_stub"
    assert r["ext_witness_ready"] is False
    assert r["provenance"]["mode"] == "offline_stub"
    assert r["provenance"]["ext_witness_ready"] is False


def test_stamp_live_ready() -> None:
    r = stamp_ext_witness(
        {"ok": True, "mode": "live", "count": 3},
        tool_name="geox_earthquake_catalog",
    )
    assert r["ext_witness_ready"] is True
    assert r["data_mode"] == "live"


def test_stamp_never_invents_live() -> None:
    r = stamp_ext_witness({"ok": True, "status": "OK"}, tool_name="geox_petrophysics")
    assert r["data_mode"] != "live"
    assert r["ext_witness_ready"] is False


def test_infer_earth_surface_defaults_stub() -> None:
    assert infer_mode("geox_earthquake_catalog", {"ok": True}) == "offline_stub"


def test_infer_interpret_defaults_derived() -> None:
    assert infer_mode("geox_seismic_interpret", {"ok": True}) == "derived"


def test_preserve_tool_operation_mode() -> None:
    """interpret_section is operation mode; data_mode is derived."""
    r = stamp_ext_witness(
        {"ok": True, "mode": "interpret_section"},
        tool_name="geox_seismic_interpret",
    )
    assert r["mode"] == "interpret_section"
    assert r["data_mode"] == "derived"
    assert r["ext_witness_ready"] is False


def test_require_live_off_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEOX_REQUIRE_LIVE", raising=False)
    r = stamp_and_gate(
        {"ok": True, "mode": "offline_stub"},
        tool_name="geox_earthquake_catalog",
    )
    assert r["ext_witness_ready"] is False


def test_require_live_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEOX_REQUIRE_LIVE", "1")
    with pytest.raises(RequireLiveError) as ei:
        stamp_and_gate(
            {"ok": True, "mode": "offline_stub"},
            tool_name="geox_earthquake_catalog",
        )
    assert ei.value.mode == "offline_stub"
    assert "geox_earthquake_catalog" in str(ei.value)


def test_require_live_allows_live(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEOX_REQUIRE_LIVE", "1")
    r = stamp_and_gate(
        {"ok": True, "mode": "live"},
        tool_name="geox_earthquake_catalog",
    )
    assert r["ext_witness_ready"] is True


def test_enforce_require_live_noop_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEOX_REQUIRE_LIVE", raising=False)
    r = {"mode": "offline_stub", "ext_witness_ready": False}
    assert enforce_require_live(r, tool_name="t") is r


def test_stamp_pydantic_like_model() -> None:
    class _M:
        def model_dump(self, mode: str = "python"):  # noqa: A003
            return {"ok": True, "mode": "offline_stub", "count": 1}

    r = stamp_ext_witness(_M(), tool_name="geox_earthquake_catalog")
    assert isinstance(r, dict)
    assert r["ext_witness_ready"] is False
    assert r["data_mode"] == "offline_stub"


def test_non_dict_passthrough() -> None:
    assert stamp_ext_witness("raw", tool_name="x") == "raw"


def test_stamp_preserves_fastmcp_toolresult_to_mcp_result() -> None:
    """P1 regression: middleware must not strip ToolResult.to_mcp_result().

    FastMCP wire path does ``return result.to_mcp_result()``. Stamping a raw
    model_dump into a dict crashes every tools/call.
    """
    from fastmcp.tools.base import ToolResult

    tr = ToolResult(
        structured_content={
            "ok": True,
            "status": "OK",
            "mode": "offline_stub",
            "tool": "geox_surface_status",
        }
    )
    out = stamp_and_gate(tr, tool_name="geox_surface_status")
    assert hasattr(out, "to_mcp_result"), f"lost to_mcp_result: {type(out)}"
    assert not isinstance(out, dict)
    wire = out.to_mcp_result()
    assert wire is not None
    sc = getattr(out, "structured_content", None) or {}
    assert sc.get("ext_witness_ready") is False
    assert sc.get("data_mode") == "offline_stub"


def test_stamp_toolresult_live_ready() -> None:
    from fastmcp.tools.base import ToolResult

    tr = ToolResult(structured_content={"ok": True, "mode": "live", "count": 2})
    out = stamp_and_gate(tr, tool_name="geox_earthquake_catalog")
    assert hasattr(out, "to_mcp_result")
    assert out.structured_content.get("ext_witness_ready") is True
    out.to_mcp_result()  # must not raise
