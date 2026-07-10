"""
backstrip.py — Basin Backstripping Engine
═════════════════════════════════════════
Reconstruct tectonic subsidence history from validated well stratigraphy.

Physics: Steckler & Watts (1978) Airy isostasy + Sclater & Christie (1980) decompaction.
Equations: Wikipedia Back-stripping, Geological Digressions (Ricketts 2024).

Key equation (Steckler & Watts 1978):
  Y = S * (ρm - ρs) / (ρm - ρw) + Wd - ΔSL * ρm / (ρm - ρw)

where:
  Y = tectonic subsidence (m)
  S = decompacted sediment thickness (m)
  ρm = mantle density (kg/m³)
  ρs = mean sediment density (kg/m³)
  ρw = water density (kg/m³)
  Wd = paleowater depth (m)
  ΔSL = sea level change (m)

Porosity-depth (Athy 1930):
  φ(z) = φ₀ * exp(-c * z)

where:
  φ₀ = surface porosity
  c = compaction coefficient (m⁻¹)
  z = depth (m)

Decompaction (Newton-Raphson):
  L_decompacted = L * (1 - φ_avg(z)) / (1 - φ_avg(z_new))

DITEMPA BUKAN DIBERI — Forged, Not Given.

References:
  - Steckler, M.S. & Watts, A.B. (1978) Subsidence of the Atlantic-type continental margin off New York.
  - Sclater, J.G. & Christie, P.A.F. (1980) Continental stretching: North Sea subsidence.
  - Bond, G.C. & Kominz, M.A. (1984) Construction of tectonic subsidence curves.
  - Allen, P.A. & Allen, J.R. (2013) Basin Analysis: Principles and Application.
  - Angevine, C.L. et al. (1990) Quantitative Sedimentary Basin Modeling.
  - Watts, A.B. & Ryan, W.B.F. (1976) Flexure of the lithosphere and continental margin basins.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════════
# Physical Constants
# ═══════════════════════════════════════════════════════════════════════════════

RHO_MANTLE = 3300.0  # kg/m³ — mantle density
RHO_WATER = 1030.0  # kg/m³ — seawater density
RHO_GRAIN = 2650.0  # kg/m³ — average grain density (quartz-dominated)

# ═══════════════════════════════════════════════════════════════════════════════
# Lithology Parameters — Porosity-Depth Curves
# ═══════════════════════════════════════════════════════════════════════════════
# φ(z) = φ₀ * exp(-c * z)
# From: Sclater & Christie (1980), Allen & Allen (2013), Svadlenak et al. (2026)

LITHOLOGY_DEFAULTS: dict[str, dict[str, float]] = {
    "sandstone": {
        "phi0": 0.49,  # surface porosity
        "c": 0.27e-3,  # compaction coefficient (m⁻¹)
        "rho_grain": 2650,  # grain density (kg/m³)
    },
    "shale": {
        "phi0": 0.63,
        "c": 0.51e-3,
        "rho_grain": 2720,
    },
    "mudstone": {
        "phi0": 0.55,
        "c": 0.39e-3,
        "rho_grain": 2700,
    },
    "siltstone": {
        "phi0": 0.50,
        "c": 0.32e-3,
        "rho_grain": 2680,
    },
    "limestone": {
        "phi0": 0.40,
        "c": 0.22e-3,
        "rho_grain": 2710,
    },
    "dolomite": {
        "phi0": 0.20,
        "c": 0.12e-3,
        "rho_grain": 2850,
    },
    "chalk": {
        "phi0": 0.70,
        "c": 0.40e-3,
        "rho_grain": 2710,
    },
    "marl": {
        "phi0": 0.55,
        "c": 0.35e-3,
        "rho_grain": 2700,
    },
    "evaporite": {
        "phi0": 0.10,
        "c": 0.05e-3,
        "rho_grain": 2900,
    },
    "conglomerate": {
        "phi0": 0.35,
        "c": 0.20e-3,
        "rho_grain": 2650,
    },
    "volcanic_ash": {
        "phi0": 0.60,
        "c": 0.45e-3,
        "rho_grain": 2600,
    },
}


@dataclass
class LithologyParams:
    """Porosity-depth parameters for a single lithology."""

    name: str
    phi0: float  # surface porosity (0-1)
    c: float  # compaction coefficient (m⁻¹)
    rho_grain: float  # grain density (kg/m³)

    @classmethod
    def from_name(cls, name: str) -> LithologyParams:
        """Look up standard lithology parameters."""
        key = name.lower().strip()
        if key in LITHOLOGY_DEFAULTS:
            d = LITHOLOGY_DEFAULTS[key]
            return cls(name=key, phi0=d["phi0"], c=d["c"], rho_grain=d["rho_grain"])
        # Default to sandstone if unknown
        d = LITHOLOGY_DEFAULTS["sandstone"]
        return cls(name="sandstone", phi0=d["phi0"], c=d["c"], rho_grain=d["rho_grain"])

    def porosity_at_depth(self, depth_m: float) -> float:
        """Porosity at depth using Athy (1930) exponential law."""
        return self.phi0 * math.exp(-self.c * depth_m)

    def density_at_depth(self, depth_m: float, rho_water: float = RHO_WATER) -> float:
        """Bulk density at depth: ρ = φ*ρw + (1-φ)*ρgrain"""
        phi = self.porosity_at_depth(depth_m)
        return phi * rho_water + (1 - phi) * self.rho_grain


@dataclass
class StratigraphicLayer:
    """A single stratigraphic layer in a well."""

    name: str
    top_depth_m: float  # present-day top depth
    base_depth_m: float  # present-day base depth
    age_ma: float  # age of top surface (Ma)
    lithology: LithologyParams
    paleowater_depth_m: float = 0.0  # estimated paleowater depth at deposition
    sea_level_change_m: float = 0.0  # sea level change since deposition


@dataclass
class DecompactedLayer:
    """Result of decompaction for a single layer."""

    name: str
    age_ma: float
    original_thickness_m: float
    decompacted_thickness_m: float
    porosity_top: float
    porosity_base: float
    avg_density_kg_m3: float
    depth_top_m: float  # decompacted top depth
    depth_base_m: float  # decompacted base depth


@dataclass
class BackstripStep:
    """Result of one backstripping step (one time slice)."""

    age_ma: float
    total_subsidence_m: float  # Y_total = decompacted thickness + water depth
    tectonic_subsidence_m: float  # Y_tectonic (Steckler & Watts equation)
    sediment_load_subsidence_m: float  # Y_total - Y_tectonic
    paleowater_depth_m: float
    sea_level_change_m: float
    avg_sediment_density_kg_m3: float
    decompacted_layers: list[DecompactedLayer]
    sediment_thickness_m: float  # total decompacted sediment column


@dataclass
class BackstripResult:
    """Complete backstripping result for a well."""

    well_name: str
    steps: list[BackstripStep]
    total_subsidence_curve: list[tuple[float, float]]  # (age_ma, subsidence_m)
    tectonic_subsidence_curve: list[tuple[float, float]]  # (age_ma, tectonic_m)
    sediment_load_curve: list[tuple[float, float]]  # (age_ma, load_m)
    subsidence_rates: list[tuple[float, float]]  # (age_ma, rate_m_myr)
    tectonic_rates: list[tuple[float, float]]  # (age_ma, rate_m_myr)
    basin_type_hint: str  # "passive_margin", "foreland", "strike_slip", "rift", "unknown"
    provenance: dict[str, Any]
    diagnostics: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Core Physics
# ═══════════════════════════════════════════════════════════════════════════════


def decompact_layer(
    layer: StratigraphicLayer,
    depth_top_present: float,
    depth_base_present: float,
    depth_top_decompacted: float,
    rho_water: float = RHO_WATER,
) -> DecompactedLayer:
    """Decompact a single layer using Newton-Raphson iteration.

    Given present-day thickness and new top depth after removal of overlying
    layers, compute the decompacted thickness.

    The decompaction equation:
      L_decompacted = L_present * integral(1-φ(z))dz from top to base
                      / integral(1-φ(z))dz from new_top to new_base

    Solved iteratively because new_base depends on decompacted thickness.
    """
    lith = layer.lithology
    L_present = depth_base_present - depth_top_present

    # Present-day average porosity
    phi_top = lith.porosity_at_depth(depth_top_present)
    phi_base = lith.porosity_at_depth(depth_base_present)
    phi_avg_present = (phi_top + phi_base) / 2

    # Solid thickness (compaction-invariant)
    solid_thickness = L_present * (1 - phi_avg_present)

    # Newton-Raphson: find new_base such that
    # integral(1-φ(z)) from depth_top_decompacted to new_base = solid_thickness
    # Approximate: L_decomp * (1 - φ_avg(new_depths)) = solid_thickness
    # Iterate: L_decomp = solid_thickness / (1 - φ_avg(depth_top + L_decomp/2))

    L_decomp = L_present  # initial guess
    for _ in range(50):  # max iterations
        depth_mid = depth_top_decompacted + L_decomp / 2
        phi_mid = lith.porosity_at_depth(depth_mid)
        L_new = solid_thickness / (1 - phi_mid)
        if abs(L_new - L_decomp) < 0.001:  # convergence: 1mm
            break
        L_decomp = L_new

    depth_base_decomp = depth_top_decompacted + L_decomp

    # Average density of decompacted layer
    phi_top_decomp = lith.porosity_at_depth(depth_top_decompacted)
    phi_base_decomp = lith.porosity_at_depth(depth_base_decomp)
    phi_avg_decomp = (phi_top_decomp + phi_base_decomp) / 2
    avg_density = phi_avg_decomp * rho_water + (1 - phi_avg_decomp) * lith.rho_grain

    return DecompactedLayer(
        name=layer.name,
        age_ma=layer.age_ma,
        original_thickness_m=L_present,
        decompacted_thickness_m=L_decomp,
        porosity_top=phi_top_decomp,
        porosity_base=phi_base_decomp,
        avg_density_kg_m3=avg_density,
        depth_top_m=depth_top_decompacted,
        depth_base_m=depth_base_decomp,
    )


def tectonic_subsidence(
    sediment_thickness_m: float,
    avg_sediment_density_kg_m3: float,
    paleowater_depth_m: float,
    sea_level_change_m: float = 0.0,
    rho_mantle: float = RHO_MANTLE,
    rho_water: float = RHO_WATER,
) -> float:
    """Compute tectonic subsidence using Steckler & Watts (1978) equation.

    Y = S * (ρm - ρs) / (ρm - ρw) + Wd - ΔSL * ρm / (ρm - ρw)

    Returns Y (tectonic subsidence in meters).
    """
    S = sediment_thickness_m
    rho_s = avg_sediment_density_kg_m3
    rho_m = rho_mantle
    rho_w = rho_water
    Wd = paleowater_depth_m
    dSL = sea_level_change_m

    Y = S * (rho_m - rho_s) / (rho_m - rho_w) + Wd - dSL * rho_m / (rho_m - rho_w)
    return Y


def backstrip_well(
    well_name: str,
    layers: list[StratigraphicLayer],
    rho_mantle: float = RHO_MANTLE,
    rho_water: float = RHO_WATER,
    uncertainty_realizations: int = 1,
) -> BackstripResult:
    """Backstrip a complete well section.

    Steps:
    1. Sort layers by age (oldest first)
    2. For each time slice, decompact all remaining layers
    3. Compute average sediment density
    4. Apply Steckler & Watts equation for tectonic subsidence
    5. Track total and tectonic subsidence curves

    Returns BackstripResult with complete subsidence history.
    """
    if not layers:
        return BackstripResult(
            well_name=well_name,
            steps=[],
            total_subsidence_curve=[],
            tectonic_subsidence_curve=[],
            sediment_load_curve=[],
            subsidence_rates=[],
            tectonic_rates=[],
            basin_type_hint="unknown",
            provenance={"error": "no layers provided"},
            diagnostics=["No stratigraphic layers provided"],
        )

    # Sort layers by age (oldest first = bottom of section)
    sorted_layers = sorted(layers, key=lambda l: l.age_ma, reverse=True)

    steps: list[BackstripStep] = []
    diagnostics: list[str] = []

    # Iterate: remove top layer at each step
    for i in range(len(sorted_layers)):
        # Remaining layers (after removing top i layers)
        remaining = sorted_layers[i:]
        age = remaining[0].age_ma  # age of the oldest remaining layer

        # Decompact all remaining layers
        # Start from depth = 0 (seafloor after removing overlying layers)
        current_top = 0.0
        decompacted_layers: list[DecompactedLayer] = []
        total_sediment_thickness = 0.0

        for layer in remaining:
            # Present-day depths for this layer
            # For the remaining column, we use the original depths
            # but the decompaction is computed from the new top
            depth_top_present = layer.top_depth_m
            depth_base_present = layer.base_depth_m

            decomp = decompact_layer(
                layer=layer,
                depth_top_present=depth_top_present,
                depth_base_present=depth_base_present,
                depth_top_decompacted=current_top,
                rho_water=rho_water,
            )
            decompacted_layers.append(decomp)
            current_top = decomp.depth_base_m
            total_sediment_thickness += decomp.decompacted_thickness_m

        # Average sediment density for the entire column
        if total_sediment_thickness > 0:
            weighted_density = sum(d.decompacted_thickness_m * d.avg_density_kg_m3 for d in decompacted_layers)
            avg_density = weighted_density / total_sediment_thickness
        else:
            avg_density = RHO_GRAIN

        # Paleowater depth (use the youngest remaining layer's estimate)
        paleowater_depth = remaining[0].paleowater_depth_m

        # Sea level change
        sea_level_change = remaining[0].sea_level_change_m

        # Total subsidence = sediment thickness + water depth
        total_subsidence = total_sediment_thickness + paleowater_depth

        # Tectonic subsidence (Steckler & Watts 1978)
        tect_sub = tectonic_subsidence(
            sediment_thickness_m=total_sediment_thickness,
            avg_sediment_density_kg_m3=avg_density,
            paleowater_depth_m=paleowater_depth,
            sea_level_change_m=sea_level_change,
            rho_mantle=rho_mantle,
            rho_water=rho_water,
        )

        # Sediment load subsidence
        sediment_load = total_subsidence - tect_sub

        step = BackstripStep(
            age_ma=age,
            total_subsidence_m=total_subsidence,
            tectonic_subsidence_m=tect_sub,
            sediment_load_subsidence_m=sediment_load,
            paleowater_depth_m=paleowater_depth,
            sea_level_change_m=sea_level_change,
            avg_sediment_density_kg_m3=avg_density,
            decompacted_layers=decompacted_layers,
            sediment_thickness_m=total_sediment_thickness,
        )
        steps.append(step)

    # Build curves (sorted by age, oldest first)
    total_curve = [(s.age_ma, s.total_subsidence_m) for s in steps]
    tectonic_curve = [(s.age_ma, s.tectonic_subsidence_m) for s in steps]
    load_curve = [(s.age_ma, s.sediment_load_subsidence_m) for s in steps]

    # Compute subsidence rates (ΔY / Δt)
    subsidence_rates: list[tuple[float, float]] = []
    tectonic_rates: list[tuple[float, float]] = []
    for i in range(1, len(steps)):
        dt = steps[i - 1].age_ma - steps[i].age_ma  # Myr (positive forward in time)
        if dt > 0:
            d_total = steps[i].total_subsidence_m - steps[i - 1].total_subsidence_m
            d_tect = steps[i].tectonic_subsidence_m - steps[i - 1].tectonic_subsidence_m
            subsidence_rates.append((steps[i].age_ma, d_total / dt))
            tectonic_rates.append((steps[i].age_ma, d_tect / dt))

    # Classify basin type from tectonic subsidence curve shape
    basin_type = _classify_basin_type(tectonic_curve)

    # Provenance
    provenance = {
        "method": "backstripping",
        "reference": "Steckler & Watts (1978), Sclater & Christie (1980)",
        "isostasy_model": "Airy (local)",
        "decompaction": "Athy (1930) exponential — Newton-Raphson",
        "rho_mantle_kg_m3": rho_mantle,
        "rho_water_kg_m3": rho_water,
        "layer_count": len(sorted_layers),
        "step_count": len(steps),
        "well_name": well_name,
        "uncertainty_realizations": uncertainty_realizations,
    }

    if basin_type == "passive_margin":
        diagnostics.append(
            "Tectonic subsidence shows rapid initial subsidence followed by "
            "exponential decay — consistent with synrift-postrift thermal subsidence."
        )
    elif basin_type == "foreland":
        diagnostics.append(
            "Tectonic subsidence shows punctuated acceleration — consistent with flexural loading from thrust emplacement."
        )

    return BackstripResult(
        well_name=well_name,
        steps=steps,
        total_subsidence_curve=total_curve,
        tectonic_subsidence_curve=tectonic_curve,
        sediment_load_curve=load_curve,
        subsidence_rates=subsidence_rates,
        tectonic_rates=tectonic_rates,
        basin_type_hint=basin_type,
        provenance=provenance,
        diagnostics=diagnostics,
    )


def _classify_basin_type(tectonic_curve: list[tuple[float, float]]) -> str:
    """Classify basin type from tectonic subsidence curve shape.

    Heuristic classification based on Xie & Heller (2006) motifs:
    - Passive margin: rapid initial subsidence + exponential decay
    - Foreland: punctuated acceleration (thrust loading)
    - Strike-simp: short-lived rapid subsidence
    - Rift: rapid initial subsidence (may not have postrift)
    """
    if len(tectonic_curve) < 3:
        return "unknown"

    # Extract subsidence values
    ages = [p[0] for p in tectonic_curve]
    subs = [p[1] for p in tectonic_curve]

    # Check for exponential decay pattern (passive margin)
    # Compute rate of change of subsidence rate
    rates = []
    for i in range(1, len(subs)):
        dt = ages[i - 1] - ages[i]
        if dt > 0:
            rates.append((subs[i] - subs[i - 1]) / dt)

    if len(rates) < 2:
        return "unknown"

    # Check if rates are decreasing (exponential decay)
    decreasing_count = sum(1 for i in range(1, len(rates)) if rates[i] < rates[i - 1])
    if decreasing_count > len(rates) * 0.6:
        return "passive_margin"

    # Check for acceleration (foreland)
    increasing_count = sum(1 for i in range(1, len(rates)) if rates[i] > rates[i - 1])
    if increasing_count > len(rates) * 0.4:
        return "foreland"

    return "unknown"


def compute_subsidencde_ratio(
    result_a: BackstripResult,
    result_b: BackstripResult,
    time_ma: float,
) -> dict[str, Any]:
    """Compute subsidence ratios between two wells at a given time.

    Used for the Two Oceanics framework:
      - Accommodation ratio = total_subsidence_A / total_subsidence_B
      - Load ratio = sediment_load_A / sediment_load_B
    """

    # Find nearest time step in each result
    def nearest_step(result: BackstripResult, t: float) -> BackstripStep | None:
        if not result.steps:
            return None
        return min(result.steps, key=lambda s: abs(s.age_ma - t))

    step_a = nearest_step(result_a, time_ma)
    step_b = nearest_step(result_b, time_ma)

    if step_a is None or step_b is None:
        return {"error": "no data at requested time"}

    total_a = step_a.total_subsidence_m
    total_b = step_b.total_subsidence_m
    load_a = step_a.sediment_load_subsidence_m
    load_b = step_b.sediment_load_subsidence_m

    return {
        "time_ma": time_ma,
        "total_subsidence_a_m": total_a,
        "total_subsidence_b_m": total_b,
        "accommodation_ratio": total_a / total_b if total_b > 0 else float("inf"),
        "sediment_load_a_m": load_a,
        "sediment_load_b_m": load_b,
        "load_ratio": load_a / load_b if load_b > 0 else float("inf"),
        "tectonic_a_m": step_a.tectonic_subsidence_m,
        "tectonic_b_m": step_b.tectonic_subsidence_m,
    }
