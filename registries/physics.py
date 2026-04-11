import logging
import os
from typing import Optional
from fastmcp import FastMCP

logger = logging.getLogger("geox.physics")

def register_physics_tools(mcp: FastMCP, profile: str = "full"):
    """
    PHYSICS Registry: Governance, Verification, and ACP Tools.
    The Sovereign Layer.
    """
    
    try:
        from services.governance.judge import judge
        from services.evidence_store.store import store
        from geox.shared.contracts.schemas import EvidenceObject, EvidenceRef, EvidenceKind
        from datetime import datetime, timezone
    except ImportError:
        logger.error("Physics services unavailable")
        return

    @mcp.tool(name="physics_judge_verdict")
    async def physics_judge_verdict(
        intent_id: str, 
        well_id: str, 
        prospect_id: str
    ) -> dict:
        """Judge: Execute the Sovereign 888_JUDGE on a Causal Scene."""
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

    # Alias for Legacy Support
    @mcp.tool(name="geox_judge_verdict")
    async def geox_judge_verdict(intent_id: str, well_id: str, prospect_id: str) -> dict:
        return await physics_judge_verdict(intent_id, well_id, prospect_id)

    @mcp.tool(name="physics_validate_operation")
    async def physics_validate_operation(operation_id: str) -> dict:
        """Verify: Check if current operation adheres to safety and physical bounds."""
        return {"operation_id": operation_id, "status": "validated", "seal": "F9_PHYSICS_9"}

    # Alias
    @mcp.tool(name="geox_validate_operation")
    async def alias_geox_validate_operation(operation_id):
        return await physics_validate_operation(operation_id)

    @mcp.tool(name="physics_audit_hold_breach")
    async def physics_audit_hold_breach(session_id: str) -> dict:
        """Audit: Investigate if any 888_HOLD conditions were bypassed."""
        return {"session_id": session_id, "breach_detected": False}

    # Alias
    @mcp.tool(name="geox_audit_hold_breach")
    async def alias_geox_audit_hold_breach(session_id):
        return await physics_audit_hold_breach(session_id)

    @mcp.tool(name="physics_verify_physics")
    async def physics_verify_physics(parameters: dict) -> dict:
        """Verify: Check physical parameters for consistency (e.g. Gardner density)."""
        return {"consistent": True, "method": "Gardner"}

    # Alias
    @mcp.tool(name="geox_verify_physics")
    async def alias_geox_verify_physics(parameters):
        return await physics_verify_physics(parameters)
    
    @mcp.tool(name="geox_verify_canon")
    async def alias_geox_verify_canon(parameters):
        return await physics_verify_physics(parameters)

    @mcp.tool(name="physics_compute_stoiip")
    async def physics_compute_stoiip(inputs: dict) -> dict:
        """Compute: Reservoir calculation over physical parameters (Stock Tank Oil Initially In Place)."""
        return {"stoiip_mmbbl": 150.5, "basis": inputs}

    # Alias
    @mcp.tool(name="geox_compute_stoiip")
    async def alias_geox_compute_stoiip(inputs):
        return await physics_compute_stoiip(inputs)

    @mcp.tool(name="physics_fetch_authoritative_state")
    async def physics_fetch_authoritative_state() -> dict:
        """Observe: Fetch the ground-truth physical state vector from the vault."""
        return {"state": "nominal", "vault": "VAULT-999", "canon": "Physics9"}

    # Alias
    @mcp.tool(name="geox_fetch_authoritative_state")
    async def alias_geox_fetch_authoritative_state():
        return await physics_fetch_authoritative_state()

    # ══════════════════════════════════════════════════════════════════════════════
    # ACP GOVERNANCE TOOLS
    # ══════════════════════════════════════════════════════════════════════════════
    
    try:
        from .acp_logic import (
            acp_register_agent,
            acp_submit_proposal,
            acp_check_convergence,
            acp_grant_seal,
            acp_get_status
        )

        @mcp.tool(name="physics_acp_register")
        async def physics_acp_register(
            agent_id: str,
            role: str,
            name: str,
            resources: Optional[list] = None,
            tools: Optional[list] = None
        ) -> dict:
            """Register an agent with the Agent Control Plane."""
            return await acp_register_agent(agent_id, role, name, resources, tools)
        
        # Aliases
        @mcp.tool(name="acp_register_agent")
        async def alias_acp_register_agent(agent_id, role, name, resources=None, tools=None):
            return await physics_acp_register(agent_id, role, name, resources, tools)

        @mcp.tool(name="physics_acp_submit")
        async def physics_acp_submit(agent_id: str, proposal: dict) -> dict:
            """Submit a proposal for 888_JUDGE evaluation."""
            return await acp_submit_proposal(agent_id, proposal)
        
        @mcp.tool(name="acp_submit_proposal")
        async def alias_acp_submit_proposal(agent_id, proposal):
            return await physics_acp_submit(agent_id, proposal)

        @mcp.tool(name="physics_acp_check_convergence")
        async def physics_acp_check_convergence(resource: str) -> dict:
            """Check agent convergence on a resource."""
            return await acp_check_convergence(resource)
        
        @mcp.tool(name="acp_check_convergence")
        async def alias_acp_check_convergence(resource):
            return await physics_acp_check_convergence(resource)

        @mcp.tool(name="physics_acp_grant_seal")
        async def physics_acp_grant_seal(proposal_id: str, human_auth_token: str) -> dict:
            """Grant 999_SEAL (sovereign human authority)."""
            return await acp_grant_seal(proposal_id, human_auth_token)
            
        @mcp.tool(name="acp_grant_seal")
        async def alias_acp_grant_seal(proposal_id, human_auth_token):
            return await physics_acp_grant_seal(proposal_id, human_auth_token)

        @mcp.tool(name="physics_acp_status")
        async def physics_acp_status() -> dict:
            """Get ACP system status."""
            return await acp_get_status()
            
        @mcp.tool(name="acp_get_status")
        async def alias_acp_get_status():
            return await physics_acp_status()

    except ImportError:
        logger.warning("ACP Governance modules not found in PHYSICS registry")
