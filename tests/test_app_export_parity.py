from __future__ import annotations

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
from geox_mcp.surface_manifest import plugin_export_tool_names
from geox_mcp.tools.registry import geox_system_registry_status


class TestAppExportParity:
    def test_surface_counts_remain_frozen(self):
        exported_app_tools = plugin_export_tool_names()
        public_mcp_tools = CANONICAL_PUBLIC_TOOLS

        assert len(exported_app_tools) == 23
        assert len(public_mcp_tools) == 32
        assert "geox_map_context_scene" in exported_app_tools

    async def test_registry_truth_reports_unwired_app_exports(self):
        status = await geox_system_registry_status(session_id="SEAL-workspace", actor_id="ARIF")
        assert status["registry_truth"] == "DRIFT"
        assert len(status["plugin_export_public"]) == 17
        assert len(status["manifest_public"]) == 32
        assert set(status["missing_from_app_export"]) == {
            "geox_cascade_pathway",
            "geox_claim_graph_evaluate",
            "geox_consequence_footprint",
            "geox_feedback_integrity",
            "geox_material_truth_challenge",
            "geox_optionality_loss",
        }
