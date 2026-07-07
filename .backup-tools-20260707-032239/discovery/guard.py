from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("geox.discovery.guard")

_REGISTRY: dict[str, dict[str, Any]] = {}
_TTL: int = 300  # seconds — covers a typical multi-step retrieval session


def register_route_completion(request_id: str, route_output: dict[str, Any]) -> None:
    _purge()
    _REGISTRY[request_id] = {"output": route_output, "ts": time.monotonic()}


def check_route_completion(request_id: str) -> tuple[bool, dict[str, Any] | None]:
    _purge()
    entry = _REGISTRY.get(request_id)
    if not entry:
        return False, None
    return True, entry["output"]


def require_router(request_id: str, calling_tool: str) -> dict[str, Any] | None:
    """
    Call at the start of any discovery retrieval tool.
    Returns an error dict if arifos_route_query has not been called for this
    request_id; returns None if the tool is cleared to proceed.
    """
    completed, route = check_route_completion(request_id)
    if not completed:
        from geox_mcp.tools.discovery.audit_logger import log_guard_block

        log_guard_block(request_id, calling_tool)
        logger.warning("GUARD_BLOCK: %s called before router. request_id=%s", calling_tool, request_id)
        return {
            "ok": False,
            "error_code": "ROUTER_GUARD_BLOCKED",
            "calling_tool": calling_tool,
            "request_id": request_id,
            "message": (
                f"'{calling_tool}' requires a prior arifos_route_query call for "
                f"request_id='{request_id}'. Call the router first, then use "
                "the returned allowed_tools list."
            ),
            "guard": "DISCOVERY_ROUTER_GUARD",
            "floor": "F4_CLARITY",
            "safe_next_action": "Call arifos_route_query with this request_id, then retry.",
        }
    return None


def _purge() -> None:
    now = time.monotonic()
    expired = [k for k, v in _REGISTRY.items() if now - v["ts"] > _TTL]
    for k in expired:
        del _REGISTRY[k]
