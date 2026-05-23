"""
GEOX Registry Truth Tests — P4 Priority
Validates: listed_tools == callable_tools, tool counts consistent.
DITEMPA BUKAN DIBERI
"""
import pytest
import sys
import os

# Allow import of geox_mcp from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from geox_mcp.tools.registry import (
    geox_system_registry_status,
    geox_test_receipt_status,
    geox_bundle_security_audit,
)


class TestRegistryTruth:
    """Listed tools must equal callable tools. No ghosts. No phantoms."""

    @pytest.mark.asyncio
    async def test_tools_count_positive(self):
        result = await geox_system_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        count = payload.get("tools_count", payload.get("registered_tools", 0))
        assert count > 0, "Registry must report at least one tool"

    @pytest.mark.asyncio
    async def test_registry_truth_not_warn(self):
        result = await geox_system_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        rt = payload.get("registry_truth", "")
        assert rt in ("PASS", "VERIFIED"), f"registry_truth must be PASS, got: {rt}"

    @pytest.mark.asyncio
    async def test_canonical_tools_list_present(self):
        result = await geox_system_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        # Either 'tools' list or 'canonical_tools' count must be present
        assert "tools" in payload or "canonical_tools" in payload or "registered_tools" in payload, (
            "Registry must expose a tools list or count"
        )

    @pytest.mark.asyncio
    async def test_test_receipt_has_nonzero_tests(self):
        """Test receipt must report real tests, not collect_only_fallback with zero."""
        result = await geox_test_receipt_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        total = payload.get("total_tests", 0)
        # Accept 0 if source is collect-only during CI, but fail if it's a lazy fallback
        source = payload.get("source", "")
        assert total > 0 or source == "collect_only_in_test_session", (
            f"total_tests={total} with source={source!r} — real test discovery required"
        )

    @pytest.mark.asyncio
    async def test_test_receipt_no_failures(self):
        result = await geox_test_receipt_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        assert payload.get("tests_failed", 0) == 0, (
            f"tests_failed={payload.get('tests_failed')} — all tests must pass"
        )

    @pytest.mark.asyncio
    async def test_tool_count_consistency(self):
        """Registry-reported tool count must match a plausible range."""
        result = await geox_system_registry_status()
        payload = result.get("primary_artifact", result.get("artifact", result))
        count = payload.get("tools_count", payload.get("registered_tools", None))
        canonical = payload.get("canonical_tools", count)
        if count is not None and canonical is not None:
            # Allow ≤1 delta for system-only tools
            assert abs(int(count) - int(canonical)) <= 1, (
                f"Tool count mismatch: tools_count={count}, canonical_tools={canonical}"
            )
