"""2026-09-06 — GEOX four-failure cluster: map NameError + basin ok:true lie."""
from __future__ import annotations

import asyncio

from geox_mcp.tools.earth_map import geox_map_layers_list
from geox_mcp.tools.mcp_apps_bridge import compact_structured_for_ui


def test_map_layers_list_sunda_strait_does_not_crash():
    result = asyncio.run(geox_map_layers_list(bbox=[104.5, -7.0, 106.5, -5.5]))
    assert "error" not in result or result.get("ok") is True or result.get("status") == "OK"
    assert "layers" in result
    assert result.get("layer_count", 0) >= 0


def test_compact_ui_does_not_stamp_ok_true_on_error_envelope():
    envelope = {
        "execution_status": "ERROR",
        "primary_artifact": {
            "tool": "geox_basin_profile",
            "error": "Basin data not found for: Sunda",
        },
    }
    compact = compact_structured_for_ui(envelope, tool="geox_basin", app_id="basin_explorer")
    assert compact["ok"] is False
    assert "Basin data not found" in str(compact.get("error", ""))


def test_compact_ui_preserves_true_success():
    compact = compact_structured_for_ui(
        {"ok": True, "basin_name": "Malay Basin", "status": "OK"},
        tool="geox_basin",
        app_id="basin_explorer",
    )
    assert compact["ok"] is True
    assert compact["basin_name"] == "Malay Basin"
