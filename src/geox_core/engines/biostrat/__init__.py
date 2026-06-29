"""
geox_core.engines.biostrat — Biostratigraphy Zonation Engine
═════════════════════════════════════════════════════════════
Automated zonation using conodont and foraminifera schemes.
Provides age constraints and facies context for Physics13State.

Physics: Biostratigraphy doesn't measure physics directly — it constrains
TIME (age) and FACIES (depositional environment), which bound:
  - φ (porosity): facies-dependent
  - Vp/Vs (velocity ratio): lithology-dependent
  - T (temperature): burial history
  - P (pressure): compaction state

Constitutional: F2 (evidence-labeled), F9 (fossils are data, not interpretation).
Author: FORGE (000Ω) | DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

import numpy as np

from geox_core.physics.state import Physics13State

logger = logging.getLogger("geox.biostrat")


# ─── Zonation Schemes ───────────────────────────────────────────────────────


class FossilGroup(str, Enum):
    CONODONT = "conodont"
    FORAMINIFERA = "foraminifera"
    NANNOFOSSIL = "nannofossil"
    PALYNOMORPH = "palynomorph"


class ZoneType(str, Enum):
    RANGE = "range"           # total range zone
    INTERVAL = "interval"     # interval zone
    ASSEMBLAGE = "assemblage" # assemblage zone
    ABUNDANCE = "abundance"   # abundance zone


@dataclass
class BiostratZone:
    """A single biostratigraphic zone."""
    zone_name: str
    fossil_group: FossilGroup
    zone_type: ZoneType
    key_species: list[str]
    top_age_ma: float          # youngest occurrence (Ma)
    bottom_age_ma: float       # oldest occurrence (Ma)
    facies_hint: str = ""      # depositional environment
    confidence: float = 0.8    # 0-1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "fossil_group": self.fossil_group.value,
            "zone_type": self.zone_type.value,
            "key_species": self.key_species,
            "top_age_ma": self.top_age_ma,
            "bottom_age_ma": self.bottom_age_ma,
            "facies_hint": self.facies_hint,
            "confidence": self.confidence,
        }


@dataclass
class FossilOccurrence:
    """A fossil occurrence in a well/core sample."""
    species: str
    fossil_group: FossilGroup
    depth_m: float
    abundance: int = 1         # count
    preservation: str = "moderate"  # good/moderate/poor
    identification_method: str = "visual"  # visual/SEM/microCT
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ZonationResult:
    """Result of biostratigraphic zonation."""
    well_id: str
    zones: list[BiostratZone]
    depth_intervals: list[tuple[float, float]]  # (top_m, bottom_m)
    age_model: np.ndarray | None     # depth → age interpolation
    depth_axis: np.ndarray | None
    confidence_curve: np.ndarray | None
    facies_constraints: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "well_id": self.well_id,
            "n_zones": len(self.zones),
            "zones": [z.to_dict() for z in self.zones],
            "depth_intervals": self.depth_intervals,
            "n_facies_constraints": len(self.facies_constraints),
            "metadata": self.metadata,
        }


# ─── Conodont Zonation Database ─────────────────────────────────────────────

CONODONT_ZONES: list[BiostratZone] = [
    # Carboniferous-Permian boundary zones (from Copilot deep research)
    BiostratZone(
        zone_name="Idiognathoides sinuatus Zone",
        fossil_group=FossilGroup.CONODONT,
        zone_type=ZoneType.RANGE,
        key_species=["Idiognathoides sinuatus", "Mesogondolella clarki", "Gondolella gymna"],
        top_age_ma=307.0,
        bottom_age_ma=315.0,
        facies_hint="shallow_marine_carbonate",
        confidence=0.85,
    ),
    BiostratZone(
        zone_name="Streptognathodus vitali Zone",
        fossil_group=FossilGroup.CONODONT,
        zone_type=ZoneType.RANGE,
        key_species=["Streptognathodus vitali", "Gondolella postdenuda"],
        top_age_ma=303.0,
        bottom_age_ma=307.0,
        facies_hint="open_marine_shelf",
        confidence=0.82,
    ),
    BiostratZone(
        zone_name="Streptognathodus bellus Zone",
        fossil_group=FossilGroup.CONODONT,
        zone_type=ZoneType.RANGE,
        key_species=["Streptognathodus bellus", "Streptognathodus elongatus", "Streptognathodus conjunctus"],
        top_age_ma=299.0,
        bottom_age_ma=303.0,
        facies_hint="deep_marine_pelagic",
        confidence=0.80,
    ),
    BiostratZone(
        zone_name="Streptognathodus isolatus Zone (GSSP)",
        fossil_group=FossilGroup.CONODONT,
        zone_type=ZoneType.INTERVAL,
        key_species=["Streptognathodus isolatus"],
        top_age_ma=295.0,
        bottom_age_ma=299.0,
        facies_hint="pelagic_panthalassa",
        confidence=0.95,
        metadata={"gssp": True, "event": "Carboniferous-Permian boundary"},
    ),
    BiostratZone(
        zone_name="Streptognathodus constrictus Zone",
        fossil_group=FossilGroup.CONODONT,
        zone_type=ZoneType.RANGE,
        key_species=["Streptognathodus constrictus", "Mesogondolella belladontae", "Mesogondolella dentiseparata"],
        top_age_ma=290.0,
        bottom_age_ma=295.0,
        facies_hint="shallow_marine_mixed",
        confidence=0.78,
    ),
    BiostratZone(
        zone_name="Mesogondolella bisselli Zone",
        fossil_group=FossilGroup.CONODONT,
        zone_type=ZoneType.RANGE,
        key_species=["Mesogondolella bisselli", "Mesogondolella intermedia", "Sweetognathus asymmetricus"],
        top_age_ma=280.0,
        bottom_age_ma=290.0,
        facies_hint="carbonate_platform",
        confidence=0.75,
    ),
]

# ─── Foraminifera Zonation Database ─────────────────────────────────────────

FORAMINIFERA_ZONES: list[BiostratZone] = [
    BiostratZone(
        zone_name="Lepidocyclina-Operculina Assemblage",
        fossil_group=FossilGroup.FORAMINIFERA,
        zone_type=ZoneType.ASSEMBLAGE,
        key_species=["Lepidocyclina", "Operculina", "Miogypsina"],
        top_age_ma=18.0,
        bottom_age_ma=28.0,
        facies_hint="carbonate_platform_reef",
        confidence=0.80,
    ),
    BiostratZone(
        zone_name="Globigerina-Zone (Planktonic)",
        fossil_group=FossilGroup.FORAMINIFERA,
        zone_type=ZoneType.RANGE,
        key_species=["Globigerina", "Globorotalia", "Orbulina"],
        top_age_ma=10.0,
        bottom_age_ma=20.0,
        facies_hint="open_marine_pelagic",
        confidence=0.85,
    ),
    BiostratZone(
        zone_name="Nummulites Assemblage",
        fossil_group=FossilGroup.FORAMINIFERA,
        zone_type=ZoneType.ASSEMBLAGE,
        key_species=["Nummulites", "Assilina", "Alveolina"],
        top_age_ma=33.0,
        bottom_age_ma=55.0,
        facies_hint="shallow_marine_carbonate",
        confidence=0.78,
    ),
    BiostratZone(
        zone_name="Textularia-Ammobaculites Assemblage",
        fossil_group=FossilGroup.FORAMINIFERA,
        zone_type=ZoneType.ASSEMBLAGE,
        key_species=["Textularia", "Ammobaculites", "Haplophragmoides"],
        top_age_ma=65.0,
        bottom_age_ma=100.0,
        facies_hint="brackish_marginal_marine",
        confidence=0.70,
    ),
]


# ─── Zonation Engine ────────────────────────────────────────────────────────


def match_species_to_zones(
    occurrences: list[FossilOccurrence],
    zone_database: list[BiostratZone] | None = None,
) -> list[BiostratZone]:
    """
    Match fossil occurrences to known biostratigraphic zones.

    Returns list of matching zones sorted by age.
    """
    if zone_database is None:
        zone_database = CONODONT_ZONES + FORAMINIFERA_ZONES

    species_found = set()
    for occ in occurrences:
        species_found.add(occ.species.lower())

    matched_zones = []
    for zone in zone_database:
        zone_species = {s.lower() for s in zone.key_species}
        if species_found & zone_species:  # intersection
            matched_zones.append(zone)

    # Sort by top age (youngest first)
    matched_zones.sort(key=lambda z: z.top_age_ma)
    return matched_zones


def assign_zones_to_well(
    occurrences: list[FossilOccurrence],
    well_id: str = "unknown",
    zone_database: list[BiostratZone] | None = None,
) -> ZonationResult:
    """
    Assign biostratigraphic zones to a well based on fossil occurrences.

    Returns depth intervals, age model, and facies constraints.
    """
    matched_zones = match_species_to_zones(occurrences, zone_database)

    if not matched_zones:
        return ZonationResult(
            well_id=well_id,
            zones=[],
            depth_intervals=[],
            age_model=None,
            depth_axis=None,
            confidence_curve=None,
            facies_constraints=[],
            metadata={"status": "NO_MATCHES", "n_occurrences": len(occurrences)},
        )

    # Sort occurrences by depth
    sorted_occ = sorted(occurrences, key=lambda o: o.depth_m)

    # Build depth intervals
    depth_intervals = []
    for zone in matched_zones:
        # Find depths where this zone's species occur
        zone_depths = []
        for occ in sorted_occ:
            if occ.species.lower() in {s.lower() for s in zone.key_species}:
                zone_depths.append(occ.depth_m)

        if zone_depths:
            top_m = min(zone_depths)
            bottom_m = max(zone_depths)
            depth_intervals.append((top_m, bottom_m))
        else:
            depth_intervals.append((0, 0))

    # Build age model (linear interpolation between zone boundaries)
    all_depths = sorted(set(d for top, bot in depth_intervals for d in [top, bot] if d > 0))
    if len(all_depths) >= 2:
        depth_axis = np.linspace(min(all_depths), max(all_depths), 100)
        # Interpolate ages
        age_points = []
        depth_points = []
        for i, zone in enumerate(matched_zones):
            if i < len(depth_intervals) and depth_intervals[i][0] > 0:
                depth_points.append(depth_intervals[i][0])
                age_points.append(zone.top_age_ma)
                depth_points.append(depth_intervals[i][1])
                age_points.append(zone.bottom_age_ma)

        if len(depth_points) >= 2:
            # Sort by depth
            sorted_pairs = sorted(zip(depth_points, age_points))
            dp_sorted = [p[0] for p in sorted_pairs]
            ap_sorted = [p[1] for p in sorted_pairs]
            age_model = np.interp(depth_axis, dp_sorted, ap_sorted)
        else:
            age_model = np.full_like(depth_axis, matched_zones[0].top_age_ma)
    else:
        depth_axis = np.array(all_depths) if all_depths else np.array([0])
        age_model = np.full_like(depth_axis, matched_zones[0].top_age_ma)

    # Build facies constraints
    facies_constraints = []
    for zone, interval in zip(matched_zones, depth_intervals):
        if zone.facies_hint:
            facies_constraints.append({
                "depth_top_m": interval[0],
                "depth_bottom_m": interval[1],
                "facies": zone.facies_hint,
                "zone": zone.zone_name,
                "confidence": zone.confidence,
            })

    # Confidence curve
    confidence_curve = np.ones_like(depth_axis) * 0.5  # default
    for zone, interval in zip(matched_zones, depth_intervals):
        mask = (depth_axis >= interval[0]) & (depth_axis <= interval[1])
        confidence_curve[mask] = zone.confidence

    return ZonationResult(
        well_id=well_id,
        zones=matched_zones,
        depth_intervals=depth_intervals,
        age_model=age_model,
        depth_axis=depth_axis,
        confidence_curve=confidence_curve,
        facies_constraints=facies_constraints,
        metadata={
            "n_occurrences": len(occurrences),
            "n_zones_matched": len(matched_zones),
            "age_range_ma": [
                float(min(z.top_age_ma for z in matched_zones)),
                float(max(z.bottom_age_ma for z in matched_zones)),
            ],
            "epistemic_rung": 3,
            "note": "Biostratigraphic zonation. Age constraints are INTERPRETED_LOCAL.",
        },
    )


# ─── Facies → Physics9 Constraints ─────────────────────────────────────────


def facies_to_physics9_constraints(
    facies: str,
    base_state: Physics13State | None = None,
) -> dict[str, Any]:
    """
    Map facies interpretation to Physics9 parameter constraints.

    Returns permissible ranges for porosity, Vp/Vs, temperature, pressure.
    """
    from geox_core.physics.state import Physics13State

    FACIES_BOUNDS = {
        "shallow_marine_carbonate": {"phi": (0.05, 0.30), "vp_vs": (1.6, 2.0), "rho_e": (50, 500)},
        "deep_marine_pelagic": {"phi": (0.30, 0.45), "vp_vs": (1.8, 2.5), "rho_e": (0.5, 10)},
        "carbonate_platform": {"phi": (0.03, 0.25), "vp_vs": (1.6, 1.9), "rho_e": (100, 2000)},
        "carbonate_platform_reef": {"phi": (0.10, 0.35), "vp_vs": (1.6, 1.9), "rho_e": (50, 1000)},
        "shallow_marine_mixed": {"phi": (0.10, 0.35), "vp_vs": (1.7, 2.2), "rho_e": (5, 100)},
        "open_marine_shelf": {"phi": (0.15, 0.40), "vp_vs": (1.7, 2.3), "rho_e": (1, 50)},
        "brackish_marginal_marine": {"phi": (0.20, 0.45), "vp_vs": (1.8, 2.5), "rho_e": (1, 20)},
        "pelagic_panthalassa": {"phi": (0.30, 0.45), "vp_vs": (1.9, 2.5), "rho_e": (0.5, 5)},
    }

    bounds = FACIES_BOUNDS.get(facies, {"phi": (0.02, 0.45), "vp_vs": (1.5, 3.0), "rho_e": (0.1, 1e6)})

    return {
        "facies": facies,
        "constraints": bounds,
        "note": "Facies-derived bounds. Use as soft constraints in joint inversion.",
    }


# ─── Age → Burial History Constraints ───────────────────────────────────────


def age_to_burial_constraints(
    age_ma: float,
    present_depth_m: float,
    geothermal_gradient_c_km: float = 30.0,
    surface_temperature_c: float = 25.0,
) -> dict[str, Any]:
    """
    From biostratigraphic age and present depth, estimate burial history constraints.

    Returns estimated maximum temperature, pressure, and maturity.
    """
    # Simple burial model: assume linear subsidence
    depth_km = present_depth_m / 1000.0
    T_estimated = surface_temperature_c + geothermal_gradient_c_km * depth_km
    P_estimated = depth_km * 9.81 * 2300.0 / 1e6  # MPa (lithostatic, ρ=2300)

    # Simple maturity proxy (TTI-like)
    # Each 10°C doubling of reaction rate
    tti = age_ma * 2 ** ((T_estimated - 100) / 10)
    if tti < 1:
        maturity = "IMMATURE"
    elif tti < 100:
        maturity = "OIL_WINDOW"
    elif tti < 1000:
        maturity = "GAS_WINDOW"
    else:
        maturity = "OVERMATURE"

    return {
        "age_ma": age_ma,
        "present_depth_m": present_depth_m,
        "estimated_temperature_c": round(T_estimated, 1),
        "estimated_pressure_mpa": round(P_estimated, 2),
        "tti": round(tti, 2),
        "maturity": maturity,
        "physics9_constraints": {
            "T_range_K": (T_estimated + 273.15 - 20, T_estimated + 273.15 + 20),
            "P_range_Pa": (P_estimated * 1e6 * 0.8, P_estimated * 1e6 * 1.2),
        },
        "note": "Burial history estimate from age + depth. Use as soft constraints.",
    }
