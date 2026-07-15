"""
geox_timeseries.backends — Backend implementations for time-series forecasting.

Each backend implements the TimeSeriesBackend abstract interface.

Available backbones (as of 2026-06-27):

  statistical
    Status: ALWAYS ON
    Source: built-in
    Use:    deterministic fallback for short-horizon, low-variance signals.
    Implements: ARIMA-light (autoregressive mean), EWMA (exponentially weighted).

  ttm
    Status: FLAG-GATED (OFF by default)
    Source: ibm/granite-ttm (IBM Granite Tiny Time Mixer, R1 / R2 variants)
    Gate:   GEOX_TIMESERIES_BACKBONE=ibm/granite-ttm AND
            GEOX_TIMESERIES_TTM_ENABLED=1
    Use:    multivariate forecasting, long-context dynamics, attention residual.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from .base import BackendCapabilities, ForecastResult, TimeSeriesBackend

__all__ = ["TimeSeriesBackend", "BackendCapabilities", "ForecastResult"]
