"""
geox_core.engines.joint_inversion — Multi-Physics Joint Inversion Under Physics9
═══════════════════════════════════════════════════════════════════════════════════
The crown jewel: fuses seismic, gravity, magnetics, CSEM/MT, and biostratigraphy
into one Physics13State per subsurface node.

Physics:
    Given N geophysical observations {d₁, d₂, ..., dₙ} from different methods,
    find the Physics13State vector S = {ρ, Vp, Vs, ρ_e, χ, k, P, T, φ} at each
    node that simultaneously satisfies all forward models within uncertainty.

    Joint objective:
        Φ(S) = Σᵢ wᵢ · ||dᵢ - Gᵢ(S)||² + λ·R(S)

    where:
        Gᵢ(S) = forward model for method i
        wᵢ = weight for method i (data quality / confidence)
        R(S) = regularisation (smoothness, well tie, physics bounds)

Constitutional: F1 (reversible), F2 (truth), F4 (reduce entropy), F9 (physics-only).
Author: FORGE (000Ω) | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from scipy import optimize

from geox_core.physics.state import Physics13State, EARTH_MATERIAL_CATALOG
from geox_core.physics.parameters import forward_physics9
from geox_core.engines.potential_fields import (
    gravity_forward_slab,
    magnetic_forward_prism,
)
from geox_core.engines.em import LayerModel, mt_forward_1d

logger = logging.getLogger("geox.joint_inversion")


# ─── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class GeophysicalObservation:
    """Single geophysical observation with metadata."""
    method: Literal["seismic", "gravity", "magnetics", "csem", "mt", "biostrat"]
    values: np.ndarray
    uncertainties: np.ndarray
    coordinates: np.ndarray  # (x, y, z) or (x, y)
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class JointInversionConfig:
    """Configuration for joint inversion."""
    max_iterations: int = 50
    convergence_threshold: float = 0.01
    smoothness_weight: float = 0.01
    well_tie_weight: float = 0.005
    seismic_weight: float = 1.0
    gravity_weight: float = 0.5
    magnetics_weight: float = 0.3
    em_weight: float = 0.4
    biostrat_weight: float = 0.2
    damping: float = 0.1
    use_physics_guard: bool = True


@dataclass
class JointInversionResult:
    """Result of multi-physics joint inversion."""
    physics9_states: list[Physics13State]     # one per node
    misfit_history: list[float]              # total misfit per iteration
    method_misfits: dict[str, list[float]]   # per-method misfit
    converged: bool
    iterations: int
    final_total_misfit: float
    node_coordinates: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_nodes": len(self.physics9_states),
            "states": [s.to_dict() for s in self.physics9_states],
            "converged": self.converged,
            "iterations": self.iterations,
            "final_misfit": self.final_total_misfit,
            "misfit_history": self.misfit_history[:20],
            "method_misfits": {k: v[:20] for k, v in self.method_misfits.items()},
            "metadata": self.metadata,
        }


# ─── Forward Model Wrappers ─────────────────────────────────────────────────


def _forward_seismic(state: Physics13State) -> dict[str, float]:
    """Extract seismic observables from Physics13State."""
    ai = state.vp * state.rho
    return {"ai": ai, "vp_vs": state.vp / max(state.vs, 0.001)}


def _forward_gravity(state: Physics13State, ref_density: float = 2670.0) -> float:
    """Density contrast → gravity anomaly (simplified slab)."""
    delta_rho = state.rho - ref_density
    return 0.04193 * (delta_rho / 1000.0) * 100.0  # 100m slab, mGal


def _forward_magnetics(state: Physics13State) -> float:
    """Susceptibility → magnetic anomaly (simplified)."""
    B0 = 50000e-9
    mu0 = 4.0 * np.pi * 1e-7
    M = state.chi * B0 / mu0
    return abs(M) * 1e9  # nT (simplified amplitude)


def _forward_em(state: Physics13State) -> float:
    """Resistivity → EM response (apparent resistivity proxy)."""
    return state.rho_e


# ─── Joint Objective Function ───────────────────────────────────────────────


def _joint_objective(
    state_vector: np.ndarray,
    observations: list[GeophysicalObservation],
    config: JointInversionConfig,
    reference_states: list[Physics13State] | None = None,
) -> float:
    """
    Joint objective function: Φ(S) = Σᵢ wᵢ·||dᵢ - Gᵢ(S)||² + λ·R(S)

    state_vector: flattened Physics13State parameters [rho, vp, vs, rho_e, chi, k, P, T, phi]
    """
    n_params = 9
    n_nodes = len(state_vector) // n_params

    total_misfit = 0.0

    for node_idx in range(n_nodes):
        start = node_idx * n_params
        sv = state_vector[start:start + n_params]

        # Build Physics13State from vector
        state = Physics13State(
            rho=max(1000, min(5000, sv[0])),
            vp=max(1500, min(7000, sv[1])),
            vs=max(500, min(4000, sv[2])),
            rho_e=max(0.1, min(1e6, sv[3])),
            chi=max(0, min(0.1, sv[4])),
            k=max(0.1, min(10, sv[5])),
            P=max(1e5, min(1e9, sv[6])),
            T=max(200, min(600, sv[7])),
            phi=max(0.01, min(0.45, sv[8])),
        )

        for obs in observations:
            if node_idx >= len(obs.values):
                continue

            predicted = None
            weight = obs.weight * obs.uncertainties[node_idx] if node_idx < len(obs.uncertainties) else obs.weight

            if obs.method == "seismic":
                fwd = _forward_seismic(state)
                predicted = fwd["ai"]
                weight *= config.seismic_weight
            elif obs.method == "gravity":
                predicted = _forward_gravity(state)
                weight *= config.gravity_weight
            elif obs.method == "magnetics":
                predicted = _forward_magnetics(state)
                weight *= config.magnetics_weight
            elif obs.method in ("csem", "mt"):
                predicted = _forward_em(state)
                weight *= config.em_weight
            elif obs.method == "biostrat":
                # Biostrat constrains age → temperature/pressure window
                predicted = state.T  # proxy
                weight *= config.biostrat_weight

            if predicted is not None:
                residual = (obs.values[node_idx] - predicted) ** 2
                total_misfit += weight * residual

        # Smoothness regularisation (penalise large jumps between nodes)
        if node_idx > 0 and reference_states is not None:
            prev_start = (node_idx - 1) * n_params
            prev_sv = state_vector[prev_start:prev_start + n_params]
            smooth_penalty = np.sum((sv - prev_sv) ** 2)
            total_misfit += config.smoothness_weight * smooth_penalty

        # Well tie regularisation
        if reference_states and node_idx < len(reference_states):
            ref = reference_states[node_idx]
            ref_vec = np.array([ref.rho, ref.vp, ref.vs, ref.rho_e, ref.chi, ref.k, ref.P, ref.T, ref.phi])
            well_penalty = np.sum((sv - ref_vec) ** 2)
            total_misfit += config.well_tie_weight * well_penalty

    return total_misfit


# ─── Joint Inversion Solver ─────────────────────────────────────────────────


def run_joint_inversion(
    observations: list[GeophysicalObservation],
    initial_states: list[Physics13State],
    config: JointInversionConfig | None = None,
    well_constraints: list[Physics13State] | None = None,
) -> JointInversionResult:
    """
    Multi-physics joint inversion under Physics9 governance.

    Inverts seismic, gravity, magnetics, CSEM/MT, and biostratigraphy
    observations simultaneously to find the Physics13State at each node
    that best explains ALL data.

    Args:
        observations: list of GeophysicalObservation (one per data type)
        initial_states: starting Physics13State at each node
        config: inversion configuration
        well_constraints: optional well-constrained states for regularisation

    Returns:
        JointInversionResult with converged Physics13State field
    """
    if config is None:
        config = JointInversionConfig()

    n_nodes = len(initial_states)
    n_params = 9

    # Flatten initial states to vector
    x0 = np.zeros(n_nodes * n_params)
    for i, state in enumerate(initial_states):
        start = i * n_params
        x0[start:start + n_params] = [
            state.rho, state.vp, state.vs, state.rho_e,
            state.chi, state.k, state.P, state.T, state.phi,
        ]

    # Bounds for each parameter
    bounds = []
    for _ in range(n_nodes):
        bounds.extend([
            (1000, 5000),    # rho
            (1500, 7000),    # vp
            (500, 4000),     # vs
            (0.1, 1e6),      # rho_e
            (0, 0.1),        # chi
            (0.1, 10),       # k
            (1e5, 1e9),      # P
            (200, 600),      # T
            (0.01, 0.45),    # phi
        ])

    # Track misfits
    misfit_history = []
    method_misfits = {obs.method: [] for obs in observations}

    # Callback for monitoring
    def callback(xk):
        misfit = _joint_objective(xk, observations, config, well_constraints)
        misfit_history.append(float(misfit))

    # Run optimisation
    try:
        result = optimize.minimize(
            _joint_objective,
            x0,
            args=(observations, config, well_constraints),
            method="L-BFGS-B",
            bounds=bounds,
            options={
                "maxiter": config.max_iterations,
                "ftol": config.convergence_threshold,
                "disp": False,
            },
            callback=callback,
        )
        converged = result.success
        final_x = result.x
        iterations = result.nit
    except Exception as e:
        logger.warning(f"Joint inversion failed: {e}, returning initial states")
        converged = False
        final_x = x0
        iterations = 0

    # Reconstruct Physics13States
    states = []
    for i in range(n_nodes):
        start = i * n_params
        sv = final_x[start:start + n_params]
        states.append(Physics13State(
            rho=float(np.clip(sv[0], 1000, 5000)),
            vp=float(np.clip(sv[1], 1500, 7000)),
            vs=float(np.clip(sv[2], 500, 4000)),
            rho_e=float(np.clip(sv[3], 0.1, 1e6)),
            chi=float(np.clip(sv[4], 0, 0.1)),
            k=float(np.clip(sv[5], 0.1, 10)),
            P=float(np.clip(sv[6], 1e5, 1e9)),
            T=float(np.clip(sv[7], 200, 600)),
            phi=float(np.clip(sv[8], 0.01, 0.45)),
        ))

    # Compute per-method misfits for the final state
    for obs in observations:
        method_total = 0.0
        for i in range(min(n_nodes, len(obs.values))):
            if obs.method == "seismic":
                fwd = _forward_seismic(states[i])
                method_total += (obs.values[i] - fwd["ai"]) ** 2
            elif obs.method == "gravity":
                method_total += (obs.values[i] - _forward_gravity(states[i])) ** 2
            elif obs.method == "magnetics":
                method_total += (obs.values[i] - _forward_magnetics(states[i])) ** 2
            elif obs.method in ("csem", "mt"):
                method_total += (obs.values[i] - _forward_em(states[i])) ** 2
        method_misfits[obs.method] = [float(np.sqrt(method_total / max(len(obs.values), 1)))]

    # PhysicsGuard validation
    guard_violations = []
    if config.use_physics_guard:
        for i, state in enumerate(states):
            grade = state.grade()
            if grade != "AAA":
                guard_violations.append({"node": i, "grade": grade, "state": state.to_dict()})

    return JointInversionResult(
        physics9_states=states,
        misfit_history=misfit_history,
        method_misfits=method_misfits,
        converged=converged,
        iterations=iterations,
        final_total_misfit=misfit_history[-1] if misfit_history else float("inf"),
        node_coordinates=np.arange(n_nodes).reshape(-1, 1),
        metadata={
            "config": {
                "max_iterations": config.max_iterations,
                "convergence_threshold": config.convergence_threshold,
                "weights": {
                    "seismic": config.seismic_weight,
                    "gravity": config.gravity_weight,
                    "magnetics": config.magnetics_weight,
                    "em": config.em_weight,
                    "biostrat": config.biostrat_weight,
                },
            },
            "n_observations": len(observations),
            "guard_violations": guard_violations,
            "epistemic_rung": 5,
            "note": "Joint inversion result. All 9 parameters per node. Governed by Physics9 bounds.",
        },
    )


# ─── Convenience: Quick Joint Inversion ─────────────────────────────────────


def quick_joint_inversion(
    ai_observations: np.ndarray | None = None,
    gravity_observations: np.ndarray | None = None,
    magnetics_observations: np.ndarray | None = None,
    resistivity_observations: np.ndarray | None = None,
    n_nodes: int = 10,
    config: JointInversionConfig | None = None,
) -> JointInversionResult:
    """
    Quick joint inversion from numpy arrays.

    Convenience wrapper for common use cases.
    """
    observations = []
    if ai_observations is not None:
        observations.append(GeophysicalObservation(
            method="seismic", values=ai_observations,
            uncertainties=np.ones(len(ai_observations)),
            coordinates=np.arange(len(ai_observations)).reshape(-1, 1),
        ))
    if gravity_observations is not None:
        observations.append(GeophysicalObservation(
            method="gravity", values=gravity_observations,
            uncertainties=np.ones(len(gravity_observations)),
            coordinates=np.arange(len(gravity_observations)).reshape(-1, 1),
        ))
    if magnetics_observations is not None:
        observations.append(GeophysicalObservation(
            method="magnetics", values=magnetics_observations,
            uncertainties=np.ones(len(magnetics_observations)),
            coordinates=np.arange(len(magnetics_observations)).reshape(-1, 1),
        ))
    if resistivity_observations is not None:
        observations.append(GeophysicalObservation(
            method="mt", values=resistivity_observations,
            uncertainties=np.ones(len(resistivity_observations)),
            coordinates=np.arange(len(resistivity_observations)).reshape(-1, 1),
        ))

    # Default initial states from sandstone
    sandstone = EARTH_MATERIAL_CATALOG["Sandstone"]
    initial_states = [sandstone] * n_nodes

    return run_joint_inversion(observations, initial_states, config)
