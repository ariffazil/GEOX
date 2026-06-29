"""
biostrat_constraint.py — W13+ Phase C forge: Biostratigraphy constraints.

Per strategic vision: biostratigraphy (conodont/foram zonation) imposes
time-facies constraints on (φ, Vp/Vs, T, P) at the cell level.

Mechanism:
  - A biostratigraphic zone has a known age range and a known
    paleo-environment (depositional facies).
  - Each zone constrains which Earth material catalog entries are
    admissible for that cell.
  - This prunes the joint inversion prior.

This is a heuristic engine — not a full biostratigraphic classifier
(which is its own ML field). It uses a small built-in zone catalog
that operators can extend.

DITEMPA BUKAN DIBEI — time-facies constraint is forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Literal, Optional

from geox_core.physics.state import EARTH_MATERIAL_CATALOG, Physics13State


# ───────────────────────────── ZONE CATALOG ───────────────────────────────────────
DepositionalEnvironment = Literal[
    "marine_shelf", "deep_marine", "reef", "sabkha", "fluvial",
    "deltaic", "lacustrine", "volcaniclastic", "basement",
]


@dataclass(frozen=True)
class BiostratZone:
    """One biostratigraphic zone."""

    name: str
    age_top_ma: float  # age at top of zone (Ma)
    age_base_ma: float  # age at base of zone (Ma)
    environment: DepositionalEnvironment
    admissible_materials: tuple[str, ...]
    # Expected porosity range for the zone (heuristic)
    phi_min: float = 0.05
    phi_max: float = 0.40
    # Expected Vp/Vs ratio range
    vpvs_min: float = 1.5
    vpvs_max: float = 3.0


# Built-in zone catalog (extendable). Examples based on common
# geological intervals; not exhaustive.
BUILTIN_ZONES: list[BiostratZone] = [
    BiostratZone(
        name="Quaternary_Alluvium",
        age_top_ma=0.0, age_base_ma=2.6,
        environment="fluvial",
        admissible_materials=("Sandstone", "Shale"),
        phi_min=0.15, phi_max=0.40,
        vpvs_min=1.7, vpvs_max=2.5,
    ),
    BiostratZone(
        name="Miocene_Reef",
        age_top_ma=5.3, age_base_ma=23.0,
        environment="reef",
        admissible_materials=("Limestone", "Dolomite"),
        phi_min=0.05, phi_max=0.30,
        vpvs_min=1.8, vpvs_max=2.2,
    ),
    BiostratZone(
        name="Cretaceous_Shale",
        age_top_ma=66.0, age_base_ma=145.0,
        environment="marine_shelf",
        admissible_materials=("Shale", "Limestone"),
        phi_min=0.05, phi_max=0.25,
        vpvs_min=1.7, vpvs_max=2.4,
    ),
    BiostratZone(
        name="Jurassic_Sabkha",
        age_top_ma=145.0, age_base_ma=201.0,
        environment="sabkha",
        admissible_materials=("Anhydrite", "Salt", "Dolomite"),
        phi_min=0.01, phi_max=0.15,
        vpvs_min=1.7, vpvs_max=2.0,
    ),
    BiostratZone(
        name="Carboniferous_Coal",
        age_top_ma=298.9, age_base_ma=358.9,
        environment="deltaic",
        admissible_materials=("Coal", "Shale", "Sandstone"),
        phi_min=0.05, phi_max=0.30,
        vpvs_min=1.6, vpvs_max=2.6,
    ),
    BiostratZone(
        name="Precambrian_Basement",
        age_top_ma=541.0, age_base_ma=4000.0,
        environment="basement",
        admissible_materials=("Basement",),
        phi_min=0.0, phi_max=0.10,
        vpvs_min=1.6, vpvs_max=1.9,
    ),
]


# ───────────────────────────── CONSTRAINT EVALUATION ──────────────────────────────
@dataclass(frozen=True)
class BiostratConstraintResult:
    """Result of biostrat constraint on a cell state."""

    zone_name: str
    zone_admissible_materials: tuple[str, ...]
    cell_material_match: Optional[str]
    is_material_admissible: bool
    is_phi_in_range: bool
    is_vpvs_in_range: bool
    is_consistent: bool
    notes: list[str] = field(default_factory=list)


def evaluate_biostrat_constraint(
    state: Physics13State,
    age_ma: float,
    zones: Optional[list[BiostratZone]] = None,
) -> BiostratConstraintResult:
    """Check whether a Physics13State is admissible for a biostrat zone at given age.

    Resolution logic:
      1. Find the zone whose age range contains `age_ma`. (If multiple match,
         pick the one with the smallest age interval.)
      2. Identify the catalog material closest to `state` by Euclidean distance
         in (ρ, Vp, Vs, φ) space.
      3. Check whether that material is in the zone's admissible list.
      4. Check whether φ and Vp/Vs are inside the zone's expected ranges.
    """
    if zones is None:
        zones = BUILTIN_ZONES
    elif isinstance(zones, BiostratZone):
        zones = [zones]

    # Find matching zone. Convention: age_top_ma < age_base_ma (younger at top).
    matching = [z for z in zones if z.age_top_ma <= age_ma <= z.age_base_ma]
    if not matching:
        return BiostratConstraintResult(
            zone_name="<none>",
            zone_admissible_materials=(),
            cell_material_match=None,
            is_material_admissible=False,
            is_phi_in_range=False,
            is_vpvs_in_range=False,
            is_consistent=False,
            notes=[f"No biostrat zone matches age {age_ma} Ma."],
        )
    zone = min(matching, key=lambda z: z.age_top_ma - z.age_base_ma)

    # Find closest material in catalog
    best_name = None
    best_dist = float("inf")
    for name, ref in EARTH_MATERIAL_CATALOG.items():
        d = math.sqrt(
            ((state.rho - ref.rho) / 200.0) ** 2
            + ((state.vp - ref.vp) / 500.0) ** 2
            + ((state.vs - ref.vs) / 200.0) ** 2
            + ((state.phi - ref.phi) / 0.1) ** 2
        )
        if d < best_dist:
            best_dist = d
            best_name = name

    is_material = best_name in zone.admissible_materials
    is_phi = zone.phi_min <= state.phi <= zone.phi_max
    vpvs = state.vp / max(state.vs, 1e-6)
    is_vpvs = zone.vpvs_min <= vpvs <= zone.vpvs_max
    is_consistent = is_material and is_phi and is_vpvs

    notes = []
    if not is_material:
        notes.append(
            f"Cell material '{best_name}' not in zone admissible list "
            f"{zone.admissible_materials}."
        )
    if not is_phi:
        notes.append(
            f"Porosity φ={state.phi:.3f} outside zone range "
            f"[{zone.phi_min:.3f}, {zone.phi_max:.3f}]."
        )
    if not is_vpvs:
        notes.append(
            f"Vp/Vs={vpvs:.3f} outside zone range "
            f"[{zone.vpvs_min:.3f}, {zone.vpvs_max:.3f}]."
        )
    if is_consistent:
        notes.append("Cell is admissible for this biostrat zone.")

    return BiostratConstraintResult(
        zone_name=zone.name,
        zone_admissible_materials=zone.admissible_materials,
        cell_material_match=best_name,
        is_material_admissible=is_material,
        is_phi_in_range=is_phi,
        is_vpvs_in_range=is_vpvs,
        is_consistent=is_consistent,
        notes=notes,
    )


__all__ = [
    "DepositionalEnvironment",
    "BiostratZone",
    "BiostratConstraintResult",
    "BUILTIN_ZONES",
    "evaluate_biostrat_constraint",
]
