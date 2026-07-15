"""
geox_basin_backstrip — Basin Backstripping MCP Tool
════════════════════════════════════════════════════
Reconstruct tectonic and total subsidence history from validated well stratigraphy.

Uses Steckler & Watts (1978) Airy isostasy + Sclater & Christie (1980) decompaction.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any


async def geox_basin_backstrip(
    well_ref: str,
    stratigraphic_ages: list[dict[str, Any]],
    lithology_model: dict[str, Any],
    palaeobathymetry_model: dict[str, Any],
    sea_level_model_ref: str = "",
    water_density_kg_m3: float = 1030.0,
    mantle_density_kg_m3: float = 3300.0,
    uncertainty_realizations: int = 1000,
) -> dict[str, Any]:
    """Reconstruct tectonic and total subsidence through time from validated well stratigraphy.

    Uses Steckler & Watts (1978) Airy isostasy + Sclater & Christie (1980) decompaction.
    Each stratigraphic layer is progressively removed and the isostatic response calculated.

    Args:
        well_ref: Well identifier (must have passed geox_well_qc)
        stratigraphic_ages: List of {name, top_depth_m, base_depth_m, age_ma, lithology, paleowater_depth_m}
        lithology_model: {lithology_name: {phi0, c, rho_grain}} — porosity-depth parameters
        palaeobathymetry_model: {age_ma: water_depth_m} — paleowater depth estimates
        sea_level_model_ref: Reference to sea level curve (optional)
        water_density_kg_m3: Seawater density (default 1030)
        mantle_density_kg_m3: Mantle density (default 3300)
        uncertainty_realizations: Number of Monte Carlo realizations (default 1000)

    Returns:
        BackstripResult with total_subsidence, tectonic_subsidence, sediment_load_subsidence,
        uncertainty envelope, diagnostics, and provenance.

    OBS — Reads validated well data. No mutation.
    """
    from geox_core.engines.basin.backstrip import (
        LithologyParams,
        StratigraphicLayer,
        backstrip_well,
    )

    # Build stratigraphic layers from input
    layers: list[StratigraphicLayer] = []
    for s in stratigraphic_ages:
        lith_name = s.get("lithology", "sandstone")
        lith_params = LithologyParams.from_name(lith_name)

        # Override with custom parameters if provided
        if lith_name in lithology_model:
            custom = lithology_model[lith_name]
            lith_params = LithologyParams(
                name=lith_name,
                phi0=custom.get("phi0", lith_params.phi0),
                c=custom.get("c", lith_params.c),
                rho_grain=custom.get("rho_grain", lith_params.rho_grain),
            )

        # Paleowater depth
        age = s.get("age_ma", 0.0)
        pwd = s.get("paleowater_depth_m", 0.0)
        if age in palaeobathymetry_model:
            pwd = palaeobathymetry_model[age]

        layer = StratigraphicLayer(
            name=s.get("name", f"layer_{age}"),
            top_depth_m=s.get("top_depth_m", 0.0),
            base_depth_m=s.get("base_depth_m", 0.0),
            age_ma=age,
            lithology=lith_params,
            paleowater_depth_m=pwd,
            sea_level_change_m=s.get("sea_level_change_m", 0.0),
        )
        layers.append(layer)

    # Run backstripping
    result = backstrip_well(
        well_name=well_ref,
        layers=layers,
        rho_mantle=mantle_density_kg_m3,
        rho_water=water_density_kg_m3,
        uncertainty_realizations=uncertainty_realizations,
    )

    # Build output
    return {
        "success": True,
        "well_ref": well_ref,
        "total_subsidence": [{"age_ma": age, "subsidence_m": val} for age, val in result.total_subsidence_curve],
        "tectonic_subsidence": [{"age_ma": age, "subsidence_m": val} for age, val in result.tectonic_subsidence_curve],
        "sediment_load_subsidence": [{"age_ma": age, "subsidence_m": val} for age, val in result.sediment_load_curve],
        "subsidence_rates_m_myr": [{"age_ma": age, "rate_m_myr": rate} for age, rate in result.subsidence_rates],
        "tectonic_rates_m_myr": [{"age_ma": age, "rate_m_myr": rate} for age, rate in result.tectonic_rates],
        "basin_type_hint": result.basin_type_hint,
        "step_count": len(result.steps),
        "diagnostics": result.diagnostics,
        "provenance": result.provenance,
        "uncertainty": {
            "realizations": uncertainty_realizations,
            "method": "Monte Carlo (TODO: implement uncertainty propagation)",
            "note": "Uncertainty envelope requires multiple realizations with perturbed inputs",
        },
        "epistemic": {
            "truth_class": "DERIVED",
            "evidence_tag": "DER",
            "not_fact_because": [
                "Depends on paleowater depth estimates (interpreted)",
                "Depends on lithology model parameters (empirical)",
                "Airy isostasy assumes local compensation (simplified)",
                "Porosity-depth curve is exponential approximation",
            ],
        },
    }
