"""
physics.py — EGS Physics Hooks
=================================
GEOX EGS: Physical property computations, fluid substitution, rock physics.

DITEMPA BUKAN DIBERI — Forged, Not Given.

NOTE: These are structural hooks. Actual physical computations should
leverage existing GEOX physics engines (bruges, geox.core.physics9, etc.).
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from geox.egs.models.uncertainty import IntervalUncertainty, UncertainValue


# ═══════════════════════════════════════════════════════════════════════════════
# Fluid Properties (Batzle-Wang approximations)
# ═══════════════════════════════════════════════════════════════════════════════


def brine_density(temperature_c: float, salinity_ppm: float, pressure_mpa: float) -> float:
    """Brine density using Batzle-Wang approximation. Returns g/cc."""
    rho_w = 1.0 + 1e-6 * (
        -80 * temperature_c
        - 3.3 * temperature_c**2
        + 0.00175 * temperature_c**3
        + 489 * pressure_mpa
        - 2 * temperature_c * pressure_mpa
        + 0.016 * temperature_c**2 * pressure_mpa
        - 1.3e-5 * temperature_c**3 * pressure_mpa
        - 0.333 * pressure_mpa**2
        - 0.002 * temperature_c * pressure_mpa**2
    )
    # Salinity correction
    s = salinity_ppm / 1e6
    rho_b = rho_w + s * (
        0.668
        + 0.44 * s
        + 1e-6
        * (
            300 * pressure_mpa
            - 2400 * pressure_mpa * s
            + temperature_c * (80 + 3 * temperature_c - 3300 * s - 13 * pressure_mpa + 47 * pressure_mpa * s)
        )
    )
    return rho_b


def oil_density(api_gravity: float, gas_oil_ratio: float, temperature_c: float, pressure_mpa: float) -> float:
    """Oil density using Batzle-Wang. Returns g/cc."""
    # Dead oil density at STP
    rho_o_stp = 141.5 / (api_gravity + 131.5)
    # Simplified GOR correction
    rho_o = rho_o_stp + 0.001 * gas_oil_ratio * (0.5 - 0.01 * temperature_c)
    # Pressure correction
    rho_o += 0.0001 * (pressure_mpa - 0.1)
    return max(rho_o, 0.1)


def gas_density(temperature_c: float, pressure_mpa: float, gas_gravity: float = 0.6) -> float:
    """Gas density using Batzle-Wang approximation. Returns g/cc.

    Simplified implementation using the real gas law with Papay Z-factor.
    Reference: Batzle & Wang (1992), Geophysics.
    """
    t_k = temperature_c + 273.15
    p_mpa = pressure_mpa

    # Pseudo-critical properties (gas_gravity correlation)
    t_pc = 94.0 + 170.8 * gas_gravity  # K, Sutton correlation
    p_pc = 4.64 + 0.916 * gas_gravity - 0.0137 * gas_gravity**2  # MPa

    # Reduced properties
    t_pr = t_k / t_pc
    p_pr = p_mpa / p_pc

    # Papay Z-factor (simplified)
    z = 1.0 - (3.53 * p_pr / (10 ** (0.9813 * t_pr))) + (0.274 * p_pr**2 / (10 ** (0.8157 * t_pr)))
    z = max(z, 0.2)  # prevent unphysical values

    # Gas density: rho = p * M / (Z * R * T)
    # p in Pa, M in kg/mol, R in J/(mol*K), T in K => result in kg/m^3
    # 1 g/cc = 1000 kg/m^3
    p_pa = p_mpa * 1e6  # MPa -> Pa
    m_kg_per_mol = gas_gravity * 28.97 / 1000  # g/mol -> kg/mol
    r = 8.314462  # J/(mol*K)
    rho_kg_m3 = (p_pa * m_kg_per_mol) / (z * r * t_k)
    rho_g_cc = rho_kg_m3 / 1000  # kg/m^3 -> g/cc
    return max(rho_g_cc, 0.001)


# ═══════════════════════════════════════════════════════════════════════════════
# Rock Physics Transform Hooks
# ═══════════════════════════════════════════════════════════════════════════════


def gardner_vp_to_rho(vp_m_s: float) -> float:
    """Gardner's equation: rho = 0.31 * Vp^0.25. Returns g/cc."""
    return 0.31 * (vp_m_s**0.25)


def castagna_mudrock_vp_to_vs(vp_m_s: float) -> float:
    """Castagna's mudrock line: Vs = (Vp - 1360) / 1.16. Returns m/s."""
    vs = (vp_m_s - 1360.0) / 1.16
    return max(vs, 1.0)


def acoustic_impedance(vp_m_s: float, rho_g_cc: float) -> float:
    """Acoustic impedance: AI = Vp * rho. Returns (m/s)*(g/cc)."""
    return vp_m_s * rho_g_cc


def elastic_impedance(vp_m_s: float, vs_m_s: float, rho_g_cc: float, chi: float = 0.3) -> float:
    """Elastic impedance (Connolly 1999). Returns (m/s)*(g/cc)."""
    k = (vs_m_s / vp_m_s) ** 2 if vp_m_s > 0 else 0
    ei = vp_m_s * rho_g_cc * ((vp_m_s ** (1 + chi)) * (vs_m_s ** (-8 * k * chi)) * (rho_g_cc ** (1 - 4 * k * chi)))
    return ei


# ═══════════════════════════════════════════════════════════════════════════════
# Velocity Bounds (Voigt-Reuss)
# ═══════════════════════════════════════════════════════════════════════════════


def voigt_reuss_hill(vp_mineral: float, vp_fluid: float, phi: float, rho_mineral: float, rho_fluid: float) -> dict[str, float]:
    """Voigt-Reuss-Hill average for velocity estimation."""
    # Voigt upper bound
    v_voigt = (1 - phi) * vp_mineral + phi * vp_fluid
    # Reuss lower bound
    v_reuss = 1.0 / ((1 - phi) / vp_mineral + phi / vp_fluid)
    # Hill average
    v_hill = (v_voigt + v_reuss) / 2.0

    # Density
    rho_bulk = (1 - phi) * rho_mineral + phi * rho_fluid

    return {
        "vp_voigt_m_s": v_voigt,
        "vp_reuss_m_s": v_reuss,
        "vp_hill_m_s": v_hill,
        "rho_bulk_g_cc": rho_bulk,
    }
