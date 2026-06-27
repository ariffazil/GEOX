"""
geox_timeseries.registry — Backend selector and availability probe.

Reads GEOX_TIMESERIES_BACKBONE env var to choose the active backend.
Default: 'statistical' (always-on, deterministic fallback).

Public API:
    build_backend(name=None) -> TimeSeriesBackend
    list_available() -> list[dict]  (with name, enabled, source, gate_reason)
    is_enabled(backbone_name) -> bool

F2 TRUTH: registry reports gating honestly. A gated backbone that hasn't
been opted into appears as "available but not enabled" in list_available().

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import os
from typing import Any

from .backends.base import TimeSeriesBackend
from .backends.statistical import StatisticalBackend
from .backends.ttm import TTMBackend


# ── Default selection ──────────────────────────────────────────────────────
DEFAULT_BACKBONE = "statistical"


def build_backend(name: str | None = None) -> TimeSeriesBackend:
    """Construct a backend by name (or env default).

    Args:
        name: Optional override. If None, reads GEOX_TIMESERIES_BACKBONE
              env var; defaults to 'statistical'.

    Returns:
        Instantiated TimeSeriesBackend.

    Raises:
        ValueError: If the backbone name is unknown.
        RuntimeError: If the backbone is gated and env opt-in is missing.
    """
    selected = (name or os.getenv("GEOX_TIMESERIES_BACKBONE") or DEFAULT_BACKBONE).strip()

    if selected == "statistical":
        return StatisticalBackend()

    if selected == "ibm/granite-ttm":
        backend = TTMBackend()
        # Trigger gate check (raises if not enabled) so callers fail fast.
        backend._assert_enabled()  # noqa: SLF001 — intentional gate assertion
        return backend

    raise ValueError(f"unknown backbone: {selected!r}. Available: 'statistical', 'ibm/granite-ttm'.")


def is_enabled(backbone_name: str) -> bool:
    """Check whether a backbone is currently enabled (gates passed)."""
    if backbone_name == "statistical":
        return True
    if backbone_name == "ibm/granite-ttm":
        return os.getenv("GEOX_TIMESERIES_BACKBONE") == "ibm/granite-ttm" and os.getenv("GEOX_TIMESERIES_TTM_ENABLED") == "1"
    return False


def list_available() -> list[dict[str, Any]]:
    """List available backbones with their gating status.

    Returns:
        List of dicts with keys:
          - name:        backbone identifier
          - enabled:     whether it's currently active
          - source:      built-in | remote
          - gate_reason: explanation if gated
    """
    out: list[dict[str, Any]] = []

    out.append(
        {
            "name": "statistical",
            "enabled": True,
            "source": "built-in",
            "gate_reason": None,
        }
    )

    ttm_enabled = is_enabled("ibm/granite-ttm")
    out.append(
        {
            "name": "ibm/granite-ttm",
            "enabled": ttm_enabled,
            "source": "remote" if ttm_enabled else "remote (flag-gated)",
            "gate_reason": (
                None
                if ttm_enabled
                else "Set GEOX_TIMESERIES_BACKBONE=ibm/granite-ttm AND GEOX_TIMESERIES_TTM_ENABLED=1 to activate."
            ),
        }
    )

    return out
