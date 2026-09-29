"""Tests for polarity/phase register."""
from __future__ import annotations

import pytest

from geox.seismic.contracts import (
    POLARITY_SIGN,
    PhaseShiftEstimate,
    PolarityPhaseRegister,
)


class TestPolarityPhaseRegister:
    def test_valid_register_seg_normal(self):
        r = PolarityPhaseRegister(
            register_id="geox://artifact/polarity-f3",
            polarity="SEG_NORMAL",
            constant_phase_deg=0.0,
            registered_by="kimi-code/FI-008",
        )
        assert r.is_actionable() is True
        assert r.polarity_sign() == 1.0

    def test_valid_register_seg_reverse(self):
        r = PolarityPhaseRegister(
            register_id="geox://artifact/polarity-f3",
            polarity="SEG_REVERSE",
            registered_by="kimi-code/FI-008",
        )
        assert r.polarity_sign() == -1.0

    def test_unknown_polarity_not_actionable(self):
        r = PolarityPhaseRegister(
            register_id="geox://artifact/polarity-unknown",
            polarity="UNKNOWN",
            registered_by="kimi-code/FI-008",
        )
        assert r.is_actionable() is False
        assert r.polarity_sign() is None

    def test_phase_estimates_supported(self):
        r = PolarityPhaseRegister(
            register_id="geox://artifact/polarity-f3",
            polarity="SEG_NORMAL",
            constant_phase_deg=15.5,
            phase_estimates=[
                PhaseShiftEstimate(
                    method="kurtosis_max",
                    phase_deg=15.0,
                    confidence=0.8,
                    sample_size=10000,
                ),
                PhaseShiftEstimate(
                    method="cross_correlation_with_well",
                    phase_deg=16.0,
                    confidence=0.95,
                    sample_size=5000,
                ),
            ],
            registered_by="kimi-code/FI-008",
        )
        assert len(r.phase_estimates) == 2

    def test_duplicate_estimation_methods_rejected(self):
        with pytest.raises(ValueError):
            PolarityPhaseRegister(
                register_id="geox://artifact/polarity-bad",
                polarity="SEG_NORMAL",
                phase_estimates=[
                    PhaseShiftEstimate(method="kurtosis_max", phase_deg=0.0, confidence=0.8),
                    PhaseShiftEstimate(method="kurtosis_max", phase_deg=10.0, confidence=0.7),
                ],
                registered_by="kimi-code/FI-008",
            )

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            PhaseShiftEstimate(
                method="kurtosis_max",
                phase_deg=0.0,
                confidence=1.5,  # > 1
            )

    def test_phase_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            PhaseShiftEstimate(
                method="kurtosis_max",
                phase_deg=200.0,  # > 180
                confidence=0.5,
            )

    def test_supersession_chain(self):
        old = PolarityPhaseRegister(
            register_id="geox://artifact/polarity-v1",
            polarity="SEG_NORMAL",
            registered_by="kimi-code/FI-008",
        )
        new = PolarityPhaseRegister(
            register_id="geox://artifact/polarity-v2",
            polarity="SEG_REVERSE",  # corrected
            superseded_by="geox://artifact/polarity-v1",
            registered_by="kimi-code/FI-008",
        )
        assert new.superseded_by == "geox://artifact/polarity-v1"
        # Old register should still be valid for historic artifacts
        assert old.is_actionable()

    def test_polarity_sign_table_complete(self):
        """Every PolarityConvention value must have a sign entry."""
        from geox.seismic.contracts.polarity import PolarityConvention
        # Use the Literal's __args__
        for conv in PolarityConvention.__args__:
            assert conv in POLARITY_SIGN, f"Missing sign for {conv}"

    def test_volume_ref_pattern(self):
        with pytest.raises(ValueError):
            PolarityPhaseRegister(
                register_id="geox://artifact/polarity-bad",
                volume_ref="invalid-pattern",
                polarity="SEG_NORMAL",
                registered_by="kimi-code/FI-008",
            )
