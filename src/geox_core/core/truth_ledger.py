import sqlite3
import json
from pathlib import Path

DB_PATH = Path("/root/geox/asset_memory.db")


class TruthLedger:
    """
    WAJIB #1: Unified Relational Truth Model.
    All ingestion, QC, and prospect evaluations MUST be anchored here.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS well_ingestion_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    well_id TEXT NOT NULL,
                    uwi TEXT,
                    source_type TEXT,
                    claim_state TEXT,
                    suitability TEXT,
                    qc_fail_count INTEGER,
                    limitations TEXT,
                    vault_receipt_hash TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def anchor_ingestion(self, well_result: dict) -> int:
        """Anchor a WellLoadResult to the unified truth ledger."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO well_ingestion_ledger (
                    well_id, uwi, source_type, claim_state, 
                    suitability, qc_fail_count, limitations, vault_receipt_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    well_result.get("well_id", "UNKNOWN"),
                    well_result.get("uwi", "UNKNOWN"),
                    well_result.get("source_type", "UNKNOWN"),
                    well_result.get("claim_state", "UNKNOWN"),
                    well_result.get("suitability", "UNKNOWN"),
                    well_result.get("qcfail_count", 0),
                    json.dumps(well_result.get("limitations", [])),
                    well_result.get("vault_receipt", {}).get("hash", "N/A"),
                ),
            )
            return cursor.lastrowid
