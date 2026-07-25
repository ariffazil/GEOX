"""P1 session apex echo on interpret receipts (2026-07-25)."""

from __future__ import annotations

from geox_mcp.session_apex import (
    _sanitize_kernel_apex,
    attach_session_apex,
)


def test_sanitize_rejects_nominal() -> None:
    raw = {
        "G": {"value": 0.5, "status": "NOMINAL"},
        "C_dark": {"value": 0.31, "status": "MEASURED"},
        "W3": {"value": None, "status": "UNMEASURED"},
    }
    out = _sanitize_kernel_apex(raw)
    assert out["G"]["status"] == "UNMEASURED"
    assert out["G"]["value"] is None
    assert out["C_dark"]["status"] == "MEASURED"
    assert out["C_dark"]["value"] == 0.31
    assert out["C_dark"]["g_canonical_source"] == "arif_think.mode=apex"


def test_attach_session_apex_stamps_authority() -> None:
    r = attach_session_apex({"ok": True, "mode": "interpret_section"}, force=True)
    assert "apex_scalars" in r
    assert r["g_authority"] in ("arifos.health", "unmeasured")
    assert "arif_think" in r.get("g_note", "")
    assert r["apex_scalars"]["G"]["g_canonical_source"] == "arif_think.mode=apex"


def test_attach_strips_fabricated_g() -> None:
    r = attach_session_apex({"ok": True, "G": 0.5}, force=True)
    assert "G" not in r or r.get("G") != 0.5
    assert "apex_scalars" in r


def test_attach_passthrough_non_dict() -> None:
    assert attach_session_apex("x") == "x"
