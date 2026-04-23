"""
GEOX Canonical Substrate Tool: geox_lithos_tool
Substrate: Lithos (The Matrix) | Constant: Mass (rho_b)
"""
from geox.envelopes.ses_evidence import SESEvidenceObject
from geox.laws.physics_guard import PhysicsGuard
from geox.legacy_skills.petro import las_ingest
from geox.legacy_skills.subsurface import stress_geomechanics

@mcp.tool(name="geox_lithos_tool")
async def geox_lithos_tool(uwi: str):
    """Evaluates Earth Matrix: grain size, mineralogy, density."""
    await PhysicsGuard.verify_vertical(uwi, [])
    
    # Surgical Extraction: Load well and compute matrix density
    raw_data = await las_ingest.ingest(uwi)
    vp_ms = raw_data.get("vp_avg", 3000.0)
    rho_matrix = stress_geomechanics.gardner_velocity_to_density(vp_ms)
    
    result = {
        "substrate": "lithos",
        "uwi": uwi,
        "rho_matrix_gcc": rho_matrix,
        "vp_avg_ms": vp_ms,
        "lithology_guess": "sandstone" if rho_matrix < 2.6 else "carbonate",
    }
    
    envelope = SESEvidenceObject(tool_name="geox_lithos_tool")
    return envelope.wrap(result, claim_tag="COMPUTED")
