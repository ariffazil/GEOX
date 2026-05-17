from geox.skills.subsurface.asset_memory_tool import (
    geox_memory_recall_asset_tool,
    geox_memory_store_asset_tool,
)
from geox.services.asset_memory import AssetMemoryStore

_store = AssetMemoryStore()


def geox_memory_store_asset(
    asset_id: str,
    eval_type: str,
    payload: dict,
    amanah_locked: bool = False,
    **_: object,
) -> dict:
    return _store.store(
        asset_id=asset_id,
        eval_type=eval_type,
        payload=payload,
        amanah_locked=amanah_locked,
    ).to_dict()


def geox_memory_recall_asset(
    asset_id: str,
    eval_type: str | None = None,
    query: str | None = None,
    limit: int = 10,
    **_: object,
) -> dict:
    return _store.recall(
        asset_id=asset_id,
        eval_type=eval_type,
        query=query,
        limit=limit,
    ).to_dict()

__all__ = [
    "geox_memory_recall_asset_tool",
    "geox_memory_store_asset_tool",
    "geox_memory_store_asset",
    "geox_memory_recall_asset",
]
