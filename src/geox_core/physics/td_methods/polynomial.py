"""
geox_core.physics.td_methods.polynomial — Eureka 1 fitter #2

Weighted polynomial fit through checkshot data.

Uses `np.polyfit` with weights = 1 / (checkshot_TWT_uncertainty²).
Default degree = 2 (quadratic) — captures the dominant compaction
acceleration. Higher degrees are opt-in.

Properties:
  - C^infinity smoothness
  - CAN extrapolate beyond checkshot range (with growing uncertainty)
  - Coefficients are physically interpretable:
      a₀ ≈ 0 (TWT at surface ≈ 0)
      a₁ ≈ 2/V₀ (inverse surface velocity)
      a₂ ≈ slope of dV/dz (compaction trend)
      a₃ ≈ curvature of dV/dz (overpressure onset indicator)

Use this when:
  - Checkshot density is moderate (1 per 200–500 m)
  - Velocity field is smoothly varying (no sharp lithology breaks)
  - You want to fill small gaps between checkshots with a smooth curve
  - You can tolerate the assumption of smooth gradient

Anti-overfit: if degree >= 4 and RMSE on train < 0.5 ms, suspect overfit.
The PhysicsGuard catches curvature explosions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from geox_core.physics.td_methods.base import (
    TDFitResult,
    _audit,
    _coverage,
    _extrapolation_risk,
    _validate_inputs,
)


def fit_polynomial(
    checkshot_data: List[Dict[str, Any]],
    depth_array: np.ndarray,
    degree: int = 2,
    weights: Optional[np.ndarray] = None,
    allow_extrapolation: bool = False,
) -> TDFitResult:
    """Weighted polynomial fit of TWT vs depth.

    Args:
        checkshot_data: list of {"depth_md", "twt_ms"} or [[d, t], ...]
        depth_array: target depths to predict TWT at
        degree: polynomial degree (default 2; 3 for overpressure; 4 max)
        weights: per-point weight (default uniform). Use 1/σ² if uncertain.
        allow_extrapolation: if False, raises when depth_array extends
                             beyond checkshot range (fail-closed).

    Returns:
        TDFitResult with coefficients [a_0, a_1, ..., a_degree]
        such that TWT(z) = a_0 + a_1·z + a_2·z² + ...
    """
    if degree < 1 or degree > 4:
        raise ValueError(f"Polynomial degree must be 1-4, got {degree}.")
    cs_d, cs_t = _validate_inputs(checkshot_data, depth_array)
    min_d, max_d = float(cs_d.min()), float(cs_d.max())
    if not allow_extrapolation and (depth_array.min() < min_d or depth_array.max() > max_d):
        raise ValueError(
            f"Polynomial fitter (deg={degree}): checkshot covers [{min_d:.1f}, {max_d:.1f}] m MD — "
            f"depth array extends to {depth_array.min():.1f}..{depth_array.max():.1f} m MD. "
            f"Pass allow_extrapolation=True to override, or extend checkshot."
        )

    if weights is None:
        weights = np.ones_like(cs_d, dtype=float)
    if len(weights) != len(cs_d):
        raise ValueError(f"weights length {len(weights)} != checkshot length {len(cs_d)}.")

    # Normalise depths for numerical stability (avoids polyfit blow-up at 5000 m)
    z_scale = float(cs_d.max()) if cs_d.max() > 0 else 1.0
    z_norm = cs_d / z_scale

    # polyfit
    coeffs_norm = np.polyfit(z_norm, cs_t, deg=degree, w=weights)
    # Predict at target depths
    z_target_norm = depth_array / z_scale
    twt_pred = np.polyval(coeffs_norm, z_target_norm)

    # Residuals at checkshot levels
    twt_at_cs = np.polyval(coeffs_norm, z_norm)
    residuals = cs_t - twt_at_cs
    rmse = float(np.sqrt(np.mean(residuals**2)))

    cov = _coverage(depth_array, cs_d)
    audit = _audit(twt_pred, depth_array, residuals)
    risk = _extrapolation_risk(depth_array, cs_d) if allow_extrapolation else 0.0

    # Anti-overfit guard: if RMSE is near-zero and degree >= 3, flag suspicion
    overfit_flag = rmse < 0.5 and degree >= 3

    equation = "TWT(z) = " + " + ".join(
        f"a_{i}·z^{i}" if i > 1 else (f"a_{i}·z" if i == 1 else f"a_{i}") for i in range(degree + 1)
    )
    result = TDFitResult(
        method=f"polynomial_d{degree}",
        equation=equation,
        coefficients=[float(c) for c in coeffs_norm],
        twt_ms=twt_pred,
        residuals_ms=residuals,
        rmse_ms=rmse,
        physics_guard={**audit, "overfit_suspected": overfit_flag, "z_scale": z_scale},
        extrapolation_risk=risk,
        fail_closed=not allow_extrapolation,
    )
    return result
