"""
REGISTRY/RUNTIME TRUTH TEST — F2 TRUTH enforcer
================================================
Every tool advertised by CANONICAL_PUBLIC_TOOLS must be callable via
FastMCP. If a tool is in the list but the runtime returns UnknownTool,
this test FAILS.

This is the single most important contract test in GEOX.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

import pytest
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
from geox_mcp.server import mcp  # the live FastMCP instance


class TestRegistryRuntimeTruth:
    """Every canonical tool must be callable at runtime."""

    @pytest.mark.asyncio
    async def test_all_canonical_tools_are_registered(self):
        """Every CANONICAL_PUBLIC_TOOLS entry must be findable in FastMCP's tool list."""
        registered_tools = {t.name for t in await mcp.list_tools()}
        canonical_set = set(CANONICAL_PUBLIC_TOOLS)

        missing = canonical_set - registered_tools
        extra = registered_tools - canonical_set

        assert not missing, (
            f"F2 TRUTH VIOLATION: {len(missing)} tool(s) advertised in "
            f"CANONICAL_PUBLIC_TOOLS but NOT registered with FastMCP runtime:\n"
            + "\n".join(f"  - {t}" for t in sorted(missing))
        )

        # Extra tools are informational only — not a failure
        if extra:
            print(f"Note: {len(extra)} tool(s) registered but not in CANONICAL_PUBLIC_TOOLS (may be internal):")
            for t in sorted(extra):
                print(f"  - {t}")

    @pytest.mark.asyncio
    async def test_registry_count_matches_canonical(self):
        """The total number of registered canonical tools must match CANONICAL_PUBLIC_TOOLS."""
        registered_tools = {t.name for t in await mcp.list_tools()}
        canonical_set = set(CANONICAL_PUBLIC_TOOLS)
        overlap = registered_tools & canonical_set
        assert len(overlap) == len(canonical_set), (
            f"Canonical count {len(canonical_set)} but only {len(overlap)} "
            f"are registered in FastMCP runtime."
        )


class TestNoGhostAliases:
    """Legacy aliases must route to real canonical tools."""

    @pytest.mark.asyncio
    async def test_legacy_aliases_map_to_registered_tools(self):
        """Every alias in LEGACY_ALIAS_MAP must point to a registered canonical tool."""
        from geox_mcp.registry import LEGACY_ALIAS_MAP

        registered_tools = {t.name for t in await mcp.list_tools()}

        for alias, canonical in LEGACY_ALIAS_MAP.items():
            assert canonical in registered_tools, (
                f"Alias '{alias}' -> '{canonical}' but '{canonical}' is not "
                f"registered in FastMCP runtime."
            )


class TestSystemRegistryTruth:
    """geox_system_registry_status must self-report consistent truth."""

    @pytest.mark.asyncio
    async def test_registry_tool_self_reports_truth(self):
        """The registry_status tool must report registry_truth: PASS."""
        from geox_mcp.tools.registry import geox_system_registry_status

        result = await geox_system_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))

        assert payload.get("registry_truth") == "PASS", (
            f"System registry reports {payload.get('registry_truth')} — "
            f"should be PASS. Phantom tools: {payload.get('phantom_tools', [])}"
        )

    @pytest.mark.asyncio
    async def test_no_phantom_tools(self):
        """geox_system_registry_status must report zero phantom tools."""
        from geox_mcp.tools.registry import geox_system_registry_status

        result = await geox_system_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))

        phantom = payload.get("phantom_tools", [])
        assert len(phantom) == 0, (
            f"F2 TRUTH VIOLATION: {len(phantom)} phantom tool(s) detected: {phantom}"
        )
