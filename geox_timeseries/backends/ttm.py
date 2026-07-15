"""
geox_timeseries.backends.ttm — IBM Granite Tiny Time Mixer backend (FLAG-GATED).

Status: STUB — wireframe implementation.
Activation requires TWO env vars:
  GEOX_TIMESERIES_BACKBONE=ibm/granite-ttm
  GEOX_TIMESERIES_TTM_ENABLED=1

When gated, this backend RAISES RuntimeError on .forecast() call.
The registry returns a "ttm (gated)" entry in list_backends() so callers
can see it's available but must opt-in.

Reference:
  - IBM Granite TTM: https://huggingface.co/ibm/granite-ttm
  - Variants: granite-ttm-r1 (encoder-only), granite-ttm-r2 (encoder-decoder)
  - Default context length: 512 (R1) / 1024 (R2)

Constitutional notes:
  - F2 TRUTH: epistemic state = INTERPRETED (transformer output, not observation).
  - F7 HUMILITY: confidence capped at 0.90 (default for ML backbones).
  - F11 AUDIT: provenance records model variant, revision, tokenizer hash.

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged 2026-06-27 20:25 UTC.
"""

from __future__ import annotations

import os
from typing import Any, Sequence

from .base import BackendCapabilities, ForecastResult, TimeSeriesBackend


class TTMBackend(TimeSeriesBackend):
    """IBM Granite Tiny Time Mixer — flag-gated transformer backend."""

    VERSION = "0.1.0-stub"

    # Default model id; can be overridden via GEOX_TIMESERIES_TTM_MODEL env var.
    DEFAULT_MODEL_ID = "ibm/granite-ttm-r1"

    def __init__(self, model_id: str | None = None) -> None:
        self._model_id = model_id or os.getenv("GEOX_TIMESERIES_TTM_MODEL", self.DEFAULT_MODEL_ID)

    def name(self) -> str:
        return "ibm/granite-ttm"

    def capabilities(self) -> BackendCapabilities:
        # Granite-TTM defaults: context up to 512 (R1) / 1024 (R2),
        # multivariate, quantiles via MC-dropout.
        return BackendCapabilities(
            min_context_length=10,
            max_context_length=512,
            supports_multivariate=True,
            supports_quantiles=True,
            expected_latency_ms_p50=120,
            confidence_cap=0.90,
        )

    def _assert_enabled(self) -> None:
        """Raise if TTM is not enabled via env gates.

        Hard gates:
          GEOX_TIMESERIES_BACKBONE == 'ibm/granite-ttm'
          GEOX_TIMESERIES_TTM_ENABLED == '1'
        """
        if os.getenv("GEOX_TIMESERIES_BACKBONE") != "ibm/granite-ttm":
            raise RuntimeError("ttm.forecast: backbone not selected. Set GEOX_TIMESERIES_BACKBONE=ibm/granite-ttm to use TTM.")
        if os.getenv("GEOX_TIMESERIES_TTM_ENABLED") != "1":
            raise RuntimeError(
                "ttm.forecast: TTM not enabled. Set GEOX_TIMESERIES_TTM_ENABLED=1 to enable (F2 TRUTH: explicit opt-in)."
            )

    def forecast(
        self,
        series: Sequence[float],
        horizon: int,
        ctx: dict[str, Any] | None = None,
    ) -> ForecastResult:
        # ── F2 TRUTH + F4 CLARITY: fail loud when gated off ─────────────────
        self._assert_enabled()

        if not series:
            raise ValueError("ttm.forecast: empty series")
        if horizon < 1:
            raise ValueError("ttm.forecast: horizon must be >= 1")

        # ── Stub: defer to statistical baseline for the actual computation ──
        # When the real TTM inference is wired, replace this block with:
        #   - tokenizer/normalizer
        #   - encoder forward pass
        #   - MC-dropout for quantiles
        #   - denormalization
        # The statistical fallback keeps the bridge honest:
        # the constitutional lane works even before TTM is wired.
        from .statistical import StatisticalBackend

        delegate = StatisticalBackend()
        result = delegate.forecast(series, horizon, ctx)

        # ── Annotate result with TTM provenance (F11 AUDIT) ───────────────
        result.backend = self.name()
        result.epistemic = "INTERPRETED"  # F2: transformer output is interpretation
        result.confidence = min(
            self.capabilities().confidence_cap,
            max(result.confidence, 0.0),
        )
        result.provenance.update(
            {
                "model_id": self._model_id,
                "backend_version": self.VERSION,
                "method": "ttm-delegate-to-statistical-stub",
                "wire_status": "STUB",
                "note": (
                    "STUB: TTM inference not wired. Delegates to statistical "
                    "baseline so the constitutional lane works. Replace with "
                    "real encoder forward pass when ibm/granite-ttm is loaded."
                ),
            }
        )
        result.delta_S = -0.10
        return result
