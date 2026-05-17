"""
MCP wrappers for GEOX asset memory.
"""

from __future__ import annotations

from geox.core.governed_output import classify_claim_tag, make_vault_receipt
from geox.services.asset_memory import AssetMemoryStore


def geox_memory_store_asset_tool(
    asset_id: str,
    eval_type: str,
    payload: dict,
    db_path: str = "asset_memory.db",
    authorized: bool = False,
) -> dict:
    receipt = make_vault_receipt("geox_memory_store_asset", payload)
    store = AssetMemoryStore(db_path=db_path)
    result = store.store_record(
        asset_id=asset_id,
        eval_type=eval_type,
        payload=payload,
        vault_receipt=receipt["hash"],
        authorized=authorized,
    )
    result["claim_tag"] = classify_claim_tag(0.85)
    result["vault_receipt"] = receipt
    return result


def geox_memory_recall_asset_tool(
    asset_id: str,
    eval_type: str | None = None,
    query: str | None = None,
    db_path: str = "asset_memory.db",
    limit: int = 10,
) -> dict:
    store = AssetMemoryStore(db_path=db_path)
    records = [record.to_dict() for record in store.recall_asset(asset_id=asset_id, eval_type=eval_type, query=query, limit=limit)]
    payload = {"asset_id": asset_id, "count": len(records), "query": query}
    return {
        "asset_id": asset_id,
        "count": len(records),
        "records": records,
        "claim_tag": classify_claim_tag(0.8 if records else 0.2),
        "vault_receipt": make_vault_receipt("geox_memory_recall_asset", payload, verdict="SEAL" if records else "QUALIFY"),
    }
