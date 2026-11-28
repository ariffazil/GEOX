"""Chaos attribute — discontinuity measure, complement to coherence.

chaos = 1 - coherence

Per the Copilot forge prompt, chaos has multiple definitions across
vendors — we use the canonical 1 - coherence definition (Bahorich & Farmer
1995, normalized to [0, 1]).
"""
from __future__ import annotations

import numpy as np

from geox.seismic.attributes.dip import gst_coherence


def chaos(volume: np.ndarray, window_size: int = 5, sigma: float = 1.0) -> np.ndarray:
    """Chaos = 1 - gst_coherence, clipped to [0, 1].

    Per Canon #0: when contrast is undefined (polarity UNKNOWN), the caller
    must add behavior=UNKNOWN. This function is polarity-agnostic; callers
    apply the polarity gate.
    """
    coherence = gst_coherence(volume, window_size=window_size, sigma=sigma)
    return np.clip(1.0 - coherence, 0.0, 1.0)
