"""
GEOX Canonical Tool: geox_log_tool
Standard: Consolidation Spec v1.1
Plane: X-1D (Sight)
"""
import uuid
from datetime import datetime
try:
    from geox.legacy_skills import petro_ensemble_tool
except ImportError:
    class _PetroEnsembleStub:
        @staticmethod
        async def execute_petrophysics(well_id, curves):
            return {"phie": 0.0, "sw": 1.0, "lithology": "unknown", "uncertainty_model": {}, "lineage_id": "none"}
    petro_ensemble_tool = _PetroEnsembleStub()
from geox.laws.physics_guard import physics_guard

def generate_ses_id():
    return str(uuid.uuid4())

async def log_tool_execute(well_id: str, curves: list, interval: dict):
    """Canonical log interpretation primitive. Absorbs legacy petrophysics."""
    
    # 1. PhysicsGuard (SES Gate)
    # Checks Archie/Gassmann preconditions (phie >= 0, sw <= 1.0)
    await physics_guard.verify_preconditions(well_id, curves, interval)
    
    # 2. Substrate Call
    # Absorbs: geox_log_interpreter, petro_ensemble_v1
    raw_petro = await petro_ensemble_tool.execute_petrophysics(well_id, curves)
    
    # 3. Emit Evidence (Standard Spec v1.1)
    evidence = {
        "evidence_id": generate_ses_id(),
        "tool": "geox_log_tool",
        "timestamp": datetime.utcnow().isoformat(),
        "parent_ids": [raw_petro.get("lineage_id", "none")],
        "physics_hash": "sha256_petro_v1_archie",
        "claim_tag": "ESTIMATE",
        "uncertainty": raw_petro.get("uncertainty_model", {}),
        "data": {
            "phie": raw_petro.get("phie"),
            "sw": raw_petro.get("sw"),
            "lithology": raw_petro.get("lithology")
        }
    }
    
    return evidence
