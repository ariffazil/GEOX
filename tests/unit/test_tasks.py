"""
H3 — SEP-1686 Background Task Tool Tests
═══════════════════════════════════════════════════════════════════════════════
Verify task=True registration, empty-input fail-closed behavior,
and server-level task support.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import pytest
import fastmcp
from fastmcp import FastMCP


# FastMCP 3.x removed the tasks= parameter and task_config support.
# Skip the entire module if running against FastMCP >= 3.0.
_FMC_VERSION = tuple(int(x) for x in fastmcp.__version__.split(".")[:2])
if _FMC_VERSION >= (3, 0):
    pytest.skip("FastMCP 3.x removed background task support (tasks=True, task_config)", allow_module_level=True)


@pytest.fixture
def mcp_server():
    """Bootstrap a minimal MCP server with task support."""
    mcp = FastMCP(name="GEOX_Test", version="test", tasks=True)
    # Register canonical tools
    from geox_mcp.tools.unified_13 import register_unified_tools
    register_unified_tools(mcp)
    # Register task tools
    from geox_mcp.tools.data import geox_task_ingest_las_batch
    from geox_mcp.tools.abduction import geox_task_metabolize_basin
    mcp.tool(name="geox_task_ingest_las_batch", task=True)(geox_task_ingest_las_batch)
    mcp.tool(name="geox_task_metabolize_basin", task=True)(geox_task_metabolize_basin)
    return mcp


@pytest.mark.asyncio
async def test_task_tools_registered(mcp_server):
    """Both task tools must appear in the tool registry."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "geox_task_ingest_las_batch" in names, "geox_task_ingest_las_batch not registered"
    assert "geox_task_metabolize_basin" in names, "geox_task_metabolize_basin not registered"


@pytest.mark.asyncio
async def test_task_ingest_empty_refs_fail_closed():
    """Empty artifact_refs must return ERROR/HOLD, not crash."""
    from geox_mcp.tools.data import geox_task_ingest_las_batch
    result = await geox_task_ingest_las_batch(artifact_refs=[])
    payload = result.get("payload", result)
    assert payload.get("execution_status") == "ERROR"
    assert payload.get("claim_state") == "NO_VALID_EVIDENCE"


@pytest.mark.asyncio
async def test_task_metabolize_empty_refs_fail_closed():
    """Empty well_refs must return ERROR/HOLD, not crash."""
    from geox_mcp.tools.abduction import geox_task_metabolize_basin
    result = await geox_task_metabolize_basin(well_refs=[], basin_context="test")
    assert result.get("execution_status") == "ERROR"
    assert result.get("claim_state") == "NO_VALID_EVIDENCE"


@pytest.mark.asyncio
async def test_task_metabolize_nonexistent_wells():
    """Non-existent wells should produce PARTIAL with per-well errors."""
    from geox_mcp.tools.abduction import geox_task_metabolize_basin
    result = await geox_task_metabolize_basin(
        well_refs=["NONEXISTENT_WELL_001"],
        basin_context="malay_basin",
    )
    assert result.get("execution_status") == "PARTIAL"
    assert result.get("derived", {}).get("error_count", 0) >= 1


@pytest.mark.asyncio
async def test_server_task_support_enabled(mcp_server):
    """FastMCP server must advertise task support."""
    # _support_tasks_by_default is the internal flag
    assert getattr(mcp_server, "_support_tasks_by_default", False), (
        "Server task support not enabled. Pass tasks=True to FastMCP()."
    )


@pytest.mark.asyncio
async def test_task_tool_task_config(mcp_server):
    """Task tools must have task_config.mode != 'forbidden'."""
    tool = await mcp_server.get_tool("geox_task_ingest_las_batch")
    assert tool is not None, "Tool not found"
    assert tool.task_config.supports_tasks(), (
        f"geox_task_ingest_las_batch task mode={tool.task_config.mode}, expected supports_tasks=True"
    )

    tool2 = await mcp_server.get_tool("geox_task_metabolize_basin")
    assert tool2 is not None, "Tool not found"
    assert tool2.task_config.supports_tasks(), (
        f"geox_task_metabolize_basin task mode={tool2.task_config.mode}, expected supports_tasks=True"
    )
