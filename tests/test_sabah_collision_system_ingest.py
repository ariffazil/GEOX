"""Sabah collision-system ingest + resolve evidence-shape regression (2026-09-30).

Two contracts:
1. The six NW Borneo Collision System entities resolve with correct ids.
2. resolve() payloads carry observed/interpreted evidence fields so
   geox-evidence-postcondition-v1 cannot downgrade them as false success
   (historic defect: resolve returned SUCCESS-shaped payloads with no
   evidence fields for EVERY basin; malay_basin masked it in direct tests).
"""

import pytest

from geox_mcp.tools.basin import geox_basin_profile, geox_basin_resolve

SABAH_ENTITIES = {
    "NW Borneo Collision System": "NW_BORNEO_COLLISION_SYSTEM",
    "Layang-Layang Basin": "LAYANG_LAYANG_BASIN",
    "Sabah Trough": "SABAH_TROUGH",
    "Kinabalu Basin": "KINABALU_BASIN",
    "Dangerous Grounds": "DANGEROUS_GROUNDS",
    "Northwest Borneo Trough": "NORTHWEST_BORNEO_TROUGH",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("name,expected_id", sorted(SABAH_ENTITIES.items()))
async def test_sabah_entities_resolve(name, expected_id):
    res = await geox_basin_resolve(name=name)
    assert res["execution_status"] == "SUCCESS", res
    art = res["primary_artifact"]
    assert art["basin_id"] == expected_id
    # postcondition-critical: at least one substantive evidence field
    assert art.get("observed"), "resolve payload missing observed — postcondition would downgrade"
    assert art.get("interpreted"), "resolve payload missing interpreted — postcondition would downgrade"
    assert art.get("polygon_ref", "") == "", "polygon intentionally absent until boundaries evidenced"


@pytest.mark.asyncio
async def test_kinabalu_carries_system_ontology():
    res = await geox_basin_resolve(name="Kinabalu Basin")
    art = res["primary_artifact"]
    assert art["parent_system"] == "NW_BORNEO_COLLISION_SYSTEM"
    assert "UPPER PLATE" in art["structural_position"]
    assert art["bbox"] == [115.6, 5.5, 117.5, 7.0]


@pytest.mark.asyncio
async def test_trough_bbox_not_placeholder():
    res = await geox_basin_resolve(name="Sabah Trough")
    assert res["primary_artifact"]["bbox"] != [0.0, 0.0, 0.0, 0.0]


@pytest.mark.asyncio
async def test_system_profile_exposes_event_registry():
    prof = await geox_basin_profile(basin_name="NW Borneo Collision System", mode="overview")
    assert prof["execution_status"] == "SUCCESS"
    interp = prof["primary_artifact"]["interpreted"]
    assert "events" in interp and len(interp["events"]) >= 10
    assert "COLLISION_MM" in {e["event_id"] for e in interp["events"]}
    assert "opposite sign" in interp["master_paradox"].lower()


@pytest.mark.asyncio
async def test_malay_legacy_path_preserved():
    res = await geox_basin_resolve(name="Malay Basin")
    art = res["primary_artifact"]
    assert art["basin_id"] == "MALAY_BASIN"
    assert "Malay Basin" in art["aliases"] and "Basin Melayu" in art["aliases"]
    assert art["bbox"] == [102.0, 4.0, 106.5, 8.5]
    assert art["neighbor_basins"] == ["Penyu", "Gulf of Thailand", "West Natuna"]
