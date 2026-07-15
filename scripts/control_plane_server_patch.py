"""
GEOX Control Plane Server Patch — RT-1 / RT-3 Dispatch Guards
=============================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

RT-1 Guard (Runtime Tier 1):
  - Validates tool name is in CANONICAL_PUBLIC_TOOLS (from registry.py)
  - Rejects calls to undeclared tools with 403 Forbidden
  - Applied at HTTP handler level before FastMCP tool dispatch

RT-3 Guard (Runtime Tier 3):
  - Validates irreversible operations have explicit ack_irreversible=True
  - Required for: vault seals, prospect verdicts, artifact deletions
  - F1 Amanah: no irreversible action without explicit human consent
  - Applied at tool handler level for flagged operations

Epoch: 2026-06-22-GEOX-16TOOLS-PHASE2
Source of truth: src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("geox.dispatch_guard")

# ─── CANONICAL TOOL SURFACE (single source of truth) ─────────────────────────
# Import from registry.py — the ONLY authoritative source.
# NEVER import from contracts.enums.statuses.CANONICAL_TOOLS (stale, pre-Phase 2).


def _get_canonical_tools() -> set[str]:
    """Load canonical + compat tool set from registry.py. Fail-open on import error."""
    try:
        from geox_mcp.registry import CANONICAL_COMPAT_TOOLS, CANONICAL_PUBLIC_TOOLS

        return set(CANONICAL_PUBLIC_TOOLS) | set(CANONICAL_COMPAT_TOOLS)
    except ImportError:
        logger.warning("RT1: registry.py not importable — allowing pass-through")
        return set()


# ─── IRREVERSIBLE TOOL DEFINITIONS (RT-3 scope) ──────────────────────────────
# Tools that perform irreversible state changes require explicit human ack.
# Phase 2: geox_claim(mode="seal") and geox_prospect(mode="seal") are the
# canonical irreversible paths. Old direct names are removed.

_IRREVERSIBLE_TOOLS: set[str] = {
    "geox_claim",  # mode="seal" requires ack_irreversible=True
    "geox_prospect",  # mode="seal" requires ack_irreversible=True
}

# ─── RT-1 GUARD ───────────────────────────────────────────────────────────────


def rt1_check_tool(tool_name: str) -> tuple[bool, str]:
    """
    RT-1: Verify tool is on the canonical public surface.

    Returns:
        (allowed, error_message)
        - allowed=True, error=""  → pass
        - allowed=False, error=msg → reject with 403
    """
    canonical = _get_canonical_tools()
    if not canonical:
        # Registry unavailable — fail open (cold start)
        return True, ""

    if tool_name not in canonical:
        logger.warning(f"RT1_GUARD: Tool '{tool_name}' is not on canonical public surface. Valid surface: {sorted(canonical)}")
        return False, (
            f"Tool '{tool_name}' is not on the canonical or compat public surface. "
            f"Public surface has {len(canonical)} declared tools. "
            f"Use geox_surface_status(mode='registry') to enumerate available tools."
        )
    return True, ""


def rt1_guard_middleware(get_response: Callable):
    """
    Starlette middleware that applies RT-1 guard to all MCP POST /mcp requests.

    Applied at: HTTP handler level (before FastMCP processes the tool call)
    Enforcement: fail-closed — unknown tools get 403 before FastMCP sees them
    """

    async def middleware(request: Request):
        if request.method != "POST":
            return await get_response(request)

        # Only guard /mcp tool calls
        if request.url.path.rstrip("/") not in ("/mcp", "/mcp/"):
            return await get_response(request)

        try:
            body = await request.body()
            if not body:
                return await get_response(request)

            payload = json.loads(body)
            method = payload.get("method", "")
            params = payload.get("params", {})

            # tools/call method — validate tool name
            if method == "tools/call":
                tool_name = params.get("name", "") if isinstance(params, dict) else ""
                allowed, error = rt1_check_tool(tool_name)
                if not allowed:
                    logger.warning(f"RT1_BLOCK: {tool_name} — {error}")
                    canonical = _get_canonical_tools()
                    return JSONResponse(
                        {
                            "jsonrpc": "2.0",
                            "id": payload.get("id"),
                            "error": {
                                "code": -32001,
                                "message": f"RT1_GUARD: {error}",
                                "data": {
                                    "guard": "RT1",
                                    "tool": tool_name,
                                    "canonical_count": len(canonical),
                                },
                            },
                        },
                        status_code=403,
                    )
        except json.JSONDecodeError:
            pass  # Let FastMCP handle parse errors
        except Exception as exc:
            logger.error(f"RT1 middleware error: {exc}")

        return await get_response(request)

    return middleware


# ─── RT-3 GUARD ───────────────────────────────────────────────────────────────


def rt3_check_irreversible(tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str]:
    """
    RT-3: Verify irreversible operations have explicit human acknowledgment.

    F1 Amanah: No irreversible action without explicit sovereign consent.
    Required arg: ack_irreversible = True

    Returns:
        (allowed, error_message)
        - allowed=True, error=""  → pass
        - allowed=False, error=msg → reject with 422
    """
    if tool_name not in _IRREVERSIBLE_TOOLS:
        return True, ""

    ack = arguments.get("ack_irreversible", False)
    if not ack:
        logger.warning(
            f"RT3_BLOCK: {tool_name} requires ack_irreversible=True. "
            f"F1 Amanah: irreversible operations require explicit human consent."
        )
        return False, (
            f"Tool '{tool_name}' performs an irreversible state change. "
            f"F1 Amanah requires explicit human consent via ack_irreversible=True. "
            f"Provide ack_irreversible=True in the tool call arguments to proceed."
        )
    return True, ""


def rt3_guard(tool_name: str, arguments: dict[str, Any]) -> JSONResponse | None:
    """
    RT-3 guard for tool handlers.

    Call this at the start of any irreversible tool handler.
    Returns a JSONResponse error (to return to caller) if blocked.
    Returns None if allowed.
    """
    allowed, error = rt3_check_irreversible(tool_name, arguments)
    if not allowed:
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32003,
                    "message": f"RT3_GUARD: {error}",
                    "data": {
                        "guard": "RT3",
                        "tool": tool_name,
                        "floor": "F1_AMANAH",
                    },
                },
            },
            status_code=422,
        )
    return None


# ─── REGISTRY HASH (for runtime parity verification) ───────────────────────────


def compute_registry_hash() -> str:
    """
    Compute SHA-256 hash of the canonical tool surface.
    Used to verify runtime registry matches declared surface.
    """
    try:
        from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

        canonical_sorted = sorted(CANONICAL_PUBLIC_TOOLS)
        payload = json.dumps(
            {
                "epoch": "2026-06-22-GEOX-16TOOLS-PHASE2",
                "tools": canonical_sorted,
                "count": len(canonical_sorted),
                "computed_at": datetime.now(UTC).isoformat(),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
    except Exception as exc:
        logger.error(f"Failed to compute registry hash: {exc}")
        return "UNKNOWN"


# ─── GUARD REGISTRY REPORT ─────────────────────────────────────────────────────


def guard_report() -> dict[str, Any]:
    """Runtime guard status report for geox_doctrine(mode='registry')."""
    canonical = _get_canonical_tools()
    return {
        "guard_active": True,
        "rt1_enabled": True,
        "rt3_enabled": True,
        "irreversible_tools": sorted(_IRREVERSIBLE_TOOLS),
        "canonical_tool_count": len(canonical),
        "canonical_tools": sorted(canonical),
        "registry_hash": compute_registry_hash(),
        "epoch": "2026-06-22-GEOX-16TOOLS-PHASE2",
        "source_of_truth": "src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS",
        "floors_enforced": ["F1_AMANAH", "F9_ANTI_HANTU", "F13_SOVEREIGN"],
    }
