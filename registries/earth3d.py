import logging
from fastmcp import FastMCP

logger = logging.getLogger("geox.earth3d")

def register_earth3d_tools(mcp: FastMCP, profile: str = "full"):
    """
    EARTH 3D Registry: Volumetric seismic tools.
    'What does the seismic show?'
    """
    
    @mcp.tool(name="earth3d_load_seismic")
    async def earth3d_load_seismic(line_id: str) -> dict:
        """Load a seismic 3D volume or line."""
        return {"line_id": line_id, "status": "Loaded", "vols": ["3D_Full_Stack"]}

    @mcp.tool(name="geox_load_seismic_line")
    async def alias_geox_load_seismic_line(line_id):
        return await earth3d_load_seismic(line_id)

    @mcp.tool(name="earth3d_extract_views")
    async def earth3d_extract_views(line_id: str, slice_type: str) -> dict:
        """Extract seismic views (inline, crossline, timeslice)."""
        return {"line_id": line_id, "view": slice_type, "url": f"geox://seismic/view/{line_id}/{slice_type}"}

    @mcp.tool(name="geox_extract_seismic_views")
    async def alias_geox_extract_seismic_views(line_id, slice_type):
        return await earth3d_extract_views(line_id, slice_type)

    @mcp.tool(name="earth3d_interpret_line")
    async def earth3d_interpret_line(line_id: str) -> dict:
        """Interpret single seismic line for horizons and faults."""
        return {"line_id": line_id, "horizons": ["H1", "H2"], "faults": ["F1"]}

    @mcp.tool(name="geox_interpret_single_line")
    async def alias_geox_interpret_single_line(line_id):
        return await earth3d_interpret_line(line_id)

    @mcp.tool(name="earth3d_create_overlay")
    async def earth3d_create_overlay(line_id: str, data_type: str) -> dict:
        """Create a data overlay on a seismic view."""
        return {"line_id": line_id, "overlay": data_type, "status": "Success"}

    @mcp.tool(name="geox_create_overlay")
    async def alias_geox_create_overlay(line_id, data_type):
        return await earth3d_create_overlay(line_id, data_type)
