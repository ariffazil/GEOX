from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

GEOX_ENABLE_ARIFOS_ROUTE_QUERY = os.getenv("GEOX_ENABLE_ARIFOS_ROUTE_QUERY", "0").lower() in {"1", "true", "yes"}
GEOX_ROUTE_QUERY_GUARD_ENABLED = os.getenv("GEOX_ROUTE_QUERY_GUARD_ENABLED", "0").lower() in {"1", "true", "yes"}

_PROTECTED_TOOLS = {
    tool.strip()
    for tool in os.getenv(
        "GEOX_ROUTE_QUERY_PROTECTED_TOOLS",
        "enterprise_graph_search,geox_contrast_search,geox_disconfirm_evidence_scan",
    ).split(",")
    if tool.strip()
}


class _RouteDecisionStore:
    def __init__(self) -> None:
        self._decisions: dict[str, str] = {}

    def record(self, request_id: str, mode: str) -> None:
        self._decisions[request_id] = mode

    def has(self, request_id: str) -> bool:
        return request_id in self._decisions


_route_decision_store = _RouteDecisionStore()


def record_route_decision(request_id: str, mode: str) -> None:
    _route_decision_store.record(request_id, mode)


def guard_route_requirement(tool_name: str, arguments: dict[str, Any]) -> JSONResponse | None:
    if not GEOX_ROUTE_QUERY_GUARD_ENABLED or tool_name not in _PROTECTED_TOOLS:
        return None
    request_id = str(arguments.get("request_id", "")).strip()
    if request_id and _route_decision_store.has(request_id):
        return None
    return JSONResponse(
        {
            "status": "partial",
            "error": "ROUTER_REQUIRED",
            "message": f"Tool '{tool_name}' requires arifos_route_query before retrieval.",
            "safe_next_action": "Call arifos_route_query with the same request_id, then retry retrieval.",
        },
        status_code=428,
    )


class RouteQueryGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
        if request.method != "POST" or request.url.path != "/mcp":
            return await call_next(request)

        body = await request.body()
        if body:
            try:
                payload = json.loads(body)
                if payload.get("method") == "tools/call":
                    params = payload.get("params", {})
                    tool_name = params.get("name", "")
                    arguments = params.get("arguments", {})
                    guard_response = guard_route_requirement(tool_name, arguments)
                    if guard_response is not None:
                        return guard_response
            except json.JSONDecodeError:
                pass

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive  # type: ignore[attr-defined]
        return await call_next(request)
