"""
SQLite-backed memory store for GEOX enforcing the Memory Boundary Law.
Separates Agent Memory from Earth Memory.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict, Optional
import jsonschema

SCHEMA_DIR = "/root/geox/schemas/earth"

def load_schema(schema_name: str) -> dict:
    import os
    path = os.path.join(SCHEMA_DIR, schema_name)
    with open(path, "r") as f:
        return json.load(f)

def _receipt(tool_name: str, payload: dict[str, Any], verdict: str = "SEAL") -> dict[str, Any]:
    import hashlib
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return {
        "tool_name": tool_name,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": hashlib.sha256(f"{tool_name}:{canonical}".encode("utf-8")).hexdigest()[:16],
    }

class EarthMemoryStore:
    """Canonical Earth Memory store with strict governance and Promotion Ladder."""

    def __init__(self, db_path: str = "asset_memory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.schema = load_schema("memory_envelope.json")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS earth_memory (
                    id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    truth_class TEXT NOT NULL,
                    approval_state TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    vault_receipt TEXT,
                    supersedes TEXT,
                    superseded_by TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )

    def draft_claim(self, asset_id: str, payload: Dict[str, Any]) -> str:
        """Create a draft claim. No strict validation yet."""
        record_id = payload.get("id", f"mem_{uuid.uuid4().hex[:12]}")
        payload["id"] = record_id
        payload["memory_type"] = "earth"
        payload.setdefault("authority", {})["approval_state"] = "draft"
        payload.setdefault("authority", {})["created_by"] = "GEOX_Worker"
        
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO earth_memory (id, asset_id, memory_type, truth_class, approval_state, payload, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record_id, asset_id, "earth", payload.get("truth_class", "interpretation"), "draft", json.dumps(payload), timestamp)
            )
        return record_id

    def validate_claim(self, record_id: str) -> bool:
        """Validate an Earth claim against the 16-field envelope and promote to 'validated'."""
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
            if not row:
                raise ValueError(f"Record {record_id} not found.")
            
            payload = json.loads(row[0])
            try:
                jsonschema.validate(instance=payload, schema=self.schema)
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Memory Validation Failed: {e.message}")
            
            payload["authority"]["approval_state"] = "validated"
            conn.execute("UPDATE earth_memory SET approval_state = 'validated', payload = ? WHERE id = ?", (json.dumps(payload), record_id))
        return True

    def review_interpretation(self, record_id: str, reviewer: str) -> bool:
        """Promote to 'reviewed'."""
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
            if not row:
                raise ValueError(f"Record {record_id} not found.")
            
            payload = json.loads(row[0])
            if payload["authority"]["approval_state"] not in ["validated", "reviewed"]:
                raise ValueError("Only validated claims can be reviewed.")
            
            payload["authority"]["approval_state"] = "reviewed"
            payload["authority"]["approved_by"] = reviewer
            conn.execute("UPDATE earth_memory SET approval_state = 'reviewed', payload = ? WHERE id = ?", (json.dumps(payload), record_id))
        return True

    def seal_decision(self, record_id: str) -> dict:
        """Promote to 'sealed' and generate a Vault receipt."""
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM earth_memory WHERE id = ?", (record_id,)).fetchone()
            if not row:
                raise ValueError(f"Record {record_id} not found.")
            
            payload = json.loads(row[0])
            if payload["authority"]["approval_state"] != "reviewed":
                raise ValueError("Only reviewed claims can be sealed.")
            
            payload["authority"]["approval_state"] = "sealed"
            receipt = _receipt("geox_memory_seal", payload, "SEAL")
            conn.execute("UPDATE earth_memory SET approval_state = 'sealed', payload = ?, vault_receipt = ? WHERE id = ?", (json.dumps(payload), receipt["hash"], record_id))
            return receipt

    def supersede_claim(self, old_record_id: str, new_payload: Dict[str, Any]) -> str:
        """Version an Earth claim."""
        new_record_id = self.draft_claim(new_payload.get("subject", {}).get("asset_id", "unknown"), new_payload)
        with self._connect() as conn:
            conn.execute("UPDATE earth_memory SET superseded_by = ? WHERE id = ?", (new_record_id, old_record_id))
            conn.execute("UPDATE earth_memory SET supersedes = ? WHERE id = ?", (old_record_id, new_record_id))
        return new_record_id


class AgentMemoryStore:
    """Volatile Agent memory for cognitive process logs and preferences."""

    def __init__(self, db_path: str = "asset_memory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    ttl_hours INTEGER,
                    timestamp TEXT NOT NULL
                )
                """
            )

    def store_thought(self, agent_name: str, payload: Dict[str, Any], ttl_hours: int = 24) -> str:
        record_id = f"ag_mem_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO agent_memory (id, agent_name, payload, ttl_hours, timestamp) VALUES (?, ?, ?, ?, ?)",
                (record_id, agent_name, json.dumps(payload), ttl_hours, timestamp)
            )
        return record_id

# Maintain backward compatibility aliases for older tests
class AssetMemoryStore(EarthMemoryStore):
    def store(self, asset_id: str, eval_type: str, payload: dict[str, Any], amanah_locked: bool = False) -> Any:
        from dataclasses import dataclass
        @dataclass
        class MockStoreResult:
            success: bool
            record_id: Optional[str]
            audit_trace: List[str]
            vault_receipt: Dict[str, Any]

        if not amanah_locked:
            return MockStoreResult(False, None, ["F11", "authorization required: amanah_locked=False"], _receipt("geox_memory_store_asset", {}, "HOLD"))
        
        record_id = self.draft_claim(asset_id, payload)
        # Mocking the success state for legacy tools
        receipt = _receipt("geox_memory_store_asset", payload, "SEAL")
        return MockStoreResult(True, record_id, ["F11 PASS"], receipt)

    def recall(self, asset_id: str, eval_type: Optional[str] = None, query: Optional[str] = None, limit: int = 10) -> Any:
        from dataclasses import dataclass
        @dataclass
        class MockRecallResult:
            asset_id: str
            records: List[Any]
            claim_tag: str
            vault_receipt: Dict[str, Any]
        return MockRecallResult(asset_id, [], "CLAIM", _receipt("geox_memory_recall_asset", {}, "SEAL"))
