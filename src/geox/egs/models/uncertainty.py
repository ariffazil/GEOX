"""
uncertainty.py — Uncertainty Algebra for EGS
==============================================
GEOX EGS: Interval, distribution, scenario-set uncertainty.
Epistemic vs Aleatory flags. First-class uncertainty on every earth value.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ═══════════════════════════════════════════════════════════════════════════════
# Uncertainty Classification
# ═══════════════════════════════════════════════════════════════════════════════


class UncertaintyNature(StrEnum):
    """Epistemic (reducible by more data) vs Aleatory (irreducible randomness)."""

    EPISTEMIC = "epistemic"
    ALEATORY = "aleatory"
    MIXED = "mixed"


class UncertaintyKind(StrEnum):
    """Structural form of the uncertainty representation."""

    INTERVAL = "interval"
    DISTRIBUTION = "distribution"
    SCENARIO_SET = "scenario_set"
    DISCRETE = "discrete"
    UNKNOWN = "unknown"


class ConfidenceGrade(StrEnum):
    """Grade of confidence based on evidence quality."""

    AAA = "AAA"  # Direct measurement, calibrated
    AA = "AA"  # Multiple independent lines of evidence
    A = "A"  # Single good measurement
    B = "B"  # Interpreted with constraints
    C = "C"  # Regional analogue / best guess
    D = "D"  # Speculative
    INFERRED = "inferred"
    NOT_GRADED = "not_graded"


# ═══════════════════════════════════════════════════════════════════════════════
# Uncertainty Models
# ═══════════════════════════════════════════════════════════════════════════════


class IntervalUncertainty(BaseModel):
    """Interval-based uncertainty: a value with min/max bounds."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal[UncertaintyKind.INTERVAL] = UncertaintyKind.INTERVAL
    value: float = Field(..., description="Best estimate / P50")
    lower_bound: float = Field(..., description="Minimum plausible value")
    upper_bound: float = Field(..., description="Maximum plausible value")
    confidence_pct: float = Field(default=90.0, ge=0.0, le=100.0, description="Confidence that true value lies within bounds")
    unit: str = Field(default="", description="Physical unit")
    nature: UncertaintyNature = UncertaintyNature.EPISTEMIC

    @model_validator(mode="after")
    def _validate_bounds(self) -> IntervalUncertainty:
        if self.upper_bound <= self.lower_bound:
            raise ValueError(f"upper_bound ({self.upper_bound}) must be > lower_bound ({self.lower_bound})")
        if self.value < self.lower_bound or self.value > self.upper_bound:
            raise ValueError(f"value ({self.value}) must be within bounds [{self.lower_bound}, {self.upper_bound}]")
        return self

    @property
    def range(self) -> float:
        return self.upper_bound - self.lower_bound

    @property
    def relative_uncertainty(self) -> float:
        """Coefficient of variation approximation: range / (2 * |value|)."""
        if abs(self.value) < 1e-12:
            return float("inf")
        return self.range / (2 * abs(self.value))


class DistributionType(StrEnum):
    """Supported parametric distributions."""

    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    PERT = "pert"
    BETA = "beta"
    EMPIRICAL = "empirical"


class DistributionUncertainty(BaseModel):
    """Distribution-based uncertainty with parametric specification."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal[UncertaintyKind.DISTRIBUTION] = UncertaintyKind.DISTRIBUTION
    dist_type: DistributionType = Field(..., description="Distribution family")
    # Normal/lognormal params
    mean: float | None = Field(default=None)
    std: float | None = Field(default=None, ge=0.0)
    # Uniform params
    min_val: float | None = Field(default=None)
    max_val: float | None = Field(default=None)
    # Triangular/PERT params
    mode_val: float | None = Field(default=None)
    low_val: float | None = Field(default=None)
    high_val: float | None = Field(default=None)
    # Common
    p10: float | None = Field(default=None, description="10th percentile")
    p50: float | None = Field(default=None, description="50th percentile / median")
    p90: float | None = Field(default=None, description="90th percentile")
    unit: str = Field(default="")
    nature: UncertaintyNature = UncertaintyNature.ALEATORY
    n_samples: int | None = Field(default=None, description="Number of samples (empirical)")

    @model_validator(mode="after")
    def _validate_distribution(self) -> DistributionUncertainty:
        if self.dist_type == DistributionType.NORMAL:
            if self.mean is None or self.std is None:
                raise ValueError("Normal requires mean and std")
        elif self.dist_type == DistributionType.UNIFORM:
            if self.min_val is None or self.max_val is None:
                raise ValueError("Uniform requires min_val and max_val")
            if self.max_val <= self.min_val:
                raise ValueError("max_val must be > min_val")
        elif self.dist_type in (DistributionType.TRIANGULAR, DistributionType.PERT):
            if self.low_val is None or self.high_val is None or self.mode_val is None:
                raise ValueError(f"{self.dist_type} requires low_val, mode_val, high_val")
        return self

    @property
    def p10_p50_p90(self) -> tuple[float, float, float] | None:
        """Return (P10, P50, P90) if available."""
        if self.p10 is not None and self.p50 is not None and self.p90 is not None:
            return (self.p10, self.p50, self.p90)
        return None


class ScenarioMember(BaseModel):
    """A single scenario within a scenario set."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="Scenario name")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability weight")
    description: str = Field(default="", description="Scenario description")
    assumptions: list[str] = Field(default_factory=list, description="Key assumptions")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Scenario-specific values")


class ScenarioSet(BaseModel):
    """Discrete scenario set: multiple competing interpretations with probabilities."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal[UncertaintyKind.SCENARIO_SET] = UncertaintyKind.SCENARIO_SET
    scenarios: list[ScenarioMember] = Field(..., min_length=1, description="At least one scenario")
    description: str = Field(default="", description="What these scenarios represent")
    nature: UncertaintyNature = UncertaintyNature.EPISTEMIC
    base_case_index: int = Field(default=0, description="Index of the base case scenario")

    @model_validator(mode="after")
    def _probabilities_sum(self) -> ScenarioSet:
        total = sum(s.probability for s in self.scenarios)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Scenario probabilities must sum to 1.0, got {total:.4f}")
        if self.base_case_index < 0 or self.base_case_index >= len(self.scenarios):
            raise ValueError(f"base_case_index {self.base_case_index} out of range")
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# Unified Uncertainty Wrapper
# ═══════════════════════════════════════════════════════════════════════════════


UncertaintyBody = IntervalUncertainty | DistributionUncertainty | ScenarioSet


class UncertainValue(BaseModel):
    """A value with explicit uncertainty — the fundamental EGS data type."""

    model_config = ConfigDict(extra="forbid")
    label: str = Field(default="", description="What this value represents")
    value: float | None = Field(default=None, description="Best estimate / point value")
    uncertainty: UncertaintyBody = Field(..., discriminator="kind", description="Uncertainty model")
    grade: ConfidenceGrade = Field(default=ConfidenceGrade.NOT_GRADED, description="Confidence grade")
    source: str = Field(default="", description="Source of this value")

    @property
    def nature(self) -> UncertaintyNature:
        return self.uncertainty.nature

    @property
    def p50(self) -> float | None:
        """Extract P50 from whatever uncertainty form."""
        if isinstance(self.uncertainty, IntervalUncertainty):
            return self.uncertainty.value
        elif isinstance(self.uncertainty, DistributionUncertainty):
            return self.uncertainty.p50 or self.uncertainty.mean
        elif isinstance(self.uncertainty, ScenarioSet):
            return self.uncertainty.scenarios[self.uncertainty.base_case_index].parameters.get("value", self.value)
        return self.value


class UncertaintyBudget(BaseModel):
    """A collection of UncertainValues forming an uncertainty budget for a computation."""

    model_config = ConfigDict(extra="forbid")
    items: dict[str, UncertainValue] = Field(default_factory=dict, description="Named uncertainty items")
    description: str = Field(default="")
    created_at: str = Field(default="")

    def add(self, name: str, uv: UncertainValue) -> None:
        self.items[name] = uv

    def get(self, name: str) -> UncertainValue | None:
        return self.items.get(name)
