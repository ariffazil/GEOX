import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("/root/geox/asset_memory.db")


class ScarLedger:
    """
    WAJIB F12: SCAR → LAW → ECHO (Institutional Memory).
    GeoX forgets. GEOX canonizes failures so they are never repeated.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scar_canon (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_tag TEXT NOT NULL,
                    failed_assumption TEXT NOT NULL,
                    consequence TEXT NOT NULL,
                    enforced_rule TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def canonize_scar(self, context_tag: str, failed_assumption: str, consequence: str, enforced_rule: str) -> int:
        """
        Permanently record a failure.
        Example:
          tag: "BLOCK_B_SOURCE"
          assumption: "Source rock extends uniformly."
          consequence: "Dry hole drilled in 2024. $15M lost."
          rule: "Source risk must never be >0.5 without explicit geochemical samples."
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scar_canon (context_tag, failed_assumption, consequence, enforced_rule)
                VALUES (?, ?, ?, ?)
            """,
                (context_tag.upper(), failed_assumption, consequence, enforced_rule),
            )
            return cursor.lastrowid

    def audit_against_scars(self, context_tags: list[str]) -> list[dict[str, Any]]:
        """
        Audit a new evaluation against known scars.
        Returns a list of applicable scars (echoes) that must be respected.
        """
        if not context_tags:
            return []

        tags = [t.upper() for t in context_tags]
        placeholders = ",".join("?" for _ in tags)

        scars = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT context_tag, failed_assumption, enforced_rule, timestamp 
                FROM scar_canon 
                WHERE context_tag IN ({placeholders})
            """,
                tags,
            )

            for row in cursor.fetchall():
                scars.append(
                    {
                        "context_tag": row["context_tag"],
                        "failed_assumption": row["failed_assumption"],
                        "enforced_rule": row["enforced_rule"],
                        "scar_date": row["timestamp"],
                    }
                )
        return scars
