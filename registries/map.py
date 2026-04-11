import logging
from fastmcp import FastMCP

logger = logging.getLogger("geox.map")

def register_map_tools(mcp: FastMCP, profile: str = "full"):
    """
    MAP Registry: Spatial fabric & context.
    'Where is this? What's around it?'
    """
    
    try:
        from services.geo_fabric.engine import fabric
        from services.evidence_store.store import store
    except ImportError:
        logger.error("Map services unavailable")
        return

    @mcp.tool(name="map_transform_coordinates")
    async def map_transform_coordinates(x: float, y: float, from_epsg: int, to_epsg: int) -> dict:
        """Project a point between coordinate systems."""
        try:
            xt, yt = fabric.transform_point(x, y, from_epsg, to_epsg)
            return {"x": xt, "y": yt, "crs": f"EPSG:{to_epsg}"}
        except Exception as e:
            return {"error": str(e)}

    # Alias
    @mcp.tool(name="geox_transform_coordinates")
    async def alias_geox_transform_coordinates(x, y, from_epsg, to_epsg):
        return await map_transform_coordinates(x, y, from_epsg, to_epsg)

    @mcp.tool(name="map_project_well")
    async def map_project_well(well_id: str, target_epsg: int = 4326) -> dict:
        """Project a well trajectory into map coordinates (WGS84 default)."""
        evidence = store.get_evidence(well_id)
        if not evidence or evidence.ref.kind != "well":
            return {"error": "Valid well evidence required"}

        payload = evidence.payload
        try:
            head = payload["head"]
            survey = payload["survey"]
            
            xyz_points = fabric.project_well_trajectory(
                head_xy=(head["x"], head["y"]),
                md_points=survey["md"],
                incl_points=survey["inc"],
                azim_points=survey["azi"]
            )
            
            head_epsg = head.get("epsg", 32648)
            projected = []
            for p in xyz_points:
                xt, yt = fabric.transform_point(p[0], p[1], head_epsg, target_epsg)
                projected.append({"x": xt, "y": yt, "z": p[2]})
                
            return {"well_id": well_id, "points": projected, "crs": f"EPSG:{target_epsg}"}
        except Exception as e:
            return {"error": f"Projection failed: {e}"}

    # Alias
    @mcp.tool(name="geox_project_well_trajectory")
    async def alias_geox_project_well_trajectory(well_id, target_epsg=4326):
        return await map_project_well(well_id, target_epsg)

    # Standardized tools from user request
    @mcp.tool(name="map_verify_coordinates")
    async def map_verify_coordinates(x: float, y: float, epsg: int) -> dict:
        """Verify if coordinates are within valid geospatial bounds."""
        return {"valid": True, "message": "Placeholder for coord verification"}
    
    @mcp.tool(name="geox_verify_geospatial")
    async def alias_geox_verify_geospatial(x, y, epsg):
        return await map_verify_coordinates(x, y, epsg)

    @mcp.tool(name="map_get_context")
    async def map_get_context(bounds: list) -> dict:
        """Get summary of spatial context within bounds."""
        return {"summary": "Placeholder for spatial context logic"}
    
    @mcp.tool(name="geox_get_context_summary")
    async def alias_geox_get_context_summary(bounds):
        return await map_get_context(bounds)

    @mcp.tool(name="map_render_scene")
    async def map_render_scene(scene_id: str) -> dict:
        """Render a scene for the geospatial fabric."""
        return {"render_url": f"geox://map/render/{scene_id}"}
    
    @mcp.tool(name="geox_render_scene_context")
    async def alias_geox_render_scene_context(scene_id):
        return await map_render_scene(scene_id)
