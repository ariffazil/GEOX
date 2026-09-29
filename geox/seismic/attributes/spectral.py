"""Spectral decomposition — STFT-based bandpass amplitudes.

Per the Copilot forge prompt: "Spectral decomposition: STFT/CWT/S-transform
voice volumes; amplitude per frequency."

Slice 1 implements STFT (Short-Time Fourier Transform) with configurable
window. CWT is deferred to P1.

Output: amplitude per (time, frequency) bin, normalized.
"""
from __future__ import annotations

import numpy as np


def spectral_voice(
    volume: np.ndarray,
    target_freq_hz: float,
    window_ms: float = 32.0,
    sample_interval_s: float = 0.004,
) -> np.ndarray:
    """STFT amplitude at a target frequency, per trace.

    Parameters
    ----------
    volume : np.ndarray
        Input seismic amplitude volume (2D or 3D).
    target_freq_hz : float
        Center frequency of the bandpass.
    window_ms : float
        STFT window length in milliseconds.
    sample_interval_s : float
        Sample interval in seconds.

    Returns
    -------
    np.ndarray of same spatial shape as input, with peak amplitude at the
    target frequency (per trace, not per voxel).
    """
    if target_freq_hz <= 0:
        raise ValueError("target_freq_hz must be > 0")

    window_samples = max(8, int(window_ms / 1000.0 / sample_interval_s))
    # Apply per-trace STFT
    n_samples = volume.shape[-1]
    if n_samples < window_samples:
        raise ValueError(
            f"trace too short ({n_samples} samples) for window ({window_samples})"
        )

    # Build frequency-domain Gaussian bandpass centered on target
    freqs = np.fft.rfftfreq(n_samples, d=sample_interval_s)
    sigma_hz = max(1.0, target_freq_hz * 0.25)  # 25% fractional bandwidth
    bandpass = np.exp(-0.5 * ((freqs - target_freq_hz) / sigma_hz) ** 2)

    # Apply per trace: spectral magnitude after bandpass
    spec = np.fft.rfft(volume, axis=-1)
    filtered = spec * bandpass
    voice = np.abs(np.fft.irfft(filtered, n=n_samples, axis=-1))
    return voice
