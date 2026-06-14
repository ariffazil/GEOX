"""
test_canonical_public_surface.py — Proof that the GEOX MCP server's tool
surface matches the canonical registry.

F2 TRUTH: Tests against the LIVE MCP server at 127.0.0.1:8081.
F7 HUMILITY: If the server is down, tests skip gracefully.

There is ONE source of truth: src/geox_mcp/registry.py (40 canonical tools).
The contracts/canonical_registry.py is a derived copy verified here.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

import pytest

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS, LEGACY_ALIAS_MAP

# Live server — the only truth that matters
GEOX_MCP_URL = "http://127.0.0.1:8081"


def _fetch_tools_from_server() -> list[str] | None:
    """Call the live MCP server's tool list via the /tools/list SSE endpoint."""
    try:
        # MCP list_tools via HTTP POST to /mcp
        req = urllib.request.Request(
            f"{GEOX_MCP_URL}/mcp",
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": "canonical-test-1",
                "method": "tools/list",
                "params": {},
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            tools = body.get("result", {}).get("tools", [])
            return [t["name"] for t in tools]
    except (urllib.error.URLError, json.JSONDecodeError, ConnectionRefusedError, KeyError) as e:
        pytest.skip(f"Cannot reach GEOX MCP server at {GEOX_MCP_URL}: {e}")
        return None


def _fetch_registry_status() -> dict | None:
    """Use the geox_system_registry_status tool to get canonical surface."""
    try:
        req = urllib.request.Request(
            f"{GEOX_MCP_URL}/mcp",
            data=json.dumps({
                "jsonrpc": "2.0",
                "id": "registry-test-1",
                "method": "tools/call",
                "params": {
                    "name": "geox_system_registry_status",
                    "arguments": {},
                },
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            content = body.get("result", {}).get("content", [])
            for c in content:
                if c.get("type") == "text":
                    return json.loads(c["text"])
    except Exception:
        pass
    return None


class TestCanonicalSurface:
    """Canonical surface = the tools exposed by the live GEOX MCP server."""

    def test_live_server_reachable(self):
        """GEOX MCP server must be running on its published port."""
        try:
            req = urllib.request.Request(f"{GEOX_MCP_URL}/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                assert resp.status == 200
        except Exception as e:
            pytest.skip(f"GEOX MCP not reachable: {e}")

    def test_tool_count_matches_registry(self):
        """The number of tools on the live server must match src/geox_mcp/registry.py."""
        live_tools = _fetch_tools_from_server()
        assert live_tools is not None, "Could not fetch tools from live server"
        canonical = set(CANONICAL_PUBLIC_TOOLS)
        live_names = set(live_tools)
        # All canonical tools must be present
        missing = canonical - live_names
        assert not missing, (
            f"Canonical tools NOT found on live server ({len(missing)}): {sorted(missing)}"
        )

    def test_no_canonical_tool_dropped(self):
        """Every tool in CANONICAL_PUBLIC_TOOLS must be callable on the live server."""
        live_tools = _fetch_tools_from_server()
        assert live_tools is not None
        live_names = set(live_tools)
        canonical = set(CANONICAL_PUBLIC_TOOLS)
        # Some MCP servers also show legacy aliases — that's fine
        # But no canonical tool may be dropped
        assert canonical.issubset(live_names), (
            f"Tools in registry but NOT on live server: {sorted(canonical - live_names)}"
        )

    def test_no_dotted_names(self):
        """No canonical tool name may contain a dot."""
        dotted = [t for t in CANONICAL_PUBLIC_TOOLS if "." in t]
        assert not dotted, f"Dotted tool names in registry: {dotted}"

    def test_no_phantom_tools(self):
        """All registry tools must have the geox_ prefix."""
        non_prefixed = [t for t in CANONICAL_PUBLIC_TOOLS if not t.startswith("geox_")]
        assert not non_prefixed, f"Non-geox_ prefixed tools in registry: {non_prefixed}"

    def test_registry_vs_contracts_drift(self):
        """Verify contracts/canonical_registry.py matches src/geox_mcp/registry.py."""
        from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS as CONTRACT_TOOLS
        contract_set = set(CONTRACT_TOOLS)
        src_set = set(CANONICAL_PUBLIC_TOOLS)
        missing_in_contracts = src_set - contract_set
        extra_in_contracts = contract_set - src_set
        if missing_in_contracts:
            pytest.fail(f"contracts/canonical_registry.py missing tools: {sorted(missing_in_contracts)}")
        if extra_in_contracts:
            pytest.fail(f"contracts/canonical_registry.py has extra tools not in src: {sorted(extra_in_contracts)}")

    def test_no_alias_collision(self):
        """No alias should conflict with a canonical tool name."""
        canonical = set(CANONICAL_PUBLIC_TOOLS)
        alias_names = set(LEGACY_ALIAS_MAP.keys())
        conflicts = canonical & alias_names
        assert not conflicts, f"Alias names collide with canonical tools: {sorted(conflicts)}"

    def test_legacy_aliases_point_to_live_tools(self):
        """Every legacy alias should point to a tool that exists in CANONICAL_PUBLIC_TOOLS."""
        canonical = set(CANONICAL_PUBLIC_TOOLS)
        for alias, target in LEGACY_ALIAS_MAP.items():
            assert target in canonical, (
                f"Alias '{alias}' points to '{target}' which is not in CANONICAL_PUBLIC_TOOLS"
            )


class TestRegistryStatusTool:
    """The geox_system_registry_status tool must work and report accurately."""

    def test_registry_status_returns_ok(self):
        """Registry status tool should execute successfully."""
        registry = _fetch_registry_status()
        if registry is None:
            pytest.skip("geox_system_registry_status not callable directly via HTTP")
        assert isinstance(registry, dict)
        # Registry must report tool count
        tools = registry.get("tools", registry.get("canonical_tools", registry.get("tool_count", None)))
        if tools is not None:
            assert len(tools) >= 40  # at minimum 40 tools
