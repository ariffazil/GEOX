"""P2 2026-10-30 — p2-geox-governance-hold-reason-empty.

Lesson under test: "a HOLD gate must name its reason — an empty reason
is a blind gate." A GOV_BLOCK message must never be bare verdict+trace,
and every governed error envelope must carry a reason in its data.
"""

from __future__ import annotations

from geox_mcp.geox_middleware import (
    build_governed_error_envelope,
    compose_gov_block_error_message,
)


def test_bare_hold_is_impossible_when_reason_missing():
    """A guard that ships no reason still yields a NAMED client message."""
    msg = compose_gov_block_error_message(
        guard="",
        gov_verdict="HOLD",
        trace_id="gov-test0001",
        lane="",
        reason="",
        fix="",
        err={"code": -32003, "message": "INSUFFICIENT_AUTHORITY"},
        err_data={"verdict": "HOLD"},
    )
    assert "verdict=HOLD" in msg
    assert "trace=gov-test0001" in msg
    # named defect marker, not silence
    assert "REASON_EMPTY_GATE_DEFECT" in msg
    assert "p2-geox-governance-hold-reason-empty" in msg
    # the fallback reports what the guard DID send
    assert "data keys=['verdict']" in msg
    assert "UNKNOWN_GUARD" in msg


def test_named_reason_preserved_and_sliced_to_300():
    reason = "x" * 500
    msg = compose_gov_block_error_message(
        guard="AUTHORITY_GATE",
        gov_verdict="HOLD",
        trace_id="gov-test0002",
        lane="judgment",
        reason=reason,
        fix="re-auth with higher authority",
        err={"code": -32003, "message": "INSUFFICIENT_AUTHORITY"},
        err_data={"guard": "AUTHORITY_GATE", "reason": reason},
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
        detail="kernel HOLD: system floors F1+F8 red",
        trace_id="gov-test0003",
    )
    data = env["error"]["data"]
    assert data["reason"] == "kernel HOLD: system floors F1+F8 red"
    assert data["verdict"] == "HOLD"
    assert data["guard"] == "GOVERNANCE_BLOCK"
