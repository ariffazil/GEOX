"""
uncertainty_cascade.py — Confidence Propagation Math (D5)

DITEMPA BUKAN DIBERI — Forged, not given.

This module implements the uncertainty propagation functions used by the
BasinSynthesisPipeline to compute joint confidence across serial and parallel
stages.

Core rules (from the blueprint):
  - Serial stages:    confidence = ∏ conf_i       (multiplicative product)
  - Parallel stages:  confidence = 1 - ∏(1 - conf_i)  (noisy-or)
  - Cap at 0.90       (F7 HUMILITY — never claim certainty)

Edge cases:
  - Empty list → 0.0 confidence
  - Any 0.0 in serial → 0.0 product
  - Any 1.0 in parallel → 1.0 noisy-or
  - All values capped at 0.90 after computation

Pure functions — no I/O, no side effects, no Pydantic model mutation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# ─── Constants ────────────────────────────────────────────────────────────────

F7_CONFIDENCE_CAP: float = 0.90
"""F7 HUMILITY: confidence hard-capped at 0.90. Never claim certainty."""

# ─── Pure cascade functions ───────────────────────────────────────────────────


def cap_confidence(value: float) -> float:
    """Cap a confidence value at 0.90 per F7 HUMILITY.

    Args:
        value: Raw confidence (0.0–1.0)

    Returns:
        Capped confidence (max 0.90)
    """
    return min(value, F7_CONFIDENCE_CAP)


def cascade_serial(confidences: list[float]) -> float:
    """Propagate confidence through serial (dependent) stages.

    Serial = multiplicative product. If any stage has zero confidence,
    the joint confidence is zero (pipeline breaks).

    Args:
        confidences: List of per-stage confidence values (0.0–1.0)

    Returns:
        Joint confidence ∏ conf_i, capped at 0.90

    Example:
        cascade_serial([0.9, 0.8, 0.95]) → min(0.9 * 0.8 * 0.95, 0.90) = 0.684
    """
    if not confidences:
        return 0.0
    product = 1.0
    for conf in confidences:
        if conf <= 0.0:
            return 0.0
        product *= conf
    return cap_confidence(product)


def cascade_parallel(confidences: list[float]) -> float:
    """Propagate confidence through parallel (independent) stages.

    Parallel = independence union (product of complements).
    Equivalent to: 1 - ∏(1 - conf_i)

    Args:
        confidences: List of per-stage confidence values (0.0–1.0)

    Returns:
        Joint confidence, capped at 0.90

    Example:
        cascade_parallel([0.8, 0.7, 0.6]) → 1 - (0.2 * 0.3 * 0.4) = 0.976 → cap 0.90
    """
    if not confidences:
        return 0.0
    complement_product = 1.0
    for conf in confidences:
        complement_product *= 1.0 - max(conf, 0.0)
    return cap_confidence(1.0 - complement_product)


def cascade_noisy_or(confidences: list[float], leak: float = 0.0) -> float:
    """Noisy-OR gate for partially independent stages.

    Treats each stage as an independent cause that can reduce uncertainty.
    More conservative than pure product (serial) but more optimistic than
    independence union (parallel).

    noisy_or = 1 - ∏(1 - conf_i / (1 + leak))

    Args:
        confidences: List of per-stage confidence values (0.0–1.0)
        leak: Baseline noise factor (0.0 = pure noisy-or, higher = more conservative)

    Returns:
        Joint confidence, capped at 0.90
    """
    if not confidences:
        return 0.0
    complement = 1.0
    for conf in confidences:
        adjusted = max(conf, 0.0) / (1.0 + leak)
        complement *= 1.0 - adjusted
    return cap_confidence(1.0 - complement)


# ─── Composite cascade model ──────────────────────────────────────────────────


class UncertaintyCascade(BaseModel):
    """Structured uncertainty cascade — propagates confidence across pipeline stages.

    Holds the per-stage confidences and provides methods to compute
    joint confidence at any point in the pipeline.

    F7 HUMILITY: all output values capped at 0.90.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    basin_id: str = Field(default="", description="Canonical basin identifier")
    stage_confidences: dict[int, float] = Field(
        default_factory=dict,
        description="Per-stage confidence {stage_number: confidence_0_to_1}",
    )

    def set_stage(self, stage: int, confidence: float) -> None:
        """Set confidence for a pipeline stage."""
        self.stage_confidences[stage] = cap_confidence(confidence)

    def get_stage(self, stage: int) -> float:
        """Get confidence for a specific stage (0.0 if unset)."""
        return self.stage_confidences.get(stage, 0.0)

    def joint_confidence(self, stages: list[int] | None = None) -> float:
        """Compute joint confidence across specified (or all) stages via serial cascade.

        Args:
            stages: Specific stages to include (default: all registered stages, sorted)

        Returns:
            Serial-cascaded confidence, capped at 0.90
        """
        if stages is None:
            stages = sorted(self.stage_confidences.keys())
        confs = [self.get_stage(s) for s in stages]
        return cascade_serial(confs)

    def parallel_confidence(self, stages: list[int]) -> float:
        """Compute parallel (independent) confidence across specified stages.

        Args:
            stages: Stages to treat as independent

        Returns:
            Parallel-cascaded confidence, capped at 0.90
        """
        confs = [self.get_stage(s) for s in stages]
        return cascade_parallel(confs)

    @property
    def overall_confidence(self) -> float:
        """Overall pipeline confidence — serial cascade across all stages."""
        return self.joint_confidence()

    @property
    def stages_completed(self) -> int:
        """Number of stages with registered confidence."""
        return len(self.stage_confidences)

    def summary(self) -> dict[str, float | int | dict[int, float]]:
        """Return a summary dict for BasinSynthesisReport."""
        return {
            "overall_confidence": self.overall_confidence,
            "stages_completed": self.stages_completed,
            "per_stage": dict(sorted(self.stage_confidences.items())),
        }


__all__ = [
    "F7_CONFIDENCE_CAP",
    "cap_confidence",
    "cascade_serial",
    "cascade_parallel",
    "cascade_noisy_or",
    "UncertaintyCascade",
]
