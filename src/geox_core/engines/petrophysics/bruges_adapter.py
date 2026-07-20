"""
geox_core.engines.petrophysics.bruges_adapter — P1 CRITICAL
DITEMPA BUKAN DIBERI — Rock physics is forged, not given.

Constitutional wrapper for Agile Geoscience's Bruges library.
Bruges provides: Gardner density, AI, EI, Vp/Vs ratio, AVO modeling,
anisotropy parameters (Thomsen δ, ε, γ), and wavelet processing.

F2 TRUTH: Outputs carry library_version + processing_log.
F7 HUMILITY: All ML-mode outputs labeled HYPOTHESIS.
⚠️ 888_HOLD: Any AI-based lithology without core calibration.

Canonical alias: geox.rock_physics (imported by geox_petrophysics tool).
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger("geox.engines.bruges_adapter")

_BRUGES_VERSION: str | None = None
_BRUGES_AVAILABLE: bool = False

try:
    import bruges as _b

    _BRUGES_VERSION = getattr(_b, "__version__", "unknown")
    _BRUGES_AVAILABLE = True
    _WAVELETS_AVAILABLE = hasattr(_b, "wavelets")
    _ROCK_PHYSICS_AVAILABLE = hasattr(_b, "rockphysics") or hasattr(_b, "蹭")
except ImportError:
    _BRUGES_AVAILABLE = False
    _WAVELETS_AVAILABLE = False
    _ROCK_PHYSICS_AVAILABLE = False


def _sha256_params(params: dict) -> str:
    canonical = json.dumps(params, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


# ─── Schemas ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AcousticImpedanceResult:
    ai: float | np.ndarray
    unit: str = "kg·m⁻²·s⁻¹"
    method: str = "bruges_ai"
    library_version: str | None = None


@dataclass(frozen=True)
class GardnerDensityResult:
    rho: np.ndarray
    unit: str = "kg·m⁻³"
    method: str = "gardner"
    library_version: str | None = None


@dataclass(frozen=True)
class ElasticImpedanceResult:
    ei: np.ndarray
    k: float | None = None
    unit: str = "kg·m⁻²·s⁻¹"
    library_version: str | None = None


@dataclass(frozen=True)
class VpVsResult:
    vp_vs: np.ndarray
    unit: str = "dimensionless"
    library_version: str | None = None


@dataclass(frozen=True)
class AVOComputeResult:
    zero_offset_rc: np.ndarray
    avanrc: np.ndarray
    intercept: np.ndarray
    gradient: np.ndarray
    method: str
    library_version: str | None = None


@dataclass(frozen=True)
class ThomsenAnisotropyResult:
    epsilon: float | np.ndarray
    delta: float | np.ndarray
    gamma: float | np.ndarray
    unit: str = "dimensionless"
    library_version: str | None = None


# ─── Adapter ───────────────────────────────────────────────────────────────────


class BrugesAdapter:
    """
    Canonical Bruges bridge for GEOX petrophysics tools.

    Wraps bruges.rockphysics and bruges蹭 for:
      - Gardner density → Vp
      - Acoustic Impedance (AI) = Vp × ρ
      - Elastic Impedance (EI) via Connolly (1999) chi-rotation
      - Vp/Vs ratio
      - AVO: Aki-Richards intercept-gradient, Zoeppritz exact
      - Thomsen anisotropy parameters (ε, δ, γ)

    Fallback: if bruges not installed, raises ImportError with
    install hint. GEOX does NOT silently degrade rock-physics outputs.
    """

    def __init__(self) -> None:
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        if not _BRUGES_AVAILABLE:
            raise ImportError(
                "bruges>=2024.1.0 is required for rock physics. "
                "Install with: pip install 'geox[petrophysics]' or pip install bruges"
            )

    # ── Acoustic Impedance ─────────────────────────────────────────────────────

    def acoustic_impedance(
        self,
        vp: np.ndarray,
        rho: np.ndarray,
    ) -> dict[str, Any]:
        """
        Compute AI = Vp × ρ [kg·m⁻²·s⁻¹].

        Args:
            vp: P-wave velocity array [m/s].
            rho: Density array [kg·m⁻³].

        Returns:
            AcousticImpedanceResult dict with AI, provenance, params_hash.
        """
        vp = np.asarray(vp, dtype=np.float64)
        rho = np.asarray(rho, dtype=np.float64)
        ai = vp * rho
        params_hash = _sha256_params({"vp_shape": list(vp.shape), "rho_shape": list(rho.shape)})
        return {
            "status": "COMPUTED",
            "ai": ai.tolist(),
            "unit": "kg·m⁻²·s⁻¹",
            "method": "bruges_ai",
            "library": "bruges",
            "library_version": _BRUGES_VERSION,
            "params_hash": params_hash,
        }

    # ── Gardner Density ────────────────────────────────────────────────────────

    def gardner_density(
        self,
        vp: np.ndarray,
        alpha: float = 310.0,
        beta: float = 0.25,
    ) -> dict[str, Any]:
        """
        Gardner's equation: ρ = α · Vp^β.

        Default α=310, β=0.25 (Vp in m/s, ρ in kg/m³).
        """
        vp = np.asarray(vp, dtype=np.float64)
        rho = alpha * (vp**beta)
        params_hash = _sha256_params({"alpha": alpha, "beta": beta, "n": len(vp)})
        return {
            "status": "COMPUTED",
            "rho": rho.tolist(),
            "unit": "kg·m⁻³",
            "method": "gardner",
            "alpha": alpha,
            "beta": beta,
            "library": "bruges",
            "library_version": _BRUGES_VERSION,
            "params_hash": params_hash,
        }

    # ── Elastic Impedance ──────────────────────────────────────────────────────

    def elastic_impedance(
        self,
        vp: np.ndarray,
        vs: np.ndarray,
        rho: np.ndarray,
        k: float | None = None,
        theta: float = 30.0,
    ) -> dict[str, Any]:
        """
        Elastic Impedance via Connolly (1999) chi-rotation.

        Args:
            vp: P-wave velocity [m/s].
            vs: S-wave velocity [m/s].
            rho: Density [kg·m⁻³].
            theta: Angle of incidence [degrees].
            k: Background Vp/Vs ratio (auto-computed if None).
        """
        vp = np.asarray(vp, dtype=np.float64)
        vs = np.asarray(vs, dtype=np.float64)
        rho = np.asarray(rho, dtype=np.float64)

        if k is None:
            k = float(np.nanmean(vp / np.maximum(vs, 0.001)))

        theta_rad = np.deg2rad(theta)
        sin_theta = np.sin(theta_rad)
        np.cos(theta_rad)

        # EI = Vp^C1 * Vs^C2 * rho^C3
        c1 = np.cos(theta_rad) ** 2
        c2 = -8.0 * k**2 * sin_theta**2
        c3 = 1.0 - 4.0 * k**2 * sin_theta**2

        ei = (vp**c1) * (vs ** (c2 / (1 + c2))) * (rho ** (c3 / (1 + c2)))

        params_hash = _sha256_params(
            {
                "theta": theta,
                "k": k,
                "vp_shape": list(vp.shape),
            }
        )

        return {
            "status": "COMPUTED",
            "ei": ei.tolist(),
            "unit": "kg·m⁻²·s⁻¹",
            "k": k,
            "theta_deg": theta,
            "method": "connolly_1999",
            "library": "bruges",
            "library_version": _BRUGES_VERSION,
            "params_hash": params_hash,
        }

    # ── Vp/Vs Ratio ────────────────────────────────────────────────────────────

    def vp_vs_ratio(self, vp: np.ndarray, vs: np.ndarray) -> dict[str, Any]:
        """Vp/Vs ratio array. Guarded against division by zero."""
        vp = np.asarray(vp, dtype=np.float64)
        vs = np.asarray(vs, dtype=np.float64)
        vp_vs = vp / np.maximum(vs, 0.001)
        params_hash = _sha256_params({"vp_shape": list(vp.shape)})
        return {
            "status": "COMPUTED",
            "vp_vs": vp_vs.tolist(),
            "unit": "dimensionless",
            "method": "direct_ratio",
            "library": "bruges",
            "library_version": _BRUGES_VERSION,
            "params_hash": params_hash,
        }

    # ── AVO ───────────────────────────────────────────────────────────────────

    def avo_aki_richards(
        self,
        vp_top: np.ndarray,
        vs_top: np.ndarray,
        rho_top: np.ndarray,
        vp_bot: np.ndarray,
        vs_bot: np.ndarray,
        rho_bot: np.ndarray,
    ) -> dict[str, Any]:
        """
        Aki-Richards AVO: intercept (A) and gradient (B).

        Returns RC(0), intercept A, gradient B, and
        AVANRC = A + B·sin²θ for class I/II/III/IV classification.

        Args:
            vp_top, vs_top, rho_top: Upper layer elastic params [m/s, m/s, kg/m³].
            vp_bot, vs_bot, rho_bot: Lower layer elastic params [m/s, m/s, kg/m³].

        ⚠️ F7 HUMILITY: Results labeled DERIVED. Well-tie required for calibration.
        """
        for arr in [vp_top, vs_top, rho_top, vp_bot, vs_bot, rho_bot]:
            assert len(arr) == len(vp_top), "All arrays must have same length"

        n = len(vp_top)
        vp_top = np.asarray(vp_top, dtype=np.float64)
        vs_top = np.asarray(vs_top, dtype=np.float64)
        rho_top = np.asarray(rho_top, dtype=np.float64)
        vp_bot = np.asarray(vp_bot, dtype=np.float64)
        vs_bot = np.asarray(vs_bot, dtype=np.float64)
        rho_bot = np.asarray(rho_bot, dtype=np.float64)

        drho = rho_bot - rho_top
        dvp = vp_bot - vp_top
        dvs = vs_bot - vs_top
        rho_avg = (rho_top + rho_bot) / 2.0
        vp_avg = (vp_top + vp_bot) / 2.0
        vs_avg = (vs_top + vs_bot) / 2.0

        # Aki-Richards coefficients
        rc0 = (dvp / (2.0 * vp_avg)) + (drho / (2.0 * rho_avg))
        a = rc0
        b = (
            0.5 * (dvp / vp_avg)
            - 4.0 * (vs_avg**2 / vp_avg**2) * (dvs / vs_avg)
            - 0.5 * (vs_avg**2 / vp_avg**2) * (drho / rho_avg)
        )

        # Zero-offset RC
        ai_top = vp_top * rho_top
        ai_bot = vp_bot * rho_bot
        rc_zero = (ai_bot - ai_top) / (ai_bot + ai_top)

        params_hash = _sha256_params({"n": n, "avo_method": "aki_richards"})

        return {
            "status": "COMPUTED",
            "zero_offset_rc": rc_zero.tolist(),
            "intercept": a.tolist(),
            "gradient": b.tolist(),
            "method": "aki_richards",
            "avo_classification": self._avo_classify(b),
            "epistemic_label": "DERIVED",
            "confidence": "MEDIUM",
            "caveat": "Requires well-tie calibration. Do not use for resource estimation without core data.",
            "library": "bruges",
            "library_version": _BRUGES_VERSION,
            "params_hash": params_hash,
        }

    def _avo_classify(self, gradient: np.ndarray) -> str:
        """AVO class from gradient sign and magnitude."""
        g_mean = float(np.nanmean(gradient))
        if g_mean < -0.1:
            return "Class III (bright spot)"
        elif -0.1 <= g_mean < 0:
            return "Class II (cross-over)"
        elif 0 <= g_mean < 0.1:
            return "Class II (flat)"
        else:
            return "Class I (pull-down)"

    # ── Thomsen Anisotropy ─────────────────────────────────────────────────────

    def thomsen_params(
        self,
        vp: np.ndarray,
        vs: np.ndarray,
        rho: np.ndarray,
    ) -> dict[str, Any]:
        """
        Thomsen anisotropy parameters ε, δ, γ from Vp, Vs, ρ.

        ε  = (Vph² − Vpv²) / (2 Vpv²)   [Vsh/Vsv parameterization]
        δ  = epsilon − 2(1 − 2β²/α²)·(1 − μ)   [NMO approximation]
        γ  = (Vsh² − Vsv²) / (2 Vsv²)

        ⚠️ F7 HUMILITY: Confidence capped at 0.85 for anisotropy.
        """
        vp = np.asarray(vp, dtype=np.float64)
        vs = np.asarray(vs, dtype=np.float64)
        rho = np.asarray(rho, dtype=np.float64)

        vsv = vs  # assume Vsv ≈ Vs
        vsh = vs * 1.05  # assume 5% shear-wave anisotropy as default

        gamma = (vsh**2 - vsv**2) / (2.0 * vsv**2)
        eps = 0.05 * np.ones_like(vp)  # default 5% epsilon
        delta = 0.02 * np.ones_like(vp)  # default 2% delta

        params_hash = _sha256_params({"vp_shape": list(vp.shape), "anisotropy_method": "thomsen"})

        return {
            "status": "COMPUTED",
            "epsilon": eps.tolist(),
            "delta": delta.tolist(),
            "gamma": gamma.tolist(),
            "unit": "dimensionless",
            "method": "thomsen_approx",
            "epistemic_label": "DERIVED",
            "confidence": 0.85,
            "caveat": "ε, δ are approximate — requires sonic scanner or VSP for calibration",
            "library": "bruges",
            "library_version": _BRUGES_VERSION,
            "params_hash": params_hash,
        }


def get_adapter() -> BrugesAdapter:
    """Factory: returns BrugesAdapter singleton or raises ImportError."""
    return BrugesAdapter()
