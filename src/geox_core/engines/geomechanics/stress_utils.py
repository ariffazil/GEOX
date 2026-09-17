"""Stress utility functions for geomechanical QC.

Pure functions — no side effects, no external dependencies.
"""

from __future__ import annotations

import math


def classify_fault_orientation(
    fault_azimuth_deg: float,
    stress_regime: str,
    sigma1_azimuth_deg: float | None = None,
) -> dict[str, object]:
    """Classify fault orientation relative to stress regime.

    Returns consistency score and classification.
    Does NOT determine fault age — that requires relational evidence.

    TECT-004: Fault azimuth is evidence, not age.
    """
    # Expected orientations for each stress regime
    regime_expectations = {
        "NORMAL": {"optimal_dip_deg": 60, "preferred_azimuth_relation": "perpendicular_to_sigma1"},
        "STRIKE_SLIP": {"optimal_dip_deg": 90, "preferred_azimuth_relation": "30_to_60_from_sigma1"},
        "REVERSE": {"optimal_dip_deg": 30, "preferred_azimuth_relation": "perpendicular_to_sigma1"},
        "TRANSTENSIONAL": {"optimal_dip_deg": 60, "preferred_azimuth_relation": "15_to_45_from_sigma1"},
        "TRANSPRESSIONAL": {"optimal_dip_deg": 45, "preferred_azimuth_relation": "15_to_45_from_sigma1"},
    }

    regime = stress_regime.upper()
    expectation = regime_expectations.get(regime)
    if expectation is None:
        return {
            "consistent": False,
            "consistency_score": 0.0,
            "reason": f"Unknown stress regime: {stress_regime}",
        }

    if sigma1_azimuth_deg is None:
        return {
            "consistent": False,
            "consistency_score": 0.0,
            "reason": "σ1 azimuth not provided — cannot evaluate orientation consistency",
        }

    # Angular difference between fault azimuth and σ1
    diff = abs(fault_azimuth_deg - sigma1_azimuth_deg) % 180
    if diff > 90:
        diff = 180 - diff

    relation = expectation["preferred_azimuth_relation"]

    # Scoring based on regime
    if relation == "perpendicular_to_sigma1":
        # Normal/reverse: fault should be ~perpendicular to σ1
        # Optimal: 70-90° from σ1
        if 70 <= diff <= 90:
            score = 1.0
        elif 60 <= diff < 70:
            score = 0.7
        elif 45 <= diff < 60:
            score = 0.4
        else:
            score = 0.1
    elif relation == "30_to_60_from_sigma1":
        # Strike-slip: fault should be30-60° from σ1
        if 25 <= diff <= 65:
            score = 1.0
        elif 15 <= diff < 25 or 65 < diff <= 75:
            score = 0.7
        else:
            score = 0.3
    elif relation == "15_to_45_from_sigma1":
        # Transpressional/transtensional
        if 10 <= diff <= 50:
            score = 1.0
        elif 0 <= diff < 10 or 50 < diff <= 70:
            score = 0.6
        else:
            score = 0.2
    else:
        score = 0.0

    return {
        "consistent": score >= 0.7,
        "consistency_score": score,
        "fault_azimuth_deg": fault_azimuth_deg,
        "sigma1_azimuth_deg": sigma1_azimuth_deg,
        "angular_difference_deg": round(diff, 1),
        "stress_regime": regime,
        "preferred_relation": relation,
        "note": (
            "Consistency score ≥ 0.7 means the orientation is compatible "
            "with the stress regime. It does NOT prove fault age."
        ),
    }


def compute_slip_tendency(
    fault_strike_deg: float,
    fault_dip_deg: float,
    sigma1_deg: tuple[float, float],  # (azimuth, plunge)
    sigma3_deg: tuple[float, float],  # (azimuth, plunge)
    sigma2_deg: tuple[float, float] | None = None,
) -> float:
    """Compute slip tendency (τ/σn) on a fault plane.

    Simplified version — full 3D tensor decomposition needed for
    production use.
    """
    # This is a placeholder for the full tensor decomposition
    # The actual implementation requires proper3D stress rotation
    # onto the fault plane normal
    raise NotImplementedError(
        "Full3D slip tendency requires tensor decomposition. "
        "Use check_reactivation_viability() for the simplified version."
    )
