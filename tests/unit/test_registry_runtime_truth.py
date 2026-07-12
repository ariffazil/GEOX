from __future__ import annotations

from geox_mcp.registry import CANONICAL_COMPAT_TOOLS, CANONICAL_PUBLIC_TOOLS, INTERNAL_TOOLS
from geox_mcp.server import create_app, mcp
from geox_mcp.surface_manifest import plugin_export_tool_names
from geox_mcp.tools.registry import geox_system_registry_status

create_app()


class TestRegistryRuntimeTruth:
    async def test_runtime_public_surface_equals_manifest_public(self):
        registered = {tool.name for tool in await mcp.list_tools()}
        manifest_public = set(CANONICAL_PUBLIC_TOOLS)
        assert registered == manifest_public

    async def test_internal_and_compat_do_not_leak_into_public_list(self):
        registered = {tool.name for tool in await mcp.list_tools()}
        assert not (registered & set(INTERNAL_TOOLS))
        assert not (registered & set(CANONICAL_COMPAT_TOOLS))

    async def test_registry_status_reports_no_drift(self):
        status = await geox_system_registry_status(session_id="SEAL-registry", actor_id="ARIF")
        assert status["registry_truth"] == "PASS"
        assert status["phantom_tools"] == []
        assert status["missing_from_manifest"] == []
        assert status["missing_from_app_export"] == []
        assert status["manifest_only_tools"] == []
        assert status["runtime_only_tools"] == []
        assert status["mcp_list_only_tools"] == []
        assert status["plugin_export_only_tools"] == []
        assert set(status["manifest_public"]) == set(CANONICAL_PUBLIC_TOOLS)
        assert set(status["runtime_callable_public"]) == set(CANONICAL_PUBLIC_TOOLS)
        assert set(status["mcp_tools_list_public"]) == set(CANONICAL_PUBLIC_TOOLS)
        assert set(status["plugin_export_public"]) == set(plugin_export_tool_names())
        assert set(status["expected_app_export"]) == set(plugin_export_tool_names())
        assert status["physics_guard"]["guard_passed"] is True
