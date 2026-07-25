"""P0-4 D.4+D.5 hardening 2026-07-25 · FI-008 — Envelope normalizer tests.

These tests assert the middleware-side guarantee that mutating tool
returns carry the audit-defined 5-status envelope contract.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import pytest

from geox_mcp.envelope_normalizer import (
    REQUIRED_ENVELOPE_FIELDS,
    envelope_is_complete,
    normalize_envelope_for_mutation,
    synthesize_envelope,
)
from geox_mcp.registry import is_mutating_call


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mutating_args_overwrite_true() -> dict:
    return {"overwrite": True, "actor_id": "ARIF", "session_id": "SEAL-x"}


@pytest.fixture
def mutating_args_prospect_seal() -> dict:
    return {"verdict": "seal", "actor_id": "ARIF", "session_id": "SEAL-x"}


@pytest.fixture
def mutating_args_claim_seal() -> dict:
    return {"mode": "seal", "actor_id": "ARIF", "session_id": "SEAL-x"}


# ── 1. envelope_is_complete ────────────────────────────────────────────────


def test_complete_envelope_passes() -> None:
    env = synthesize_envelope(
        tool_name="test",
        result={},
        actor_id="ARIF",
        session_id="SEAL-x",
    )
    assert envelope_is_complete(env) is True


def test_empty_envelope_fails() -> None:
    assert envelope_is_complete({}) is False


def test_partial_envelope_fails() -> None:
    env = synthesize_envelope(tool_name="t", result={}, actor_id="a", session_id="s")
    env["verification_status"] = ""  # clear one field
    assert envelope_is_complete(env) is False


def test_required_fields_are_documented() -> None:
    """The 5-status contract must remain documented."""
    expected = {
        "transport_status",
        "execution_status",
        "artifact_status",
        "verification_status",
        "governance_verdict",
        "claim_state",
    }
    assert set(REQUIRED_ENVELOPE_FIELDS) == expected


# ── 2. synthesize_envelope defaults ─────────────────────────────────────────


def test_synthesize_defaults_to_hold() -> None:
    """Synthesized envelopes MUST default governance_verdict to HOLD, never SEAL."""
    env = synthesize_envelope(
        tool_name="test", result={}, actor_id="a", session_id="s",
    )
    assert env["governance_verdict"] == "HOLD"


def test_synthesize_anonymous_when_no_actor() -> None:
    env = synthesize_envelope(
        tool_name="test", result={}, actor_id=None, session_id=None,
    )
    assert env["actor_id"] == "anonymous"
    assert env["session_id"] == "anonymous"


def test_synthesize_detects_error_status() -> None:
    env = synthesize_envelope(
        tool_name="test",
        result={"status": "ERROR"},
        actor_id="a", session_id="s",
    )
    assert env["execution_status"] == "ERROR"
    assert env["artifact_status"] == "ERROR"
    assert env["claim_state"] == "HYPOTHESIS"


# ── 3. normalize_envelope_for_mutation ────────────────────────────────────


def test_normalize_passthrough_for_readonly_tool() -> None:
    """Read-only tools pass through untouched."""
    result = {"status": "OK", "data": "some read-only output"}
    out = normalize_envelope_for_mutation(
        tool_name="geox_surface_status",
        result=result,
        arguments={},
    )
    assert out == result  # unchanged


def test_normalize_passthrough_for_complete_envelope() -> None:
    """Mutating tools WITH a complete envelope pass through unchanged."""
    env = synthesize_envelope(
        tool_name="geox_well_ingest",
        result={},
        actor_id="ARIF",
        session_id="SEAL-x",
        verification_status="VERIFIED",
        receipt_state="SEALED",
        receipt_ref="vault999://abc",
    )
    result = {"status": "OK", "envelope": env, "data": "ok"}
    out = normalize_envelope_for_mutation(
        tool_name="geox_well_ingest",
        result=result,
        arguments={"overwrite": True, "actor_id": "ARIF", "session_id": "SEAL-x"},
    )
    assert out == result  # unchanged


def test_normalize_downgrades_incomplete_envelope(
    mutating_args_overwrite_true: dict,
) -> None:
    """Mutating tool with no envelope returns OK → downgraded to ENVELOPE_INCOMPLETE."""
    result = {"status": "OK", "data": "some artifact"}
    out = normalize_envelope_for_mutation(
        tool_name="geox_well_ingest",
        result=result,
        arguments=mutating_args_overwrite_true,
    )
    assert out["status"] == "ENVELOPE_INCOMPLETE"
    assert "envelope" in out
    assert out["envelope"]["governance_verdict"] == "HOLD"
    assert out["envelope"]["verification_status"] == "UNVERIFIED"


def test_normalize_handles_prospect_seal(
    mutating_args_prospect_seal: dict,
) -> None:
    """The audit's 'seal mode' case must trigger the normalizer."""
    assert is_mutating_call("geox_prospect", mutating_args_prospect_seal) is True
    result = {"status": "OK"}
    out = normalize_envelope_for_mutation(
        tool_name="geox_prospect",
        result=result,
        arguments=mutating_args_prospect_seal,
    )
    assert out["status"] == "ENVELOPE_INCOMPLETE"


def test_normalize_handles_claim_seal(
    mutating_args_claim_seal: dict,
) -> None:
    """claim mode=seal is MUTATE per manifest — normalizer fires."""
    assert is_mutating_call("geox_claim", mutating_args_claim_seal) is True
    result = {"status": "OK"}
    out = normalize_envelope_for_mutation(
        tool_name="geox_claim",
        result=result,
        arguments=mutating_args_claim_seal,
    )
    assert out["status"] == "ENVELOPE_INCOMPLETE"


def test_normalize_preserves_partial_envelope_data() -> None:
    """If tool produced a partial envelope, preserve its fields."""
    partial = {
        "transport_status": "OK",
        "verification_status": "FAILED",
        "receipt": {"state": "PENDING", "ref": None},
    }
    result = {"status": "OK", "envelope": partial}
    out = normalize_envelope_for_mutation(
        tool_name="geox_well_ingest",
        result=result,
        arguments={"overwrite": True, "actor_id": "ARIF", "session_id": "SEAL-x"},
    )
    env = out["envelope"]
    assert env["transport_status"] == "OK"
    assert env["verification_status"] == "FAILED"  # preserved from partial
    assert env["receipt"]["state"] == "PENDING"
    assert env["governance_verdict"] == "HOLD"


def test_normalize_non_dict_result_passes_through() -> None:
    """Strings, lists, etc. pass through unchanged."""
    out = normalize_envelope_for_mutation(
        tool_name="geox_well_ingest",
        result="just a string",
        arguments={"overwrite": True},
    )
    assert out == "just a string"


# ── 4. Contract guarantee: every mutating tool CANNOT return OK without envelope


def test_no_mutating_tool_can_falsely_succeed() -> None:
    """The audit's false-success class is now structurally impossible.

    Any mutating tool that returns status=OK without an envelope gets
    downgraded to ENVELOPE_INCOMPLETE. The agent cannot claim completion
    without producing verifiable evidence.
    """
    # Simulate every mutating tool returning status=OK with no envelope.
    cases = [
        ("geox_well_ingest", {"overwrite": True}),
        ("geox_prospect", {"verdict": "seal"}),
        ("geox_claim", {"mode": "seal"}),
        ("geox_evidence", {"forbidden_uses": ["x"]}),
    ]
    for tool, args in cases:
        assert is_mutating_call(tool, args), f"setup: {tool} should be mutating"
        result = {"status": "OK"}
        out = normalize_envelope_for_mutation(
            tool_name=tool, result=result, arguments=args,
        )
        assert out["status"] == "ENVELOPE_INCOMPLETE", (
            f"{tool} with mutating args returned status=OK without downgrade"
        )
        assert "envelope" in out
        assert out["envelope"]["governance_verdict"] == "HOLD"
