"""
geox_mcp.tools.inverse_volumetrics — Inverse Volumetric Screening Tool
═══════════════════════════════════════════════════════════════════════
Answers real exploration questions:
Given claimed GIIP / recoverable gas, what effective area is required?
What is the implied raw in-place volume across variable CO2 (0-60%)?
What are the plateau-years at a stated production rate?

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger("geox.canonical.inverse_volumetrics")


def solve_inverse_volumetrics(
    claimed_giip_tcf: float | list[float] = 5.0,
    net_pay_m: float = 600.0,
    porosity_range: tuple[float, float] | list[float] = (0.15, 0.30),
    sw_range: tuple[float, float] | list[float] = (0.15, 0.35),
    pressure_mpa_range: tuple[float, float] | list[float] = (50.0, 70.0),
    temperature_c_range: tuple[float, float] | list[float] = (140.0, 170.0),
    z_range: tuple[float, float] | list[float] = (1.05, 1.25),
    geometry_factor_range: tuple[float, float] | list[float] = (0.3, 0.6),
    co2_fraction: float = 0.0,
    recovery_factor: float = 0.70,
    recoverable_tcf: float | None = None,
    production_rate_bscfd: float | None = None,
    samples: int = 200_000,
    seed: int = 42,
    input_provenance: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Calculate required effective area and implied volumes using Monte Carlo.

    Standard conditions:
      P_std = 0.101325 MPa (14.696 psia)
      T_std = 288.15 K (60 deg F)
      1 m^3 = 35.3146667 rcf

    Args:
        claimed_giip_tcf: In-place gas volume (Tcf). Can be scalar or [min, max].
        net_pay_m: Net pay thickness in meters.
        porosity_range: [min, max] fractional porosity phi.
        sw_range: [min, max] water saturation Sw.
        pressure_mpa_range: [min, max] reservoir pressure in MPa.
        temperature_c_range: [min, max] reservoir temperature in deg C.
        z_range: [min, max] gas compressibility factor z.
        geometry_factor_range: [min, max] geometric shape factor (0.3 - 0.6).
        co2_fraction: Bulk CO2 fraction in reservoir fluid.
        recovery_factor: Gas recovery factor (default 0.70).
        recoverable_tcf: Stated recoverable volume (if different from giip * RF).
        production_rate_bscfd: Production plateau rate in Bscf/day.
        samples: Monte Carlo sample count (default 200k).
        seed: Random seed for repeatability (default 42).
        input_provenance: Dict mapping parameter names to 'OBS' or 'ASSUMPTION'.
    """
    np.random.seed(seed)
    n = int(samples)

    # Resolve ranges
    p_min, p_max = float(pressure_mpa_range[0]), float(pressure_mpa_range[1])
    t_min, t_max = float(temperature_c_range[0]), float(temperature_c_range[1])
    z_min, z_max = float(z_range[0]), float(z_range[1])
    phi_min, phi_max = float(porosity_range[0]), float(porosity_range[1])
    sw_min, sw_max = float(sw_range[0]), float(sw_range[1])
    geom_min, geom_max = float(geometry_factor_range[0]), float(geometry_factor_range[1])

    # Sample uniform distributions
    p_samples = np.random.uniform(p_min, p_max, n)
    t_c_samples = np.random.uniform(t_min, t_max, n)
    t_k_samples = t_c_samples + 273.15
    z_samples = np.random.uniform(z_min, z_max, n)
    phi_samples = np.random.uniform(phi_min, phi_max, n)
    sw_samples = np.random.uniform(sw_min, sw_max, n)
    geom_samples = np.random.uniform(geom_min, geom_max, n)

    p_std = 0.101325  # MPa
    t_std = 288.15  # K
    m3_to_rcf = 35.3146667

    # Gas expansion factor E (scf/rcf)
    e_samples = (p_samples / p_std) * (t_std / t_k_samples) / z_samples

    e_p10 = float(np.percentile(e_samples, 10))
    e_p50 = float(np.percentile(e_samples, 50))
    e_p90 = float(np.percentile(e_samples, 90))

    # Area calculation: A (m2) = GIIP (scf) / (net_pay * geom * phi * (1 - Sw) * m3_to_rcf * E)
    # A (km2) = A (m2) / 1e6
    area_results: dict[str, Any] = {}
    giip_targets = [claimed_giip_tcf] if isinstance(claimed_giip_tcf, (int, float)) else claimed_giip_tcf

    for g_tcf in giip_targets:
        giip_val = float(g_tcf)
        giip_scf = giip_val * 1e12
        denom = float(net_pay_m) * geom_samples * phi_samples * (1.0 - sw_samples) * m3_to_rcf * e_samples
        area_km2_samples = (giip_scf / denom) / 1e6

        p10_area = float(np.percentile(area_km2_samples, 10))
        p50_area = float(np.percentile(area_km2_samples, 50))
        p90_area = float(np.percentile(area_km2_samples, 90))

        area_results[f"{giip_val}_tcf"] = {
            "p10_km2": round(p10_area, 2),
            "p50_km2": round(p50_area, 2),
            "p90_km2": round(p90_area, 2),
            "mean_km2": round(float(np.mean(area_km2_samples)), 2),
        }

    # Primary area (for the first or scalar target)
    primary_giip = float(giip_targets[0])
    primary_area = area_results[f"{primary_giip}_tcf"]

    # Implied in-place volume across CO2 fraction 0% to 60%
    base_rec = recoverable_tcf if recoverable_tcf is not None else (primary_giip * float(recovery_factor))
    rf = float(recovery_factor) if recovery_factor > 0 else 0.70

    co2_sensitivity = []
    for co2_f in [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60]:
        # Required raw GIIP to yield stated recoverable hydrocarbon sales gas
        # Sales gas = Raw GIIP * (1 - co2) * RF
        # -> Raw GIIP = Sales gas / ((1 - co2) * RF)
        implied_raw = base_rec / ((1.0 - co2_f) * rf)
        co2_sensitivity.append(
            {
                "co2_fraction": round(co2_f, 2),
                "co2_percent": f"{int(round(co2_f * 100))}%",
                "implied_raw_giip_tcf": round(implied_raw, 2),
                "sales_gas_recoverable_tcf": round(base_rec, 2),
                "recovery_factor": rf,
            }
        )

    # Plateau years at given rate
    plateau_years = None
    if production_rate_bscfd and float(production_rate_bscfd) > 0:
        annual_rate_tcf = float(production_rate_bscfd) * 0.365
        plateau_years = round(base_rec / annual_rate_tcf, 1)

    # Input provenance tracking
    default_provenance = {
        "claimed_giip_tcf": "ASSUMPTION",
        "net_pay_m": "OBS",
        "porosity_range": "ASSUMPTION",
        "sw_range": "ASSUMPTION",
        "pressure_mpa_range": "OBS",
        "temperature_c_range": "OBS",
        "z_range": "ASSUMPTION",
        "geometry_factor_range": "ASSUMPTION",
        "co2_fraction": "OBS",
        "recovery_factor": "ASSUMPTION",
    }
    if input_provenance:
        default_provenance.update(input_provenance)

    return {
        "tool": "geox_prospect",
        "mode": "screen",
        "sub_mode": "inverse_volumetrics",
        "claim_tag": "ASSUMPTION",
        "epistemic_label": "ASSUMPTION",
        "forbidden_use": "not a reserve or drilling recommendation",
        "claimed_giip_tcf": primary_giip,
        "expansion_factor_scf_per_rcf": {
            "p10": round(e_p10, 1),
            "p50": round(e_p50, 1),
            "p90": round(e_p90, 1),
        },
        "required_effective_area_km2": primary_area,
        "all_targets_area_km2": area_results,
        "co2_sensitivity_table": co2_sensitivity,
        "recoverable_tcf": round(base_rec, 2),
        "plateau_years": plateau_years,
        "production_rate_bscfd": production_rate_bscfd,
        "parameters_used": {
            "net_pay_m": net_pay_m,
            "porosity_range": [phi_min, phi_max],
            "sw_range": [sw_min, sw_max],
            "pressure_mpa_range": [p_min, p_max],
            "temperature_c_range": [t_min, t_max],
            "z_range": [z_min, z_max],
            "geometry_factor_range": [geom_min, geom_max],
            "co2_fraction": co2_fraction,
            "recovery_factor": rf,
            "samples": n,
            "seed": seed,
        },
        "input_provenance": default_provenance,
    }
