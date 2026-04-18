"""
SQLite-backed asset memory for GEOX Wave 2.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
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
