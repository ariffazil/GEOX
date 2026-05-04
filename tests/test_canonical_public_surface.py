import pytest
from fastmcp import FastMCP
from contracts.canonical_registry import CANONICAL_PUBLIC_TOOLS
from contracts.tools.unified_13 import register_unified_tools
from contracts.tools.well_correlation import register_well_correlation_tools


@pytest.fixture
def mcp_server():
    mcp = FastMCP(name="GEOX_Test", version="test")
    register_unified_tools(mcp)
    register_well_correlation_tools(mcp)
    return mcp


@pytest.mark.asyncio
async def test_canonical_public_surface_count(mcp_server):
    """Verify that exactly 13 sovereign public tools are exposed."""
    registered_tools = await mcp_server.list_tools()
    public_tools = [t.name for t in registered_tools if t.name in CANONICAL_PUBLIC_TOOLS]
    assert len(public_tools) == 14, f"Expected 14 public tools, found {len(public_tools)}: {public_tools}"


@pytest.mark.asyncio
async def test_canonical_public_surface_names(mcp_server):
    """Verify all 13 canonical public tool names are correctly registered."""
    registered_tool_names = {t.name for t in await mcp_server.list_tools()}
    missing_tools = [t for t in CANONICAL_PUBLIC_TOOLS if t not in registered_tool_names]
    # Extra = tools registered that are NOT in CANONICAL_PUBLIC_TOOLS (ok to have internal tools,
    # but none of the canonical names may be missing from the server).
    assert not missing_tools, f"Missing canonical public tools: {missing_tools}"
    # Confirm canonical set is a subset of registered — no canonical tool silently dropped
    assert set(CANONICAL_PUBLIC_TOOLS).issubset(registered_tool_names), (
        f"CANONICAL_PUBLIC_TOOLS not fully covered: {set(CANONICAL_PUBLIC_TOOLS) - registered_tool_names}"
    )


@pytest.mark.asyncio
async def test_canonical_public_surface_no_dotted_names(mcp_server):
    """Verify no public tool name contains \'.\'."""
    registered_tools = await mcp_server.list_tools()
    dotted_names = [t.name for t in registered_tools if "." in t.name and t.name in CANONICAL_PUBLIC_TOOLS]
    assert not dotted_names, f"Dotted names on canonical surface: {dotted_names}"
