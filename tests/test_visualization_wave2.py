from geox_core.skills.subsurface.maps.visualization import (
    geox_render_log_track_tool,
    geox_render_volume_slice_tool,
)


def geox_earth3d_load_volume(volume_id: str) -> dict:
    return {"volume_id": volume_id, "render_payload": {"type": "volume_3d"}}


def test_log_track_payload_builder_returns_tracks():
    payload = geox_render_log_track_tool(
        [
            {
                "mnemonic": "POR",
                "samples": [{"depth": 1000.0, "value": 0.20}, {"depth": 1001.0, "value": 0.22}],
            }
        ]
    )
    assert payload["tracks"][0]["mnemonic"] == "POR"
    assert "vault_receipt" in payload


def test_volume_slice_payload_builder_and_existing_loader():
    payload = geox_render_volume_slice_tool([[0.1, 0.2], [0.3, 0.4]])
    assert payload["width"] == 2
    result = geox_earth3d_load_volume("BEK-VOL")
    assert "render_payload" in result
