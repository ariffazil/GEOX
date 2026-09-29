"""GEOX Seismic attribute primitives (L0 deterministic).

Per the GEOX Seismic Interpretation Forge Package, Slice 1 Step 4.
Every attribute primitive here:
- Consumes a 3D seismic volume (numpy ndarray, shape = (iline, xline, sample))
- Returns a 3D attribute volume of the same shape
- Holds UNKNOWN behavior if polarity is UNKNOWN (Canon #0 — every contract
  has a clear failure mode)
- Carries provenance: algorithm_id, parameters, parent hash

Implemented attributes:
- envelope              |analytic signal| amplitude
- instantaneous_phase    angle of analytic signal (radians)
- instantaneous_freq     derivative of unwrapped phase (Hz)
- rms_amplitude          windowed RMS amplitude
- sweetness              envelope / sqrt(frequency) (guarded)
- gst_dip                gradient structure tensor dip/azimuth
- gst_azimuth            azimuth of GST gradient
- coherence_semblance    normalized similarity (window-based)
- variance               windowed variance
- chaos                  1 - coherence (or entropy of GLCM)
- curvature_most_positive most-positive curvature from dip field
- curvature_most_negative most-negative curvature from dip field
- spectral_voice         spectral decomposition (STFT bandpass)

Reference: van der Baan & Fomel (2009), Chopra & Marfurt (2007).

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

from geox.seismic.attributes.analytic import (
    envelope,
    instantaneous_phase,
    instantaneous_frequency,
    sweetness,
)
from geox.seismic.attributes.amplitude import (
    rms_amplitude,
    variance,
)
from geox.seismic.attributes.dip import (
    gst_dip,
    gst_azimuth,
    gst_coherence,
)
from geox.seismic.attributes.chaos import chaos
from geox.seismic.attributes.curvature import (
    curvature_most_positive,
    curvature_most_negative,
)
from geox.seismic.attributes.spectral import spectral_voice

__all__ = [
    # Analytic-signal attributes
    "envelope",
    "instantaneous_phase",
    "instantaneous_frequency",
    "sweetness",
    # Amplitude attributes
    "rms_amplitude",
    "variance",
    # Dip/azimuth via gradient structure tensor
    "gst_dip",
    "gst_azimuth",
    "gst_coherence",
    # Discontinuity
    "chaos",
    # Curvature
    "curvature_most_positive",
    "curvature_most_negative",
    # Spectral
    "spectral_voice",
]
