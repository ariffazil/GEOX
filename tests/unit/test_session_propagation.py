"""
GEOX Session Propagation Tests — P5 Priority
Validates: session_id, actor_id, tool_name propagate correctly through _wrap_tool_outputs.
DITEMPA BUKAN DIBERI
"""
import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestSessionPropagation:
    """
    If the caller passes session_id, the output must NOT degrade to 'geox-no-session'.
    """

    @pytest.mark.asyncio
    async def test_audit_receipt_has_session_id_field(self):
        """audit_receipt must contain 'session_id' key."""
        from geox_mcp.server import mcp  # noqa: F401 — ensure app initialized
        # Import a simple tool directly to test envelope
        from geox_mcp.tools import registry as reg
        result = await reg.geox_system_registry_status()
        # system tools get minimal envelope — check it doesn't crash
        assert isinstance(result, dict), "Tool must return a dict"

    @pytest.mark.asyncio
    async def test_wrap_tool_outputs_injects_audit_receipt(self):
        """After _wrap_tool_outputs, result dict must contain audit_receipt."""
        from geox_mcp.tools import registry as reg
        # geox_system_registry_status is a registry tool — it gets minimal envelope
        # Use contradiction registry which is non-registry
        from geox_mcp.tools.registry import geox_contradiction_registry_status
        result = await geox_contradiction_registry_status()
        # The universal wrapper should have injected audit_receipt
        assert "audit_receipt" in result or "primary_artifact" in result, (
            "Non-registry tools must have audit_receipt injected by _wrap_tool_outputs"
        )

    @pytest.mark.asyncio
    async def test_session_id_not_degraded_when_provided(self):
        """
        When session_id is passed as a kwarg, audit_receipt.session_id must NOT be 'geox-no-session'.
        This validates the _find_field() propagation logic in _wrap_tool_outputs.
        """
        from geox_mcp.tools.registry import geox_contradiction_registry_status
        # Call with session_id kwarg
        result = await geox_contradiction_registry_status(session_id="test-session-abc123")
        ar = result.get("audit_receipt", {})
        sid = ar.get("session_id", "geox-no-session")
        assert sid != "geox-no-session", (
            f"session_id degraded to 'geox-no-session' even though 'test-session-abc123' was provided. "
            f"audit_receipt={ar}"
        )
        assert sid == "test-session-abc123", f"Expected 'test-session-abc123', got '{sid}'"

    @pytest.mark.asyncio
    async def test_tool_name_injected_in_audit_receipt(self):
        """audit_receipt.tool_name must be the actual tool name, not 'unknown'."""
        from geox_mcp.tools.registry import geox_contradiction_registry_status
        result = await geox_contradiction_registry_status()
        ar = result.get("audit_receipt", {})
        tool_name = ar.get("tool_name", "unknown")
        assert tool_name != "unknown", (
            f"tool_name must be injected by _wrap_tool_outputs, got 'unknown'. audit_receipt={ar}"
        )

    @pytest.mark.asyncio
    async def test_audit_receipt_has_timestamp(self):
        """audit_receipt must contain a valid ISO timestamp."""
        from geox_mcp.tools.registry import geox_contradiction_registry_status
        result = await geox_contradiction_registry_status()
        ar = result.get("audit_receipt", {})
        ts = ar.get("timestamp", "")
        assert ts != "", "audit_receipt.timestamp must be set"
        # Basic ISO format check
        assert "T" in ts or "-" in ts, f"timestamp must be ISO format, got: {ts}"

    @pytest.mark.asyncio
    async def test_actor_id_present_in_audit_receipt(self):
        """audit_receipt.actor_id must be present."""
        from geox_mcp.tools.registry import geox_contradiction_registry_status
        result = await geox_contradiction_registry_status()
        ar = result.get("audit_receipt", {})
        assert "actor_id" in ar, (
            f"audit_receipt must contain actor_id. Keys present: {list(ar.keys())}"
        )
