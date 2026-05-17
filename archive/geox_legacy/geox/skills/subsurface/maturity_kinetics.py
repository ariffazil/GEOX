"""
GEOX Legacy Substrate: Kinetic Maturity Logic (Easy%Ro)
Surgically extracted from geox/core/basin_charge.py
"""
import math
from typing import Any

def compute_tti(burial_history: list[dict[str, float]]) -> float:
    """
    Compute TTI (Time-Temperature Index) using Lopatin's method.
    phi = duration * 2^((T-100)/10)
    """
    tti = 0.0
    for step in burial_history:
        temp_c = step.get("temperature_c", 0.0)
        duration_ma = step.get("duration_ma", 0.0)
        tti += duration_ma * (2.0 ** ((temp_c - 100.0) / 10.0))
    return max(tti, 0.0)

def compute_easy_ro(tti: float) -> float:
    """
    Compute Vitrinite Reflectance (Easy%Ro) from TTI.
    Simplified formula based on Sweeney & Burnham (1990) proxy.
    """
    if tti <= 0.0:
        return 0.2
    # Ro = 0.42 + 0.23 * log10(TTI + 1)
    return max(0.2, min(3.5, 0.42 + 0.23 * math.log10(tti + 1.0)))

def get_charge_age(burial_history: list[dict[str, float]], threshold_c: float = 90.0) -> float:
    """Age at which source rock reached thermal expulsion threshold."""
    ages = [step.get("age_ma", 0.0) for step in burial_history if step.get("temperature_c", 0) >= threshold_c]
    return max(ages) if ages else 0.0
