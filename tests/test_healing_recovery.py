"""Tests for P0 self-healing recovery hints in GEOX error envelopes.

Verifies:
  - SCHEMA_REJECTION errors include recovery.available_fields when Pydantic errors present
  - _extract_recovery_from_error handles Pydantic ValidationError, TypeError, KeyError
  - Recovery fields are bounded at MAX_RECOVERY_FIELDS
  - Internal session_id/actor_id/trace_id fields are excluded from recovery
  - build_governed_error_envelope passes recovery through to output
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


# ── Import the functions under test ─────────────────────────────────────────
from geox_mcp.geox_middleware import (
    _extract_recovery_from_error,
    build_governed_error_envelope,
)


class TestExtractRecoveryFromError:
    """_extract_recovery_from_error extracts field names from exceptions."""

    def test_pydantic_validation_error(self):
        """Pydantic ValidationError with wrong field types → available_fields."""
        with pytest.raises(ValidationError) as exc_info:
            SampleToolInput(basin_name=123, formation=456, mode=789)  # type: ignore[arg-type]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_basin")
        assert recovery is not None
        # Should include the fields that failed validation
        assert "basin_name" in recovery["available_fields"] or "formation" in recovery["available_fields"]
        assert recovery["retryable"] is True

    def test_pydantic_missing_required_field(self):
        """Missing required field → field name in available_fields."""
        with pytest.raises(ValidationError) as exc_info:
            SampleToolInput()  # type: ignore[call-arg]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_basin")
        assert recovery is not None
        assert "basin_name" in recovery["available_fields"]
        assert "formation" in recovery["available_fields"]

    def test_internal_fields_excluded(self):
        """session_id, actor_id, trace_id are excluded from recovery hints."""
        with pytest.raises(ValidationError) as exc_info:
            SampleToolInput()  # type: ignore[call-arg]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_basin")
        assert recovery is not None
        assert "session_id" not in recovery["available_fields"]
        assert "actor_id" not in recovery["available_fields"]
        assert "trace_id" not in recovery["available_fields"]

    def test_keyerror_extracts_field(self):
        """KeyError → closest_match set to the key."""
        exc = KeyError("reservoir_pressure")
        recovery = _extract_recovery_from_error(exc, "geox_well")
        assert recovery is not None
        assert recovery["closest_match"] == "reservoir_pressure"
        assert recovery["retryable"] is True

    def test_typeerror_extracts_field(self):
        """TypeError with 'unexpected keyword argument' → closest_match."""
        exc = TypeError("unexpected keyword argument 'bad_field'")
        recovery = _extract_recovery_from_error(exc, "geox_well")
        assert recovery is not None
        assert recovery["closest_match"] == "bad_field"

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
        """Available fields capped at MAX_RECOVERY_FIELDS (10)."""

        class ManyFieldModel(BaseModel):
            f0: str = Field()
            f1: str = Field()
            f2: str = Field()
            f3: str = Field()
            f4: str = Field()
            f5: str = Field()
            f6: str = Field()
            f7: str = Field()
            f8: str = Field()
            f9: str = Field()
            f10: str = Field()
            f11: str = Field()

        with pytest.raises(ValidationError) as exc_info:
            ManyFieldModel()  # type: ignore[call-arg]
        recovery = _extract_recovery_from_error(exc_info.value, "geox_test")
        assert recovery is not None
        assert len(recovery["available_fields"]) <= 10


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
            "available_fields": ["basin_name", "formation"],
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
        assert data["recovery"]["available_fields"] == ["basin_name", "formation"]
        assert data["recovery"]["retryable"] is True

    def test_envelope_json_serializable(self):
        """Envelope with recovery is JSON-serializable."""
        recovery = {"available_fields": ["a", "b"], "retryable": True}
        envelope = build_governed_error_envelope(
            tool_name="geox_basin",
            error_class="SCHEMA_REJECTION",
            detail="test",
            recovery=recovery,
        )
        # Must not raise
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
