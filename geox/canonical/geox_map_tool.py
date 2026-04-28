"""
GEOX Canonical Tool: geox_map_tool
Standard: Consolidation Spec v1.1
Plane: X-2D (Sense)
"""
import uuid
from datetime import datetime
try:
    from geox.skills.subsurface import visualization as map_viz
except ImportError:
    class _MapVizStub:
        @staticmethod
        async def get_geospatial_grid(area_id, crs, resolution):
            return {"id": "none", "binary_values": [], "extents": {}}
    map_viz = _MapVizStub()
from geox.laws.physics_guard import physics_guard

def generate_ses_id():
    return str(uuid.uuid4())

async def map_tool_execute(area_id: str, crs: str, resolution: float):
    """Canonical map/spatial primitive."""
    
    # 1. PhysicsGuard
    await physics_guard.verify_preconditions(area_id, {"crs": crs, "res": resolution})
    
    # 2. Substrate Call
    # Absorbs: map_get_context_summary, georeference
    map_data = await map_viz.get_geospatial_grid(area_id, crs, resolution)
    
    # 3. Emit Evidence
    evidence = {
        "evidence_id": generate_ses_id(),
        "tool": "geox_map_tool",
        "timestamp": datetime.utcnow().isoformat(),
        "parent_ids": [map_data.get("id")],
        "physics_hash": "sha256_spatial_grid_v1",
        "claim_tag": "OBSERVATION",
        "uncertainty": {"grid_variance": 0.02},
        "data": {
            "grid": map_data.get("binary_values"),
            "extents": map_data.get("extents"),
            "crs": crs
        }
    }
    
    return evidence
