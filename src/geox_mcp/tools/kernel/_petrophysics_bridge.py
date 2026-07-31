"""
_petrophysics_bridge.py — Petrophysics ↔ Restoration Causal Closure Bridge
═══════════════════════════════════════════════════════════════════════════════

B1: Petrophysics → Burial History  (_build_burial_path_from_stratigraphy)
B2: Burial → Predicted Porosity     (_predict_porosity_forward)
B3: Backstrip → Validation          (_compare_measured_vs_predicted)
B4: Petrophysics → Geomechanics     (_compute_sv_from_density_log)

DITEMPA BUKAN DIBERI — Forged, Not Given.
Phase 1 (Scientific Closure): B1 + B2 + B3
Phase 2 (Physics State):        B4 + EarthStateVector

Physics:
  Athy (1930):           φ(z) = φ₀ · exp(-c·z)
  Sclater & Christie (1980):  decompaction from backstrip engine
  Steckler & Watts (1978):    tectonic subsidence
  Zoback (2010):              stress polygon from density integration

References:
  - Athy, L.F. (1930) Density, porosity, and compaction of sedimentary rocks.
  - Sclater, J.G. & Christie, P.A.F. (1980) Continental stretching.
  - Allen, P.A. & Allen, J.R. (2013) Basin Analysis.
"""

from __future__ import annotations

import math
import os
from typing import Any

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
# B1 — Petrophysics → Burial History
# ═══════════════════════════════════════════════════════════════════════════════


def _build_burial_path_from_stratigraphy(
    depth_m: list[float],
    stratigraphic_tops: list[dict[str, Any]],
) -> dict[str, Any]:
    """Convert LAS depth array + stratigraphic tops into burial history dict.

    Each stratigraphic top must have:
      - top_depth_m:    present-day depth of formation top (m)
      - age_ma:         geological age of the top (Ma, 0 = present)
      - lithology:      lithology name (sandstone, shale, etc.)

    Returns a burial_history dict compatible with geox_thermal_maturity_history:
      {ages_ma: [...], depths_m: [...]}

    Physics: burial depth at time t = present-day depth - (uplift since t)
    For a non-uplifted basin: burial(t) = depth of horizon of age t

    DER — Derived from stratigraphic interpretation. Not a direct measurement.
    """
    if not stratigraphic_tops or len(stratigraphic_tops) < 1:
        return {"error": "NO_STRATIGRAPHIC_TOPS", "recoverable": True}

    # Sort tops by age (oldest first = deepest)
    sorted_tops = sorted(stratigraphic_tops, key=lambda t: t.get("age_ma", 0), reverse=True)

    ages_ma: list[float] = []
    depths_burial_m: list[float] = []

    # For each top, the burial at that time is the present-day depth
    # of the horizon deposited at that age.
    # This is a first-order approximation assuming no uplift/exhumation.
    for top in sorted_tops:
        age = top.get("age_ma", 0.0)
        depth = top.get("top_depth_m", 0.0)

        # Burial depth cannot be negative for a depositional surface
        if depth < 0:
            depth = 0.0

        ages_ma.append(age)
        depths_burial_m.append(depth)

    # Add present-day seafloor (age 0, depth 0) if not already present
    if not ages_ma or min(ages_ma) > 0.01:
        ages_ma.insert(0, 0.0)
        depths_burial_m.insert(0, 0.0)

    lithologies = [t.get("lithology", "sandstone") for t in sorted_tops]

    return {
        "ages_ma": ages_ma,
        "depths_m": depths_burial_m,
        "lithologies": lithologies,
        "n_tops": len(sorted_tops),
        "method": "stratigraphic_age_depth_conversion",
        "assumptions": [
            "No uplift/exhumation — burial depth at time t equals present-day depth of horizon aged t",
            "Continuous deposition between tops",
            "Stratigraphic ages are chronostratigraphically calibrated",
        ],
        "epistemic_label": "DER",
        "recoverable": True,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# B2 — Burial → Predicted Porosity (Forward Compaction Model)
# ═══════════════════════════════════════════════════════════════════════════════

# Lithology porosity-depth parameters (from Sclater & Christie 1980 / Allen & Allen 2013)
# φ(z) = φ₀ · exp(-c · z)
_POROSITY_PARAMS: dict[str, dict[str, float]] = {
    "sandstone": {"phi0": 0.49, "c": 0.27e-3, "rho_grain": 2650.0},
    "shale": {"phi0": 0.63, "c": 0.51e-3, "rho_grain": 2720.0},
    "mudstone": {"phi0": 0.55, "c": 0.39e-3, "rho_grain": 2700.0},
    "siltstone": {"phi0": 0.50, "c": 0.32e-3, "rho_grain": 2680.0},
    "limestone": {"phi0": 0.40, "c": 0.22e-3, "rho_grain": 2710.0},
    "dolomite": {"phi0": 0.20, "c": 0.12e-3, "rho_grain": 2850.0},
    "chalk": {"phi0": 0.70, "c": 0.40e-3, "rho_grain": 2710.0},
    "marl": {"phi0": 0.55, "c": 0.35e-3, "rho_grain": 2700.0},
    "evaporite": {"phi0": 0.10, "c": 0.05e-3, "rho_grain": 2900.0},
    "conglomerate": {"phi0": 0.35, "c": 0.20e-3, "rho_grain": 2650.0},
    "volcanic_ash": {"phi0": 0.60, "c": 0.45e-3, "rho_grain": 2600.0},
}


def _predict_porosity_forward(
    burial_history: dict[str, Any],
    lithology: str = "sandstone",
    present_depth_m: float | None = None,
) -> dict[str, Any]:
    """Forward-compact: predict present-day porosity from burial history.

    Uses Athy (1930) exponential porosity-depth law:
      φ(z) = φ₀ · exp(-c · z)

    For each burial step, computes the porosity at that depth.
    The present-day predicted porosity is from the deepest burial step.

    Args:
        burial_history: {ages_ma: [...], depths_m: [...]} — from B1 or manual
        lithology:       lithology name (default: sandstone)
        present_depth_m: override present-day depth (if different from max burial)

    Returns:
        {predicted_phi_fraction, phi_at_each_step, lithology_params, method}

    DER — Derived from forward compaction model. Not a direct measurement.
    """
    ages = burial_history.get("ages_ma", [])
    depths = burial_history.get("depths_m", [])

    if len(ages) != len(depths) or len(ages) < 1:
        return {
            "error": "INVALID_BURIAL_HISTORY",
            "detail": "ages_ma and depths_m arrays must match and contain ≥1 points",
            "recoverable": True,
        }

    # Resolve lithology parameters
    params = _POROSITY_PARAMS.get(lithology.lower(), _POROSITY_PARAMS["sandstone"])
    phi0 = params["phi0"]
    c = params["c"]

    # Use deepest point for present-day prediction unless overridden
    max_burial_idx = int(np.argmax(depths))
    max_burial_depth = depths[max_burial_idx]
    max_burial_age = ages[max_burial_idx]

    effective_depth = present_depth_m if present_depth_m is not None else max_burial_depth

    # Predict porosity at each burial step
    phi_at_step: list[dict[str, Any]] = []
    for age, depth in zip(ages, depths, strict=False):
        phi_pred = phi0 * math.exp(-c * depth)
        phi_at_step.append(
            {
                "age_ma": age,
                "depth_m": depth,
                "predicted_phi": round(phi_pred, 4),
            }
        )

    # Present-day predicted porosity
    phi_predicted = phi0 * math.exp(-c * effective_depth)

    return {
        "predicted_phi_fraction": round(phi_predicted, 4),
        "lithology": lithology,
        "phi0": phi0,
        "c_m_inv": c,
        "rho_grain_kg_m3": params["rho_grain"],
        "max_burial_depth_m": max_burial_depth,
        "max_burial_age_ma": max_burial_age,
        "effective_depth_m": effective_depth,
        "phi_at_each_step": phi_at_step,
        "method": "Athy_1930_forward_compaction",
        "equation": "φ(z) = φ₀ · exp(-c · z)",
        "reference": "Athy (1930) · Sclater & Christie (1980)",
        "caveat": (
            "Forward porosity prediction does not account for: "
            "uplift/exhumation, cementation, dissolution, overpressure, fracturing. "
            "Deviation between predicted and measured porosity is the PETROPHYSICAL ANOMALY "
            "that geology must explain."
        ),
        "epistemic_label": "DER",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# B3 — Compare Measured vs Predicted Porosity (The Scientific Closure)
# ═══════════════════════════════════════════════════════════════════════════════


def _compare_measured_vs_predicted(
    measured_phi_fraction: float,
    predicted_phi_fraction: float,
    measured_phi_p10: float | None = None,
    measured_phi_p90: float | None = None,
    measured_depth_m: float | None = None,
    lithology: str = "sandstone",
    burial_max_depth_m: float | None = None,
) -> dict[str, Any]:
    """Compare measured (from petrophysics) vs predicted (from burial) porosity.

    The residual Δφ = φ_measured - φ_predicted is the PETROPHYSICAL ANOMALY.

    Interpretation guide:
      |Δφ| < 0.02  → CONSISTENT (burial explains porosity)
      Δφ > +0.05   → ANOMALOUS_HIGH (requires uplift, fractures, leaching, dissolution)
      Δφ < -0.05   → ANOMALOUS_LOW  (requires extra compaction, cementation, overpressure)
      Δφ > +0.10   → CRITICAL_ANOMALY (strong secondary porosity or measurement error)

    NULL: no comparison made (0.0). INVERSE: swap predicted/measured roles.

    QQQ-3 compliant: enumerated paths + blast_radius + reversibility.
    """
    delta_phi = measured_phi_fraction - predicted_phi_fraction
    abs_delta = abs(delta_phi)

    # Classification thresholds
    if abs_delta < 0.02:
        anomaly_class = "CONSISTENT"
        interpretation = "Burial history adequately explains observed porosity."
        action = "No geological override required."
        blast_radius = 0  # benign — no structural revision needed
    elif abs_delta < 0.05:
        anomaly_class = "SLIGHT_DEVIATION"
        interpretation = "Minor deviation from burial prediction. Possible measurement error or minor diagenesis."
        action = "Review QC flags. Consider core calibration."
        blast_radius = 1
    elif abs_delta < 0.10:
        if delta_phi > 0:
            anomaly_class = "ANOMALOUS_HIGH"
            interpretation = (
                "Porosity significantly higher than burial prediction. "
                "Possible causes: uplift/exhumation, fracture porosity, leaching, "
                "dolomitisation, overpressure preservation, or measurement error."
            )
            action = (
                "Investigate: uplift history, fracture analysis, dissolution evidence. "
                "Review pressure data. Compare with regional porosity-depth trends."
            )
        else:
            anomaly_class = "ANOMALOUS_LOW"
            interpretation = (
                "Porosity significantly lower than burial prediction. "
                "Possible causes: extra compaction, cementation, overpressure collapse, "
                "or incorrect burial history."
            )
            action = (
                "Investigate: cement phases (thin section/SEM), burial history uncertainty, "
                "temperature history. Check if overpressure collapsed."
            )
        blast_radius = 2
    else:
        anomaly_class = "CRITICAL_ANOMALY"
        if delta_phi > 0:
            interpretation = (
                "Porosity critically higher than burial prediction. "
                "Strong secondary porosity — likely fractures, karst, or hydrothermal alteration. "
                "Verify measurement is not a washout/cycle skip."
            )
            action = (
                "URGENT: Check caliper for washouts. Verify porosity method. "
                "If real: this is a major geological story — fractures, dissolution, "
                "or the burial history is fundamentally wrong."
            )
        else:
            interpretation = (
                "Porosity critically lower than burial prediction. "
                "Possible measurement error (tight zone, bad density reading) "
                "or extreme diagenesis (quartz cementation, pressure solution)."
            )
            action = (
                "Verify log quality. If real: check for quartz overgrowths, "
                "stylolites, or authigenic clay. Burial history may need revision."
            )
        blast_radius = 3

    # Uncertainty propagation: does measured range contain predicted value?
    in_prediction_range = False
    if measured_phi_p10 is not None and measured_phi_p90 is not None:
        in_prediction_range = measured_phi_p10 <= predicted_phi_fraction <= measured_phi_p90

    return {
        "measured_phi": round(measured_phi_fraction, 4),
        "predicted_phi": round(predicted_phi_fraction, 4),
        "delta_phi": round(delta_phi, 4),
        "abs_delta_phi": round(abs_delta, 4),
        "anomaly_class": anomaly_class,
        "interpretation": interpretation,
        "action": action,
        "blast_radius": blast_radius,
        "in_prediction_range": in_prediction_range,
        "measured_phi_p10": measured_phi_p10,
        "measured_phi_p90": measured_phi_p90,
        "measured_depth_m": measured_depth_m,
        "lithology": lithology,
        "burial_max_depth_m": burial_max_depth_m,
        "method": "Athy_1930_forward_vs_measured",
        "epistemic_label": "DER",
        "qqq_note": (
            "Q1: 5 paths enumerated (CONSISTENT, SLIGHT, HIGH, LOW, CRITICAL). "
            "Q2: blast_radius {0-3}. Q3: observer effect — choosing a class "
            "may bias subsequent interpretation. Arif judges."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# B4 — Density Log Integration → Overburden Stress (Petrophysics → Geomechanics)
# ═══════════════════════════════════════════════════════════════════════════════


def _compute_sv_from_density_log(
    depth_m: list[float],
    rhob_g_cm3: list[float],
    water_depth_m: float = 0.0,
    water_density_kg_m3: float = 1025.0,
) -> dict[str, Any]:
    """Integrate RHOB density log to produce overburden stress profile.

    Sv(z) = g · ∫₀ᶻ ρ(z) dz

    This is the bridge from petrophysics to geomechanics (stress polygon).

    Args:
        depth_m:        depth array in metres (MD or TVD)
        rhob_g_cm3:     bulk density in g/cm³
        water_depth_m:  water depth for hydrostatic offset
        water_density_kg_m3: seawater density

    Returns:
        {sv_at_td_mpa, sv_profile: [(depth_m, sv_mpa)], avg_density_integrated, method}

    DER — Derived from density log integration. Not a direct measurement.
    """
    g = 9.81  # m/s²

    depth = np.asarray(depth_m, dtype=float)
    rhob = np.asarray(rhob_g_cm3, dtype=float) * 1000.0  # convert to kg/m³

    # Filter NaN
    valid = ~np.isnan(rhob) & ~np.isnan(depth) & (rhob > 500.0)  # density must be physical
    if valid.sum() < 2:
        return {
            "error": "INSUFFICIENT_VALID_DENSITY_SAMPLES",
            "detail": f"Only {int(valid.sum())} valid density samples after NaN filter",
            "recoverable": True,
        }

    depth_v = depth[valid]
    rhob_v = rhob[valid]

    # Sort by depth
    sort_idx = np.argsort(depth_v)
    depth_v = depth_v[sort_idx]
    rhob_v = rhob_v[sort_idx]

    # Trapezoidal integration
    dz = np.diff(depth_v)
    rho_avg = 0.5 * (rhob_v[:-1] + rhob_v[1:])
    sv_increments_pa = rho_avg * g * dz
    sv_cumulative_pa = np.cumsum(sv_increments_pa)
    sv_cumulative_mpa = sv_cumulative_pa / 1e6

    # Hydrostatic water column offset
    water_sv_pa = water_depth_m * water_density_kg_m3 * g
    water_sv_mpa = water_sv_pa / 1e6

    # Build Sv profile
    sv_profile: list[dict[str, float]] = []
    # Add water column point
    if water_depth_m > 0:
        sv_profile.append({"depth_m": 0.0, "sv_mpa": 0.0})
        sv_profile.append({"depth_m": round(float(water_depth_m), 1), "sv_mpa": round(water_sv_mpa, 3)})

    for i in range(len(sv_cumulative_mpa)):
        d = round(float(depth_v[i + 1]), 1)  # depth_v[i+1] is the depth at end of interval
        sv = round(float(sv_cumulative_mpa[i] + water_sv_mpa), 3)
        sv_profile.append({"depth_m": d, "sv_mpa": sv})

    sv_at_td = sv_cumulative_mpa[-1] + water_sv_mpa if len(sv_cumulative_mpa) > 0 else water_sv_mpa

    # Average integrated density (from Sv at TD)
    total_depth = depth_v[-1] - depth_v[0]
    avg_density = (sv_at_td * 1e6) / (g * (total_depth + water_depth_m)) if total_depth > 0 else water_density_kg_m3

    return {
        "sv_at_td_mpa": round(float(sv_at_td), 3),
        "water_depth_m": water_depth_m,
        "water_sv_offset_mpa": round(water_sv_mpa, 3),
        "total_depth_m": round(float(depth_v[-1]), 1),
        "avg_integrated_density_kg_m3": round(float(avg_density), 1),
        "n_valid_samples": int(valid.sum()),
        "sv_profile": sv_profile[:50],  # limit profile points for serialization
        "sv_profile_truncated": len(sv_profile) > 50,
        "method": "density_log_trapezoidal_integration",
        "equation": "Sv(z) = g · ∫₀ᶻ ρ(z) dz",
        "reference": "Zoback (2010) Reservoir Geomechanics",
        "caveat": "Integration assumes TVD. For deviated wells, use TVD depth channel.",
        "epistemic_label": "DER",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# X3 — Multi-Mineral Solver (Chemistry9 — constrained linear inversion)
# ═══════════════════════════════════════════════════════════════════════════════

# Mineral response matrix for log-based multi-mineral inversion.
# Rows: log measurements (RHOB, NPHI, GR, DT)
# Columns: mineral end-members
# Values from _mineral_catalog.py


def _get_mineral_response_matrix(
    mineral_names: list[str],
) -> tuple[np.ndarray, list[str], dict[str, float]]:
    """Build the system matrix A for multi-mineral inversion.

    Args:
        mineral_names: list of mineral names to include (e.g. ['quartz', 'calcite', 'clay'])

    Returns:
        (A_matrix, ordered_columns, mineral_properties_dict)
        A_matrix shape: (n_responses, n_minerals + 1) — last column is fluid (porosity)
    """
    from geox_mcp.tools.kernel._mineral_catalog import get_mineral

    # Response ordering: RHOB, NPHI, GR, DT
    A_rows = 4  # number of log responses
    A_cols = len(mineral_names) + 1  # +1 for fluid (porosity)

    A = np.zeros((A_rows, A_cols))

    for j, name in enumerate(mineral_names):
        mineral = get_mineral(name)
        if mineral is None:
            continue
        A[0, j] = mineral.get("rho_gcc", 2.65)  # RHOB response
        A[1, j] = mineral.get("neutron_phi_nphi", 0.0)  # NPHI response
        A[2, j] = mineral.get("gr_api", 0.0)  # GR response
        A[3, j] = 1.0 / (mineral.get("vp_ms", 4000) / 1e6) * 1e6  # DT ≈ 1/Vp (µs/m)

    # Fluid column (last)
    A[0, -1] = 1.0  # RHOB_fluid = 1.0 g/cc (fresh water)
    A[1, -1] = 1.0  # NPHI_fluid = 1.0 (100% neutron porosity)
    A[2, -1] = 0.0  # GR_fluid = 0
    A[3, -1] = 1.0 / (1500.0 / 1e6) * 1e6  # Vp_water ≈ 1500 m/s → DT ~ 667 µs/m

    return A, mineral_names + ["fluid"], {}


def _multi_mineral_solve(
    rhob: float,
    nphi: float,
    gr: float,
    dt: float | None = None,
    mineral_names: list[str] | None = None,
    gr_clean: float = 15,
    gr_shale: float = 150,
) -> dict[str, Any]:
    """Deterministic multi-mineral analysis from petrophysical transforms.

    Uses standard petrophysical equations to estimate mineral volumes from
    log responses, rather than unconstrained inversion (which is underdetermined
    for typical 3-measurement suites).

    Method:
      1. Compute apparent matrix density (ρ_ma) from RHOB-NPHI crossplot
      2. Apportion ρ_ma between end-member minerals (quartz/calcite/dolomite)
      3. Compute clay volume from GR using linear/Larionov
      4. Compute porosity from density once matrix density is known
      5. Optionally include DT for additional constraint

    Args:
        rhob:        bulk density (g/cm³)
        nphi:        neutron porosity (v/v, limestone matrix)
        gr:          gamma ray (API)
        dt:          sonic transit time (µs/ft) — optional, for additional lithology constraint
        mineral_names: list of minerals to consider. If None, auto-selects.
        gr_clean:    GR endpoint for clean sand (API)
        gr_shale:    GR endpoint for pure shale (API)

    Returns:
        dict with mineral volumes, porosity, matrix properties, solver diagnostics

    DER — Derived from petrophysical transforms. Not a direct measurement.
    """
    from geox_mcp.tools.kernel._mineral_catalog import (
        CLAY_MINERALS,
        get_mineral,
        compute_matrix_density,
        compute_matrix_elastic,
    )

    # ── Step 1: Clay volume from GR ──────────────────────────────────────
    igr = max(0.0, min(1.0, (gr - gr_clean) / max(gr_shale - gr_clean, 1.0)))
    # Use Larionov (tertiary) for more realistic clay volumes
    if igr > 0:
        vsh = 0.083 * (2.0 ** (3.7 * igr) - 1.0)
        vsh = max(0.0, min(1.0, vsh))
    else:
        vsh = 0.0

    # ── Step 2: Apparent matrix density ──────────────────────────────────
    # From density porosity: φ_d = (ρ_ma - ρ_b) / (ρ_ma - ρ_f)
    # Rearranging: ρ_ma = (ρ_b - φ·ρ_f) / (1 - φ)
    # Need porosity first. Use neutron-density crossplot method.

    # Density porosity (quartz matrix, fresh water)
    phi_d = (2.65 - rhob) / (2.65 - 1.0) if rhob < 2.65 else 0.0
    # Neutron porosity (limestone matrix)
    phi_n = nphi

    # Average porosity (density-neutron average, standard approach)
    phi_avg = 0.5 * (phi_d + phi_n) if (phi_d > 0 and phi_n > 0) else max(phi_d, phi_n)
    phi_avg = max(0.0, min(0.50, phi_avg))

    # Apparent matrix density from density porosity equation
    # ρ_ma_apparent = (ρ_b - φ·ρ_f) / (1 - φ)
    denom = 1.0 - phi_avg
    if denom > 0.001:
        rho_ma_apparent = (rhob - phi_avg * 1.0) / denom
    else:
        rho_ma_apparent = rhob

    # Clamp to physical range
    rho_ma_apparent = max(2.40, min(3.00, rho_ma_apparent))

    # ── Step 3: Apportion matrix density to minerals ──────────────────────
    # Quartz: 2.65, Calcite: 2.71, Dolomite: 2.87
    # Linear mixing: ρ_ma = Σ(v_i · ρ_i) where v_i are volume fractions of matrix
    # For 2 minerals: v1 = (ρ_ma - ρ2) / (ρ1 - ρ2)

    if mineral_names is None:
        # Auto-select mineral pair. GR is the primary lithology discriminator in
        # sedimentary basins. Density discriminates within families.
        # Bug fix (31 Jul 2026): original only used density, misclassifying
        # sandstones with calcite cement or limestone-scale NPHI as carbonates.
        # Now: GR < 60 API → clastic (quartz-dominated, possibly with calcite).
        #      GR >= 60 API → shaly (quartz+clay).
        #      Carbonate only when GR < 20 API AND density > 2.68.
        is_low_gr = gr < 20
        is_clean = vsh < 0.10
        is_carbonate_matrix = is_low_gr and is_clean and rho_ma_apparent > 2.68

        if is_carbonate_matrix and rho_ma_apparent > 2.78:
            mineral_names = ["dolomite", "calcite"]
        elif is_carbonate_matrix:
            mineral_names = ["calcite", "dolomite"]
        elif vsh > 0.25:
            # Shaly — quartz + clay
            mineral_names = ["quartz", "clay"]
        else:
            # Clean to slightly shaly — quartz with possible calcite cement
            mineral_names = ["quartz", "calcite"]

    # Get densities for selected minerals
    mineral_densities = {}
    for name in mineral_names:
        m = get_mineral(name)
        if m:
            mineral_densities[name] = m.get("rho_gcc", 2.65)

    # Apportion: find fractions that reproduce rho_ma_apparent
    # For 2 minerals: v1 = (ρ_ma - ρ2) / (ρ1 - ρ2)
    names = list(mineral_densities.keys())
    if len(names) >= 2:
        rho1 = mineral_densities[names[0]]
        rho2 = mineral_densities[names[1]]
        drho = rho1 - rho2
        if abs(drho) > 0.01:
            v1 = (rho_ma_apparent - rho2) / drho
            v1 = max(0.0, min(1.0, v1))
            v2 = 1.0 - v1
        else:
            v1 = 0.5
            v2 = 0.5
    else:
        v1 = 1.0
        v2 = 0.0

    # ── Step 4: Build mineral volume fractions ────────────────────────────
    mineral_volumes: dict[str, float] = {}

    # Clay from GR
    clay_vol = round(vsh, 4)
    if clay_vol > 0.001:
        mineral_volumes["clay"] = clay_vol

    # Apportion non-clay fraction to matrix minerals
    non_clay = 1.0 - clay_vol - phi_avg
    if non_clay < 0:
        non_clay = max(0.0, 1.0 - phi_avg)
        # Scale clay down
        if clay_vol > 0 and mineral_volumes.get("clay", 0) > 0:
            mineral_volumes["clay"] = round(max(0.0, 1.0 - phi_avg - non_clay), 4)

    if names:
        mineral_volumes[names[0]] = round(v1 * non_clay, 4)
    if len(names) >= 2:
        mineral_volumes[names[1]] = round(v2 * non_clay, 4)

    porosity = round(phi_avg, 4)

    # ── Step 5: Diagnostics ───────────────────────────────────────────────
    # Residual: compare predicted RHOB from mineral volumes vs actual
    pred_rhob = 0.0
    for name, vol in mineral_volumes.items():
        m = get_mineral(name)
        if m:
            pred_rhob += vol * m.get("rho_gcc", 2.65)
    pred_rhob += porosity * 1.0
    rhob_residual = abs(pred_rhob - rhob)

    # Clay typing
    clay_type = None
    cec = None
    if clay_vol > 0.01:
        clay_type = _infer_clay_type(gr, gr_clean, gr_shale, rhob, nphi)
        if clay_type:
            cm = get_mineral(clay_type)
            cec = cm.get("cec_meq_100g", 0) if cm else None

    # Matrix properties from mineral fractions
    mineral_fracs_norm = {}
    total_mineral = sum(mineral_volumes.values())
    if total_mineral > 0:
        mineral_fracs_norm = {k: v / total_mineral for k, v in mineral_volumes.items()}

    matrix_rho = compute_matrix_density(mineral_fracs_norm) if mineral_fracs_norm else 2.65
    matrix_elastic = compute_matrix_elastic(mineral_fracs_norm) if mineral_fracs_norm else {}

    rms_residual = round(rhob_residual, 6)
    if rms_residual < 0.02:
        confidence = "HIGH"
    elif rms_residual < 0.08:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "quartz": mineral_volumes.get("quartz"),
        "feldspar": mineral_volumes.get("feldspar"),
        "calcite": mineral_volumes.get("calcite"),
        "dolomite": mineral_volumes.get("dolomite"),
        "clay": round(clay_vol, 4) if clay_vol > 0.001 else None,
        "pyrite": mineral_volumes.get("pyrite"),
        "organic_matter": mineral_volumes.get("organic_matter"),
        "clay_type": clay_type,
        "cec_meq_100g": cec,
        "matrix_density_gcc": round(matrix_rho, 3),
        "matrix_vp_ms": matrix_elastic.get("vp_matrix_ms"),
        "matrix_vs_ms": matrix_elastic.get("vs_matrix_ms"),
        "solver_residual": rms_residual,
        "solver_confidence": confidence,
        "solver_n_constraints": 3,
        "apparent_matrix_density_gcc": round(rho_ma_apparent, 3),
        "porosity": porosity,
    }


def _compute_sw_model_selector(
    clay_volume: float,
    clay_type: str | None = None,
    cec_meq_100g: float | None = None,
    matrix_density_gcc: float | None = None,
    rhob: float | None = None,
) -> dict[str, Any]:
    """Auto-select water saturation model based on clay volume and type.

    Rules (from Arif's Chemistry9 build spec):
      - clay < 8%        → Archie (clean rock)
      - clay ≥ 8% + CEC  → Waxman-Smits (shaly sand with clay conductivity)
      - clay ≥ 8% no CEC → Dual-Water (clay present but unknown type)
      - carbonate vuggy   → carbonate-specific Archie m/n

    Also considers carbonate indicators (matrix density > 2.75 suggests dolomite,
    vuggy porosity suspected if density-neutron separation is large).

    Returns: {sw_model, sw_method, reasoning, confidence}
    """
    warnings: list[str] = []

    # Default
    sw_model = "archie"
    sw_method = "standard_archie"
    confidence = "HIGH"

    if clay_volume is None or clay_volume < 0.03:
        sw_model = "archie"
        sw_method = "clean_archie"
        confidence = "HIGH"
        reasoning = "Very low clay volume — standard Archie is appropriate."

    elif clay_volume < 0.08:
        sw_model = "archie"
        sw_method = "clean_archie"
        confidence = "MEDIUM"
        reasoning = "Low clay volume. Archie likely adequate. Monitor for clay conduction in high-Sw zones."
        warnings.append("clay_volume_borderline — consider dual-water if Sw > 0.70")

    elif cec_meq_100g is not None and cec_meq_100g > 10:
        sw_model = "waxman_smits"
        sw_method = "waxman_smits_qv_estimated"
        confidence = "MEDIUM"
        reasoning = (
            f"Significant clay ({clay_volume:.0%}) with CEC={cec_meq_100g} meq/100g. "
            "Clay conduction likely affects resistivity. Waxman-Smits recommended."
        )
        if cec_meq_100g > 50:
            warnings.append("high_cec — smectite suspected, bound water may dominate")

    else:
        sw_model = "dual_water"
        sw_method = "dual_water_default"
        confidence = "MEDIUM"
        reasoning = (
            f"Significant clay ({clay_volume:.0%}) but CEC unknown. Dual-water model recommended as conservative approach."
        )
        warnings.append("cec_unknown — dual-water uses default clay parameters")

    # Carbonate-specific overrides
    if matrix_density_gcc is not None and matrix_density_gcc > 2.75:
        sw_model = "carbonate_archie"
        sw_method = "carbonate_archie_variable_m"
        confidence = "LOW"
        reasoning = (
            f"Carbonate-dominated matrix (ρ_ma={matrix_density_gcc:.2f}). "
            "Archie m varies with pore type. Calibrate m from core or Pickett plot. "
            "Vuggy/fracture porosity may invalidate standard Archie."
        )
        warnings.append("carbonate_pore_system — Archie m/n may not be constant")
        warnings.append("calibrate_m_from_core_recommended")

    return {
        "sw_model": sw_model,
        "sw_method": sw_method,
        "confidence": confidence,
        "reasoning": reasoning,
        "warnings": warnings,
    }


def _multi_mineral_zone(
    depth_m: list[float],
    rhob: list[float],
    nphi: list[float],
    gr: list[float],
    dt: list[float] | None = None,
    pef: list[float] | None = None,
    rt: list[float] | None = None,
    mineral_names: list[str] | None = None,
    gr_clean: float = 15,
    gr_shale: float = 150,
    well_id: str = "unknown",
    zone_name: str = "zone",
    depth_top_m: float | None = None,
    depth_base_m: float | None = None,
) -> dict[str, Any]:
    """Per-zone multi-mineral analysis with statistical summary.

    Solves multi-mineral volumes for every depth sample in the zone,
    then aggregates into P10/P50/P90 statistics.

    Args:
        depth_m:      depth array (m)
        rhob:         bulk density (g/cm³)
        nphi:         neutron porosity (v/v, limestone matrix)
        gr:           gamma ray (API)
        dt:           sonic transit time (µs/ft) — optional
        pef:          photoelectric factor (barns/e) — optional, improves carbonate discrimination
        rt:           resistivity (Ω·m) — optional, for Sw model selection only
        mineral_names: list of minerals to solve for
        gr_clean:     GR clean endpoint
        gr_shale:     GR shale endpoint
        well_id:      well identifier
        zone_name:    zone identifier
        depth_top_m:  zone top depth
        depth_base_m: zone base depth

    Returns:
        Per-zone summary with mineralogy P10/P50/P90, matrix properties, warnings

    DER — zone-aggregated multi-mineral analysis. Not a direct measurement.
    """
    import numpy as np

    n = min(len(depth_m), len(rhob), len(nphi), len(gr))

    results: list[dict[str, Any]] = []
    warnings: set[str] = set()

    for i in range(n):
        d = float(depth_m[i])
        r = float(rhob[i])
        np_val = float(nphi[i])
        g = float(gr[i])
        dt_val = float(dt[i]) if dt and i < len(dt) else None
        pef_val = float(pef[i]) if pef and i < len(pef) else None

        if np.isnan(r) or np.isnan(np_val) or np.isnan(g):
            continue
        if r < 1.0 or r > 3.5:
            continue
        if np_val < -0.15 or np_val > 0.60:
            continue

        mvs = _multi_mineral_solve(
            rhob=r,
            nphi=np_val,
            gr=g,
            dt=dt_val,
            mineral_names=mineral_names,
            gr_clean=gr_clean,
            gr_shale=gr_shale,
        )

        if pef_val is not None and not np.isnan(pef_val) and pef_val > 0:
            mvs["pef_barns_e"] = round(pef_val, 2)
            # PEF refines carbonate discrimination
            if pef_val > 4.5:
                mvs["pef_note"] = "High PEF — calcite/dolomite discrimination improved"
            # Recompute with PEF as additional weight
            rho_ma = mvs.get("apparent_matrix_density_gcc", 2.65)
            if pef_val > 4.0 and rho_ma > 2.68:
                # PEF confirms carbonate — bias toward calcite/dolomite
                mvs["pef_carbonate_confirmed"] = True

        results.append(mvs)

        # Collect warnings from solver
        for w in mvs.get("warnings", []):
            warnings.add(w)

    if not results:
        return {"status": "INVALID", "errors": ["No valid samples in zone"], "well_id": well_id, "zone": zone_name}

    # ── Aggregate statistics ──────────────────────────────────────────────
    def pct(key, p):
        vals = [r.get(key) for r in results if r.get(key) is not None]
        if not vals:
            return None
        return round(float(np.percentile(vals, p)), 4)

    def mean(key):
        vals = [r.get(key) for r in results if r.get(key) is not None]
        if not vals:
            return None
        return round(float(np.mean(vals)), 4)

    # Mineralogy stats
    mineral_stats = {}
    for mineral in ["quartz", "calcite", "dolomite", "clay", "feldspar", "pyrite", "organic_matter"]:
        vals = [r.get(mineral) for r in results if r.get(mineral) is not None and r.get(mineral, 0) > 0]
        if vals:
            mineral_stats[mineral] = {
                "p10": pct(mineral, 10),
                "p50": pct(mineral, 50),
                "p90": pct(mineral, 90),
                "mean": mean(mineral),
                "n_detected": len(vals),
                "n_total": len(results),
            }

    # Solver quality
    residuals = [r.get("solver_residual", 0) for r in results if r.get("solver_residual") is not None]
    avg_residual = float(np.mean(residuals)) if residuals else 0.0
    confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        c = r.get("solver_confidence", "LOW")
        confidence_counts[c] = confidence_counts.get(c, 0) + 1
    dominant_confidence = max(confidence_counts, key=confidence_counts.get)

    # Porosity
    porosities = [r.get("porosity", 0) for r in results]
    phi_p50 = round(float(np.percentile(porosities, 50)), 4) if porosities else 0

    # Matrix density
    matrix_densities = [r.get("matrix_density_gcc", 2.65) for r in results if r.get("matrix_density_gcc")]
    avg_matrix_rho = float(np.mean(matrix_densities)) if matrix_densities else 2.65

    # Clay type
    clay_types = [r.get("clay_type") for r in results if r.get("clay_type")]
    dominant_clay = max(set(clay_types), key=clay_types.count) if clay_types else None

    # Average clay and CEC
    clay_vols = [r.get("clay", 0) for r in results if r.get("clay") is not None]
    avg_clay = float(np.mean(clay_vols)) if clay_vols else 0
    cec_vals = [r.get("cec_meq_100g") for r in results if r.get("cec_meq_100g") is not None]
    avg_cec = float(np.mean(cec_vals)) if cec_vals else None

    # Sw model selection
    sw_selector = _compute_sw_model_selector(
        clay_volume=avg_clay,
        clay_type=dominant_clay,
        cec_meq_100g=avg_cec,
        matrix_density_gcc=avg_matrix_rho,
    )

    # Build warnings list
    if not pef:
        warnings.add("PEF unavailable — carbonate mineral separation confidence reduced")
        warnings.add("calcite-dolomite separation uncertain without PEF")
    if dt is None:
        warnings.add("DT unavailable — velocity constraint absent")

    return {
        "status": "OK",
        "mode": "multi_mineral_zone",
        "well": well_id,
        "zone": zone_name,
        "depth_top_m": depth_top_m or (float(depth_m[0]) if depth_m else None),
        "depth_base_m": depth_base_m or (float(depth_m[-1]) if depth_m else None),
        "n_samples": len(results),
        "n_valid": len([r for r in results if r.get("solver_confidence") != "LOW"]),
        "mineralogy": mineral_stats,
        "matrix_density_gcc": round(avg_matrix_rho, 3),
        "phie": phi_p50,  # effective porosity (mineral-corrected)
        "sw_model": sw_selector["sw_model"],
        "sw_method": sw_selector["sw_method"],
        "sw_confidence": sw_selector["confidence"],
        "avg_clay_fraction": round(avg_clay, 4),
        "dominant_clay_type": dominant_clay,
        "avg_cec_meq_100g": avg_cec,
        "solver_residual": round(avg_residual, 6),
        "solver_confidence": dominant_confidence,
        "confidence_distribution": confidence_counts,
        "warnings": sorted(list(warnings)),
        "epistemic": {
            "evidence_layer": "WELL",
            "source": "geox_multi_mineral_zone",
            "reversible": True,
            "authority_claim": "ADVISORY",
        },
    }


def _infer_clay_type(
    gr: float,
    gr_clean: float,
    gr_shale: float,
    rhob: float,
    nphi: float,
) -> str:
    """Infer dominant clay type from GR, density, and neutron response.

    Heuristic based on Thomas & Stieber (1975) and Crain's rules:
      - High GR + high NPHI + moderate density → illite
      - Moderate GR + very high NPHI + low density → smectite
      - Moderate GR + moderate NPHI + density near quartz → kaolinite
      - Low GR + high density + high PE → chlorite

    Args:
        gr:        gamma ray reading (API)
        gr_clean:  clean sand GR endpoint (API)
        gr_shale:  pure shale GR endpoint (API)
        rhob:      bulk density (g/cm³)
        nphi:      neutron porosity (v/v)
    """
    # Normalise GR to IGR
    igr = max(0.0, min(1.0, (gr - gr_clean) / max(gr_shale - gr_clean, 1.0)))

    # Density-neutron patterns
    if igr > 0.7 and nphi > 0.25 and rhob < 2.30:
        return "smectite"  # swelling clay — low density, high neutron
    elif igr > 0.6 and rhob > 2.75:
        return "chlorite"  # iron-rich — high density
    elif igr > 0.5 and nphi > 0.15 and 2.55 < rhob < 2.80:
        return "illite"  # most common burial clay
    elif igr > 0.3 and 2.60 < rhob < 2.70:
        return "kaolinite"  # pore-throat blocking
    elif igr > 0.1:
        return "illite"  # default
    else:
        return "illite"  # fallback


# ═══════════════════════════════════════════════════════════════════════════════
# Mineral Volume State — Chemistry9 Foundation
# ═══════════════════════════════════════════════════════════════════════════════


class MineralVolumeState:
    """Mineral volume fractions from multi-mineral analysis (Chemistry9 X1+X3).

    This is the chemical nucleus — every downstream petrophysical number
    derives its physical meaning from these fractions.

    Without this, GEOX is a single-mineral calculator.
    With this, GEOX is a rock chemistry reasoning system.
    """

    def __init__(
        self,
        quartz: float | None = None,
        feldspar: float | None = None,
        calcite: float | None = None,
        dolomite: float | None = None,
        clay: float | None = None,
        pyrite: float | None = None,
        organic_matter: float | None = None,
        clay_type: str | None = None,
        cec_meq_100g: float | None = None,
        matrix_density_gcc: float | None = None,
        matrix_pef_barns_e: float | None = None,
        matrix_gr_api: float | None = None,
        matrix_vp_ms: float | None = None,
        matrix_vs_ms: float | None = None,
        solver_residual: float | None = None,
        solver_confidence: str | None = None,
        solver_n_constraints: int | None = None,
    ):
        self.quartz = quartz
        self.feldspar = feldspar
        self.calcite = calcite
        self.dolomite = dolomite
        self.clay = clay
        self.pyrite = pyrite
        self.organic_matter = organic_matter
        self.clay_type = clay_type
        self.cec_meq_100g = cec_meq_100g
        self.matrix_density_gcc = matrix_density_gcc
        self.matrix_pef_barns_e = matrix_pef_barns_e
        self.matrix_gr_api = matrix_gr_api
        self.matrix_vp_ms = matrix_vp_ms
        self.matrix_vs_ms = matrix_vs_ms
        self.solver_residual = solver_residual
        self.solver_confidence = solver_confidence
        self.solver_n_constraints = solver_n_constraints

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @property
    def brittleness_index(self) -> float | None:
        brittle = (self.quartz or 0) + (self.calcite or 0) + (self.dolomite or 0) + (self.feldspar or 0)
        ductile = brittle + (self.clay or 0) + (self.organic_matter or 0)
        if ductile < 0.001:
            return None
        return round(brittle / ductile, 4)

    @property
    def dominant_mineral(self) -> str | None:
        fractions = {
            k: v
            for k, v in self.__dict__.items()
            if k
            not in (
                "clay_type",
                "cec_meq_100g",
                "matrix_density_gcc",
                "matrix_pef_barns_e",
                "matrix_gr_api",
                "matrix_vp_ms",
                "matrix_vs_ms",
                "solver_residual",
                "solver_confidence",
                "solver_n_constraints",
            )
            and v is not None
            and (v or 0) > 0
        }
        if not fractions:
            return None
        return max(fractions, key=lambda k: fractions[k] or 0)


# ═══════════════════════════════════════════════════════════════════════════════
# Earth State Vector — Shared Physical State Between Tools
# ═══════════════════════════════════════════════════════════════════════════════


class EarthStateVector:
    """Physical state at current workspace location, propagated between tools.

    This is the architectural fix for the "memoryless calculator" problem.
    Every tool writes to and reads from this shared state so that:
      - geox_petrophysics → EarthStateVector.porosity_fraction
      - geox_multi_mineral → EarthStateVector.mineralogy
      - geox_thermal_maturity → EarthStateVector.burial_max_depth
      - geox_geomechanics → EarthStateVector.sv_mpa

    Without this, every tool reconstructs physical context from scratch.
    """

    # ── Mineralogy (Chemistry9 foundation) ────────────────────────────────────
    mineralogy: MineralVolumeState | None = None

    # ── From Petrophysics ─────────────────────────────────────────────────────
    porosity_fraction: float | None = None
    sw_fraction: float | None = None
    vsh_fraction: float | None = None
    permeability_md: float | None = None
    net_pay_m: float | None = None
    density_integrated_sv_mpa: float | None = None

    # ── From Geomechanics ─────────────────────────────────────────────────────
    sv_mpa: float | None = None
    pp_mpa: float | None = None
    shmin_mpa: float | None = None
    shmax_mpa: float | None = None
    vp_ms: float | None = None
    vs_ms: float | None = None

    # ── From Basin / Thermal ──────────────────────────────────────────────────
    burial_max_depth_m: float | None = None
    burial_max_age_ma: float | None = None
    thermal_maturity_ro: float | None = None
    tectonic_subsidence_km: float | None = None
    sediment_load_subsidence_km: float | None = None
    rift_beta: float | None = None

    # ── From Forward Prediction ───────────────────────────────────────────────
    predicted_phi_fraction: float | None = None
    measured_phi_fraction: float | None = None
    delta_phi: float | None = None
    anomaly_class: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for tool output or workspace storage."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_petrophysics(cls, petro_result: dict[str, Any], **kwargs: Any) -> EarthStateVector:
        """Populate from geox_petrophysics output."""
        esv = cls(**kwargs)
        phi_stats = petro_result.get("phi", {}) or petro_result.get("phi_stats", {})
        esv.porosity_fraction = phi_stats.get("mean") or phi_stats.get("p50")
        sw_stats = petro_result.get("sw", {}) or petro_result.get("sw_stats", {})
        esv.sw_fraction = sw_stats.get("mean") or sw_stats.get("p50")
        vsh_stats = petro_result.get("vsh", {}) or petro_result.get("vsh_stats", {})
        esv.vsh_fraction = vsh_stats.get("mean") or vsh_stats.get("p50")
        np_data = petro_result.get("net_pay", {})
        esv.net_pay_m = np_data.get("thickness_m") if isinstance(np_data, dict) else None
        return esv

    def inject_into_tool_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Auto-inject Earth State Vector values into tool parameters.

        Only fills params that are None/empty. Explicit values always win.
        """
        inject_map = {
            "porosity_fraction": self.porosity_fraction,
            "sw_fraction": self.sw_fraction,
            "vsh_fraction": self.vsh_fraction,
            "permeability_md": self.permeability_md,
            "burial_max_depth_m": self.burial_max_depth_m,
            "sv_mpa": self.sv_mpa,
            "pp_mpa": self.pp_mpa,
            "thermal_maturity_ro": self.thermal_maturity_ro,
            "rift_beta": self.rift_beta,
        }
        for key, value in inject_map.items():
            if value is not None and key in params and not params.get(key):
                params[key] = value
        return params
