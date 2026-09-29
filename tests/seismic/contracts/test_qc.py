"""Tests for QC receipt contract."""
from __future__ import annotations

import pytest

from geox.seismic.contracts import FailureMode, QCReceipt, ValidationCheck


def _valid_kwargs(verdict: str = "PASS"):
    return {
        "artifact_ref": "geox://derived/coherence/test",
        "qc_id": "geox://qc/test-qc-1",
        "created_by": "kimi-code/FI-008",
        "verdict": verdict,
        "checks": [
            ValidationCheck(
                name="edge_mask_complete",
                passed=True,
                metric_name="edge_coverage",
                metric_value=0.95,
                threshold=0.9,
            ),
        ],
        "code_version": "1.0.0",
    }


class TestQCReceipt:
    def test_valid_receipt(self):
        q = QCReceipt(**_valid_kwargs())
        assert q.verdict == "PASS"
        assert len(q.checks) == 1
        assert q.has_hold_failures() is False

    def test_hold_failure_detected(self):
        kw = _valid_kwargs(verdict="HOLD")
        kw["failures"] = [
            FailureMode(code="polarity_unknown", severity="HOLD", message="Polarity not registered")
        ]
        q = QCReceipt(**kw)
        assert q.has_hold_failures() is True

    def test_fail_severity_detected(self):
        kw = _valid_kwargs(verdict="FAIL")
        kw["failures"] = [
            FailureMode(code="horizon_untrackable", severity="FAIL", message="No coherent reflectors")
        ]
        q = QCReceipt(**kw)
        assert q.has_hold_failures() is True

    def test_warn_only_not_hold(self):
        kw = _valid_kwargs(verdict="CAUTION")
        kw["failures"] = [
            FailureMode(code="edge_halo", severity="WARN", message="Edge halo detected")
        ]
        q = QCReceipt(**kw)
        assert q.has_hold_failures() is False

    def test_duplicate_check_names_rejected(self):
        kw = _valid_kwargs()
        kw["checks"] = [
            ValidationCheck(name="edge_mask_complete", passed=True),
            ValidationCheck(name="edge_mask_complete", passed=False),
        ]
        with pytest.raises(ValueError):
            QCReceipt(**kw)

    def test_duplicate_failure_codes_rejected(self):
        kw = _valid_kwargs()
        kw["failures"] = [
            FailureMode(code="polarity_unknown", severity="HOLD", message="a"),
            FailureMode(code="polarity_unknown", severity="WARN", message="b"),
        ]
        with pytest.raises(ValueError):
            QCReceipt(**kw)

    def test_code_version_pattern(self):
        kw = _valid_kwargs()
        kw["code_version"] = "1.0"  # not semver
        with pytest.raises(ValueError):
            QCReceipt(**kw)

    def test_provenance_chain_via_parent_qc(self):
        kw = _valid_kwargs()
        kw["parent_qc_ref"] = "geox://qc/previous-qc"
        q = QCReceipt(**kw)
        assert q.parent_qc_ref == "geox://qc/previous-qc"

    def test_extra_field_rejected(self):
        kw = _valid_kwargs()
        kw["unknown_field"] = "bad"
        with pytest.raises(ValueError):
            QCReceipt(**kw)
