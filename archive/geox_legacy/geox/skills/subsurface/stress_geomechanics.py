"""
GEOX Legacy Substrate: Stress & Pressure Logic
Surgically extracted from geox/core/geox_data.py and petro_ensemble.py
"""
import math

def compute_overburden_pressure(depth_m: float, avg_density_gcc: float = 2.3) -> float:
    """
    Computes lithostatic pressure (Sv).
    Substrate: Stress (Pressure constant).
    """
    # Pressure (MPa) = density (kg/m3) * g * h / 1e6
    density_kgm3 = avg_density_gcc * 1000
    pressure_mpa = (density_kgm3 * 9.81 * depth_m) / 1000000.0
    return pressure_mpa

def estimate_pore_pressure(depth_m: float, gradient_mpa_m: float = 0.0105) -> float:
    """
    Simplified pore pressure estimate based on hydrostatic gradient.
    """
    return depth_m * gradient_mpa_m

def gardner_velocity_to_density(vp_ms: float) -> float:
    """
    Gardner's Relation: rho = 0.23 * Vp^0.25 (Vp in ft/s, rho in g/cc)
    Converting Vp to ft/s: Vp_fts = Vp_ms * 3.28084
    """
    vp_fts = vp_ms * 3.28084
    rho = 0.23 * (vp_fts**0.25)
    return round(rho, 3)
