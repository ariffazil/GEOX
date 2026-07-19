"""
geox_core.physics.thermal_history — Cooling Path Calculator

Computes cooling rates, exhumation rates, and thermal history curves
from thermochronological data (U-Pb, Ar/Ar, fission track, (U-Th)/He).

Eureka #4: Cooling rate 360°C/Myr = tectonic unroofing (not erosional).
Normal erosional exhumation: 1–10°C/Myr. Tectonic unroofing: >100°C/Myr.

DITEMPA BUKAN DIBERI — Physics first, AI second.
F2 TRUTH: all values labeled OBS/DER.
F7 HUMILITY: confidence capped at 0.90.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ── Canonical Closure Temperatures ──────────────────────────────────────────
# Source: Reiners & Brandon (2006), Farley (2002), Hurford (1986)

CLOSURE_TEMPS: dict[str, float] = {
    "zircon_upb": 900.0,  # °C — Zircon U-Pb (Cherniak & Watson, 2001)
    "biotite_arar": 350.0,  # °C — Biotite 40Ar/39Ar (McDougall & Harrison, 1999)
    "zft": 240.0,  # °C — Zircon Fission Track (Tagami, 2005)
    "muscovite_arar": 400.0,  # °C — Muscovite 40Ar/39Ar
    "kfeldspar_arar": 250.0,  # °C — K-Feldspar 40Ar/39Ar (multi-domain)
    "apatite_ft": 110.0,  # °C — Apatite Fission Track (Ketcham et al., 1999)
    "ahe": 70.0,  # °C — Apatite (U-Th)/He (Farley, 2002)
    "zhe": 180.0,  # °C — Zircon (U-Th)/He (Reiners, 2005)
}

# Standard geothermal gradient (continental average)
DEFAULT_GEOTHERMAL_GRADIENT_C_PER_KM = 25.0  # °C/km


@dataclass
class ThermochronPoint:
    """A single thermochronological measurement."""

    system: str  # e.g., "zircon_upb", "ahe"
    closure_temp_C: float  # °C
    age_ma: float  # Ma (central age)
    age_uncertainty_ma: float | None = None  # ± Ma (1σ)
    label: str = "DER"  # Epistemic label
    source: str = ""  # Literature reference


@dataclass
class CoolingPathSegment:
    """A segment of the cooling path between two thermochronological systems."""

    from_system: str
    to_system: str
    from_age_ma: float
    to_age_ma: float
    from_temp_C: float
    to_temp_C: float
    delta_T: float  # °C
    delta_t: float  # Myr
    cooling_rate_C_per_Myr: float  # °C/Myr
    exhumation_rate_mm_yr: float  # mm/yr
    is_tectonic_unroofing: bool  # cooling_rate > 100°C/Myr
    label: str = "DER"


@dataclass
class ThermalHistoryResult:
    """Complete thermal history analysis."""

    points: list[ThermochronPoint]
    segments: list[CoolingPathSegment]
    mean_cooling_rate_C_per_Myr: float
    max_cooling_rate_C_per_Myr: float
    mean_exhumation_rate_mm_yr: float
    max_exhumation_rate_mm_yr: float
    is_tectonic_unroofing: bool
    total_cooling_C: float
    total_time_Myr: float
    geothermal_gradient_C_per_km: float
    interpretation: str
    confidence: float  # 0.0–0.90 (F7 HUMILITY)
    label: str = "DER"

    @property
    def cooling_path_summary(self) -> str:
        """Human-readable cooling path summary."""
        lines = []
        for seg in self.segments:
            flag = "⚡ TECTONIC" if seg.is_tectonic_unroofing else ""
            lines.append(
                f"  {seg.from_system} → {seg.to_system}: "
                f"{seg.from_temp_C:.0f}°C → {seg.to_temp_C:.0f}°C "
                f"over {seg.delta_t:.2f} Myr = "
                f"{seg.cooling_rate_C_per_Myr:.1f} °C/Myr "
                f"({seg.exhumation_rate_mm_yr:.1f} mm/yr) {flag}"
            )
        return "\n".join(lines)


def compute_cooling_path(
    points: list[ThermochronPoint],
    geothermal_gradient_C_per_km: float = DEFAULT_GEOTHERMAL_GRADIENT_C_PER_KM,
) -> ThermalHistoryResult:
    """
    Compute cooling path from thermochronological data.

    Args:
        points: List of ThermochronPoint (system, closure temp, age)
        geothermal_gradient: °C/km (default 25°C/km = continental average)

    Returns:
        ThermalHistoryResult with cooling rates, exhumation rates, interpretation

    Raises:
        ValueError: if fewer than 2 points provided
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 thermochronological points")

    # Sort by age (oldest first = highest closure temp)
    sorted_points = sorted(points, key=lambda p: p.age_ma, reverse=True)

    # Compute segments
    segments: list[CoolingPathSegment] = []
    for i in range(len(sorted_points) - 1):
        p1 = sorted_points[i]  # Older (hotter)
        p2 = sorted_points[i + 1]  # Younger (cooler)

        delta_T = p1.closure_temp_C - p2.closure_temp_C
        delta_t = p1.age_ma - p2.age_ma

        if delta_t <= 0:
            # Overlapping ages — skip segment
            continue

        cooling_rate = delta_T / delta_t  # °C/Myr
        exhumation_rate = cooling_rate / geothermal_gradient_C_per_km  # km/Myr
        exhumation_rate_mm = exhumation_rate * 1000.0  # mm/yr

        seg = CoolingPathSegment(
            from_system=p1.system,
            to_system=p2.system,
            from_age_ma=p1.age_ma,
            to_age_ma=p2.age_ma,
            from_temp_C=p1.closure_temp_C,
            to_temp_C=p2.closure_temp_C,
            delta_T=delta_T,
            delta_t=delta_t,
            cooling_rate_C_per_Myr=cooling_rate,
            exhumation_rate_mm_yr=exhumation_rate_mm,
            is_tectonic_unroofing=cooling_rate > 100.0,
        )
        segments.append(seg)

    # Aggregate statistics
    cooling_rates = [s.cooling_rate_C_per_Myr for s in segments]
    exhumation_rates = [s.exhumation_rate_mm_yr for s in segments]

    mean_cooling = float(np.mean(cooling_rates))
    max_cooling = float(np.max(cooling_rates))
    mean_exhumation = float(np.mean(exhumation_rates))
    max_exhumation = float(np.max(exhumation_rates))

    total_cooling = sorted_points[0].closure_temp_C - sorted_points[-1].closure_temp_C
    total_time = sorted_points[0].age_ma - sorted_points[-1].age_ma

    is_tectonic = max_cooling > 100.0

    # Interpretation
    if max_cooling > 200.0:
        interpretation = (
            f"TECTONIC UNROOFING: Maximum cooling rate {max_cooling:.0f} °C/Myr "
            f"({max_exhumation:.1f} mm/yr) far exceeds erosional exhumation "
            f"(1–10 °C/Myr). This records rapid crustal thinning, likely driven by "
            f"slab break-off, delamination, or tectonic exhumation."
        )
    elif max_cooling > 50.0:
        interpretation = (
            f"RAPID EXHUMATION: Maximum cooling rate {max_cooling:.0f} °C/Myr "
            f"({max_exhumation:.1f} mm/yr) suggests tectonically-assisted exhumation. "
            f"May record post-orogenic collapse or rapid erosion."
        )
    elif max_cooling > 10.0:
        interpretation = (
            f"MODERATE EXHUMATION: Cooling rate {max_cooling:.0f} °C/Myr "
            f"({max_exhumation:.1f} mm/yr) consistent with erosional exhumation "
            f"in an uplifting orogen."
        )
    else:
        interpretation = (
            f"SLOW EXHUMATION: Cooling rate {max_cooling:.0f} °C/Myr "
            f"({max_exhumation:.1f} mm/yr) typical of stable continental interior "
            f"or slow erosional unroofing."
        )

    # Confidence: depends on number of points and age consistency
    n_points = len(sorted_points)
    age_spread = total_time
    if n_points >= 4 and age_spread >= 1.0:
        confidence = 0.85
    elif n_points >= 3 and age_spread >= 0.5:
        confidence = 0.75
    elif n_points >= 2:
        confidence = 0.65
    else:
        confidence = 0.50

    # F7 HUMILITY: cap at 0.90
    confidence = min(confidence, 0.90)

    return ThermalHistoryResult(
        points=sorted_points,
        segments=segments,
        mean_cooling_rate_C_per_Myr=mean_cooling,
        max_cooling_rate_C_per_Myr=max_cooling,
        mean_exhumation_rate_mm_yr=mean_exhumation,
        max_exhumation_rate_mm_yr=max_exhumation,
        is_tectonic_unroofing=is_tectonic,
        total_cooling_C=total_cooling,
        total_time_Myr=total_time,
        geothermal_gradient_C_per_km=geothermal_gradient_C_per_km,
        interpretation=interpretation,
        confidence=confidence,
    )


# ── Sabah-Specific: Kinabalu Granite Cooling Path ──────────────────────────


def kinabalu_cooling_path() -> ThermalHistoryResult:
    """
    Compute the Kinabalu granite cooling path from Cottam et al. (2013).

    This is the Eureka #4 calculation:
    - Zircon U-Pb: 900°C at 7.8 Ma
    - Biotite Ar/Ar: 350°C at 7.63 Ma
    - Zircon Fission Track: 240°C at 6.6 Ma
    - Apatite He: 70°C at 5.5 Ma
    - Cooling rate: ~360°C/Myr = TECTONIC UNROOFING

    Returns:
        ThermalHistoryResult with Kinabalu-specific interpretation
    """
    points = [
        ThermochronPoint(
            system="zircon_upb",
            closure_temp_C=900.0,
            age_ma=7.85,
            age_uncertainty_ma=0.08,
            source="Cottam et al. 2010 (JGS)",
        ),
        ThermochronPoint(
            system="biotite_arar",
            closure_temp_C=350.0,
            age_ma=7.63,
            age_uncertainty_ma=0.15,
            source="Cottam et al. 2013 (JGS)",
        ),
        ThermochronPoint(
            system="zft",
            closure_temp_C=240.0,
            age_ma=6.6,
            age_uncertainty_ma=0.4,
            source="Cottam et al. 2013 (JGS)",
        ),
        ThermochronPoint(
            system="ahe",
            closure_temp_C=70.0,
            age_ma=5.5,
            age_uncertainty_ma=0.3,
            source="Cottam et al. 2013 (JGS)",
        ),
    ]

    result = compute_cooling_path(points)

    # Override interpretation with Sabah-specific context
    result.interpretation = (
        f"KINABALU TECTONIC UNROOFING: Cooling rate {result.max_cooling_rate_C_per_Myr:.0f} °C/Myr "
        f"({result.max_exhumation_rate_mm_yr:.1f} mm/yr) confirms rapid crustal thinning. "
        f"This is NOT related to the Sabah orogeny (terminated ~16 Ma). "
        f"Driver: Sulu Arc rollback → lithospheric delamination or slab break-off. "
        f"The granite is a post-collisional tectonic wound, not an orogenic crown."
    )

    return result


# ── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("GEOX Thermal History Calculator — Cooling Path Analysis")
    print("=" * 70)

    # Kinabalu example
    result = kinabalu_cooling_path()

    print(f"\n{'─' * 70}")
    print("KINABALU GRANITE COOLING PATH (Cottam et al. 2013)")
    print(f"{'─' * 70}")
    print(f"Points: {len(result.points)}")
    for p in result.points:
        print(f"  {p.system:20s} | {p.closure_temp_C:6.0f}°C | {p.age_ma:6.2f} Ma ± {p.age_uncertainty_ma or 0:.2f}")
    print("\nCooling Path Segments:")
    print(result.cooling_path_summary)
    print("\nSummary:")
    print(f"  Mean cooling rate:    {result.mean_cooling_rate_C_per_Myr:.1f} °C/Myr")
    print(f"  Max cooling rate:     {result.max_cooling_rate_C_per_Myr:.1f} °C/Myr")
    print(f"  Mean exhumation:      {result.mean_exhumation_rate_mm_yr:.1f} mm/yr")
    print(f"  Max exhumation:       {result.max_exhumation_rate_mm_yr:.1f} mm/yr")
    print(f"  Total cooling:        {result.total_cooling_C:.0f}°C over {result.total_time_Myr:.2f} Myr")
    print(f"  Tectonic unroofing:   {'YES' if result.is_tectonic_unroofing else 'NO'}")
    print(f"  Confidence:           {result.confidence:.2f}")
    print("\nInterpretation:")
    print(f"  {result.interpretation}")
    print(f"\n{'=' * 70}")
    print("DITEMPA BUKAN DIBERI — Physics first, AI second.")
