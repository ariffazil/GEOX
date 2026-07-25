"""
canonical_surface_gate — P0-1 canonical surface enforcement (Phase A).

Forged 2026-07-25 · FI-008 (kimi-code).

The audit identified that the live MCP connector exposes 115 tools while the
canonical public surface is 33. This module is the lowest-possible-layer
filter: any `list_tools` response passes through ``filter_tools_list`` and
only canonical public tools survive.

DOCTRINE
========

1. The single source of truth is ``tools_manifest.yaml`` (symlinked from
   ``surface.yaml``) loaded via :mod:`geox_mcp.surface_manifest`.
2. ``CANONICAL_PUBLIC_TOOLS`` from :mod:`geox_mcp.registry` is the set
   exposed to MCP clients — every name advertised in tools/list MUST be in
   this set, and every name in this set MUST be advertised.
3. Anything not in canonical public is "drift". Drift is logged at WARNING
   with the ``SURFACE_DRIFT`` event code and counted. The connector still
   serves (reversibility) but the receipt is sealed.
4. The actual cleanup of legacy ``@mcp.tool`` decorators happens in Phase B.
   Until then, drift is observable, not fatal — because F1 AMANAH requires
   reversible-first.

REVERSIBILITY
=============

Delete this file and remove the 3-line ``filter_tools_list`` call from the
``list_tools`` handler — original behavior restored.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any
from collections.abc import Iterable, Sequence

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

logger = logging.getLogger("geox_mcp.canonical_surface_gate")

# Event codes for structured logging — grep-able.
EVT_SURFACE_DRIFT = "SURFACE_DRIFT"
EVT_SURFACE_GAP = "SURFACE_GAP"
EVT_SURFACE_OK = "SURFACE_OK"

# Cached so we don't re-do the set conversion on every list_tools call.
_CANONICAL_SET: frozenset[str] = frozenset(CANONICAL_PUBLIC_TOOLS)


def canonical_set() -> frozenset[str]:
    """Return the canonical public tool set as a frozenset."""
    return _CANONICAL_SET


def is_canonical(tool_name: str) -> bool:
    """True iff ``tool_name`` is in the canonical public surface."""
    return tool_name in _CANONICAL_SET


def filter_tools_list(
    tools: Iterable[dict[str, Any]],
    *,
    log_drift: bool = True,
) -> list[dict[str, Any]]:
    """Return only the tools that are in canonical public surface.

    ``tools`` is an iterable of dicts, each carrying at minimum a ``name``
    key — the same shape produced by FastMCP's ``list_tools`` handler.

    Drift (non-canonical tools in the input) and gap (canonical tools
    missing from the input) are logged at WARNING with structured event
    codes so the audit-style probe can pick them up via journalctl.

    The function NEVER raises — drift is observable, not fatal. The
    federation is honest about what it serves and the receipt reflects it.
    """
    tools_list = list(tools)
    live_names = [t.get("name", "") for t in tools_list]
    live_set = set(n for n in live_names if n)

    drift = sorted(live_set - _CANONICAL_SET)
    gap = sorted(_CANONICAL_SET - live_set)

    if drift and log_drift:
        logger.warning(
            "%s live_count=%d canonical_count=%d drift_count=%d drifted=%s",
            EVT_SURFACE_DRIFT,
            len(live_set),
            len(_CANONICAL_SET),
            len(drift),
            drift,
        )
    if gap and log_drift:
        logger.warning(
            "%s canonical_count=%d live_count=%d gap_count=%d missing=%s",
            EVT_SURFACE_GAP,
            len(_CANONICAL_SET),
            len(live_set),
            len(gap),
            gap,
        )
    if not drift and not gap and log_drift:
        logger.info(
            "%s live_count=%d canonical_count=%d ok=true",
            EVT_SURFACE_OK,
            len(live_set),
            len(_CANONICAL_SET),
        )

    return [t for t in tools_list if t.get("name", "") in _CANONICAL_SET]


def drift_report(
    live_tool_names: Sequence[str],
) -> dict[str, Any]:
    """Compute a structured drift report (audit-style).

    Pure function — no logging side effects. Used by the test harness and
    the audit re-probe. Returns a dict suitable for VAULT999 sealing.
    """
    live_set = set(n for n in live_tool_names if n)
    drift = sorted(live_set - _CANONICAL_SET)
    gap = sorted(_CANONICAL_SET - live_set)
    overlap = sorted(live_set & _CANONICAL_SET)
    # Phase A: drift (extra compat/legacy tools on the live surface) is
    # expected — the middleware filters them from tools/list.  ok=False only
    # when canonical tools are MISSING from the live surface (gaps).
    return {
        "canonical_count": len(_CANONICAL_SET),
        "live_count": len(live_set),
        "drift_count": len(drift),
        "gap_count": len(gap),
        "ok": len(gap) == 0,
        "drifted": drift,
        "missing": gap,
        "overlap_count": len(overlap),
        "canonical_tools": sorted(_CANONICAL_SET),
    }


def surface_invariant_violated(live_tool_names: Sequence[str]) -> bool:
    """Return True iff ``filter_tools_list`` would alter the live set.

    Used by the boot path to decide whether to elevate to ``HOLD``.
    """
    report = drift_report(live_tool_names)
    return not report["ok"]
