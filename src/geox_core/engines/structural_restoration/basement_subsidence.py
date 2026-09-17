"""compute_basement_subsidence — State differencing for basement subsidence.

SR_INV-005: Subsidence ≠ accommodation ≠ thickness.
TECT-003: Subsidence is an effect, not a cause.
TECT-011: Basement may contain multiple histories.

basement_subsidence = basement_position(state_t1) - basement_position(state_t0)

Guardrails:
- Basement surface must represent the same geological boundary in both states.
- Report tectonic subsidence separately from stratigraphic accommodation.

Forged: 2026-09-14
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .state import RestorationScenario


def compute_basement_subsidence(
    scenario: RestorationScenario,
    basement_source_grid: NDArray[np.float64],
    basement_target_grid: NDArray[np.float64],
) -> dict[str, Any]:
    """Compute basement subsidence by state differencing.

    Parameters
    ----------
    scenario : RestorationScenario
        Validated restoration scenario.
    basement_source_grid : NDArray
        Basement surface in source state (metres).
    basement_target_grid : NDArray
        Basement surface in target state (metres).

    Returns
    -------
    dict with:
        subsidence_grid: NDArray
        invalid_mask: NDArray[bool]
        uplift_mask: NDArray[bool]
        equation: str
        units: str
        scenario_id: str
        basement_boundary_check: dict
    """
    if basement_source_grid.shape != basement_target_grid.shape:
        raise ValueError(
            f"Basement grid shape mismatch: source {basement_source_grid.shape} "
            f"vs target {basement_target_grid.shape}"
        )

    # SR_INV-001: never mutate inputs
    src = np.array(basement_source_grid, dtype=np.float64)
    tgt = np.array(basement_target_grid, dtype=np.float64)

    # Convention: subsidence = target(older) - source(younger)
    # positive = basement moved down (subsidence)
    if scenario.source_age_ma < scenario.target_age_ma:
        subsidence = tgt - src
        subtraction_order = f"target({scenario.target_age_ma}Ma) - source({scenario.source_age_ma}Ma)"
    else:
        subsidence = src - tgt
        subtraction_order = f"source({scenario.source_age_ma}Ma) - target({scenario.target_age_ma}Ma)"

    # Masks
    invalid_mask = ~np.isfinite(src) | ~np.isfinite(tgt)
    uplift_mask = (subsidence < 0) & ~invalid_mask

    subsidence_out = subsidence.copy()
    subsidence_out[invalid_mask] = np.nan

    valid = subsidence_out[~invalid_mask]
    stats: dict[str, Any] = {}
    if valid.size > 0:
        stats = {
            "mean_subsidence_m": float(np.nanmean(valid)),
            "max_subsidence_m": float(np.nanmax(valid)),
            "max_uplift_m": float(np.nanmin(valid)),
            "std_m": float(np.nanstd(valid)),
            "n_valid": int(valid.size),
            "n_uplift": int(np.sum(uplift_mask)),
            "n_invalid": int(np.sum(invalid_mask)),
        }

    # TECT-011: basement heterogeneity warning
    basement_check = {
        "source_surface_id": scenario.basement_source.surface_id if scenario.basement_source else None,
        "target_surface_id": scenario.basement_target.surface_id if scenario.basement_target else None,
        "warning": (
            "TECT-011: One basement horizon ≠ one geological event. "
            "The basement surface may represent multiple elements "
            "(stretched crust, inherited blocks, igneous additions). "
            "Verify basement homogeneity before interpreting subsidence."
        ),
        "same_boundary_check": (
            scenario.basement_source.surface_id == scenario.basement_target.surface_id
            if scenario.basement_source and scenario.basement_target
            else "UNKNOWN"
        ),
    }

    return {
        "subsidence_grid": subsidence_out,
        "invalid_mask": invalid_mask,
        "uplift_mask": uplift_mask,
        "subtraction_order": subtraction_order,
        "equation": "subsidence = older_state - younger_state (positive = downward movement)",
        "units": scenario.crs_proof.z_units if scenario.crs_proof else "m",
        "scenario_id": scenario.scenario_id,
        "basement_boundary_check": basement_check,
        "statistics": stats,
        "verdict": "SEAL" if not np.any(invalid_mask) else "PARTIAL",
    }


__all__ = ["compute_basement_subsidence"]
