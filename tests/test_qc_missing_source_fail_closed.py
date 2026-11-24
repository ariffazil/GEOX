"""P0.1 regression lock — a missing LAS source must never yield a QC_VERIFIED receipt.

Measured defect (2026-11-24, FI-003): with ``las_path`` absent, ``geox_data_qc_bundle``
recorded ``qc_passed=True, claim_state="QC_VERIFIED"`` on the artifact entry and returned
an envelope carrying ``qc_passed=True, claim_state="INGESTED"``. Artifact existence was
valid; *evidence availability* was not — so QC never ran.

The distinction this locks in:
    artifact_status == REGISTERED_NO_PATH   (the artifact exists)
    qc_passed       == False                (no evidence was assessed)
    claim_state     == NO_VALID_EVIDENCE
    execution_status== ERROR + HOLD         (the call could not do its job)
"""

from __future__ import annotations

import asyncio

import pytest

from geox_core.enums.statuses import ExecutionStatus, GovernanceStatus
from geox_mcp.tools.kernel import _registry
from geox_mcp.tools.qc import geox_data_qc_bundle

REF = "well_las:P01-MISSING-SOURCE-CANARY"


@pytest.fixture()
def missing_source_artifact(tmp_path, monkeypatch):
    """An artifact registered with a las_path that does not exist."""
    monkeypatch.setattr(_registry, "_persist_artifact_registry", lambda: None)
    _registry._artifact_store[REF] = {
        "artifact_ref": REF,
        "las_path": str(tmp_path / "absent.las"),
        "aliases": [],
        "artifact_type": "well_log",
    }
    yield REF
    _registry._artifact_store.pop(REF, None)


def test_envelope_reports_no_valid_evidence(missing_source_artifact):
    envelope = asyncio.run(geox_data_qc_bundle(missing_source_artifact))

    assert envelope["claim_state"] == "NO_VALID_EVIDENCE"
    assert envelope["execution_status"] == ExecutionStatus.ERROR.value
    assert envelope["governance_status"] == GovernanceStatus.HOLD.value

    payload = envelope["primary_artifact"]
    assert payload["qc_passed"] is False, "missing source must not report qc_passed=True"
    assert payload["qc_overall"] == "NOT_RUN"
    assert payload["claim_state"] == "NO_VALID_EVIDENCE"
    assert "SOURCE_MISSING" in payload["flags"]


def test_stored_receipt_is_also_fail_closed(missing_source_artifact):
    """The assertion that would have caught the bug: the STORE, not just the envelope."""
    asyncio.run(geox_data_qc_bundle(missing_source_artifact))

    stored = _registry._artifact_store[missing_source_artifact]["latest_qc"]
    assert stored["qc_passed"] is False
    assert stored["qc_overall"] == "NOT_RUN"
    assert stored["claim_state"] == "NO_VALID_EVIDENCE"
    assert "SOURCE_MISSING" in stored["flags"]
