"""
geox_timeseries — Time-series forecasting backends for GEOX.

Purpose
═══════
Provide pluggable backends for time-series forecasting tasks
(production forecasting, anomaly detection, multivariate dynamics).
Backbones are selected via the `GEOX_TIMESERIES_BACKBONE` environment
variable and the `geox_timeseries.backends.registry` module.

Backends
════════
  statistical     — always-on, deterministic fallback (ARIMA-light, simple EWMA).
  ttm             — IBM Granite Tiny Time Mixer (transformer).
                    FLAG-GATED: requires GEOX_TIMESERIES_BACKBONE=ibm/granite-ttm
                    and explicit GEOX_TIMESERIES_TTM_ENABLED=1.
  (future) tsmix  — xLSTM/TSMix for long-context forecasting.

Constitutional Lane
═══════════════════
  Organ:   GEOX (earth_evidence)
  Authority: EVIDENCE_ONLY (no state mutation; advisory outputs only)
  Bridge:   Blueprint see /root/AAA/docs/architecture/ASSETOPSBENCH_BRIDGE.md
            (TokenRouter policy: /root/tokenrouter/policies/geox.yaml)
  Floor binding:
    F1 AMANAH  — all outputs reversible; no writes
    F2 TRUTH   — epistemic ladder OBSERVED → DERIVED → INTERPRETED → HYPOTHESIS
    F4 CLARITY — one source of truth per field
    F7 HUMILITY — confidence capped at 0.90
    F9 ANTI-HANTU — no metaphor as fact
    F11 AUDIT  — every forecast has provenance

DITEMPA BUKAN DIBERI — Forged, Not Given.
Forged 2026-06-27 20:25 UTC by FORGE (000Ω) → 333-AGI.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backends.base import TimeSeriesBackend


__version__ = "0.1.0"
__all__ = ["select_backend", "list_backends"]


def select_backend(name: str | None = None) -> TimeSeriesBackend:
    """Select a backend by name (or env default).

    Args:
        name: Optional backend name override. If None, reads
              GEOX_TIMESERIES_BACKBONE env var; defaults to 'statistical'.

    Returns:
        The selected backend instance.

    Raises:
        ValueError: If the requested backend is unknown.
        RuntimeError: If the backend is gated and not enabled.
    """
    # Local import to avoid hard dependency at module import time.
    from .registry import build_backend

    return build_backend(name)


def list_backends() -> list[dict]:
    """List available backbones with their gating status.

    Returns:
        List of dicts with keys: name, enabled, source, gate_reason.
    """
    from .registry import list_available

    return list_available()
