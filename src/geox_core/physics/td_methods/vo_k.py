"""
geox_core.physics.td_methods.vo_k — Eureka 1 fitter #3

Vo-Keystone velocity model: V(z) = V₀ + k·z (linear compaction)
or
                         V(z) = V₀·exp(k·z) (exponential compaction)

TWT(z) = ∫ 2/V(z) dz

Linear compaction:
  TWT(z) = 2/k · ln(1 + k·z/V₀)

Exponential compaction:
  TWT(z) = 2/(V₀·k) · (1 - exp(-k·z))

This is the geologically-motivated fitter: it assumes velocity increases
with depth (compaction), with the rate parameter k. Fits in 2-3 seconds
on a 10k-sample grid.

Properties:
  - Closed-form TWT(z) (no numerical integration needed)
  - 2 free parameters (V₀, k) — stable inversion
  - Extrapolates gracefully (deeper than deepest checkshot still physical)
  - Fails to fit velocity inversions (overpressure) by design

Use this when:
  - Basin is in normal compaction regime (no major overpressure)
  - You have 3+ checkshot points spanning the section
  - You want a smooth, geologically-anchored T-D curve
  - Regional exploration (sparse well control)

Cannot fit:
  - Velocity inversions (overpressure, low-velocity zones) → use layer_cake
  - Salt bodies (sharp velocity contrast) → use layer_cake
"""

from __future__ import annotations

from typing import Any

import numpy as np

from geox_core.physics.td_methods.base import (
    TDFitResult,
    _audit,
    _coverage,
    _extrapolation_risk,
    _validate_inputs,
)


def fit_vo_k(
    checkshot_data: list[dict[str, Any]],
    depth_array: np.ndarray,
    mode: str = "linear",
    v0_init: float = 1800.0,
    k_init: float = 0.0006,
    allow_extrapolation: bool = True,
) -> TDFitResult:
    """Vo-Keystone velocity model fit.

    Args:
        checkshot_data: list of {"depth_md", "twt_ms"} or [[d, t], ...]
        depth_array: target depths to predict TWT at
        mode: "linear" (V = V₀ + k·z) or "exponential" (V = V₀·exp(k·z))
        v0_init: initial guess for V₀ (m/s)
        k_init: initial guess for k (1/m)
        allow_extrapolation: Vo-K naturally extrapolates; default True
    """
    if mode not in ("linear", "exponential"):
        raise ValueError(f"Vo-K mode must be 'linear' or 'exponential', got {mode}.")
    cs_d, cs_t = _validate_inputs(checkshot_data, depth_array)
    min_d, max_d = float(cs_d.min()), float(cs_d.max())
    if depth_array.min() < min_d or depth_array.max() > max_d:
        if not allow_extrapolation:
            raise ValueError(
                "Vo-K fitter: depth array outside checkshot range. Pass allow_extrapolation=True (recommended for Vo-K)."
            )

    # Initial V_avg per checkshot point
    vavg_obs = 2.0 * cs_d / np.where(cs_t > 0, cs_t, 1e-9) / 1000.0  # ms → s
    vavg_obs = np.clip(vavg_obs, 1500, 6000)  # CANON-9 guard

    if mode == "linear":
        # V = V₀ + k·z  →  fit vavg_obs = V₀ + k·cs_d
        A = np.vstack([np.ones_like(cs_d), cs_d]).T
        params, *_ = np.linalg.lstsq(A, vavg_obs, rcond=None)
        V0, k = float(params[0]), float(params[1])
        if k < 0:
            k = abs(k)  # force positive compaction (warn if not?)
        # TWT(z) = 2/k · ln(1 + k·z/V₀)
        if k < 1e-9:
            # Degenerate: k≈0 → constant velocity → TWT = 2z/V₀
            twt_pred = 2.0 * depth_array / max(V0, 1500) * 1000.0
        else:
            twt_pred = (2.0 / k) * np.log(1.0 + k * depth_array / max(V0, 1500)) * 1000.0
        # At checkshot
        twt_at_cs = (2.0 / k) * np.log(1.0 + k * cs_d / max(V0, 1500)) * 1000.0
        equation = f"TWT(z) = (2/{k:.4e})·ln(1 + {k:.4e}·z/{V0:.1f}) × 1000   [linear Vo-K, V₀={V0:.1f} m/s, k={k:.4e} 1/m]"
        coeffs = [V0, k]
    else:  # exponential
        # V = V₀·exp(k·z)  →  ln(vavg_obs) = ln(V₀) + k·cs_d
        ln_v = np.log(np.clip(vavg_obs, 1500, 6000))
        A = np.vstack([np.ones_like(cs_d), cs_d]).T
        params, *_ = np.linalg.lstsq(A, ln_v, rcond=None)
        lnV0, k = float(params[0]), float(params[1])
        V0 = float(np.exp(lnV0))
        if k < 0:
            k = abs(k)
        # TWT(z) = 2/(V₀·k)·(1 - exp(-k·z))
        if k < 1e-9:
            twt_pred = 2.0 * depth_array / max(V0, 1500) * 1000.0
        else:
            twt_pred = (2.0 / (max(V0, 1500) * k)) * (1.0 - np.exp(-k * depth_array)) * 1000.0
        twt_at_cs = (2.0 / (max(V0, 1500) * k)) * (1.0 - np.exp(-k * cs_d)) * 1000.0
        equation = (
            f"TWT(z) = (2/({V0:.1f}·{k:.4e}))·(1 - exp(-{k:.4e}·z)) × 1000   [exponential Vo-K, V₀={V0:.1f} m/s, k={k:.4e} 1/m]"
        )
        coeffs = [V0, k]

    residuals = cs_t - twt_at_cs
    rmse = float(np.sqrt(np.mean(residuals**2)))
    _coverage(depth_array, cs_d)
    audit = _audit(twt_pred, depth_array, residuals)
    risk = _extrapolation_risk(depth_array, cs_d) if allow_extrapolation else 0.0

    return TDFitResult(
        method=f"vo_k_{mode}",
        equation=equation,
        coefficients=coeffs,
        twt_ms=twt_pred,
        residuals_ms=residuals,
        rmse_ms=rmse,
        physics_guard={**audit, "vo_k_mode": mode, "V0": float(coeffs[0]), "k": float(coeffs[1])},
        extrapolation_risk=risk,
        fail_closed=not allow_extrapolation,
    )
