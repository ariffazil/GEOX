import pytest
from fastmcp import FastMCP
from contracts.tools.unified_13 import register_unified_tools
from contracts.tools.canonical._helpers import CLAIM_STATES

@pytest.fixture
def mcp_server():
    mcp = FastMCP(name="GEOX_Test", version="test")
    register_unified_tools(mcp)
    return mcp

@pytest.mark.xfail(
    reason="Claim laundering guard at Pydantic input layer not yet implemented — Sprint 2 deliverable.",
    strict=False,
)
@pytest.mark.asyncio
async def test_claim_laundering_guard_prospect_evaluate_blocks_hypothesis(mcp_server):
    """Tool 09 must block evidence_refs with HYPOTHESIS claim_state.

    Implementation note: the guard requires looking up each evidence_ref in
    _artifact_store and checking its claim_state at call time. Sprint 2 deliverable.
    """
    import json
    from contracts.tools.canonical._helpers import _artifact_store as _ARTIFACT_STORE
    _ARTIFACT_STORE["hypo_ref_001"] = {
        "ref": "hypo_ref_001", "claim_state": "HYPOTHESIS",
        "file_path": "/dev/null", "format": "las",
    }
    response = await mcp_server.call_tool(
        "geox_prospect_evaluate",
        arguments={"prospect_ref": "hypo_ref_001", "mode": "volumetrics"},
    )
    result = json.loads(response.content[0].text)
    assert "CLAIM_LAUNDERING" in str(result.get("error_code", "")), (
        f"Expected CLAIM_LAUNDERING_BLOCKED for HYPOTHESIS input, got: {result}"
    )


@pytest.mark.xfail(
    reason="Claim laundering guard not yet implemented at input layer — Sprint 2 deliverable.",
    strict=False,
)
@pytest.mark.asyncio
async def test_claim_laundering_guard_prospect_judge_verdict_blocks_hypothesis(mcp_server):
    """Tool 10 must block when prospect_ref resolves to HYPOTHESIS claim_state."""
    import json
    from contracts.tools.canonical._helpers import _artifact_store as _ARTIFACT_STORE
    _ARTIFACT_STORE["hypo_ref_002"] = {
        "ref": "hypo_ref_002", "claim_state": "HYPOTHESIS",
        "file_path": "/dev/null", "format": "las",
    }
    response = await mcp_server.call_tool(
        "geox_prospect_judge_verdict",
        arguments={"prospect_ref": "hypo_ref_002", "ac_risk_score": 0.3, "ack_irreversible": True},
    )
    result = json.loads(response.content[0].text)
    assert "CLAIM_LAUNDERING" in str(result.get("error_code", "")), (
        f"Expected CLAIM_LAUNDERING_BLOCKED for HYPOTHESIS input, got: {result}"
    )


@pytest.mark.xfail(
    reason="Claim laundering guard not yet implemented at input layer — Sprint 2 deliverable.",
    strict=False,
)
@pytest.mark.asyncio
async def test_claim_laundering_guard_evidence_summarize_cross_blocks_hypothesis(mcp_server):
    """Tool 11 must block evidence_refs containing HYPOTHESIS claim_state."""
    import json
    from contracts.tools.canonical._helpers import _artifact_store as _ARTIFACT_STORE
    _ARTIFACT_STORE["hypo_ref_003"] = {
        "ref": "hypo_ref_003", "claim_state": "HYPOTHESIS",
        "file_path": "/dev/null", "format": "las",
    }
    response = await mcp_server.call_tool(
        "geox_evidence_summarize_cross",
        arguments={"evidence_refs": ["hypo_ref_003"], "export_format": "json"},
    )
    result = json.loads(response.content[0].text)
    assert "CLAIM_LAUNDERING" in str(result.get("error_code", "")), (
        f"Expected CLAIM_LAUNDERING_BLOCKED for HYPOTHESIS input, got: {result}"
    )
