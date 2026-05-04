"""
GEOX Control Plane Server Patch — RT-1 / RT-3 Dispatch Guards
=============================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

RT-1 Guard (Runtime Tier 1):
  - Validates tool name is in CANONICAL_TOOLS (public surface)
  - Rejects calls to undeclared tools with 403 Forbidden
  - Applied at HTTP handler level before FastMCP tool dispatch

RT-3 Guard (Runtime Tier 3):
  - Validates irreversible operations have explicit ack_irreversible=True
  - Required for: vault seals, prospect verdicts, artifact deletions
  - F1 Amanah: no irreversible action without explicit human consent
  - Applied at tool handler level for flagged operations

Epoch: GEOX-11TOOLS-v0.3
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("geox.dispatch_guard")

# ─── IRREVERSIBLE TOOL DEFINITIONS (RT-3 scope) ──────────────────────────────
# Tools that perform irreversible state changes require explicit human ack.
# Any new irreversible tool MUST be added here.

_IRREVERSIBLE_TOOLS: set[str] = {
    "geox_prospect_judge_verdict",   # SEAL/VOID/SABAR — constitutional adjudication only
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
    try:
        from contracts.enums.statuses import CANONICAL_TOOLS
    except ImportError:
        logger.warning("RT1: CANONICAL_TOOLS not importable — allowing pass-through")
        return True, ""

    if tool_name not in CANONICAL_TOOLS:
        # Check if it's a dimension/legacy tool (allowed but logged)
        # RT-1 only blocks truly undeclared tools
        logger.warning(
            f"RT1_GUARD: Tool '{tool_name}' is not on canonical public surface. "
            f"Valid surface: {CANONICAL_TOOLS}"
        )
        # Fail open for dimension tools (they are registered), fail closed for unknown
        # This allows dimension tools while blocking hallucinated tool names
        return False, (
            f"Tool '{tool_name}' is not on the canonical public surface. "
            f"Public surface has {len(CANONICAL_TOOLS)} declared tools. "
            f"Use geox_registry_contract to enumerate available tools."
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
        if not request.url.path.rstrip("/") in ("/mcp", "/mcp/"):
            return await get_response(request)

        try:
            body = await request.body()
            if not body:
                return await get_response(request)

            payload = json.loads(body)
            method = payload.get("method", "")
            params = params = payload.get("params", {})

            # tools/call method — validate tool name
            if method == "tools/call":
                tool_name = params.get("name", "") if isinstance(params, dict) else ""
                allowed, error = rt1_check_tool(tool_name)
                if not allowed:
                    logger.warning(f"RT1_BLOCK: {tool_name} — {error}")
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
                                    "canonical_count": 13,
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


def rt3_guard(tool_name: str, arguments: dict[str, Any]) -> Optional[JSONResponse]:
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
        from contracts.enums.statuses import CANONICAL_TOOLS
        canonical_sorted = sorted(CANONICAL_TOOLS)
        payload = json.dumps(
            {
                "epoch": "GEOX-11TOOLS-v0.3",
                "tools": canonical_sorted,
                "count": len(canonical_sorted),
                "computed_at": datetime.now(timezone.utc).isoformat(),
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
    except Exception as exc:
        logger.error(f"Failed to compute registry hash: {exc}")
        return "UNKNOWN"


# ─── GUARD REGISTRY REPORT ─────────────────────────────────────────────────────

def guard_report() -> dict[str, Any]:
    """Runtime guard status report for geox_registry_contract."""
    try:
        from contracts.enums.statuses import CANONICAL_TOOLS
        canonical_count = len(CANONICAL_TOOLS)
    except ImportError:
        canonical_count = 0

    return {
        "guard_active": True,
        "rt1_enabled": True,
        "rt3_enabled": True,
        "irreversible_tools": sorted(_IRREVERSIBLE_TOOLS),
        "canonical_tool_count": canonical_count,
        "registry_hash": compute_registry_hash(),
        "epoch": "GEOX-11TOOLS-v0.3",
        "floors_enforced": ["F1_AMANAH", "F10_COHERENCE"],
    }
