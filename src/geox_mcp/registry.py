from __future__ import annotations

from typing import Any

from geox_mcp.surface_manifest import (
    compat_tools,
    internal_tool_names,
    manifest_entries_for_registry,
    manifest_tool_map,
    public_tool_names,
    runtime_tool_names,
)

# Canonical public surface: only tools intentionally exposed to MCP clients.
SURFACE_TOOLS: list[str] = public_tool_names()

# Internal runtime tools: executable inside GEOX but hidden from tools/list.
INTERNAL_TOOLS: list[str] = internal_tool_names()

# Backward-compat aliases accepted during transition, never exposed publicly.
CANONICAL_COMPAT_TOOLS: list[str] = list(compat_tools())

# Public = discoverable MCP surface.
CANONICAL_PUBLIC_TOOLS: list[str] = list(SURFACE_TOOLS)

# Runtime = public + explicitly internal tools.
CANONICAL_RUNTIME_TOOLS: list[str] = runtime_tool_names()

# Legacy alias routing table intentionally empty until explicit migrations exist.
LEGACY_ALIAS_MAP: dict[str, str] = {}

# Canonical registry rows consumed by governance, status, and discovery helpers.
GEOX_TOOL_MANIFEST: list[dict[str, Any]] = manifest_entries_for_registry()


def get_tool_domain(tool_name: str) -> str:
    entry = manifest_tool_map().get(tool_name)
    return entry.domain if entry else "unknown"


def surface_tool_count() -> int:
    return len(SURFACE_TOOLS)


def internal_tool_count() -> int:
    return len(INTERNAL_TOOLS)


def is_surface_tool(tool_name: str) -> bool:
    return tool_name in set(SURFACE_TOOLS)


def is_internal_tool(tool_name: str) -> bool:
    return tool_name in set(INTERNAL_TOOLS)
