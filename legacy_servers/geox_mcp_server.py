import os
import logging
import sys
import pandas as pd
from typing import Optional
from fastmcp import FastMCP
from geox.shared.contracts.schemas import EvidenceObject, EvidenceRef, EvidenceKind

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Sovereign MCP Server (v1.9.1) - PHYSICS9 CORE
# ═══════════════════════════════════════════════════════════════════════════════
# DITEMPA BUKAN DIBERI: Structured Response Contract Live
# ═══════════════════════════════════════════════════════════════════════════════

mcp = FastMCP("geox")
logger = logging.getLogger("geox_mcp")
GEOX_SEAL = "999_SEAL_V1"

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS_REGISTRY: Manifest for UI/Bridge Sync (Physics9 Alignment)
# ═══════════════════════════════════════════════════════════════════════════════
TOOLS_REGISTRY = {
    "dimensions": ["prospect", "well", "section", "earth3d", "time4d", "physics", "map"],
    "apps": [
        {"id": "prospect-ui", "name": "Prospect UI", "dim": "prospect"},
        {"id": "well-desk", "name": "Well Desk", "dim": "well"},
        {"id": "section-canvas", "name": "Section Canvas", "dim": "section"},
        {"id": "earth-volume", "name": "Earth Volume", "dim": "earth3d"},
        {"id": "chronos-history", "name": "Chronos History", "dim": "time4d"},
        {"id": "judge-console", "name": "Judge Console", "dim": "physics"},
        {"id": "map-layer", "name": "Map Layer", "dim": "map"}
    ],
    "version": "2026.04.12-EIC"
}

# Inject arifOS Intelligence Layer
try:
    # Ensure arifosmcp is in path if not installed
    arifos_path = r"C:\ariffazil\arifOS"
    if arifos_path not in sys.path:
        sys.path.append(arifos_path)
    
    from arifosmcp.runtime.thinking import ThinkingSessionManager
    tsm = ThinkingSessionManager()
    HAS_THINKING = True
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"arifOS Thinking Module not functional: {e}")
    HAS_THINKING = False

# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES: Sovereign Reference Data
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.resource("physics9://materials_atlas")
async def get_geox_materials() -> str:
    """RATLAS Global Material Database for physics verification."""
    if os.path.exists("geox_atlas_99_materials.csv"):
        return pd.read_csv("geox_atlas_99_materials.csv").to_string()
    return "Error: RATLAS csv missing."

# Interchangeable Alias (Legacy support)
@mcp.resource("canon9://materials_atlas")
async def get_geox_materials_legacy() -> str:
    return await get_geox_materials()

@mcp.resource("geox://reasoning/traces/{session_id}")
async def get_reasoning_trace_resource(session_id: str) -> str:
    """Provides a markdown view of a specific reasoning trace."""
    if not HAS_THINKING:
        return "Thinking module disabled."
    
    session = tsm.get_session(session_id)
    if not session:
        return f"Session {session_id} not found."
    
    return session.export_markdown()

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS: Sovereign Intelligence (Structured Contracts)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.prompt(name="SOVEREIGN_GEOX_SYSTEM_PROMPT")
def geox_system_prompt() -> str:
    return """
    You are GEOX, a sovereign subsurface governance coprocessor. 
    You are a Brutalist Geologist.
    
    RESPONSE CONTRACT (MANDATORY):
    Return your response as a structured report:
    - SUMMARY: [Max 2 sentences UI text]
    - STANCE: [CLAIM | PLAUSIBLE | HYPOTHESIS | UNKNOWN | HOLD]
    - BLOCKING: [true | false]
    - FLOOR_REPORT: [F2 Truth status, F7 Humility notes, F9 Anti-Hantu flags]
    - NEXT_TOOL: [Optional mcp.tool suggestion to clear blocks]
    
    GOVERNANCE RULES:
    1. If scene status is 'HOLD', you MUST set BLOCKING: true and STANCE: HOLD.
    2. Never invent numbers. Reference only provided context.
    3. State the dimension (PROSPECT/WELL/SECTION/EARTH3D/TIME4D/PHYSICS/MAP).
    """

# ═══════════════════════════════════════════════════════════════════════════════
# BRIDGE: Governance & Synthesis
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICES: Internal Business Logic
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from services.geo_fabric.engine import fabric
    from services.evidence_store.store import store
    from services.governance.judge import judge
    from services.witness_engine.petrophysics import witness
    HAS_SERVICES = True
except ImportError as e:
    logger.error(f"Failed to load core services: {e}")
    HAS_SERVICES = False
    # Print traceback for debugging
    import traceback
    traceback.print_exc()

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS: WITNESS (PETROPHYSICS)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_select_sw_model")
async def geox_select_sw_model(formation: str, temperature_c: float) -> dict:
    """Recommends a Water Saturation (Sw) model based on formation context."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}
    return witness.select_sw_model(formation, temperature_c)

@mcp.tool(name="geox_compute_petrophysics")
async def geox_compute_petrophysics(
    model: str, 
    rw: float, 
    rt: float, 
    phi: float, 
    a: float = 1.0, 
    m: float = 2.0, 
    n: float = 2.0
) -> dict:
    """Executes physics-9 grounded petrophysical calculations."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}
    
    result = witness.compute_archie_sw(model, rw, rt, phi, a, m, n)
    return result.model_dump()

@mcp.tool(name="geox_petrophysical_hold_check")
async def geox_petrophysical_hold_check(well_id: str, phi: float, sw: float) -> dict:
    """Governance check (888_HOLD) for anomalous petrophysics."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}
    return witness.hold_check(well_id, phi, sw)

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS: EVIDENCE & MANIFOLD
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_search_evidence")
async def geox_search_evidence(kind: Optional[str] = None) -> list:
    """List and filter evidence from the Sovereign Ledger."""
    if not HAS_SERVICES:
        return [{"error": "Services unavailable"}]
    
    refs = store.list_evidence(kind=kind)
    return [ref.model_dump() for ref in refs]

@mcp.tool(name="geox_get_evidence_details")
async def geox_get_evidence_details(evidence_id: str) -> dict:
    """Fetch full evidence object including spatial context and payload."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}
    
    obj = store.get_evidence(evidence_id)
    if not obj:
        return {"error": f"Evidence {evidence_id} not found."}
    return obj.model_dump()

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS: GEO-FABRIC (SPATIAL LAWS)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_transform_coordinates")
async def geox_transform_coordinates(x: float, y: float, from_epsg: int, to_epsg: int) -> dict:
    """Project a point between coordinate systems."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}
    
    try:
        xt, yt = fabric.transform_point(x, y, from_epsg, to_epsg)
        return {"x": xt, "y": yt, "crs": f"EPSG:{to_epsg}"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool(name="geox_project_well_trajectory")
async def geox_project_well_trajectory(well_id: str, target_epsg: int = 4326) -> dict:
    """Project a well trajectory into map coordinates (WGS84 default)."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}

    evidence = store.get_evidence(well_id)
    if not evidence or evidence.ref.kind != "well":
        return {"error": "Valid well evidence required"}

    payload = evidence.payload
    # Expected payload: { head: {x, y, epsg}, survey: {md: [], inc: [], azi: []} }
    try:
        head = payload["head"]
        survey = payload["survey"]
        
        xyz_points = fabric.project_well_trajectory(
            head_xy=(head["x"], head["y"]),
            md_points=survey["md"],
            incl_points=survey["inc"],
            azim_points=survey["azi"]
        )
        
        # Transform each point to target EPSG
        head_epsg = head.get("epsg", 32648) # Default Malay Basin
        projected = []
        for p in xyz_points:
            xt, yt = fabric.transform_point(p[0], p[1], head_epsg, target_epsg)
            projected.append({"x": xt, "y": yt, "z": p[2]})
            
        return {"well_id": well_id, "points": projected, "crs": f"EPSG:{target_epsg}"}
    except Exception as e:
        return {"error": f"Projection failed: {e}"}

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS: GOVERNANCE (888_JUDGE)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_judge_verdict")
async def geox_judge_verdict(
    intent_id: str, 
    well_id: str, 
    prospect_id: str
) -> dict:
    """Execute the Sovereign 888_JUDGE on a Causal Scene."""
    if not HAS_SERVICES:
        return {"error": "Services unavailable"}
    
    well = store.get_evidence(well_id)
    prospect = store.get_evidence(prospect_id)
    
    if not well or not prospect:
        return {"error": f"Evidence not found: well={well_id}, prospect={prospect_id}"}
    
    verdict = judge.evaluate_well_prospect_fit(intent_id, well, prospect)
    
    # Audit the loop
    store.save_evidence(EvidenceObject(
        ref=EvidenceRef(
            id=verdict.verdictId,
            kind=EvidenceKind.verdict,
            sourceUri=f"geox://verdicts/{verdict.verdictId}",
            timestamp=verdict.timestamp
        ),
        context=well.context,
        payload=verdict.model_dump()
    ))
    
    return verdict.model_dump()

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS: ACP GOVERNANCE (AGENT CONTROL PLANE)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from geox_mcp_server_acp import (
        acp_register_agent,
        acp_submit_proposal,
        acp_check_convergence,
        acp_grant_seal,
        acp_get_status
    )
    
    @mcp.tool(name="acp_register_agent")
    async def tool_acp_register_agent(
        agent_id: str,
        role: str,
        name: str,
        resources: Optional[list] = None,
        tools: Optional[list] = None
    ) -> dict:
        """Register an agent with the Agent Control Plane."""
        return await acp_register_agent(agent_id, role, name, resources, tools)

    @mcp.tool(name="acp_submit_proposal")
    async def tool_acp_submit_proposal(agent_id: str, proposal: dict) -> dict:
        """Submit a proposal for 888_JUDGE evaluation."""
        return await acp_submit_proposal(agent_id, proposal)

    @mcp.tool(name="acp_check_convergence")
    async def tool_acp_check_convergence(resource: str) -> dict:
        """Check agent convergence on a resource."""
        return await acp_check_convergence(resource)

    @mcp.tool(name="acp_grant_seal")
    async def tool_acp_grant_seal(proposal_id: str, human_auth_token: str) -> dict:
        """Grant 999_SEAL (sovereign human authority)."""
        return await acp_grant_seal(proposal_id, human_auth_token)

    @mcp.tool(name="acp_get_status")
    async def tool_acp_get_status() -> dict:
        """Get ACP system status."""
        return await acp_get_status()

except ImportError as e:
    logger.warning(f"ACP Governance modules not found: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# BRIDGE: Legacy & Registry
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="geox_get_tools_registry")
async def geox_get_tools_registry() -> dict:
    """Returns the architectural TOOLS_REGISTRY for UI synchronization."""
    return TOOLS_REGISTRY

if __name__ == "__main__":
    mcp.run()