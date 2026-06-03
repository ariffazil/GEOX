"""
geox_core.physics.parameters — Static Physics Equations

Pure functions: state → scalar or array.
No side effects, no interpretation, no ML.

Includes:
  • Derived elastic moduli
  • Rock physics (Gardner, Faust, Bellotti)
  • Anisotropy (Thomsen)
  • Attenuation (Q-factor)
  • Well-tie primitives (AI, RC, wavelet, convolution)

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np
from scipy import signal

from geox_core.physics.state import Physics9State


# ─── Derived Elastic Moduli ─────────────────────────────────────────────────


def bulk_modulus(vp: float, vs: float, rho: float) -> float:
    """K = ρ(Vp² − 4/3 Vs²) [Pa]"""
    return rho * (vp**2 - (4.0 / 3.0) * vs**2)


def shear_modulus(vs: float, rho: float) -> float:
    """G = ρ Vs² [Pa]"""
    return rho * vs**2


def young_modulus(K: float, G: float) -> float:
    """E = G(3K + G)/(K + G) [Pa]"""
    return G * (3 * K + G) / (K + G)


def poisson_ratio(K: float, G: float) -> float:
    """ν = (3K − 2G)/(6K + 2G)"""
    return (3 * K - 2 * G) / (6 * K + 2 * G)


def acoustic_impedance(vp: float, rho: float) -> float:
    """Z = ρ Vp [kg·m⁻²·s⁻¹]"""
    return vp * rho


def vp_vs_ratio(vp: float, vs: float) -> float:
    """Vp/Vs, guarded against division by zero."""
    return vp / max(vs, 0.001)


def thermal_diffusivity(k: float, rho: float, cp: float = 850.0) -> float:
    """κ = k/(ρ·Cp) [m²/s]. Cp defaults to 850 J·kg⁻¹·K⁻¹ (typical sedimentary)."""
    return k / (rho * cp)


def fatigue_proxy(phi: float, delta_P: float, cycles: int = 1000) -> float:
    """Empirical fatigue indicator: φ · (ΔP/1 MPa) · ln(cycles)."""
    return phi * (delta_P / 1e6) * math.log(max(cycles, 1))


# ─── Rock Physics ────────────────────────────────────────────────────────────


def gardner_density(vp: np.ndarray, alpha: float = 310.0, beta: float = 0.25) -> np.ndarray:
    """
    Gardner's equation: ρ = α · Vp^β
    Default α=310, β=0.25 for Vp in m/s and ρ in kg/m³.
    """
    return alpha * (vp**beta)


def bellotti_velocity_from_density(rho: np.ndarray) -> np.ndarray:
    """Inverse Gardner fallback: Vp ≈ (ρ/310)^4 [m/s]."""
    return (rho / 310.0) ** 4


def faust_velocity(depth: np.ndarray, resistivity: np.ndarray, faust_k: float = 2.288, exp: float = 1.0 / 6.0) -> np.ndarray:
    """Faust's equation: Vp = k · (Z · Rt)^(1/6).

    Args:
        depth: Depth in meters (Z).
        resistivity: Formation resistivity in ohm-m (Rt).
        faust_k: Faust's proportionality constant (default 2.288; regional calibration recommended).
        exp: Exponent on the (depth * resistivity) product (default 1/6; classical value).

    Returns:
        P-wave velocity in m/s, same shape as depth.
    """
    return faust_k * (depth * resistivity) ** exp


# ─── Anisotropy (Thomsen) ──────────────────────────────────────────────────


def estimate_thomsen_parameters(vp: np.ndarray, vsh: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Empirical Thomsen parameters from Vsh.
    Epsilon ≈ 0.2·Vsh, Delta ≈ 0.1·Vsh, Gamma ≈ 0.15·Vsh.
    """
    return {
        "epsilon": 0.2 * vsh,
        "delta": 0.1 * vsh,
        "gamma": 0.15 * vsh,
    }


def apply_anisotropic_velocity_correction(
    vp_vertical: np.ndarray, theta_deg: float, epsilon: np.ndarray, delta: np.ndarray
) -> np.ndarray:
    """
    Thomsen weak-anisotropy approximation:
    Vp(θ) = Vp_vertical · (1 + δ·sin²θ·cos²θ + ε·sin⁴θ)
    """
    theta_rad = np.deg2rad(theta_deg)
    sin2 = np.sin(theta_rad) ** 2
    cos2 = np.cos(theta_rad) ** 2
    sin4 = np.sin(theta_rad) ** 4
    return vp_vertical * (1.0 + delta * sin2 * cos2 + epsilon * sin4)


# ─── Attenuation (Q-factor) ─────────────────────────────────────────────────


def spectral_decay(f_initial: float, twt_s: float, q_factor: float) -> float:
    """
    Dominant-frequency shift due to attenuation.
    Kjaer et al. (1991) approximation:
    f_decayed = f_initial / (1 + π·f_initial·t / Q)
    """
    if q_factor <= 0:
        return f_initial
    f_decayed = f_initial / (1.0 + (np.pi * f_initial * twt_s) / q_factor)
    return max(5.0, f_decayed)


def time_variant_wavelet_params(f_initial: float, time_vector: np.ndarray, q_factor: float) -> np.ndarray:
    """Vector of dominant frequencies shifting with TWT."""
    return np.array([spectral_decay(f_initial, t, q_factor) for t in time_vector])


# ─── Well-Tie Primitives ────────────────────────────────────────────────────


def impedance_array(rho: np.ndarray, vp: np.ndarray) -> np.ndarray:
    """Z = ρ·Vp with shape guard."""
    if rho.shape != vp.shape:
        raise ValueError("HOLD: Density and Velocity arrays must match in shape.")
    return rho * vp


def reflectivity_array(z: np.ndarray) -> np.ndarray:
    """R[i] = (Z[i+1] − Z[i]) / (Z[i+1] + Z[i])."""
    r = np.zeros_like(z)
    r[:-1] = (z[1:] - z[:-1]) / (z[1:] + z[:-1])
    return r


def ricker_wavelet(freq: float, dt: float, length: float = 0.2) -> np.ndarray:
    """Zero-phase Ricker wavelet."""
    t = np.arange(-length / 2, (length + dt) / 2, dt)
    y = (1.0 - 2.0 * (np.pi**2) * (freq**2) * (t**2)) * np.exp(-(np.pi**2) * (freq**2) * (t**2))
    return y


def convolve_trace(reflectivity: np.ndarray, wavelet: np.ndarray) -> np.ndarray:
    """Deterministic 1D convolution, 'same' mode."""
    return signal.convolve(reflectivity, wavelet, mode="same")


# ─── Forward Physics (all derived from a state) ─────────────────────────────


def forward_physics9(state: Physics9State) -> Dict[str, float]:
    """Compute all derived scalar properties from a canonical state."""
    K = bulk_modulus(state.vp, state.vs, state.rho)
    G = shear_modulus(state.vs, state.rho)
    E = young_modulus(K, G)
    nu = poisson_ratio(K, G)
    ai = acoustic_impedance(state.vp, state.rho)
    vpvsv = vp_vs_ratio(state.vp, state.vs)
    kappa = thermal_diffusivity(state.k, state.rho)
    fatigue = fatigue_proxy(state.phi, state.P * 0.1)

    return {
        "K_GPa": K / 1e9,
        "G_GPa": G / 1e9,
        "E_GPa": E / 1e9,
        "nu": nu,
        "ai_kg_ms2": ai,
        "vp_vs_ratio": vpvsv,
        "thermal_diff": kappa,
        "fatigue_proxy": fatigue,
        "acoustic_impedance": ai,
    }
