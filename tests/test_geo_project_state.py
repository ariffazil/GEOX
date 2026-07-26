"""test_geo_project_state.py — Unit tests for canonical GeoProjectState contract.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from geox_mcp.contracts.geo_project_state import (
    CoordinateReferenceSystem,
    GeoProjectState,
    HumanEditRecord,
    ScenarioBranch,
)


def test_geo_project_state_creation_and_hashing():
    state = GeoProjectState(
        project_id="PROJ-BARAM-001",
        project_name="Baram Delta Deepwater Prospect",
        coordinate_reference=CoordinateReferenceSystem(crs_code="EPSG:32650", projected_unit="m"),
        wells=[{"well_id": "DEMO_WELL_A", "top_md_m": 1200, "bottom_md_m": 3500}],
        scenarios=[
            ScenarioBranch(
                scenario_id="Scenario_A_Channel",
                title="Turbidite Channel Complex",
                hypothesis_summary="High-amplitude anomaly represents Miocene basin-floor fan",
                supporting_evidence=["amplitude_bright_spot", "well_A_sand_count"],
                volumetric_p50_mmboe=120.5,
                gcos=0.35,
            )
        ],
    )

    assert state.project_id == "PROJ-BARAM-001"
    assert state.coordinate_reference.crs_code == "EPSG:32650"
    assert len(state.wells) == 1
    assert len(state.scenarios) == 1
    assert state.scenarios[0].scenario_id == "Scenario_A_Channel"

    state_hash = state.compute_state_hash()
    assert isinstance(state_hash, str)
    assert len(state_hash) == 64


def test_human_edit_record_capture():
    edit = HumanEditRecord(
        edit_id="EDIT-1001",
        actor_id="ARIF",
        target_object="horizon_miocene_top",
        previous_value=1450.0,
        new_value=1432.0,
        reason="Corrected mistie at Well DEMO_WELL_A using checkshot",
        before_hash="sha256-before-123",
        after_hash="sha256-after-456",
        affected_claims=["CLAIM-001-MIOCENE-AGE"],
    )

    assert edit.edit_id == "EDIT-1001"
    assert edit.actor_id == "ARIF"
    assert edit.new_value == 1432.0
    assert len(edit.affected_claims) == 1
