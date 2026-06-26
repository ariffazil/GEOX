"""
GEOX-LEM Physics Organ — External Teach/Guard/Score Engine
══════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

This is the EXTERNAL physics organ — not baked into any FM loss.
It operates alongside the three FMs as a sovereign constitutional organ.

Three operations:
  1. TEACH  — generate synthetic training data via forward physics models
  2. GUARD  — penalize physically impossible latent states (post-hoc)
  3. SCORE  — epistemic uncertainty + feasibility + causality violation

This organ is callable as an MCP tool. It does not require GPU.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("geox.lem.physics_organ")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    torch = None
    nn = None
    F = None


# ── Physics Constants (CANON-9 aligned) ─────────────────────────────────────

@dataclass
class PhysicsDefaults:
    """Default physics parameters — single source of truth."""
    rw: float = 0.05               # Formation water resistivity (ohm.m)
    archie_a: float = 1.0          # Archie tortuosity factor
    archie_m: float = 2.0          # Archie cementation exponent
    archie_n: float = 2.0          # Archie saturation exponent
    rho_matrix: float = 2.65       # Matrix density (g/cc) — quartz
    rho_fluid: float = 1.0         # Fluid density (g/cc) — fresh water
    gardner_alpha: float = 310.0   # Gardner density coefficient
    gardner_beta: float = 0.25     # Gardner exponent
    faust_a: float = 2000.0        # Faust velocity coefficient
    faust_c: float = 0.5           # Faust exponent
    phi_max: float = 0.45          # Maximum porosity
    sw_max: float = 1.0            # Maximum water saturation
    vsh_max: float = 1.0           # Maximum shale volume


PHYSICS = PhysicsDefaults()


# ── TEACH: Synthetic Data Generation ───────────────────────────────────────

class PhysicsTeacher:
    """
    TEACH operation: Generate synthetic training data from forward models.
    
    This is how the physics organ teaches the FMs what physically
    valid Earth looks like — without baking physics into their losses.
    """

    @staticmethod
    def synthetic_well_logs(
        n_wells: int = 10,
        n_samples_per_well: int = 1000,
        seed: int = 42,
    ) -> dict[str, np.ndarray]:
        """
        Generate synthetic well logs that obey rock physics.
        
        Returns dict with curves, depth, and ground-truth properties.
        """
        rng = np.random.RandomState(seed)
        
        # Generate depth
        depth = np.arange(n_samples_per_well, dtype=float)
        
        # Generate ground-truth Vsh, phi, Sw with geological patterns
        vsh_true = 0.3 + 0.4 * np.sin(depth / 200.0 * np.pi) + 0.1 * rng.randn(n_samples_per_well)
        vsh_true = np.clip(vsh_true, 0.02, 0.95)
        
        phi_true = 0.15 + 0.15 * np.cos(depth / 150.0 * np.pi) + 0.03 * rng.randn(n_samples_per_well)
        phi_true = np.clip(phi_true, 0.02, PHYSICS.phi_max)
        
        sw_true = 0.3 + 0.4 * (1.0 - np.exp(-depth / 500.0)) + 0.05 * rng.randn(n_samples_per_well)
        sw_true = np.clip(sw_true, 0.1, 1.0)
        
        # Forward model to generate curves
        # GR: linear with Vsh
        gr = 30.0 + 120.0 * vsh_true + 5.0 * rng.randn(n_samples_per_well)
        
        # RHOB from density-porosity
        rhob = PHYSICS.rho_matrix * (1.0 - phi_true) + PHYSICS.rho_fluid * phi_true
        rhob += 0.02 * rng.randn(n_samples_per_well)
        
        # RT from Archie
        rt = (PHYSICS.archie_a * PHYSICS.rw) / (phi_true ** PHYSICS.archie_m * sw_true ** PHYSICS.archie_n)
        rt += 0.1 * rt * rng.randn(n_samples_per_well)
        rt = np.clip(rt, 0.1, 1000.0)
        
        # NPHI: neutron porosity ≈ φ + Vsh * phi_clay
        nphi = phi_true + 0.15 * vsh_true + 0.01 * rng.randn(n_samples_per_well)
        
        # DT: sonic, from Wyllie time-average or Faust
        dt = 55.0 + 40.0 * phi_true + 20.0 * vsh_true + 2.0 * rng.randn(n_samples_per_well)
        
        return {
            "depth": depth,
            "GR": gr,
            "RT": rt,
            "RHOB": rhob,
            "NPHI": nphi,
            "DT": dt,
            "Vsh_true": vsh_true,
            "phi_true": phi_true,
            "Sw_true": sw_true,
            "n_wells": n_wells,
            "n_samples": n_samples_per_well,
        }

    @staticmethod
    def synthetic_seismic_trace(
        n_traces: int = 100,
        n_samples: int = 256,
        dt: float = 0.004,
        seed: int = 42,
    ) -> dict[str, np.ndarray]:
        """
        Generate synthetic seismic trace from reflectivity series.
        
        Uses random reflectivity + Ricker wavelet convolution.
        """
        rng = np.random.RandomState(seed)
        
        # Random reflectivity
        reflectivity = 0.02 * rng.randn(n_traces, n_samples)
        
        # Ricker wavelet (30 Hz)
        fc = 30.0
        t = np.arange(-0.06, 0.06, dt)
        wavelet = (1.0 - 2.0 * (np.pi * fc * t) ** 2) * np.exp(-(np.pi * fc * t) ** 2)
        
        # Convolve
        from scipy import signal
        seismic = np.array([signal.fftconvolve(r, wavelet, mode='same') for r in reflectivity])
        
        return {
            "seismic": seismic,
            "reflectivity": reflectivity,
            "wavelet": wavelet,
            "dt": dt,
            "n_traces": n_traces,
            "n_samples": n_samples,
        }


# ── GUARD: Physics Constraint Check ─────────────────────────────────────────

@dataclass
class PhysicsGuardResult:
    """Result of a physics guard check."""
    passed: bool
    violations: list[dict[str, Any]]
    score_pct: float  # 0-100, lower = more violations
    details: dict[str, Any] = field(default_factory=dict)


class PhysicsGuard:
    """
    GUARD operation: Check any latent state or prediction against physics.
    
    This is a stateless function — no training, no weights.
    Callable as MCP tool from any organ.
    """

    @staticmethod
    def check_petrophysics(
        vsh: np.ndarray,
        phi: np.ndarray,
        sw: np.ndarray,
        rt: Optional[np.ndarray] = None,
    ) -> PhysicsGuardResult:
        """Check petrophysical predictions against CANON-9 bounds + Archie."""
        violations: list[dict[str, Any]] = []
        
        # Bound checks
        if np.any(vsh < 0) or np.any(vsh > PHYSICS.vsh_max):
            violations.append({
                "rule": "vsh_bounds",
                "detail": f"Vsh range [{vsh.min():.3f}, {vsh.max():.3f}] exceeds [0, {PHYSICS.vsh_max}]",
                "severity": "error"
            })
        
        if np.any(phi < 0) or np.any(phi > PHYSICS.phi_max):
            violations.append({
                "rule": "phi_bounds",
                "detail": f"Phi range [{phi.min():.3f}, {phi.max():.3f}] exceeds [0, {PHYSICS.phi_max}]",
                "severity": "error"
            })
        
        if np.any(sw < 0) or np.any(sw > PHYSICS.sw_max):
            violations.append({
                "rule": "sw_bounds",
                "detail": f"Sw range [{sw.min():.3f}, {sw.max():.3f}] exceeds [0, {PHYSICS.sw_max}]",
                "severity": "error"
            })
        
        # Archie consistency (if RT provided)
        if rt is not None and len(rt) > 0:
            phi_clamped = np.clip(phi, 0.01, PHYSICS.phi_max)
            rt_clamped = np.clip(rt, 0.01, None)
            sw_archie = (
                (PHYSICS.archie_a * PHYSICS.rw) / 
                (rt_clamped * phi_clamped ** PHYSICS.archie_m)
            ) ** (1.0 / PHYSICS.archie_n)
            sw_archie = np.clip(sw_archie, 0, PHYSICS.sw_max)
            
            archie_diff = np.abs(sw - sw_archie).mean()
            if archie_diff > 0.15:
                violations.append({
                    "rule": "archie_consistency",
                    "detail": f"Mean |Sw - Sw_Archie| = {archie_diff:.3f} > 0.15",
                    "severity": "warning",
                    "archie_diff": float(archie_diff)
                })
        
        # Score
        score = max(0.0, 100.0 - len(violations) * 25.0)
        if len(violations) == 0:
            score = 100.0
        
        return PhysicsGuardResult(
            passed=len(violations) == 0,
            violations=violations,
            score_pct=score,
            details={
                "vsh_range": [float(vsh.min()), float(vsh.max())],
                "phi_range": [float(phi.min()), float(phi.max())],
                "sw_range": [float(sw.min()), float(sw.max())],
            }
        )

    @staticmethod
    def check_rock_physics(
        vp: np.ndarray,
        density: np.ndarray,
    ) -> PhysicsGuardResult:
        """Check Vp-density consistency via Gardner."""
        violations: list[dict[str, Any]] = []
        
        vp_clamped = np.clip(vp, 1500.0, 6500.0)
        density_pred = PHYSICS.gardner_alpha * (vp_clamped ** PHYSICS.gardner_beta) / 1000.0  # g/cc
        
        gardner_diff = np.abs(density - density_pred).mean()
        if gardner_diff > 0.25:
            violations.append({
                "rule": "gardner_consistency",
                "detail": f"Mean |density - Gardner(density)| = {gardner_diff:.3f} g/cc > 0.25",
                "severity": "warning",
                "gardner_diff": float(gardner_diff)
            })
        
        score = 100.0 if len(violations) == 0 else 50.0
        return PhysicsGuardResult(
            passed=len(violations) == 0,
            violations=violations,
            score_pct=score,
        )


# ── SCORE: Epistemic Uncertainty + Feasibility + Causality ──────────────────

@dataclass
class PhysicsScore:
    """Score from the physics organ."""
    epistemic_uncertainty: float  # 0-1, higher = more uncertain
    feasibility: float            # 0-1, higher = more feasible
    causality_violation: bool     # True if physics-causality chain is broken
    details: dict[str, Any] = field(default_factory=dict)


class PhysicsScorer:
    """
    SCORE operation: Quantify uncertainty, feasibility, and causality.
    
    This is what GEOX returns alongside every prediction.
    """

    @staticmethod
    def score_prediction(
        prediction: dict[str, np.ndarray],
        input_coverage: dict[str, float],
    ) -> PhysicsScore:
        """
        Score a prediction based on:
          - Epistemic uncertainty (how much data was available)
          - Feasibility (do the outputs obey physics?)
          - Causality (is the inference chain valid?)
        """
        # Epistemic uncertainty from input coverage
        # Less coverage = more uncertainty
        n_inputs = sum(1 for v in input_coverage.values() if v > 0)
        total_inputs = len(input_coverage)
        coverage_ratio = n_inputs / max(total_inputs, 1)
        
        epistemic = 1.0 - coverage_ratio  # 0 = all inputs, 1 = no inputs
        
        # Feasibility from physics guard
        guard = PhysicsGuard()
        if "vsh" in prediction and "phi" in prediction and "sw" in prediction:
            result = guard.check_petrophysics(
                prediction["vsh"],
                prediction["phi"],
                prediction["sw"],
                prediction.get("rt"),
            )
            feasibility = result.score_pct / 100.0
        else:
            feasibility = 0.5  # Unknown
        
        # Causality violation detection
        causality_violation = False
        if feasibility < 0.3:
            causality_violation = True  # Physics-infeasible outputs = causality broken
        
        return PhysicsScore(
            epistemic_uncertainty=float(epistemic),
            feasibility=float(feasibility),
            causality_violation=causality_violation,
            details={
                "input_coverage": input_coverage,
                "n_inputs_available": n_inputs,
                "n_inputs_total": total_inputs,
            }
        )


# ── Physics Organ Public API ────────────────────────────────────────────────

class PhysicsOrgan:
    """
    Sovereign physics organ for GEOX-LEM.
    
    Three operations:
      organ.teach(mode='well_logs')  → synthetic training data
      organ.guard(vsh, phi, sw, ...) → constraint check
      organ.score(pred, coverage)    → epistemic + feasibility + causality
    """

    def __init__(self):
        self.teacher = PhysicsTeacher()
        self.guard = PhysicsGuard()
        self.scorer = PhysicsScorer()

    def teach(self, mode: str = "well_logs", **kwargs) -> dict[str, Any]:
        """Generate synthetic training data from forward physics."""
        if mode == "well_logs":
            return self.teacher.synthetic_well_logs(**kwargs)
        elif mode == "seismic":
            return self.teacher.synthetic_seismic_trace(**kwargs)
        else:
            raise ValueError(f"Unknown teach mode: {mode}")

    def guard(self, **kwargs) -> PhysicsGuardResult:
        """Check any prediction against physics constraints."""
        return self.guard.check_petrophysics(**kwargs)

    def score(self, prediction: dict, coverage: dict) -> PhysicsScore:
        """Score uncertainty + feasibility + causality."""
        return self.scorer.score_prediction(prediction, coverage)


__all__ = [
    "PhysicsOrgan",
    "PhysicsTeacher",
    "PhysicsGuard",
    "PhysicsScorer",
    "PhysicsGuardResult",
    "PhysicsScore",
    "PHYSICS",
]
