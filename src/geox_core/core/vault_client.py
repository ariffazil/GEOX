"""
GEOX Vault Client — Simple File-Backed JSONL Vault
DITEMPA BUKAN DIBERI

Provides tamper-evident product storage and lookup for inter-product
dependency resolution and SEAL audit trails.
"""

import json
import os
from typing import Dict, Any, Optional


DEFAULT_VAULT_PATH = os.path.expanduser("~/.geox/vault.jsonl")


class VaultClient:
    """
    Minimal append-only vault for GEOX canonical products.
    Each line is a JSON object: {"product_id": ..., "version": ..., ...}
    """

    def __init__(self, vault_path: str = DEFAULT_VAULT_PATH):
        self.vault_path = vault_path
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)

    def _read_all(self) -> list[Dict[str, Any]]:
        if not os.path.exists(self.vault_path):
            return []
        records = []
        with open(self.vault_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Return the latest record for a given product_id."""
        records = self._read_all()
        # Return the last matching record (latest version wins)
        for record in reversed(records):
            if record.get("product_id") == product_id:
                return record
        return None

    def get_products_by_type(self, product_type: str) -> list[Dict[str, Any]]:
        """Return all records for a given product_type, latest first."""
        records = self._read_all()
        return [r for r in reversed(records) if r.get("product_type") == product_type]

    def seal_product(self, product: Dict[str, Any]) -> None:
        """Append a product record to the vault."""
        with open(self.vault_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(product, ensure_ascii=False) + "\n")

    def list_products(self, limit: int = 100) -> list[Dict[str, Any]]:
        """Return the latest N product records."""
        records = self._read_all()
        return records[-limit:][::-1]
