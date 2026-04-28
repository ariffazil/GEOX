"""
MCP wrapper for LAS ingestion.
"""

from __future__ import annotations

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.services.las_ingestor import LASIngestor


def geox_ingest_las_tool(path: str, asset_id: str | None = None, chunk_size: int = 200) -> dict:
    manifest = LASIngestor().ingest(path=path, asset_id=asset_id, chunk_size=chunk_size).to_dict()
    manifest["claim_tag"] = classify_claim_tag(0.8 if manifest["qcfail_count"] == 0 else 0.55, hold_enforced=manifest["qcfail_count"] > 0)
    manifest["vault_receipt"] = make_vault_receipt("geox_ingest_las", manifest, verdict="HOLD" if manifest["qcfail_count"] > 0 else "SEAL")
    return manifest
