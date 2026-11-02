"""
tests/test_envelope_honesty.py — S3.3 Envelope Honesty Invariant Test

Enforces:
  ok=False => is_error: True, execution_status: FAILED, artifact_status: REJECTED
"""

import pytest
from geox_mcp.geox_middleware import GeoxGovernanceMiddleware


def test_envelope_honesty_on_failure():
    result = {"ok": False, "error": "Test failure condition"}
    gov_envelope = {
        "artifact_id": "test:artifact:001",
        "session_id": "test-session",
        "actor_id": "test-actor",
        "gate_verdict": "TRANSPORT_OK",
    }
    injected = GeoxGovernanceMiddleware._inject_evidence_envelope(result, "geox_test_tool", gov_envelope)
    
    assert injected["_evidence_envelope"] is not None
    env = injected["_evidence_envelope"]["_envelope"]
    receipt = injected["_evidence_envelope"]["_receipt"]

    assert env["execution_status"] == "FAILED"
    assert env["artifact_status"] == "REJECTED"
    assert receipt["is_error"] is True
    assert receipt["error_detail"] == "Test failure condition"


def test_envelope_honesty_on_success():
    result = {"ok": True, "data": "Test payload"}
    gov_envelope = {
        "artifact_id": "test:artifact:002",
        "session_id": "test-session",
        "actor_id": "test-actor",
        "gate_verdict": "TRANSPORT_OK",
    }
    injected = GeoxGovernanceMiddleware._inject_evidence_envelope(result, "geox_test_tool", gov_envelope)
    
    assert injected["_evidence_envelope"] is not None
    env = injected["_evidence_envelope"]["_envelope"]
    receipt = injected["_evidence_envelope"]["_receipt"]

    assert env["execution_status"] == "COMPLETED"
    assert env["artifact_status"] == "CREATED"
    assert receipt["is_error"] is False
