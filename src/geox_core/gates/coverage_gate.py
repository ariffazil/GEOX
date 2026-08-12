"""
Coverage Gate — GEOX Unknown-Space Mapping
DITEMPA BUKAN DIBERI — Forged, not given

Component #36: UNKNOWN_SPACE_MAPPING

Implements 4-layer coverage check:
  1. Sensing — did sensors touch reality?
  2. Recognition — was the signal seen?
  3. Interpretation — was the signal correctly interpreted?
  4. Institutional memory — was the interpretation preserved or compressed?

Canonical example: Bekok Deep-1 (SCAR-6)
  - Sensing: PASS (3D seismic bright spot + historical well + mud logging)
  - Recognition: FAIL (bright spot = DHI, not hazard)
  - Interpretation: FAIL (pressure increase = formation, not gas)
  - Institutional memory: FAIL (report compressed to 'formation issue')
  - Result: LOPC Tier 1, platform evacuation

Axiom: "Confidence calibrated to data is engineering.
        Confidence detached from calibration is narrative."
Coverage axiom: "Disasters begin when confidence outruns evidence."

Source: Arif Fazil (F13 SOVEREIGN), 2026-08-13
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CoverageLevel(str, Enum):
    """Coverage density levels — ordered highest to lowest."""

    SUFFICIENT = "SUFFICIENT"  # score 0.70-1.00
    PARTIAL = "PARTIAL"  # score 0.30-0.69
    SPARSE = "SPARSE"  # score 0.10-0.29
    VOID = "VOID"  # score 0.00-0.09


COVERAGE_THRESHOLDS = {
    CoverageLevel.SUFFICIENT: {"min": 0.70, "max": 1.00},
    CoverageLevel.PARTIAL: {"min": 0.30, "max": 0.69},
    CoverageLevel.SPARSE: {"min": 0.10, "max": 0.29},
    CoverageLevel.VOID: {"min": 0.00, "max": 0.09},
}


class InterpretationLayer(str, Enum):
    """The 4-layer coverage check from SCAR-6 forensics."""

    SENSING = "sensing"
    RECOGNITION = "recognition"
    INTERPRETATION = "interpretation"
    INSTITUTIONAL_MEMORY = "institutional_memory"


@dataclass
class LayerStatus:
    """Status of a single coverage layer."""

    layer: InterpretationLayer
    status: str  # "PASS" | "FAIL" | "UNKNOWN"
    evidence: list[str] = field(default_factory=list)
    root_cause: str | None = None


@dataclass
class CoverageManifest:
    """
    Coverage manifest for geopressure analysis.

    Captures both quantitative (coverage_score) and
    qualitative (4-layer interpretation chain) coverage.
    """

    # Quantitative
    observation_count: int = 0
    interval_thickness_100m_bins: int = 0
    coverage_score: float = 0.0  # observation_count / interval_thickness_100m_bins

    # Qualitative — from SCAR-6 forensics
    sensing: LayerStatus | None = None
    recognition: LayerStatus | None = None
    interpretation_layer: LayerStatus | None = None
    institutional_memory: LayerStatus | None = None

    # Confidence relationship
    confidence: float = 0.0
    confidence_outruns_evidence: bool = False

    # Source tracking
    basin_context_ref: str | None = None
    observation_sources: list[str] = field(default_factory=list)

    def compute_coverage_score(self) -> float:
        """Compute quantitative coverage score."""
        if self.interval_thickness_100m_bins == 0:
            self.coverage_score = 0.0
        else:
            self.coverage_score = min(
                self.observation_count / self.interval_thickness_100m_bins,
                1.0,
            )
        return self.coverage_score

    def compute_confidence_gap(self) -> float:
        """Return confidence - coverage. Positive = outrunning evidence."""
        gap = self.confidence - self.coverage_score
        self.confidence_outruns_evidence = gap > 0.30
        return gap


@dataclass
class CoverageGateResult:
    """Result of coverage gate check."""

    status: str  # "PASS" | "888_HOLD"
    level: CoverageLevel
    coverage_score: float
    confidence: float
    confidence_gap: float
    confidence_outruns_evidence: bool
    layer_statuses: dict[str, str] = field(default_factory=dict)
    hold_reasons: list[str] = field(default_factory=list)
    epistemic_override: str | None = None  # forced label if coverage is low
    message: str = ""


def check_coverage_gate(
    manifest: CoverageManifest | None,
    confidence: float = 0.0,
) -> CoverageGateResult:
    """
    Check coverage gate. Implements Component #36 from pressure_components.yaml.

    Three independent checks:
    1. Quantitative: coverage_score vs confidence gap
    2. Qualitative: 4-layer interpretation chain
    3. Void check: zero observations = 888_HOLD regardless of anything else

    Args:
        manifest: Coverage manifest
        confidence: Model confidence to check against coverage

    Returns:
        CoverageGateResult with status and details
    """
    if manifest is None:
        return CoverageGateResult(
            status="888_HOLD",
            level=CoverageLevel.VOID,
            coverage_score=0.0,
            confidence=confidence,
            confidence_gap=confidence,
            confidence_outruns_evidence=confidence > 0.30,
            hold_reasons=["no_coverage_manifest_provided"],
            message="No coverage manifest provided. 888_HOLD.",
        )

    # Compute scores
    score = manifest.compute_coverage_score()
    gap = manifest.compute_confidence_gap()

    # Determine coverage level
    level = CoverageLevel.VOID
    for lv, thresh in COVERAGE_THRESHOLDS.items():
        if thresh["min"] <= score <= thresh["max"]:
            level = lv
            break

    hold_reasons: list[str] = []
    epistemic_override: str | None = None
    layer_statuses: dict[str, str] = {}

    # CHECK 1: Void coverage
    if level == CoverageLevel.VOID:
        hold_reasons.append("void_coverage_no_observational_basis")
        epistemic_override = "HYPOTHESIS"

    # CHECK 2: Sparse coverage — label drops regardless of confidence
    if level == CoverageLevel.SPARSE:
        hold_reasons.append("insufficient_observational_coverage")
        epistemic_override = "HYPOTHESIS"

    # CHECK 3: Confidence outruns evidence
    if manifest.confidence_outruns_evidence:
        hold_reasons.append("confidence_outruns_evidence")
        if epistemic_override is None:
            epistemic_override = "HYPOTHESIS"

    # CHECK 4: Qualitative layer check (SCAR-6 forensics)
    for layer_name in [
        "sensing",
        "recognition",
        "interpretation_layer",
        "institutional_memory",
    ]:
        layer: LayerStatus | None = getattr(manifest, layer_name, None)
        if layer is not None:
            layer_statuses[layer_name] = layer.status
            if layer.status == "FAIL":
                hold_reasons.append(
                    f"{layer.layer.value}_failure"
                    + (f": {layer.root_cause}" if layer.root_cause else "")
                )

    # CHECK 5: If ANY qualitative layer fails, flag it
    has_layer_failure = any(s == "FAIL" for s in layer_statuses.values())
    if has_layer_failure and "confidence_outruns_evidence" not in hold_reasons:
        if epistemic_override is None:
            epistemic_override = "HYPOTHESIS"

    # CHECK 6: Sensing PASS but recognition/interpretation/memory FAIL
    # This is the Bekok Deep-1 pattern — data exists but wasn't recognized
    sensing_pass = layer_statuses.get("sensing") == "PASS"
    any_other_fail = any(
        layer_statuses.get(k) == "FAIL"
        for k in ["recognition", "interpretation_layer", "institutional_memory"]
    )
    if sensing_pass and any_other_fail:
        hold_reasons.append(
            "sensing_exists_but_not_recognized_or_interpreted"
        )

    # Determine final status
    is_hold = bool(hold_reasons)
    status = "888_HOLD" if is_hold else "PASS"

    return CoverageGateResult(
        status=status,
        level=level,
        coverage_score=score,
        confidence=confidence,
        confidence_gap=gap,
        confidence_outruns_evidence=manifest.confidence_outruns_evidence,
        layer_statuses=layer_statuses,
        hold_reasons=hold_reasons,
        epistemic_override=epistemic_override,
        message=(
            f"Coverage level: {level.value} (score={score:.2f}). "
            f"Confidence: {confidence:.2f}. Gap: {gap:.2f}. "
            f"Hold reasons: {', '.join(hold_reasons) if hold_reasons else 'none'}."
        ),
    )


def requires_coverage(min_level: CoverageLevel = CoverageLevel.PARTIAL):
    """
    Decorator that enforces coverage requirements for geopressure functions.

    The wrapped function must accept a `coverage_manifest` kwarg.
    If coverage is below minimum level, returns 888_HOLD dict.

    Args:
        min_level: Minimum required coverage level

    Returns:
        Decorated function
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manifest = kwargs.get("coverage_manifest")
            confidence = kwargs.get("confidence", 0.0)

            gate_result = check_coverage_gate(manifest, confidence)

            # Check if coverage level meets minimum
            level_order = [
                CoverageLevel.SUFFICIENT,
                CoverageLevel.PARTIAL,
                CoverageLevel.SPARSE,
                CoverageLevel.VOID,
            ]
            detected_idx = level_order.index(gate_result.level)
            required_idx = level_order.index(min_level)

            if detected_idx > required_idx:
                return {
                    "status": "888_HOLD",
                    "reason": "coverage_required",
                    "required_level": min_level.value,
                    "current_level": gate_result.level.value,
                    "coverage_score": gate_result.coverage_score,
                    "confidence": gate_result.confidence,
                    "confidence_gap": gate_result.confidence_gap,
                    "hold_reasons": gate_result.hold_reasons,
                    "message": gate_result.message,
                }

            # If qualitative layers failed, also HOLD regardless of score
            if gate_result.status == "888_HOLD":
                return {
                    "status": "888_HOLD",
                    "reason": "coverage_layer_failure",
                    "required_level": min_level.value,
                    "current_level": gate_result.level.value,
                    "coverage_score": gate_result.coverage_score,
                    "confidence": gate_result.confidence,
                    "confidence_gap": gate_result.confidence_gap,
                    "hold_reasons": gate_result.hold_reasons,
                    "epistemic_override": gate_result.epistemic_override,
                    "message": gate_result.message,
                }

            # Strip internal kwargs before calling wrapped function
            clean_kwargs = {
                k: v
                for k, v in kwargs.items()
                if not k.startswith("_coverage_")
            }
            return func(*args, **clean_kwargs)

        return wrapper

    return decorator
