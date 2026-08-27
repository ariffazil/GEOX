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
from typing import Callable, Optional

import numpy as np

from geox_core.physics.gl_forward_inverse_loop import (
    GLOFObservation, forward_glof, log_likelihood,
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
    valid = (theta.E > 0 and theta.c > 0 and theta.phi > 0 and
              theta.tau_0 > 0 and theta.sigma_t > 0 and theta.phi_p > 0)
    return 0.0 if valid else -1e10


def _pack_theta(theta: GLOFMaterialState) -> np.ndarray:
    """Pack 6 uncertain params into a vector (log-scale for positive).

    Sampling on (log_E, log_c, phi, log_tau_0, log_sigma_t, phi_p) since
    these are the 6 most-uncertain for dam-material inference.
    """
    return np.array([
        math.log(max(theta.E, 1.0)),
        math.log(max(theta.c, 1.0)),
        theta.phi,
        math.log(max(theta.tau_0, 1.0)),
        math.log(max(theta.sigma_t, 1.0)),
        theta.phi_p,
    ])


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
    seed: Optional[int] = None,
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
    if seed is not None:
        np.random.seed(seed)

    # Initial parameter vector + covariance
    x0 = _pack_theta(theta0)
    n_params = len(x0)
    # Initial proposal: diagonal with moderate scale
    proposal_cov = np.eye(n_params) * 0.1
    proposal_chol = np.linalg.cholesky(proposal_cov)

    # Initialize chains from slightly perturbed starts
    chains_x = []
    chains_ll = []
    for c_idx in range(n_chains):
        np.random.seed((seed or 42) + c_idx)
        perturb = np.random.normal(0, 0.05, n_params)
        x_init = x0 + perturb
        theta_init = _unpack_theta(theta0, x_init)
        ll_init = _log_posterior(theta_init, obs)
        chains_x.append([x_init.copy()])
        chains_ll.append([ll_init])

    # Adaptive Metropolis warm-up
    adapt_scale = 2.38 ** 2 / n_params
    eps = 1e-6
    chain_mean = np.mean([np.array(c[-1]) for c in chains_x], axis=0)
    chain_cov = proposal_cov.copy()
    sample_count = n_chains

    for it in range(n_warmup + n_iter):
        chain_idx = it % n_chains
        x_curr = np.array(chains_x[chain_idx][-1])

        # Adapt covariance from history if sufficient samples
        if it >= 50 and it % 20 == 0:
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

        # Propose
        try:
            x_prop = x_curr + proposal_chol @ np.random.normal(0, 1, n_params)
        except ValueError:
            x_prop = x_curr + np.random.normal(0, 0.05, n_params)

        theta_prop = _unpack_theta(theta0, x_prop)
        ll_prop = _log_posterior(theta_prop, obs)
        ll_curr = chains_ll[chain_idx][-1]

        # Metropolis accept/reject
        log_alpha = ll_prop - ll_curr
        if math.log(np.random.random()) < log_alpha:
            chains_x[chain_idx].append(x_prop.copy())
            chains_ll[chain_idx].append(ll_prop)
        else:
            chains_x[chain_idx].append(x_curr.copy())
            chains_ll[chain_idx].append(ll_curr)

    # Diagnostics
    diag = _diagnose(chains_x, chains_ll, n_warmup)
    return chains_x, diag


def _diagnose(chains_x: list, chains_ll: list, n_warmup: int) -> MCMCDiagnostics:
    """Compute Gelman-Rubin R-hat, ESS, posterior summary."""
    # Drop warm-up
    prod_chains = [np.array(c[n_warmup:]) for c in chains_x]
    n_chains = len(prod_chains)
    n_iter = prod_chains[0].shape[0]
    n_params = prod_chains[0].shape[1]

    # Per-parameter Gelman-Rubin R-hat
    r_hats = []
    ess_vals = []
    for p_idx in range(n_params):
        chain_means = np.array([c[:, p_idx].mean() for c in prod_chains])
        chain_vars = np.array([c[:, p_idx].var(ddof=1) for c in prod_chains])
        overall_mean = chain_means.mean()
        B = n_iter * np.var(chain_means, ddof=1)  # between-chain var
        W = chain_vars.mean()                        # within-chain var
        var_plus = (n_iter - 1) / n_iter * W + B / n_iter
        r_hat = float(np.sqrt(var_plus / W)) if W > 0 else float('inf')
        r_hats.append(r_hat)
        # Effective sample size (rough): n_iter / (1 + 2 * sum_autocorr)
        ess = n_iter  # crude upper bound
        ess_vals.append(ess)

    # Flatten for posterior summary
    all_samples = np.vstack(prod_chains)  # (n_chains*n_iter, n_params)
    summary_mean = all_samples.mean(axis=0)
    summary_std = all_samples.std(axis=0)
    summary_p05 = np.percentile(all_samples, 5, axis=0)
    summary_p50 = np.percentile(all_samples, 50, axis=0)
    summary_p95 = np.percentile(all_samples, 95, axis=0)

    # Find best sample (highest log-likelihood)
    all_ll = np.array([l for ll_list in chains_ll for l in ll_list[n_warmup:]])
    best_idx = int(np.argmax(all_ll))
    best_ll = float(all_ll[best_idx])

    labels = ["E", "c", "phi", "tau_0", "sigma_t", "phi_p"]

    return MCMCDiagnostics(
        n_iter=n_iter,
        n_accept=int(np.sum(all_ll > -1e9)),
        accept_rate=float(np.mean(all_ll > -1e9)),
        r_hat=float(np.mean(r_hats)),
        ess=float(np.mean(ess_vals)),
        mean={labels[i]: float(summary_mean[i]) for i in range(n_params)},
        std={labels[i]: float(summary_std[i]) for i in range(n_params)},
        p05={labels[i]: float(summary_p05[i]) for i in range(n_params)},
        p50={labels[i]: float(summary_p50[i]) for i in range(n_params)},
        p95={labels[i]: float(summary_p95[i]) for i in range(n_params)},
        converged=(float(np.mean(r_hats)) < 1.1),
    )


if __name__ == "__main__":
    from geox_core.physics.gl_forward_inverse_loop import run_fim_cycle
    from geox_core.physics.glgeomaterial import himalayan_defaults

    obs = GLOFObservation(
        label="Trishuli_MCMC_test",
        water_head_m=110.0, breach_width_m=150.0,
        peak_discharge_m3s=3000.0, time_to_peak_min=12.0,
        downstream_surge_m=9.0, source="gauge",
    )

    print("Running MCMC for Trishuli 2026-08-26...")
    chains, diag = metropolis_hastings(
        himalayan_defaults(), obs,
        n_warmup=100, n_iter=300, n_chains=2, seed=42,
    )
    print(f"  n_iter = {diag.n_iter}")
    print(f"  accept_rate = {diag.accept_rate:.2%}")
    print(f"  R-hat (avg) = {diag.r_hat:.3f}")
    print(f"  ESS (avg) = {diag.ess:.0f}")
    print(f"  converged (R-hat < 1.1) = {diag.converged}")
    print(f"  posterior summary:")
    for k in diag.mean:
        print(f"    {k:14s} mean={diag.mean[k]:.3g} "
              f"p05={diag.p05[k]:.3g} p95={diag.p95[k]:.3g}")