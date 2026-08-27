"""glof_cascade.py — GEOX GLOF Cascade MCP tool surface.

Constitutional MCP tools wrapping geox_core.physics.gl* modules:

    geox_glof_cascade_initialize   — load geometry + initial state
    geox_glof_cascade_step        — advance one timestep
    geox_glof_cascade_phase        — yield surface evaluation per cell
    geox_glof_cascade_inverse     — Bayesian inference of dam params
    geox_glof_cascade_metabolize  — close F-I-M loop, emit receipt

Integrates existing GEOX surfaces:
    forward   seeds from geox_seismic_compute(mode='avo_forward')
              or geox_geomechanics (E, nu from vp, vs, rho).
    inverse   refines against field observations (Trishuli 2026-08-26).

DITEMPA BUKAN DIBERI — the cascade is forged, not given.
"""
from __future__ import annotations

import math
import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("geox.glof_cascade")


# ──────────────────────────────────────────────────────────────── Request models
class GLOFCascadeInitRequest(BaseModel):
    domain_bounds_x_m: float = Field(default=4000.0, description="Horizontal extent [m]")
    domain_bounds_z_m: float = Field(default=600.0, description="Vertical extent [m]")
    resolution_m: float = Field(default=10.0, description="Cell size [m]")
    dam_height_m: float = Field(default=150.0, description="Dam crest elevation [m]")
    water_head_initial_m: float = Field(default=0.0, description="Initial lake level [m]")
    use_seismic_priors: bool = Field(default=True,
                                     description="Seed from existing geox_geomechanics if state provided")
    # ── 33D state input (zen-33 architecture, GEOX LEWM) ──
    initial_state_33: Optional[dict] = Field(
        default=None,
        description="Full GEOXEarthState33 dict (33 scalars: M9 + P9 + W9 + X6). "
                    "If None, defaults to himalayan_glof_33().")
    panel_focus: Optional[str] = Field(
        default="all",
        description="Which panel to focus mutation: M | P | W | X | all")


class GLOFCascadeStepRequest(BaseModel):
    state_id: str = Field(..., description="ID returned from initialize")
    n_steps: int = Field(default=10, description="Timesteps to advance")
    dt_sec: float = Field(default=1.0, description="Time step [s]")
    boundary_conditions: dict = Field(default_factory=dict,
                                       description="{north: 'inflow', south: 'open', ...}")


class GLOFCascadePhaseRequest(BaseModel):
    state_id: str
    cell_id: str
    sigma_n: float = Field(..., description="Normal stress [Pa]")
    tau_applied: float = Field(..., description="Applied shear [Pa]")
    velocity: float = Field(default=0.0, description="Flow velocity [m/s]")
    sigma_applied: float = Field(default=0.0, description="Tensile stress [Pa]")
    saturation: Optional[float] = Field(default=None, description="Water saturation 0..1")


class GLOFCascadeInverseRequest(BaseModel):
    observation: dict = Field(..., description="GLOFObservation dict: {water_head_m, Q_peak, t_peak, surge}")
    base_theta: Optional[dict] = Field(default=None,
                                       description="Seed theta dict (9 fields) — defaults to himalayan_defaults")
    n_grid: int = Field(default=4, description="Grid resolution per dimension")


class GLOFCascadeMetabolizeRequest(BaseModel):
    cycle_id: str = Field(default="", description="F-I-M cycle identifier")
    theta_hat: dict = Field(..., description="Inferred 9-field theta dict")
    forward_prediction: dict = Field(..., description="Forward sim output")
    observation: dict = Field(..., description="Field observation dict")


class GLOFCascadeResponse(BaseModel):
    ok: bool
    tool: str
    result: dict
    error: str = ""


# ──────────────────────────────────────────────────────────────── Tool registry
class _StateRegistry:
    """In-memory state store — keyed by state_id.

    For production, this should be backed by Redis / Postgres.
    """
    def __init__(self):
        self._states: dict[str, "GLOFSimSession"] = {}

    def put(self, state_id: str, session) -> None:
        self._states[state_id] = session

    def get(self, state_id: str):
        return self._states.get(state_id)


REGISTRY = _StateRegistry()


class GLOFSimSession:
    """One simulation session: state + history.

    Holds BOTH:
        - self.material     : legacy GLOFMaterialState (9 geomech scalars, M panel)
        - self.state_33     : full GEOXEarthState33 (33 scalars, zen-33 architecture)

    The 33D state is the canonical source-of-truth. The legacy 9-field
    material is exposed for backward-compat with the previous GLOF
    pipeline (glgeomaterial.py + glphase_switcher.py + gl_forward_inverse_loop.py).
    """
    def __init__(self, init_req: GLOFCascadeInitRequest):
        from geox_core.physics.glgeomaterial import (
            himalayan_defaults, GLOFMaterialState,
        )
        from geox_core.physics.gl33 import (
            GEOXEarthState33, himalayan_glof_33,
        )
        self.init_req = init_req
        self.material = himalayan_defaults()  # legacy M slice
        self.history: list[dict] = []
        self.state_id = f"glof33_{init_req.dict().get('domain_bounds_x_m', 0):.0f}_{id(self)}"
        self.cycle_count = 0
        # Zen-33 canonical state
        if init_req.initial_state_33:
            try:
                self.state_33 = GEOXEarthState33(**init_req.initial_state_33)
            except Exception:
                self.state_33 = himalayan_glof_33()
        else:
            self.state_33 = himalayan_glof_33()
        # Cell grid
        nx = int(init_req.domain_bounds_x_m / init_req.resolution_m)
        nz = int(init_req.domain_bounds_z_m / init_req.resolution_m)
        self.grid_shape = (nx, nz)

    def snapshot(self) -> dict:
        return {
            "state_id": self.state_id,
            "material": self.material.to_dict(),
            "state_33": self.state_33.to_dict(),
            "history_len": len(self.history),
            "cycle_count": self.cycle_count,
            "grid_shape": list(self.grid_shape),
        }


# ──────────────────────────────────────────────────────────────── Tools
async def geox_glof_cascade_initialize(
    request: GLOFCascadeInitRequest,
) -> GLOFCascadeResponse:
    """Initialize a GLOF cascade simulation session.

    Optional seismic coupling: if use_seismic_priors=True, caller should
    also pass base_theta dict from geox_geomechanics(state_dict) to seed
    rho, E, nu via existing Physics13State.
    """
    try:
        s = GLOFSimSession(request)
        REGISTRY.put(s.state_id, s)
        return GLOFCascadeResponse(
            ok=True,
            tool="geox_glof_cascade_initialize",
            result={"snapshot": s.snapshot()},
        )
    except Exception as e:
        return GLOFCascadeResponse(
            ok=False,
            tool="geox_glof_cascade_initialize",
            result={},
            error=str(e),
        )


async def geox_glof_cascade_step(
    request: GLOFCascadeStepRequest,
) -> GLOFCascadeResponse:
    """Advance simulation by n_steps timesteps; record phase transitions."""
    from geox_core.physics.gl_forward_inverse_loop import forward_glof
    from dataclasses import replace

    s = REGISTRY.get(request.state_id)
    if s is None:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_step", result={},
            error=f"state_id {request.state_id} not found",
        )
    try:
        # Use forward_glof with current material; scale steps by dt
        result = forward_glof(
            s.material,
            water_head_m=s.init_req.water_head_initial_m,
            dam_height_m=s.init_req.dam_height_m,
            dt_sec=request.dt_sec,
            n_steps=request.n_steps,
        )
        # NEW: advance 33D state via metabolize_33 (zen-33 closure)
        from geox_core.physics.gl33 import metabolize_33, forward_kinematics
        from dataclasses import replace as dc_replace
        # Advance 33D state n_steps times (1 metabolize per step)
        s33 = s.state_33
        for _ in range(request.n_steps):
            s33 = dc_replace(s33, Pp=s33.Pp + 1000.0 * request.dt_sec)
            s33 = metabolize_33(s33)
        s.state_33 = s33
        # Append summarized step to history
        s.history.append({
            "n_steps": request.n_steps,
            "dt_sec": request.dt_sec,
            "breach_step": result.get("breach_step"),
            "Q_peak": result.get("Q_peak_m3s"),
            "phase_series_unique": sorted(set(result["phase_series"])),
            "phase_id_33_after": s33.phase_id,
        })
        s.cycle_count += 1
        # 33D forward observation (derived W from new M,P)
        w33 = forward_kinematics(s33)
        return GLOFCascadeResponse(
            ok=True,
            tool="geox_glof_cascade_step",
            result={
                "snapshot": s.snapshot(),
                "step_summary": {
                    "breach_time_min": result.get("breach_time_min"),
                    "Q_peak_m3s": result.get("Q_peak_m3s"),
                    "time_to_peak_min": result.get("time_to_peak_min"),
                    "downstream_surge_m_est": result.get("downstream_surge_m_est"),
                    "phase_final": result["phase_series"][-1] if result["phase_series"] else "unknown",
                },
                # zen-33 outputs
                "state_33": s33.to_dict(),
                "W_derived": {
                    "Vp_m_s": round(w33["Vp"], 2),
                    "Vs_m_s": round(w33["Vs"], 2),
                    "alpha_B": round(w33["alpha_B"], 4),
                },
                "panel_focus": s.init_req.panel_focus,
            },
        )
    except Exception as e:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_step", result={}, error=str(e),
        )


async def geox_glof_cascade_phase(
    request: GLOFCascadePhaseRequest,
) -> GLOFCascadeResponse:
    """Evaluate yield surfaces for one cell at given loads.

    Operates on BOTH the legacy GLOFMaterialState (M slice) and the
    full 33D state (M + P + W + X). Yield verdict is returned alongside
    the 33D-derived stress tensor and breach probability.
    """
    from geox_core.physics.glphase_switcher import evaluate_cascade

    s = REGISTRY.get(request.state_id)
    if s is None:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_phase", result={},
            error=f"state_id {request.state_id} not found",
        )
    try:
        v = evaluate_cascade(
            s.material,
            sigma_n=request.sigma_n,
            tau_applied=request.tau_applied,
            velocity=request.velocity,
            sigma_applied=request.sigma_applied,
            saturation=request.saturation,
        )
        # 33D-derived breach risk via Terzaghi + Mohr-Coulomb
        s33 = s.state_33
        sigma_eff_33 = s33.rho * s33.g * 100.0 - s33.alpha_B * s33.Pp
        tau_max_33 = s33.c + max(sigma_eff_33, 0.0) * math.tan(max(s33.phi_angle, 1e-3))
        breach_prob_33 = max(0.0, min(1.0,
            request.tau_applied / max(tau_max_33, 1.0)))
        # Hydro-fracture indicator: tensile stress vs sigma_t
        hydro_fracture = (
            request.sigma_applied > s33.sigma_t if request.sigma_applied > 0 else False
        )
        return GLOFCascadeResponse(
            ok=True,
            tool="geox_glof_cascade_phase",
            result={
                "cell_id": request.cell_id,
                # Legacy 9-property verdict
                "current_phase": v.current_phase.value,
                "next_phase": v.next_phase.value,
                "failure_mode": v.failure_mode,
                "margin": round(v.margin, 4),
                "fails": v.fails,
                "transitions": v.transitions,
                "fracture_K": round(v.fracture_K, 2),
                # 33D zen breach assessment
                "state_33_breach": {
                    "sigma_eff_Pa": round(sigma_eff_33, 2),
                    "tau_max_Pa": round(tau_max_33, 2),
                    "breach_probability_33D": round(breach_prob_33, 4),
                    "hydro_fracture": hydro_fracture,
                    "panel_focus": s.init_req.panel_focus,
                },
            },
        )
    except Exception as e:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_phase", result={}, error=str(e),
        )


async def geox_glof_cascade_inverse(
    request: GLOFCascadeInverseRequest,
) -> GLOFCascadeResponse:
    """Bayesian grid-search inference of dam parameters from observations."""
    from geox_core.physics.gl_forward_inverse_loop import (
        inverse_infer, GLOFObservation,
    )
    from geox_core.physics.glgeomaterial import (
        himalayan_defaults, GLOFMaterialState,
    )

    try:
        obs = GLOFObservation(**request.observation)
        base = None
        if request.base_theta:
            base = GLOFMaterialState(**request.base_theta)
        else:
            base = himalayan_defaults()

        theta_hat, log_ll, posterior = inverse_infer(
            obs, base_theta=base, n_grid=request.n_grid,
        )
        return GLOFCascadeResponse(
            ok=True,
            tool="geox_glof_cascade_inverse",
            result={
                "theta_hat": theta_hat.to_dict(),
                "log_likelihood": round(log_ll, 4),
                "posterior_summary": posterior,
                "observation": obs.to_dict(),
            },
        )
    except Exception as e:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_inverse", result={}, error=str(e),
        )


async def geox_glof_cascade_metabolize(
    request: GLOFCascadeMetabolizeRequest,
) -> GLOFCascadeResponse:
    """Close the F-I-M loop — produce receipt with tri-witness G-score."""
    from geox_core.physics.gl_forward_inverse_loop import (
        metabolize as metabolize_fn, GLOFObservation,
    )
    from geox_core.physics.glgeomaterial import GLOFMaterialState, MaterialPhase

    try:
        # Reconstruct with phase_id coercion (dict -> Enum)
        theta_dict = dict(request.theta_hat)
        pid = theta_dict.get("phase_id", "unknown")
        if isinstance(pid, str):
            try:
                theta_dict["phase_id"] = MaterialPhase(pid)
            except ValueError:
                theta_dict["phase_id"] = MaterialPhase.UNKNOWN
        theta = GLOFMaterialState(**theta_dict)
        obs = GLOFObservation(**request.observation)
        receipt = metabolize_fn(
            cycle_id=request.cycle_id,
            theta_hat=theta,
            forward_pred=request.forward_prediction,
            obs=obs,
        )
        return GLOFCascadeResponse(
            ok=True,
            tool="geox_glof_cascade_metabolize",
            result={"receipt": receipt.to_dict()},
        )
    except Exception as e:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_metabolize", result={}, error=str(e),
        )


# ─────────────────────────────────────────────────────────────── Phase C tools
class GLOFCascadeMCMCRequest(BaseModel):
    """MCMC Bayesian posterior inference (Phase C)."""
    observation: dict = Field(..., description="GLOFObservation dict")
    base_theta: dict | None = Field(default=None, description="Initial 33D state (full)")
    n_warmup: int = Field(default=80, description="Adaptive warm-up iterations per chain")
    n_iter: int = Field(default=200, description="Production iterations per chain")
    n_chains: int = Field(default=2, description="Number of independent chains")
    seed: int = Field(default=42, description="RNG seed for reproducibility")


class GLOFCascadePropagateRequest(BaseModel):
    """Saint-Venant 1D propagation (Phase C)."""
    breach_Q_profile: str = Field(
        default="costa1985",
        description="Q(t) profile: 'costa1985' | 'instant' | 'linear_decay'"
    )
    length_m: float = Field(default=60_000.0, description="Reach length [m]")
    nx: int = Field(default=200, description="Cells along reach")
    manning_n: float = Field(default=0.05, description="Manning roughness")
    bed_slope: float = Field(default=0.01, description="Bed slope [-]")
    duration_s: float = Field(default=7200.0, description="Simulation time [s]")
    output_interval_s: float = Field(default=120.0, description="Snapshot interval [s]")


class GLOFCascadePropagateResponse(BaseModel):
    ok: bool
    tool: str
    result: dict
    error: str = ""


async def geox_glof_cascade_mcmc_inverse(
    request: GLOFCascadeMCMCRequest,
) -> GLOFCascadeResponse:
    """Phase C — proper Bayesian posterior via MCMC (replaces grid search)."""
    from geox_core.physics.gl_forward_inverse_loop import (
        mcmc_infer, GLOFObservation,
    )
    from geox_core.physics.glgeomaterial import GLOFMaterialState
    try:
        obs = GLOFObservation(**request.observation)
        base = None
        if request.base_theta:
            base = GLOFMaterialState(**request.base_theta)
        theta_hat, log_ll, posterior = mcmc_infer(
            obs, base,
            n_warmup=request.n_warmup,
            n_iter=request.n_iter,
            n_chains=request.n_chains,
            seed=request.seed,
        )
        return GLOFCascadeResponse(
            ok=True,
            tool="geox_glof_cascade_mcmc_inverse",
            result={
                "theta_hat": theta_hat.to_dict(),
                "log_likelihood": round(log_ll, 4),
                "posterior": posterior,
            },
        )
    except Exception as e:
        return GLOFCascadeResponse(
            ok=False, tool="geox_glof_cascade_mcmc_inverse", result={}, error=str(e),
        )


async def geox_glof_cascade_propagate(
    request: GLOFCascadePropagateRequest,
) -> GLOFCascadePropagateResponse:
    """Phase C — 1D Saint-Venant propagation from breach to downstream."""
    import math
    from geox_core.physics.gl_forward_inverse_loop import saint_venant_propagate

    def _q_costa(t: float, peak: float = 3000.0) -> float:
        if request.breach_Q_profile == "instant":
            return peak if t < 300 else peak * 0.1
        elif request.breach_Q_profile == "linear_decay":
            return peak * max(0.0, 1.0 - t / 3600.0)
        else:  # costa1985
            if t < 60:
                return peak * (t / 60.0)
            elif t < 720:
                return peak * math.exp(-(t - 60) / 300.0)
            else:
                return peak * math.exp(-(t - 60) / 1800.0)

    try:
        result = saint_venant_propagate(
            breach_Q_func=_q_costa,
            length_m=request.length_m,
            nx=request.nx,
            manning_n=request.manning_n,
            bed_slope=request.bed_slope,
            duration_s=request.duration_s,
            output_interval_s=request.output_interval_s,
        )
        return GLOFCascadePropagateResponse(
            ok=True,
            tool="geox_glof_cascade_propagate",
            result=result,
        )
    except Exception as e:
        return GLOFCascadePropagateResponse(
            ok=False, tool="geox_glof_cascade_propagate", result={},
            error=str(e),
        )


# ──────────────────────────────────────────────────────────────── Seismic coupling
async def geox_glof_cascade_seed_from_seismic(
    physics13_state_dict: dict,
    extras: dict,
) -> GLOFMaterialState:
    """Bridge existing Physics13State -> GLOFMaterialState (E, nu derived).

    Use case: caller has run geox_seismic_compute(mode='avo_forward') to
    get vp/vs/rho, then geox_geomechanics(state_dict) for E/nu, then
    passes result here along with GLOF-specific extras (c, phi, k,
    tau_0, sigma_t) to seed a cascade simulation.

    F9 ANTI-HANTU: caller MUST supply the 5 GLOF extras (c, phi, k,
    tau_0, sigma_t). Petrophysical state alone is insufficient.
    """
    from geox_core.physics.glgeomaterial import from_physics13_state
    from geox_core.physics.state import Physics13State

    p = Physics13State.from_raw_dict(physics13_state_dict)
    return from_physics13_state(p, **extras)


# ──────────────────────────────────────────────────────────────── Smoke test
if __name__ == "__main__":
    import asyncio

    async def main():
        # 1. Init
        init = GLOFCascadeInitRequest()
        r = await geox_glof_cascade_initialize(init)
        state_id = r.result["snapshot"]["state_id"]
        print(f"[1] init ok={r.ok} state_id={state_id}")

        # 2. Phase check at cell bhotekoshi_dam
        ph = GLOFCascadePhaseRequest(
            state_id=state_id, cell_id="dam_crest",
            sigma_n=500e3, tau_applied=80e3, saturation=0.1,
        )
        r = await geox_glof_cascade_phase(ph)
        print(f"[2] phase margin={r.result.get('margin'):+.3f} "
              f"mode={r.result.get('failure_mode')}")

        # 3. Inverse inference
        obs = {
            "label": "Trishuli_test",
            "water_head_m": 110.0,
            "breach_width_m": 150.0,
            "peak_discharge_m3s": 3000.0,
            "time_to_peak_min": 12.0,
            "downstream_surge_m": 9.0,
            "source": "gauge",
        }
        inv = GLOFCascadeInverseRequest(observation=obs, n_grid=3)
        r = await geox_glof_cascade_inverse(inv)
        theta_hat = r.result["theta_hat"]
        print(f"[3] inverse c={theta_hat['c']:.0f} phi={math.degrees(theta_hat['phi']):.1f}deg "
              f"ll={r.result['log_likelihood']:.2f}")

        # 4. Metabolize
        fwd_pred = {"Q_peak_m3s": 3000.0, "time_to_peak_min": 12.0, "downstream_surge_m_est": 9.0}
        met = GLOFCascadeMetabolizeRequest(
            cycle_id="c1", theta_hat=theta_hat,
            forward_prediction=fwd_pred, observation=obs,
        )
        r = await geox_glof_cascade_metabolize(met)
        rec = r.result["receipt"]
        print(f"[4] metabolize G={rec['G_score']:.3f} ll={rec['log_likelihood']:.2f}")

    asyncio.run(main())