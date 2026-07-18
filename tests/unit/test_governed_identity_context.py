"""Governed ingress identity reaches envelopes even when legacy tools omit kwargs."""

from geox_core.enums.statuses import get_standard_envelope
from geox_core.identity_context import GEOX_IDENTITY_CONTEXT


def test_standard_envelope_uses_governed_identity_context():
    token = GEOX_IDENTITY_CONTEXT.set(
        {
            "session_id": "SEAL-real-session-0001",
            "actor_id": "ARIF",
            "trace_id": "trace-real-0001",
        }
    )
    try:
        result = get_standard_envelope({"tool": "geox_evidence"})
    finally:
        GEOX_IDENTITY_CONTEXT.reset(token)

    assert result["session_id"] == "SEAL-real-session-0001"
    assert result["trace_id"] == "trace-real-0001"
    assert result["audit_receipt"]["session_id"] == "SEAL-real-session-0001"
    assert result["audit_receipt"]["actor_id"] == "ARIF"
