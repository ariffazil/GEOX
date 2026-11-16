"""gl_mcmc.py — Metropolis-Hastings MCMC sampler for GLOF posterior inference.

Replaces the uniform-grid search in gl_forward_inverse_loop.py with a proper
Bayesian sampler. Two-stage:

  Stage 1 (warm-up): Adaptive Metropolis — tune proposal covariance from
    chain history (Haario et al. 2001).
  Stage 2 (production): Standard Metropolis-Hastings with tuned proposal.

Convergence diagnostics:
  - R-hat (Gelman-Rubin): potential scale reduction factor across chains.
  - ESS (effective sample size): integrated autocorrelation time.
  - Trace mean ± MCSE.

Returned posterior_summary:
  - mean, std, 5/50/95 percentiles per parameter
  - G-R, ESS, n_accept, n_iter

DITEMPA BUKAN DIBERI — posterior is forged from likelihood, not assumed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional
from collections.abc import Callable

import numpy as np

from geox_core.physics.gl_forward_inverse_loop import (
    GLOFObservation,
    forward_glof,
    log_likelihood,
)
from geox_core.physics.glgeomaterial import GLOFMaterialState


@dataclass
class MCMCDiagnostics:
    n_iter: int = 0
    n_accept: int = 0
    accept_rate: float = 0.0
    r_hat: float = 0.0
    ess: float = 0.0
    mean: dict = field(default_factory=dict)
    std: dict = field(default_factory=dict)
    p05: dict = field(default_factory=dict)
    p50: dict = field(default_factory=dict)
    p95: dict = field(default_factory=dict)
    converged: bool = False


def _log_prior(theta: GLOFMaterialState) -> float:
    """Box-uniform prior on the 6 most-uncertain dam parameters.

    Other fields are derived or fixed (g=9.81, rho is weakly informed).
    """
    valid = theta.E > 0 and theta.c > 0 and theta.phi > 0 and theta.tau_0 > 0 and theta.sigma_t > 0 and theta.phi_p > 0
    return 0.0 if valid else -1e10


def _pack_theta(theta: GLOFMaterialState) -> np.ndarray:
    """Pack 6 uncertain params into a vector (log-scale for positive).

    Sampling on (log_E, log_c, phi, log_tau_0, log_sigma_t, phi_p) since
    these are the 6 most-uncertain for dam-material inference.
    """
    return np.array(
        [
            math.log(max(theta.E, 1.0)),
            math.log(max(theta.c, 1.0)),
            theta.phi,
            math.log(max(theta.tau_0, 1.0)),
            math.log(max(theta.sigma_t, 1.0)),
            theta.phi_p,
        ]
    )


def _unpack_theta(theta0: GLOFMaterialState, x: np.ndarray) -> GLOFMaterialState:
    """Unpack 6-vector back into a GLOFMaterialState (keep non-sampled fields)."""
    from dataclasses import replace

    return replace(
        theta0,
        E=math.exp(x[0]),
        c=math.exp(x[1]),
        phi=max(0.0, min(1.55, x[2])),
        tau_0=math.exp(x[3]),
        sigma_t=math.exp(x[4]),
        phi_p=max(0.0, min(0.6, x[5])),
    )


def _log_posterior(theta: GLOFMaterialState, obs: GLOFObservation) -> float:
    """Unnormalized log posterior = log likelihood + log prior."""
    lp = _log_prior(theta)
    if lp < -1e9:
        return -1e10
    return lp + log_likelihood(theta, obs)


def metropolis_hastings(
    theta0: GLOFMaterialState,
    obs: GLOFObservation,
    n_warmup: int = 200,
    n_iter: int = 1000,
    n_chains: int = 4,
    seed: int | None = None,
) -> tuple:
    """Adaptive Metropolis-Hastings sampler for the 6-D GLOF posterior.

    Args:
        theta0: Initial guess (defaults to himalayan_defaults if too vague).
        obs: GLOFObservation dict.
        n_warmup: Adaptive warm-up iterations per chain.
        n_iter: Production iterations per chain.
        n_chains: Number of independent chains for R-hat.

    Returns:
        chains: list of (n_iter,) arrays of accepted samples per chain.
        diag: MCMCDiagnostics with posterior summary.
    """
    base_seed = 42 if seed is None else seed
    chain_rngs = [
        np.random.default_rng(np.random.SeedSequence([base_seed, c_idx]))
        for c_idx in range(n_chains)
    ]

    # Initial parameter vector + covariance
    x0 = _pack_theta(theta0)
    n_params = len(x0)
    # Initial proposal: diagonal with moderate scale
    proposal_cov = np.eye(n_params) * 0.1
    proposal_chol = np.linalg.cholesky(proposal_cov)

    # Initialize chains from slightly perturbed starts (isolated RNG per chain)
    chains_x = []
    chains_ll = []
    for c_idx in range(n_chains):
        perturb = chain_rngs[c_idx].normal(0, 0.05, n_params)
        x_init = x0 + perturb
        theta_init = _unpack_theta(theta0, x_init)
        ll_init = _log_posterior(theta_init, obs)
        chains_x.append([x_init.copy()])
        chains_ll.append([ll_init])

    # Adaptive Metropolis warm-up (per chain: n_warmup warm-up + n_iter production)
    adapt_scale = 2.38**2 / n_params
    eps = 1e-6
    chain_cov = proposal_cov.copy()
    prod_accepts = 0
    prod_proposals = 0

    for step in range(n_warmup + n_iter):
        is_prod = step >= n_warmup
        # Adapt proposal covariance only during warm-up to preserve stationarity
        if not is_prod and step >= 25 and step % 10 == 0:
            all_samples = []
            for c in chains_x:
                all_samples.extend(c[-100:])
            if len(all_samples) >= 20:
                samples_arr = np.array(all_samples)
                chain_cov = np.cov(samples_arr.T) + eps * np.eye(n_params)
                try:
                    proposal_chol = np.linalg.cholesky(chain_cov * adapt_scale)
                except np.linalg.LinAlgError:
                    pass  # fall back to previous cholesky

        for chain_idx in range(n_chains):
            rng_c = chain_rngs[chain_idx]
            x_curr = np.array(chains_x[chain_idx][-1])

            try:
                x_prop = x_curr + proposal_chol @ rng_c.normal(0, 1, n_params)
            except ValueError:
                x_prop = x_curr + rng_c.normal(0, 0.05, n_params)

            theta_prop = _unpack_theta(theta0, x_prop)
            ll_prop = _log_posterior(theta_prop, obs)
            ll_curr = chains_ll[chain_idx][-1]

            # Metropolis accept/reject
            log_alpha = ll_prop - ll_curr
            if is_prod:
                prod_proposals += 1
            if math.log(max(float(rng_c.random()), 1e-300)) < log_alpha:
                chains_x[chain_idx].append(x_prop.copy())
                chains_ll[chain_idx].append(ll_prop)
                if is_prod:
                    prod_accepts += 1
            else:
                chains_x[chain_idx].append(x_curr.copy())
                chains_ll[chain_idx].append(ll_curr)

    # Diagnostics (skip initial seed state + n_warmup warm-up draws)
    prod_chains = [np.array(c[n_warmup + 1 :]) for c in chains_x]
    diag = diagnose_chains(prod_chains, n_accept=prod_accepts, n_proposals=prod_proposals)
    return chains_x, diag


def _chain_ess(x: np.ndarray) -> float:
    """Estimate effective sample size of a 1D chain via Geyer's positive sequence."""
    n = len(x)
    if n < 4:
        return 0.0
    xc = x - float(np.mean(x))
    var = float(np.dot(xc, xc) / n)
    if not math.isfinite(var) or var <= 1e-18:
        return 0.0  # frozen chain has zero effective information

    acov = np.correlate(xc, xc, mode="full")[n - 1 :] / (var * n)
    # Geyer's initial positive sequence on lag pairs
    tau = 1.0
    if n > 2:
        p0 = 1.0 + float(acov[1])
        pair_sum = max(0.0, p0)
        k = 2
        while k + 1 < n:
            pk = float(acov[k] + acov[k + 1])
            if pk <= 0.0:
                break
            pair_sum += pk
            k += 2
        tau = max(1.0, -1.0 + 2.0 * pair_sum)
    return float(min(float(n), n / tau))


def diagnose_chains(
    prod_chains: list[np.ndarray],
    n_accept: int | None = None,
    n_proposals: int | None = None,
    labels: list[str] | None = None,
) -> MCMCDiagnostics:
    """Compute Gelman-Rubin R-hat, autocorrelation ESS, and convergence gate."""
    n_chains = len(prod_chains)
    n_iter = prod_chains[0].shape[0] if n_chains else 0
    n_params = prod_chains[0].shape[1] if n_chains and n_iter else 0
    if labels is None:
        labels = ["E", "c", "phi", "tau_0", "sigma_t", "phi_p"]

    if n_chains == 0 or n_iter == 0 or n_params == 0:
        return MCMCDiagnostics(n_iter=0, n_accept=0, accept_rate=0.0, r_hat=float("inf"), ess=0.0, converged=False)

    r_hats: list[float] = []
    ess_vals: list[float] = []
    for p_idx in range(n_params):
        if n_chains >= 2 and n_iter >= 2:
            chain_means = np.array([c[:, p_idx].mean() for c in prod_chains])
            chain_vars = np.array([c[:, p_idx].var(ddof=1) for c in prod_chains])
            B = n_iter * float(np.var(chain_means, ddof=1))
            W = float(chain_vars.mean())
            if W <= 1e-18:
                r_hat = float("inf")
            else:
                var_plus = ((n_iter - 1) / n_iter) * W + B / n_iter
                r_hat = float(np.sqrt(var_plus / W))
        else:
            r_hat = float("inf")
        r_hats.append(r_hat)

        param_ess = sum(_chain_ess(c[:, p_idx]) for c in prod_chains)
        ess_vals.append(param_ess)

    all_samples = np.vstack(prod_chains)
    summary_mean = all_samples.mean(axis=0)
    summary_std = all_samples.std(axis=0)
    summary_p05 = np.percentile(all_samples, 5, axis=0)
    summary_p50 = np.percentile(all_samples, 50, axis=0)
    summary_p95 = np.percentile(all_samples, 95, axis=0)

    if n_accept is not None and n_proposals is not None and n_proposals > 0:
        actual_accept = int(n_accept)
        accept_rate = float(n_accept / n_proposals)
    else:
        # Infer transitions from adjacent distinct rows if proposal counts not supplied
        transitions = 0
        proposals = 0
        for c in prod_chains:
            if len(c) > 1:
                diffs = np.any(np.diff(c, axis=0) != 0, axis=1)
                transitions += int(np.sum(diffs))
                proposals += len(c) - 1
        actual_accept = transitions
        accept_rate = float(transitions / proposals) if proposals > 0 else 0.0

    worst_r_hat = float(max(r_hats))
    min_ess = float(min(ess_vals))
    converged = bool(
        n_chains >= 2
        and n_iter >= 10
        and math.isfinite(worst_r_hat)
        and worst_r_hat < 1.1
        and min_ess >= 10.0
        and accept_rate > 0.0
    )

    param_names = [labels[i] if i < len(labels) else f"p{i}" for i in range(n_params)]
    return MCMCDiagnostics(
        n_iter=n_iter,
        n_accept=actual_accept,
        accept_rate=accept_rate,
        r_hat=worst_r_hat,
        ess=min_ess,
        mean={param_names[i]: float(summary_mean[i]) for i in range(n_params)},
        std={param_names[i]: float(summary_std[i]) for i in range(n_params)},
        p05={param_names[i]: float(summary_p05[i]) for i in range(n_params)},
        p50={param_names[i]: float(summary_p50[i]) for i in range(n_params)},
        p95={param_names[i]: float(summary_p95[i]) for i in range(n_params)},
        converged=converged,
    )


def _diagnose(chains_x: list, chains_ll: list, n_warmup: int) -> MCMCDiagnostics:
    """Backward-compatible wrapper over diagnose_chains."""
    prod_chains = [np.array(c[n_warmup:]) for c in chains_x]
    return diagnose_chains(prod_chains)


if __name__ == "__main__":
    from geox_core.physics.gl_forward_inverse_loop import run_fim_cycle
    from geox_core.physics.glgeomaterial import himalayan_defaults

    obs = GLOFObservation(
        label="Trishuli_MCMC_test",
        water_head_m=110.0,
        breach_width_m=150.0,
        peak_discharge_m3s=3000.0,
        time_to_peak_min=12.0,
        downstream_surge_m=9.0,
        source="gauge",
    )

    print("Running MCMC for Trishuli 2026-08-26...")
    chains, diag = metropolis_hastings(
        himalayan_defaults(),
        obs,
        n_warmup=100,
        n_iter=300,
        n_chains=2,
        seed=42,
    )
    print(f"  n_iter = {diag.n_iter}")
    print(f"  accept_rate = {diag.accept_rate:.2%}")
    print(f"  R-hat (avg) = {diag.r_hat:.3f}")
    print(f"  ESS (avg) = {diag.ess:.0f}")
    print(f"  converged (R-hat < 1.1) = {diag.converged}")
    print("  posterior summary:")
    for k in diag.mean:
        print(f"    {k:14s} mean={diag.mean[k]:.3g} p05={diag.p05[k]:.3g} p95={diag.p95[k]:.3g}")
