"""gl_saint_venant.py — 1D Saint-Venant shallow-water equations for GLOF wave propagation.

System (conservation form):
    ∂h/∂t + ∂(hu)/∂x = 0           (mass)
    ∂(hu)/∂t + ∂(hu² + ½gh²)/∂x = g h (S_0 - S_f)   (momentum)

Where:
    h = flow depth (m)
    u = depth-averaged velocity (m/s)
    S_0 = bed slope (-)
    S_f = friction slope (Manning-Strickler): S_f = n² u² / R_h^(4/3) ≈ n² u² / h^(4/3)
    g = gravity (9.81 m/s²)

Numerical scheme: Lax-Friedrichs (1st-order, monotone, conservative).
Simple but stable for dam-break-like flows. CFL condition:
    dt <= dx / (|u| + sqrt(g*h))

Boundary conditions (dam-break scenario):
    upstream (x=0): prescribed discharge Q_in(t) from breach model
    downstream (x=L): zero-gradient (transmissive)

Initial conditions: h(x,0) = h_initial(x), u(x,0) = Q_initial(x) / h_initial(x)

Output: time series of (x, t, u) for downstream surge tracking.

DITEMPA BUKAN DIBERI — Saint-Venant is the canonical shallow-water model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np


@dataclass
class SVDomain:
    """Spatial domain + discretization."""
    length_m: float = 60_000.0       # 60 km reach
    nx: int = 200                     # cells
    manning_n: float = 0.05           # gravel/boulder bed
    bed_slope: float = 0.01           # 1% slope (Himalayan V-shape)
    g: float = 9.81

    @property
    def dx(self) -> float:
        return self.length_m / self.nx


@dataclass
class SVResult:
    """Time-series result from Saint-Venant simulation."""
    x: np.ndarray                            # (nx,) cell centers [m]
    t: np.ndarray                            # (nt,) output times [s]
    h: np.ndarray = field(default=None)      # (nt, nx) depth [m]
    u: np.ndarray = field(default=None)      # (nt, nx) velocity [m/s]
    Q: np.ndarray = field(default=None)      # (nt, nx) discharge [m³/s]
    cfl: float = 0.0
    n_steps: int = 0


def cfl_timestep(h: np.ndarray, u: np.ndarray, dx: float, g: float) -> float:
    """Max stable dt under CFL: dt <= dx / (|u| + c) where c = sqrt(g*h)."""
    c = np.sqrt(np.maximum(g * h, 1e-6))
    max_speed = float(np.max(np.abs(u) + c))
    if max_speed <= 0:
        return float("inf")
    return dx / max_speed


def saint_venant_step(
    h: np.ndarray,
    u: np.ndarray,
    domain: SVDomain,
    dt: float,
    Q_in: float,
) -> tuple:
    """One Lax-Friedrichs timestep of Saint-Venant.

    Args:
        h: (nx,) depth at cell centers.
        u: (nx,) velocity at cell centers.
        domain: Spatial setup.
        dt: Timestep (must satisfy CFL).
        Q_in: Upstream discharge (prescribed BC at x=0).

    Returns:
        h_new, u_new: updated state.
    """
    nx = domain.nx
    dx = domain.dx
    g = domain.g

    # Compute fluxes F = (hu, hu² + ½gh²)
    hu = h * u
    F_mass = hu
    F_mom = hu * u + 0.5 * g * h * h

    # Lax-Friedrichs: numerical flux = 0.5*(F_L + F_R) - 0.5*(dx/dt)*(U_R - U_L)
    # State U = (h, hu)
    U = np.stack([h, hu], axis=1)  # (nx, 2)

    # Upstream BC: cell 0 gets prescribed discharge
    h[0] = max(h[0], 0.1)
    u[0] = Q_in / max(h[0], 0.1)
    hu[0] = h[0] * u[0]

    # Compute flux differences
    F = np.stack([F_mass, F_mom], axis=1)  # (nx, 2)
    # Lax-Friedrichs flux
    flux_L = F[:-1, :]    # F at left of each interface (nx-1, 2)
    flux_R = F[1:, :]     # F at right (nx-1, 2)
    U_L = U[:-1, :]
    U_R = U[1:, :]

    # Maximum wave speed at each interface (for numerical diffusion)
    h_L = h[:-1]
    h_R = h[1:]
    c_L = np.sqrt(np.maximum(g * h_L, 1e-6))
    c_R = np.sqrt(np.maximum(g * h_R, 1e-6))
    u_L = u[:-1]
    u_R = u[1:]
    max_speed = np.maximum(np.abs(u_L) + c_L, np.abs(u_R) + c_R)

    # Numerical flux
    F_num = 0.5 * (flux_L + flux_R) - 0.5 * (max_speed[:, None]) * (U_R - U_L)

    # Update (upwind for interior, BC for boundaries)
    h_new = h.copy()
    u_new = u.copy()
    hu_new = hu.copy()

    # Update interior cells (excluding BCs)
    # Source term: g * h * (S_0 - S_f)
    # Use Manning friction: S_f = n² |u| u / h^(4/3)
    S_f = domain.manning_n ** 2 * np.abs(u) * u / np.maximum(h, 0.1) ** (4.0 / 3.0)
    S_0 = domain.bed_slope
    src = g * h * (S_0 - S_f)

    # Interior update (cells 1..nx-2)
    h_new[1:-1] = h[1:-1] - dt / dx * (F_num[1:, 0] - F_num[:-1, 0])
    hu_new[1:-1] = hu[1:-1] - dt / dx * (F_num[1:, 1] - F_num[:-1, 1]) + dt * src[1:-1]
    u_new[1:-1] = hu_new[1:-1] / np.maximum(h_new[1:-1], 0.1)

    # Upstream BC (prescribed discharge)
    h_new[0] = max(h_new[1], 0.1)  # transmissive
    u_new[0] = Q_in / max(h_new[0], 0.1)
    hu_new[0] = h_new[0] * u_new[0]

    # Downstream BC (transmissive / zero-gradient)
    h_new[-1] = h_new[-2]
    u_new[-1] = u_new[-2]
    hu_new[-1] = h_new[-1] * u_new[-1]

    return h_new, u_new


def simulate_glof_propagation(
    breach_Q_func: Callable[[float], float],
    domain: SVDomain,
    duration_s: float = 7200.0,       # 2 hours
    output_interval_s: float = 60.0,  # output every minute
    h_initial: float = 1.0,           # base flow depth
    Q_initial: float = 5.0,           # base flow discharge (mild)
) -> SVResult:
    """Run Saint-Venant 1D for GLOF propagation.

    Args:
        breach_Q_func: Function Q(t) returning upstream discharge at time t (s).
                       Real implementation: Q(t) from breach model (Costa 1985).
        domain: SVDomain with length, nx, slope, manning, g.
        duration_s: Total simulation time.
        output_interval_s: How often to snapshot state.
        h_initial: Initial depth along domain.
        Q_initial: Initial discharge.

    Returns:
        SVResult with x, t, h, u, Q arrays.
    """
    nx = domain.nx
    dx = domain.dx
    x = np.linspace(dx / 2, domain.length_m - dx / 2, nx)

    # Initial state: low flow everywhere (clamp u to be small)
    h = np.full(nx, max(h_initial, 0.5))
    u_base = Q_initial / max(h_initial, 0.5)  # ~5 m/s for Q=5, h=1
    u = np.full(nx, min(u_base, 2.0))  # cap initial velocity for stability

    # Output buffer
    n_outputs = int(duration_s / output_interval_s) + 1
    t_out = np.zeros(n_outputs)
    h_out = np.zeros((n_outputs, nx))
    u_out = np.zeros((n_outputs, nx))

    # Initial state at t=0
    t_out[0] = 0.0
    h_out[0, :] = h
    u_out[0, :] = u

    # CFL timestep — be conservative (CFL number 0.4)
    max_cfl_dt = cfl_timestep(h, u, dx, domain.g)
    dt = min(0.4 * max_cfl_dt, output_interval_s / 20)
    if not np.isfinite(dt) or dt <= 0:
        dt = 1.0

    # Time loop
    t = 0.0
    out_idx = 1
    step_count = 0
    max_cfl_seen = 0.0

    while t < duration_s:
        Q_in = breach_Q_func(t)
        # Sanitize: clip Q to physically plausible for a GLOF (1-5000 m³/s)
        Q_in = min(max(Q_in, 0.0), 5000.0)
        h, u = saint_venant_step(h, u, domain, dt, Q_in)
        # Sanitize state after step
        h = np.nan_to_num(h, nan=1.0, posinf=10.0, neginf=0.1)
        u = np.nan_to_num(u, nan=0.0, posinf=20.0, neginf=-20.0)
        # Floor depth
        h = np.maximum(h, 0.1)
        # Cap velocity
        u = np.clip(u, -30.0, 30.0)

        t += dt
        step_count += 1

        # CFL diagnostic (record, but don't blow up if NaN)
        try:
            cfl_now = dt * float(np.max(np.abs(u) + np.sqrt(np.maximum(domain.g * h, 1e-6)))) / dx
            if np.isfinite(cfl_now):
                max_cfl_seen = max(max_cfl_seen, cfl_now)
        except (ValueError, RuntimeWarning):
            pass

        # Re-adapt dt for CFL (every 10 steps)
        if step_count % 10 == 0:
            try:
                max_cfl_dt = cfl_timestep(h, u, dx, domain.g)
                if np.isfinite(max_cfl_dt) and max_cfl_dt > 0:
                    dt = min(0.4 * max_cfl_dt, output_interval_s / 20)
            except (ValueError, RuntimeWarning):
                pass

        # Snapshot
        if out_idx < n_outputs and t >= out_idx * output_interval_s:
            t_out[out_idx] = t
            h_out[out_idx, :] = h
            u_out[out_idx, :] = u
            out_idx += 1

    # Trim outputs to actual written count
    return SVResult(
        x=x,
        t=t_out[:out_idx],
        h=h_out[:out_idx],
        u=u_out[:out_idx],
        Q=h_out[:out_idx] * u_out[:out_idx],
        cfl=max_cfl_seen,
        n_steps=step_count,
    )


if __name__ == "__main__":
    # Smoke test: Costa 1985 breach Q(t) profile, 60 km reach
    def Q_breach(t_s: float) -> float:
        """Peak Q at 12 min = 720 s, exponential decay."""
        if t_s < 60:        # ramp-up 0–60 s
            return 3000.0 * (t_s / 60.0)
        elif t_s < 720:    # ramp-down 60–720 s
            return 3000.0 * math.exp(-(t_s - 60) / 300.0)
        else:
            return 3000.0 * math.exp(-(t_s - 60) / 1800.0)  # long tail

    domain = SVDomain(length_m=60_000.0, nx=200, manning_n=0.05,
                      bed_slope=0.01, g=9.81)
    print(f"Running Saint-Venant 1D for {domain.length_m/1000:.0f} km reach, "
          f"{domain.nx} cells, g={domain.g}...")

    result = simulate_glof_propagation(
        breach_Q_func=Q_breach, domain=domain,
        duration_s=7200.0, output_interval_s=120.0,
    )
    print(f"  n_steps = {result.n_steps}, CFL max = {result.cfl:.2f}")
    print(f"  snapshots = {len(result.t)} (every 2 min)")
    print(f"  max depth at downstream (x=L): {result.h[:, -1].max():.2f} m")
    print(f"  max velocity at downstream:    {result.u[:, -1].max():.2f} m/s")
    print(f"  max Q at downstream:            {result.Q[:, -1].max():.0f} m³/s")
    print(f"  time of peak downstream (s):    "
          f"{result.t[np.argmax(result.Q[:, -1])]:.0f}")