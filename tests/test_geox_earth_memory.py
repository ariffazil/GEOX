import pytest
import json
from geox_core.services.asset_memory import EarthMemoryStore, AgentMemoryStore
import os

@pytest.fixture
def memory_db(tmp_path):
    db_path = tmp_path / "test_memory.db"
    store = EarthMemoryStore(str(db_path))
    agent_store = AgentMemoryStore(str(db_path))
    return store, agent_store

def test_agent_memory_volatile(memory_db):
    _, agent_store = memory_db
    
    payload = {"thought": "I think this amplitude is gas."}
    record_id = agent_store.store_thought("GEOX.AbductionAgent", payload, ttl_hours=1)
    
    assert record_id.startswith("ag_mem_")
    
    with agent_store._connect() as conn:
        row = conn.execute("SELECT payload, ttl_hours FROM agent_memory WHERE id = ?", (record_id,)).fetchone()
        assert json.loads(row[0])["thought"] == "I think this amplitude is gas."
        assert row[1] == 1

def test_earth_memory_promotion_ladder(memory_db):
    earth_store, _ = memory_db
    
    # 1. Draft a claim
    draft_payload = {
        "truth_class": "interpretation",
        "subject": {"asset_id": "A-01"},
        "claim": "Net reservoir top at 1200m MD",
        "evidence": [],
        "provenance": {
            "source_id": "well_top_1",
            "source_type": "well_log",
            "source_hash": "abc12345",
            "observed_at": "2026-05-27T00:00:00Z",
            "ingested_at": "2026-05-27T00:00:00Z"
        },
        "measurement": {
            "value": 1200,
            "unit": "m",
            "datum": "MD",
            "crs": "EPSG:4326"
        },
        "uncertainty": {
            "confidence": 0.8,
            "alternatives": ["Log artifact"]
        }
    }
    
    record_id = earth_store.draft_claim("A-01", draft_payload)
    
    # Verify it's in draft state
    with earth_store._connect() as conn:
        row = conn.execute("SELECT approval_state FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
        assert row[0] == "draft"

    # 2. Validate claim
    earth_store.validate_claim(record_id)
    
    with earth_store._connect() as conn:
        row = conn.execute("SELECT approval_state FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
        assert row[0] == "validated"

    # 3. Review claim
    earth_store.review_interpretation(record_id, reviewer="Arif")
    
    with earth_store._connect() as conn:
        row = conn.execute("SELECT approval_state, payload FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
        assert row[0] == "reviewed"
        payload = json.loads(row[1])
        assert payload["authority"]["approved_by"] == "Arif"

    # 4. Seal claim
    receipt = earth_store.seal_decision(record_id)
    assert receipt["verdict"] == "SEAL"
    
    with earth_store._connect() as conn:
        row = conn.execute("SELECT approval_state, vault_receipt FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
        assert row[0] == "sealed"
        assert row[1] == receipt["hash"]

def test_earth_memory_validation_failure(memory_db):
    earth_store, _ = memory_db
    
    # Payload missing provenance and uncertainty (Required for earth memory)
    invalid_payload = {
        "truth_class": "interpretation",
        "subject": {"asset_id": "A-01"},
        "claim": "Naked Earth claim without proof"
    }
    
    record_id = earth_store.draft_claim("A-01", invalid_payload)
    
    # Should fail validation because it lacks provenance and uncertainty
    with pytest.raises(ValueError, match="Memory Validation Failed"):
        earth_store.validate_claim(record_id)
