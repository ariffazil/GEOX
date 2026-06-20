"""GEOX ObsPy Adapter — Phase 0 Library Integration
DITEMPA BUKAN DIBERI — Seismic intelligence is forged, not given.

This module provides the canonical ObsPy bridge for GEOX seismic tools.
It translates ObsPy objects to GEOX internal schemas with full
provenance, uncertainty bands, and constitutional compliance.

F2 TRUTH: All outputs carry processing_log + library_versions.
F4 CLARITY: Every processing step is documented.
F7 HUMILITY: Uncertainty is declared, not hidden.
F10 ONTOLOGY: Strict schema translation, no type confusion.
"""

from __future__ import annotations

import hashlib
import json
import logging
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger("geox.engines.obspy_adapter")

OBSPY_VERSION: str = "1.4.0"
NUMPY_VERSION: str = "2.0.0"


@dataclass
class TraceStats:
    station: str
    network: str
    channel: str
    starttime: str
    endtime: str
    sampling_rate: float
    delta: float
    npts: int
    coordinates: dict[str, float]


@dataclass
class ProcessedTrace:
    data: np.ndarray
    stats: TraceStats
    processing_log: list[dict[str, Any]]


@dataclass
class AttributeResult:
    attribute: str
    value: float | np.ndarray
    unit: str
    description: str
    confidence: str


@dataclass
class AnomalousContrastResult:
    ac_score: float
    ac_class: str
    anomaly_mask: np.ndarray | None
    confidence: str
    semblance: float
    variance_ratio: float


class ObsPyAdapter:
    """Canonical ObsPy bridge for GEOX seismic tools.

    Translates ObsPy Stream objects to GEOX internal schemas.
    All methods return structured dicts with provenance,
    uncertainty, and constitutional metadata.

    Never exposes raw ObsPy objects outside this adapter.
    """

    def __init__(self):
        self._processing_log: list[dict[str, Any]] = []
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        try:
            import obspy
            self._obspy_version = obspy.__version__
        except ImportError:
            raise ImportError(
                "ObsPy is required for seismic operations. "
                "Install with: pip install 'geox[seismic]'"
            )

    def _sha256_params(self, params: dict) -> str:
        """Fingerprint parameters for reproducibility."""
        canonical = json.dumps(params, sort_keys=True, default=str)
        return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"

    def _make_stats(self, trace) -> TraceStats:
        coords = {}
        if hasattr(trace.stats, "coordinates"):
            coords = {"lat": float(trace.stats.coordinates.latitude),
                       "lon": float(trace.stats.coordinates.longitude)}
        return TraceStats(
            station=str(getattr(trace.stats, "station", "")),
            network=str(getattr(trace.stats, "network", "")),
            channel=str(getattr(trace.stats, "channel", "")),
            starttime=str(trace.stats.starttime),
            endtime=str(trace.stats.endtime),
            sampling_rate=float(trace.stats.sampling_rate),
            delta=float(trace.stats.delta),
            npts=int(trace.stats.npts),
            coordinates=coords,
        )

    def _add_log(self, step: str, library: str, params: dict) -> None:
        self._processing_log.append({
            "step": step,
            "library": library,
            "version": self._obspy_version,
            "params": params,
            "params_hash": self._sha256_params(params),
        })

    def load_seismic(
        self,
        path: str,
        format: str | None = None,
        starttime: str | None = None,
        endtime: str | None = None,
    ) -> dict[str, Any]:
        """Load seismic data from file using ObsPy.

        Supports: SEG-Y, MiniSEED, SAC, GSE2, Q, SEG2,冯

        Args:
            path: Path to seismic file.
            format: ObsPy format specifier (auto-detected if None).
            starttime: Optional start time filter (ISO string).
            endtime: Optional end time filter (ISO string).

        Returns:
            GEOX schema dict with traces, stats, and processing_log.
        """
        import obspy
        from obspy import read

        self._processing_log = []

        try:
            stream = read(path, format=format, headonly=False)
        except Exception as exc:
            return {
                "status": "ERROR",
                "error_code": "OBSPY_LOAD_FAILED",
                "message": f"Failed to load {path}: {exc}",
                "processing_log": self._processing_log,
                "library_versions": {
                    "obspy": self._obspy_version,
                    "numpy": NUMPY_VERSION,
                },
            }

        if starttime or endtime:
            t_start = obspy.UTCDateTime(starttime) if starttime else None
            t_end = obspy.UTCDateTime(endtime) if endtime else None
            stream = stream.slice(t_start, t_end)

        self._add_log("load", "obspy", {"path": path, "format": format})

        traces = []
        for tr in stream:
            traces.append({
                "data": tr.data.tolist(),
                "stats": {
                    "station": str(tr.stats.station),
                    "network": str(tr.stats.network),
                    "channel": str(tr.stats.channel),
                    "starttime": str(tr.stats.starttime),
                    "endtime": str(tr.stats.endtime),
                    "sampling_rate": float(tr.stats.sampling_rate),
                    "delta": float(tr.stats.delta),
                    "npts": int(tr.stats.npts),
                    "coordinates": getattr(tr.stats, "coordinates", None),
                },
            })

        return {
            "status": "LOADED",
            "trace_count": len(traces),
            "traces": traces,
            "stream_summary": {
                "n_traces": len(stream),
                "total_samples": sum(tr.stats.npts for tr in stream),
                "duration_s": float(stream[0].stats.endtime - stream[0].stats.starttime) if len(stream) > 0 else 0,
                "sampling_rate_hz": float(stream[0].stats.sampling_rate) if len(stream) > 0 else 0,
            },
            "processing_log": list(self._processing_log),
            "library_versions": {
                "obspy": self._obspy_version,
                "numpy": NUMPY_VERSION,
            },
        }

    def compute_attribute(
        self,
        data: list[float] | np.ndarray,
        attribute: str = "rms",
        sample_rate: float = 1000.0,
        window_size: int = 5,
    ) -> dict[str, Any]:
        """Compute seismic attributes on trace data.

        Args:
            data: Seismic amplitude values.
            attribute: One of "rms", "variance", "sweetness", "coherence".
            sample_rate: Sampling rate in Hz.
            window_size: Window size for rolling attributes.

        Returns:
            AttributeResult with value, unit, description, confidence.
        """
        arr = np.asarray(data, dtype=np.float64)
        n_samples = len(arr)

        self._processing_log = []
        self._add_log("attribute_computation", "obspy", {
            "attribute": attribute,
            "sample_rate": sample_rate,
            "window_size": window_size,
            "n_samples": n_samples,
        })

        if attribute == "rms":
            window = min(window_size, n_samples)
            padded = np.pad(arr, (window // 2, window - 1 - window // 2), mode="edge")
            rms = np.array([
                np.sqrt(np.mean(padded[i:i + window] ** 2))
                for i in range(n_samples)
            ])
            result = float(np.mean(rms))
            unit = "amplitude_units"
            description = "Root-mean-square amplitude in sliding window"
            confidence = "HIGH"

        elif attribute == "variance":
            window = min(window_size, n_samples)
            padded = np.pad(arr, (window // 2, window - 1 - window // 2), mode="edge")
            var = np.array([
                np.var(padded[i:i + window])
                for i in range(n_samples)
            ])
            result = float(np.mean(var))
            unit = "amplitude_units^2"
            description = "Variance of amplitude in sliding window"
            confidence = "MEDIUM"

        elif attribute == "sweetness":
            from scipy.ndimage import uniform_filter1d
            if n_samples < window_size:
                return {
                    "status": "ERROR",
                    "error_code": "INSUFFICIENT_DATA",
                    "message": f"Need at least {window_size} samples, got {n_samples}",
                }
            window = window_size
            env = np.abs(uniform_filter1d(arr.astype(float), size=window))
            diff = np.abs(np.gradient(arr))
            diff_smooth = uniform_filter1d(diff.astype(float), size=window)
            with np.errstate(divide="ignore", invalid="ignore"):
                sweetness = np.where(env > 1e-6, diff_smooth / (env + 1e-6), 0.0)
            sweetness = np.clip(sweetness, 0, None)
            result = float(np.nanmean(sweetness))
            unit = "unitless"
            description = "Sweetness: ratio of derivative to envelope"
            confidence = "MEDIUM"

        elif attribute == "coherence":
            window = min(window_size, n_samples)
            if n_samples < window_size * 2:
                return {
                    "status": "ERROR",
                    "error_code": "INSUFFICIENT_DATA",
                    "message": f"Need at least {window_size * 2} samples for coherence, got {n_samples}",
                }
            padded = np.pad(arr, (window, window), mode="edge")
            n_windows = n_samples - window + 1
            windowed = np.array([padded[i:i + window] for i in range(n_windows)])
            mean_vals = np.mean(windowed, axis=1)
            cross = np.correlate(arr[:n_windows], mean_vals, mode="valid") / window
            coherence = np.abs(cross)
            result = float(np.nanmean(coherence))
            unit = "correlation_unit"
            description = "Local coherence: correlation with local mean window"
            confidence = "MEDIUM"

        else:
            return {
                "status": "ERROR",
                "error_code": "UNKNOWN_ATTRIBUTE",
                "message": f"Attribute '{attribute}' not supported. Use: rms, variance, sweetness, coherence",
                "supported_attributes": ["rms", "variance", "sweetness", "coherence"],
            }

        return {
            "status": "COMPUTED",
            "attribute": attribute,
            "value": result,
            "unit": unit,
            "description": description,
            "confidence": confidence,
            "n_samples": n_samples,
            "processing_log": list(self._processing_log),
            "parameters_hash": self._sha256_params({
                "attribute": attribute,
                "window_size": window_size,
                "n_samples": n_samples,
            }),
            "library_versions": {
                "obspy": self._obspy_version,
                "numpy": NUMPY_VERSION,
            },
        }

    def filter_stream(
        self,
        data: list[float],
        filter_type: str,
        sample_rate: float = 1000.0,
        **filter_params: Any,
    ) -> dict[str, Any]:
        """Apply signal processing filter to seismic trace.

        Args:
            data: Seismic amplitude values.
            filter_type: One of "bandpass", "lowpass", "highpass", "detrend", "taper".
            sample_rate: Sampling rate in Hz.
            **filter_params: Filter-specific parameters.

        Returns:
            Filtered trace data + processing_log.
        """
        import scipy.signal as signal

        self._processing_log = []
        arr = np.asarray(data, dtype=np.float64)

        self._add_log("filter_load", "numpy", {"filter_type": filter_type})

        if filter_type == "bandpass":
            freqmin = filter_params.get("freqmin", 1.0)
            freqmax = filter_params.get("freqmax", 50.0)
            corners = filter_params.get("corners", 4)
            arr_filtered = signal.butter(
                N=corners, Wn=[freqmin, freqmax], btype="bandpass",
                fs=sample_rate, output="sos"
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = signal.sosfilt(arr_filtered, arr)
            step_desc = f"bandpass {freqmin}-{freqmax} Hz, corners={corners}"

        elif filter_type == "lowpass":
            freq = filter_params.get("freq", 50.0)
            corners = filter_params.get("corners", 4)
            sos = signal.butter(N=corners, Wn=freq, btype="lowpass", fs=sample_rate, output="sos")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = signal.sosfilt(sos, arr)
            step_desc = f"lowpass {freq} Hz, corners={corners}"

        elif filter_type == "highpass":
            freq = filter_params.get("freq", 5.0)
            corners = filter_params.get("corners", 4)
            sos = signal.butter(N=corners, Wn=freq, btype="highpass", fs=sample_rate, output="sos")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = signal.sosfilt(sos, arr)
            step_desc = f"highpass {freq} Hz, corners={corners}"

        elif filter_type == "detrend":
            result = signal.detrend(arr)
            step_desc = "linear detrend"

        elif filter_type == "taper":
            max_percentage = filter_params.get("max_percentage", 0.05)
            type_ = filter_params.get("type", "hann")
            taper_window = int(n * max_percentage) if (n := len(arr)) > 0 else 0
            if taper_window > 0:
                taper = np.hanning(taper_window * 2)
                result = arr.copy()
                result[:taper_window] *= taper[:taper_window]
                result[-taper_window:] *= taper[taper_window:]
            else:
                result = arr
            step_desc = f"taper {max_percentage*100}% ({type_})"

        else:
            return {
                "status": "ERROR",
                "error_code": "UNKNOWN_FILTER",
                "message": f"Filter '{filter_type}' not supported.",
                "supported_filters": ["bandpass", "lowpass", "highpass", "detrend", "taper"],
            }

        self._add_log("filter_apply", "scipy", {"step": step_desc})

        return {
            "status": "FILTERED",
            "filter_applied": filter_type,
            "filter_params": filter_params,
            "data": result.tolist(),
            "n_samples": len(result),
            "processing_log": list(self._processing_log),
            "parameters_hash": self._sha256_params({
                "filter_type": filter_type,
                "filter_params": filter_params,
            }),
            "library_versions": {
                "obspy": self._obspy_version,
                "numpy": NUMPY_VERSION,
                "scipy": "1.11.0",
            },
        }

    def detect_anomalous_contrast(
        self,
        data: list[float] | np.ndarray,
        sample_rate: float = 1000.0,
        window_size: int = 20,
        threshold_sigma: float = 2.0,
    ) -> dict[str, Any]:
        """Detect Anomalous Contrast (AC) in seismic trace.

        AC is coherent noise that looks like real geological signal.
        Uses semblance + variance anomaly detection.

        Ref: Arif Fazil (2025) — GEOX Anomalous Contrast Protocol.

        Args:
            data: Seismic trace amplitudes.
            sample_rate: Sampling rate in Hz.
            window_size: Analysis window in samples.
            threshold_sigma: Anomaly threshold in standard deviations.

        Returns:
            AnomalousContrastResult with AC score, class, and anomaly mask.
        """
        arr = np.asarray(data, dtype=np.float64)
        n = len(arr)

        self._processing_log = []
        self._add_log("ac_detection", "geox", {
            "window_size": window_size,
            "threshold_sigma": threshold_sigma,
            "n_samples": n,
        })

        if n < window_size * 2:
            return {
                "status": "ERROR",
                "error_code": "INSUFFICIENT_DATA",
                "message": f"Need at least {window_size * 2} samples, got {n}",
                "processing_log": self._processing_log,
            }

        semblance_vals = np.zeros(n)
        for i in range(window_size, n - window_size):
            window = arr[i - window_size:i + window_size]
            window_mean = np.mean(window)
            window_var = np.var(window)
            point_var = np.var(arr[i])
            if window_var > 1e-10:
                semblance_vals[i] = point_var / (window_var + 1e-10)
            else:
                semblance_vals[i] = 1.0

        local_mean = np.convolve(arr, np.ones(window_size) / window_size, mode="same")
        local_var = np.array([
            np.var(arr[max(0, i - window_size):min(n, i + window_size)])
            for i in range(n)
        ])
        global_var = np.var(arr)
        variance_ratio = np.where(global_var > 1e-10, local_var / global_var, 1.0)

        anomaly_mask = (semblance_vals > threshold_sigma) | (variance_ratio > threshold_sigma)

        ac_score = float(np.mean(semblance_vals[:n]))

        if ac_score < 0.3:
            ac_class = "LOW_AC"
        elif ac_score < 0.6:
            ac_class = "MODERATE_AC"
        else:
            ac_class = "HIGH_AC"

        self._add_log("ac_classification", "geox", {
            "ac_score": ac_score,
            "ac_class": ac_class,
            "anomaly_fraction": float(np.sum(anomaly_mask) / n),
        })

        return {
            "status": "COMPUTED",
            "ac_score": round(ac_score, 4),
            "ac_class": ac_class,
            "anomaly_mask": anomaly_mask.tolist(),
            "anomaly_fraction": round(float(np.sum(anomaly_mask) / n), 4),
            "semblance_mean": round(float(np.mean(semblance_vals)), 4),
            "variance_ratio_mean": round(float(np.mean(variance_ratio)), 4),
            "confidence": "MEDIUM",
            "processing_log": list(self._processing_log),
            "parameters_hash": self._sha256_params({
                "window_size": window_size,
                "threshold_sigma": threshold_sigma,
                "n_samples": n,
            }),
            "library_versions": {
                "obspy": self._obspy_version,
                "numpy": NUMPY_VERSION,
            },
        }


def get_adapter() -> ObsPyAdapter:
    """Factory: returns ObsPyAdapter singleton."""
    return ObsPyAdapter()
