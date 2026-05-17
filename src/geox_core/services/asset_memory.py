"""
SQLite-backed asset memory for GEOX Wave 2.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AssetMemoryRecord:
    asset_id: str
    eval_type: str
    timestamp: str
    payload: dict[str, Any]
    vault_receipt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "eval_type": self.eval_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "vault_receipt": self.vault_receipt,
        }


@dataclass
class AssetStoreResult:
    success: bool
    record_id: str | None
    audit_trace: list[str] = field(default_factory=list)
    vault_receipt: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "record_id": self.record_id,
            "audit_trace": self.audit_trace,
            "vault_receipt": self.vault_receipt,
        }


@dataclass
class AssetRecallResult:
    asset_id: str
    records: list[AssetMemoryRecord]
    claim_tag: str
    vault_receipt: dict[str, Any]

    @property
    def n_records(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "records": [record.to_dict() for record in self.records],
            "n_records": self.n_records,
            "claim_tag": self.claim_tag,
            "vault_receipt": self.vault_receipt,
        }


def _receipt(tool_name: str, payload: dict[str, Any], verdict: str = "SEAL") -> dict[str, Any]:
    import hashlib

    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return {
        "tool_name": tool_name,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": hashlib.sha256(f"{tool_name}:{canonical}".encode("utf-8")).hexdigest()[:16],
    }


class AssetMemoryStore:
    """Simple per-asset store for GEOX evaluations."""

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
                CREATE TABLE IF NOT EXISTS asset_memory (
                    asset_id TEXT NOT NULL,
                    eval_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    vault_receipt TEXT NOT NULL
                )
                """
            )

    def store_record(
        self,
        asset_id: str,
        eval_type: str,
        payload: dict[str, Any],
        vault_receipt: str,
        authorized: bool,
    ) -> dict[str, Any]:
        if not authorized:
            raise PermissionError("F11 authorization required for asset memory writes")
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO asset_memory (asset_id, eval_type, timestamp, payload, vault_receipt) VALUES (?, ?, ?, ?, ?)",
                (asset_id, eval_type, timestamp, json.dumps(payload), vault_receipt),
            )
        return {
            "stored": True,
            "asset_id": asset_id,
            "eval_type": eval_type,
            "timestamp": timestamp,
        }

    def store(
        self,
        asset_id: str,
        eval_type: str,
        payload: dict[str, Any],
        amanah_locked: bool = False,
    ) -> AssetStoreResult:
        if not amanah_locked:
            return AssetStoreResult(
                success=False,
                record_id=None,
                audit_trace=["F11", "authorization required: amanah_locked=False"],
                vault_receipt=_receipt("geox_memory_store_asset", {"asset_id": asset_id}, "HOLD"),
            )
        receipt = _receipt(
            "geox_memory_store_asset",
            {"asset_id": asset_id, "eval_type": eval_type, "payload": payload},
            "SEAL",
        )
        stored = self.store_record(
            asset_id=asset_id,
            eval_type=eval_type,
            payload=payload,
            vault_receipt=receipt["hash"],
            authorized=True,
        )
        return AssetStoreResult(
            success=True,
            record_id=f"{asset_id}:{eval_type}:{stored['timestamp']}",
            audit_trace=["F11 PASS", "F1 AMANAH locked"],
            vault_receipt=receipt,
        )

    def recall_asset(
        self,
        asset_id: str,
        eval_type: str | None = None,
        query: str | None = None,
        limit: int = 10,
    ) -> list[AssetMemoryRecord]:
        sql = "SELECT asset_id, eval_type, timestamp, payload, vault_receipt FROM asset_memory WHERE asset_id = ?"
        params: list[Any] = [asset_id]
        if eval_type:
            sql += " AND eval_type = ?"
            params.append(eval_type)
        if query:
            sql += " AND payload LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            AssetMemoryRecord(
                asset_id=row[0],
                eval_type=row[1],
                timestamp=row[2],
                payload=json.loads(row[3]),
                vault_receipt=row[4],
            )
            for row in rows
        ]

    def recall(
        self,
        asset_id: str,
        eval_type: str | None = None,
        query: str | None = None,
        limit: int = 10,
    ) -> AssetRecallResult:
        records = self.recall_asset(asset_id, eval_type=eval_type, query=query, limit=limit)
        return AssetRecallResult(
            asset_id=asset_id,
            records=records,
            claim_tag="CLAIM" if records else "ESTIMATE",
            vault_receipt=_receipt(
                "geox_memory_recall_asset",
                {"asset_id": asset_id, "eval_type": eval_type, "n_records": len(records)},
                "SEAL",
            ),
        )
