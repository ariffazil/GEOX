"""
GEOX Canonical Substrate Tool: geox_pore_tool & geox_fluid_tool
Substrate: Pores (Void) & Fluids (Charge)
"""
from geox.envelopes.ses_evidence import SESEvidenceObject
from geox.laws.physics_guard import PhysicsGuard
from geox.skills.subsurface import reservoir_dynamics

@mcp.tool(name="geox_pore_tool")
async def geox_pore_tool(well_id: str, phi_avg: float = 0.2):
    """Evaluates Earth Void: porosity and permeability proxies."""
    await PhysicsGuard.verify_vertical(well_id, [])
    
    # Surgical Extraction: Compute permeability from porosity
    perm_md = reservoir_dynamics.estimate_permeability_from_phi(phi_avg)
    
    result = {
        "substrate": "pore",
        "well_id": well_id,
        "phi_avg": phi_avg,
        "permeability_est_md": perm_md,
    }
    envelope = SESEvidenceObject(tool_name="geox_pore_tool")
    return envelope.wrap(result, claim_tag="ESTIMATE")

@mcp.tool(name="geox_fluid_tool")
async def geox_fluid_tool(well_id: str, phi: float, sw: float, area_m2: float = 1e6, thickness_m: float = 20.0):
    """Evaluates Earth Charge: saturation and HC volume."""
    await PhysicsGuard.verify_vertical(well_id, [])
    
    # Surgical Extraction: Compute HCPV
    hcpv_m3 = reservoir_dynamics.probabilistic_hcpv_lite(
        area_m2=area_m2, thickness_m=thickness_m, ntg=0.8, phi=phi, sw=sw, fvf=1.2
    )
    
    result = {
        "substrate": "fluid",
        "well_id": well_id,
        "sw": sw,
        "hcpv_m3": hcpv_m3,
        "unit": "cubic_meters"
    }
    envelope = SESEvidenceObject(tool_name="geox_fluid_tool")
    return envelope.wrap(result, claim_tag="COMPUTED")
