"""
geox_core.physics.drivers — Dynamic Physics: Forward, Inverse, Contrast

These functions operate on Physics9State and produce predictions or inferences.
They are the "engine" layer above the static parameters.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

from geox_core.physics.state import Physics9State
from geox_core.physics.parameters import forward_physics9


# ─── Lithology Discrimination (Vp/Vs/ρ only) ────────────────────────────────


def build_lithology_model(state: Physics9State) -> Tuple[str, float, Dict[str, float]]:
    """
    Vp/Vs/ρ → lithology name + confidence + derived properties.

    This is the *only* interpretive step allowed in the physics layer,
    and it is bounded to hard velocity thresholds with low confidence
    ceiling (max 0.85) to signal uncertainty.
    """
    vpvsv = state.vp / max(state.vs, 0.001)

    if state.vp > 5500:
        litho, conf = "Dolomite", 0.85
    elif state.vp > 4000:
        litho, conf = "Limestone", 0.80
    elif state.vp > 3000 and vpvsv > 1.75:
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

    Contrast = observed − background (normalised by scale).
    Returns a machine-readable verdict, not a story.
    """

    def dev(bkg: float, obs: float, scale: float) -> float:
        return (obs - bkg) / max(scale, 1e-6)

    d_vp = dev(background.vp, observed.vp, 500)
    d_rho = dev(background.rho, observed.rho, 200)
    d_phi = dev(background.phi, observed.phi, 0.10)
    d_rhoe = dev(background.rho_e, observed.rho_e, 100)

    u_ambiguity = math.sqrt(d_vp**2 + d_rho**2 + d_phi**2 + d_rhoe**2) / 2
    D_transform = abs(d_vp) * abs(d_phi) + abs(d_rho)
    B_cog = 1.0 / (1.0 + u_ambiguity)
    AC_Risk = u_ambiguity * D_transform * B_cog

    return {
        "AC_Risk": round(AC_Risk, 4),
        "u_ambiguity": round(u_ambiguity, 4),
        "D_transform": round(D_transform, 4),
        "B_cog": round(B_cog, 4),
        "d_vp": round(d_vp, 4),
        "d_rho": round(d_rho, 4),
        "d_phi": round(d_phi, 4),
        "d_rhoe": round(d_rhoe, 4),
        "verdict": ("SEAL" if AC_Risk < 0.5 else "HOLD" if AC_Risk < 1.5 else "VOID"),
        "metadata": {
            "formula": "AC_Risk = u_ambiguity × D_transform_effective × B_cog",
            "constitution": "888_JUDGE",
        },
    }


# ─── Inverse Physics ────────────────────────────────────────────────────────


def inverse_physics9(
    measurements: Dict[str, float],
    prior_state: Optional[Physics9State] = None,
) -> Dict[str, Any]:
    """
    Infer canonical state from sparse measurements.
    Simple ratio-update; not Bayesian MCMC.
    """
    if prior_state is None:
        prior_state = Physics9State(
            rho=2350,
            vp=2950,
            vs=1680,
            rho_e=20,
            chi=0.001,
            k=2.5,
            P=20e6,
            T=320,
            phi=0.20,
        )

    updated = Physics9State(
        rho=prior_state.rho * measurements.get("density_ratio", 1.0),
        vp=prior_state.vp * measurements.get("vp_ratio", 1.0),
        vs=prior_state.vs * measurements.get("vs_ratio", 1.0),
        rho_e=prior_state.rho_e * measurements.get("resistivity_ratio", 1.0),
        chi=prior_state.chi,
        k=prior_state.k,
        P=measurements.get("pressure_pa", prior_state.P),
        T=measurements.get("temperature_k", prior_state.T),
        phi=measurements.get("porosity", prior_state.phi),
    )

    litho, conf, derived = build_lithology_model(updated)
    return {
        "inferred_state": updated.to_dict(),
        "lithology": litho,
        "confidence": conf,
        "derived": derived,
    }


# ─── Metabolic Loop (Forward ↔ Inverse Convergence) ────────────────────────


def metabolic_loop(
    initial_state: Physics9State,
    measurements: Dict[str, float],
    max_iterations: int = 50,
) -> Dict[str, Any]:
    """
    Forward → Inverse → Forward until residual < 0.01 or max_iterations.
    """
    state = initial_state
    converged = False
    i = 0

    for i in range(max_iterations):
        predicted = forward_physics9(state)

        residual = 0.0
        for key in ("ai_kg_ms2", "thermal_diff"):
            if key in measurements:
                residual += (predicted.get(key, 0.0) - measurements[key]) ** 2
        residual = math.sqrt(residual)

        if residual < 0.01:
            converged = True
            break

        delta = residual * 0.1
        state = Physics9State(
            rho=max(1000.0, state.rho * (1.0 - delta)),
            vp=max(1500.0, state.vp * (1.0 - delta * 0.5)),
            vs=max(500.0, state.vs * (1.0 - delta * 0.3)),
            rho_e=state.rho_e * (1.0 + delta * 0.2),
            chi=state.chi,
            k=state.k,
            P=measurements.get("pressure_pa", state.P),
            T=measurements.get("temperature_k", state.T),
            phi=max(0.01, min(0.45, state.phi * (1.0 + delta * 0.1))),
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
