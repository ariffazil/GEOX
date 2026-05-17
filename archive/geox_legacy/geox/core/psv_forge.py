"""
GEOX PSV Forge: The Prospect State Vector
Unifying Ninefold Substrates into Earth Intelligence PSV.
[PSV = f(Energy, Flux, Pressure, Structure, Time)]
"""
from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np

@dataclass
class ProspectStateVector:
    p_charge: float
    p_trap: float
    p_reservoir: float
    gcoS: float  # Geological Chance of Success
    p10: float
    p50: float
    p90: float
    substrate_lineage: Dict[str, str]
    systemic_entropy: float

def compute_psv_from_substrates(substrate_evidence: Dict[str, Any]) -> ProspectStateVector:
    """
    Translates substrate evidence into the Prospect State Vector.
    """
    # 1. Energy -> Kinetic Intelligence (Maturity)
    kinetic = substrate_evidence.get("kinetic", {"maturity": 0.5})
    # 2. Flux -> Flow Intelligence (Migration)
    flow = substrate_evidence.get("flow", {"mobility": 0.5})
    # 3. Pressure -> Stress Intelligence (Containment)
    stress = substrate_evidence.get("stress", {"seal_integrity": 0.5})
    # 4. Structure -> Break/Strata Intelligence (Trap)
    structure = substrate_evidence.get("structure", {"closure": 0.5})
    # 5. Material -> Lithos/Pore Intelligence (Reservoir)
    material = substrate_evidence.get("pore", {"porosity": 0.15})
    
    # ── Probability Derivation ──
    # P_charge = f(Kinetic Energy * Flow Flux)
    p_charge = min(1.0, kinetic["maturity"] * 1.2 * flow["mobility"])
    
    # P_trap = f(Stress Containment * Structural Closure)
    p_trap = min(1.0, stress["seal_integrity"] * structure["closure"])
    
    # P_reservoir = f(Pore Void * Lithos Matrix)
    p_reservoir = 0.85 if material["porosity"] > 0.1 else 0.4
    
    gcoS = p_charge * p_trap * p_reservoir
    
    # ── Volumetric Derivation (Probabilistic Volume) ──
    # Derived from Pore (Volume) and Strata (Geometry)
    base_volume = substrate_evidence.get("volume_m3", 1000000)
    p50 = base_volume * (material["porosity"] / 0.15)
    p10 = p50 * 2.5 # Upside
    p90 = p50 * 0.4 # Downside
    
    return ProspectStateVector(
        p_charge=round(p_charge, 4),
        p_trap=round(p_trap, 4),
        p_reservoir=round(p_reservoir, 4),
        gcoS=round(gcoS, 4),
        p10=round(p10, 0),
        p50=round(p50, 0),
        p90=round(p90, 0),
        substrate_lineage={
            "energy": "kinetic_substrate",
            "flux": "flow_substrate",
            "pressure": "stress_substrate",
            "structure": "break_substrate",
            "time": "strata_substrate"
        },
        systemic_entropy=substrate_evidence.get("dS", 0.1)
    )
