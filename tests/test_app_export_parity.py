"""App / plugin export must equal the 24-tool canonical public surface.

ZEN-24 rule: public MCP surface == plugin export == documentation snapshot.
No phantom plugin-only names. No missing canonical exports.
Resurrected 2026-07-16: 9 tools restored (basin_backstrip, claim_graph_evaluate,
contradiction_scan, evidence, falsify, lem_predict, sediment_mass_balance,
thermal_maturity_history, to_wealth_bridge).
"""

from __future__ import annotations

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
from geox_mcp.surface_manifest import plugin_export_tool_names, public_tool_names
from geox_mcp.tools.registry import geox_system_registry_status


class TestAppExportParity:
    def test_surface_counts_remain_frozen_at_zen24(self):
        exported_app_tools = plugin_export_tool_names()
        public_mcp_tools = list(CANONICAL_PUBLIC_TOOLS)
        manifest_public = public_tool_names()

        assert len(exported_app_tools) == 33
        assert len(public_mcp_tools) == 33
        assert len(manifest_public) == 33
        assert set(exported_app_tools) == set(public_mcp_tools) == set(manifest_public)

        # Required canonical names (must not vanish from app export)
        for required in (
            "geox_claim",
            "geox_gravmag_studio",
            "geox_prospect",
            "geox_well_desk",
            "geox_basin_backstrip",
            "geox_evidence",
            "geox_falsify",
        ):
            assert required in exported_app_tools

        # Phantom pre-ZEN-24 plugin names must not reappear
        # (2026-07-25 update: geox_well_qc and geox_gravmag_studio
        #  are now canonical — moved out of phantom list)
        for phantom in (
            "geox_vision",
            "geox_map_context_scene",
            "geox_material_truth_challenge",
            "geox_cascade_pathway",
            "geox_feedback_integrity",
            "geox_well_desk_open",
            "geox_gravmag_studio_open",
        ):
            assert phantom not in exported_app_tools

    async def test_registry_truth_is_pass_when_surfaces_aligned(self):
        status = await geox_system_registry_status(session_id="SEAL-workspace", actor_id="ARIF")
        assert status["registry_truth"] == "PASS"
        assert status["plugin_export_only_tools"] == []
        assert status["missing_from_app_export"] == []
        assert status["phantom_tools"] == []
        assert set(status["plugin_export_public"]) == set(CANONICAL_PUBLIC_TOOLS)
        assert set(status["expected_app_export"]) == set(CANONICAL_PUBLIC_TOOLS)
        assert set(status["manifest_public"]) == set(CANONICAL_PUBLIC_TOOLS)
        # Deterministic registry inspection must not tag as UNKNOWN
        assert status.get("perception_class") == "OBSERVED"
        assert status.get("confidence_level") == "HIGH"
