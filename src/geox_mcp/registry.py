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

# ── Ghost tools (ARCHIVED 2026-07-13) ─────────────────────────────────────
# Tools that exist in the manifest but have been deregistered from the live
# MCP surface. Excluded from SURFACE_TOOLS and INTERNAL_TOOLS so registry
# counts match tools/list. Sovereign directive: GEOX-RED-TEAM-2026-07-07.
# Reactivation requires F13 SOVEREIGN ack.
GHOST_TOOLS: set[str] = {
    # Public ghost — RESURRECTED 2026-07-16 (removed from ghost set)
    # Internal ghosts
    "geox_3d_model",
    "geox_3d_model_build",
    "geox_atlas",
    "geox_bid_round_screener",
    "geox_biostrat_nn_age",
    "geox_biostrat_ruling_check",
    "geox_cognitive_rank_hypotheses",
    "geox_forbidden_claims_scan",
    "geox_geological_cognition_run",
    "geox_macrostrat_calibrate",
    "geox_map_export_package",
    "geox_panel_d_render",
    "geox_panel_d_render_mcp",
    "geox_physical_reality_interpret",
    "geox_render_audit",
    "geox_rsi_interpret",
    "geox_segy_audit",
    "geox_segy_trace_audit",
    "geox_seismic_cognition",
    "geox_well_desurvey",
}
GHOST_COUNT = len(GHOST_TOOLS)

# Canonical public surface: only tools intentionally exposed to MCP clients,
# excluding archived ghosts.
SURFACE_TOOLS: list[str] = [t for t in public_tool_names() if t not in GHOST_TOOLS]

# Internal runtime tools: executable inside GEOX but hidden from tools/list,
# excluding archived ghosts.
INTERNAL_TOOLS: list[str] = [t for t in internal_tool_names() if t not in GHOST_TOOLS]

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
