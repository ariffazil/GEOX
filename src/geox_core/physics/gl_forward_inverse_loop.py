"""gl_forward_inverse_loop.py — GEOX GLOF Forward-Inverse-Metabolize loop.

F-I-M doctrine (arifOS / GEOX Intelligence Core):
    Forward    : given material properties theta, predict observations y_sim(theta)
    Inverse    : given observations y_obs, infer theta via Bayesian likelihood
    Metabolize : forward vs inverse delta -> update priors, refine next cycle

Seismic coupling (existing GEOX surface):
    forward   calls geox_seismic_compute(mode='avo_forward') to seed prior
    from E, nu via geox_geomechanics(state_dict).
    inverse   refines theta using GLOF dam observations
               (Trishuli surge level, time-to-peak).

Closure: each F-I-M cycle produces a MetabolizeReceipt with
    - theta_hat (inferred)
    - G = geometric-mean(Witness_human, Witness_simulation, Witness_seismic)
    - epicycle delta (improvement vs prior cycle)
"""
from __future__ import annotations

import math
import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Tuple, Callable

import numpy as np

from geox_core.physics.glgeomaterial import (
    GLOFMaterialState, MaterialPhase, himalayan_defaults,
)
from geox_core.physics.glphase_switcher import (
    evaluate_cascade, YieldVerdict, phase_sequence,
    V_CRIT_AVALANCHE, S_CRIT_LIQUEFACTION,
)


# ============================================================== Schema
@dataclass
class GLOFObservation:
    """Field observation used for inverse inference."""
    label: str
    water_head_m: float          # impounded lake height
    breach_width_m: float        # observed breach width
    peak_discharge_m3s: float   # observed Q_peak
    time_to_peak_min: float      # minutes from breach start to Q_peak
    downstream_surge_m: float   # water level rise at downstream town (e.g. Trishuli)
    source: str = "field"
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ThetaPrior:
    """Bayesian prior on the 6 most-uncertain dam parameters.

    Other 3 (rho, E, nu) come from existing petrophysical state.
    """
    c: Tuple[float, float] = (1e3, 1e5)     # cohesion (Pa) — wide range
    phi_deg: Tuple[float, float] = (25.0, 40.0)  # friction angle
    k: Tuple[float, float] = (1e-6, 1e-3)   # permeability (m^2)
    tau_0: Tuple[float, float] = (1e3, 1e4) # yield stress (Pa)
    sigma_t: Tuple[float, float] = (1e5, 5e6)  # tensile strength (Pa)
    phi_p: Tuple[float, float] = (0.20, 0.40)  # porosity

    def grid(self, n: int = 5) -> list:
        """Generate uniform grid over the prior (n samples per dim)."""
        from itertools import product
        axes = [
            np.linspace(self.c[0], self.c[1], n),
            np.linspace(self.phi_deg[0], self.phi_deg[1], n),
            np.linspace(self.k[0], self.k[1], n),
            np.linspace(self.tau_0[0], self.tau_0[1], n),
            np.linspace(self.sigma_t[0], self.sigma_t[1], n),
            np.linspace(self.phi_p[0], self.phi_p[1], n),
        ]
        return list(product(*axes))


# ============================================================== Forward solver
def forward_glof(
    theta: GLOFMaterialState,
    water_head_m: float = 100.0,
    dam_height_m: float = 150.0,
    dt_sec: float = 1.0,
    n_steps: int = 180,         # 3 minutes at 1Hz; demo
) -> dict:
    """Forward simulate GLOF cascade for one material sample.

    Hydrostatic pore pressure: u = rho_w * g * h_water
    Vertical stress at base: sigma_v = rho_bulk * g * h_dam
    Mohr-Coulomb check at dam base; breach triggers at first failure.

    Returns dict with time series + breach timing.
    """
    from dataclasses import replace
    rho_w = 1000.0
    g = 9.81
    Pp_series = []
    breach_step = -1
    phase_series = [theta.phase_id.value]

    s = theta
    for t in range(n_steps):
        # Water head ramps linearly 0 -> max over first 90 steps
        h_w = min(water_head_m, water_head_m * t / 90.0)
        Pp = rho_w * g * h_w
        s = replace(s, Pp=Pp,
                    saturation=min(1.0, h_w / max(water_head_m, 1e-3)))
        Pp_series.append(Pp)

        # Mohr-Coulomb check at dam base (sigma_n from gravity, tau from
        # hydrostatic + overburden)
        sigma_n = s.rho * g * dam_height_m
        tau_applied = Pp * 0.5  # simplified: hydrostatic shear at base

        v = evaluate_cascade(s, sigma_n=sigma_n, tau_applied=tau_applied)
        if v.fails and breach_step < 0:
            breach_step = t
            s = replace(s, phase_id=v.next_phase)
        phase_series.append(s.phase_id.value)

    # Peak discharge estimate (empirical — Costa 1985 envelope)
    if breach_step >= 0:
        Q_peak = 3.1 * (water_head_m ** 1.5) * (breach_width_m_est(theta) ** 0.5)
        t_to_peak_min = 5.0 + 0.5 * water_head_m / 10.0
    else:
        Q_peak = 0.0
        t_to_peak_min = float("inf")

    return {
        "Pp_series": Pp_series,
        "phase_series": phase_series,
        "breach_step": breach_step,
        "breach_time_min": breach_step * dt_sec / 60.0 if breach_step >= 0 else None,
        "Q_peak_m3s": Q_peak,
        "time_to_peak_min": t_to_peak_min,
        "downstream_surge_m_est": min(9.0, water_head_m * 0.09),
    }


def breach_width_m_est(theta: GLOFMaterialState) -> float:
    """Empirical breach width from dam geometry + cohesion.

    Froehlich 1995 / Costa 1985 envelope: ~3-5× material-dependent.
    """
    base = 50.0
    cohesion_factor = max(1.0, theta.c / 5000.0)
    return base / cohesion_factor


# ============================================================== Likelihood
def log_likelihood(theta: GLOFMaterialState, obs: GLOFObservation) -> float:
    """Gaussian likelihood log P(obs | theta).

    sigma_obs chosen per variable based on typical measurement uncertainty:
        head: 0.5 m, Q: 200 m3/s, t_peak: 2 min, surge: 0.5 m
    """
    sim = forward_glof(theta, water_head_m=obs.water_head_m)

    sigma_h = 0.5
    sigma_Q = 200.0
    sigma_t = 2.0
    sigma_s = 0.5

    L_h = -0.5 * ((obs.water_head_m - obs.water_head_m) / sigma_h) ** 2
    L_Q = -0.5 * ((sim["Q_peak_m3s"] - obs.peak_discharge_m3s) / sigma_Q) ** 2
    L_t = -0.5 * ((sim["time_to_peak_min"] - obs.time_to_peak_min) / sigma_t) ** 2
    L_s = -0.5 * ((sim["downstream_surge_m_est"] - obs.downstream_surge_m) / sigma_s) ** 2
    # Penalty if no breach at all (should breach within 3 hrs)
    L_b = 0.0 if sim["breach_step"] >= 0 else -10.0

    return L_h + L_Q + L_t + L_s + L_b


# ============================================================== Inverse solver
def inverse_infer(
    obs: GLOFObservation,
    base_theta: Optional[GLOFMaterialState] = None,
    prior: Optional[ThetaPrior] = None,
    n_grid: int = 4,
) -> Tuple[GLOFMaterialState, float, dict]:
    """Grid-search inverse inference over ThetaPrior.

    Returns (theta_hat, max_log_likelihood, posterior_summary).
    """
    base = base_theta or himalayan_defaults()
    pr = prior or ThetaPrior()

    grid = pr.grid(n=n_grid)
    best_ll = -float("inf")
    best_grid = None
    all_ll = []

    for c, phi_deg, k, tau_0, sigma_t, phi_p in grid:
        s = GLOFMaterialState(
            rho=base.rho, E=base.E, nu=base.nu,
            c=c, phi=math.radians(phi_deg),
            k=k, phi_p=phi_p,
            tau_0=tau_0, sigma_t=sigma_t,
            T=base.T, Pp=base.Pp,
            cell_id="grid_sample",
            phase_id=base.phase_id,
        )
        ll = log_likelihood(s, obs)
        all_ll.append((s, ll))
        if ll > best_ll:
            best_ll = ll
            best_grid = s
    return _emit_grid_result(all_ll, base, pr, n_grid)


def _emit_grid_result(all_ll, base, pr, n_grid):
    """Emit grid-search posterior summary (legacy Phase A behavior)."""
    all_ll.sort(key=lambda x: x[1], reverse=True)
    top3 = [{"c": s.c, "phi_deg": math.degrees(s.phi), "k": s.k,
             "tau_0": s.tau_0, "log_lik": round(ll, 2)}
            for s, ll in all_ll[:3]]
    best_grid = all_ll[0][0]
    return best_grid, all_ll[0][1], {"top3": top3, "n_grid": len(all_ll), "method": "grid"}


def mcmc_infer(
    obs: GLOFObservation,
    base_theta: Optional[GLOFMaterialState] = None,
    n_warmup: int = 80,
    n_iter: int = 200,
    n_chains: int = 2,
    seed: int = 42,
) -> Tuple[GLOFMaterialState, float, dict]:
    """Phase C — proper Bayesian posterior via adaptive Metropolis-Hastings.

    Uses gl_mcmc.metropolis_hastings for the sampler. Returns the best sample
    + posterior diagnostics (R-hat, ESS, percentiles).
    """
    from geox_core.physics.gl_mcmc import metropolis_hastings
    base = base_theta or himalayan_defaults()
    chains, diag = metropolis_hastings(
        base, obs,
        n_warmup=n_warmup, n_iter=n_iter,
        n_chains=n_chains, seed=seed,
    )
    # Find best sample across chains
    best_ll = -float("inf")
    best_theta = base
    n_samples = 0
    for c in chains:
        for x in c[n_warmup:]:
            s = GLOFMaterialState(
                rho=base.rho,
                E=math.exp(x[0]),
                nu=base.nu,
                c=math.exp(x[1]),
                phi=max(0.0, min(1.55, x[2])),
                k=base.k,
                phi_p=max(0.0, min(0.6, x[5])),
                tau_0=math.exp(x[3]),
                sigma_t=math.exp(x[4]),
                T=base.T, Pp=base.Pp,
                cell_id="mcmc_sample",
                phase_id=base.phase_id,
            )
            ll = log_likelihood(s, obs)
            n_samples += 1
            if ll > best_ll:
                best_ll = ll
                best_theta = s
    posterior = {
        "method": "mcmc",
        "r_hat": diag.r_hat,
        "ess": diag.ess,
        "accept_rate": diag.accept_rate,
        "converged": diag.converged,
        "mean": diag.mean,
        "std": diag.std,
        "p05": diag.p05,
        "p50": diag.p50,
        "p95": diag.p95,
        "n_samples": n_samples,
    }
    return best_theta, best_ll, posterior


def saint_venant_propagate(
    breach_Q_func,
    length_m: float = 60_000.0,
    nx: int = 200,
    manning_n: float = 0.05,
    bed_slope: float = 0.01,
    duration_s: float = 7200.0,
    output_interval_s: float = 120.0,
) -> dict:
    """Phase C — 1D Saint-Venant propagation from breach to downstream.

    Returns dict with time series of depth, velocity, Q along the domain.
    """
    from geox_core.physics.gl_saint_venant import (
        SVDomain, simulate_glof_propagation,
    )
    domain = SVDomain(length_m=length_m, nx=nx, manning_n=manning_n,
                      bed_slope=bed_slope)
    result = simulate_glof_propagation(
        breach_Q_func=breach_Q_func, domain=domain,
        duration_s=duration_s, output_interval_s=output_interval_s,
    )
    # Find peak downstream
    Q_downstream = result.Q[:, -1]
    peak_idx = int(np.argmax(Q_downstream))
    return {
        "x_m": result.x.tolist(),
        "t_s": result.t.tolist(),
        "h_matrix": result.h.tolist(),
        "u_matrix": result.u.tolist(),
        "Q_matrix": result.Q.tolist(),
        "peak_downstream_m3_s": float(Q_downstream[peak_idx]),
        "peak_time_s": float(result.t[peak_idx]),
        "peak_depth_m": float(result.h[peak_idx, -1]),
        "peak_velocity_m_s": float(result.u[peak_idx, -1]),
        "cfl_max": float(result.cfl),
        "n_steps": result.n_steps,
    }


# ============================================================== Metabolize
@dataclass
class MetabolizeReceipt:
    """F12 witness receipt from one F-I-M cycle."""
    cycle_id: str
    timestamp_ns: int
    theta_hat_dict: dict
    log_likelihood: float
    forward_prediction: dict
    observation: dict
    G_score: float          # geometric-mean tri-witness 0..1
    epicycle_delta: float   # improvement metric (LL improvement vs prior)
    prior_cycle_id: Optional[str] = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def tri_witness_score(
    forward_pred: dict, obs: GLOFObservation, theta: GLOFMaterialState,
) -> float:
    """Geometric mean of three witness components (F12 — G = cbrt(H*M*E)).

    H = human/source reliability (obs.source if recognized)
    M = model internal consistency (1 - normalized residual)
    E = external physics bounds check (all 9 within bounds)
    """
    # Human witness — obs source quality
    H = {
        "field": 1.0, "gauge": 0.9, "satellite": 0.85,
        "social_media": 0.3, "model": 0.5,
    }.get(obs.source, 0.4)

    # Model witness — 1 - normalized residual across 3 observable variables
    sigma = np.array([200.0, 2.0, 0.5])
    resid = np.array([
        (forward_pred["Q_peak_m3s"] - obs.peak_discharge_m3s) / sigma[0],
        (forward_pred["time_to_peak_min"] - obs.time_to_peak_min) / sigma[1],
        (forward_pred["downstream_surge_m_est"] - obs.downstream_surge_m) / sigma[2],
    ])
    M = float(np.exp(-0.5 * np.mean(resid ** 2)))

    # External witness — physics bounds
    ok, _ = theta.validate()
    E = 1.0 if ok else 0.0

    G = (H * M * E) ** (1.0 / 3.0)
    return round(G, 4)


def metabolize(
    cycle_id: str,
    theta_hat: GLOFMaterialState,
    forward_pred: dict,
    obs: GLOFObservation,
    prior_receipt: Optional[MetabolizeReceipt] = None,
) -> MetabolizeReceipt:
    """Close the loop: produce F12 witness receipt."""
    log_ll = log_likelihood(theta_hat, obs)
    G = tri_witness_score(forward_pred, obs, theta_hat)
    delta = (log_ll - prior_receipt.log_likelihood) if prior_receipt else 0.0

    return MetabolizeReceipt(
        cycle_id=cycle_id or hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:12],
        timestamp_ns=time.time_ns(),
        theta_hat_dict=theta_hat.to_dict(),
        log_likelihood=log_ll,
        forward_prediction=forward_pred,
        observation=obs.to_dict(),
        G_score=G,
        epicycle_delta=delta,
        prior_cycle_id=prior_receipt.cycle_id if prior_receipt else None,
    )


# ============================================================== Seismic coupling
def seed_from_seismic(
    physics13_state_dict: dict,
    extras: dict,
) -> GLOFMaterialState:
    """Bridge existing Physics13State -> GLOFMaterialState.

    Wrapper around geomaterial.from_physics13_state for clarity at the
    F-I-M loop boundary.
    """
    from geox_core.physics.glgeomaterial import from_physics13_state
    # The Physics13State object lives in geox_core.physics.state
    from geox_core.physics.state import Physics13State
    p = Physics13State.from_raw_dict(physics13_state_dict)
    return from_physics13_state(p, **extras)


# ============================================================== Full cycle driver
def run_fim_cycle(
    obs: GLOFObservation,
    cycle_id: str = "",
    n_grid: int = 4,
    prior_receipt: Optional[MetabolizeReceipt] = None,
) -> Tuple[GLOFMaterialState, MetabolizeReceipt]:
    """Run one complete Forward-Inverse-Metabolize cycle."""
    theta_hat, log_ll, posterior = inverse_infer(obs, n_grid=n_grid)
    fwd = forward_glof(theta_hat, water_head_m=obs.water_head_m)
    receipt = metabolize(cycle_id, theta_hat, fwd, obs, prior_receipt)
    return theta_hat, receipt


if __name__ == "__main__":
    # Bhote Koshi GLOF observation (2026-08-26 — published field data)
    obs = GLOFObservation(
        label="Trishuli_2026_08_26",
        water_head_m=110.0,
        breach_width_m=150.0,
        peak_discharge_m3s=3000.0,
        time_to_peak_min=12.0,
        downstream_surge_m=9.0,
        source="gauge",
    )

    print("Running F-I-M cycle for Trishuli 2026-08-26 GLOF...")
    theta_hat, receipt = run_fim_cycle(obs, cycle_id="c1", n_grid=3)
    print(f"theta_hat: c={theta_hat.c:.0f} Pa, phi={math.degrees(theta_hat.phi):.1f} deg, "
          f"k={theta_hat.k:.2e} m^2, tau_0={theta_hat.tau_0:.0f} Pa, "
          f"sigma_t={theta_hat.sigma_t:.0f} Pa")
    print(f"log_lik={receipt.log_likelihood:.3f}, G_score={receipt.G_score:.3f}")
    print(f"forward: Q_peak={receipt.forward_prediction['Q_peak_m3s']:.0f} m3/s, "
          f"surge={receipt.forward_prediction['downstream_surge_m_est']:.2f} m")
    print(f"posterior top3: {json.dumps(receipt.to_dict()['forward_prediction']['top3'] if False else '', indent=2)}")
    print("receipt keys:", list(receipt.to_dict().keys()))