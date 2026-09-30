"""compute_accommodation_space — State differencing for accommodation.

SR_INV-005: Accommodation ≠ subsidence ≠ thickness.
TECT-001: Output is an observation, not an explanation.
TECT-002: Accommodation is an effect, not a cause.

This is STATE DIFFERENCING: subtract two restoration states to get
accommodation grid. NOT a forward physics simulation.

accommodation = elevation(restored_depositional_state)
              - elevation(reference_state)

Sign depends on Z convention — recorded in output.

Forged: 2026-09-14
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .state import RestorationScenario, ZConvention


def compute_accommodation(
    scenario: RestorationScenario,
    source_grid: NDArray[np.float64],
    target_grid: NDArray[np.float64],
) -> dict[str, Any]:
    """Compute accommodation by state differencing.

    Parameters
    ----------
    scenario : RestorationScenario
        Validated restoration scenario (must pass validate_restoration_inputs).
    source_grid : NDArray
        Present-day or source state elevation grid (metres).
    target_grid : NDArray
        Restored or target state elevation grid (metres).

    Returns
    -------
    dict with:
        accommodation_grid: NDArray (same shape as inputs)
        invalid_mask: NDArray[bool] (cells where computation is invalid)
        negative_mask: NDArray[bool] (cells with negative accommodation)
        subtraction_order: str
        sign_convention: str
        equation: str
        units: str
        scenario_id: str
        source_lineage: dict
        uncertainty_ref: dict
    """
    # SR_INV-003: verify shapes match
    if source_grid.shape != target_grid.shape:
        raise ValueError(
            f"Grid shape mismatch: source {source_grid.shape} vs "
            f"target {target_grid.shape}. SR_INV-003 violated."
        )

    # SR_INV-001: never mutate inputs
    src = np.array(source_grid, dtype=np.float64)
    tgt = np.array(target_grid, dtype=np.float64)

    # Determine subtraction order based on age
    # Convention: accommodation = younger_state - older_state
    # (positive = space created)
    if scenario.source_age_ma < scenario.target_age_ma:
        # Source is younger (present day), target is older (restored)
        # accommodation = present - restored (positive = space above restored surface)
        accommodation = src - tgt
        subtraction_order = f"source({scenario.source_age_ma}Ma) - target({scenario.target_age_ma}Ma)"
    else:
        accommodation = tgt - src
        subtraction_order = f"target({scenario.target_age_ma}Ma) - source({scenario.source_age_ma}Ma)"

    # Build masks
    # Invalid: NaN or inf in either input
    invalid_mask = ~np.isfinite(src) | ~np.isfinite(tgt)
    # Negative: accommodation < 0 (possible erosion or uplift)
    negative_mask = (accommodation < 0) & ~invalid_mask

    # Apply masks — invalid cells get NaN
    accommodation_out = accommodation.copy()
    accommodation_out[invalid_mask] = np.nan

    # Statistics (excluding invalid)
    valid = accommodation_out[~invalid_mask]
    stats: dict[str, Any] = {}
    if valid.size > 0:
        stats = {
            "mean_m": float(np.nanmean(valid)),
            "min_m": float(np.nannanmin(valid)),
            "max_m": float(np.nannanmax(valid)),
            "std_m": float(np.nanstd(valid)),
            "n_valid": int(valid.size),
            "n_negative": int(np.sum(negative_mask)),
            "n_invalid": int(np.sum(invalid_mask)),
            "negative_fraction": float(np.sum(negative_mask) / valid.size),
        }

    # SR_INV-002: lineage
    source_lineage = {
        "source_surface_id": scenario.source_state.surface_id,
        "source_surface_hash": scenario.source_state.hash,
        "target_surface_id": scenario.target_state.surface_id,
        "target_surface_hash": scenario.target_state.hash,
        "scenario_id": scenario.scenario_id,
    }

    # SR_INV-013: uncertainty reference
    uncertainty_ref = {
        "numerical": scenario.uncertainty.numerical if scenario.uncertainty else {},
        "spatial": scenario.uncertainty.spatial if scenario.uncertainty else {},
        "compaction": scenario.uncertainty.compaction if scenario.uncertainty else {},
    }

    # Z convention
    z_conv = scenario.crs_proof.z_convention.value if scenario.crs_proof else "positive_down"

    return {
        "accommodation_grid": accommodation_out,
        "invalid_mask": invalid_mask,
        "negative_mask": negative_mask,
        "subtraction_order": subtraction_order,
        "sign_convention": z_conv,
        "equation": "accommodation = younger_state - older_state (positive = space created)",
        "units": scenario.crs_proof.z_units if scenario.crs_proof else "m",
        "scenario_id": scenario.scenario_id,
        "source_lineage": source_lineage,
        "uncertainty_ref": uncertainty_ref,
        "statistics": stats,
        "verdict": "SEAL" if not np.any(invalid_mask) else "PARTIAL",
    }


__all__ = ["compute_accommodation"]
