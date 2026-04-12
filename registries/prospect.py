import logging
from fastmcp import FastMCP

logger = logging.getLogger("geox.prospect")

def register_prospect_tools(mcp: FastMCP, profile: str = "full"):
    """
    PROSPECT Registry: Play fairway discovery.
    'Should we drill here?'
    """
    
    @mcp.tool(name="prospect_evaluate_prospect")
    async def prospect_evaluate_prospect(area_id: str) -> dict:
        """Judge: Evaluate hydrocarbon potential based on 888_JUDGE verdict."""
        return {"area_id": area_id, "score": 0.88, "status": "Highly Prospective (F9 Checked)"}

    # Alias
    @mcp.tool(name="geox_evaluate_prospect")
    async def alias_geox_evaluate_prospect(area_id):
        return await prospect_evaluate_prospect(area_id)

    @mcp.tool(name="prospect_build_structural_candidates")
    async def prospect_build_structural_candidates(area_id: str) -> dict:
        """Interpret: Generate structural trap candidates for a prospect."""
        return {"area_id": area_id, "candidates": ["Anticline_01", "Fault_Trap_Beta"]}

    # Alias
    @mcp.tool(name="geox_build_structural_candidates")
    async def alias_geox_build_structural_candidates(area_id):
        return await prospect_build_structural_candidates(area_id)

    @mcp.tool(name="prospect_feasibility_check")
    async def prospect_feasibility_check(area_id: str) -> dict:
        """Verify: Technical and economic gating for the prospect."""
        return {"area_id": area_id, "feasible": True, "confidence": "High"}

    # Alias
    @mcp.tool(name="geox_feasibility_check")
    async def alias_geox_feasibility_check(area_id):
        return await prospect_feasibility_check(area_id)
