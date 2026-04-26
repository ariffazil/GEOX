"""
GEOX Canonical Tool: geox_well_tool
Standard: Consolidation Spec v1.1
Plane: X-1D (Sense)
"""
import uuid
from datetime import datetime
try:
    from geox.legacy_skills import las_ingest_tool
except ImportError:
    class _LasIngestStub:
        @staticmethod
        async def ingest(uwi: str):
            return {"header": {}, "tops": [], "intervals": []}
    las_ingest_tool = _LasIngestStub()
from geox.laws.physics_guard import physics_guard

def generate_ses_id():
    return str(uuid.uuid4())

async def well_tool_execute(uwi: str, depth_range: dict = None):
    """Canonical wrapper for vertical well intelligence."""
    
    # 1. PhysicsGuard (SES Gate)
    # Verifies depth_range consistency and UWI presence
    await physics_guard.verify_preconditions(uwi, depth_range)
    
    # 2. Substrate Call (Internal Legacy Logic)
    # Absorbs: geox_well_load_bundle, geox_well_qc_logs
    raw_data = await las_ingest_tool.ingest(uwi)
    
    # 3. Emit Evidence (NOT Sealed)
    evidence = {
        "evidence_id": generate_ses_id(),
        "tool": "geox_well_tool",
        "timestamp": datetime.utcnow().isoformat(),
        "parent_ids": [raw_data.get("lineage_id", "none")],
        "physics_hash": "sha256_well_structural_v1",
        "claim_tag": "OBSERVATION",
        "uncertainty": {
            "method": "depth_error_correction",
            "sigma": 0.05
        },
        "data": {
            "header": raw_data.get("header"),
            "tops": raw_data.get("tops"),
            "intervals": raw_data.get("intervals")
        }
    }
    
    return evidence
