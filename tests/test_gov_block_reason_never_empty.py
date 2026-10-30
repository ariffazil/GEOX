"""P2 2026-10-30 — p2-geox-governance-hold-reason-empty.

Lessons under test:
1. "A HOLD gate must name its reason — an empty reason is a blind gate."
   A GOV_BLOCK message must never be bare verdict+trace.
2. PUBLIC-EDGE ALLOWLIST (Arif review): no internal key names, no raw
   error detail. reason = missing | "" | whitespace | None | non-string
   all normalize to a withheld marker; err/err_data never surface.
"""

from __future__ import annotations

from geox_mcp.geox_middleware import (
    build_governed_error_envelope,
    compose_gov_block_error_message,
)


def _compose(reason) -> str:
    return compose_gov_block_error_message(
        guard="",
        gov_verdict="HOLD",
        trace_id="gov-test0001",
        lane="",
        reason=reason,
        fix="",
    )


def test_reason_missing_empty_whitespace_none_normalize_to_withheld():
    for bad in ("", "   ", "\t\n", None):
        msg = _compose(bad)
        assert "verdict=HOLD" in msg
        assert "trace=gov-test0001" in msg
        assert "REASON_WITHHELD" in msg
        assert "p2-geox-governance-hold-reason-empty" in msg
        assert "UNKNOWN_GUARD" in msg


def test_reason_non_string_normalizes_to_withheld_no_leak():
    for bad in ({"internal_key": "secret-ish"}, ["raw", "list"], 12345, b"bytes"):
        msg = _compose(bad)
        assert "REASON_WITHHELD" in msg
        # non-string content must never surface on the public edge
        assert "internal_key" not in msg
        assert "raw" not in msg
        assert "12345" not in msg
        assert "b'bytes'" not in msg


def test_no_internal_key_names_or_raw_detail_anywhere():
    msg = compose_gov_block_error_message(
        guard="",
        gov_verdict="HOLD",
        trace_id="gov-test0002",
        lane="judgment",
        reason="",
        fix="",
    )
    # the earlier draft leaked these — regression-guard them
    assert "data keys" not in msg
    assert "err_data" not in msg
    assert "error code=" not in msg


def test_named_reason_preserved_and_sliced_to_300():
    reason = "x" * 500
    msg = compose_gov_block_error_message(
        guard="AUTHORITY_GATE",
        gov_verdict="HOLD",
        trace_id="gov-test0003",
        lane="judgment",
        reason=reason,
        fix="re-auth with higher authority",
    )
    assert "AUTHORITY_GATE" in msg
    assert "lane=judgment" in msg
    assert "x" * 300 in msg
    assert "x" * 301 not in msg  # P3 slice honoured
    assert msg.endswith("fix: re-auth with higher authority")


def test_governed_envelope_data_carries_reason():
    """build_governed_error_envelope data must name its reason (≤300)."""
    env = build_governed_error_envelope(
        tool_name="geox_claim",
        error_class="GOVERNANCE_BLOCK",
        detail="kernel HOLD: system floors red",
        trace_id="gov-test0004",
    )
    data = env["error"]["data"]
    assert data["reason"] == "kernel HOLD: system floors red"
    assert data["verdict"] == "HOLD"
    assert data["guard"] == "GOVERNANCE_BLOCK"
