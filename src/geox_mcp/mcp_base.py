"""
mcp_base.py — Shared MCP transport coercion utilities.

F1 AMANAH: MCP transport serializes nested dicts/lists as JSON strings.
This module provides shared coercion so every tool wrapper handles it
transparently. Single source of truth for MCP transport quirks.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, field_validator

logger = logging.getLogger("geox.mcp_base")


def coerce_json_string(value: Any, field_name: str = "unknown") -> Any:
    """Coerce a JSON string to its native Python type.

    MCP-over-HTTP transport serializes nested dicts/lists as JSON strings.
    This function parses them back. Returns original value if already native.

    Args:
        value: The value to coerce. May be str, dict, list, or None.
        field_name: Field name for error messages.

    Returns:
        Parsed value (dict/list) or original value if not a string.

    Raises:
        ValueError: If string is not valid JSON.
    """
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("MCP coercion failed for %s: %s", field_name, e)
            raise ValueError(f"Field '{field_name}' is a string but not valid JSON: {value[:200]}") from e
    # Return as-is for primitive types (int, float, bool)
    return value


class MCPBaseModel(BaseModel):
    """Base model with automatic JSON-string coercion for nested fields.

    Any field typed as dict | list | Any will automatically parse
    JSON strings from MCP transport. Use this as the base for all
    GEOX MCP tool request models.

    Example:
        class GeomechanicsRequest(MCPBaseModel):
            state: dict | None = None
            # state='{"vp": 3500}' will be auto-parsed to {"vp": 3500}
    """

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_json_strings(cls, v: Any, info) -> Any:
        """Auto-coerce JSON strings for dict/list/Any typed fields."""
        if v is None:
            return v
        if isinstance(v, str):
            # Only coerce if the field type accepts dict or list
            field_info = cls.model_fields.get(info.field_name)
            if field_info is None:
                return v
            ann = field_info.annotation
            # Check if annotation accepts dict or list
            _type_str = str(ann) if ann else ""
            if "dict" in _type_str or "list" in _type_str or "Any" in _type_str:
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, (dict, list)):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    pass  # Not JSON, return as-is
        return v


def mcp_coerce_dict(value: Any, field_name: str = "state") -> dict | None:
    """Convenience: coerce to dict or None. For use in non-Pydantic wrappers."""
    if value is None:
        return None
    result = coerce_json_string(value, field_name)
    if not isinstance(result, dict):
        raise TypeError(f"Field '{field_name}' must be dict, got {type(result).__name__}")
    return result


def mcp_coerce_list(value: Any, field_name: str = "list") -> list | None:
    """Convenience: coerce to list or None. For use in non-Pydantic wrappers."""
    if value is None:
        return None
    result = coerce_json_string(value, field_name)
    if not isinstance(result, list):
        raise TypeError(f"Field '{field_name}' must be list, got {type(result).__name__}")
    return result


__all__ = [
    "MCPBaseModel",
    "coerce_json_string",
    "mcp_coerce_dict",
    "mcp_coerce_list",
]
