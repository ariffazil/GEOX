"""glphase_switcher.py — Constitutive regime switcher for GLOF cascade.

Three yield surfaces evaluated per (state, stress) pair:

    1. Mohr-Coulomb (granular / dam failure):
           tau = c + (sigma_n - u) * tan(phi)
       Switch GRANULAR -> plastic when tau_applied > tau_max.

    2. Voellmy-Salm (ice avalanche flow):
           tau = tau_0 + mu*sigma_n + rho*v^2/xi
       Switch GRANULAR -> Voellmy-fluid when v > v_crit.

    3. Bingham-Herschel-Bulkley (debris flow surge):
           tau = tau_0 + eta * gamma_dot^n
       Switch SOLID/GRANULAR -> FLUID when saturation > S_crit
       AND tau_0 < tau_applied.

Also: Linear-Elastic Fracture Mechanics (LEFM) for tensile failure:
       sigma > sigma_t  ->  fracture (K_IC governs crack growth)
       Switch SOLID -> GRANULAR via tensile cracking.

Conservative ordering — only one phase transition per evaluation.
Velocity- and pressure-driven regimes evaluated against current state vector.

DITEMPA BUKAN DIBERI — phase is computed, not asserted.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from geox_core.physics.glgeomaterial import (
    GLOFMaterialState, MaterialPhase, Bounds,
)

# Empirical thresholds from Himalayan / Alpine GLOF literature
V_CRIT_AVALANCHE = 5.0      # m/s   threshold for granular -> Voellmy flow
S_CRIT_LIQUEFACTION = 0.90   # -    saturation threshold for liquefaction
SIGMA_T_FACTOR = 1.2         # safety factor on tensile strength


@dataclass
class YieldVerdict:
    """Result of one yield-surface evaluation."""
    current_phase: MaterialPhase
    next_phase: MaterialPhase
    failure_mode: str          # "stable" / "mohr_coulomb" / "voellmy" / "tensile" / "bingham"
    tau_applied: float         # Pa
    tau_resisted: float        # Pa
    margin: float              # (resisted - applied) / resisted, <0 means failure
    fracture_K: float          # stress intensity (Pa*m^0.5), 0 if not computed

    @property
    def fails(self) -> bool:
        return self.margin < 0.0

    @property
    def transitions(self) -> bool:
        return self.current_phase != self.next_phase


# ============================================================== Mohr-Coulomb
def evaluate_mohr_coulomb(
    s: GLOFMaterialState, sigma_n: float, tau_applied: float,
) -> Tuple[float, float]:
    """Mohr-Coulomb shear strength at given normal stress.

    tau_max = c + (sigma_n - u) * tan(phi)

    Returns (tau_resisted, margin_ratio). margin < 0 -> shear failure.
    """
    phi_eff = max(s.phi, 1e-3)  # avoid tan(0) singularity
    u = s.Pp
    tau_max = s.c + max(sigma_n - u, 0.0) * math.tan(phi_eff)
    if tau_max <= 0:
        return (0.0, -1.0)
    margin = (tau_max - tau_applied) / tau_max
    return (tau_max, margin)


# ============================================================== LEFM
def evaluate_tensile(
    s: GLOFMaterialState, sigma_applied: float,
    crack_length_m: float = 1.0,
) -> Tuple[float, float]:
    """Linear-elastic fracture mechanics — mode I.

    K_I = sigma_applied * sqrt(pi * a)
    Failure: K_I > K_IC = sigma_t * sqrt(pi * a_crit)

    For simplicity (no separate K_IC param): margin on sigma_applied vs
    sigma_t * safety factor.

    Returns (sigma_resisted, margin_ratio).
    """
    sigma_resisted = s.sigma_t * SIGMA_T_FACTOR
    if sigma_resisted <= 0:
        return (0.0, -1.0)
    margin = (sigma_resisted - sigma_applied) / sigma_resisted
    # Stress intensity (informational, for UI)
    K_I = sigma_applied * math.sqrt(math.pi * crack_length_m)
    return (sigma_resisted, margin)


# ============================================================== Voellmy-Salm
def evaluate_voellmy(
    s: GLOFMaterialState, sigma_n: float, velocity: float,
    mu: float = 0.15, xi: float = 1000.0,
) -> Tuple[float, float]:
    """Voellmy-Salm rheology for granular avalanche flow.

    tau = tau_0 + mu*sigma_n + rho*v^2/xi

    Returns (tau_resisted, margin_ratio). Margin < 0 -> flow regime unstable.
    """
    v = max(velocity, 0.0)
    tau = s.tau_0 + mu * max(sigma_n, 0.0) + s.rho * v * v / xi
    # Use a reference stress scale of tau_0 + rho*g*h with h=10m for normalization
    ref = max(s.tau_0 + s.rho * 9.81 * 10.0, 1.0)
    margin = 1.0 - tau / ref
    return (tau, margin)


# ============================================================== Bingham-H-B
def evaluate_bingham(
    s: GLOFMaterialState, gamma_dot: float,
    eta: float = 0.05, n: float = 1.0,
) -> Tuple[float, float]:
    """Bingham-Herschel-Bulkley rheology for debris flow.

    tau = tau_0 + eta * gamma_dot^n

    gamma_dot = strain rate (1/s)
    Returns (tau_resisted, margin_ratio).
    """
    gdot = max(gamma_dot, 0.0)
    tau = s.tau_0 + eta * (gdot ** n)
    ref = max(s.tau_0 + eta * 10.0, 1.0)  # reference: gamma_dot = 10
    margin = 1.0 - tau / ref
    return (tau, margin)


# ============================================================== Master evaluator
def evaluate_cascade(
    s: GLOFMaterialState,
    sigma_n: float,
    tau_applied: float,
    velocity: float = 0.0,
    sigma_applied: float = 0.0,
    saturation: float = None,
) -> YieldVerdict:
    """Master evaluator — picks dominant yield surface per state.

    Order (most specific to least):
        1. Tensile (if sigma_applied provided and >0)
        2. Liquefaction (if saturation > S_CRIT_LIQUEFACTION)
        3. Voellmy (if velocity > V_CRIT_AVALANCHE)
        4. Mohr-Coulomb (default granular check)

    Transitions:
        SOLID -> GRANULAR on tensile fracture or MC shear failure
        GRANULAR -> FLUID on liquefaction or high-velocity Voellmy
        FLUID -> SOLID (re-freeze): no transition (constitutive only)
    """
    cur = s.phase_id
    nxt = cur
    mode = "stable"
    tau_r, tau_a = 0.0, tau_applied
    margin = 1.0
    K_I = 0.0

    sat = saturation if saturation is not None else s.saturation

    # ---- 1. Tensile check (LEFM) — applies mostly to SOLID
    if sigma_applied > 0 and s.sigma_t > 0:
        sigma_r, m = evaluate_tensile(s, sigma_applied)
        K_I = sigma_applied * math.sqrt(math.pi * 1.0)
        if m < 0:
            nxt = MaterialPhase.GRANULAR
            mode = "tensile"
            margin = m
            return YieldVerdict(cur, nxt, mode, tau_applied, 0.0, margin, K_I)

    # ---- 2. Liquefaction — granular -> fluid
    if sat >= S_CRIT_LIQUEFACTION and s.tau_0 > 0:
        # Liquefied if tau_0 is below gravity-induced stress threshold
        g_stress = s.rho * 9.81 * 5.0  # 5m column reference
        if s.tau_0 < g_stress:
            nxt = MaterialPhase.FLUID
            mode = "liquefaction"
            margin = (s.tau_0 - g_stress) / g_stress
            return YieldVerdict(cur, nxt, mode, tau_applied, s.tau_0, margin, K_I)

    # ---- 3. Voellmy — high velocity granular flow
    if velocity >= V_CRIT_AVALANCHE:
        tau_r, m = evaluate_voellmy(s, sigma_n, velocity)
        mode = "voellmy"
        margin = m
        if m < -0.05:  # tolerant: small negative margin still flows but stable
            nxt = MaterialPhase.FLUID
        return YieldVerdict(cur, nxt, mode, tau_applied, tau_r, margin, K_I)

    # ---- 4. Mohr-Coulomb — default shear failure
    tau_r, m = evaluate_mohr_coulomb(s, sigma_n, tau_applied)
    mode = "mohr_coulomb"
    margin = m
    if m < 0:
        nxt = MaterialPhase.GRANULAR

    return YieldVerdict(cur, nxt, mode, tau_applied, tau_r, margin, K_I)


# ============================================================== Sequence driver
def phase_sequence(s0: GLOFMaterialState, loads: list) -> list:
    """Evaluate a sequence of load events and return YieldVerdicts.

    Useful for GLOF cascade:
        loads = [
            {"sigma_n": 500e3, "tau_applied": 80e3,  "saturation": 0.1},  # dry
            {"sigma_n": 500e3, "tau_applied": 80e3,  "saturation": 0.5},  # filling
            {"sigma_n": 500e3, "tau_applied": 80e3,  "saturation": 0.95}, # critical
            {"sigma_n": 100e3, "tau_applied": 200e3, "velocity": 8.0},   # breach
        ]
    """
    from dataclasses import replace
    s = s0
    results = []
    for ev in loads:
        v = evaluate_cascade(
            s,
            sigma_n=ev.get("sigma_n", 0.0),
            tau_applied=ev.get("tau_applied", 0.0),
            velocity=ev.get("velocity", 0.0),
            sigma_applied=ev.get("sigma_applied", 0.0),
            saturation=ev.get("saturation"),
        )
        # Update state to next phase if transition (preserve Enum)
        if v.transitions:
            s = replace(s, phase_id=v.next_phase)
        results.append(v)
    return results


if __name__ == "__main__":
    from geox_core.physics.glgeomaterial import himalayan_defaults

    s0 = himalayan_defaults()
    # GLOF cascade scenario
    loads = [
        {"sigma_n": 500e3, "tau_applied": 80e3,  "saturation": 0.1},   # t=0
        {"sigma_n": 500e3, "tau_applied": 80e3,  "saturation": 0.5},   # t+45min
        {"sigma_n": 500e3, "tau_applied": 80e3,  "saturation": 0.95},  # t+90min
        {"sigma_n": 100e3, "tau_applied": 200e3, "velocity": 8.0},     # t+135min breach
    ]
    for t, v in enumerate(phase_sequence(s0, loads)):
        flag = " *FAIL*" if v.fails else ""
        flag2 = " -> " + v.next_phase.value if v.transitions else ""
        print(f"t+{t*45:3d}min : {v.current_phase.value:8s}{flag2:12s} "
              f"mode={v.failure_mode:14s} margin={v.margin:+.3f}{flag}")