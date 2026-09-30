"""Geomechanical QC checks for seismic fault interpretations.

When a fault is interpreted from seismic, these checks evaluate whether
the interpretation is geomechanically consistent with the proposed
stress regime, rock properties, and tectonic context.

A fault observed on seismic is an INTERPRETATION (F7).
Its geomechanical viability is a PHYSICS constraint (F0/F1).

Forward: Stress → Geomechanics → Fault
Inverse: Fault → Infer stress conditions → Validate against independent evidence

Forged: 2026-09-14
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class QCVerdict(StrEnum):
    """Geomechanical QC verdict."""

    CONSISTENT = "CONSISTENT"  # Interpretation is geomechanically viable
    INCONSISTENT = "INCONSISTENT"  # Interpretation violates geomechanical constraints
    UNDERCONSTRAINED = "UNDERCONSTRAINED"  # Insufficient data to evaluate
    ANOMALOUS = "ANOMALOUS"  # Requires explanation (e.g., inherited fabric)


class FaultQCResult(BaseModel):
    """Result of geomechanical fault QC."""

    fault_id: str = Field(..., description="Fault being evaluated")
    verdict: QCVerdict = Field(..., description="QC verdict")

    # What was checked
    checks_performed: list[str] = Field(
        default_factory=list, description="Checks that were run"
    )
    checks_passed: list[str] = Field(
        default_factory=list, description="Checks that passed"
    )
    checks_failed: list[str] = Field(
        default_factory=list, description="Checks that failed"
    )
    checks_skipped: list[str] = Field(
        default_factory=list, description="Checks that could not run (missing data)"
    )

    # Findings
    findings: list[dict[str, Any]] = Field(
        default_factory=list, description="Per-check findings"
    )
    anomalies: list[str] = Field(
        default_factory=list,
        description="Anomalies that require explanation",
    )
    competing_hypotheses: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Alternative explanations for the fault",
    )

    # Geomechanical context
    evaluated_stress_regime: str = Field(
        default="UNKNOWN", description="Stress regime used for evaluation"
    )
    evaluated_stress_age_ma: float | None = Field(
        default=None, description="Age of stress tensor used"
    )
    slip_tendency: float | None = Field(default=None)
    dilation_tendency: float | None = Field(default=None)
    is_yielding: bool | None = Field(default=None)

    # Recommendations
    recommendation: str = Field(
        default="", description="Recommended next action"
    )


def check_azimuth_vs_stress(
    fault_azimuth_deg: float,
    stress_regime: str,
    sigma1_azimuth_deg: float | None = None,
) -> dict[str, Any]:
    """Check whether fault orientation is consistent with stress regime.

    TECT-004: Fault azimuth is evidence, not age.
    TECT-005: Stress rotation outranks fault orientation.
    SR_INV_008: Fault generation from relational evidence.
    """
    from .stress_utils import classify_fault_orientation

    classification = classify_fault_orientation(
        fault_azimuth_deg, stress_regime, sigma1_azimuth_deg
    )

    return {
        "check": "azimuth_vs_stress",
        "fault_azimuth_deg": fault_azimuth_deg,
        "stress_regime": stress_regime,
        "sigma1_azimuth_deg": sigma1_azimuth_deg,
        "classification": classification,
        "consistent": classification.get("consistent", False),
        "note": (
            "Azimuth consistency is a NECESSARY but NOT SUFFICIENT condition. "
            "Fault age requires relational evidence (SR_INV_008)."
        ),
    }


def check_reactivation_viability(
    fault_strike_deg: float,
    fault_dip_deg: float,
    sigma1_azimuth_deg: float,
    sigma1_plunge_deg: float,
    sigma3_azimuth_deg: float,
    friction_coefficient: float = 0.6,
) -> dict[str, Any]:
    """Evaluate whether a fault can be reactivated under the given stress.

    This is the core geomechanical QC: Mohr-Coulomb analysis on the
    resolved stress on the fault plane.
    """
    import math

    # Simplified 3D Mohr-Coulomb slip tendency analysis
    # Convert angles to radians
    strike_rad = math.radians(fault_strike_deg)
    dip_rad = math.radians(fault_dip_deg)
    s1_az_rad = math.radians(sigma1_azimuth_deg)
    s1_pl_rad = math.radians(sigma1_plunge_deg)
    s3_az_rad = math.radians(sigma3_azimuth_deg)

    # Fault normal vector (simplified — assumes right-hand rule)
    nx = math.sin(dip_rad) * math.cos(strike_rad + math.pi / 2)
    ny = math.sin(dip_rad) * math.sin(strike_rad + math.pi / 2)
    nz = math.cos(dip_rad)

    # σ1 direction vector
    s1x = math.cos(s1_pl_rad) * math.cos(s1_az_rad)
    s1y = math.cos(s1_pl_rad) * math.sin(s1_az_rad)
    s1z = math.sin(s1_pl_rad)

    # σ3 direction vector
    s3_az_rad = math.radians(sigma3_azimuth_deg)
    s3_plunge = 0.0  # Simplified: horizontal σ3
    s3x = math.cos(s3_plunge) * math.cos(s3_az_rad)
    s3y = math.cos(s3_plunge) * math.sin(s3_az_rad)
    s3z = math.sin(s3_plunge)

    # Normal stress on fault plane (projection of σ1 and σ3 onto fault normal)
    cos_theta1 = abs(nx * s1x + ny * s1y + nz * s1z)
    cos_theta3 = abs(nx * s3x + ny * s3y + nz * s3z)

    # Slip tendency = τ/σn (simplified)
    # For optimally oriented faults, slip tendency → 1/friction
    slip_ratio = cos_theta1 / max(cos_theta1 + cos_theta3, 1e-10)
    slip_tendency = slip_ratio

    # Dilation tendency (simplified)
    dilation_tendency = (1.0 - cos_theta1) / max(cos_theta1 + cos_theta3, 1e-10)

    # Is the fault yielding? (Mohr-Coulomb: τ ≥ c + μσn)
    is_yielding = slip_tendency >= (1.0 / max(friction_coefficient, 0.01))

    return {
        "check": "reactivation_viability",
        "slip_tendency": round(slip_tendency, 3),
        "dilation_tendency": round(dilation_tendency, 3),
        "is_yielding": is_yielding,
        "friction_coefficient": friction_coefficient,
        "note": (
            "Simplified Mohr-Coulomb analysis. Full3D requires "
            "tensor decomposition on fault plane."
        ),
    }


def check_basement_inheritance(
    fault_azimuth_deg: float,
    basement_fabric_azimuth_deg: float | None,
    tolerance_deg: float = 15.0,
) -> dict[str, Any]:
    """Check whether fault orientation matches inherited basement fabric.

    TECT-009: The diagnostic signal is the transition, not the value.
    Basement fabric from gravity/magnetics may show structural trends
    that seismic cannot image.
    """
    if basement_fabric_azimuth_deg is None:
        return {
            "check": "basement_inheritance",
            "result": "UNDERCONSTRAINED",
            "note": "No basement fabric data available",
        }

    # Angular difference (accounting for180° ambiguity in strike)
    diff = abs(fault_azimuth_deg - basement_fabric_azimuth_deg) % 180
    if diff > 90:
        diff = 180 - diff

    is_inherited = diff <= tolerance_deg

    return {
        "check": "basement_inheritance",
        "fault_azimuth_deg": fault_azimuth_deg,
        "basement_fabric_azimuth_deg": basement_fabric_azimuth_deg,
        "angular_difference_deg": round(diff, 1),
        "tolerance_deg": tolerance_deg,
        "is_inherited": is_inherited,
        "note": (
            "Inheritance is a hypothesis, not a conclusion. "
            "Requires cross-cutting and displacement evidence (SR_INV_008)."
        ),
    }


def check_stress_rotation_evidence(
    fault_azimuth_deg: float,
    stress_phases: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check whether fault orientation is explained by a stress rotation.

    TECT-005: Stress rotation outranks fault orientation.
    TECT-009: The signal is the transition.

    When multiple stress phases exist, test which phase best explains
    the fault orientation.
    """
    from .stress_utils import classify_fault_orientation

    best_match = None
    best_score = -1.0

    for phase in stress_phases:
        regime = phase.get("stress_regime", "UNKNOWN")
        sigma1_az = phase.get("sigma1_azimuth_deg")
        result = classify_fault_orientation(
            fault_azimuth_deg, regime, sigma1_az
        )
        score = result.get("consistency_score", 0.0)
        if score > best_score:
            best_score = score
            best_match = {
                "phase_id": phase.get("event_id", "unknown"),
                "age_ma": phase.get("age_ma"),
                "stress_regime": regime,
                "sigma1_azimuth_deg": sigma1_az,
                "consistency_score": round(score, 3),
            }

    return {
        "check": "stress_rotation_evidence",
        "fault_azimuth_deg": fault_azimuth_deg,
        "n_stress_phases_evaluated": len(stress_phases),
        "best_matching_phase": best_match,
        "note": (
            "Best-matching stress phase is a hypothesis, not a conclusion. "
            "Fault age requires relational evidence beyond azimuth."
        ),
    }


__all__ = [
    "QCVerdict",
    "FaultQCResult",
    "check_azimuth_vs_stress",
    "check_reactivation_viability",
    "check_basement_inheritance",
    "check_stress_rotation_evidence",
]
