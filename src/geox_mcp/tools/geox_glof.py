"""geox_glof — Unified GLOF Multi-Phase Cascade Tool
════════════════════════════════════════════════════
333 ARCHITECT ruling (2026-09-19): collapse 7 geox_glof_cascade_* tools into
one unified tool following the multi-mode pattern of geox_seismic_compute
and geox_claim.

Physics preserved — multi-phase solid → granular → fluid cascade:
  • SOLID DAM:    Mohr-Coulomb yield surface (geox_core.physics.glphase_switcher)
  • GRANULAR DEBRIS: friction + pore-pressure mechanics (glgeomaterial)
  • LIQUID FLOOD: Saint-Venant 1D shallow-water wave propagation (gl_forward_inverse_loop)

33D zen-33 state machine runs internally (M9 + P9 + W9 + X6 scalars).
The session registry (REGISTRY) is fully preserved — just hidden from the
public surface. Modes:

  mode='run'       (default) — full cascade: init→step(50, dt=1s)→metabolize.
                              Returns breach_summary + G-score in one call.
  mode='inverse'   — Bayesian grid-search inference from observations
  mode='mcmc'      — proper MCMC posterior (adaptive Metropolis-Hastings)
  mode='propagate' — 1D Saint-Venant downstream flood propagation
  mode='phase'     — raw Mohr-Coulomb yield surface (expert/debug mode)

DITEMPA BUKAN DIBERI — the cascade is forged, not given.
"""
from __future__ import annotations

import math
import logging
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from geox_mcp.tools.glof_cascade import (  # noqa: F401 — DEPRECATED surface kept internal
    geox_glof_cascade_initialize as _cascade_init,      # DEPRECATED: use geox_glof(mode='run')
    geox_glof_cascade_step as _cascade_step,            # DEPRECATED: use geox_glof(mode='run')
    geox_glof_cascade_phase as _cascade_phase,          # DEPRECATED: use geox_glof(mode='phase')
    geox_glof_cascade_inverse as _cascade_inverse,      # DEPRECATED: use geox_glof(mode='inverse')
    geox_glof_cascade_metabolize as _cascade_metabolize,# DEPRECATED: use geox_glof(mode='run')
    geox_glof_cascade_mcmc_inverse as _cascade_mcmc,    # DEPRECATED: use geox_glof(mode='mcmc')
    geox_glof_cascade_propagate as _cascade_propagate,  # DEPRECATED: use geox_glof(mode='propagate')
    GLOFCascadeInitRequest,
    GLOFCascadePhaseRequest,
    GLOFCascadeInverseRequest,
    GLOFCascadeMetabolizeRequest,
    GLOFCascadeMCMCRequest,
    GLOFCascadePropagateRequest,
    GLOFCascadeResponse,
    REGISTRY,
)

logger = logging.getLogger("geox.glof")

_TOOL = "geox_glof"


def _err(message: str, code: str = "BAD_MODE") -> dict[str, Any]:
    """Standard fail-closed error envelope."""
    return {
        "ok": False,
        "tool": _TOOL,
        "result": {},
        "error": code,
        "message": message,
        "governance_status": "HOLD",
        "execution_status": "ERROR",
    }


# ─────────────────────────────────────────────── mode='run' (full cascade)

async def _run_full_cascade(
    domain_bounds_x_m: float = 4000.0,
    domain_bounds_z_m: float = 600.0,
    resolution_m: float = 10.0,
    dam_height_m: float = 150.0,
    water_head_initial_m: float = 0.0,
    initial_state_33: Optional[dict] = None,
    panel_focus: str = "all",
    # step params
    n_steps: int = 50,
    dt_sec: float = 1.0,
    # metabolize params
    cycle_id: str = "",
    observation: Optional[dict] = None,
) -> dict[str, Any]:
    """Full cascade: init → step(n_steps) → metabolize. One-call summary."""
    # 1. init
    init_r = await _cascade_init(
        GLOFCascadeInitRequest(
            domain_bounds_x_m=domain_bounds_x_m,
            domain_bounds_z_m=domain_bounds_z_m,
            resolution_m=resolution_m,
            dam_height_m=dam_height_m,
            water_head_initial_m=water_head_initial_m,
            initial_state_33=initial_state_33,
            panel_focus=panel_focus,
        )
    )
    if not init_r.ok:
        return {"ok": False, "tool": _TOOL, "result": {}, "error": init_r.error,
                "message": "init failed"}

    state_id = init_r.result["snapshot"]["state_id"]

    # 2. step
    from geox_mcp.tools.glof_cascade import GLOFCascadeStepRequest
    step_r = await _cascade_step(
        GLOFCascadeStepRequest(
            state_id=state_id,
            n_steps=n_steps,
            dt_sec=dt_sec,
            boundary_conditions={},
        )
    )
    if not step_r.ok:
        return {"ok": False, "tool": _TOOL, "result": {}, "error": step_r.error,
                "message": "step failed"}

    step_summary = step_r.result.get("step_summary", {})

    # 3. metabolize (if observation provided, use it; else synthesise from fwd)
    # Build minimal forward_prediction from step_summary
    fwd_pred = {
        "Q_peak_m3s": step_summary.get("Q_peak_m3s", 0.0),
        "time_to_peak_min": step_summary.get("time_to_peak_min", 0.0),
        "downstream_surge_m_est": step_summary.get("downstream_surge_m_est", 0.0),
    }

    # Metabolize requires theta_hat + forward_prediction + observation.
    # Without caller-supplied observation we build a synthetic one for G-score.
    if observation is None:
        observation = {
            "label": f"run_mode_synthetic_{state_id[:8]}",
            "water_head_m": water_head_initial_m,
            "breach_width_m": 100.0,
            "peak_discharge_m3s": max(fwd_pred["Q_peak_m3s"], 1.0),
            "time_to_peak_min": max(fwd_pred["time_to_peak_min"], 1.0),
            "downstream_surge_m": max(fwd_pred["downstream_surge_m_est"], 0.1),
            "source": "synthetic_run_mode",
        }

    s = REGISTRY.get(state_id)
    if s is None:
        return _err(f"state_id {state_id} lost after step (internal error)", "REGISTRY_MISS")

    theta_hat = s.material.to_dict()

    met_r = await _cascade_metabolize(
        GLOFCascadeMetabolizeRequest(
            cycle_id=cycle_id or state_id[:12],
            theta_hat=theta_hat,
            forward_prediction=fwd_pred,
            observation=observation,
        )
    )

    breach_summary = {
        "state_id": state_id,
        "breach_time_min": step_summary.get("breach_time_min"),
        "Q_peak_m3s": step_summary.get("Q_peak_m3s"),
        "time_to_peak_min": step_summary.get("time_to_peak_min"),
        "downstream_surge_m_est": step_summary.get("downstream_surge_m_est"),
        "phase_final": step_summary.get("phase_final"),
        "n_steps": n_steps,
        "dt_sec": dt_sec,
    }

    g_score = None
    receipt = {}
    if met_r.ok:
        receipt = met_r.result.get("receipt", {})
        g_score = receipt.get("G_score")

    return {
        "ok": True,
        "tool": _TOOL,
        "mode": "run",
        "result": {
            "breach_summary": breach_summary,
            "G_score": g_score,
            "state_33": step_r.result.get("state_33", {}),
            "W_derived": step_r.result.get("W_derived", {}),
            "receipt": receipt,
        },
        "error": "",
    }


# ─────────────────────────────────────────────── unified entry point

async def geox_glof(
    mode: Literal["run", "inverse", "mcmc", "propagate", "phase"] = "run",
    # ── run mode params ─────────────────────────────────────────────────────
    domain_bounds_x_m: float = 4000.0,
    domain_bounds_z_m: float = 600.0,
    resolution_m: float = 10.0,
    dam_height_m: float = 150.0,
    water_head_initial_m: float = 0.0,
    initial_state_33: Optional[dict] = None,
    panel_focus: str = "all",
    n_steps: int = 50,
    dt_sec: float = 1.0,
    cycle_id: str = "",
    # ── inverse / mcmc mode params ──────────────────────────────────────────
    observation: Optional[dict] = None,
    base_theta: Optional[dict] = None,
    n_grid: int = 4,
    n_warmup: int = 80,
    n_iter: int = 200,
    n_chains: int = 2,
    seed: int = 42,
    # ── propagate mode params ────────────────────────────────────────────────
    breach_Q_profile: str = "costa1985",
    length_m: float = 60_000.0,
    nx: int = 200,
    manning_n: float = 0.05,
    bed_slope: float = 0.01,
    duration_s: float = 7200.0,
    output_interval_s: float = 120.0,
    # ── phase mode params ────────────────────────────────────────────────────
    state_id: str = "",
    cell_id: str = "",
    sigma_n: float = 500_000.0,
    tau_applied: float = 80_000.0,
    velocity: float = 0.0,
    sigma_applied: float = 0.0,
    saturation: Optional[float] = None,
) -> dict[str, Any]:
    """Unified GLOF multi-phase cascade simulation tool.

    Multi-phase physics: solid dam → granular debris → liquid flood.

    Modes
    ─────
    run        (default) Full cascade in one call: init → step(n_steps, dt_sec)
                → metabolize. Returns breach_summary (Q_peak, breach_time,
                downstream_surge) + G-score from tri-witness receipt.
                Use for most cases — 95% of GLOF workflows.

    inverse    Bayesian grid-search inference of dam parameters from a field
                observation (GLOFObservation dict). Returns theta_hat (9-scalar
                GLOFMaterialState), log_likelihood, and posterior_summary.
                Required observation keys: label, water_head_m, breach_width_m,
                peak_discharge_m3s, time_to_peak_min, downstream_surge_m.

    mcmc       Proper MCMC posterior (adaptive Metropolis-Hastings). More
                accurate than grid-search inverse but slower. Sampling over
                (E, c, phi, tau_0, sigma_t, phi_p). Returns posterior mean/std,
                percentiles, R-hat, ESS, accept_rate.

    propagate  1D Saint-Venant (shallow-water) downstream flood propagation via
                Lax-Friedrichs finite-volume solver with Manning friction.
                Returns time series of (h, u, Q) along domain + peak values.

    phase      Raw Mohr-Coulomb + Voellmy yield surface for one dam cell.
                Expert/debug mode — requires state_id from a prior run or
                explicit initialization. Returns failure_mode, margin, fails,
                transitions, fracture_K, and 33D-derived breach probability.

    Physics chain (all modes share the same underlying physics):
      • Mohr-Coulomb: τ_f = c + (σ_n − α·P_p) tan(φ)  [Terzaghi effective stress]
      • Voellmy: τ_bed = ρ·g·h·(sin θ + cos θ / ξ) + ρ·g·h² / (ξ·u²)
      • Saint-Venant 1D: ∂h/∂t + ∂(hu)/∂x = 0,  ∂(hu)/∂t + ∂(hu²+½gh²)/∂x = -g·h·S_f
      • 33D zen-33 state: M9 (material) + P9 (process) + W9 (wave) + X6 (extended)

    DITEMPA BUKAN DIBERI — the cascade is forged, not given.
    """
    try:
        # ── mode='run' ───────────────────────────────────────────────────────
        if mode == "run":
            return await _run_full_cascade(
                domain_bounds_x_m=domain_bounds_x_m,
                domain_bounds_z_m=domain_bounds_z_m,
                resolution_m=resolution_m,
                dam_height_m=dam_height_m,
                water_head_initial_m=water_head_initial_m,
                initial_state_33=initial_state_33,
                panel_focus=panel_focus,
                n_steps=n_steps,
                dt_sec=dt_sec,
                cycle_id=cycle_id,
                observation=observation,
            )

        # ── mode='inverse' ───────────────────────────────────────────────────
        if mode == "inverse":
            if not observation:
                return _err(
                    "mode='inverse' requires observation dict with keys: label, "
                    "water_head_m, breach_width_m, peak_discharge_m3s, "
                    "time_to_peak_min, downstream_surge_m.",
                    "MISSING_OBSERVATION",
                )
            r = await _cascade_inverse(
                GLOFCascadeInverseRequest(
                    observation=observation,
                    base_theta=base_theta,
                    n_grid=n_grid,
                )
            )
            return {
                "ok": r.ok,
                "tool": _TOOL,
                "mode": "inverse",
                "result": r.result,
                "error": r.error,
            }

        # ── mode='mcmc' ──────────────────────────────────────────────────────
        if mode == "mcmc":
            if not observation:
                return _err(
                    "mode='mcmc' requires observation dict with keys: label, "
                    "water_head_m, breach_width_m, peak_discharge_m3s, "
                    "time_to_peak_min, downstream_surge_m.",
                    "MISSING_OBSERVATION",
                )
            r = await _cascade_mcmc(
                GLOFCascadeMCMCRequest(
                    observation=observation,
                    base_theta=base_theta,
                    n_warmup=n_warmup,
                    n_iter=n_iter,
                    n_chains=n_chains,
                    seed=seed,
                )
            )
            return {
                "ok": r.ok,
                "tool": _TOOL,
                "mode": "mcmc",
                "result": r.result,
                "error": r.error,
            }

        # ── mode='propagate' ─────────────────────────────────────────────────
        if mode == "propagate":
            r = await _cascade_propagate(
                GLOFCascadePropagateRequest(
                    breach_Q_profile=breach_Q_profile,
                    length_m=length_m,
                    nx=nx,
                    manning_n=manning_n,
                    bed_slope=bed_slope,
                    duration_s=duration_s,
                    output_interval_s=output_interval_s,
                )
            )
            return {
                "ok": r.ok,
                "tool": _TOOL,
                "mode": "propagate",
                "result": r.result,
                "error": r.error,
            }

        # ── mode='phase' ─────────────────────────────────────────────────────
        if mode == "phase":
            if not state_id:
                return _err(
                    "mode='phase' requires state_id (from a prior run or explicit init). "
                    "Use mode='run' first or supply a valid state_id.",
                    "MISSING_STATE_ID",
                )
            if not cell_id:
                return _err("mode='phase' requires cell_id.", "MISSING_CELL_ID")
            r = await _cascade_phase(
                GLOFCascadePhaseRequest(
                    state_id=state_id,
                    cell_id=cell_id,
                    sigma_n=sigma_n,
                    tau_applied=tau_applied,
                    velocity=velocity,
                    sigma_applied=sigma_applied,
                    saturation=saturation,
                )
            )
            return {
                "ok": r.ok,
                "tool": _TOOL,
                "mode": "phase",
                "result": r.result,
                "error": r.error,
            }

        # ── unknown mode — fail-closed ────────────────────────────────────────
        return _err(
            f"Unknown mode='{mode}'. Valid modes: run, inverse, mcmc, propagate, phase.",
            "UNKNOWN_MODE",
        )

    except Exception as exc:  # pragma: no cover — unexpected runtime errors
        logger.exception("geox_glof(mode=%s) unhandled exception", mode)
        return {
            "ok": False,
            "tool": _TOOL,
            "mode": mode,
            "result": {},
            "error": type(exc).__name__,
            "message": str(exc),
        }
