"""Hypothesis + WitnessProvenance model (W3 + W4 hardening pass 2026-07-24).

A legitimate hypothesis must come from one of these sources:
  1. independent model witness (e.g. separate AI or different prompt);
  2. classical computer-vision proposer (e.g. Canny + tracking);
  3. human-supplied geometry (operator picks);
  4. deterministic geological transformation whose derivation is explicitly recorded;
  5. an empty conceptual alternative that states what geometry is still required.

A hypothesis is never produced by mutating a single base framework and renaming
its label. `HypothesisModel.confidence_value` is null unless a named, versioned,
and validated benchmark receipt is attached. Image-only outputs never produce
percentage chance of closure, POS, drilling recommendation, etc.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Enums (string-valued for JSON-friendliness) ─────────────────────────────


class WitnessType(str, Enum):
    INDEPENDENT_MODEL = "independent_model"
    CLASSICAL_CV = "classical_cv"
    HUMAN_SUPPLIED = "human_supplied"
    DETERMINISTIC_TRANSFORM = "deterministic_transform"
    EMPTY_CONCEPTUAL = "empty_conceptual"


class HypothesisStatus(str, Enum):
    UNTESTED = "UNTESTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SURVIVES_CURRENT_TESTS = "SURVIVES_CURRENT_TESTS"
    REJECTED = "REJECTED"


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    PARTIAL = "PARTIAL"
    CALIBRATED = "CALIBRATED"


class GeometryOrigin(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    INTERPRETED = "interpreted"
    SPECULATIVE = "speculative"


class CoordinateDomain(str, Enum):
    PIXEL = "pixel"
    TRACE = "trace"
    CDP = "cdp"
    DISTANCE_M = "distance_m"
    TIME_MS = "time_ms"
    DEPTH_M = "depth_m"


# ── Provenance + witness ────────────────────────────────────────────────────


class WitnessProvenance(BaseModel):
    """Origin of one hypothesis. Never copy a geometry and rename it."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    witness_id: str
    witness_type: WitnessType
    model_or_method: str
    derivation: str  # explicit chain, e.g. "as_proposed(unchanged)" or "relay_segmented(throw_profile × 0.3 tips)"
    source_geometry_hash: str
    prompt_hash: str | None = None
    structural_style: str = "unknown"
    kinematic_claims: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    unresolved_measurements: list[str] = Field(default_factory=list)
    attachments: dict[str, Any] = Field(default_factory=dict)


# ── Hypothesis ──────────────────────────────────────────────────────────────


class Hypothesis(BaseModel):
    """A single seismic interpretation hypothesis.

    `confidence_value` is null unless `confidence_basis` carries a benchmark
    receipt (named, versioned, validated). Image-only inputs may not produce
    a confidence_value for any sealed verdict.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    hypothesis_id: str
    witness: WitnessProvenance
    faults: list[dict[str, Any]] = Field(default_factory=list)
    horizons: list[dict[str, Any]] = Field(default_factory=list)
    fault_blocks: list[dict[str, Any]] = Field(default_factory=list)
    structural_style: str = "unknown"
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    evidence_coverage_measured: int = 0
    evidence_coverage_applicable: int = 0
    calibration_status: CalibrationStatus = CalibrationStatus.UNCALIBRATED
    confidence_value: float | None = None
    confidence_basis: str | None = None
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    physics_gates: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    combined_gate_verdict: str | None = None
    attachments: dict[str, Any] = Field(default_factory=dict)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _param_hash(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def derive_hypothesis_status(
    *,
    kills: list[str],
    passes: list[str],
    warns: list[str],
    unmeasured: list[str],
) -> HypothesisStatus:
    """Aggregation law from the hardening prompt.

    any hard KILL → REJECTED
    no KILL + ≥1 measured hard gate → SURVIVES_CURRENT_TESTS
    no measurable gates → UNTESTED
    conflicting measured gates → INCONCLUSIVE
    """
    if kills:
        return HypothesisStatus.REJECTED
    measured = len(passes) + len(warns)
    if not measured and not unmeasured:
        return HypothesisStatus.UNTESTED
    if measured == 0:
        return HypothesisStatus.UNTESTED
    if passes and warns:
        return HypothesisStatus.INCONCLUSIVE
    if passes:
        return HypothesisStatus.SURVIVES_CURRENT_TESTS
    # only warns
    return HypothesisStatus.SURVIVES_CURRENT_TESTS


def evidence_coverage(applicable: int, measured: int) -> tuple[int, int]:
    """Return (measured, applicable). Caller is responsible for the
    denominator-guard. This is not a probability of geological truth.
    """
    return max(0, int(measured)), max(0, int(applicable))


def calibration_status_from_calibration(cal: dict[str, Any] | None) -> CalibrationStatus:
    if not isinstance(cal, dict):
        return CalibrationStatus.UNCALIBRATED
    has_axis = any(cal.get(k) is not None for k in ("x_axis", "vertical_axis", "horizontal"))
    has_scale = any(cal.get(k) is not None for k in ("bin_spacing_m", "vertical_exaggeration"))
    has_velocity = any(cal.get(k) is not None for k in ("velocity_td", "velocity_linear_m_s", "well_tie"))
    if has_axis and has_scale and has_velocity and cal.get("calibrated"):
        return CalibrationStatus.CALIBRATED
    if has_axis or has_scale or has_velocity:
        return CalibrationStatus.PARTIAL
    return CalibrationStatus.UNCALIBRATED


def make_empty_conceptual_hypothesis(
    hypothesis_id: str,
    *,
    missing_measurements: list[str],
    witness_method: str = "empty_conceptual",
) -> Hypothesis:
    """An empty conceptual hypothesis that states what geometry is still required.

    Per W3 source #5. Carries no geometry; carries an explicit list of
    unresolved measurements.
    """
    return Hypothesis(
        hypothesis_id=hypothesis_id,
        witness=WitnessProvenance(
            witness_id=f"empty_conceptual:{hypothesis_id}",
            witness_type=WitnessType.EMPTY_CONCEPTUAL,
            model_or_method=witness_method,
            derivation=(
                "Empty conceptual hypothesis — geometry not yet acquired. "
                "States what measurements are still required to make this "
                "hypothesis falsifiable."
            ),
            source_geometry_hash="0" * 16,
            structural_style="unresolved",
            unresolved_measurements=list(missing_measurements),
        ),
        faults=[],
        horizons=[],
        status=HypothesisStatus.UNTESTED,
        evidence_coverage_measured=0,
        evidence_coverage_applicable=0,
        calibration_status=CalibrationStatus.UNCALIBRATED,
        confidence_value=None,
        confidence_basis=None,
        supporting_evidence=[],
        contradicting_evidence=[],
        physics_gates=[],
        unresolved_questions=list(missing_measurements),
        combined_gate_verdict="UNMEASURED",
    )


__all__ = [
    "CalibrationStatus",
    "CoordinateDomain",
    "GeometryOrigin",
    "Hypothesis",
    "HypothesisStatus",
    "WitnessProvenance",
    "WitnessType",
    "calibration_status_from_calibration",
    "derive_hypothesis_status",
    "evidence_coverage",
    "make_empty_conceptual_hypothesis",
]
