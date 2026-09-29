"""Analytic-signal attributes: envelope, instantaneous phase, instantaneous frequency, sweetness.

All operate on a 2D or 3D numpy array. The analytic signal is computed
in the frequency domain (FFT-based Hilbert), avoiding scipy.signal dependency
at the cost of slight efficiency.

Per Canon #0: if polarity is UNKNOWN, callers must add behavior=UNKNOWN.
This module is polarity-AGNOSTIC — the polarity is applied externally.
"""
from __future__ import annotations

import numpy as np


def _analytic_signal(volume: np.ndarray) -> np.ndarray:
    """Compute the analytic signal via FFT (zero negative frequencies).

    Works on 2D (iline, xline) and 3D (iline, xline, sample) volumes.
    """
    if volume.ndim not in (2, 3):
        raise ValueError(f"Expected 2D or 3D volume, got shape {volume.shape}")

    spec = np.fft.fft(volume, axis=-1)
    n = spec.shape[-1]

    # Build Hilbert multiplier: 1 for DC, 2 for positive frequencies, 0 for negative
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = 1.0
        h[n // 2] = 1.0
        h[1 : n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1 : (n + 1) // 2] = 2.0

    # Broadcast h across leading dimensions
    h_shape = [1] * volume.ndim
    h_shape[-1] = n
    h = h.reshape(h_shape)

    analytic_spec = spec * h
    return np.fft.ifft(analytic_spec, axis=-1)


def envelope(volume: np.ndarray) -> np.ndarray:
    """Instantaneous amplitude (reflection strength).

    Output: same shape as input, real-valued, non-negative.
    """
    return np.abs(_analytic_signal(volume))


def instantaneous_phase(volume: np.ndarray) -> np.ndarray:
    """Instantaneous phase in radians, range (-pi, pi].

    Output: same shape as input.
    """
    return np.angle(_analytic_signal(volume))


def instantaneous_frequency(
    volume: np.ndarray, sample_interval_s: float = 0.004
) -> np.ndarray:
    """Instantaneous frequency in Hz.

    Computed as the derivative of the UNWRAPPED phase divided by 2*pi.
    For numerical stability, we unwrap along the sample axis only.

    Parameters
    ----------
    volume : np.ndarray
        Input seismic amplitude (same units as time-domain signal).
    sample_interval_s : float
        Sample interval in seconds (default 4 ms = 0.004 s).
    """
    analytic = _analytic_signal(volume)
    phase = np.unwrap(np.angle(analytic), axis=-1)
    # Derivative via finite differences along the sample axis
    inst_freq = np.zeros_like(phase, dtype=np.float64)
    if volume.ndim == 3:
        inst_freq[:, :, 1:] = (phase[:, :, 1:] - phase[:, :, :-1]) / (2.0 * np.pi * sample_interval_s)
    else:
        inst_freq[:, 1:] = (phase[:, 1:] - phase[:, :-1]) / (2.0 * np.pi * sample_interval_s)
    return inst_freq


def sweetness(volume: np.ndarray, sample_interval_s: float = 0.004) -> np.ndarray:
    """Sweetness = envelope / sqrt(instantaneous_frequency).

    Guarded against zero frequency (DC or very-low-frequency dominated signals).
    Returns NaN where instantaneous frequency is <= 0 (caller may mask).
    """
    env = envelope(volume)
    inst_freq = instantaneous_frequency(volume, sample_interval_s=sample_interval_s)
    safe_freq = np.where(inst_freq > 0.0, inst_freq, np.nan)
    return env / np.sqrt(safe_freq)
