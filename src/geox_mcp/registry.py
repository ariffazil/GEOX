from __future__ import annotations

import os
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
    "geox_panel_d_render",
    "geox_panel_d_render_mcp",
    "geox_physical_reality_interpret",
    "geox_render_audit",
    "geox_rsi_interpret",
    "geox_segy_audit",
    "geox_segy_trace_audit",
    "geox_visual_generate_hypotheses",  # GHOSTED 2026-07-29 — experimental DL, overlaps seismic_interpret
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


# ── P0-2 authority policy (2026-07-25 · FI-008) ─────────────────────────
# Per-tool minimum authority for tools/call admission. Computed from the
# manifest's governance.action_class plus a small override table for tools
# whose effective action depends on call-time arguments (e.g. geox_well_ingest
# with overwrite=True is a MUTATE despite the manifest declaring OBSERVE).
#
# Authority ranks (from session_enforcement.AUTHORITY_LEVELS):
#   OBSERVE_ONLY < OPERATOR < LIMITED_MUTATE < FULL < SOVEREIGN
#
# F1 AMANAH: when a caller presents an authority band, it MUST be at least
# the value returned by ``required_authority_for``. Lower → 403 rejection.

# Default required authority by tool action_class.
_ACTION_CLASS_AUTH: dict[str, str] = {
    "OBSERVE": "OBSERVE_ONLY",
    "MUTATE": "LIMITED_MUTATE",
    "EXECUTE": "LIMITED_MUTATE",
}

# Tools whose mutating-ness depends on call-time arguments (override the
# manifest's action_class). Two override shapes:
#
#   _MUTATING_ARG_OVERRIDES: truthy-arg triggers MUTATE
#     tool_name → tuple of arg_names; any-true → LIMITED_MUTATE
#
#   _MUTATING_VALUE_OVERRIDES: arg-equals-value triggers MUTATE
#     tool_name → dict of {arg_name: matching_value}; match → LIMITED_MUTATE
#
# Both lists feed ``required_authority_for`` and are evaluated before the
# manifest's action_class is consulted. The audit-reproducible cases live
# here: the SEAL modes of geox_claim / geox_prospect MUST require
# LIMITED_MUTATE even though the manifest declares action_class: OBSERVE.
_MUTATING_ARG_OVERRIDES: dict[str, tuple[str, ...]] = {
    # tool_name: tuple of arg_names; any-true → LIMITED_MUTATE
    "geox_well_ingest": ("overwrite",),
    "geox_evidence": ("forbidden_uses",),  # attaching forbidden uses is a mutation
}

_MUTATING_VALUE_OVERRIDES: dict[str, dict[str, Any]] = {
    # tool_name: {arg_name: matching_value}; match → LIMITED_MUTATE
    "geox_claim": {"mode": "seal"},  # mode=seal is the irreversible path
    "geox_prospect": {"verdict": "seal"},  # verdict=seal is the irreversible path
}

# Env flag: when false, session enforcement is bypassed for OBSERVE-only
# tools (backward-compat). When true (default for production), every call
# must present a verified session_id. Per F13: this default lives in env,
# not in code, so the sovereign can flip it without a redeploy.
_REQUIRE_SESSION_ENV = "GEOX_REQUIRE_SESSION_FOR_MUTATE"


def require_session_for_all() -> bool:
    """Return True iff every tools/call MUST carry a session_id.

    Default: True (every call requires session). Override via env
    ``GEOX_REQUIRE_SESSION_FOR_MUTATE=0`` for local dev / smoke tests.
    """
    val = os.getenv(_REQUIRE_SESSION_ENV, "1").strip().lower()
    return val not in ("0", "false", "off", "no")


def required_authority_for(tool_name: str, arguments: dict[str, Any] | None = None) -> str:
    """Return the minimum authority required to call ``tool_name``.

    Resolution order:
      1. Per-tool mutating-arg overrides (when supplied arguments include
         any of the listed arg names set truthy, the tool is treated as
         MUTATE for the duration of this call).
      2. Manifest ``governance.action_class`` for the tool.
      3. Default: ``OBSERVE_ONLY`` (safe-fail — never grant MUTATE by
         absence of declaration).

    Returns one of: ``OBSERVE_ONLY`` | ``LIMITED_MUTATE``. Callers SHOULD
    rank-compare against the session's authority band and reject with 403
    when the session is below the required level.
    """
    arguments = arguments or {}

    # 1. mutating-arg overrides (any-truthy or specific-value triggers MUTATE)
    arg_override = _MUTATING_ARG_OVERRIDES.get(tool_name)
    if arg_override and any(bool(arguments.get(arg)) for arg in arg_override):
        return "LIMITED_MUTATE"
    value_override = _MUTATING_VALUE_OVERRIDES.get(tool_name)
    if value_override:
        for arg_name, expected in value_override.items():
            if arguments.get(arg_name) == expected:
                return "LIMITED_MUTATE"

    # 2. manifest action_class
    entry = manifest_tool_map().get(tool_name)
    if entry is not None:
        action = str(entry.governance.get("action_class", "OBSERVE") or "OBSERVE").upper()
        return _ACTION_CLASS_AUTH.get(action, "OBSERVE_ONLY")

    # 3. safe-fail default
    return "OBSERVE_ONLY"


def is_mutating_call(tool_name: str, arguments: dict[str, Any] | None = None) -> bool:
    """Return True iff ``required_authority_for`` resolves to LIMITED_MUTATE."""
    return required_authority_for(tool_name, arguments) == "LIMITED_MUTATE"
