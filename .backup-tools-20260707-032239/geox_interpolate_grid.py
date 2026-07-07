"""
geox_interpolate_grid — Biharmonic Grid Inpainting MCP Tool
════════════════════════════════════════════════════════════
CARD 001 of AAA-GEOX-ADAPT-CARDS-2026-06-27.

Inpaints sparse/null cells in 2D geological grids using biharmonic (4th-order
PDE) interpolation. Synthesises a smooth surface from scattered control points
(well tops, formation markers, seismic horizon picks) while respecting boundary
conditions.

Boundary: geox_core.engines.modeling.biharmonic_adapter

MCP naming: geox_interpolate_grid
F2: uncertainty = distance-decay from nearest control point
F7: confidence decays to 0 beyond CONF_MAX_KM (50 km)
F9: algorithm interpolates — does NOT "know" geology
F11: input_hash + params_hash in every result envelope

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from fastmcp import FastMCP

from geox_core.engines.modeling.biharmonic_adapter import (
    BiharmonicResult,
    biharmonic_inpaint_grid,
)

logger = logging.getLogger("geox.interpolate_grid")

# ── MCP Server (add to server.py mount list) ────────────────────────────────
mcp = FastMCP("geox_interpolate_grid")


@mcp.tool()
def geox_interpolate_grid(
    grid_data: list[list[float]],
    nodata_value: float | None = None,
    anisotropic_weights: tuple[float, float] | None = None,
    decay_km: float = 50.0,
) -> dict[str, Any]:
    """Inpaint missing data in a 2D geological grid using biharmonic PDE.

    Biharmonic interpolation solves the 4th-order PDE ∇⁴φ = 0, producing
    a smooth surface that respects boundary conditions — preferred over
    linear or cubic interpolation for geological surfaces where discontinuities
    (faults, unconformities) should be honoured.

    Use cases:
      - Seismic horizon gap-filling (fault shadow, processing mute zones)
      - Formation top map completion between well control
      - Gravity/magnetic grid inpainting (survey flight-line gaps)
      - Any 2D property grid with sparse null cells

    Parameters
    ----------
    grid_data : list of list of float
        2D array as nested list. NaN or nodata_value marks missing cells.
        Maximum size: 2048 × 2048 (4,194,304 cells).
    nodata_value : float, optional
        Explicit no-data marker. If None, NaN is assumed.
    anisotropic_weights : (x_weight, y_weight), optional
        Anisotropy weights for geological fabric direction.
        e.g. (1.0, 3.0) slows variation in Y (e.g., bedding dip direction).
    decay_km : float
        Confidence decay half-distance in km. Default 50 km.
        At distance = decay_km from any control point, confidence ≈ 0.37.

    Returns
    -------
    dict
        geox.biharmonic.v1 envelope:
        {
          "grid": [[...]],           # inpainted 2D array (list of list)
          "confidence": [[...]],      # 0-1 confidence map
          "nodata_mask": [[...]],     # original null cells (bool)
          "epistemic_label": str,    # "DERIVED" | "INTERPRETED_LOCAL"
          "metrics": {
            "nulls_filled": int,
            "known_cells": int,
            "grid_shape": [int, int],
            "compute_time_ms": float,
            "input_hash": str,
            "params_hash": str,
            "mean_confidence_at_holes": float,
            "algorithm": "biharmonic_PDE"
          },
          "provenance": {
            "version": str,
            "algorithm": str,
            "input_hash": str,
            "params_hash": str
          }
        }

    Raises
    ------
    ValueError: Grid exceeds 2048×2048, empty, or all nodata.
    RuntimeError: Inpainting algorithm failed.

    Examples
    --------
    >>> import numpy as np
    >>> grid = np.full((100, 100), np.nan)
    >>> grid[10:30, 10:30] = 1.0   # control patch
    >>> grid[60:80, 60:80] = 2.0   # another control patch
    >>> result = geox_interpolate_grid(grid.tolist(), decay_km=10.0)
    >>> result["epistemic_label"]
    "DERIVED"
    >>> result["metrics"]["nulls_filled"]
    9600
    """
    logger.info(
        "geox_interpolate_grid: shape=%s nodata=%s decay_km=%.1f",
        f"{len(grid_data)}×{len(grid_data[0]) if grid_data else 0}",
        nodata_value,
        decay_km,
    )

    # ── Invoke core engine ────────────────────────────────────────────────
    try:
        result: BiharmonicResult = biharmonic_inpaint_grid(
            grid_data=grid_data,
            nodata_value=nodata_value,
            anisotropic_weights=anisotropic_weights,
            decay_km=decay_km,
        )
    except ValueError as exc:
        logger.warning("geox_interpolate_grid validation error: %s", exc)
        raise

    # ── Serialise to dict (MCP JSON must be primitive types) ────────────
    return {
        "grid": result.grid.tolist(),
        "confidence": result.confidence.tolist(),
        "nodata_mask": result.nodata_mask.tolist(),
        "epistemic_label": result.epistemic_label,
        "metrics": result.metrics,
        "provenance": result.provenance,
        # Canonical envelope (Appendix B of GEOX constitution)
        "geox.biharmonic.v1": {
            "envelope_type": "biharmonic_inpaint",
            "tool": "geox_interpolate_grid",
            "version": "2026.06.29",
            "f2_uncertainty_note": (
                "confidence = exp(-d/d_half) from nearest known cell; label DERIVED if mean_conf > 0.6 else INTERPRETED_LOCAL"
            ),
            "f7_humility_note": (
                f"decay_km={decay_km} — beyond {decay_km} km from any "
                "control point, confidence → 0; surface is interpolated, "
                "not geology"
            ),
        },
    }
