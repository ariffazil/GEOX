"""Claimed identities must validate; anonymous evidence remains explicit."""

from __future__ import annotations

from geox_mcp import organ_governance
from geox_mcp.session_enforcement import ValidationResult


def test_anonymous_evidence_lane_remains_read_only_accessible():
    verdict, error = organ_governance._check_identity_propagation(
        "geox_evidence",
        session_id=None,
        actor_id="geox-governed",
    )

    assert verdict == "SEAL"
    assert error is None


def test_fabricated_claimed_session_is_held(monkeypatch):
    monkeypatch.setattr(
        organ_governance,
        "validate_session",
        lambda *_args, **_kwargs: ValidationResult(
            ok=False,
            error_code="SESSION_INVALID",
            error_message="arifOS rejected fabricated session",
        ),
    )

    verdict, error = organ_governance._check_identity_propagation(
        "geox_evidence",
        session_id="SEAL-deadbeef00000000",
        actor_id="fake-actor",
    )

    assert verdict == "HOLD"
    assert error is not None
    assert b'"message":"SESSION_INVALID"' in error.body
    assert b'"guard":"SESSION_BINDING"' in error.body


def test_valid_claimed_session_preserves_actor_binding(monkeypatch):
    monkeypatch.setattr(
        organ_governance,
        "validate_session",
        lambda *_args, **_kwargs: ValidationResult(
            ok=True,
            actor="ARIF",
            authority="OBSERVE_ONLY",
            session={"session_id": "SEAL-valid-session-0001"},
        ),
    )

    verdict, error = organ_governance._check_identity_propagation(
        "geox_evidence",
        session_id="SEAL-valid-session-0001",
        actor_id="ARIF",
    )

    assert verdict == "SEAL"
    assert error is None


def test_signed_token_is_replaced_with_canonical_session(monkeypatch):
    monkeypatch.setattr(
        organ_governance,
        "validate_session",
        lambda *_args, **_kwargs: ValidationResult(
            ok=True,
            actor="ARIF",
            authority="OBSERVE_ONLY",
            session={"sid": "SEAL-canonical-session-0001", "actor": "ARIF"},
        ),
    )
    arguments = {
        "session_id": "sct_v1.payload.signature",
        "actor_id": "ARIF",
    }

    verdict, error = organ_governance._check_identity_propagation(
        "geox_evidence",
        session_id=arguments["session_id"],
        actor_id=arguments["actor_id"],
        arguments=arguments,
    )

    assert verdict == "SEAL"
    assert error is None
    assert arguments["session_id"] == "SEAL-canonical-session-0001"
    assert not arguments["session_id"].startswith("sct_v1.")
