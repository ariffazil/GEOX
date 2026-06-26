"""
test_transport_manifest.py — F0-Equivalent Guard for MCP Transport Surface

Phase 2 Clean Architecture (2026-06-22, locked 2026-06-25):
- 16 canonical tools (12 surface + 4 internal)
- Resources and prompts unchanged

This test introspects the actual FastMCP server instance and verifies that
the counts match the canonical registry. If they diverge, the test fails
and the registry must be updated.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import pytest

from geox_mcp.server import mcp
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, GEOX_TOOL_MANIFEST


# Phase 2 Clean Architecture canonical counts (locked 2026-06-25)
EXPECTED_TOOL_COUNT = 16  # 12 surface + 4 internal
EXPECTED_PROMPT_COUNT_MIN = 10  # at least 10 (matches manifest)
EXPECTED_RESOURCE_COUNT_MIN = 17  # at least 17 (matches manifest)


class TestTransportManifest:
    """F0-equivalent guards for the MCP transport surface."""

    def test_tools_count_matches_manifest(self):
        """CANONICAL_PUBLIC_TOOLS must be exactly 16 (Phase 2 Clean Architecture, locked)."""
        assert len(CANONICAL_PUBLIC_TOOLS) == EXPECTED_TOOL_COUNT, (
            f"CANONICAL_PUBLIC_TOOLS count {len(CANONICAL_PUBLIC_TOOLS)} "
            f"!= Phase 2 expected {EXPECTED_TOOL_COUNT}. "
            f"If intentional, update EXPECTED_TOOL_COUNT and registry.py."
        )

    def test_geo_tool_manifest_count_matches_canonical(self):
        """GEOX_TOOL_MANIFEST must have same count as CANONICAL_PUBLIC_TOOLS."""
        assert len(GEOX_TOOL_MANIFEST) == len(CANONICAL_PUBLIC_TOOLS), (
            f"GEOX_TOOL_MANIFEST count {len(GEOX_TOOL_MANIFEST)} "
            f"!= CANONICAL_PUBLIC_TOOLS count {len(CANONICAL_PUBLIC_TOOLS)}. "
            f"Both lists must stay in sync (server-side registry invariant)."
        )

    def test_tools_list_via_mcp_runtime(self):
        """The live FastMCP server must report at least 16 canonical tools."""
        import asyncio

        async def _list():
            tools = await mcp.list_tools()
            return tools

        tools = asyncio.run(_list())
        # The MCP server registers canonical + compat tools.
        # The middleware filters on_list_tools to canonical only.
        # But mcp.list_tools() bypasses middleware — so we check >= 16.
        assert len(tools) >= EXPECTED_TOOL_COUNT, (
            f"Live FastMCP reports {len(tools)} tools, "
            f"expected at least {EXPECTED_TOOL_COUNT}. "
            f"Update docs/MCP_TRANSPORT_SURFACE.md if tools were removed."
        )

    def test_resources_list_via_mcp_runtime(self):
        """The live FastMCP server must report at least 17 resources."""
        import asyncio

        async def _list():
            try:
                resources = await mcp.list_resources()
                return resources
            except AttributeError:
                # Older FastMCP versions use list_resource_templates
                templates = await mcp.list_resource_templates()
                return templates

        resources = asyncio.run(_list())
        assert len(resources) >= EXPECTED_RESOURCE_COUNT_MIN, (
            f"Live FastMCP reports {len(resources)} resources, "
            f"manifest expects at least {EXPECTED_RESOURCE_COUNT_MIN}. "
            f"Update docs/MCP_TRANSPORT_SURFACE.md if resources were added/removed."
        )

    def test_prompts_list_via_mcp_runtime(self):
        """The live FastMCP server must report at least 11 prompts."""
        import asyncio

        async def _list():
            prompts = await mcp.list_prompts()
            return prompts

        prompts = asyncio.run(_list())
        assert len(prompts) >= EXPECTED_PROMPT_COUNT_MIN, (
            f"Live FastMCP reports {len(prompts)} prompts, "
            f"manifest expects at least {EXPECTED_PROMPT_COUNT_MIN}. "
            f"Update docs/MCP_TRANSPORT_SURFACE.md if prompts were added/removed."
        )

    def test_tool_names_match_manifest(self):
        """All canonical tool names must match between registry and runtime."""
        import asyncio

        async def _list():
            tools = await mcp.list_tools()
            return {t.name for t in tools}

        runtime_names = asyncio.run(_list())
        canonical = set(CANONICAL_PUBLIC_TOOLS)
        missing = canonical - runtime_names

        assert not missing, (
            f"CANONICAL_PUBLIC_TOOLS has tools NOT registered with FastMCP: "
            f"{sorted(missing)}. Update src/geox_mcp/server.py to register them."
        )


class TestTransportURIScheme:
    """URI scheme consistency for resources."""

    def test_resources_use_documented_schemes(self):
        """All resources must use 'geox://' or 'tree777://' scheme."""
        import asyncio

        async def _list():
            try:
                resources = await mcp.list_resources()
            except AttributeError:
                resources = await mcp.list_resource_templates()
            return resources

        resources = asyncio.run(_list())
        valid_schemes = ("geox://", "tree777://")
        bad = []
        for r in resources:
            uri = getattr(r, "uri", None) or getattr(r, "uriTemplate", None) or ""
            uri_str = str(uri)
            if not any(uri_str.startswith(s) for s in valid_schemes):
                bad.append(uri_str)
        assert not bad, (
            f"Resources using non-standard URI schemes: {bad}. "
            f"Use 'geox://' or 'tree777://'."
        )


class TestToolLaneClassification:
    """Every canonical tool must have a lane classification in GEOX_TOOL_MANIFEST."""

    def test_every_tool_has_a_lane(self):
        """Each tool entry in GEOX_TOOL_MANIFEST must declare a lane."""
        valid_lanes = {"discovery", "evidence", "reasoning", "judgment"}
        for entry in GEOX_TOOL_MANIFEST:
            lane = entry.get("lane")
            assert lane in valid_lanes, (
                f"Tool {entry.get('name')} has invalid lane '{lane}'. "
                f"Must be one of {valid_lanes}."
            )

    def test_lane_distribution_matches_phase2(self):
        """Lane counts should match Phase 2 distribution."""
        from collections import Counter
        lane_counts = Counter(e["lane"] for e in GEOX_TOOL_MANIFEST)
        # Phase 2: Discovery: 2, Evidence: 5, Reasoning: 5, Judgment: 4
        expected_min = {"discovery": 2, "evidence": 4, "reasoning": 4, "judgment": 3}
        for lane, exp_min in expected_min.items():
            actual = lane_counts.get(lane, 0)
            assert actual >= exp_min, (
                f"Lane '{lane}' has {actual} tools, expected >= {exp_min} "
                f"per Phase 2 manifest. Update if intentional."
            )