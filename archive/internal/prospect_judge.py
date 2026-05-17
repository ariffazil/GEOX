import math
from typing import Dict, Any

def calculate_pg(source: float, reservoir: float, trap: float, seal: float, migration: float) -> Dict[str, Any]:
    """
    T02_35: Prospect Judge - Geological Chance of Success (Pg) calculation.
    Enforces F7 Humility: Mandatory uncertainty band Omega_0.
    """
    # Canonical Pg Formula
    raw_pg = source * reservoir * trap * seal * migration
    
    # F7 Humility Constraint: Omega_0 in [0.03, 0.05]
    # We never claim 100% success; we cap the 'Confidence' at 0.95
    omega_0 = 0.05
    forged_pg = min(raw_pg, 1.0 - omega_0)
    
    # F4 Clarity Signal: If Pg is too low, trigger SABAR
    verdict = "FORGED" if forged_pg > 0.15 else "SABAR"
    
    return {
        "raw_pg": round(raw_pg, 4),
        "forged_pg": round(forged_pg, 4),
        "omega_0": omega_0,
        "verdict": verdict,
        "rationale": "F7 Humility Floor applied. Max confidence capped at 0.95."
    }
