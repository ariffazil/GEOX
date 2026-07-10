"""
geox_thermal_maturity_history — Thermal Maturity History MCP Tool
═════════════════════════════════════════════════════════════════
Model burial + heat flow + maturity through time.

Uses EasyRo (Sweeney & Burnham 1990) + TTI (Lopatin 1971).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any


async def geox_thermal_maturity_history(
    well_ref: str,
    burial_history: dict[str, Any],
    heat_flow_history: dict[str, Any] | None = None,
    surface_temp_c: float = 20.0,
    geothermal_gradient_c_km: float = 30.0,
    time_step_myr: float = 1.0,
) -> dict[str, Any]:
    """Model burial + heat flow + maturity through time.

    Computes EasyRo (Sweeney & Burnham 1990) and TTI (Lopatin 1971)
    from burial history and thermal parameters.

    Args:
        well_ref: Well identifier
        burial_history: {ages_ma: [...], depths_m: [...]} — burial path
        heat_flow_history: {ages_ma: [...], heat_flow_mw_m2: [...]} — optional heat flow
        surface_temp_c: Surface temperature (default 20°C)
        geothermal_gradient_c_km: Geothermal gradient (default 30°C/km)
        time_step_myr: Time step for computation (default 1 Myr)

    Returns:
        MaturityResult with easyro_final, tti_final, hydrocarbon windows,
        loading pulse detection, and provenance.

    DER — Derived from kinetic models. Not a direct measurement.
    """
    from geox_core.engines.basin.thermal_maturity import (
        ThermalHistory,
        burial_maturity_history,
        temperature_at_depth,
    )

    # Build thermal history
    ages = burial_history.get("ages_ma", [])
    depths = burial_history.get("depths_m", [])

    if len(ages) != len(depths) or len(ages) < 2:
        return {
            "success": False,
            "error": "burial_history must have matching ages_ma and depths_m arrays (≥2 points)",
            "recoverable": True,
        }

    # Compute temperatures from depths
    hf_ages = heat_flow_history.get("ages_ma", []) if heat_flow_history else []
    hf_values = heat_flow_history.get("heat_flow_mw_m2", []) if heat_flow_history else []

    temperatures: list[float] = []
    heat_flows: list[float] = []
    gradients: list[float] = []

    for i, (age, depth) in enumerate(zip(ages, depths)):
        # Interpolate heat flow if provided
        if hf_ages and hf_values:
            hf = _interpolate(age, hf_ages, hf_values)
            # Convert heat flow to gradient: q = k * dT/dz
            # k ~ 2.5 W/(m·K) for sedimentary rocks
            k = 2.5
            grad = hf / k  # °C/km (hf in mW/m² = 10⁻³ W/m²)
            # Actually: q (mW/m²) = k (W/m·K) * dT/dz (°C/km) * 1000 (m/km) / 1000 (mW/W)
            # So: dT/dz = q / k (°C/km)
            grad = hf / k
        else:
            grad = geothermal_gradient_c_km
            hf = grad * 2.5  # approximate

        temp = temperature_at_depth(depth, surface_temp_c, grad)
        temperatures.append(temp)
        heat_flows.append(hf)
        gradients.append(grad)

    thermal = ThermalHistory(
        name=well_ref,
        ages_ma=ages,
        temperatures_c=temperatures,
        depths_m=depths,
        heat_flow_mw_m2=heat_flows,
        geothermal_gradient_c_km=gradients,
    )

    # Run maturity computation
    result = burial_maturity_history(thermal, time_step_myr=time_step_myr)

    return {
        "success": True,
        "well_ref": well_ref,
        "easyro_final": result.easyro_final,
        "tti_final": result.tti_final,
        "ro_from_tti": result.ro_from_tti,
        "easyro_history": [{"age_ma": age, "easyro": ro} for age, ro in result.easyro_history],
        "tti_history": [{"age_ma": age, "tti": tti} for age, tti in result.tti_history],
        "temperature_history": [{"age_ma": age, "temp_c": temp} for age, temp in result.temperature_history],
        "depth_history": [{"age_ma": age, "depth_m": depth} for age, depth in result.depth_history],
        "hydrocarbon_windows": {
            "oil_window_entered_ma": result.oil_window_entered_ma,
            "oil_window_exited_ma": result.oil_window_exited_ma,
            "gas_window_entered_ma": result.gas_window_entered_ma,
            "gas_window_exited_ma": result.gas_window_exited_ma,
            "overmature_ma": result.overmature_ma,
        },
        "loading_pulse": {
            "age_ma": result.loading_pulse_age_ma,
            "rate_m_myr": result.loading_pulse_rate_m_myr,
        },
        "diagnostics": result.diagnostics,
        "provenance": result.provenance,
        "epistemic": {
            "truth_class": "DERIVED",
            "evidence_tag": "DER",
            "not_fact_because": [
                "EasyRo uses simplified 20-reaction kinetic model",
                "TTI is empirical correlation, not physics",
                "Geothermal gradient may vary through time",
                "Burial history depends on decompaction accuracy",
                "Heat flow history is often poorly constrained",
            ],
        },
    }


def _interpolate(x: float, x_data: list[float], y_data: list[float]) -> float:
    """Linear interpolation."""
    if not x_data or not y_data:
        return 0.0
    if x >= max(x_data):
        return y_data[x_data.index(max(x_data))]
    if x <= min(x_data):
        return y_data[x_data.index(min(x_data))]
    for i in range(len(x_data) - 1):
        if x_data[i] >= x >= x_data[i + 1]:
            frac = (x_data[i] - x) / (x_data[i] - x_data[i + 1])
            return y_data[i] + frac * (y_data[i + 1] - y_data[i])
    return y_data[-1]
