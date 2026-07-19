"""
geox_core.engines.seismic.inversion — Post-Stack AI Inversion Engine
═══════════════════════════════════════════════════════════════════════
Transforms recorded seismograms into acoustic impedance (AI).

Three inversion strategies:
  1. Coloured Inversion — spectral match, relative AI (fast, robust)
  2. Model-Based Inversion — iterative, absolute AI (requires initial model)
  3. PINN-Assisted Inversion — physics-constrained, absolute AI (best lateral continuity)

Physics:
    AI(z) = Vp(z) × ρ(z)                          [kg/m²·s]
    RC(i) = [AI(i+1) - AI(i)] / [AI(i+1) + AI(i)] [dimensionless]
    S(t) = RC(t) ∗ W(t)                            [convolutional model]
    Inverse: S(t), W(t) → AI(z)                    [ill-posed, regularised]

Constitutional: F2 (epistemic labels), F4 (reduce entropy), F9 (physics-only).
Author: FORGE (000Ω) | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

import numpy as np
from scipy import linalg, signal

from geox_core.physics.parameters import (
    convolve_trace,
    reflectivity_array,
    ricker_wavelet,
)

logger = logging.getLogger("geox.inversion")


# ─── Enums ───────────────────────────────────────────────────────────────────


class InversionMethod(StrEnum):
    COLOURED = "coloured"
    MODEL_BASED = "model_based"
    PINN = "pinn"


class ConfidenceBand(StrEnum):
    HIGH = "HIGH"        # r > 0.9
    MODERATE = "MODERATE"  # 0.7 < r <= 0.9
    LOW = "LOW"          # r <= 0.7
    VOID = "VOID"        # failed validation


# ─── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class LowFrequencyModel:
    """Low-frequency impedance model from well logs + horizons."""
    depth: np.ndarray
    ai_lfm: np.ndarray
    cutoff_hz: float = 12.0
    source: str = "well_interpolation"
    well_count: int = 1


@dataclass
class WaveletEstimate:
    """Estimated seismic wavelet."""
    samples: np.ndarray
    dt_ms: float
    frequency_hz: float
    phase_deg: float = 0.0
    source: str = "ricker"  # ricker | statistical | well_derived


@dataclass
class InversionResult:
    """Output of any inversion method."""
    method: InversionMethod
    ai_absolute: np.ndarray          # Absolute AI [kg/m²·s]
    ai_relative: np.ndarray | None   # Relative AI (coloured only)
    depth: np.ndarray                # Depth axis [m]
    time_ms: np.ndarray              # Time axis [ms]
    correlation: float               # r(observed, predicted)
    confidence: ConfidenceBand
    low_freq_model: LowFrequencyModel | None
    wavelet: WaveletEstimate
    residual: np.ndarray             # observed - predicted
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method.value,
            "ai_absolute": self.ai_absolute.tolist(),
            "ai_relative": self.ai_relative.tolist() if self.ai_relative is not None else None,
            "depth": self.depth.tolist(),
            "time_ms": self.time_ms.tolist(),
            "correlation": round(self.correlation, 6),
            "confidence": self.confidence.value,
            "wavelet_frequency_hz": self.wavelet.frequency_hz,
            "wavelet_phase_deg": self.wavelet.phase_deg,
            "metadata": self.metadata,
        }


@dataclass
class ConsistencyGate:
    """Re-forward-model gate: inversion result must reproduce input seismic."""
    r_forward: float
    threshold: float = 0.90
    passed: bool = False
    message: str = ""

    def validate(self) -> bool:
        self.passed = self.r_forward >= self.threshold
        if self.passed:
            self.message = (
                f"DATA_CONSISTENT (r={self.r_forward:.4f}): Inversion reproduces input seismic. "
                "Lancaster-Whitcombe (2000) gate passed."
            )
        else:
            self.message = (
                f"CONSISTENCY_FAILED (r={self.r_forward:.4f} < {self.threshold}): "
                "Inversion does not reproduce input seismic. Result unreliable."
            )
        return self.passed


# ─── Utility Functions ───────────────────────────────────────────────────────


def _correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation coefficient."""
    if len(a) != len(b):
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _bandpass_filter(data: np.ndarray, dt_s: float, low_hz: float, high_hz: float) -> np.ndarray:
    """Butterworth bandpass filter."""
    nyquist = 0.5 / dt_s
    low = low_hz / nyquist
    high = min(high_hz / nyquist, 0.99)
    if low >= high or low <= 0:
        return data
    b, a = signal.butter(4, [low, high], btype="band")
    return signal.filtfilt(b, a, data)


def _build_lfm_from_wells(
    well_logs: list[dict[str, np.ndarray]],
    depth_target: np.ndarray,
    cutoff_hz: float = 12.0,
    dt_s: float = 0.004,
) -> LowFrequencyModel:
    """Build low-frequency model by interpolating well AI and low-pass filtering."""
    well_ais = []
    for log in well_logs:
        vp = log.get("VP", log.get("vp", np.array([])))
        rho = log.get("RHOB", log.get("rho", log.get("RHOZ", np.array([]))))
        if len(vp) > 0 and len(rho) > 0:
            n = min(len(vp), len(rho))
            ai = vp[:n] * rho[:n]
            well_ais.append(ai)

    if not well_ais:
        # Synthetic fallback: gradient model
        ai_lfm = np.linspace(4000, 12000, len(depth_target))
        return LowFrequencyModel(
            depth=depth_target,
            ai_lfm=ai_lfm,
            cutoff_hz=cutoff_hz,
            source="synthetic_gradient",
            well_count=0,
        )

    # Average well AI (if multiple wells)
    max_len = max(len(ai) for ai in well_ais)
    ai_stack = np.zeros(max_len)
    count = np.zeros(max_len)
    for ai in well_ais:
        ai_stack[:len(ai)] += ai
        count[:len(ai)] += 1
    count[count == 0] = 1
    ai_avg = ai_stack / count

    # Interpolate to target depth
    if len(ai_avg) != len(depth_target):
        ai_interp = np.interp(
            depth_target,
            np.linspace(depth_target[0], depth_target[-1], len(ai_avg)),
            ai_avg,
        )
    else:
        ai_interp = ai_avg

    # Low-pass filter to retain only low frequencies
    # Convert cutoff_hz to samples
    nyquist = 0.5 / dt_s
    wn = min(cutoff_hz / nyquist, 0.99)
    if wn > 0 and wn < 1:
        b, a = signal.butter(2, wn, btype="low")
        ai_lfm = signal.filtfilt(b, a, ai_interp)
    else:
        ai_lfm = ai_interp

    return LowFrequencyModel(
        depth=depth_target,
        ai_lfm=ai_lfm,
        cutoff_hz=cutoff_hz,
        source="well_interpolation",
        well_count=len(well_logs),
    )


def _estimate_wavelet_from_well(
    seismic_trace: np.ndarray,
    reflectivity: np.ndarray,
    dt_ms: float,
    method: Literal["statistical", "deterministic"] = "statistical",
) -> WaveletEstimate:
    """Estimate wavelet from seismic and well reflectivity."""
    dt_s = dt_ms / 1000.0

    if method == "deterministic":
        # Wiener deconvolution: W = seismic / RC
        # Stabilised: W = (RC^T * S) / (RC^T * RC + ε)
        n = min(len(seismic_trace), len(reflectivity))
        rc = reflectivity[:n]
        s = seismic_trace[:n]

        # Toeplitz matrix
        rc_padded = np.zeros(n)
        rc_padded[:len(rc)] = rc
        R = linalg.toeplitz(rc_padded)
        eps = 1e-6 * np.max(R ** 2)
        w = linalg.solve(R.T @ R + eps * np.eye(n), R.T @ s)

        # Trim to meaningful part
        centre = len(w) // 2
        half_len = min(40, centre)
        w_trimmed = w[centre - half_len: centre + half_len + 1]
        w_trimmed = w_trimmed / (np.max(np.abs(w_trimmed)) + 1e-12)

    else:
        # Statistical: autocorrelation of seismic ≈ wavelet autocorrelation
        n = min(len(seismic_trace), 128)
        ac = np.correlate(seismic_trace[:n], seismic_trace[:n], mode="full")
        ac = ac[n - 1:]  # one-sided
        ac = ac / (ac[0] + 1e-12)

        # Spectral factorisation (Kolmogorov)
        spec = np.fft.rfft(ac)
        spec = np.sqrt(np.abs(spec)) * np.exp(1j * np.angle(spec))
        w = np.fft.irfft(spec, n=n)
        w_trimmed = w[:61]  # 61 samples ≈ 240ms at 4ms
        w_trimmed = w_trimmed / (np.max(np.abs(w_trimmed)) + 1e-12)

    # Estimate dominant frequency
    W = np.abs(np.fft.rfft(w_trimmed))
    freqs = np.fft.rfftfreq(len(w_trimmed), d=dt_s)
    if len(W) > 1:
        dom_freq = freqs[np.argmax(W[1:]) + 1]
    else:
        dom_freq = 20.0

    return WaveletEstimate(
        samples=w_trimmed,
        dt_ms=dt_ms,
        frequency_hz=float(dom_freq),
        phase_deg=0.0,
        source=method,
    )


# ─── Coloured Inversion ─────────────────────────────────────────────────────


def coloured_inversion(
    seismic_trace: np.ndarray,
    well_ai: np.ndarray | None = None,
    dt_ms: float = 4.0,
    lfm: LowFrequencyModel | None = None,
) -> InversionResult:
    """
    Coloured Inversion: spectral matching to produce relative AI.

    Method: Match seismic spectrum to well-log AI spectrum.
    Output is RELATIVE impedance (no absolute values).

    Lancaster & Whitcombe (2000): fast, robust, zero-phase assumption.
    """
    dt_s = dt_ms / 1000.0
    n = len(seismic_trace)

    # Compute seismic spectrum
    S_seismic = np.abs(np.fft.rfft(seismic_trace))

    if well_ai is not None and len(well_ai) > 0:
        # Match to well AI spectrum
        n_well = min(len(well_ai), n)
        ai_padded = np.zeros(n)
        ai_padded[:n_well] = well_ai[:n_well]
        S_ai = np.abs(np.fft.rfft(ai_padded))

        # Transfer function: H(f) = S_ai(f) / S_seismic(f)
        eps = 1e-6 * np.max(S_seismic)
        H = S_ai / (S_seismic + eps)

        # Apply transfer function
        seismic_fft = np.fft.rfft(seismic_trace)
        ai_fft = seismic_fft * H
        ai_relative = np.fft.irfft(ai_fft, n=n)
    else:
        # No well data: use spectral integration (Coloured Inversion standard)
        # H(f) = (2πf)^(-1/2) — integrates seismic spectrum
        freqs = np.fft.rfftfreq(n, d=dt_s)
        freqs[0] = 1.0  # avoid division by zero
        H = (2.0 * np.pi * freqs) ** (-0.5)
        H[0] = 0.0  # DC component removed

        seismic_fft = np.fft.rfft(seismic_trace)
        ai_fft = seismic_fft * H
        ai_relative = np.fft.irfft(ai_fft, n=n)

    # If LFM available, add low-frequency component for absolute AI
    ai_absolute = None
    if lfm is not None and len(lfm.ai_lfm) == n:
        ai_absolute = ai_relative + lfm.ai_lfm
    elif lfm is not None:
        ai_lfm_interp = np.interp(
            np.arange(n), np.linspace(0, n - 1, len(lfm.ai_lfm)), lfm.ai_lfm
        )
        ai_absolute = ai_relative + ai_lfm_interp

    # Predict seismic from inverted AI (consistency check)
    if ai_absolute is not None:
        rc = reflectivity_array(ai_absolute)
        wavelet = ricker_wavelet(20.0, dt_s)
        predicted = convolve_trace(rc, wavelet)
    else:
        rc = reflectivity_array(ai_relative + np.mean(np.abs(ai_relative)))
        wavelet = ricker_wavelet(20.0, dt_s)
        predicted = convolve_trace(rc, wavelet)

    n_min = min(len(seismic_trace), len(predicted))
    r = _correlation(seismic_trace[:n_min], predicted[:n_min])

    depth = np.arange(n) * 1.0  # sample index as depth proxy
    time_ms = np.arange(n) * dt_ms

    return InversionResult(
        method=InversionMethod.COLOURED,
        ai_absolute=ai_absolute if ai_absolute is not None else ai_relative,
        ai_relative=ai_relative,
        depth=depth,
        time_ms=time_ms,
        correlation=r,
        confidence=_classify_confidence(r),
        low_freq_model=lfm,
        wavelet=WaveletEstimate(
            samples=ricker_wavelet(20.0, dt_s),
            dt_ms=dt_ms,
            frequency_hz=20.0,
            source="ricker",
        ),
        residual=seismic_trace[:n_min] - predicted[:n_min],
        metadata={
            "method_detail": "Lancaster-Whitcombe (2000) coloured inversion",
            "has_lfm": lfm is not None,
            "epistemic_rung": 3 if lfm is not None else 2,
        },
    )


# ─── Model-Based Inversion ──────────────────────────────────────────────────


def model_based_inversion(
    seismic_trace: np.ndarray,
    initial_ai: np.ndarray,
    wavelet: np.ndarray | None = None,
    dt_ms: float = 4.0,
    iterations: int = 30,
    damping: float = 0.1,
    lfm: LowFrequencyModel | None = None,
) -> InversionResult:
    """
    Model-Based Inversion: iterative AI estimation from initial model.

    Uses Gauss-Newton optimisation with Tikhonov regularisation.
    Produces ABSOLUTE AI if initial model is calibrated.

    Physics:
        Forward: S = W * RC(AI)
        Residual: ΔS = S_obs - S_pred
        Update: AI += J^T (J J^T + λI)^{-1} ΔS
    """
    dt_s = dt_ms / 1000.0
    n = len(seismic_trace)
    n_ai = len(initial_ai)

    if wavelet is None:
        wavelet = ricker_wavelet(20.0, dt_s)

    # Ensure wavelet is shorter than data
    if len(wavelet) > n:
        wavelet = wavelet[:n]

    ai_current = initial_ai.copy()
    residuals = []

    for _iteration in range(iterations):
        # Forward model: AI → RC → Synthetic
        rc = reflectivity_array(ai_current)
        synthetic = convolve_trace(rc, wavelet)

        # Match lengths
        n_min = min(len(seismic_trace), len(synthetic))
        residual = seismic_trace[:n_min] - synthetic[:n_min]
        residuals.append(float(np.sqrt(np.mean(residual ** 2))))

        # Jacobian (finite difference approximation)
        delta = np.max(np.abs(ai_current)) * 0.001 + 1e-6
        J = np.zeros((n_min, n_ai))
        for j in range(min(n_ai, n_min)):
            ai_perturbed = ai_current.copy()
            ai_perturbed[j] += delta
            rc_p = reflectivity_array(ai_perturbed)
            syn_p = convolve_trace(rc_p, wavelet)
            J[:, j] = (syn_p[:n_min] - synthetic[:n_min]) / delta

        # Gauss-Newton update with Tikhonov regularisation
        # ΔAI = J^T (J J^T + λI)^{-1} residual
        JJT = J @ J.T
        lambda_I = damping * np.eye(n_min) * np.mean(np.diag(JJT))
        try:
            update = J.T @ linalg.solve(JJT + lambda_I, residual)
        except linalg.LinAlgError:
            break

        # Clip update to prevent divergence
        max_update = np.max(np.abs(ai_current)) * 0.1
        update = np.clip(update, -max_update, max_update)

        ai_current[:len(update)] += update[:n_ai]

        # Enforce physical bounds
        ai_current = np.clip(ai_current, 1000, 50000)

    # Final predicted seismic
    rc_final = reflectivity_array(ai_current)
    predicted = convolve_trace(rc_final, wavelet)
    n_min = min(len(seismic_trace), len(predicted))
    r = _correlation(seismic_trace[:n_min], predicted[:n_min])

    depth = np.arange(n_ai) * 1.0
    time_ms = np.arange(n_ai) * dt_ms

    return InversionResult(
        method=InversionMethod.MODEL_BASED,
        ai_absolute=ai_current,
        ai_relative=None,
        depth=depth,
        time_ms=time_ms,
        correlation=r,
        confidence=_classify_confidence(r),
        low_freq_model=lfm,
        wavelet=WaveletEstimate(
            samples=wavelet,
            dt_ms=dt_ms,
            frequency_hz=20.0,
            source="provided" if wavelet is not None else "ricker",
        ),
        residual=seismic_trace[:n_min] - predicted[:n_min],
        metadata={
            "iterations": iterations,
            "damping": damping,
            "final_rmse": residuals[-1] if residuals else None,
            "convergence": residuals,
            "epistemic_rung": 4,
        },
    )


# ─── PINN-Assisted Inversion ────────────────────────────────────────────────


def pinn_assisted_inversion(
    seismic_trace: np.ndarray,
    well_ai: np.ndarray | None = None,
    dt_ms: float = 4.0,
    lfm: LowFrequencyModel | None = None,
    wavelet_freq_hz: float = 20.0,
    regularisation_weight: float = 0.01,
    smoothness_weight: float = 0.005,
    iterations: int = 100,
    learning_rate: float = 0.01,
) -> InversionResult:
    """
    Physics-Informed Neural Network (PINN) style inversion.

    Combines:
      - Data misfit (seismic residual)
      - Physics constraint (convolutional forward model)
      - Regularisation (smoothness + well tie)

    No actual neural network — uses gradient descent with physics-informed loss.
    This is the "poor man's PINN" — same loss function, no neural architecture.
    For true PINN, replace optimiser with torch.nn + autograd.

    Loss = ||S_obs - W*RC(AI)||² + λ₁||∇AI||² + λ₂||AI - AI_well||²
    """
    dt_s = dt_ms / 1000.0
    n = len(seismic_trace)
    wavelet = ricker_wavelet(wavelet_freq_hz, dt_s)

    # Initial AI model
    if lfm is not None and len(lfm.ai_lfm) == n:
        ai = lfm.ai_lfm.copy()
    elif well_ai is not None and len(well_ai) > 0:
        ai = np.interp(np.arange(n), np.linspace(0, n - 1, len(well_ai)), well_ai)
    else:
        # Default gradient
        ai = np.linspace(5000, 10000, n)

    # Well target (for regularisation)
    ai_well = well_ai.copy() if well_ai is not None else None

    losses = []

    for _iteration in range(iterations):
        # Forward model
        rc = reflectivity_array(ai)
        predicted = convolve_trace(rc, wavelet)
        n_min = min(len(seismic_trace), len(predicted))

        # Data misfit
        misfit = seismic_trace[:n_min] - predicted[:n_min]
        data_loss = np.mean(misfit ** 2)

        # Smoothness regularisation (second derivative)
        if len(ai) > 2:
            d2 = np.diff(ai, n=2)
            smooth_loss = np.mean(d2 ** 2)
        else:
            smooth_loss = 0.0

        # Well tie regularisation
        well_loss = 0.0
        if ai_well is not None and len(ai_well) > 0:
            n_w = min(len(ai), len(ai_well))
            well_loss = np.mean((ai[:n_w] - ai_well[:n_w]) ** 2)

        # Total loss
        total_loss = data_loss + smoothness_weight * smooth_loss + regularisation_weight * well_loss
        losses.append(float(total_loss))

        # Gradient (numerical finite difference)
        grad = np.zeros_like(ai)
        delta = np.max(np.abs(ai)) * 0.0001 + 1e-3

        for j in range(len(ai)):
            ai_plus = ai.copy()
            ai_plus[j] += delta

            rc_p = reflectivity_array(ai_plus)
            pred_p = convolve_trace(rc_p, wavelet)
            misfit_p = seismic_trace[:n_min] - pred_p[:n_min]
            data_loss_p = np.mean(misfit_p ** 2)

            # Smoothness gradient
            if len(ai_plus) > 2:
                d2_p = np.diff(ai_plus, n=2)
                smooth_loss_p = np.mean(d2_p ** 2)
            else:
                smooth_loss_p = 0.0

            well_loss_p = 0.0
            if ai_well is not None and len(ai_well) > 0:
                n_w = min(len(ai_plus), len(ai_well))
                well_loss_p = np.mean((ai_plus[:n_w] - ai_well[:n_w]) ** 2)

            loss_p = data_loss_p + smoothness_weight * smooth_loss_p + regularisation_weight * well_loss_p
            grad[j] = (loss_p - total_loss) / delta

        # Update
        ai -= learning_rate * grad

        # Enforce physical bounds
        ai = np.clip(ai, 1000, 50000)

    # Final prediction
    rc_final = reflectivity_array(ai)
    predicted_final = convolve_trace(rc_final, wavelet)
    n_min = min(len(seismic_trace), len(predicted_final))
    r = _correlation(seismic_trace[:n_min], predicted_final[:n_min])

    depth = np.arange(len(ai)) * 1.0
    time_ms = np.arange(len(ai)) * dt_ms

    return InversionResult(
        method=InversionMethod.PINN,
        ai_absolute=ai,
        ai_relative=None,
        depth=depth,
        time_ms=time_ms,
        correlation=r,
        confidence=_classify_confidence(r),
        low_freq_model=lfm,
        wavelet=WaveletEstimate(
            samples=wavelet,
            dt_ms=dt_ms,
            frequency_hz=wavelet_freq_hz,
            source="ricker",
        ),
        residual=seismic_trace[:n_min] - predicted_final[:n_min],
        metadata={
            "iterations": iterations,
            "learning_rate": learning_rate,
            "regularisation_weight": regularisation_weight,
            "smoothness_weight": smoothness_weight,
            "final_loss": losses[-1] if losses else None,
            "loss_curve": losses[:20],  # first 20 for monitoring
            "epistemic_rung": 5,
        },
    )


# ─── Consistency Gate ───────────────────────────────────────────────────────


def reforward_consistency_gate(
    inversion_result: InversionResult,
    seismic_observed: np.ndarray,
    threshold: float = 0.90,
) -> ConsistencyGate:
    """
    Lancaster-Whitcombe (2000) consistency gate.

    Re-forward-model the inversion result and correlate against input seismic.
    r ≈ 1.0 proves the inversion is data-consistent.
    """
    ai = inversion_result.ai_absolute
    inversion_result.wavelet.dt_ms / 1000.0
    wavelet = inversion_result.wavelet.samples

    rc = reflectivity_array(ai)
    predicted = convolve_trace(rc, wavelet)

    n_min = min(len(seismic_observed), len(predicted))
    r = _correlation(seismic_observed[:n_min], predicted[:n_min])

    gate = ConsistencyGate(r_forward=r, threshold=threshold)
    gate.validate()
    return gate


# ─── Full Inversion Pipeline ────────────────────────────────────────────────


def run_inversion_pipeline(
    seismic_trace: np.ndarray,
    method: Literal["coloured", "model_based", "pinn"] = "coloured",
    dt_ms: float = 4.0,
    well_logs: list[dict[str, np.ndarray]] | None = None,
    initial_ai: np.ndarray | None = None,
    wavelet_freq_hz: float = 20.0,
    iterations: int = 30,
) -> dict[str, Any]:
    """
    Complete inversion pipeline: method selection → inversion → consistency gate.

    Returns dict with inversion result + consistency gate + governance metadata.
    """
    # Build LFM if well data available
    lfm = None
    well_ai = None
    if well_logs:
        depth = np.arange(len(seismic_trace)) * 1.0
        lfm = _build_lfm_from_wells(well_logs, depth, dt_s=dt_ms / 1000.0)
        # Extract average well AI for coloured/PINN
        for log in well_logs:
            vp = log.get("VP", log.get("vp", np.array([])))
            rho = log.get("RHOB", log.get("rho", log.get("RHOZ", np.array([]))))
            if len(vp) > 0 and len(rho) > 0:
                n = min(len(vp), len(rho))
                well_ai = vp[:n] * rho[:n]
                break

    # Run inversion
    if method == "coloured":
        result = coloured_inversion(seismic_trace, well_ai, dt_ms, lfm)
    elif method == "model_based":
        if initial_ai is None:
            if lfm is not None:
                initial_ai = lfm.ai_lfm
            else:
                initial_ai = np.linspace(5000, 10000, len(seismic_trace))
        result = model_based_inversion(seismic_trace, initial_ai, dt_ms=dt_ms,
                                       iterations=iterations, lfm=lfm)
    elif method == "pinn":
        result = pinn_assisted_inversion(seismic_trace, well_ai, dt_ms, lfm,
                                          wavelet_freq_hz, iterations=iterations)
    else:
        raise ValueError(f"Unknown inversion method: {method}")

    # Consistency gate
    gate = reforward_consistency_gate(result, seismic_trace)

    return {
        "inversion": result.to_dict(),
        "consistency_gate": {
            "r_forward": round(gate.r_forward, 6),
            "threshold": gate.threshold,
            "passed": gate.passed,
            "message": gate.message,
        },
        "governance": {
            "physics9_state": True,
            "epistemic_rung": result.metadata.get("epistemic_rung", 2),
            "confidence": result.confidence.value,
            "method": method,
        },
    }


# ─── Helpers ────────────────────────────────────────────────────────────────


def _classify_confidence(r: float) -> ConfidenceBand:
    if r > 0.9:
        return ConfidenceBand.HIGH
    elif r > 0.7:
        return ConfidenceBand.MODERATE
    elif r > 0.0:
        return ConfidenceBand.LOW
    return ConfidenceBand.VOID
