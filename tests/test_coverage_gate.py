"""
Tests for Coverage Gate — Component #36: UNKNOWN_SPACE_MAPPING
DITEMPA BUKAN DIBERI — Forged, not given

Tests the 4-layer coverage check:
  sensing → recognition → interpretation → institutional_memory

Canonical case: Bekok Deep-1 (SCAR-6)
  - Sensing PASS, recognition/interpretation/memory FAIL
  - This pattern must trigger HOLD

Source: Arif Fazil (F13 SOVEREIGN), 2026-08-13
"""

import pytest
from geox_core.gates.coverage_gate import (
    CoverageLevel,
    CoverageManifest,
    LayerStatus,
    InterpretationLayer,
    check_coverage_gate,
    requires_coverage,
)


class TestCoverageScoring:
    """Quantitative coverage score tests."""

    def test_sufficient_coverage(self):
        """8 RFT points across 400m interval = score 2.0 (clamped to 1.0)."""
        manifest = CoverageManifest(
            observation_count=8,
            interval_thickness_100m_bins=4,
            confidence=0.85,
        )
        result = check_coverage_gate(manifest, confidence=0.85)
        assert result.level == CoverageLevel.SUFFICIENT
        assert result.status == "PASS"

    def test_partial_coverage(self):
        """2 RFT points across 800m = score 0.25 → SPARSE actually."""
        manifest = CoverageManifest(
            observation_count=2,
            interval_thickness_100m_bins=8,
            confidence=0.72,
        )
        result = check_coverage_gate(manifest, confidence=0.72)
        # 2/8 = 0.25 → SPARSE
        assert result.level == CoverageLevel.SPARSE
        assert "insufficient_observational_coverage" in result.hold_reasons

    def test_void_coverage(self):
        """0 observations = VOID = 888_HOLD."""
        manifest = CoverageManifest(
            observation_count=0,
            interval_thickness_100m_bins=10,
            confidence=0.81,
        )
        result = check_coverage_gate(manifest, confidence=0.81)
        assert result.level == CoverageLevel.VOID
        assert result.status == "888_HOLD"
        assert "void_coverage_no_observational_basis" in result.hold_reasons
        assert result.epistemic_override == "HYPOTHESIS"


class TestConfidenceOutrunsEvidence:
    """Tests for confidence > coverage + 0.30 override."""

    def test_confidence_outruns_evidence(self):
        """confidence=0.81, coverage=0.12 → gap 0.69 → override."""
        manifest = CoverageManifest(
            observation_count=1,
            interval_thickness_100m_bins=8,
            confidence=0.81,
        )
        result = check_coverage_gate(manifest, confidence=0.81)
        assert result.confidence_outruns_evidence
        assert "confidence_outruns_evidence" in result.hold_reasons
        assert result.epistemic_override == "HYPOTHESIS"

    def test_confidence_aligned_with_coverage(self):
        """confidence=0.72, coverage=0.75 → gap 0.03 → no override."""
        manifest = CoverageManifest(
            observation_count=6,
            interval_thickness_100m_bins=8,
            confidence=0.72,
        )
        result = check_coverage_gate(manifest, confidence=0.72)
        assert not result.confidence_outruns_evidence
        assert result.status == "PASS"


class TestBekokDeep1Scenario:
    """The canonical SCAR-6 scenario: sensing PASS, others FAIL."""

    def test_bekok_deep_1_pattern(self):
        """
        Sensing: PASS (3D seismic, historical well, mud logging)
        Recognition: FAIL (bright spot = DHI not hazard)
        Interpretation: FAIL (pressure = formation not gas)
        Institutional memory: FAIL (report compressed)
        → Must trigger HOLD with all 4 layers reported.
        """
        manifest = CoverageManifest(
            observation_count=0,
            interval_thickness_100m_bins=15,
            confidence=0.85,
            sensing=LayerStatus(
                layer=InterpretationLayer.SENSING,
                status="PASS",
                evidence=[
                    "3D seismic (bright spot anomaly present)",
                    "historical well operational issues",
                    "mud logging reports (pressure increase visible)",
                ],
            ),
            recognition=LayerStatus(
                layer=InterpretationLayer.RECOGNITION,
                status="FAIL",
                evidence=["Bright spot interpreted as DHI not hazard"],
                root_cause="Bright spot seen as hydrocarbon indicator, not shallow gas hazard",
            ),
            interpretation_layer=LayerStatus(
                layer=InterpretationLayer.INTERPRETATION,
                status="FAIL",
                evidence=["Mud logging pressure increase attributed to formation"],
                root_cause="Pressure increase not connected to shallow gas mechanism",
            ),
            institutional_memory=LayerStatus(
                layer=InterpretationLayer.INSTITUTIONAL_MEMORY,
                status="FAIL",
                evidence=["Historical well report vague on incident details"],
                root_cause="Institutional reporting compressed operational reality",
            ),
        )
        result = check_coverage_gate(manifest, confidence=0.85)

        # Must be HOLD
        assert result.status == "888_HOLD"

        # Must report all 4 layers
        assert result.layer_statuses["sensing"] == "PASS"
        assert result.layer_statuses["recognition"] == "FAIL"
        assert result.layer_statuses["interpretation_layer"] == "FAIL"
        assert result.layer_statuses["institutional_memory"] == "FAIL"

        # Must flag sensing-exists-but-not-recognized pattern
        assert "sensing_exists_but_not_recognized_or_interpreted" in result.hold_reasons

        # Must include recognition/interpretation/memory failures
        assert any("recognition_failure" in r for r in result.hold_reasons)
        assert any("interpretation_failure" in r for r in result.hold_reasons)
        assert any("institutional_memory_failure" in r for r in result.hold_reasons)

        # Confidence must outrun evidence
        assert result.confidence_outruns_evidence
        assert result.epistemic_override == "HYPOTHESIS"


class TestCoverageGateDecorator:
    """Tests for @requires_coverage decorator."""

    def test_decorator_blocks_below_minimum(self):
        @requires_coverage(min_level=CoverageLevel.SUFFICIENT)
        def predict_pp(depth, coverage_manifest=None, confidence=0.0):
            return {"pore_pressure_mpa": 50.0}

        manifest = CoverageManifest(
            observation_count=2,
            interval_thickness_100m_bins=10,
            confidence=0.5,
        )
        result = predict_pp(3000, coverage_manifest=manifest, confidence=0.5)
        assert result["status"] == "888_HOLD"
        assert result["reason"] == "coverage_required"

    def test_decorator_blocks_on_layer_failure(self):
        @requires_coverage(min_level=CoverageLevel.PARTIAL)
        def predict_pp(depth, coverage_manifest=None, confidence=0.0):
            return {"pore_pressure_mpa": 50.0}

        # Sensing PASS but recognition FAIL
        manifest = CoverageManifest(
            observation_count=5,
            interval_thickness_100m_bins=5,
            confidence=0.7,
            sensing=LayerStatus(
                layer=InterpretationLayer.SENSING,
                status="PASS",
            ),
            recognition=LayerStatus(
                layer=InterpretationLayer.RECOGNITION,
                status="FAIL",
                root_cause="Signal not recognized",
            ),
        )
        result = predict_pp(3000, coverage_manifest=manifest, confidence=0.7)
        assert result["status"] == "888_HOLD"
        assert result["reason"] == "coverage_layer_failure"

    def test_decorator_passes_with_good_coverage(self):
        @requires_coverage(min_level=CoverageLevel.PARTIAL)
        def predict_pp(depth, coverage_manifest=None, confidence=0.0):
            return {"pore_pressure_mpa": 50.0}

        manifest = CoverageManifest(
            observation_count=8,
            interval_thickness_100m_bins=5,
            confidence=0.85,
        )
        result = predict_pp(3000, coverage_manifest=manifest, confidence=0.85)
        assert "pore_pressure_mpa" in result
        assert result["pore_pressure_mpa"] == 50.0

    def test_no_manifest_returns_hold(self):
        @requires_coverage()
        def predict_pp(depth, coverage_manifest=None, confidence=0.0):
            return {"pore_pressure_mpa": 50.0}

        result = predict_pp(3000)
        assert result["status"] == "888_HOLD"
