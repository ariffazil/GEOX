import logging
from fastmcp import FastMCP

logger = logging.getLogger("geox.prospect")

def register_prospect_tools(mcp: FastMCP, profile: str = "full"):
    """
    PROSPECT Registry: Play fairway discovery.
    'Should we drill here?'
    """
    
    @mcp.tool(name="prospect_evaluate")
    async def prospect_evaluate(area_id: str) -> dict:
        """Evaluate a prospect area for hydrocarbon potential."""
        return {"area_id": area_id, "score": 0.85, "status": "Placeholder"}

    @mcp.tool(name="geox_evaluate_prospect")
    async def alias_geox_evaluate_prospect(area_id):
        return await prospect_evaluate(area_id)

    @mcp.tool(name="prospect_build_structural")
    async def prospect_build_structural(area_id: str) -> dict:
        """Build structural candidates for a prospect."""
        return {"area_id": area_id, "candidates": ["Anticline_01", "Fault_Trap_02"]}

    @mcp.tool(name="geox_build_structural_candidates")
    async def alias_geox_build_structural_candidates(area_id):
        return await prospect_build_structural(area_id)

    @mcp.tool(name="prospect_feasibility_check")
    async def prospect_feasibility_check(area_id: str) -> dict:
        """Check technical and economic feasibility."""
        return {"area_id": area_id, "feasible": True}

    @mcp.tool(name="geox_feasibility_check")
    async def alias_geox_feasibility_check(area_id):
        return await prospect_feasibility_check(area_id)
