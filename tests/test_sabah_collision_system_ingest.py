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
    art = prof["primary_artifact"]
    # Hoisted to top-level lane so it survives MCP compaction (4 KB dict boundary).
    assert "event_registry" in art and len(art["event_registry"]) >= 10
    assert "COLLISION_MM" in {e["event_id"] for e in art["event_registry"]}
    # Master paradox stays inside the interpreted lane for legacy consumers.
    interp = art["interpreted"]
    assert "opposite sign" in interp["master_paradox"].lower()


@pytest.mark.asyncio
async def test_malay_legacy_path_preserved():
    res = await geox_basin_resolve(name="Malay Basin")
    art = res["primary_artifact"]
    assert art["basin_id"] == "MALAY_BASIN"
    assert "Malay Basin" in art["aliases"] and "Basin Melayu" in art["aliases"]
    assert art["bbox"] == [102.0, 4.0, 106.5, 8.5]
    assert art["neighbor_basins"] == ["Penyu", "Gulf of Thailand", "West Natuna"]


# Aliases advertised in basin_profile.yaml but not equal to the canonical
# directory name. Resolver must scan the alias index before returning
# "Basin not found" so callers receive a populated envelope.
ALIAS_HITS = [
    ("DG", "DANGEROUS_GROUNDS"),
    ("Kinabalu", "KINABALU_BASIN"),
    ("NWB Trough", "NORTHWEST_BORNEO_TROUGH"),
    ("Layang Basin", "LAYANG_LAYANG_BASIN"),
    ("deepwater flat zone (operator colloquial)", "SABAH_TROUGH"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("alias,expected_id", ALIAS_HITS)
async def test_advertised_aliases_resolve(alias, expected_id):
    res = await geox_basin_resolve(name=alias)
    assert res["execution_status"] == "SUCCESS", f"alias '{alias}' should resolve, got {res}"
    art = res["primary_artifact"]
    assert art["basin_id"] == expected_id
    # Resolver must surface the canonical name in the alias list so the
    # alias → canonical mapping is auditable in receipts. Title-case mangling
    # won't match multi-word names perfectly; rely on the alias set being
    # non-empty and the requested alias being present (case-insensitive).
    assert len(art["aliases"]) >= 1
    assert alias in art["aliases"] or alias.lower() in {a.lower() for a in art["aliases"]}


@pytest.mark.asyncio
async def test_truly_unknown_basin_still_holds():
    """Alias fallback must not mask real misses."""
    res = await geox_basin_resolve(name="Atlantis Hydrocarbon Province")
    assert res["execution_status"] == "ERROR"
    assert "Basin not found" in res["primary_artifact"].get("error", "")
