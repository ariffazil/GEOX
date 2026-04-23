"""
GEOX Wealth Score Kernel: Governed Capital Translation Layer
Hardened via 9-Harness Constraint Architecture
"""
import math
from typing import Any, Dict, List, Optional, Annotated
from pydantic import Field
from geox.wealth.harness_engine import HarnessEngine

# --- Core Economic Formulas ---

def compute_npv(initial_investment: float, cash_flows: List[float], discount_rate: float) -> float:
    """Standard NPV: Sum(CF_t / (1+r)^t) - I"""
    npv = -abs(initial_investment)
    for t, cf in enumerate(cash_flows, start=1):
        npv += cf / pow(1 + discount_rate, t)
    return round(npv, 6)

def compute_emv(scenarios: List[dict]) -> float:
    """Expected Monetary Value: Sum(Prob_i * Outcome_i)"""
    emv = sum(s.get("probability", 0.0) * s.get("outcome", 0.0) for s in scenarios)
    return round(emv, 6)

def compute_capital_x_rate(base_rate: float, d_s: float, maruah: float = 0.5, peace2: float = 1.0) -> float:
    """CapitalX Pricing Function adjusted for dS."""
    entropy_penalty = max(0.0, d_s * 0.5)
    peace_discount = min(0.02, max(0.0, (peace2 - 1.0) * 0.05))
    maruah_discount = min(0.03, max(0.0, (maruah - 0.5) * 0.06))
    
    r_adj = base_rate + entropy_penalty - peace_discount - maruah_discount
    return max(0.0, round(r_adj, 6))

# --- Canonical MCP Tool ---

async def geox_to_wealth_score(
    substrate_evidence: Annotated[dict, Field(description="Evidence object from any geox substrate tool")],
    base_rate: Annotated[float, Field(description="Base cost of capital (default 0.10)")] = 0.10,
    parent_chain_hash: Annotated[str, Field(description="Parent hash for Identity Chaining protocol")] = ""
) -> dict:
    """
    Bridges GEOX Substrate Evidence to Governed Capital Projection.
    Now enforced by the 9-Harness Constraint Architecture.
    """
    engine = HarnessEngine()
    
    # Prepare inputs for audit
    flags = substrate_evidence.get("flags", [])
    if substrate_evidence.get("claim_tag") == "ESTIMATE":
        flags.append("EPISTEMIC_FALLBACK")
        
    primary_data = {
        "carbon_intensity": substrate_evidence.get("carbon_intensity", 0.01),
        "collapse_risk": substrate_evidence.get("collapse_risk", 0.05),
        "hcpv": substrate_evidence.get("primary_result", {}).get("hcpv_m3", 0)
    }
    
    # 1. THE HARNESS AUDIT
    audit_res = engine.audit(
        tool_name="geox_to_wealth_score",
        primary=primary_data,
        flags=flags,
        parent_hash=parent_chain_hash
    )
    
    if audit_res["verdict"] == "FAIL":
        return {
            "verdict": "VOID",
            "reason": "HARNESS_BREACH",
            "violations": audit_res["violations"],
            "systemic_stress": audit_res["systemic_stress"],
            "harness_status": audit_res["harness_status"]
        }
        
    # 2. Capital Projection logic (If internal audit passed)
    ds = substrate_evidence.get("dS", substrate_evidence.get("entropy", 0.1))
    r_adj = compute_capital_x_rate(base_rate, ds)
    
    outcomes = substrate_evidence.get("scenarios", [
        {"probability": 0.3, "outcome": primary_data["hcpv"] * 50}, 
        {"probability": 0.7, "outcome": -1000000}
    ])
    
    emv = compute_emv(outcomes)
    
    return {
        "tool": "geox_wealth_score_kernel",
        "verdict": "SEAL" if emv > 0 else "HOLD",
        "emv_usd": emv,
        "r_adj": r_adj,
        "harness_audit": {
             "systemic_stress": audit_res["systemic_stress"],
             "lineage_hash": audit_res["harness_lineage_hash"],
             "doctrine_hash": audit_res["doctrine_hash"]
        },
        "epistemic_grade": substrate_evidence.get("claim_tag", "ESTIMATE")
    }
