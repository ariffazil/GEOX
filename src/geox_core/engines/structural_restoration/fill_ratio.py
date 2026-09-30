"""compute_fill_ratio — Sediment fill ratio with diagnostic guard.

SR_INV-005: thickness ≠ accommodation ≠ subsidence.
SR_INV-006: Division requires positive denominator above tolerance.
SR_INV-007: fill_ratio > 1 triggers DIAGNOSTIC_REVIEW, never FAULT_ACTIVITY_CONFIRMED.
TECT-001: This is an observation, not an explanation.

fill_ratio = sediment_thickness / accommodation

Classification:
  < 0        → INVALID (sign convention error)
  0 – ~1     → Underfilled to filled
  ~ 1        → Approximately filled
  > 1        → ANOMALY (diagnostic checklist required)

Forged: 2026-09-14
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .state import RestorationScenario

# Numerical tolerance for denominator (SR_INV-006)
_DENOMINATOR_TOLERANCE = 1e-6


def compute_fill_ratio(
    scenario: RestorationScenario,
    thickness_grid: NDArray[np.float64],
    accommodation_grid: NDArray[np.float64],
) -> dict[str, Any]:
    """Compute fill ratio with diagnostic guard.

    Parameters
    ----------
    scenario : RestorationScenario
        Validated restoration scenario.
    thickness_grid : NDArray
        Sediment thickness grid (metres, must be >= 0).
    accommodation_grid : NDArray
        Accommodation grid from compute_accommodation (metres).

    Returns
    -------
    dict with:
        fill_ratio_grid: NDArray
        classification_grid: NDArray[str] (VALID/NEGATIVE/ANOMALY_GT1/INVALID_DENOMINATOR)
        invalid_mask: NDArray[bool]
        anomaly_mask: NDArray[bool] (fill_ratio > 1)
        negative_mask: NDArray[bool] (fill_ratio < 0)
        zero_denominator_mask: NDArray[bool]
        diagnostic_checklist: dict (FILL_RATIO_GT1_CHECKLIST if anomaly found)
        equation: str
        scenario_id: str
    """
    if thickness_grid.shape != accommodation_grid.shape:
        raise ValueError(
            f"Grid shape mismatch: thickness {thickness_grid.shape} "
            f"vs accommodation {accommodation_grid.shape}"
        )

    # SR_INV-001: never mutate inputs
    thick = np.array(thickness_grid, dtype=np.float64)
    accom = np.array(accommodation_grid, dtype=np.float64)

    # Build masks
    invalid_input = ~np.isfinite(thick) | ~np.isfinite(accom)
    zero_denom = (np.abs(accom) < _DENOMINATOR_TOLERANCE) & ~invalid_input
    valid_denom = ~invalid_input & ~zero_denom

    # Compute ratio (only where denominator is valid)
    ratio = np.full_like(thick, np.nan)
    ratio[valid_denom] = thick[valid_denom] / accom[valid_denom]

    # Classify
    classification = np.full(thick.shape, "INVALID_INPUT", dtype="U32")
    classification[valid_denom] = "VALID"
    classification[zero_denom] = "INVALID_DENOMINATOR"
    classification[invalid_input] = "INVALID_INPUT"

    # Anomaly: fill_ratio > 1 (SR_INV-007)
    anomaly_mask = np.zeros(thick.shape, dtype=bool)
    anomaly_mask[valid_denom] = ratio[valid_denom] > 1.0
    classification[anomaly_mask] = "ANOMALY_GT1"

    # Negative: fill_ratio < 0
    negative_mask = np.zeros(thick.shape, dtype=bool)
    negative_mask[valid_denom] = ratio[valid_denom] < 0.0
    classification[negative_mask] = "NEGATIVE"

    # Approximately filled: 0.95 –1.05
    approx_filled = np.zeros(thick.shape, dtype=bool)
    approx_filled[valid_denom] = (ratio[valid_denom] >= 0.95) & (ratio[valid_denom] <= 1.05)
    classification[approx_filled & ~anomaly_mask & ~negative_mask] = "APPROXIMATELY_FILLED"

    # Statistics
    valid_ratio = ratio[valid_denom]
    stats: dict[str, Any] = {}
    if valid_ratio.size > 0:
        stats = {
            "mean": float(np.nanmean(valid_ratio)),
            "median": float(np.nanmedian(valid_ratio)),
            "min": float(np.nanmin(valid_ratio)),
            "max": float(np.nanmax(valid_ratio)),
            "std": float(np.nanstd(valid_ratio)),
            "n_valid": int(valid_ratio.size),
            "n_anomaly_gt1": int(np.sum(anomaly_mask)),
            "n_negative": int(np.sum(negative_mask)),
            "n_invalid_denom": int(np.sum(zero_denom)),
            "n_approximately_filled": int(np.sum(approx_filled)),
        }

    # SR_INV-007: diagnostic checklist for anomalies
    has_anomaly = bool(np.any(anomaly_mask))
    diagnostic: dict[str, Any] = {}
    if has_anomaly:
        diagnostic = {
            "status": "PENDING_DIAGNOSTIC",
            "anomaly_type": "fill_ratio_gt_1",
            "n_anomalous_cells": int(np.sum(anomaly_mask)),
            "checklist": [
                {
                    "cause": "reversed_subtraction_order",
                    "priority": 1,
                    "test": "Verify sign convention and subtraction order",
                },
                {
                    "cause": "inconsistent_restoration_ages",
                    "priority": 2,
                    "test": "Verify ages of both states are correct and consistent",
                },
                {
                    "cause": "mismatched_surface_extents",
                    "priority": 3,
                    "test": "Verify both surfaces cover the same geographic area",
                },
                {
                    "cause": "unit_or_datum_mismatch",
                    "priority": 4,
                    "test": "Verify CRS, XY units, Z units, datum, polarity match",
                },
                {
                    "cause": "erosion_or_hiatus",
                    "priority": 5,
                    "test": "Check for unconformity or erosion between states",
                },
                {
                    "cause": "compaction_model_mismatch",
                    "priority": 6,
                    "test": "Verify compaction curve is appropriate for lithology/depth",
                },
                {
                    "cause": "interpolation_artefact",
                    "priority": 7,
                    "test": "Check grid interpolation method and cell size",
                },
                {
                    "cause": "missing_structural_displacement",
                    "priority": 8,
                    "test": "Check for faults not represented in restoration",
                },
                {
                    "cause": "inappropriate_facies_or_lithology",
                    "priority": 9,
                    "test": "Verify lithology assignment for depositional setting",
                },
                {
                    "cause": "fault_activity",
                    "priority": 10,
                    "test": "ONLY after ALL above excluded. Requires independent structural evidence.",
                },
            ],
            "note": (
                "SR_INV-007: fill_ratio > 1 triggers DIAGNOSTIC_REVIEW. "
                "It NEVER returns FAULT_ACTIVITY_CONFIRMED without "
                "independent structural evidence."
            ),
        }

    return {
        "fill_ratio_grid": ratio,
        "classification_grid": classification,
        "invalid_mask": invalid_input,
        "anomaly_mask": anomaly_mask,
        "negative_mask": negative_mask,
        "zero_denominator_mask": zero_denom,
        "diagnostic_checklist": diagnostic,
        "equation": "fill_ratio = sediment_thickness / accommodation",
        "scenario_id": scenario.scenario_id,
        "statistics": stats,
        "verdict": "SEAL" if not has_anomaly else "DIAGNOSTIC_REVIEW",
    }


__all__ = ["compute_fill_ratio"]
