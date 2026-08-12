"""
Tests for Calibration Gate and Basin Context
DITEMPA BUKAN DIBERI — Forged, not given

Test cases:
1. CALIBRATED with all inputs → passes gate
2. UNCALIBRATED with no inputs → returns 888_HOLD
3. PARTIAL with only sonic_log → passes gate at PARTIAL level
4. PARTIAL without any inputs → returns HOLD for min_level=PARTIAL
5. Basin context loader correctly loads malay_basin.yaml and returns Group F as overpressure seal
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from geox_core.gates.calibration_gate import (
    CalibrationLevel,
    CalibrationManifest,
    check_calibration_gate,
    get_confidence_cap,
    get_epistemic_label,
    requires_calibration,
)
from geox_core.registry.basin_context_loader import (
    BasinContextNotFoundError,
    load_basin_context,
)


# ─── Test 1: CALIBRATED with all inputs → passes gate ───


def test_calibrated_with_all_inputs_passes():
    """Test that full calibration (sonic_log + rft_mdt + lot_xlot) passes the gate."""
    manifest = CalibrationManifest(
        sonic_log="/data/sonic_log.las",
        rft_mdt="/data/rft_data.csv",
        lot_xlot="/data/lot_xlot.csv",
    )

    result = check_calibration_gate(manifest, CalibrationLevel.CALIBRATED)

    assert result.status == "PASS"
    assert result.level == CalibrationLevel.CALIBRATED


# ─── Test 2: UNCALIBRATED with no inputs → returns 888_HOLD ───


def test_uncalibrated_no_inputs_returns_hold():
    """Test that no calibration returns 888_HOLD when min_level is PARTIAL."""
    manifest = None

    result = check_calibration_gate(manifest, CalibrationLevel.PARTIAL)

    assert result.status == "888_HOLD"
    assert result.level == CalibrationLevel.UNCALIBRATED
    assert result.required_level == CalibrationLevel.PARTIAL
    assert "sonic_log or offset_wells" in result.missing_inputs


# ─── Test 3: PARTIAL with only sonic_log → passes gate at PARTIAL level ───


def test_partial_with_sonic_log_passes():
    """Test that partial calibration (sonic_log only) passes at PARTIAL level."""
    manifest = CalibrationManifest(
        sonic_log="/data/sonic_log.las",
    )

    result = check_calibration_gate(manifest, CalibrationLevel.PARTIAL)

    assert result.status == "PASS"
    assert result.level == CalibrationLevel.PARTIAL


# ─── Test 4: PARTIAL without any inputs → returns HOLD for min_level=PARTIAL ───


def test_partial_without_inputs_returns_hold():
    """Test that PARTIAL required but no inputs returns 888_HOLD."""
    manifest = CalibrationManifest()

    result = check_calibration_gate(manifest, CalibrationLevel.PARTIAL)

    assert result.status == "888_HOLD"
    assert result.level == CalibrationLevel.UNCALIBRATED
    assert result.required_level == CalibrationLevel.PARTIAL


# ─── Test 5: Basin context loader returns Group F as overpressure seal ───


def test_basin_context_loads_malay_basin_group_f_seal():
    """Test that Malay Basin context loader returns Group F as the overpressure seal."""
    ctx = load_basin_context("Malay_Basin")

    # Check basin name
    assert ctx.basin == "Malay_Basin"

    # Check provenance
    assert "Madon" in ctx.provenance.get("primary_source", "")
    assert ctx.confidence == 0.95

    # Check Group F is the overpressure seal
    seal_letter = ctx.get_overpressure_seal("basin_central")
    assert seal_letter == "F", f"Expected Group F as seal, got {seal_letter}"

    # Verify Group F properties
    group_f = ctx.get_group("F")
    assert group_f.overpressure_top_seal is True
    assert group_f.confidence == 0.97
    assert "seal" in group_f.hc_role.lower()

    # Check overpressure compartment
    basin_central = ctx.overpressure.get("basin_central")
    assert basin_central is not None
    assert basin_central.controlling_seal == "F"
    assert basin_central.depth_top_m == [1900, 2000]


# ─── Additional tests: confidence caps and epistemic labels ───


def test_confidence_caps():
    """Test confidence caps for each calibration level."""
    assert get_confidence_cap(CalibrationLevel.CALIBRATED) == 0.85
    assert get_confidence_cap(CalibrationLevel.PARTIAL) == 0.72
    assert get_confidence_cap(CalibrationLevel.UNCALIBRATED) == 0.45


def test_epistemic_labels():
    """Test epistemic labels for each calibration level."""
    assert get_epistemic_label(CalibrationLevel.CALIBRATED) == "CLAIM"
    assert get_epistemic_label(CalibrationLevel.PARTIAL) == "ESTIMATE"
    assert get_epistemic_label(CalibrationLevel.UNCALIBRATED) == "HYPOTHESIS"


# ─── Test for decorator behavior ───


def test_requires_calibration_decorator():
    """Test that the decorator correctly gates functions."""

    @requires_calibration(min_level=CalibrationLevel.PARTIAL)
    def dummy_function(depths, calibration_manifest=None):
        return {"status": "computed", "depths": depths}

    # Test without calibration - should return HOLD
    result = dummy_function([1000, 2000, 3000])

    assert result["status"] == "888_HOLD"
    assert "calibration_required" in result["reason"]
    assert result["required_level"] == "PARTIAL"
    assert result["current_level"] == "UNCALIBRATED"


def test_basin_context_not_found():
    """Test that loading non-existent basin raises appropriate error."""
    with pytest.raises(BasinContextNotFoundError) as exc_info:
        load_basin_context("NonExistent_Basin")

    assert "NonExistent_Basin" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
