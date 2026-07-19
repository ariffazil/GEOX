"""
sea_level_ensemble.py — Dual-source Cenozoic sea-level with cross-validation.

Sources:
  Miller et al. 2020 (Science Advances) — backstripping + δ18O, absolute magnitude
  Haq & Ogg 2024 (GSA Today v.34) — sequence stratigraphy + biochronostrat + δ18O

Physics flow: CO₂ → Temperature → Ice → Sea Level
Time is the dimension. Every variable is time-indexed. Consistency is the test.

DITEMPA BUKAN DIBERI — Earth physics is forged, not given.
"""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

logger = logging.getLogger("geox.sea_level_ensemble")

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class SeaLevelSource(StrEnum):
    MILLER_2020 = "miller_2020"
    HAQ_OGG_2024 = "haq_ogg_2024"
    ENSEMBLE = "ensemble"


@dataclass
class SeaLevelEstimate:
    age_ma: float
    sea_level_m: float | None
    uncertainty_m: float
    source: SeaLevelSource
    source_citation: str
    agreement: str = "UNKNOWN"  # AGREE | DISAGREE | SINGLE_SOURCE
    reference_curve: str = ""
    reference_component: str = "long_term"
    reference_datum: str = "present_msl"
    notes: str = ""


@dataclass
class SequenceBoundary:
    age_ma: float
    sea_level_m: float
    amplitude: str  # minor | medium | major
    order: int  # 3, 4, 5
    stage: str
    label: str  # PgSB1, NgSB8, QSB2, etc.
    notes: str = ""


def _load_csv(filename: str) -> list[dict[str, Any]]:
    """Load a CSV file from the data directory."""
    path = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append({k: float(v) if k in ("age_Ma", "sea_level_m", "uncertainty_m") else v for k, v in row.items()})
            except (ValueError, TypeError):
                rows.append(row)
    return rows


def _interpolate(rows: list[dict], age_ma: float, age_key: str, val_key: str) -> float | None:
    """Linear interpolation from a table of (age, value) pairs."""
    if not rows:
        return None
    ages = [r[age_key] for r in rows if age_key in r]
    vals = [r[val_key] for r in rows if val_key in r]
    if not ages or not vals:
        return None

    # Exact match
    for a, v in zip(ages, vals, strict=False):
        if abs(a - age_ma) < 0.01:
            return v

    # Interpolate
    for i in range(len(ages) - 1):
        if ages[i] <= age_ma <= ages[i + 1]:
            t = (age_ma - ages[i]) / (ages[i + 1] - ages[i])
            return vals[i] + t * (vals[i + 1] - vals[i])

    # Extrapolation guard
    if age_ma < ages[0] or age_ma > ages[-1]:
        return None
    return None


def load_miller_2020(age_ma: float) -> SeaLevelEstimate:
    """Load sea level from Miller et al. 2020 (backstripping + δ18O)."""
    rows = _load_csv("sea_level_miller.csv")
    val = _interpolate(rows, age_ma, "age_Ma", "sea_level_m")
    unc = _interpolate(rows, age_ma, "age_Ma", "uncertainty_m") if rows else None

    return SeaLevelEstimate(
        age_ma=age_ma,
        sea_level_m=val,
        uncertainty_m=unc or 20.0,
        source=SeaLevelSource.MILLER_2020,
        source_citation="Miller et al. 2020 (Science Advances, CC-BY-4.0)",
        reference_curve="Miller2020",
        reference_component="long_term",
        reference_datum="present_msl",
        notes="Backstripping-derived. INTERPRETED. Uncertainty ±10-45 m depending on age.",
    )


def load_haq_ogg_2024(age_ma: float) -> SeaLevelEstimate:
    """Load sea level from Haq & Ogg 2024 (sequence stratigraphy + δ18O)."""
    rows = _load_csv("haq_ogg_2024_sb.csv")
    val = _interpolate(rows, age_ma, "age_Ma", "sea_level_m")

    # Find nearest sequence boundary for context
    nearest_sb = None
    min_dist = float("inf")
    for r in rows:
        dist = abs(r["age_Ma"] - age_ma)
        if dist < min_dist:
            min_dist = dist
            nearest_sb = r

    sb_note = ""
    if nearest_sb and min_dist < 0.5:
        sb_note = f"Nearest SB: {nearest_sb.get('label', '?')} at {nearest_sb['age_Ma']} Ma ({nearest_sb.get('amplitude', '?')})"

    return SeaLevelEstimate(
        age_ma=age_ma,
        sea_level_m=val,
        uncertainty_m=25.0,  # Haq doesn't provide explicit uncertainty
        source=SeaLevelSource.HAQ_OGG_2024,
        source_citation="Haq & Ogg 2024 (GSA Today v.34, DOI:10.1130/GSATGG593A.1)",
        reference_curve="HaqOgg2024",
        reference_component="sequence_stratigraphic",
        reference_datum="present_msl",
        notes=f"Sequence-stratigraphically derived. INTERPRETED. {sb_note}",
    )


def load_sea_level_ensemble(age_ma: float) -> SeaLevelEstimate:
    """Ensemble sea level from Miller 2020 + Haq & Ogg 2024.

    Returns mean of both sources. Agreement flag indicates whether
    the two independent methods agree within 25 m.
    """
    miller = load_miller_2020(age_ma)
    haq = load_haq_ogg_2024(age_ma)

    if miller.sea_level_m is None and haq.sea_level_m is None:
        return SeaLevelEstimate(
            age_ma=age_ma,
            sea_level_m=None,
            uncertainty_m=0.0,
            source=SeaLevelSource.ENSEMBLE,
            source_citation="Miller 2020 + Haq & Ogg 2024",
            agreement="NO_DATA",
            notes="Neither source has data at this age.",
        )

    if miller.sea_level_m is None:
        haq.source = SeaLevelSource.ENSEMBLE
        haq.agreement = "SINGLE_SOURCE"
        return haq

    if haq.sea_level_m is None:
        miller.source = SeaLevelSource.ENSEMBLE
        miller.agreement = "SINGLE_SOURCE"
        return miller

    # Both available — ensemble
    mean_val = (miller.sea_level_m + haq.sea_level_m) / 2
    envelope = abs(miller.sea_level_m - haq.sea_level_m)
    agreement = "AGREE" if envelope < 25 else "DISAGREE"

    return SeaLevelEstimate(
        age_ma=age_ma,
        sea_level_m=mean_val,
        uncertainty_m=envelope / 2,
        source=SeaLevelSource.ENSEMBLE,
        source_citation=("Ensemble: Miller et al. 2020 (Science Advances) + Haq & Ogg 2024 (GSA Today v.34)"),
        agreement=agreement,
        reference_curve="Miller2020+HaqOgg2024",
        reference_component="ensemble",
        reference_datum="present_msl",
        notes=(
            f"Ensemble mean of two independent methods. "
            f"Agreement: {agreement} (Δ={envelope:.0f} m). "
            f"Miller: {miller.sea_level_m:.0f} m, Haq: {haq.sea_level_m:.0f} m."
        ),
    )


def load_sequence_boundaries(
    age_min_ma: float = 0.0,
    age_max_ma: float = 66.0,
    min_amplitude: str | None = None,
) -> list[SequenceBoundary]:
    """Load sequence boundaries from Haq & Ogg 2024.

    Args:
        age_min_ma: Minimum age (Ma) to include.
        age_max_ma: Maximum age (Ma) to include.
        min_amplitude: Filter by minimum amplitude ("minor", "medium", "major").

    Returns:
        List of SequenceBoundary objects, sorted by age.
    """
    rows = _load_csv("haq_ogg_2024_sb.csv")
    amplitude_order = {"minor": 1, "medium": 2, "major": 3}
    min_amp = amplitude_order.get(min_amplitude, 0) if min_amplitude else 0

    boundaries = []
    for r in rows:
        age = r.get("age_Ma", 0)
        amp = r.get("amplitude", "minor")
        if age_min_ma <= age <= age_max_ma and amplitude_order.get(amp, 0) >= min_amp:
            boundaries.append(
                SequenceBoundary(
                    age_ma=age,
                    sea_level_m=r.get("sea_level_m", 0),
                    amplitude=amp,
                    order=int(r.get("order", 3)),
                    stage=r.get("stage", ""),
                    label=r.get("label", ""),
                    notes=r.get("notes", ""),
                )
            )

    return sorted(boundaries, key=lambda b: b.age_ma)


# ── Sabah-specific boundary registry ─────────────────────────────────────────

SABAH_BOUNDARIES = {
    "BMU/TCU": {"age_ma": 23.0, "description": "Onset of Dangerous Grounds collision"},
    "DRU": {"age_ma": 13.0, "description": "Uplift + slab breakoff (Morley 2024)"},
    "UIU": {"age_ma": 10.5, "description": "End of pocket basin phase"},
    "SRU": {"age_ma": 8.5, "description": "End of mud canopy phase"},
}


def load_sabah_boundary_correlation() -> list[dict]:
    """Correlate Sabah unconformities with Haq & Ogg 2024 sequence boundaries.

    Returns list of dicts with Sabah surface, nearest Haq SB, and Δage.
    """
    sabs = load_sequence_boundaries(age_min_ma=6.0, age_max_ma=25.0, min_amplitude="medium")
    correlations = []

    for name, info in SABAH_BOUNDARIES.items():
        age = info["age_ma"]
        nearest = min(sabs, key=lambda s: abs(s.age_ma - age))
        delta = abs(nearest.age_ma - age)

        correlations.append(
            {
                "sabah_surface": name,
                "sabah_age_ma": age,
                "description": info["description"],
                "nearest_haq_sb": nearest.label,
                "haq_age_ma": nearest.age_ma,
                "haq_amplitude": nearest.amplitude,
                "delta_ma": round(delta, 2),
                "correlation": "STRONG" if delta < 1.0 else "MODERATE" if delta < 2.0 else "WEAK",
            }
        )

    return correlations
