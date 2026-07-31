"""
restoration_bridge.py — Petrophysics↔Restoration causal loop (G9)

The bridge that the 30 July audit correctly identified as the bottleneck:
    geox_petrophysics → EarthStateVector → geox_basin_backstrip → 
    geox_thermal_maturity → EarthStateVector (enriched) → geox_prospect

This module provides the translation layer that allows tools to share
petrophysical state through the EarthStateVector, closing the
"causal connectivity" gap.

DITEMPA BUKAN DIBERI — 2026-07-31
"""
from __future__ import annotations

from typing import Any
from geox_core.physics.earth_state_vector import PetrophysicalEarthStateVector


def prepare_backstrip_input(
    esv: PetrophysicalEarthStateVector,
) -> dict[str, Any]:
    """Convert EarthStateVector to geox_basin_backstrip input parameters.
    
    The restoration loop: measured porosity from petrophysics feeds into
    burial history reconstruction, which predicts expected porosity at
    maximum burial depth. The residual (measured - predicted) reveals
    diagenetic overprint.
    """
    if esv.porosity is None:
        return {"error": "EarthStateVector missing porosity — run petrophysics first"}
    
    return {
        "current_porosity": esv.porosity,
        "current_depth_m": esv.depth_base_m,
        "matrix_density_gcc": esv.matrix_density_gcc or 2.65,
        "pore_pressure_mpa": esv.pore_pressure_mpa,
        "temperature_c": esv.temperature_c,
        "lithology": esv.dominant_mineral or "sandstone",
        "sw": esv.sw,
        "well_id": esv.well_id,
        "basin": esv.basin,
        "source": "petrophysics_restoration_bridge",
    }


def compute_porosity_residual(
    measured_phi: float,
    predicted_phi: float,
    depth_m: float,
) -> dict[str, Any]:
    """Compare measured vs predicted porosity at depth.
    
    Residual > 0: porosity higher than burial predicts → secondary porosity / undercompaction.
    Residual < 0: porosity lower than burial predicts → cementation / overcompaction.
    Residual ≈ 0: porosity explained by burial alone.
    """
    residual = measured_phi - predicted_phi
    
    if abs(residual) < 0.02:
        interpretation = "burial_consistent — porosity explained by compaction"
        flag = "NORMAL"
    elif residual > 0.05:
        interpretation = "secondary_porosity or undercompaction — higher than burial predicts"
        flag = "ANOMALY_HIGH_PHI"
    elif residual < -0.03:
        interpretation = "cementation or overcompaction — lower than burial predicts"
        flag = "ANOMALY_LOW_PHI"
    else:
        interpretation = "minor_deviation — within calibration uncertainty"
        flag = "MINOR"
    
    return {
        "measured_phi": round(measured_phi, 4),
        "predicted_phi": round(predicted_phi, 4),
        "residual": round(residual, 4),
        "depth_m": depth_m,
        "interpretation": interpretation,
        "flag": flag,
        "recommendation": _recommend_from_residual(flag),
    }


def _recommend_from_residual(flag: str) -> str:
    if flag == "ANOMALY_HIGH_PHI":
        return "Investigate secondary porosity mechanisms: dissolution, fracturing, undercompaction"
    elif flag == "ANOMALY_LOW_PHI":
        return "Investigate porosity-reducing processes: quartz cementation, carbonate cementation, compaction"
    return "Proceed with standard burial model"


def enrich_earth_state_vector_with_burial(
    esv: PetrophysicalEarthStateVector,
    backstrip_result: dict[str, Any],
) -> PetrophysicalEarthStateVector:
    """Enrich ESV with burial history results from backstrip analysis."""
    esv.max_burial_depth_m = backstrip_result.get("max_burial_depth_m")
    esv.subsidence_rate_mm_yr = backstrip_result.get("subsidence_rate_mm_yr")
    esv.tectonic_subsidence_m = backstrip_result.get("tectonic_subsidence_m")
    esv.provenance["burial"] = "geox_basin_backstrip"
    esv.confidence["burial"] = backstrip_result.get("confidence", "MEDIUM")
    return esv


def enrich_earth_state_vector_with_thermal(
    esv: PetrophysicalEarthStateVector,
    thermal_result: dict[str, Any],
) -> PetrophysicalEarthStateVector:
    """Enrich ESV with thermal maturity results."""
    esv.vitrinite_reflectance_ro = thermal_result.get("ro")
    esv.tmax_c = thermal_result.get("tmax_c")
    esv.tti = thermal_result.get("tti")
    esv.maturity_zone = thermal_result.get("maturity_zone")
    esv.provenance["thermal"] = "geox_thermal_maturity_history"
    esv.confidence["thermal"] = thermal_result.get("confidence", "MEDIUM")
    return esv
