import logging
from typing import Optional
from fastmcp import FastMCP
from registries import Dimension

logger = logging.getLogger("geox.cross")

def register_cross_tools(mcp: FastMCP, profile: str = "full"):
    """
    CROSS Registry: Evidence & Dimension introspection.
    The glue between dimensions.
    """
    
    try:
        from services.evidence_store.store import store
    except ImportError:
        logger.error("Cross services unavailable")
        return

    @mcp.tool(name="cross_evidence_list")
    async def cross_evidence_list(kind: Optional[str] = None) -> list:
        """List and filter evidence from the Sovereign Ledger."""
        refs = store.list_evidence(kind=kind)
        return [ref.model_dump() for ref in refs]

    # Aliases
    @mcp.tool(name="geox_search_evidence")
    async def alias_geox_search_evidence(kind=None):
        return await cross_evidence_list(kind)
    
    @mcp.tool(name="geox_evidence_list")
    async def alias_geox_evidence_list(kind=None):
        return await cross_evidence_list(kind)

    @mcp.tool(name="cross_evidence_get")
    async def cross_evidence_get(evidence_id: str) -> dict:
        """Fetch full evidence object including spatial context and payload."""
        obj = store.get_evidence(evidence_id)
        if not obj:
            return {"error": f"Evidence {evidence_id} not found."}
        return obj.model_dump()

    # Aliases
    @mcp.tool(name="geox_get_evidence_details")
    async def alias_geox_get_evidence_details(evidence_id):
        return await cross_evidence_get(evidence_id)
    
    @mcp.tool(name="geox_evidence_get")
    async def alias_geox_evidence_get(evidence_id):
        return await cross_evidence_get(evidence_id)

    @mcp.tool(name="cross_dimension_list")
    async def cross_dimension_list() -> dict:
        """What dimensions are currently active in this profile?"""
        return {
            "profile": profile,
            "dimensions": [d.value for d in Dimension]
        }

    # Alias
    @mcp.tool(name="geox_dimension_list")
    async def alias_geox_dimension_list():
        return await cross_dimension_list()

    @mcp.tool(name="geox_get_tools_registry")
    async def geox_get_tools_registry() -> dict:
        """Returns the architectural TOOLS_REGISTRY for UI synchronization."""
        return {
            "dimensions": {
                "prospect": {"name": "Prospecting", "description": "Play Fairway Discovery"},
                "well": {"name": "Well", "description": "Borehole Truth Channel"},
                "section": {"name": "Section", "description": "2D Correlation"},
                "earth3d": {"name": "Earth 3D", "description": "Volumetric Seismic"},
                "time4d": {"name": "Time 4D", "description": "Basin Evolution"},
                "physics": {"name": "Physics", "description": "Sovereign Verification"},
                "map": {"name": "Map", "description": "Spatial Fabric"},
                "cross": {"name": "Cross", "description": "Dimension Introspection"}
            },
            "apps": [
                {"id": "prospect-ui", "name": "Prospect UI", "dim": "prospect"},
                {"id": "well-desk", "name": "Well Desk", "dim": "well"},
                {"id": "section-canvas", "name": "Section Canvas", "dim": "section"},
                {"id": "earth-volume", "name": "Earth Volume", "dim": "earth3d"},
                {"id": "chronos-history", "name": "Chronos History", "dim": "time4d"},
                {"id": "judge-console", "name": "Judge Console", "dim": "physics"},
                {"id": "map-layer", "name": "Map Layer", "dim": "map"}
            ],
            "version": "2.0.0-UNIFIED-SPEC"
        }

    @mcp.tool(name="cross_health")
    async def cross_health() -> dict:
        """Sovereign health check for all platform services."""
        return {
            "status": "healthy",
            "registry": "unified",
            "profile": profile,
            "dimensions": [d.value for d in Dimension]
        }
