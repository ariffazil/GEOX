"""
GEOX physics9.py — EARTH.CANON_9 Canonical State Engine
DITEMPA BUKAN DIBERI | OMEGA / 888_JUDGE

9 Canonical State Variables:
  ρ  density       (kg/m³)     1000–5000
  Vp P-wave        (m/s)       1500–6000
  Vs S-wave        (m/s)       500–3500
  ρₑ resistivity   (Ω·m)        0.1–10000
  χ  magnetics     (SI)         -0.1–0.5
  k  thermal       (W/mK)      0.5–8.0
  P  pressure      (Pa)         1e6–100e6
  T  temperature   (K)          273–500
  φ  porosity      (frac)      0–0.45

Contrast = deviation from background normal.
Forward-Inverse Metabolic Loop: forward model ↔ inverse estimation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math

# ─── EARTH.CANON_9 Canonical State ──────────────────────────────────────────

@dataclass
class Physics9State:
    rho: float       # kg/m³
    vp: float        # m/s
    vs: float        # m/s
    rho_e: float     # Ω·m resistivity
    chi: float       # SI magnetics
    k: float         # W/mK thermal conductivity
    P: float         # Pa pressure
    T: float         # K temperature
    phi: float       # fraction porosity

    def to_vector(self) -> List[float]:
        return [self.rho, self.vp, self.vs, self.rho_e, self.chi, self.k, self.P, self.T, self.phi]

    @classmethod
    def from_vector(cls, v: List[float]) -> "Physics9State":
        return cls(rho=v[0], vp=v[1], vs=v[2], rho_e=v[3],
                   chi=v[4], k=v[5], P=v[6], T=v[7], phi=v[8])

    def arifos_grade(self) -> str:
        # Real quality gate — not performative
        if self.phi < 0.02 or self.phi > 0.45:
            return "RAW"
        if self.vp < 1500 or self.vp > 6000:
            return "RAW"
        if self.rho < 1000 or self.rho > 5000:
            return "RAW"
        # All in bounds
        return "AAA"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rho": self.rho, "vp": self.vp, "vs": self.vs,
            "rho_e": self.rho_e, "chi": self.chi, "k": self.k,
            "P": self.P, "T": self.T, "phi": self.phi,
            "grade": self.arifos_grade(),
        }

# ─── Earth Material Catalog ─────────────────────────────────────────────────

SANDSTONE  = Physics9State(rho=2350, vp=2950, vs=1680, rho_e=20,  chi=0.0001, k=2.8,  P=20e6, T=320, phi=0.25)
LIMESTONE  = Physics9State(rho=2710, vp=4300, vs=2500, rho_e=200, chi=0.00005,k=3.2,  P=30e6, T=340, phi=0.10)
DOLOMITE   = Physics9State(rho=2850, vp=5400, vs=2900, rho_e=100, chi=0.00006,k=3.0,  P=35e6, T=350, phi=0.08)
SHALE      = Physics9State(rho=2350, vp=2450, vs=1050, rho_e=10,  chi=0.004,  k=1.5,  P=25e6, T=330, phi=0.32)
ANHYDRITE  = Physics9State(rho=2970, vp=6000, vs=3200, rho_e=2000,chi=0.00002,k=4.1,  P=40e6, T=360, phi=0.01)
SALT       = Physics9State(rho=2160, vp=4500, vs=2300, rho_e=1e6, chi=0.00001,k=5.5,  P=15e6, T=310, phi=0.01)
COAL       = Physics9State(rho=1450, vp=2100, vs=1100, rho_e=500, chi=0.005,  k=0.3,  P=10e6, T=300, phi=0.08)
BASEMENT   = Physics9State(rho=2900, vp=5800, vs=3400, rho_e=500, chi=0.01,   k=2.5,  P=60e6, T=400, phi=0.02)

EARTH_MATERIAL_CATALOG: Dict[str, Physics9State] = {
    "Sandstone":    SANDSTONE,
    "Limestone":    LIMESTONE,
    "Dolomite":     DOLOMITE,
    "Shale":        SHALE,
    "Anhydrite":    ANHYDRITE,
    "Salt":         SALT,
    "Coal":         COAL,
    "Basement":     BASEMENT,
}

def compute_earth_material_catalog() -> Dict[str, Dict[str, float]]:
    return {
        name: {
            "rho": s.rho, "vp": s.vp, "vs": s.vs,
            "rho_e": s.rho_e, "chi": s.chi, "k": s.k,
            "P": s.P, "T": s.T, "phi": s.phi,
        }
        for name, s in EARTH_MATERIAL_CATALOG.items()
    }

# ─── Derived Physics ─────────────────────────────────────────────────────────

def _bulk_mod(vp: float, vs: float, rho: float) -> float:
    return rho * (vp**2 - (4/3) * vs**2)

def _shear_mod(vs: float, rho: float) -> float:
    return rho * vs**2

def _young_mod(K: float, G: float) -> float:
    return G * (3*K + G) / (K + G)

def _poisson_ratio(K: float, G: float) -> float:
    return (3*K - 2*G) / (6*K + 2*G)

def _ai(vp: float, rho: float) -> float:
    return vp * rho

def _vp_vs(vp: float, vs: float) -> float:
    return vp / max(vs, 0.001)

def _thermal_diff(k: float, rho: float, cp: float = 850) -> float:
    return k / (rho * cp)

def _fatigue_proxy(phi: float, delta_P: float, cycles: int = 1000) -> float:
    return phi * (delta_P / 1e6) * math.log(max(cycles, 1))

# ─── Forward physics9 ─────────────────────────────────────────────────────────

def forward_physics9(state: Physics9State) -> Dict[str, float]:
    """Compute all derived properties from canonical state."""
    K  = _bulk_mod(state.vp, state.vs, state.rho)
    G  = _shear_mod(state.vs, state.rho)
    ai = _ai(state.vp, state.rho)
    vp_vs = _vp_vs(state.vp, state.vs)
    E  = _young_mod(K, G)
    nu = _poisson_ratio(K, G)
    kappa = _thermal_diff(state.k, state.rho)
    fatigue = _fatigue_proxy(state.phi, state.P * 0.1)

    return {
        "K_GPa":           K / 1e9,
        "G_GPa":           G / 1e9,
        "E_GPa":           E / 1e9,
        "nu":              nu,
        "ai_kg_ms2":       ai,
        "vp_vs_ratio":     vp_vs,
        "thermal_diff":    kappa,
        "fatigue_proxy":   fatigue,
        "acoustic_impedance": ai,
    }

def build_lithology_model(state: Physics9State) -> Tuple[str, float, Dict[str, float]]:
    """Vp/Vs/ρ → lithology name + confidence + derived."""
    vp_vs = state.vp / max(state.vs, 0.001)

    if state.vp > 5500:
        litho, conf = "Dolomite", 0.85
    elif state.vp > 4000:
        litho, conf = "Limestone", 0.80
    elif state.vp > 3000 and vp_vs > 1.75:
        litho, conf = "Anhydrite", 0.75
    elif state.vp > 2800 and state.phi > 0.20:
        litho, conf = "Sandstone", 0.78
    elif state.vp < 2500 and state.vs < 1200:
        litho, conf = "Shale", 0.82
    elif state.vp < 2200 and state.rho < 1700:
        litho, conf = "Coal", 0.70
    else:
        litho, conf = "Mixed", 0.50

    derived = forward_physics9(state)
    return litho, conf, derived

# ─── Theory of Anomalous Contrast ───────────────────────────────────────────

def anomaly_contrast_theory(
    background: Physics9State,
    observed: Physics9State,
) -> Dict[str, Any]:
    """
    AC_Risk = u_ambiguity × D_transform_effective × B_cog
    Contrast = observed − background (normal)
    """
    # Normalize deviations
    def dev(bkg: float, obs: float, scale: float) -> float:
        return (obs - bkg) / max(scale, 1e-6)

    d_vp   = dev(background.vp,   observed.vp,   500)
    d_rho  = dev(background.rho,  observed.rho,   200)
    d_phi  = dev(background.phi,  observed.phi,   0.10)
    d_rhoe = dev(background.rho_e, observed.rho_e, 100)

    # Ambiguity (normalized spread across parameters)
    u_ambiguity = math.sqrt(d_vp**2 + d_rho**2 + d_phi**2 + d_rhoe**2) / 2

    # Transform depth (how deep into the anomaly)
    D_transform = abs(d_vp) * abs(d_phi) + abs(d_rho)

    # Bayesian confidence (composite)
    B_cog = 1.0 / (1.0 + u_ambiguity)

    AC_Risk = u_ambiguity * D_transform * B_cog

    return {
        "AC_Risk":          round(AC_Risk, 4),
        "u_ambiguity":      round(u_ambiguity, 4),
        "D_transform":      round(D_transform, 4),
        "B_cog":            round(B_cog, 4),
        "d_vp":             round(d_vp, 4),
        "d_rho":            round(d_rho, 4),
        "d_phi":            round(d_phi, 4),
        "d_rhoe":           round(d_rhoe, 4),
        "verdict":          "SEAL" if AC_Risk < 0.5 else "HOLD" if AC_Risk < 1.5 else "VOID",
        "metadata": {
            "formula": "AC_Risk = u_ambiguity × D_transform_effective × B_cog",
            "constitution": "888_JUDGE",
        },
    }

# ─── Inverse physics9 ─────────────────────────────────────────────────────────

def inverse_physics9(
    measurements: Dict[str, float],
    prior_state: Optional[Physics9State] = None,
) -> Dict[str, Any]:
    """Infer canonical state from measurements."""
    if prior_state is None:
        prior_state = Physics9State(rho=2350, vp=2950, vs=1680,
                                    rho_e=20, chi=0.001, k=2.5,
                                    P=20e6, T=320, phi=0.20)

    # Simple Bayesian update — adjust state toward measurements
    updated = Physics9State(
        rho  = prior_state.rho  * (measurements.get("density_ratio", 1.0)),
        vp   = prior_state.vp   * (measurements.get("vp_ratio", 1.0)),
        vs   = prior_state.vs   * (measurements.get("vs_ratio", 1.0)),
        rho_e= prior_state.rho_e * (measurements.get("resistivity_ratio", 1.0)),
        chi  = prior_state.chi,
        k    = prior_state.k,
        P    = measurements.get("pressure_pa", prior_state.P),
        T    = measurements.get("temperature_k", prior_state.T),
        phi  = measurements.get("porosity", prior_state.phi),
    )

    litho, conf, derived = build_lithology_model(updated)
    return {
        "inferred_state": updated.to_dict(),
        "lithology": litho,
        "confidence": conf,
        "derived": derived,
    }

# ─── Metabolic Loop ──────────────────────────────────────────────────────────

def metabolic_loop(
    initial_state: Physics9State,
    measurements: Dict[str, float],
    max_iterations: int = 50,
) -> Dict[str, Any]:
    """
    Forward → Inverse → Forward convergence loop.
    Forward model: state → predicted measurements
    Inverse: measurements → updated state
    Loop until convergence or max_iterations.
    """
    state = initial_state
    converged = False

    for i in range(max_iterations):
        # Forward pass
        predicted = forward_physics9(state)

        # Compute residual
        residual = 0.0
        for key in ["ai_kg_ms2", "thermal_diff"]:
            if key in measurements:
                residual += (predicted.get(key, 0) - measurements[key])**2
        residual = math.sqrt(residual)

        if residual < 0.01:
            converged = True
            break

        # Inverse update (gradient descent on state)
        delta = residual * 0.1
        state = Physics9State(
            rho  = max(1000,   state.rho  * (1 - delta)),
            vp   = max(1500,   state.vp   * (1 - delta * 0.5)),
            vs   = max(500,    state.vs   * (1 - delta * 0.3)),
            rho_e= state.rho_e * (1 + delta * 0.2),
            chi  = state.chi,
            k    = state.k,
            P    = measurements.get("pressure_pa", state.P),
            T    = measurements.get("temperature_k", state.T),
            phi  = max(0.01, min(0.45, state.phi * (1 + delta * 0.1))),
        )

    litho, conf, derived = build_lithology_model(state)
    return {
        "converged_state": state,
        "final_lithology": litho,
        "loop_cycles": i + 1,
        "converged": converged,
        "metadata": {
            "loop_type": "forward_inverse_metabolic",
            "constitution": "888_JUDGE",
            "omega_bound": True,
        },
    }
