from geox.geox_mcp.server import geox_earth3d_load_volume
from geox.geox_mcp.tools.visualization import (
    geox_render_log_track_tool,
    geox_render_volume_slice_tool,
)


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
