"""
mass_balance.py — Sediment Mass Balance Engine
═══════════════════════════════════════════════
Source-to-sink sediment volume and mass accounting.

Physics: Peters (2012) sediment cycling framework + standard compaction corrections.

The fundamental equation:
  V_source = V_preserved + V_bypassed + V_dissolved + V_compacted_adjustment

Mass balance:
  ρ_source * V_source = ρ_preserved * V_preserved + ρ_bypassed * V_bypassed + ...

Compaction correction:
  V_preserved_decompacted = V_preserved * (1 - φ_avg) / (1 - φ_decompacted)

Peters & Gaines (2012) insight: The Great Unconformity records massive sediment
removal from continental crust — the "source" side of the mass balance.

DITEMPA BUKAN DIBERI — Forged, Not Given.

References:
  - Peters, S.E. (2012) Sediment cycling on continental and oceanic crust. Geology.
  - Peters, S.E. & Gaines, R.R. (2012) Formation of the 'Great Unconformity'. Nature.
  - Husson, J.M. & Peters, S.E. (2017) Atmospheric oxygenation driven by unsteady growth.
  - Sadler, P.M. (1981) Sediment accumulation rates and completeness of stratigraphic sections.
  - Romans, B.W. et al. (2016) Environmental signal propagation in sedimentary systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from geox_core.engines.basin.backstrip import (
    LithologyParams,
)


@dataclass
class SedimentVolume:
    """A sediment volume with provenance and uncertainty."""

    name: str
    volume_km3: float
    area_km2: float
    thickness_m: float
    avg_porosity: float
    avg_density_kg_m3: float
    lithology: str
    age_range_ma: tuple[float, float]  # (older, younger)
    evidence_tag: str = "OBS"  # OBS / DER / INT / SPEC
    uncertainty_pct: float = 20.0  # ± percentage


@dataclass
class SedimentBudget:
    """A complete sediment budget for a basin/region."""

    name: str
    # Source volumes
    source_eroded_km3: float = 0.0
    source_eroded_mass_gt: float = 0.0  # gigatonnes
    source_area_km2: float = 0.0
    source_uplift_m: float = 0.0
    # Sink volumes
    preserved_km3: float = 0.0
    preserved_mass_gt: float = 0.0
    preserved_decompacted_km3: float = 0.0
    bypassed_km3: float = 0.0
    bypassed_mass_gt: float = 0.0
    dissolved_km3: float = 0.0
    dissolved_mass_gt: float = 0.0
    # Balance
    deficit_km3: float = 0.0
    deficit_pct: float = 0.0
    # Metadata
    age_range_ma: tuple[float, float] = (0.0, 0.0)
    evidence_tag: str = "DER"
    uncertainty_pct: float = 25.0


@dataclass
class MassBalanceResult:
    """Complete mass balance analysis result."""

    budget: SedimentBudget
    source_volumes: list[SedimentVolume]
    sink_volumes: list[SedimentVolume]
    compaction_corrections: dict[str, float]
    routing_efficiency: float  # fraction of source that reaches sink
    deficit_analysis: dict[str, Any]
    provenance: dict[str, Any]
    diagnostics: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Core Physics
# ═══════════════════════════════════════════════════════════════════════════════


def compaction_correction(
    volume_km3: float,
    avg_porosity: float,
    lithology: str = "sandstone",
    target_porosity: float | None = None,
) -> dict[str, Any]:
    """Correct a sediment volume for compaction.

    If target_porosity is None, uses surface porosity (full decompaction).

    V_decompacted = V_preserved * (1 - φ_avg) / (1 - φ_surface)

    Returns dict with original and corrected volumes.
    """
    lith = LithologyParams.from_name(lithology)
    phi_surface = target_porosity if target_porosity is not None else lith.phi0

    if avg_porosity >= 1.0:
        avg_porosity = 0.5  # fallback

    # Decompacted volume
    v_decompacted = volume_km3 * (1 - avg_porosity) / (1 - phi_surface)

    return {
        "original_volume_km3": volume_km3,
        "decompacted_volume_km3": v_decompacted,
        "correction_factor": v_decompacted / volume_km3 if volume_km3 > 0 else 1.0,
        "avg_porosity": avg_porosity,
        "surface_porosity": phi_surface,
        "lithology": lithology,
    }


def source_sink_accounting(
    source_eroded_km3: float,
    source_density_kg_m3: float,
    preserved_volumes: list[SedimentVolume],
    bypassed_km3: float = 0.0,
    dissolved_km3: float = 0.0,
    dissolved_density_kg_m3: float = 2700.0,
) -> SedimentBudget:
    """Compute source-to-sink sediment budget.

    The fundamental accounting:
      Source = Preserved + Bypassed + Dissolved + Deficit

    Where deficit is the "missing" volume that cannot be accounted for.
    """
    # Source mass
    source_mass_gt = source_eroded_km3 * source_density_kg_m3 / 1e6  # km³ * kg/m³ / 1e6 = GT

    # Preserved volume and mass
    preserved_total_km3 = sum(v.volume_km3 for v in preserved_volumes)
    preserved_mass = sum(v.volume_km3 * v.avg_density_kg_m3 / 1e6 for v in preserved_volumes)

    # Decompacted preserved volume
    preserved_decompacted = sum(
        compaction_correction(v.volume_km3, v.avg_porosity, v.lithology)["decompacted_volume_km3"] for v in preserved_volumes
    )

    # Bypassed mass
    bypassed_mass = bypassed_km3 * source_density_kg_m3 / 1e6

    # Dissolved mass
    dissolved_mass = dissolved_km3 * dissolved_density_kg_m3 / 1e6

    # Deficit
    accounted_km3 = preserved_total_km3 + bypassed_km3 + dissolved_km3
    deficit_km3 = source_eroded_km3 - accounted_km3
    deficit_pct = (deficit_km3 / source_eroded_km3 * 100) if source_eroded_km3 > 0 else 0.0

    # Age range
    if preserved_volumes:
        age_older = max(v.age_range_ma[0] for v in preserved_volumes)
        age_younger = min(v.age_range_ma[1] for v in preserved_volumes)
    else:
        age_older = 0.0
        age_younger = 0.0

    return SedimentBudget(
        name="sediment_budget",
        source_eroded_km3=source_eroded_km3,
        source_eroded_mass_gt=source_mass_gt,
        preserved_km3=preserved_total_km3,
        preserved_mass_gt=preserved_mass,
        preserved_decompacted_km3=preserved_decompacted,
        bypassed_km3=bypassed_km3,
        bypassed_mass_gt=bypassed_mass,
        dissolved_km3=dissolved_km3,
        dissolved_mass_gt=dissolved_mass,
        deficit_km3=deficit_km3,
        deficit_pct=deficit_pct,
        age_range_ma=(age_older, age_younger),
        evidence_tag="DER",
    )


def compute_mass_balance(
    basin_name: str,
    source_eroded_km3: float,
    source_density_kg_m3: float,
    preserved_volumes: list[SedimentVolume],
    bypassed_km3: float = 0.0,
    dissolved_km3: float = 0.0,
    routing_efficiency: float | None = None,
) -> MassBalanceResult:
    """Complete mass balance analysis for a basin.

    Steps:
    1. Compute source volume and mass
    2. Apply compaction corrections to preserved volumes
    3. Account for bypass and dissolution
    4. Compute deficit
    5. Analyze deficit origin (compaction? erosion? routing? model bias?)

    Returns MassBalanceResult with full accounting.
    """
    diagnostics: list[str] = []

    # Compute budget
    budget = source_sink_accounting(
        source_eroded_km3=source_eroded_km3,
        source_density_kg_m3=source_density_kg_m3,
        preserved_volumes=preserved_volumes,
        bypassed_km3=bypassed_km3,
        dissolved_km3=dissolved_km3,
    )

    # Compaction corrections for each preserved volume
    compaction_corrections: dict[str, float] = {}
    for v in preserved_volumes:
        cc = compaction_correction(v.volume_km3, v.avg_porosity, v.lithology)
        compaction_corrections[v.name] = cc["correction_factor"]

    # Routing efficiency
    if routing_efficiency is None:
        if source_eroded_km3 > 0:
            routing_efficiency = budget.preserved_km3 / source_eroded_km3
        else:
            routing_efficiency = 0.0

    # Deficit analysis
    deficit_analysis: dict[str, Any] = {
        "deficit_km3": budget.deficit_km3,
        "deficit_pct": budget.deficit_pct,
        "possible_causes": [],
    }

    if budget.deficit_pct > 10:
        deficit_analysis["possible_causes"].append(
            "Significant deficit — may indicate bypass to deeper basin, "
            "erosion of preserved section, or model bias in source estimate."
        )
    if budget.deficit_pct > 30:
        deficit_analysis["possible_causes"].append(
            "Large deficit — consider: (1) sediment routing to adjacent basins, "
            "(2) dissolution of carbonate/volatile components, "
            "(3) overestimation of source volume, "
            "(4) underestimation of preserved volume."
        )
    if budget.deficit_pct > 50:
        diagnostics.append(
            "DEFICIT >50% — This is a first-order signal. "
            "The 'missing' sediment must be accounted for before any "
            "interpretation of the mass balance can be trusted."
        )

    # Provenance
    provenance = {
        "method": "source_to_sink_mass_balance",
        "reference": "Peters (2012), Peters & Gaines (2012), Husson & Peters (2017)",
        "basin_name": basin_name,
        "source_volume_km3": source_eroded_km3,
        "source_density_kg_m3": source_density_kg_m3,
        "preserved_count": len(preserved_volumes),
        "bypassed_km3": bypassed_km3,
        "dissolved_km3": dissolved_km3,
        "routing_efficiency": routing_efficiency,
    }

    return MassBalanceResult(
        budget=budget,
        source_volumes=[],  # caller provides
        sink_volumes=preserved_volumes,
        compaction_corrections=compaction_corrections,
        routing_efficiency=routing_efficiency,
        deficit_analysis=deficit_analysis,
        provenance=provenance,
        diagnostics=diagnostics,
    )


def estimate_erosion_volume(
    area_km2: float,
    erosion_rate_m_myr: float,
    duration_myr: float,
    rock_density_kg_m3: float = 2650.0,
) -> dict[str, float]:
    """Estimate eroded sediment volume from source area parameters.

    V = area * erosion_rate * duration
    Mass = V * density
    """
    volume_km3 = area_km2 * erosion_rate_m_myr * duration_myr / 1e3  # m*km² -> km³
    mass_gt = volume_km3 * rock_density_kg_m3 / 1e6

    return {
        "volume_km3": volume_km3,
        "mass_gt": mass_gt,
        "area_km2": area_km2,
        "erosion_rate_m_myr": erosion_rate_m_myr,
        "duration_myr": duration_myr,
        "average_uplift_m": erosion_rate_m_myr * duration_myr,
    }
