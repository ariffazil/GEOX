from __future__ import annotations

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
from geox_mcp.surface_manifest import plugin_export_tool_names
from geox_mcp.tools.registry import geox_system_registry_status


class TestAppExportParity:
    def test_surface_counts_remain_frozen(self):
        exported_app_tools = plugin_export_tool_names()
        public_mcp_tools = CANONICAL_PUBLIC_TOOLS

        assert len(exported_app_tools) == 17
        assert len(public_mcp_tools) == 28
        assert "geox_map_context_scene" in exported_app_tools

    async def test_registry_truth_stays_pass(self):
        status = await geox_system_registry_status(session_id="SEAL-workspace", actor_id="ARIF")
        assert status["registry_truth"] == "PASS"
        assert len(status["plugin_export_public"]) == 17
        assert len(status["manifest_public"]) == 28
