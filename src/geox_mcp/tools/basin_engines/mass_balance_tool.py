"""
geox_sediment_mass_balance — Sediment Mass Balance MCP Tool
════════════════════════════════════════════════════════════
Source-to-sink sediment volume and mass accounting.

Physics: Peters (2012) sediment cycling framework + standard compaction corrections.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any


async def geox_sediment_mass_balance(
    basin_name: str,
    source_eroded_km3: float,
    source_density_kg_m3: float = 2650.0,
    preserved_volumes: list[dict[str, Any]] | None = None,
    bypassed_km3: float = 0.0,
    dissolved_km3: float = 0.0,
    routing_efficiency: float | None = None,
) -> dict[str, Any]:
    """Compute source-to-sink sediment mass balance with uncertainty.

    The fundamental accounting:
      V_source = V_preserved + V_bypassed + V_dissolved + V_deficit

    Compaction corrections applied automatically using lithology-specific
    porosity-depth curves.

    Args:
        basin_name: Basin identifier
        source_eroded_km3: Total volume eroded from source area (km³)
        source_density_kg_m3: Density of source rock (kg/m³, default 2650)
        preserved_volumes: List of {name, volume_km3, area_km2, thickness_m, avg_porosity,
                           avg_density_kg_m3, lithology, age_range_ma, uncertainty_pct}
        bypassed_km3: Volume bypassing the basin (km³)
        dissolved_km3: Volume dissolved (km³)
        routing_efficiency: Override routing efficiency (0-1)

    Returns:
        MassBalanceResult with budget, compaction corrections, routing efficiency,
        deficit analysis, and provenance.

    DER — Derived from volume accounting. Not a direct measurement.
    """
    from geox_core.engines.basin.mass_balance import (
        SedimentVolume,
        compute_mass_balance,
    )

    # Build sediment volumes
    volumes: list[SedimentVolume] = []
    for v in preserved_volumes or []:
        age_range = v.get("age_range_ma", [0.0, 0.0])
        if isinstance(age_range, list) and len(age_range) == 2:
            age_tuple = (age_range[0], age_range[1])
        else:
            age_tuple = (0.0, 0.0)

        sv = SedimentVolume(
            name=v.get("name", "unnamed"),
            volume_km3=v.get("volume_km3", 0.0),
            area_km2=v.get("area_km2", 0.0),
            thickness_m=v.get("thickness_m", 0.0),
            avg_porosity=v.get("avg_porosity", 0.2),
            avg_density_kg_m3=v.get("avg_density_kg_m3", 2200.0),
            lithology=v.get("lithology", "sandstone"),
            age_range_ma=age_tuple,
            uncertainty_pct=v.get("uncertainty_pct", 20.0),
        )
        volumes.append(sv)

    # Run mass balance
    result = compute_mass_balance(
        basin_name=basin_name,
        source_eroded_km3=source_eroded_km3,
        source_density_kg_m3=source_density_kg_m3,
        preserved_volumes=volumes,
        bypassed_km3=bypassed_km3,
        dissolved_km3=dissolved_km3,
        routing_efficiency=routing_efficiency,
    )

    return {
        "success": True,
        "basin_name": basin_name,
        "budget": {
            "source_eroded_km3": result.budget.source_eroded_km3,
            "source_eroded_mass_gt": result.budget.source_eroded_mass_gt,
            "preserved_km3": result.budget.preserved_km3,
            "preserved_mass_gt": result.budget.preserved_mass_gt,
            "preserved_decompacted_km3": result.budget.preserved_decompacted_km3,
            "bypassed_km3": result.budget.bypassed_km3,
            "bypassed_mass_gt": result.budget.bypassed_mass_gt,
            "dissolved_km3": result.budget.dissolved_km3,
            "dissolved_mass_gt": result.budget.dissolved_mass_gt,
            "deficit_km3": result.budget.deficit_km3,
            "deficit_pct": result.budget.deficit_pct,
        },
        "compaction_corrections": result.compaction_corrections,
        "routing_efficiency": result.routing_efficiency,
        "deficit_analysis": result.deficit_analysis,
        "diagnostics": result.diagnostics,
        "provenance": result.provenance,
        "epistemic": {
            "truth_class": "DERIVED",
            "evidence_tag": "DER",
            "not_fact_because": [
                "Source volume depends on erosion estimate (model-dependent)",
                "Preserved volume depends on mapping and isopach quality",
                "Bypass fraction is rarely measured directly",
                "Dissolution estimate depends on lithology assumptions",
                "Compaction correction uses empirical porosity-depth curves",
            ],
        },
    }
