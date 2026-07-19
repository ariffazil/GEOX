"""
joint_inversion.py — W13+ Phase C forge: Joint multi-physics inversion.

The strategic centerpiece. Fuses N independent geophysical modalities
(seismic, gravity, magnetic, EM) into one Physics13State per cell.

Inputs (per cell):
  - Seismic: acoustic_impedance (kg·m⁻²·s⁻¹) OR Vp/Vs ratio
  - Gravity: Bouguer anomaly (mGal)
  - Magnetic: total-field anomaly (nT)
  - EM: resistivity (Ω·m) from MT/CSAMT
  - Optional: porosity log, density log (from wells)

Algorithm: weighted least-squares against forward models:
  AcousticImpedance = ρ · Vp
  Bouguer           = f(prism_density, depth)         (HarmonIC)
  TMI               = f(magnetization, depth)         (HarmonIC)
  MT_apparent_resistivity = ρₑ

Physics9 bounds enforced (per state.py):
  1000 ≤ ρ ≤ 5000, 1500 ≤ Vp ≤ 6000, 0.02 ≤ φ ≤ 0.45,
  etc.

Each result is graded RAW/AAA per state.grade(). RAW cells are
flagged and never SEAL.

DITEMPA BUKAN DIBEI — the cell is forged, not given.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field, replace
from typing import Literal

import numpy as np

from geox_core.physics.state import Physics13State


# ───────────────────────────── MODALITY INPUT ────────────────────────────────────
@dataclass(frozen=True)
class ModalityObservation:
    """One observation from one modality at one cell."""

    modality: Literal["seismic_impedance", "seismic_vpvs", "gravity", "magnetic", "mt_resistivity"]
    value: float
    uncertainty: float = 0.05  # relative 1σ
    weight: float = 1.0  # user-tunable modality trust
    depth_m: float = 0.0  # depth below surface (for ordering)


@dataclass(frozen=True)
class InversionRequest:
    """A cell-wise inversion request."""

    observations: list[ModalityObservation] = field(default_factory=list)
    # Prior: best-guess Physics13State (from wells / catalog)
    prior: Physics13State | None = None
    # Bounds: per-dial min/max for solver
    bounds: dict[str, tuple[float, float]] | None = None
    # Convergence thresholds
    max_iter: int = 50
    tolerance: float = 1e-3
    # F4 CLARITY: opt-in post-inversion crust-zone classification.
    # Default OFF — existing callers see no change.
    # Stage 6 forge: wired to Huang 2021 Vp grammar.
    classify_crust_zone: bool = False
    crust_thickness_km: float | None = None  # used if classify_crust_zone=True
    heat_flow_mw_m2: float | None = None     # used if classify_crust_zone=True
    include_zone_diagnostics: bool = False      # verbose diagnostic_basis in result


# ───────────────────────────── FORWARD OPERATORS ─────────────────────────────────
def forward_impedance(state: Physics13State) -> float:
    """Z = ρ · Vp (kg·m⁻²·s⁻¹)."""
    return state.rho * state.vp


def forward_vpvs(state: Physics13State) -> float:
    """Vp/Vs ratio (dimensionless)."""
    return state.vp / max(state.vs, 1e-6)


def forward_gravity_bouguer(state: Physics13State, depth_m: float) -> float:
    """Single-prism Bouguer approximation at given depth.

    Simplified HarmonIC point-mass: Δg ≈ G · M / r² · 1e5 (mGal).
    r² = depth_m² + small horizontal offset.

    Here we treat the response as proportional to (ρ - 2670) (background density)
    and decay with depth. This is a calibration proxy, not a full forward model.
    """
    G = 6.674e-11
    rho_bg = 2670.0  # typical crust background
    rho_contrast = state.rho - rho_bg
    # Cell volume for a 100m cube (calibration)
    volume = 1e6  # m³
    mass = rho_contrast * volume
    r2 = depth_m * depth_m + 1e6  # +1km² guard for shallow cells
    return G * mass / r2 * 1e5  # mGal


def forward_magnetic_tmi(state: Physics13State, depth_m: float) -> float:
    """Simplified magnetic dipole forward.

    TMI ≈ (μ₀ / 4π) · (M · V · cos(θ)) / r³ · 1e9 (nT)
    where θ is inclination; we use 60° (typical low-latitude).
    """
    mu0 = 4 * math.pi * 1e-7
    M = state.chi * 1.0  # magnetization proportional to susceptibility
    volume = 1e6  # m³ cell
    inc = math.radians(60.0)
    r = math.sqrt(depth_m * depth_m + 1e6)
    return (mu0 / (4 * math.pi)) * (M * volume * math.cos(inc)) / (r ** 3) * 1e9


def forward_mt_resistivity(state: Physics13State) -> float:
    """The MT/CSAMT 'apparent resistivity' is just ρₑ in Ω·m."""
    return state.rho_e


# ───────────────────────────── SOLVER ─────────────────────────────────────────────
DEFAULT_BOUNDS: dict[str, tuple[float, float]] = {
    "rho": (1000.0, 5000.0),
    "vp": (1500.0, 6000.0),
    "vs": (500.0, 4000.0),
    "rho_e": (0.1, 1e7),
    "chi": (0.0, 0.1),
    "k": (0.1, 10.0),
    "P": (1e5, 200e6),
    "T": (250.0, 600.0),
    "phi": (0.0, 0.45),
}


def _clip_to_bounds(state: Physics13State, bounds: dict[str, tuple[float, float]]) -> Physics13State:
    """Clip every dial to its allowed Earth-bounds."""
    return Physics13State(
        rho=float(np.clip(state.rho, *bounds["rho"])),
        vp=float(np.clip(state.vp, *bounds["vp"])),
        vs=float(np.clip(state.vs, *bounds["vs"])),
        rho_e=float(np.clip(state.rho_e, *bounds["rho_e"])),
        chi=float(np.clip(state.chi, *bounds["chi"])),
        k=float(np.clip(state.k, *bounds["k"])),
        P=float(np.clip(state.P, *bounds["P"])),
        T=float(np.clip(state.T, *bounds["T"])),
        phi=float(np.clip(state.phi, *bounds["phi"])),
    )


def _forward_observation(state: Physics13State, obs: ModalityObservation) -> float:
    """Dispatch to the right forward operator."""
    if obs.modality == "seismic_impedance":
        return forward_impedance(state)
    if obs.modality == "seismic_vpvs":
        return forward_vpvs(state)
    if obs.modality == "gravity":
        return forward_gravity_bouguer(state, obs.depth_m)
    if obs.modality == "magnetic":
        return forward_magnetic_tmi(state, obs.depth_m)
    if obs.modality == "mt_resistivity":
        return forward_mt_resistivity(state)
    raise ValueError(f"unknown modality: {obs.modality}")


def joint_inversion(request: InversionRequest) -> dict:
    """Solve for one Physics13State per cell from N modalities.

    Algorithm: Iteratively Reweighted Least-Squares (IRLS) using
    the prior as starting point. Each iteration clips to bounds and
    updates the state vector by the gradient of the L2 residual.

    Returns
    -------
    dict with: state, residuals, grade, iterations, modality_count, ok.
    """
    bounds = request.bounds or DEFAULT_BOUNDS

    # Prior or default Sandstone
    state = request.prior or Physics13State(
        rho=2350.0, vp=2950.0, vs=1680.0, rho_e=20.0,
        chi=0.0001, k=2.8, P=20e6, T=320.0, phi=0.25,
    )

    if not request.observations:
        return {
            "ok": False,
            "error": "no_observations",
            "state": state,
            "residual_rms": float("inf"),
            "grade": state.grade(),
        }

    # IRLS: tune state toward reducing weighted L2 residual
    for it in range(request.max_iter):
        # Compute residuals
        residuals = []
        weights = []
        for obs in request.observations:
            pred = _forward_observation(state, obs)
            if obs.value == 0:
                continue
            rel = (pred - obs.value) / max(abs(obs.value), 1e-6)
            residuals.append(rel)
            weights.append(obs.weight / max(obs.uncertainty, 1e-3))

        if not residuals:
            break
        rms = float(np.sqrt(np.mean(np.square(residuals))))
        if rms < request.tolerance:
            break

        # Compute gradient via finite differences (cheap for 9 dials)
        eps = 1e-4
        grads = np.zeros(9)
        names = ["rho", "vp", "vs", "rho_e", "chi", "k_th", "Pp", "T", "phi"]
        for i, name in enumerate(names):
            value = getattr(state, name)
            state_plus = replace(state, **{name: value * (1 + eps)})
            state_minus = replace(state, **{name: value * (1 - eps)})
            res_plus = 0.0
            res_minus = 0.0
            for j, obs in enumerate(request.observations):
                if obs.value == 0:
                    continue
                v_p = _forward_observation(state_plus, obs)
                v_m = _forward_observation(state_minus, obs)
                wp = weights[j]
                rel_p = (v_p - obs.value) / max(abs(obs.value), 1e-6)
                rel_m = (v_m - obs.value) / max(abs(obs.value), 1e-6)
                res_plus += wp * rel_p * rel_p
                res_minus += wp * rel_m * rel_m
            grads[i] = (res_plus - res_minus) / (2 * eps * max(abs(value), 1e-3))

        # Step proportional to negative gradient
        step = 0.05 / max(np.linalg.norm(grads), 1e-3)
        new_state = Physics13State(
            rho=state.rho - step * grads[0],
            vp=state.vp - step * grads[1],
            vs=state.vs - step * grads[2],
            rho_e=state.rho_e - step * grads[3],
            chi=state.chi - step * grads[4],
            k_th=state.k_th - step * grads[5],
            Pp=state.Pp - step * grads[6],
            T=state.T - step * grads[7],
            phi=state.phi - step * grads[8],
        )
        state = _clip_to_bounds(new_state, bounds)

    # Final residual
    final_residuals = []
    for obs in request.observations:
        if obs.value == 0:
            continue
        pred = _forward_observation(state, obs)
        rel = (pred - obs.value) / max(abs(obs.value), 1e-6)
        final_residuals.append(rel)
    rms_final = float(np.sqrt(np.mean(np.square(final_residuals)))) if final_residuals else float("inf")

    # Per-modality breakdown
    per_modality = {}
    for obs in request.observations:
        pred = _forward_observation(state, obs)
        rel = (pred - obs.value) / max(abs(obs.value), 1e-6) if obs.value != 0 else 0.0
        per_modality.setdefault(obs.modality, []).append({
            "observed": obs.value,
            "predicted": pred,
            "relative_error": rel,
        })

    # Provenance hash
    payload = repr(sorted([
        (o.modality, round(o.value, 6), round(o.uncertainty, 6), round(o.depth_m, 3))
        for o in request.observations
    ])).encode()
    obs_hash = hashlib.sha256(payload).hexdigest()

    result = {
        "ok": True,
        "state": state,
        "grade": state.grade(),
        "residual_rms": rms_final,
        "iterations": it + 1,
        "modality_count": len(set(o.modality for o in request.observations)),
        "observation_count": len(request.observations),
        "per_modality": per_modality,
        "observation_hash": obs_hash,
        "epistemic_provenance": {
            "rung": 5,  # MODEL
            "grounding": "joint_inversion_under_physics9_bounds",
            "method": "irls_with_bounded_clipping",
            "caveat": (
                "Solver is IRLS with finite-difference gradient; "
                "weights are user-supplied. Not a substitute for "
                "production-grade Bayesian joint inversion (e.g. JIMAS, BERT)."
            ),
        },
        "godel_wall": {
            "state": "KNOWN" if state.grade() == "AAA" else "UNDECIDABLE_YET",
            "reason": (
                "Physics9 bounds satisfied (AAA grade)."
                if state.grade() == "AAA"
                else "State violates Physics9 bounds (RAW grade). Reject or refine prior."
            ),
        },
    }

    # F4 CLARITY — opt-in post-inversion crust-zone classification.
    # Stage 6 forge: wires vp_zone_classify into the inversion pipeline.
    # F13 SOVEREIGN note: this is substrate support, NOT a verdict.
    if request.classify_crust_zone:
        from geox_core.physics.joint_inversion_zone_hook import (
            PostInversionZoneHook,
            classify_state_post_inversion,
        )
        hook = PostInversionZoneHook(
            crust_thickness_km=request.crust_thickness_km,
            heat_flow_mw_m2=request.heat_flow_mw_m2,
            include_diagnostics=request.include_zone_diagnostics,
        )
        result["crust_zone_classification"] = classify_state_post_inversion(
            state=state,
            observations=request.observations,
            hook=hook,
        )

    return result


# ───────────────────────────── BATCH ENTRY ────────────────────────────────────────
def joint_inversion_batch(
    cells: list[InversionRequest],
    *,
    doctrine_registry=None,
    doctrine_wall=None,
) -> list[dict]:
    """Run joint_inversion on many cells; optionally attach doctrine verdicts.

    If both `doctrine_registry` and `doctrine_wall` are provided, each cell's
    output is wrapped with an assumption record (Gap X) and a Gödel verdict
    (Gap 5).
    """
    out = []
    for i, req in enumerate(cells):
        result = joint_inversion(req)
        if doctrine_registry is not None and doctrine_wall is not None:
            try:
                asm = doctrine_registry.register(
                    introduced_by="geox_joint_inversion",
                    rung_origin=5,
                    description=f"Joint inversion of cell {i}; residual_rms={result.get('residual_rms', 0):.4f}",
                )
                claim = doctrine_wall.register_claim(
                    rung=5,
                    description=f"Cell {i} Physics13State is bounded (AAA grade).",
                    depends_on_assumption_ids=[asm.assumption_id],
                )
                verdict = doctrine_wall.is_sealable(claim.claim_id)
                result["doctrine"] = {
                    "assumption_id": asm.assumption_id,
                    "claim_id": claim.claim_id,
                    "godel_verdict": verdict.model_dump(),
                }
            except Exception as e:  # noqa: BLE001
                result["doctrine_error"] = str(e)
        out.append(result)
    return out


__all__ = [
    "ModalityObservation",
    "InversionRequest",
    "DEFAULT_BOUNDS",
    "forward_impedance",
    "forward_vpvs",
    "forward_gravity_bouguer",
    "forward_magnetic_tmi",
    "forward_mt_resistivity",
    "joint_inversion",
    "joint_inversion_batch",
]
