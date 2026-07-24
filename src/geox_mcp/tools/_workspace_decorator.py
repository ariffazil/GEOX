"""
GEOX Workspace Decorator — H2 Auto-Injection
══════════════════════════════════════════════
Decorator that auto-injects workspace context into tool parameters.
Wraps any async tool function so that empty basin/play/well params
are filled from the persistent workspace.

Usage:
    from geox_mcp.tools._workspace_decorator import with_workspace

    @with_workspace
    async def geox_basin(basin_name: str = "", ...):
        # basin_name will be auto-filled from workspace if empty

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import functools
import logging
from typing import Any
from collections.abc import Callable

from geox_mcp.state.workspace import get_workspace

logger = logging.getLogger("geox.decorators.workspace")

# Default session ID used when no session context is available
_DEFAULT_SESSION = "default"

# Mapping of tool parameter names to workspace fields
_PARAM_TO_WORKSPACE: dict[str, str] = {
    "basin_name": "basin",
    "basin": "basin",
    "well_id": "well_id",
    "well_ref": "well_id",
    "prospect_ref": "prospect_ref",
    "field": "field",
    "play": "play",
}


def _inject_workspace_params(
    kwargs: dict[str, Any],
    session_id: str = _DEFAULT_SESSION,
) -> dict[str, Any]:
    """Inject workspace values into empty/missing parameters.

    Only fills params that are explicitly empty (None, "", or not present).
    Explicitly passed values ALWAYS win over workspace defaults.
    """
    ws = get_workspace(session_id)
    ws_dict = ws.model_dump()

    injected = {}
    for param_name, ws_field in _PARAM_TO_WORKSPACE.items():
        ws_value = ws_dict.get(ws_field)
        if ws_value and param_name in kwargs:
            current = kwargs[param_name]
            if current is None or current == "":
                kwargs[param_name] = ws_value
                injected[param_name] = ws_value

    if injected:
        logger.debug(
            "Workspace auto-injected: %s (session=%s, basin=%s)",
            injected,
            session_id,
            ws.basin,
        )

    return kwargs


def with_workspace(
    func: Callable | None = None,
    *,
    session_id: str = _DEFAULT_SESSION,
    extract_session: bool = False,
):
    """Decorator: auto-inject workspace context into tool parameters.

    Can be used as @with_workspace or @with_workspace(session_id="...")

    Args:
        func: The async function to wrap (when used as bare @with_workspace)
        session_id: Fixed session ID. Use 'default' for single-user.
        extract_session: If True, try to extract session_id from kwargs.
    """

    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            sid = session_id
            if extract_session:
                sid = kwargs.pop("_session_id", session_id)

            # Auto-inject workspace params into kwargs
            kwargs = _inject_workspace_params(kwargs, sid)

            # Record workspace context from params that ARE explicitly set
            ws = get_workspace(sid)
            if kwargs.get("basin_name") and kwargs["basin_name"] != ws.basin:
                ws.basin = kwargs["basin_name"]
            if kwargs.get("well_id") and kwargs["well_id"] != ws.well_id:
                ws.well_id = kwargs["well_id"]
            if kwargs.get("play") and kwargs["play"] != ws.play:
                ws.play = kwargs["play"]

            result = await fn(*args, **kwargs)

            # Record the tool call
            tool_name = getattr(fn, "__name__", "unknown")
            ws.record_tool_call(
                tool_name=tool_name,
                params={k: v for k, v in kwargs.items() if k in _PARAM_TO_WORKSPACE},
                result_summary=str(result)[:200],
            )

            return result

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
