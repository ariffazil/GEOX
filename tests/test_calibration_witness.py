"""Tests for CalibrationWitness schema and registration.

DITEMPA BUKAN DIBERI.
"""
from __future__ import annotations

import asyncio

import pytest

from geox_mcp.domain.calibration.contracts import (
    AnchorPoint,
    AxisCalibration,
    CalibrationPurpose,
    CalibrationReceipt,
    CalibrationWitness,
    DataClassification,
    DisplayDomain,
    EvidenceRef,
    HorizontalCalibration,
    Pick,
    VelocityEvidenceRef,
    VerticalCalibration,
    VerticalDomain,
    WitnessStatus,
    AuthorityState,
)
from geox_mcp.tools.calibration_witness import geox_calibration_register_witness


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_valid_witness():
    """Fully calibrated TWT witness should parse and stay DRAFT."""
    cw = CalibrationWitness(
        calibration_witness_id="calw_test_001",
        purpose=[CalibrationPurpose.DIP_MEASUREMENT],
        evidence_ref=EvidenceRef(
            dataset_id="test_segy",
            classification=DataClassification.SYNTHETIC,
            authority_state=AuthorityState.SYNTHETIC_VERIFIED,
        ),
        display_domain=DisplayDomain(
            vertical_domain=VerticalDomain.TWT,
            vertical_units="ms",
        ),
        axis_calibration_h=HorizontalCalibration(
            anchor_a=AnchorPoint(pixel_x=0, pixel_y=0, world_x=0, world_y=0),
            anchor_b=AnchorPoint(pixel_x=1000, pixel_y=0, world_x=5000, world_y=0),
            unit="m",
        ),
        axis_calibration_v=VerticalCalibration(
            anchor_a=AnchorPoint(pixel_x=0, pixel_y=0, value=0),
            anchor_b=AnchorPoint(pixel_x=0, pixel_y=800, value=2000),
            unit="ms",
        ),
    )
    assert cw.status == WitnessStatus.DRAFT
    assert cw.evidence_ref.classification == DataClassification.SYNTHETIC
    assert cw.display_domain.vertical_domain == VerticalDomain.TWT


def test_depth_requires_velocity():
    """Depth domain without velocity should produce HOLD."""
    witness = {
        "calibration_witness_id": "calw_test_002",
        "evidence_ref": {"dataset_id": "test"},
        "display_domain": {"vertical_domain": "DEPTH", "vertical_units": "m"},
        "axis_calibration_h": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0},
            "anchor_b": {"pixel_x": 100, "pixel_y": 0},
        },
        "axis_calibration_v": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0, "value": 0},
            "anchor_b": {"pixel_x": 0, "pixel_y": 100, "value": 1000},
        },
    }
    result = asyncio.run(geox_calibration_register_witness(witness=witness))
    assert result["status"] == "HOLD"
    assert "depth_domain_requires_velocity_or_td" in result["blockers"]


def test_depth_with_velocity_is_valid():
    """Depth domain WITH velocity should stay VALID (no blockers)."""
    witness = {
        "calibration_witness_id": "calw_test_003",
        "evidence_ref": {"dataset_id": "test"},
        "display_domain": {"vertical_domain": "DEPTH", "vertical_units": "m"},
        "axis_calibration_h": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0},
            "anchor_b": {"pixel_x": 100, "pixel_y": 0},
        },
        "axis_calibration_v": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0, "value": 0},
            "anchor_b": {"pixel_x": 0, "pixel_y": 100, "value": 1000},
        },
        "velocity_or_td_ref": {"kind": "checkshot"},
    }
    result = asyncio.run(geox_calibration_register_witness(witness=witness))
    # No blockers → status stays DRAFT (default); only blockers promote to HOLD
    assert result["status"] == "DRAFT"
    assert result["blockers"] == []
    assert result["has_velocity"] is True


def test_missing_calibrations_produces_hold():
    """Witness without axis calibrations should produce HOLD."""
    witness = {
        "calibration_witness_id": "calw_test_004",
        "evidence_ref": {"dataset_id": "test"},
        "display_domain": {"vertical_domain": "TWT", "vertical_units": "ms"},
    }
    result = asyncio.run(geox_calibration_register_witness(witness=witness))
    assert result["status"] == "HOLD"
    assert "missing_horizontal_calibration" in result["blockers"]
    assert "missing_vertical_calibration" in result["blockers"]


def test_void_on_invalid_schema():
    """Malformed witness dict returns VOID."""
    result = asyncio.run(
        geox_calibration_register_witness(witness={"not": "valid"})
    )
    assert result["status"] == "VOID"
    assert "Invalid witness schema" in result["reason"]


def test_picks_count():
    """Picks are counted correctly in the response."""
    witness = {
        "calibration_witness_id": "calw_test_005",
        "evidence_ref": {"dataset_id": "test"},
        "display_domain": {"vertical_domain": "TWT"},
        "axis_calibration_h": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0},
            "anchor_b": {"pixel_x": 100, "pixel_y": 0},
        },
        "axis_calibration_v": {
            "anchor_a": {"pixel_x": 0, "pixel_y": 0, "value": 0},
            "anchor_b": {"pixel_x": 0, "pixel_y": 100, "value": 1000},
        },
        "picks": [
            {"pick_id": "p1", "kind": "fault_trace"},
            {"pick_id": "p2", "kind": "horizon"},
        ],
    }
    result = asyncio.run(geox_calibration_register_witness(witness=witness))
    assert result["n_picks"] == 2


def test_purpose_enabled_only_when_no_blockers():
    """purposes_enabled is empty when blockers exist."""
    witness = {
        "calibration_witness_id": "calw_test_006",
        "purpose": ["dip_measurement", "fault_throw_estimation"],
        "evidence_ref": {"dataset_id": "test"},
        "display_domain": {"vertical_domain": "TWT"},
        # no calibrations → blockers
    }
    result = asyncio.run(geox_calibration_register_witness(witness=witness))
    assert result["status"] == "HOLD"
    assert result["purposes_enabled"] == []


def test_extra_fields_rejected():
    """extra='forbid' rejects unknown fields."""
    with pytest.raises(Exception):
        CalibrationWitness(
            calibration_witness_id="calw_test_007",
            evidence_ref=EvidenceRef(dataset_id="test"),
            display_domain=DisplayDomain(),
            unknown_field="nope",
        )


def test_calibration_receipt_model():
    """CalibrationReceipt round-trips."""
    r = CalibrationReceipt(
        witness_id="calw_test_001",
        validation_status="VALID",
        gates_consumed=["K-DIP", "K-THROW"],
    )
    assert r.witness_id == "calw_test_001"
    assert len(r.gates_consumed) == 2
