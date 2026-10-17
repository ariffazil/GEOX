"""Tests for P0 self-healing recovery hints in GEOX error envelopes.

Verifies:
  - SCHEMA_REJECTION errors include recovery.available (field names) when Pydantic errors present
  - _extract_recovery_from_error handles Pydantic ValidationError, TypeError, KeyError
  - Recovery fields are bounded at MAX_RECOVERY_FIELDS
  - Internal session_id/actor_id/trace_id fields are excluded from recovery
  - build_governed_error_envelope passes recovery through to output
  - Layer 1.5: tool_schema introspection + fuzzy matching
"""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, Field, ValidationError


# ── Minimal Pydantic model to trigger validation errors ─────────────────────
class SampleToolInput(BaseModel):
    basin_name: str = Field(description="Name of the basin")
    formation: str = Field(description="Geological formation")
    mode: str = Field(default="profile", description="Query mode")
    limit: int = Field(default=10, description="Max results")
    session_id: str | None = Field(default=None)
    actor_id: str | None = Field(default=None)
    trace_id: str | None = Field(default=None)


SAMPLE_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "basin_name": {"type": "string", "description": "Name of the basin"},
        "formation": {"type": "string", "description": "Geological formation"},
        "mode": {"type": "string", "description": "Query mode"},
        "limit": {"type": "integer", "description": "Max results"},
        "session_id": {"type": "string"},
        "actor_id": {"type": "string"},
        "trace_id": {"type": "string"},
    },
}


# ── Import the functions under test ─────────────────────────────────────────
from geox_mcp.geox_middleware import (
    _extract_recovery_from_error,
    build_governed_error_envelope,
)


class TestExtractRecoveryFromError:
    """_extract_recovery_from_error extracts field names from exceptions."""

    def test_pydantic_validation_error(self):
        """Pydantic ValidationError with wrong field types → rejected_fields + available."""
        with pytest.raises(ValidationError) as exc_info:
            SampleToolInput(basin_name=123, formation=456, mode=789)  # type: ignore[arg-type]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_basin", tool_schema=SAMPLE_TOOL_SCHEMA)
        assert recovery is not None
        assert len(recovery["rejected_fields"]) > 0
        assert recovery["retryable"] is True

    def test_pydantic_missing_required_field(self):
        """Missing required field → rejected_fields populated."""
        with pytest.raises(ValidationError) as exc_info:
            SampleToolInput()  # type: ignore[call-arg]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_basin", tool_schema=SAMPLE_TOOL_SCHEMA)
        assert recovery is not None
        assert "basin_name" in recovery["rejected_fields"]
        assert "formation" in recovery["rejected_fields"]

    def test_internal_fields_excluded(self):
        """session_id, actor_id, trace_id are excluded from available fields."""
        with pytest.raises(ValidationError) as exc_info:
            SampleToolInput()  # type: ignore[call-arg]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_basin", tool_schema=SAMPLE_TOOL_SCHEMA)
        assert recovery is not None
        assert "session_id" not in recovery["available"]
        assert "actor_id" not in recovery["available"]
        assert "trace_id" not in recovery["available"]

    def test_keyerror_extracts_field(self):
        """KeyError → rejected_fields with the key."""
        exc = KeyError("reservoir_pressure")
        recovery = _extract_recovery_from_error(exc, "geox_well")
        assert recovery is not None
        assert "reservoir_pressure" in recovery["rejected_fields"]
        assert recovery["retryable"] is True

    def test_typeerror_extracts_field(self):
        """TypeError with 'unexpected keyword argument' → rejected_fields."""
        exc = TypeError("unexpected keyword argument 'bad_field'")
        recovery = _extract_recovery_from_error(exc, "geox_well")
        assert recovery is not None
        assert "bad_field" in recovery["rejected_fields"]

    def test_no_recovery_from_generic_exception(self):
        """Generic exception with no field info → None."""
        exc = RuntimeError("something broke")
        recovery = _extract_recovery_from_error(exc, "geox_well")
        assert recovery is None

    def test_discovery_tool_derived(self):
        """discovery_tool is derived from tool_name prefix."""
        exc = KeyError("field")
        recovery = _extract_recovery_from_error(exc, "geox_well_log")
        assert recovery is not None
        assert recovery["discovery_tool"] == "geox_describe"

    def test_fields_bounded_at_max(self):
        """Available fields capped at MAX_RECOVERY_FIELDS (20)."""
        recovery = _extract_recovery_from_error(KeyError("test"), "geox_test", tool_schema=SAMPLE_TOOL_SCHEMA)
        assert recovery is not None
        assert len(recovery["available"]) <= 20

    def test_schema_introspection_populates_available(self):
        """Layer 1.5: tool_schema properties populate available fields."""
        exc = KeyError("basn_name")  # typo
        recovery = _extract_recovery_from_error(exc, "geox_basin", tool_schema=SAMPLE_TOOL_SCHEMA)
        assert recovery is not None
        assert "basin_name" in recovery["available"]
        assert "formation" in recovery["available"]
        assert "mode" in recovery["available"]

    def test_fuzzy_match_suggests_corrections(self):
        """Layer 1.5: fuzzy matching suggests close field names for typos."""
        exc = KeyError("basn_name")  # typo of basin_name
        recovery = _extract_recovery_from_error(exc, "geox_basin", tool_schema=SAMPLE_TOOL_SCHEMA)
        assert recovery is not None
        assert recovery["closest_match"] is not None
        # closest_match is a dict: {rejected_field: [suggestions]}
        assert "basn_name" in recovery["closest_match"]
        assert "basin_name" in recovery["closest_match"]["basn_name"]


class TestGovernedErrorEnvelopeRecovery:
    """build_governed_error_envelope passes recovery through."""

    def test_envelope_without_recovery(self):
        """Existing behavior — no recovery field when not provided."""
        envelope = build_governed_error_envelope(
            tool_name="geox_basin",
            error_class="SCHEMA_REJECTION",
            detail="test error",
        )
        data = envelope["error"]["data"]
        assert "recovery" not in data

    def test_envelope_with_recovery(self):
        """Recovery field present when provided."""
        recovery = {
            "available": ["basin_name", "formation"],
            "closest_match": None,
            "discovery_tool": "geox_describe",
            "retryable": True,
        }
        envelope = build_governed_error_envelope(
            tool_name="geox_basin",
            error_class="SCHEMA_REJECTION",
            detail="test error",
            recovery=recovery,
        )
        data = envelope["error"]["data"]
        assert "recovery" in data
        assert data["recovery"]["available"] == ["basin_name", "formation"]
        assert data["recovery"]["retryable"] is True

    def test_envelope_json_serializable(self):
        """Envelope with recovery is JSON-serializable."""
        recovery = {"available": ["a", "b"], "retryable": True}
        envelope = build_governed_error_envelope(
            tool_name="geox_basin",
            error_class="SCHEMA_REJECTION",
            detail="test",
            recovery=recovery,
        )
        serialized = json.dumps(envelope)
        assert "recovery" in serialized

    def test_governance_block_no_recovery(self):
        """GOVERNANCE_BLOCK errors don't need recovery hints."""
        envelope = build_governed_error_envelope(
            tool_name="geox_basin",
            error_class="GOVERNANCE_BLOCK",
            detail="not allowed",
        )
        assert "recovery" not in envelope["error"]["data"]
