"""
GEOX Canonical Tool: geox_coupling_engine
Substrate: THE CONVERGENCE (Nonlinear Coupling)
"""
from geox.envelopes.ses_evidence import SESEvidenceObject
from geox.laws.physics_guard import PhysicsGuard
from geox.core.physics9 import Physics9State, metabolic_loop
from typing import Dict, Any

@mcp.tool(name="geox_convergence_metabolic_loop")
async def geox_convergence_metabolic_loop(
    initial_substrate_state: Dict[str, float],
    measurements: Dict[str, float]
):
    """
    Executes the Forward-Inverse Metabolic Loop to converge multiple substrates.
    E.g., Stress + Break + Pore → Causal State Inference.
    """
    # 1. Verify Spatial/Kinetic context via PhysicsGuard
    await PhysicsGuard.verify_closure("CONVERGENCE_TARGET")
    
    # 2. Extract state from vector
    state = Physics9State.from_vector([
        initial_substrate_state.get("rho", 2350),
        initial_substrate_state.get("vp", 2950),
        initial_substrate_state.get("vs", 1680),
        initial_substrate_state.get("rho_e", 20),
        initial_substrate_state.get("chi", 0.0001),
        initial_substrate_state.get("k", 2.5),
        initial_substrate_state.get("P", 20e6),
        initial_substrate_state.get("T", 320),
        initial_substrate_state.get("phi", 0.25)
    ])
    
    # 3. Execute Nonlinear Coupling (The Metabolic Loop)
    loop_result = metabolic_loop(state, measurements, max_iterations=50)
    
    # 4. Wrap and Emit Evidence
    result = {
        "substrate": "convergence",
        "converged": loop_result["converged"],
        "final_state": loop_result["converged_state"].to_dict(),
        "lithology": loop_result["final_lithology"],
        "cycles": loop_result["loop_cycles"],
        "metabolic_metadata": loop_result["metadata"]
    }
    
    envelope = SESEvidenceObject(tool_name="geox_convergence_metabolic_loop")
    return envelope.wrap(result, claim_tag="COMPUTED")
