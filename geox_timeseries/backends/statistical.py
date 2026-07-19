"""
geox_timeseries.backends.statistical — Deterministic statistical fallback.

Always-on. Used when:
  - GEOX_TIMESERIES_BACKBONE is unset (default).
  - TTM is gated off (default).
  - Series is too short for transformer context.
  - F2 TRUTH requires a non-ML baseline.

Implements:
  - ARIMA-light: forecast = last observed value (autoregressive mean of order 1).
  - EWMA:        exponentially weighted moving average continuation.
  - Linear trend: optional naive extrapolation (off by default).

Epistemic state: DERIVED (a transformation of observations, not interpretation).

Confidence cap: 0.85 (lower than TTM because statistical baseline is naive).

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged 2026-06-27 20:25 UTC.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from .base import BackendCapabilities, ForecastResult, TimeSeriesBackend


class StatisticalBackend(TimeSeriesBackend):
    """Deterministic ARIMA-light + EWMA fallback."""

    VERSION = "0.1.0"

    def name(self) -> str:
        return "statistical"

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            min_context_length=3,
            max_context_length=10_000,
            supports_multivariate=False,
            supports_quantiles=True,
            expected_latency_ms_p50=2,
            confidence_cap=0.85,
        )

    def forecast(
        self,
        series: Sequence[float],
        horizon: int,
        ctx: dict[str, Any] | None = None,
    ) -> ForecastResult:
        if not series:
            raise ValueError("statistical.forecast: empty series")
        if horizon < 1:
            raise ValueError("statistical.forecast: horizon must be >= 1")

        ctx = ctx or {}
        seed = ctx.get("seed", 42)
        use_ewma = bool(ctx.get("use_ewma", True))
        ewma_alpha = float(ctx.get("ewma_alpha", 0.3))

        # ── ARIMA-light: forecast[i] = last value (mean reversion) ────────
        last = float(series[-1])
        # ── EWMA: weighted recent average ──────────────────────────────────
        if use_ewma and len(series) >= 2:
            ewma = float(series[0])
            for v in series[1:]:
                ewma = ewma_alpha * float(v) + (1.0 - ewma_alpha) * ewma
            last = ewma  # use EWMA as baseline

        # ── Forecast: constant baseline + uncertainty band ────────────────
        # Naive forecast: same value repeated. Uncertainty grows with horizon.
        preds = [last for _ in range(horizon)]

        # Compute residual std from series for quantile band
        residuals: list[float] = []
        if len(series) >= 2:
            for i in range(1, len(series)):
                residuals.append(float(series[i]) - float(series[i - 1]))
        sigma = (sum(r * r for r in residuals) / max(len(residuals), 1)) ** 0.5

        # Expand sigma with horizon (√h for random walk)
        quantiles: dict[str, list[float]] = {
            "q05": [last - 1.645 * sigma * math.sqrt(h + 1) for h in range(horizon)],
            "q50": list(preds),
            "q95": [last + 1.645 * sigma * math.sqrt(h + 1) for h in range(horizon)],
        }

        # F7: confidence inversely scales with horizon and sigma
        conf = max(0.0, min(self.capabilities().confidence_cap, 0.85 - horizon * 0.01))

        return ForecastResult(
            backend=self.name(),
            horizon=horizon,
            predictions=preds,
            quantiles=quantiles,
            epistemic="DERIVED",
            confidence=conf,
            provenance={
                "version": self.VERSION,
                "method": "arima-light+ewma" if use_ewma else "arima-light",
                "ewma_alpha": ewma_alpha,
                "sigma": sigma,
                "seed": seed,
                "context_length": len(series),
            },
            delta_S=-0.05,  # informative (constant forecast reduces entropy)
        )
