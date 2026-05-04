import json
import pytest
from fastmcp import FastMCP
from contracts.tools.unified_13 import register_unified_tools


@pytest.fixture
def mcp_server():
    mcp = FastMCP(name="GEOX_Test", version="test")
    register_unified_tools(mcp)
    return mcp


@pytest.mark.asyncio
async def test_fail_closed_auth_no_token_blocks_governed_tool(mcp_server):
    """RT-3: Tool 10 returns RT3_GUARD error when ack_irreversible=False."""
    response = await mcp_server.call_tool(
        "geox_prospect_judge_verdict",
        arguments={
            "prospect_ref": "test_prospect_ref",
            "ac_risk_score": 0.3,
            "ack_irreversible": False,
        }
    )
    result = json.loads(response.content[0].text)
    artifact = result.get("primary_artifact") or result
    assert artifact.get("error_code") == "RT3_GUARD_F1_AMANAH", (
        f"Expected RT3_GUARD_F1_AMANAH error when ack_irreversible=False, got: {result}"
    )
    assert result.get("execution_status") == "ERROR", f"Expected ERROR status, got: {result.get('execution_status')}"
    assert result.get("governance_status") == "HOLD", f"Expected HOLD governance status, got: {result.get('governance_status')}"


@pytest.mark.asyncio
async def test_fail_closed_auth_with_token_allows_governed_tool(mcp_server):
    """RT-3: Tool 10 issues a governance verdict when ack_irreversible=True."""
    response = await mcp_server.call_tool(
        "geox_prospect_judge_verdict",
        arguments={
            "prospect_ref": "test_prospect_ref",
            "ac_risk_score": 0.3,
            "ack_irreversible": True,
        }
    )
    result = json.loads(response.content[0].text)
    assert "RT3_GUARD" not in str(result.get("error_code", "")), (
        f"Unexpected RT3 guard with ack_irreversible=True: {result}"
    )
    assert result.get("execution_status") == "SUCCESS", f"Expected SUCCESS, got: {result.get('execution_status')}"
    assert result.get("governance_status") == "SEAL", f"Expected SEAL governance status, got: {result.get('governance_status')}"


# NOTE: Full OAuth 2.1 scope enforcement (geox:governance) happens at the HTTP layer.
