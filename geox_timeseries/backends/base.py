"""
geox_timeseries.backends.base — Abstract interface for all time-series backends.

Every backbone (statistical, TTM, future) implements this interface.
The interface is intentionally narrow: forecast → ForecastResult.
This keeps the constitutional abstraction layer thin.

Contract:
    forecast(series, horizon, ctx) -> ForecastResult
    name() -> str
    capabilities() -> BackendCapabilities

F2 TRUTH: every forecast must declare its epistemic state (OBSERVED, DERIVED,
INTERPRETED, HYPOTHESIS). The backbone knows which it produces.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class BackendCapabilities:
    """What the backbone can do. Used by callers to decide fit-for-purpose."""

    min_context_length: int
    max_context_length: int
    supports_multivariate: bool
    supports_quantiles: bool
    expected_latency_ms_p50: int
    confidence_cap: float = 0.90  # F7 HUMILITY hard cap


@dataclass
class ForecastResult:
    """Single canonical forecast result envelope.

    Fields:
        backend:        Backbone name (e.g. "statistical", "ibm/granite-ttm").
        horizon:        Forecast steps ahead.
        predictions:    Point predictions, length == horizon.
        quantiles:      Optional dict (q05, q50, q95) for uncertainty band.
        epistemic:      OBSERVED | DERIVED | INTERPRETED | HYPOTHESIS.
        confidence:     0.0–0.90 (F7 cap).
        provenance:     dict with backbone version, model id, etc.
        delta_S:        Entropy delta for the forecast (negative = informative).
    """

    backend: str
    horizon: int
    predictions: list[float]
    quantiles: dict[str, list[float]] = field(default_factory=dict)
    epistemic: str = "DERIVED"
    confidence: float = 0.0
    provenance: dict[str, Any] = field(default_factory=dict)
    delta_S: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "horizon": self.horizon,
            "predictions": list(self.predictions),
            "quantiles": dict(self.quantiles),
            "epistemic": self.epistemic,
            "confidence": min(self.confidence, 0.90),  # F7 cap
            "provenance": dict(self.provenance),
            "delta_S": float(self.delta_S),
        }


class TimeSeriesBackend(ABC):
    """Abstract base for all time-series backends.

    Implementations MUST:
      - Be deterministic when seeded.
      - Declare their epistemic state honestly.
      - Cap confidence at 0.90 (F7 HUMILITY).
      - Never mutate input series.
      - Record provenance (model version, params, seed).
    """

    @abstractmethod
    def name(self) -> str:
        """Backbone identifier (e.g. 'statistical', 'ibm/granite-ttm')."""

    @abstractmethod
    def capabilities(self) -> BackendCapabilities:
        """Declare what the backbone supports."""

    @abstractmethod
    def forecast(
        self,
        series: Sequence[float],
        horizon: int,
        ctx: dict[str, Any] | None = None,
    ) -> ForecastResult:
        """Produce a forecast.

        Args:
            series:  Observed time-series values (chronological order).
            horizon: Number of steps ahead to predict.
            ctx:     Optional context (seed, exogenous variables, etc.).

        Returns:
            ForecastResult with predictions, epistemic label, confidence, provenance.

        Raises:
            ValueError: If series is empty or horizon < 1.
        """
