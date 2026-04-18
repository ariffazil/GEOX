import pytest

from geox.services.asset_memory import AssetMemoryStore


def test_asset_memory_store_and_recall(tmp_path):
    db_path = tmp_path / "asset-memory.sqlite"
    store = AssetMemoryStore(str(db_path))
    stored = store.store_record(
        asset_id="BEK-2",
        eval_type="petrophysics",
        payload={"net_pay_m": 80},
        vault_receipt="receipt-1",
        authorized=True,
    )
    recalled = store.recall_asset("BEK-2")
    assert stored["stored"] is True
    assert len(recalled) == 1
    assert recalled[0].payload["net_pay_m"] == 80


def test_asset_memory_store_requires_auth(tmp_path):
    store = AssetMemoryStore(str(tmp_path / "asset-memory.sqlite"))
    with pytest.raises(PermissionError):
        store.store_record("BEK-2", "petrophysics", {"net_pay_m": 80}, "receipt-1", authorized=False)
