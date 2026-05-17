"""
GEOX Valuation Engine: Decision Sovereignty Layer
Translating Prospect State Vector (PSV) into Risked Capital Projections.
[PSV -> EMV -> Constitutional Gate -> SEAL]
"""
from typing import Dict, Any, List
from geox.core.psv_forge import ProspectStateVector
from geox.wealth.wealth_score_kernel import compute_emv, compute_npv, compute_capital_x_rate
from geox.wealth.harness_engine import HarnessEngine

def compute_sovereign_valuation(
    psv: ProspectStateVector,
    capex: float,
    opex_per_year: float,
    price_per_unit: float,
    discount_rate: float = 0.10,
    parent_chain_hash: str = ""
) -> Dict[str, Any]:
    """
    Project-level capital allocation audited by the 9-Harness engine.
    """
    # 1. Success Outcomes
    success_outcome = (psv.p50 * price_per_unit) - capex - (opex_per_year * 10)
    failure_outcome = -capex
    
    scenarios = [
        {"probability": psv.gcoS, "outcome": success_outcome},
        {"probability": 1.0 - psv.gcoS, "outcome": failure_outcome}
    ]
    
    # 2. Risk-Pricing (CapitalX)
    r_adj = compute_capital_x_rate(discount_rate, psv.systemic_entropy)
    
    # 3. Decision Metrics
    emv = compute_emv(scenarios)
    npv = compute_npv(capex, [success_outcome / 10] * 10, r_adj)
    
    # 4. Sovereign Audit (The Brakes)
    engine = HarnessEngine()
    audit_input = {
        "emv": emv,
        "npv": npv,
        "p_success": psv.gcoS,
        "entropy": psv.systemic_entropy,
        # Derived Civilizational metrics for the audit
        "carbon_intensity": 0.035 if emv > 0 else 0.0,
        "collapse_risk": 0.15 if psv.systemic_entropy > 0.3 else 0.05
    }
    
    audit_res = engine.audit(
        tool_name="compute_sovereign_valuation",
        primary=audit_input,
        flags=["PROBABILISTIC_CONVERGENCE"],
        parent_hash=parent_chain_hash
    )
    
    return {
        "tool": "geox_valuation_engine",
        "verdict": audit_res["verdict"],
        "metrics": {
            "emv_usd": emv,
            "npv_risked_usd": npv,
            "r_adjusted": r_adj,
            "geological_chance": psv.gcoS
        },
        "harness_audit": audit_res,
        "decision_state": "SEAL" if audit_res["verdict"] == "PASS" and emv > 0 else "HOLD"
    }
