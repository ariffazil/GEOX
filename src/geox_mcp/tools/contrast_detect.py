"""
GEOX Contrast Detect — Universal Anomalous Contrast Detector
═══════════════════════════════════════════════════════════════
Generalizes the Theory of Anomalous Contrast (ToAC) from seismic-only
to all seven dimensions of the GEOX dimensional ontology.

Original ToAC (anomalous_contrast.py): seismic impedance contrast only.
This module: Energy, Mass, Time, Space, Absence, Information, Intelligence.

Pattern (universal across all dimensions):
  1. PREDICT — expected value from model/theory/Five-Part expectation
  2. OBSERVE — actual value from data/evidence/measurement
  3. CONTRAST — |predicted − observed| normalized
  4. CLASSIFY — anomaly type, severity, governance action
  5. REPORT — structured JSON with epistemic labels

Axiom:
  Anomalous contrast is the universal signature of geological inconsistency.
  Across all seven dimensions, anomalies share one pattern:
  contrast that cannot be explained by SOURCE → TRANSFER → SINK → BURIAL → EXHUMATION.

F1-F13 binding:
  F1 AMANAH     — read-only computation, no mutation
  F2 TRUTH      — output is measured/derived, never fabricated
  F4 CLARITY    — every output carries dimension + epistemic label
  F7 HUMILITY   — confidence capped at 0.90
  F9 ANTI-HANTU — no "this IS wrong" — only "contrast detected, investigate"
  F11 AUDIT     — every contrast carries provenance

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("geox.canonical.contrast_detect")


# ═══════════════════════════════════════════════════════════════════════════════
# Dimension Enum
# ═══════════════════════════════════════════════════════════════════════════════


class Dimension(StrEnum):
    """The seven dimensions of geological systems."""

    ENERGY = "energy"
    MASS = "mass"
    TIME = "time"
    SPACE = "space"
    ABSENCE = "absence"
    INFORMATION = "information"
    INTELLIGENCE = "intelligence"


class AnomalyClass(StrEnum):
    """Classification of detected anomalies."""

    UNDERPREDICTED = "underpredicted"  # observed > predicted
    OVERPREDICTED = "overpredicted"  # predicted > observed
    IMPOSSIBLE = "impossible"  # physically inconsistent
    MISSING = "missing"  # expected but absent
    EXCESS = "excess"  # present but unexpected


class Severity(StrEnum):
    """Anomaly severity levels."""

    LOW = "low"  # within noise, informational
    MODERATE = "moderate"  # warrants investigation
    HIGH = "high"  # strong anomaly, likely real
    CRITICAL = "critical"  # governance escalation required


class FivePartViolation(StrEnum):
    """Which part of the Five-Part Model is violated."""

    SOURCE = "source"
    TRANSFER = "transfer"
    SINK = "sink"
    BURIAL = "burial"
    EXHUMATION = "exhumation"
    NONE = "none"


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ContrastResult:
    """Result of a single dimension contrast analysis."""

    dimension: Dimension
    predicted_value: float | None
    observed_value: float | None
    contrast_magnitude: float  # 0–1+ normalized
    anomaly_class: AnomalyClass
    severity: Severity
    five_part_violation: FivePartViolation
    confidence: str  # OBS/DER/INT/SPEC
    explanation: str
    evidence_refs: list[str] = field(default_factory=list)
    recommended_next_tool: str | None = None


@dataclass
class DimensionalAuditResult:
    """Result of cross-dimensional consistency audit."""

    contrasts: list[ContrastResult]
    total_anomalies: int
    critical_count: int
    highest_anomaly_dimension: Dimension | None
    dimensional_entropy: float  # 0–1, how much anomalous contrast across all dims
    cross_dimensional_conflicts: list[dict[str, Any]]
    recommended_actions: list[str]
    confidence: str


# ═══════════════════════════════════════════════════════════════════════════════
# Contrast Detection Engine
# ═══════════════════════════════════════════════════════════════════════════════


def compute_contrast(
    predicted: float,
    observed: float,
    threshold: float = 0.2,
    normalize: bool = True,
) -> tuple[float, AnomalyClass]:
    """Compute normalized contrast between predicted and observed values.

    Args:
        predicted: Expected value from model/theory
        observed: Actual value from data/evidence
        threshold: Anomaly detection threshold (default 0.2 = 20%)
        normalize: If True, normalize by predicted magnitude

    Returns:
        (contrast_magnitude, anomaly_class)
    """
    if predicted == 0 and observed == 0:
        return 0.0, AnomalyClass.UNDERPREDICTED  # no contrast

    # Normalize by predicted magnitude if requested
    if normalize and predicted != 0:
        contrast = abs(observed - predicted) / abs(predicted)
    else:
        contrast = abs(observed - predicted)

    # Classify
    if observed > predicted * (1 + threshold):
        anomaly_class = AnomalyClass.UNDERPREDICTED  # observed exceeds prediction
    elif observed < predicted * (1 - threshold):
        anomaly_class = AnomalyClass.OVERPREDICTED  # prediction exceeds observation
    else:
        anomaly_class = AnomalyClass.UNDERPREDICTED  # within threshold

    return contrast, anomaly_class


def classify_severity(
    contrast: float,
    threshold: float = 0.2,
) -> Severity:
    """Classify anomaly severity from contrast magnitude.

    Args:
        contrast: Normalized contrast magnitude
        threshold: Base anomaly threshold

    Returns:
        Severity level
    """
    if contrast < threshold:
        return Severity.LOW
    elif contrast < threshold * 2:
        return Severity.MODERATE
    elif contrast < threshold * 5:
        return Severity.HIGH
    else:
        return Severity.CRITICAL


def detect_mass_contrast(
    sediment_production: float | None,
    sediment_accumulation: float | None,
    erosion_estimate: float | None = None,
    threshold: float = 0.3,
) -> ContrastResult:
    """Detect mass balance anomalies.

    Compares sediment production (source) vs accumulation (sink).
    If accumulation << production, bypass or missing mass is indicated.

    Args:
        sediment_production: Estimated sediment production rate (m³/Myr)
        sediment_accumulation: Estimated sediment accumulation rate (m³/Myr)
        erosion_estimate: Estimated erosion volume (m³) — optional
        threshold: Anomaly threshold (default 30%)

    Returns:
        ContrastResult for Mass dimension
    """
    if sediment_production is None or sediment_accumulation is None:
        return ContrastResult(
            dimension=Dimension.MASS,
            predicted_value=sediment_production,
            observed_value=sediment_accumulation,
            contrast_magnitude=0.0,
            anomaly_class=AnomalyClass.MISSING,
            severity=Severity.LOW,
            five_part_violation=FivePartViolation.NONE,
            confidence="UNKNOWN",
            explanation="Insufficient data for mass balance computation.",
            recommended_next_tool="geox_basin",
        )

    contrast, anomaly_class = compute_contrast(sediment_production, sediment_accumulation, threshold)
    severity = classify_severity(contrast, threshold)

    # Determine which Five-Part link is violated
    if anomaly_class == AnomalyClass.OVERPREDICTED:
        # Production > accumulation → bypass or missing mass
        violation = FivePartViolation.TRANSFER
        explanation = (
            f"Sediment production ({sediment_production:.0f} m³/Myr) exceeds "
            f"accumulation ({sediment_accumulation:.0f} m³/Myr) by "
            f"{contrast * 100:.0f}%. This indicates bypass, missing mass, or "
            f"downstream deposition outside the studied basin."
        )
        next_tool = "geox_sequence"
    elif anomaly_class == AnomalyClass.UNDERPREDICTED:
        # Accumulation > production → external source or measurement error
        violation = FivePartViolation.SOURCE
        explanation = (
            f"Sediment accumulation ({sediment_accumulation:.0f} m³/Myr) exceeds "
            f"estimated production ({sediment_production:.0f} m³/Myr) by "
            f"{contrast * 100:.0f}%. This indicates an unaccounted source, "
            f"reworking of older deposits, or overestimated accumulation."
        )
        next_tool = "geox_evidence"
    else:
        violation = FivePartViolation.NONE
        explanation = "Mass balance within expected range."
        next_tool = None

    return ContrastResult(
        dimension=Dimension.MASS,
        predicted_value=sediment_production,
        observed_value=sediment_accumulation,
        contrast_magnitude=contrast,
        anomaly_class=anomaly_class,
        severity=severity,
        five_part_violation=violation,
        confidence="INT",
        explanation=explanation,
        recommended_next_tool=next_tool,
    )


def detect_energy_contrast(
    predicted_stress: float | None,
    observed_stress: float | None,
    predicted_temperature: float | None = None,
    observed_temperature: float | None = None,
    threshold: float = 0.2,
) -> ContrastResult:
    """Detect energy gradient anomalies.

    Compares predicted stress/temperature from burial model
    vs observed stress/temperature from wells/seismic.

    Args:
        predicted_stress: Expected stress (Pa) from model
        observed_stress: Measured stress (Pa) from data
        predicted_temperature: Expected temperature (K) from model
        observed_temperature: Measured temperature (K) from data
        threshold: Anomaly threshold (default 20%)

    Returns:
        ContrastResult for Energy dimension
    """
    # Use stress if available, temperature otherwise
    if predicted_stress is not None and observed_stress is not None:
        predicted, observed = predicted_stress, observed_stress
        metric = "stress"
    elif predicted_temperature is not None and observed_temperature is not None:
        predicted, observed = predicted_temperature, observed_temperature
        metric = "temperature"
    else:
        return ContrastResult(
            dimension=Dimension.ENERGY,
            predicted_value=None,
            observed_value=None,
            contrast_magnitude=0.0,
            anomaly_class=AnomalyClass.MISSING,
            severity=Severity.LOW,
            five_part_violation=FivePartViolation.NONE,
            confidence="UNKNOWN",
            explanation="Insufficient energy data for contrast computation.",
            recommended_next_tool="geox_geomechanics",
        )

    contrast, anomaly_class = compute_contrast(predicted, observed, threshold)
    severity = classify_severity(contrast, threshold)

    if anomaly_class == AnomalyClass.OVERPREDICTED:
        violation = FivePartViolation.BURIAL
        explanation = (
            f"Predicted {metric} ({predicted:.0f}) exceeds observed ({observed:.0f}) "
            f"by {contrast * 100:.0f}%. This may indicate overpressure, "
            f"fluid migration, or abnormal thermal regime."
        )
        next_tool = "geox_geomechanics"
    elif anomaly_class == AnomalyClass.UNDERPREDICTED:
        violation = FivePartViolation.SOURCE
        explanation = (
            f"Observed {metric} ({observed:.0f}) exceeds predicted ({predicted:.0f}) "
            f"by {contrast * 100:.0f}%. This may indicate additional heat source, "
            f"tectonic stress, or model underestimation."
        )
        next_tool = "geox_egs_rock_physics"
    else:
        violation = FivePartViolation.NONE
        explanation = f"Energy ({metric}) within expected range."
        next_tool = None

    return ContrastResult(
        dimension=Dimension.ENERGY,
        predicted_value=predicted,
        observed_value=observed,
        contrast_magnitude=contrast,
        anomaly_class=anomaly_class,
        severity=severity,
        five_part_violation=violation,
        confidence="DER",
        explanation=explanation,
        recommended_next_tool=next_tool,
    )


def detect_time_contrast(
    expected_age_ma: float | None,
    measured_age_ma: float | None,
    uncertainty_ma: float | None = None,
    threshold: float = 0.1,
) -> ContrastResult:
    """Detect temporal contradictions.

    Compares expected age from stratigraphic position vs measured age
    from biostrat/isotopic dating.

    Args:
        expected_age_ma: Expected age (Ma) from stratigraphy
        measured_age_ma: Measured age (Ma) from dating
        uncertainty_ma: Uncertainty on measured age (Ma)
        threshold: Anomaly threshold (default 10% of age)

    Returns:
        ContrastResult for Time dimension
    """
    if expected_age_ma is None or measured_age_ma is None:
        return ContrastResult(
            dimension=Dimension.TIME,
            predicted_value=expected_age_ma,
            observed_value=measured_age_ma,
            contrast_magnitude=0.0,
            anomaly_class=AnomalyClass.MISSING,
            severity=Severity.LOW,
            five_part_violation=FivePartViolation.NONE,
            confidence="UNKNOWN",
            explanation="Insufficient age data for temporal contrast.",
            recommended_next_tool="geox_deep_time_state",
        )

    # For time, contrast is absolute difference relative to expected age
    if expected_age_ma > 0:
        contrast = abs(measured_age_ma - expected_age_ma) / expected_age_ma
    else:
        contrast = abs(measured_age_ma - expected_age_ma)

    # Classify
    if measured_age_ma > expected_age_ma * (1 + threshold):
        anomaly_class = AnomalyClass.UNDERPREDICTED  # older than expected
        explanation = (
            f"Measured age ({measured_age_ma:.1f} Ma) is older than expected "
            f"({expected_age_ma:.1f} Ma) by {contrast * 100:.0f}%. "
            f"This may indicate reworking, inheritance, or stratigraphic misassignment."
        )
        violation = FivePartViolation.SOURCE
        next_tool = "geox_egs_query_provenance"
    elif measured_age_ma < expected_age_ma * (1 - threshold):
        anomaly_class = AnomalyClass.OVERPREDICTED  # younger than expected
        explanation = (
            f"Measured age ({measured_age_ma:.1f} Ma) is younger than expected "
            f"({expected_age_ma:.1f} Ma) by {contrast * 100:.0f}%. "
            f"This may indicate missing time, unconformity, or contamination."
        )
        violation = FivePartViolation.EXHUMATION
        next_tool = "geox_sequence"
    else:
        anomaly_class = AnomalyClass.UNDERPREDICTED
        explanation = "Age within expected range."
        violation = FivePartViolation.NONE
        next_tool = None

    severity = classify_severity(contrast, threshold)

    return ContrastResult(
        dimension=Dimension.TIME,
        predicted_value=expected_age_ma,
        observed_value=measured_age_ma,
        contrast_magnitude=contrast,
        anomaly_class=anomaly_class,
        severity=severity,
        five_part_violation=violation,
        confidence="INT",
        explanation=explanation,
        recommended_next_tool=next_tool,
    )


def detect_absence_contrast(
    expected_record_thickness: float | None,
    observed_record_thickness: float | None,
    expected_time_span_ma: float | None = None,
    observed_time_span_ma: float | None = None,
    threshold: float = 0.3,
) -> ContrastResult:
    """Detect absence anomalies — missing time, missing mass, unconformities.

    Compares expected continuous record vs observed gap.

    Args:
        expected_record_thickness: Expected thickness (m) from subsidence model
        observed_record_thickness: Observed thickness (m) from wells/seismic
        expected_time_span_ma: Expected time span (Ma) for the interval
        observed_time_span_ma: Observed time span (Ma) from dating
        threshold: Anomaly threshold (default 30%)

    Returns:
        ContrastResult for Absence dimension
    """
    # Use thickness if available, time span otherwise
    if expected_record_thickness is not None and observed_record_thickness is not None:
        expected, observed = expected_record_thickness, observed_record_thickness
        metric = "thickness"
    elif expected_time_span_ma is not None and observed_time_span_ma is not None:
        expected, observed = expected_time_span_ma, observed_time_span_ma
        metric = "time span"
    else:
        return ContrastResult(
            dimension=Dimension.ABSENCE,
            predicted_value=None,
            observed_value=None,
            contrast_magnitude=0.0,
            anomaly_class=AnomalyClass.MISSING,
            severity=Severity.LOW,
            five_part_violation=FivePartViolation.NONE,
            confidence="UNKNOWN",
            explanation="Insufficient data for absence detection.",
            recommended_next_tool="geox_sequence",
        )

    # Absence = expected but missing
    if expected > 0:
        absence_fraction = (expected - observed) / expected
    else:
        absence_fraction = 0.0

    if absence_fraction > threshold:
        anomaly_class = AnomalyClass.MISSING
        severity = classify_severity(absence_fraction, threshold)
        explanation = (
            f"Expected {metric} ({expected:.0f}) exceeds observed ({observed:.0f}) "
            f"by {absence_fraction * 100:.0f}%. This indicates absence — "
            f"unconformity, non-deposition, or erosion."
        )
        violation = FivePartViolation.EXHUMATION
        next_tool = "geox_sequence"
    elif absence_fraction < -threshold:
        anomaly_class = AnomalyClass.EXCESS
        severity = classify_severity(abs(absence_fraction), threshold)
        explanation = (
            f"Observed {metric} ({observed:.0f}) exceeds expected ({expected:.0f}) "
            f"by {abs(absence_fraction) * 100:.0f}%. This indicates excess — "
            f"additional source, reworking, or overestimation."
        )
        violation = FivePartViolation.SOURCE
        next_tool = "geox_evidence"
    else:
        anomaly_class = AnomalyClass.MISSING
        severity = Severity.LOW
        explanation = f"Record {metric} within expected range."
        violation = FivePartViolation.NONE
        next_tool = None

    return ContrastResult(
        dimension=Dimension.ABSENCE,
        predicted_value=expected,
        observed_value=observed,
        contrast_magnitude=abs(absence_fraction),
        anomaly_class=anomaly_class,
        severity=severity,
        five_part_violation=violation,
        confidence="INT",
        explanation=explanation,
        recommended_next_tool=next_tool,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Dimensional Audit
# ═══════════════════════════════════════════════════════════════════════════════


def audit_dimensional_consistency(
    contrasts: list[ContrastResult],
) -> DimensionalAuditResult:
    """Audit cross-dimensional consistency.

    Checks whether anomalies in one dimension contradict anomalies
    (or non-anomalies) in another dimension.

    Args:
        contrasts: List of per-dimension contrast results

    Returns:
        DimensionalAuditResult with cross-dimensional conflicts
    """
    total_anomalies = sum(1 for c in contrasts if c.severity in (Severity.MODERATE, Severity.HIGH, Severity.CRITICAL))
    critical_count = sum(1 for c in contrasts if c.severity == Severity.CRITICAL)

    # Find highest anomaly
    if contrasts:
        highest = max(contrasts, key=lambda c: c.contrast_magnitude)
        highest_dim = highest.dimension
    else:
        highest_dim = None

    # Compute dimensional entropy (normalized sum of contrasts)
    if contrasts:
        total_contrast = sum(c.contrast_magnitude for c in contrasts)
        max_possible = len(contrasts)  # if every dimension had contrast = 1.0
        dimensional_entropy = min(total_contrast / max_possible, 1.0) if max_possible > 0 else 0.0
    else:
        dimensional_entropy = 0.0

    # Detect cross-dimensional conflicts
    conflicts = []
    mass_contrasts = [c for c in contrasts if c.dimension == Dimension.MASS]
    [c for c in contrasts if c.dimension == Dimension.TIME]
    absence_contrasts = [c for c in contrasts if c.dimension == Dimension.ABSENCE]

    # Mass + Absence conflict: if mass is missing AND absence is detected,
    # the missing mass may be explained by the absence
    if mass_contrasts and absence_contrasts:
        mass = mass_contrasts[0]
        absence = absence_contrasts[0]
        if mass.severity in (Severity.HIGH, Severity.CRITICAL) and absence.severity in (
            Severity.HIGH,
            Severity.CRITICAL,
        ):
            if mass.anomaly_class == AnomalyClass.OVERPREDICTED and absence.anomaly_class == AnomalyClass.MISSING:
                conflicts.append(
                    {
                        "type": "MASS_ABSENCE_CORRELATION",
                        "dimensions": ["mass", "absence"],
                        "explanation": (
                            "Missing mass correlates with detected absence. "
                            "The unconformity/erosion may explain the mass deficit. "
                            "This is CONSISTENT — the anomalies reinforce each other."
                        ),
                        "consistency": "CONSISTENT",
                    }
                )

    # Energy + Mass conflict: high energy but low mass = anomalous
    energy_contrasts = [c for c in contrasts if c.dimension == Dimension.ENERGY]
    if energy_contrasts and mass_contrasts:
        energy = energy_contrasts[0]
        mass = mass_contrasts[0]
        if energy.severity in (Severity.HIGH, Severity.CRITICAL) and mass.severity in (
            Severity.HIGH,
            Severity.CRITICAL,
        ):
            if energy.anomaly_class == AnomalyClass.UNDERPREDICTED and mass.anomaly_class == AnomalyClass.OVERPREDICTED:
                conflicts.append(
                    {
                        "type": "ENERGY_MASS_CONFLICT",
                        "dimensions": ["energy", "mass"],
                        "explanation": (
                            "High energy (stress/temperature) but mass deficit. "
                            "High energy should produce more sediment, not less. "
                            "This is INCONSISTENT — check transfer zone."
                        ),
                        "consistency": "INCONSISTENT",
                    }
                )

    # Generate recommended actions
    recommended = []
    for c in contrasts:
        if c.severity in (Severity.HIGH, Severity.CRITICAL):
            if c.recommended_next_tool:
                recommended.append(f"Investigate {c.dimension.value} anomaly with {c.recommended_next_tool}")

    return DimensionalAuditResult(
        contrasts=contrasts,
        total_anomalies=total_anomalies,
        critical_count=critical_count,
        highest_anomaly_dimension=highest_dim,
        dimensional_entropy=dimensional_entropy,
        cross_dimensional_conflicts=conflicts,
        recommended_actions=recommended,
        confidence="INT",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool Interface
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve_scalar_or_p50(
    scalar: float | None,
    dist: list[float] | tuple[float, ...] | None,
) -> tuple[float | None, dict[str, float] | None]:
    """Accept flat scalar or [P90, P50, P10] distribution (low→high or high→low).

    Convention: pass [p90, p50, p10] for low/mid/high estimates of the same quantity
    (p90 = conservative low case for rates/ages as used in exploration).
    Returns (p50_or_scalar, full_dist_dict_or_None).
    """
    if dist is not None and len(dist) >= 3:
        vals = [float(x) for x in dist[:3]]
        ordered = sorted(vals)
        # map sorted low/mid/high → p90/p50/p10 labels (p90=low estimate, p10=high)
        d = {"p90": ordered[0], "p50": ordered[1], "p10": ordered[2]}
        return d["p50"], d
    if scalar is not None:
        return float(scalar), None
    return None, None


def _distribution_spread_ratio(dist: dict[str, float] | None) -> float | None:
    """(P10-P90)/max(|P50|, eps) — relative uncertainty width."""
    if not dist:
        return None
    p50 = abs(dist["p50"]) or 1e-9
    return abs(dist["p10"] - dist["p90"]) / p50


def contrast_detect(
    dimension: str = "all",
    mass_predicted: float | None = None,
    mass_observed: float | None = None,
    energy_predicted_stress: float | None = None,
    energy_observed_stress: float | None = None,
    energy_predicted_temp: float | None = None,
    energy_observed_temp: float | None = None,
    time_expected_ma: float | None = None,
    time_measured_ma: float | None = None,
    absence_expected_thickness: float | None = None,
    absence_observed_thickness: float | None = None,
    absence_expected_timespan: float | None = None,
    absence_observed_timespan: float | None = None,
    threshold: float = 0.2,
    # ── Probabilistic upgrades (2026-07-09) ──────────────────────────
    # Optional [P90, P50, P10] arrays. When provided, P50 drives the contrast
    # and the P10–P90 envelope is reported as variance / W_scar.
    mass_predicted_dist: list[float] | None = None,
    mass_observed_dist: list[float] | None = None,
    energy_predicted_temp_dist: list[float] | None = None,
    energy_observed_temp_dist: list[float] | None = None,
    time_expected_dist: list[float] | None = None,
    time_measured_dist: list[float] | None = None,
    confidence_index: float = 0.70,
    data_quality: str = "unknown",
) -> dict[str, Any]:
    """Universal anomalous contrast detector across seven dimensions.

    Generalizes the Theory of Anomalous Contrast (ToAC) from seismic-only
    to all seven dimensions of the GEOX dimensional ontology.

    Args:
        dimension: Which dimension to check ("all", "mass", "energy", "time", "absence")
        mass_predicted / mass_observed: flat scalars (legacy) OR use *_dist
        *_dist: optional [P90, P50, P10] confidence intervals
        confidence_index: data-quality weight 0.0–1.0 (3D seismic > regional 2D)
        data_quality: free label e.g. "hires_3d" | "regional_2d" | "well_only" | "unknown"
        threshold: Anomaly detection threshold (default 0.2 = 20%)

    Returns:
        Structured anomaly report with per-dimension contrasts,
        dimensional entropy, variance warnings, and recommended actions.
    """
    # Clamp confidence_index (F7)
    ci = max(0.0, min(1.0, float(confidence_index)))
    variance_warnings: list[str] = []
    if ci < 0.99:
        variance_warnings.append(
            f"confidence_index={ci:.2f} < 0.99 — P(truth) not F2-grade; treat contrast as W_scar, not verdict"
        )

    # Resolve scalar / distribution inputs
    mass_p, mass_p_d = _resolve_scalar_or_p50(mass_predicted, mass_predicted_dist)
    mass_o, mass_o_d = _resolve_scalar_or_p50(mass_observed, mass_observed_dist)
    e_tp, e_tp_d = _resolve_scalar_or_p50(energy_predicted_temp, energy_predicted_temp_dist)
    e_to, e_to_d = _resolve_scalar_or_p50(energy_observed_temp, energy_observed_temp_dist)
    t_e, t_e_d = _resolve_scalar_or_p50(time_expected_ma, time_expected_dist)
    t_m, t_m_d = _resolve_scalar_or_p50(time_measured_ma, time_measured_dist)

    for name, d in (
        ("mass_predicted", mass_p_d),
        ("mass_observed", mass_o_d),
        ("energy_temp_predicted", e_tp_d),
        ("energy_temp_observed", e_to_d),
        ("time_expected", t_e_d),
        ("time_measured", t_m_d),
    ):
        spread = _distribution_spread_ratio(d)
        if spread is not None and spread > 0.5:
            variance_warnings.append(
                f"{name} P10–P90 spread {spread:.0%} of P50 — high epistemic width; HOLD promotion"
            )

    contrasts: list[ContrastResult] = []
    dims_to_check = [d.strip().lower() for d in dimension.split(",")]

    # Mass contrast
    if "all" in dims_to_check or "mass" in dims_to_check:
        contrasts.append(detect_mass_contrast(mass_p, mass_o, threshold=threshold))

    # Energy contrast
    if "all" in dims_to_check or "energy" in dims_to_check:
        contrasts.append(
            detect_energy_contrast(
                energy_predicted_stress,
                energy_observed_stress,
                e_tp,
                e_to,
                threshold=threshold,
            )
        )

    # Time contrast
    if "all" in dims_to_check or "time" in dims_to_check:
        contrasts.append(detect_time_contrast(t_e, t_m, threshold=threshold))

    # Absence contrast
    if "all" in dims_to_check or "absence" in dims_to_check:
        contrasts.append(
            detect_absence_contrast(
                absence_expected_thickness,
                absence_observed_thickness,
                absence_expected_timespan,
                absence_observed_timespan,
                threshold=threshold,
            )
        )

    # Cross-dimensional audit
    audit = audit_dimensional_consistency(contrasts)

    # Weight severity by confidence_index (low CI → cannot escalate to CRITICAL alone)
    weighted_critical = audit.critical_count if ci >= 0.70 else 0
    if audit.critical_count > 0 and ci < 0.70:
        variance_warnings.append(
            "CRITICAL contrast demoted under low confidence_index — insufficient data quality for governance escalation"
        )

    distributions_used = {
        k: v
        for k, v in {
            "mass_predicted": mass_p_d,
            "mass_observed": mass_o_d,
            "energy_temp_predicted": e_tp_d,
            "energy_temp_observed": e_to_d,
            "time_expected": t_e_d,
            "time_measured": t_m_d,
        }.items()
        if v is not None
    }

    return {
        "status": "OK",
        "dimension_requested": dimension,
        "threshold": threshold,
        "confidence_index": ci,
        "data_quality": data_quality,
        "distributions": distributions_used,
        "variance_warnings": variance_warnings,
        "probabilistic_mode": bool(distributions_used),
        "contrasts": [
            {
                "dimension": c.dimension.value,
                "predicted": c.predicted_value,
                "observed": c.observed_value,
                "contrast_magnitude": round(c.contrast_magnitude, 4),
                "anomaly_class": c.anomaly_class.value,
                "severity": c.severity.value,
                "five_part_violation": c.five_part_violation.value,
                "confidence": c.confidence,
                "confidence_weighted": round(min(0.90, float(c.confidence or 0.5) * ci), 4)
                if isinstance(c.confidence, (int, float))
                else c.confidence,
                "explanation": c.explanation,
                "recommended_next_tool": c.recommended_next_tool,
            }
            for c in contrasts
        ],
        "audit": {
            "total_anomalies": audit.total_anomalies,
            "critical_count": audit.critical_count,
            "critical_count_confidence_weighted": weighted_critical,
            "highest_anomaly_dimension": audit.highest_anomaly_dimension.value if audit.highest_anomaly_dimension else None,
            "dimensional_entropy": round(audit.dimensional_entropy, 4),
            "cross_dimensional_conflicts": audit.cross_dimensional_conflicts,
            "recommended_actions": audit.recommended_actions,
            "confidence": audit.confidence,
            "w_scar": round(1.0 - ci, 4),
        },
        "_envelope": {
            "evidence_floor": "DERIVED",
            "method": "Universal anomalous contrast detection (ToAC generalization) + P10/P50/P90",
            "authority": "GEOX Five-Part Invariants + Seven Dimensions",
            "theory": "Theory of Anomalous Contrast (Eureka 2026-06-05)",
            "humility": "confidence_index weights severity; F2 variance warnings when CI<0.99",
        },
    }
