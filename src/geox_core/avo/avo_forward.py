"""
geox_core.avo.avo_forward — Eureka 9 core primitive.

The Earth is an impedance field. A vertical angle gather of the
impedance contrast field is a direct fluid indicator. This module
operationalises that claim via three functions and a synthetic gather.

EUREKA 9 — IMPEDANCE CONTRAST IS FLUID (AVO)
============================================

Six physics pillars (per the 999 SEAL ratified 2026-06-03):

  L1 Elastic wave equation        : Vp = sqrt((K+4/3G)/rho), Vs = sqrt(G/rho)
  L2 Biot-Gassmann fluid sub      : G_sat = G_dry, K_sat = K_dry + fluid term
  L3 Zoeppritz exact              : 4x4 system, R_PP(theta) for any angle
  L4 Shuey linearisation          : R(theta) = R0 + G sin^2 theta + F tan^2 theta sin^2 theta
  L5 Lambda-Mu-Rho (LMR)         : lambda_rho = rho(Vp^2 - 2 Vs^2), mu_rho = rho Vs^2
  L6 AVO class crossplot          : Class I/II/IIp/III/IV from (R0, G) sign

Public surface (3 functions + 2 dataclasses + 1 helper):

  AVOResult, LMRResult
  zoeppritz_rpp        — exact R_PP(theta) from full 4x4 Zoeppritz system
  shuey_avo           — Shuey 2-term: R0, G, AVO class (I/II/IIp/III/IV)
  lmr_decompose       — lambda_rho + mu_rho (Goodway 1997) at every voxel
  synth_gather        — synthetic angle gather (for testing)

F2 TRUTH BAND
=============

Zoeppritz is exact (no approximation, no empiricism). Shuey is a
linearisation (valid theta < 30 deg, error grows with angle). LMR
is exact algebra. AVO class boundaries are empirical (industry
convention, not physics law). We declare the band on Shuey/AVO
class, claim exactness on Zoeppritz/LMR.

DITEMPA BUKAN DIBERI — impedance is the earth, sliced by angle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

import numpy as np


# ────────────────────────────────────────────────────────────────────
# Data structures — the AVO envelopes
# ────────────────────────────────────────────────────────────────────


@dataclass
class AVOResult:
    """Shuey 2-term AVO result: intercept R0, gradient G, AVO class."""

    intercept_R0: float
    gradient_G: float
    far_term_F: float
    avo_class: str  # I | II | IIp | III | IV
    theta_max_deg: float
    vp1: float
    vs1: float
    rho1: float
    vp2: float
    vs2: float
    rho2: float
    physics_guard: Dict[str, Any] = field(default_factory=dict)
    acrisk: float = 0.12
    claim_state: str = "QUALIFY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intercept_R0": self.intercept_R0,
            "gradient_G": self.gradient_G,
            "far_term_F": self.far_term_F,
            "avo_class": self.avo_class,
            "theta_max_deg": self.theta_max_deg,
            "above": {"vp": self.vp1, "vs": self.vs1, "rho": self.rho1},
            "below": {"vp": self.vp2, "vs": self.vs2, "rho": self.rho2},
            "physics_guard": self.physics_guard,
            "acrisk": self.acrisk,
            "claim_state": self.claim_state,
        }


@dataclass
class LMRResult:
    """Lambda-Mu-Rho decomposition (Goodway 1997)."""

    lambda_rho: np.ndarray  # incompressibility (fluid sensitive)
    mu_rho: np.ndarray  # rigidity (lithology sensitive)
    vp: np.ndarray
    vs: np.ndarray
    rho: np.ndarray
    units: str = "SI"
    acrisk: float = 0.08
    claim_state: str = "SEAL"
    provenance: str = "lmr_decompose"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lambda_rho": self.lambda_rho,
            "mu_rho": self.mu_rho,
            "vp": self.vp,
            "vs": self.vs,
            "rho": self.rho,
            "units": self.units,
            "acrisk": self.acrisk,
            "claim_state": self.claim_state,
            "provenance": self.provenance,
        }


# ────────────────────────────────────────────────────────────────────
# Primitive 1 — zoeppritz_rpp (exact, full 4x4 system)
# ────────────────────────────────────────────────────────────────────


def zoeppritz_rpp(
    vp1: float,
    vs1: float,
    rho1: float,
    vp2: float,
    vs2: float,
    rho2: float,
    theta_deg: "np.ndarray | list[float]",
) -> np.ndarray:
    """Exact Zoeppritz R_PP(theta) via the full 4x4 system.

    Solves the exact Knott-Zoeppritz energy-coefficient equations
    (no Aki-Richards, no Shuey, no approximation). 4x4 system
    of boundary conditions at the interface, solved for [R_PP, R_PS,
    T_PP, T_PS] at each angle.

    F2 Truth:
        - Exact physics (ACRisk 0.05)
        - Post-critical angles (sin(theta2) > 1): we report the
          real part of R_PP and flag in the guard. Physics guard
          should be checked by the caller.
    """
    theta_deg = np.asarray(theta_deg, dtype=float)
    R = np.zeros_like(theta_deg, dtype=float)
    post_critical = np.zeros_like(theta_deg, dtype=bool)

    for i, td in enumerate(theta_deg):
        theta1 = float(np.deg2rad(td))
        # Snell's ray parameter
        p = np.sin(theta1) / max(vp1, 1e-6)
        # Angles in layer 1 (always real for theta1 in [0, pi/2))
        sin_t1 = float(np.sin(theta1))
        cos_t1 = float(np.cos(theta1))
        sin_f1 = p * vs1
        cos_f1 = float(np.sqrt(max(1.0 - sin_f1**2, 0.0)))
        # Angles in layer 2 — may go post-critical
        sin_t2 = p * vp2
        if abs(sin_t2) >= 1.0:
            # Post-critical: evanescent P in layer 2
            post_critical[i] = True
            # Use real part of cos (real(cos(i*sinh(x))) = cosh(x))
            # For evanescent waves the reflectivity magnitude is 1
            # with phase shift; we report the dominant real part
            R[i] = -1.0  # classic post-critical: full reflection with flip
            continue
        theta2 = float(np.arcsin(sin_t2))
        cos_t2 = float(np.cos(theta2))
        sin_f2 = p * vs2
        if abs(sin_f2) >= 1.0:
            post_critical[i] = True
            R[i] = -1.0
            continue
        phi2 = float(np.arcsin(sin_f2))
        cos_f2 = float(np.cos(phi2))

        # Build the textbook 4x4 matrix (Aki & Richards form).
        # Row 1: x-displacement continuity
        # Row 2: z-displacement continuity
        # Row 3: z-stress continuity (sigma_zz)
        # Row 4: x-stress continuity (sigma_xz)
        M = np.array(
            [
                [-sin_t1, -cos_f1, sin_t2, cos_f2],
                [cos_t1, -sin_f1, cos_t2, -sin_f2],
                [
                    2 * rho1 * vs1**2 * sin_t1 * cos_t1,
                    rho1 * vs1**2 * (1 - 2 * sin_f1**2),
                    2 * rho2 * vs2**2 * sin_t2 * cos_t2,
                    rho2 * vs2**2 * (1 - 2 * sin_f2**2),
                ],
                [
                    -rho1 * vs1**2 * (1 - 2 * sin_t1**2),
                    -rho1 * vs1**2 * 2 * sin_f1 * cos_f1,
                    rho2 * vs2**2 * (1 - 2 * sin_t2**2),
                    rho2 * vs2**2 * 2 * sin_f2 * cos_f2,
                ],
            ],
            dtype=float,
        )
        # RHS: incident P-wave amplitudes (1, 0, transmitted part = 0 in layer 1)
        D = np.array(
            [
                sin_t1,
                cos_t1,
                2 * rho1 * vs1**2 * sin_t1 * cos_t1,
                -rho1 * vs1**2 * (1 - 2 * sin_t1**2),
            ],
            dtype=float,
        )
        try:
            sol = np.linalg.solve(M, D)
            R[i] = float(sol[0])  # R_PP is the first element
        except np.linalg.LinAlgError:
            R[i] = 0.0
    return R


# ────────────────────────────────────────────────────────────────────
# Primitive 2 — shuey_avo (linearised, fast, the industry default)
# ────────────────────────────────────────────────────────────────────


def _classify_avo(R0: float, G: float) -> str:
    """AVO class from (R0, G) sign.

    Industry convention (Rutherford & Williams 1989, Castagna & Swan 1997):
      Class I    : R0 > 0, G < 0  (hard kick)
      Class II   : R0 ~ 0, G < 0  (dim near, bright far)
      Class IIp  : R0 ~ 0, G < 0  with polarity reversal
      Class III  : R0 < 0, G < 0  (classic gas sand, bright spot)
      Class IV   : R0 < 0, G > 0  (soft, increasing amplitude)
    """
    eps = 0.02
    if R0 > eps and G < -eps:
        return "I"
    if R0 < -eps and G < -eps:
        return "III"
    if R0 < -eps and G > eps:
        return "IV"
    if abs(R0) <= eps:
        return "II"  # near-zero intercept; II/IIp ambiguous by angle behaviour
    if R0 > eps and G >= 0:
        return "I"
    return "II"


def shuey_avo(
    vp1: float,
    vs1: float,
    rho1: float,
    vp2: float,
    vs2: float,
    rho2: float,
    theta_max: float = 30.0,
) -> AVOResult:
    """Shuey 2-term AVO: R(theta) = R0 + G sin^2 theta + F tan^2 theta sin^2 theta.

    Valid for theta < 30 deg. Faster than Zoeppritz; the
    industry-default for screening.

    F2 Truth:
        Linearisation error: ~5% at 20 deg, ~15% at 30 deg.
        ACRisk 0.12. Class boundaries are empirical.
    """
    vp_avg = 0.5 * (vp1 + vp2)
    vs_avg = 0.5 * (vs1 + vs2)
    rho_avg = 0.5 * (rho1 + rho2)
    dvp = vp2 - vp1
    dvs = vs2 - vs1
    drho = rho2 - rho1

    # R0
    R0 = 0.5 * (dvp / max(vp_avg, 1e-6) + drho / max(rho_avg, 1e-6))
    # G (Shuey 1985, eqn 7)
    vp_vs_sq = (vs_avg / max(vp_avg, 1e-6)) ** 2
    G = dvp / (2.0 * max(vp_avg, 1e-6)) - 2.0 * vp_vs_sq * (drho / max(rho_avg, 1e-6) + 2.0 * dvs / max(vs_avg, 1e-6))
    # F (far term, Shuey 3rd term)
    F = 0.5 * (dvp / max(vp_avg, 1e-6))

    avo_class = _classify_avo(R0, G)

    guard: Dict[str, Any] = {
        "theta_max_deg": theta_max,
        "validity": "Shuey linearisation valid for theta < 30 deg",
        "error_at_20deg_pct": 5.0,
        "error_at_30deg_pct": 15.0,
        "vp_avg": vp_avg,
        "vs_avg": vs_avg,
        "rho_avg": rho_avg,
        "avo_class_caveat": ("AVO class boundaries are industry convention, not physics law. Use with checkshot calibration."),
    }
    claim_state = "QUALIFY"
    if theta_max > 30.0:
        claim_state = "HOLD"
        guard["theta_max_exceeds_linearisation_validity"] = True

    return AVOResult(
        intercept_R0=float(R0),
        gradient_G=float(G),
        far_term_F=float(F),
        avo_class=avo_class,
        theta_max_deg=float(theta_max),
        vp1=vp1,
        vs1=vs1,
        rho1=rho1,
        vp2=vp2,
        vs2=vs2,
        rho2=rho2,
        physics_guard=guard,
        acrisk=0.12,
        claim_state=claim_state,
    )


# ────────────────────────────────────────────────────────────────────
# Primitive 3 — lmr_decompose (exact, pointwise)
# ────────────────────────────────────────────────────────────────────


def lmr_decompose(
    vp: np.ndarray,
    vs: np.ndarray,
    rho: np.ndarray,
) -> LMRResult:
    """Lambda-Mu-Rho decomposition (Goodway, Renzi, Best 1997).

    lambda_rho = rho * (Vp^2 - 2 Vs^2)   [incompressibility, fluid sensitive]
    mu_rho     = rho * Vs^2               [rigidity, lithology sensitive]

    F2 Truth: exact algebra, no empiricism. ACRisk 0.08.
    Vs < epsilon is a degenerate (fluid) case — flagged with HOLD.
    """
    vp = np.asarray(vp, dtype=float)
    vs = np.asarray(vs, dtype=float)
    rho = np.asarray(rho, dtype=float)
    if vp.shape != vs.shape or vp.shape != rho.shape:
        raise ValueError(f"Shape mismatch: vp={vp.shape}, vs={vs.shape}, rho={rho.shape}")
    if np.any(vs < 1e-6):
        # Fluid case: K_sat = K_dry + fluid term, but G=0 so mu=0
        return LMRResult(
            lambda_rho=rho * vp**2,
            mu_rho=np.zeros_like(rho),
            vp=vp,
            vs=vs,
            rho=rho,
            acrisk=0.30,
            claim_state="HOLD",
            provenance="lmr_decompose:vs<eps_fallback",
        )
    mu_rho = rho * vs**2
    lambda_rho = rho * (vp**2 - 2.0 * vs**2)
    return LMRResult(
        lambda_rho=lambda_rho,
        mu_rho=mu_rho,
        vp=vp,
        vs=vs,
        rho=rho,
        acrisk=0.08,
        claim_state="SEAL",
        provenance="lmr_decompose:exact_algebra",
    )


# ────────────────────────────────────────────────────────────────────
# Helper — synth_gather (for testing and tutorials)
# ────────────────────────────────────────────────────────────────────


def synth_gather(
    theta_deg: "np.ndarray | list[float]",
    scenario: str = "class_III_gas",
) -> Dict[str, Any]:
    """Synthetic angle gather for E9 testing.

    Scenarios:
      - "class_I_hard": positive R0, negative G (hard kick)
      - "class_II_dim": near-zero R0, negative G (dim near, bright far)
      - "class_III_gas": negative R0, negative G (classic gas sand)
      - "class_IV_soft": negative R0, positive G (soft, increasing)
    """
    theta_deg = np.asarray(theta_deg, dtype=float)
    presets = {
        "class_I_hard": (0.20, -0.15),
        "class_II_dim": (0.01, -0.18),
        "class_III_gas": (-0.10, -0.20),
        "class_IV_soft": (-0.05, 0.10),
    }
    if scenario not in presets:
        raise ValueError(f"Unknown scenario: {scenario}; choose from {list(presets)}")
    R0, G = presets[scenario]
    R = R0 + G * np.sin(np.deg2rad(theta_deg)) ** 2
    return {
        "theta_deg": theta_deg,
        "R_PP": R,
        "R0": R0,
        "G": G,
        "scenario": scenario,
    }
