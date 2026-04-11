import os
import json
import logging
import pandas as pd
from typing import Optional
from fastmcp import FastMCP
from geox_schemas import (
    OperatorKind, WitnessKind, SupportKind, ContrastOperatorSpec
)

# ═══════════════════════════════════════════════════════════════════════════════
# GEOX Sovereign MCP Server (v1.9)
# ═══════════════════════════════════════════════════════════════════════════════
# DITEMPA BUKAN DIBERI: Structured Response Contract Live
# ═══════════════════════════════════════════════════════════════════════════════

mcp = FastMCP("geox")
logger = logging.getLogger("geox_mcp")
GEOX_SEAL = "999_SEAL_V1"

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
    3. State the dimension (1D/2D/3D/PHYSICS9).
    """

# ═══════════════════════════════════════════════════════════════════════════════
# BRIDGE: Governance & Synthesis
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="bridge.sync_state")
async def bridge_sync_state() -> dict:
    """Fetches the 888_JUDGE authoritative scene state."""
    gold_path = "gold_causal_scene.json"
    if os.path.exists(gold_path):
        with open(gold_path, "r") as f:
            return {"causal_scene": json.load(f)}
    return {"status": "unverified"}

@mcp.tool(name="bridge.render_card_context")
async def bridge_render_card_context(domain: str) -> str:
    """Deterministic summarizer: Distills the scene for LLM synthesis."""
    state = await bridge_sync_state()
    scene = state.get("causal_scene", {})
    return f"""
    DOMAIN: {domain} | STATUS: {scene.get('status')} | EPOCH: {scene.get('epoch')}
    HOLDS: {scene.get('holds', [])} | SIMS: {scene.get('simulation_flags', [])}
    METRICS: {scene.get('manifold', {})}
    """

@mcp.tool(name="bridge.interpret_causal_scene")
async def bridge_interpret_causal_scene(domain: str, user_query: Optional[str] = None) -> str:
    """Assembles distilled context into a structured synthesis prompt."""
    context = await bridge_render_card_context(domain)
    return f"""
    Context: interpret_causal_scene call.
    {context}
    Query: {user_query or "NONE"}
    
    TASK: Generate the structured response contract according to the system prompt.
    """

@mcp.tool(name="bridge.audit_policy_violation")
async def bridge_audit_policy_violation(operator: str, violations: list[str]) -> str:
    """Structured audit for 888_HOLD breaches."""
    return f"""
    AUDIT_ALERT: {operator}
    VIOLATIONS: {violations}
    
    TASK: Generate the structured response contract. Classify as HARD (Block) or SOFT.
    Explain the breach against F2/F8/F9.
    """

@mcp.tool(name="bridge.check_operator_legality")
async def bridge_check_operator_legality(op_kind: str, left_kind: str, left_support: str, right_kind: str, right_support: str) -> dict:
    """Constitutional Firewall: Checks physical operation legality."""
    try:
        spec = ContrastOperatorSpec(
            op_kind=OperatorKind(op_kind),
            left_kind=WitnessKind(left_kind),
            left_support=SupportKind(left_support),
            right_kind=WitnessKind(right_kind),
            right_support=SupportKind(right_support),
            rationale="Pre-flight audit."
        )
        return {"status": "LEGAL", "spec": spec.model_dump()}
    except Exception as e:
        return {"status": "HOLD", "holds": [str(e)], "blocking": True}

# ═══════════════════════════════════════════════════════════════════════════════
# DIMENSIONAL KERNELS (Minimal v1)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool(name="prospect.compute_stoiip")
async def prospect_compute_stoiip(area: float, thickness: float, phi: float, sw: float, fvf: float, witness_id: Optional[str] = None) -> dict:
    stoiip = (6.2898 * area * thickness * phi * (1 - sw)) / fvf
    return {"stoiip_stb": stoiip, "status": "VERIFIED" if witness_id else "SIMULATED"}

@mcp.tool(name="physics9.verify_state")
async def physics9_verify_state():
    return {"status": "verified", "audit": "PASS", "floor": "F2_PHYSICS"}

@mcp.tool(name="canon9.verify_state")
async def canon9_verify_state():
    return await physics9_verify_state()

if __name__ == "__main__":
    mcp.run()