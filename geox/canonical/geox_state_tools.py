"""
GEOX Canonical Substrate Tool: geox_state_tools
Substrate: Stress (Pressure) & Flow (Flux)
"""
from geox.envelopes.ses_evidence import SESEvidenceObject
from geox.laws.physics_guard import PhysicsGuard
from geox.legacy_skills.subsurface import stress_geomechanics, reservoir_dynamics

@mcp.tool(name="geox_stress_tool")
async def geox_stress_tool(well_id: str, depth: float):
    """Evaluates Earth Potential: pore pressure and geomechanics."""
    await PhysicsGuard.verify_stress(well_id, depth)
    
    # Surgical Extraction: Overburden and Pore Pressure
    sv = stress_geomechanics.compute_overburden_pressure(depth)
    pp = stress_geomechanics.estimate_pore_pressure(depth)
    
    result = {
        "substrate": "stress",
        "well_id": well_id,
        "depth_m": depth,
        "overburden_sv_mpa": sv,
        "pore_pressure_pp_mpa": pp,
        "effective_stress_mpa": sv - pp,
        "constant_hook": "Pressure (P)"
    }
    envelope = SESEvidenceObject(tool_name="geox_stress_tool")
    return envelope.wrap(result, claim_tag="OBSERVED")

@mcp.tool(name="geox_flow_tool")
async def geox_flow_tool(asset_id: str, k_avg: float = 100.0, mu: float = 1.0, h: float = 10.0):
    """Evaluates Earth Dynamics: permeability and flux potential."""
    await PhysicsGuard.verify_closure(asset_id)
    
    # Surgical Extraction: Mobility Index (k/mu * h)
    mobility = reservoir_dynamics.compute_mobility_index(k_avg, mu, h)
    
    result = {
        "substrate": "flow",
        "asset_id": asset_id,
        "mobility_index_kh_mu": mobility,
        "constant_hook": "Flux (k, mu)",
        "unit": "md-m/cp"
    }
    envelope = SESEvidenceObject(tool_name="geox_flow_tool")
    return envelope.wrap(result, claim_tag="ESTIMATE")
