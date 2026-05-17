"""
GEOX Legacy Substrate: Flow & Dynamic Flux Logic
Surgically extracted from geox/core/volumetrics.py and reservoir-dynamics.md
"""
from typing import Any
import numpy as np

def compute_mobility_index(permeability_md: float, viscosity_cp: float, thickness_m: float) -> float:
    """
    Compute Reservoir Mobility (k/mu) * h.
    Fundamental measure for the Flow substrate (Flux constant).
    """
    if viscosity_cp <= 0:
        return 0.0
    return (permeability_md / viscosity_cp) * thickness_m

def probabilistic_hcpv_lite(
    area_m2: float, 
    thickness_m: float, 
    ntg: float, 
    phi: float, 
    sw: float, 
    fvf: float
) -> float:
    """
    Direct Deterministic HCPV calculation.
    Core logic for Pore (Volume) and Fluid (Saturation) substrates.
    """
    return area_m2 * thickness_m * ntg * phi * (1.0 - sw) / max(fvf, 1e-6)

def estimate_permeability_from_phi(phi: float, lithology: str = "sand") -> float:
    """
    Simple Kozeny-Carman proxy for permeability extraction.
    """
    if phi <= 0: return 0.0
    if lithology == "sand":
        return 10**(3 * phi + 1) # Simple log-linear proxy
    return 10**(2 * phi - 1)
