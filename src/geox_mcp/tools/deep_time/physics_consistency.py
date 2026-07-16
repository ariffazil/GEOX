"""
physics_consistency.py — Earth system physics flow consistency gate.

CO₂ → Temperature → Ice → Sea Level

Every variable at a given age must be mutually consistent.
Inconsistency = calibration error or missing data.

Time is the dimension. Physics is the constraint.

DITEMPA BUKAN DIBERI — Earth physics is forged, not given.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("geox.physics_consistency")


@dataclass
class ConsistencyResult:
    age_ma: float
    consistent: bool
    warnings: list[str]
    details: dict[str, float | str | None]


def check_physics_consistency(
    age_ma: float,
    co2_ppm: float | None = None,
    temp_anomaly_c: float | None = None,
    ice_extent: str | None = None,
    sea_level_m: float | None = None,
) -> ConsistencyResult:
    """Check that CO₂, temperature, ice, and sea level are mutually consistent.

    Physics rules:
      1. High CO₂ (>500 ppm) → warm (>3°C) → low ice → high sea level (>0 m)
      2. Low CO₂ (<300 ppm) → cool (<2°C) → has ice → lower sea level
      3. Ice-free → sea level should be higher than glacial state
      4. Post-MMCT (14-2.58 Ma) → should have Antarctic ice
      5. Pre-34 Ma → should be ice-free

    Returns ConsistencyResult with warnings for any violations.
    """
    warnings = []
    ice_has = _ice_has_ice(ice_extent) if ice_extent else None

    # Rule 1: High CO₂ + expanded ice = inconsistent
    if co2_ppm is not None and co2_ppm > 500 and ice_has is True:
        warnings.append(f"HIGH CO₂ ({co2_ppm:.0f} ppm) with EXPANDED ICE — high CO₂ should reduce ice. Verify calibration.")

    # Rule 2: Low CO₂ + ice-free = inconsistent (for post-34 Ma)
    if co2_ppm is not None and co2_ppm < 300 and ice_has is False and age_ma < 34:
        warnings.append(
            f"LOW CO₂ ({co2_ppm:.0f} ppm) with ICE-FREE state at {age_ma} Ma — low CO₂ should support ice. Verify calibration."
        )

    # Rule 3: Warm + high ice = inconsistent
    if temp_anomaly_c is not None and temp_anomaly_c > 5 and ice_has is True:
        # Check if it's Mi-1 (transient expansion during warm period)
        if not (22 <= age_ma <= 24):  # Mi-1 exception
            warnings.append(
                f"WARM ({temp_anomaly_c:+.1f}°C) with EXPANDED ICE at {age_ma} Ma — warm world should have less ice. Verify."
            )

    # Rule 4: Cold + ice-free = inconsistent (post-34 Ma)
    if temp_anomaly_c is not None and temp_anomaly_c < 0 and ice_has is False and age_ma < 34:
        warnings.append(
            f"COOL ({temp_anomaly_c:+.1f}°C) with ICE-FREE at {age_ma} Ma — cool world should have ice (post Oi-1). Verify."
        )

    # Rule 5: Ice-free + low sea level = inconsistent
    if ice_has is False and sea_level_m is not None and sea_level_m < 0:
        warnings.append(
            f"ICE-FREE with LOW sea level ({sea_level_m:.0f} m) at {age_ma} Ma — "
            f"ice-free world should have high sea level. Verify."
        )

    # Rule 6: Post-MMCT should have ice
    if 2.58 <= age_ma < 14.0 and ice_has is False:
        warnings.append(
            f"ICE-FREE at {age_ma} Ma — post-MMCT should have quasi-permanent EAIS. CRITICAL calibration error likely."
        )

    # Rule 7: Pre-34 Ma should be ice-free (except brief Oi-1)
    if age_ma > 34.5 and ice_has is True:
        warnings.append(f"EXPANDED ICE at {age_ma} Ma — pre-Oi-1 should be ice-free. Verify calibration.")

    return ConsistencyResult(
        age_ma=age_ma,
        consistent=len(warnings) == 0,
        warnings=warnings,
        details={
            "co2_ppm": co2_ppm,
            "temp_anomaly_c": temp_anomaly_c,
            "ice_extent": ice_extent,
            "sea_level_m": sea_level_m,
            "ice_has_ice": ice_has,
        },
    )


def _ice_has_ice(ice_str: str | None) -> bool | None:
    """True if ice descriptor indicates presence of significant ice."""
    if ice_str is None:
        return None
    s = ice_str.lower()
    if "ice-free" in s or "no antarctic" in s or "no polar ice" in s:
        return False
    positive = [
        "glaciation",
        "ice sheet",
        "eaismi",
        "glacial",
        "ice age",
        "quasi-permanent",
        "mi-1",
        "oi-1",
        "snowball",
        "dynamic",
        "polar",
        "expansion",
        "reduced antarctic",
    ]
    return any(p in s for p in positive)


def format_consistency_report(result: ConsistencyResult) -> str:
    """Format a consistency check result as a human-readable string."""
    if result.consistent:
        return f"✅ PHYSICS CONSISTENT at {result.age_ma} Ma"
    lines = [f"⚠️ PHYSICS INCONSISTENT at {result.age_ma} Ma:"]
    for w in result.warnings:
        lines.append(f"  • {w}")
    return "\n".join(lines)
