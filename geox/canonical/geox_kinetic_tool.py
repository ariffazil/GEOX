"""
GEOX Canonical Substrate Tool: geox_kinetic_tool
Substrate: Kinetic (Energy) | Constant: Temperature (T)
"""
from geox.envelopes.ses_evidence import SESEvidenceObject
from geox.laws.physics_guard import PhysicsGuard
from geox.legacy_skills.subsurface import maturity_kinetics

@mcp.tool(name="geox_kinetic_tool")
async def geox_kinetic_tool(uwi: str, burial_history: list[dict[str, float]]):
    """Evaluates Earth Energy: thermal maturity and heat-time index."""
    await PhysicsGuard.verify_kinetic(uwi, [])
    
    # Surgical Extraction: Easy%Ro and TTI
    tti = maturity_kinetics.compute_tti(burial_history)
    easy_ro = maturity_kinetics.compute_easy_ro(tti)
    charge_age = maturity_kinetics.get_charge_age(burial_history)
    
    result = {
        "substrate": "kinetic",
        "uwi": uwi,
        "tti": tti,
        "easy_ro": easy_ro,
        "charge_age_ma": charge_age,
        "constant_hook": "Energy (Temperature)",
        "unit": "Vitrinite Reflectance (%)"
    }
    
    envelope = SESEvidenceObject(tool_name="geox_kinetic_tool")
    return envelope.wrap(result, claim_tag="COMPUTED")
