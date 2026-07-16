from __future__ import annotations

import pytest
from fastmcp import FastMCP

from geox_mcp.tools_wiring import register_tools_on


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["registry", "health"])
async def test_surface_status_echoes_federation_context(mode: str) -> None:
    mcp = FastMCP("geox-session-test")
    register_tools_on(mcp)
    component = next(
        value
        for key, value in mcp._local_provider._components.items()
        if key.startswith("tool:geox_surface_status@")
    )
    result = await component.fn(
        mode=mode,
        session_id="SEAL-session-echo",
        actor_id="arif",
        trace_id="trace-echo",
    )
    assert result["session_id"] == "SEAL-session-echo"
    assert result["actor_id"] == "arif"
    assert result["trace_id"] == "trace-echo"
