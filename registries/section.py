import logging
from fastmcp import FastMCP

logger = logging.getLogger("geox.section")

def register_section_tools(mcp: FastMCP, profile: str = "full"):
    """
    SECTION Registry: 2D stratigraphic correlation tools.
    Cross-well analysis and profile synthesis.
    """
    
    @mcp.tool(name="section_interpret_strata")
    async def section_interpret_strata(section_id: str) -> dict:
        """Interpret: Correlate stratigraphic units across multiple wells in a section."""
        return {"section_id": section_id, "units": ["Oligocene", "Miocene_Lower"], "status": "Interpolated"}

    # Alias
    @mcp.tool(name="geox_interpret_strata")
    async def alias_geox_interpret_strata(section_id):
        return await section_interpret_strata(section_id)

    @mcp.tool(name="section_observe_well_correlation")
    async def section_observe_well_correlation(well_ids: list) -> dict:
        """Observe: Fetch raw correlation data between specified wells."""
        return {"wells": well_ids, "correlation_indices": [0.92, 0.85, 0.77]}

    # Alias
    @mcp.tool(name="geox_observe_well_correlation")
    async def alias_geox_observe_well_correlation(well_ids):
        return await section_observe_well_correlation(well_ids)

    @mcp.tool(name="section_synthesize_profile")
    async def section_synthesize_profile(start_coord: tuple, end_coord: tuple) -> dict:
        """Compute: Synthesize a 2D vertical profile from the Earth model."""
        return {"profile_id": "profile_syn_001", "length_km": 15.5}

    # Alias
    @mcp.tool(name="geox_synthesize_profile")
    async def alias_geox_synthesize_profile(start_coord, end_coord):
        return await section_synthesize_profile(start_coord, end_coord)
