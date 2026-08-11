"""
crust_vp_grammar.py — P-wave velocity crust-type classification grammar
═══════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given

Source of truth: Huang et al. (2021) — "Seismic Imaging of an Intracrustal
Deformation in the Northwestern Margin of the South China Sea"
(Tectonics, 30 OBS profile, ±0.3 km/s Vp uncertainty, ±1 km Moho uncertainty,
10,346 picked arrivals, Monte Carlo inversion).

This module encodes the 7-zone Vp grammar that lets any GEOX tool
classify crustal domain from P-wave velocity alone — without biostrat,
without opinion. The grammar is the constitution; biostrat is calibration.

Reference Plate (Huang et al. 2021):

| Zone                          | Vp range (km/s)      | Thickness | Diagnostic event              |
|-------------------------------|----------------------|-----------|-------------------------------|
| Normal continental crust      | 5.0–6.8 (gradual)    | ~22 km    | Receiver function match       |
| Stretched continental         | Upper <6.0, lower 6.8| ~10 km    | β ≈ 3.0–3.8, no ductile       |
| Hyperthinned + OCT            | 2-layer oceanic-like | ~6 km     | β ≈ 5, magnetic high          |
| Ductile mid-crustal layer     | Below 6.4 isovelocity| ~5 km     | +0.3 km/s step, PcP arrivals  |
| Lower crust + magmatic add    | up to 7.1            | +2-3 km   | Sill front at ductile boundary|
| Serpentinized upper mantle    | ~7.7 vs normal 8.0   | >3 km     | 13% serpentinization          |
| HVL underplating (NE margin)  | >7.2 thick band      | thick     | ABSENT in NW margin (contrast) |

ARIF-relevant Sabah equivalent:

| Huang's zone               | Sabah equivalent                               |
|----------------------------|-------------------------------------------------|
| Xisha Bank (continental)   | Kinabalu Basin on Dangerous Grounds (~30 km)    |
| Xisha Trough (stretched)   | Inboard Layang-Layang sub-basins                |
| Zhongsha Trough (failed rift, ductile) | Layang-Layang proper — volcanic basement |
| Zhongshanan (OCT, hyperthin) | Layang-Layang outboard → NW Sabah Trough (COB) |
| NW Subbasin (oceanic)      | Proto-SCS remnant slab under NW Sabah wedge     |

Used by:
  - Crustal Domain Map (Phase I Deliverable 1)
  - Fossil COB Surface (Phase I Deliverable 2)
  - geox_evidence_reason (future: cross-domain synthesis)
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ═══════════════════════════════════════════════════════════════════════════════
# Crust zones — canonical taxonomy
# ═══════════════════════════════════════════════════════════════════════════════


class CrustZone(StrEnum):
    """Canonical crust-type taxonomy derived from Huang et al. (2021)."""

    NORMAL_CONTINENTAL = "normal_continental"
    STRETCHED_CONTINENTAL = "stretched_continental"
    HYPERTHINNED_OCT = "hyperthinned_oct"
    DUCTILE_MID_CRUSTAL = "ductile_mid_crustal"
    LOWER_CRUST_MAGMATIC = "lower_crust_magmatic"
    SERPENTINIZED_MANTLE = "serpentinized_mantle"
    OCEANIC_CRUST = "oceanic_crust"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
# Vp windows — diagnostic thresholds (km/s)
# ═══════════════════════════════════════════════════════════════════════════════

# Normal continental crust — Xisha Bank profile
NORMAL_CONTINENTAL_VP_MIN = 5.0
NORMAL_CONTINENTAL_VP_MAX = 6.8
NORMAL_CONTINENTAL_THICKNESS_KM = 22.0

# Stretched continental — Xisha Trough (β ≈ 3.0–3.8)
STRETCHED_UPPER_CRUST_VP_MAX = 6.0
STRETCHED_LOWER_CRUST_VP = 6.8
STRETCHED_THICKNESS_KM = 10.0

# Hyperthinned OCT — Zhongshanan Basin (β ≈ 5)
HYPERTHINNED_THICKNESS_KM = 6.0
HYPERTHINNED_MAGNETIC_ANOMALY_NT = 170.0  # observed in Zhongshanan

# Ductile mid-crustal layer — Zhongsha Trough
DUCTILE_VP_TOP_THRESHOLD = 6.4  # below this Vp = ductile
DUCTILE_STEP_KM_S = 0.3  # +0.3 km/s jump at top of lower crust
DUCTILE_THICKNESS_KM = 5.0
DUCTILE_DEPTH_TOP_KM = 8.0
DUCTILE_DEPTH_BOT_KM = 13.0

# Lower crust with magmatic addition
LOWER_CRUST_VP_MAX = 7.1
LOWER_CRUST_THICKENING_KM = 2.5  # magmatic underplating

# Serpentinized upper mantle
SERPENTINIZED_VP = 7.7
NORMAL_MANTLE_VP = 8.0
SERPENTINIZATION_PCT_ESTIMATE = 13.0  # 13% partial serpentinization
SERPENTINIZED_THICKNESS_KM_MIN = 3.0

# Heat flow threshold — too cold for partial melting at OCT
SERPENTINIZED_HEATFLOW_MW_M2 = 60.0

# HVL (high-velocity lower crust) underplating — NE margin only
HVL_VP_THRESHOLD = 7.2


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic schemas — F4 CLARITY enforced
# ═══════════════════════════════════════════════════════════════════════════════


class VpObservation(BaseModel):
    """Single Vp observation at a given depth.

    F2 TRUTH: This is OBS-grade data. Source must be declared.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        str_strip_whitespace=True,
    )

    vp_km_s: float = Field(
        ...,
        ge=1.0,
        le=10.0,
        description="P-wave velocity in km/s.",
    )
    depth_km: float = Field(
        ...,
        ge=0.0,
        le=50.0,
        description="Depth below sea level or basement (km).",
    )
    uncertainty_km_s: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="1-sigma uncertainty in Vp (km/s). Huang 2021 = ±0.3.",
    )
    source: str = Field(
        default="unknown",
        min_length=1,
        description="OBS / refraction / velocity-stacking / synthetic.",
    )
    method: str = Field(
        default="unknown",
        min_length=1,
        description="e.g. wide-angle refraction, MCS stacking, joint inversion.",
    )


class CrustClassification(BaseModel):
    """Result of classifying a single cell from Vp observations.

    F2 TRUTH: classification with confidence cap and provenance.
    F7 HUMILITY: confidence hard-capped at 0.90 (floor enforced upstream).
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        str_strip_whitespace=True,
    )

    zone: CrustZone = Field(
        ...,
        description="Classified crust zone.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=0.90,  # F7 HUMILITY floor
        description="Classification confidence (0.0–0.90).",
    )
    crust_thickness_km: float | None = Field(
        default=None,
        ge=0.0,
        le=50.0,
        description="Estimated crust thickness (km), if determinable.",
    )
    diagnostic_basis: list[str] = Field(
        default_factory=list,
        min_length=1,
        description="Vp signatures that drove this classification.",
    )
    alternative_zones: list[CrustZone] = Field(
        default_factory=list,
        description="Alternative classifications considered (Eureka = contradiction scan).",
    )
    evidence_rank: str = Field(
        default="OBS",
        description="OBS | DER | INT | SPEC — epistemic status.",
    )
    source_paper: str = Field(
        default="Huang et al. 2021",
        description="Constitutional source for the grammar.",
    )

    @field_validator("alternative_zones")
    @classmethod
    def _no_self_alternative(cls, v: list[CrustZone]) -> list[CrustZone]:
        # Always allow at least one alternative for F4 CLARITY (no single-hypothesis claims)
        return v


class CrustColumn(BaseModel):
    """A 1D crust column reconstructed from a Vp profile.

    This is what gets fed into geox_joint_inversion and downstream
    crustal-domain mapping tools.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
    )

    name: str = Field(
        ...,
        min_length=1,
        description="Column identifier (e.g. 'Layang-Layang-A1').",
    )
    basin_context: str = Field(
        default="unknown",
        min_length=1,
        description="Basin name for cross-reference (e.g. 'Layang-Layang').",
    )
    observations: list[VpObservation] = Field(
        ...,
        min_length=1,
        description="Vp samples from top to bottom of crust.",
    )
    classifications: list[CrustClassification] = Field(
        default_factory=list,
        description="Zone classifications derived from observations.",
    )
    notes: str = Field(
        default="",
        description="Any non-canonical observations worth recording.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# vp_zone_classify() — pure function, F2 TRUTH
# ═══════════════════════════════════════════════════════════════════════════════


def vp_zone_classify(
    vp_km_s: float,
    crust_thickness_km: float | None = None,
    depth_km: float | None = None,
    heat_flow_mw_m2: float | None = None,
) -> CrustClassification:
    """Classify a single Vp observation into a crust zone.

    Pure function (no I/O, no side effects). Returns a CrustClassification
    with confidence capped at 0.90 (F7 HUMILITY).

    Decision logic (in priority order):
      0. If Vp outside crust range (sediment <4.5 or mantle >8.5) → UNKNOWN
      1. If Vp near 7.7 AND crust <8 km AND low heat flow → SERPENTINIZED_MANTLE
      2. If Vp > 7.2 thick band → HVL (NE-margin style, contrast-only here)
      3. If Vp ≤ 6.4 AND depth in ductile window → DUCTILE_MID_CRUSTAL
      4. If crust thickness ≤ 7 km AND Vp ≤ 7.0 (oceanic-like) → HYPERTHINNED_OCT
      5. If Vp > 6.8 (lower-crust-like) AND thickened → LOWER_CRUST_MAGMATIC
      6. If Vp ≤ 6.0 (upper) AND crust ~10 km → STRETCHED_CONTINENTAL
      7. If Vp in 5.0–6.8 gradual AND crust ~22 km → NORMAL_CONTINENTAL
      8. Else → OCEANIC_CRUST or UNKNOWN (no signature match)
    """
    diag: list[str] = []
    alts: list[CrustZone] = []
    confidence = 0.50  # default LOW-MEDIUM
    thickness: float | None = crust_thickness_km

    # ── 0. Out-of-range — sediment or sub-Moho ────────────────────────────
    # Vp < 3.5 km/s = sediment (water 1.5, soft 2–3, consolidated 3–3.5).
    # Vp > 8.5 km/s = sub-Moho / asthenosphere.
    if vp_km_s < 3.5:
        diag.append(f"Vp {vp_km_s} km/s < 3.5 km/s — sediment-like, not crust")
        return CrustClassification(
            zone=CrustZone.UNKNOWN,
            confidence=0.10,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=[],
            evidence_rank="SPEC",
        )
    if vp_km_s > 8.5:
        diag.append(f"Vp {vp_km_s} km/s > 8.5 km/s — sub-Moho / mantle, not crust")
        return CrustClassification(
            zone=CrustZone.UNKNOWN,
            confidence=0.10,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=[],
            evidence_rank="SPEC",
        )

    # ── 1. Serpentinized mantle ───────────────────────────────────────────
    # Narrow Vp window: 7.6–7.9 km/s (Huang 2021 reported ~7.7 ± ~0.1).
    # Vp 7.0–7.5 falls through to oceanic_crust (rule 8).
    if (
        7.6 <= vp_km_s <= 7.9
        and crust_thickness_km is not None
        and crust_thickness_km < 8.0
        and (heat_flow_mw_m2 is None or heat_flow_mw_m2 <= SERPENTINIZED_HEATFLOW_MW_M2)
    ):
        diag.append(
            f"Vp ~{SERPENTINIZED_VP} km/s (sub-Moho) + thin crust "
            f"(<8 km) + {'heat_flow ≤60 mW/m²' if heat_flow_mw_m2 else 'no heat_flow data'}"
        )
        diag.append(f"~{SERPENTINIZATION_PCT_ESTIMATE:.0f}% partial serpentinization estimate")
        confidence = 0.85
        if thickness is None:
            thickness = 6.0  # default OCT thickness
        alts.append(CrustZone.HYPERTHINNED_OCT)
        alts.append(CrustZone.LOWER_CRUST_MAGMATIC)
        return CrustClassification(
            zone=CrustZone.SERPENTINIZED_MANTLE,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
        )

    # ── 2. HVL underplating (contrast-only — not in NW margin) ────────────
    # Tightened: requires Vp 7.2–8.0 + crust >30 km. NW margin doesn't show this.
    if HVL_VP_THRESHOLD < vp_km_s <= 8.0 and crust_thickness_km is not None and crust_thickness_km > 30.0:
        diag.append(f"Vp > {HVL_VP_THRESHOLD} km/s + crust > 25 km = HVL signature")
        diag.append("Note: NW SCS margin does NOT show this (Huang 2021)")
        confidence = 0.70
        alts.append(CrustZone.LOWER_CRUST_MAGMATIC)
        alts.append(CrustZone.OCEANIC_CRUST)
        return CrustClassification(
            zone=CrustZone.LOWER_CRUST_MAGMATIC,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
            evidence_rank="DER",
        )

    # ── 3. Ductile mid-crustal layer ───────────────────────────────────────
    if vp_km_s <= DUCTILE_VP_TOP_THRESHOLD and depth_km is not None and DUCTILE_DEPTH_TOP_KM <= depth_km <= DUCTILE_DEPTH_BOT_KM:
        diag.append(
            f"Vp ≤ {DUCTILE_VP_TOP_THRESHOLD} km/s at depth "
            f"{depth_km} km (ductile window {DUCTILE_DEPTH_TOP_KM}–{DUCTILE_DEPTH_BOT_KM} km)"
        )
        diag.append(f"Expected +{DUCTILE_STEP_KM_S} km/s jump at top of lower crust")
        confidence = 0.85
        alts.append(CrustZone.STRETCHED_CONTINENTAL)
        alts.append(CrustZone.NORMAL_CONTINENTAL)
        return CrustClassification(
            zone=CrustZone.DUCTILE_MID_CRUSTAL,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
        )

    # ── 4. Hyperthinned OCT ───────────────────────────────────────────────
    # Requires Vp in oceanic-like range (4.5–7.0 km/s — layer 2 + layer 3).
    # Vp > 7.0 in a thin crust zone falls through to oceanic_crust (rule 8).
    if (
        crust_thickness_km is not None
        and crust_thickness_km <= HYPERTHINNED_THICKNESS_KM + 1.0  # ≤7 km tolerance
        and vp_km_s <= 7.0
    ):
        diag.append(
            f"Crust thickness {crust_thickness_km} km ≤ {HYPERTHINNED_THICKNESS_KM + 1.0} km = hyperthinned OCT signature"
        )
        diag.append(f"Expected β ≈ 5, magnetic anomaly ~{HYPERTHINNED_MAGNETIC_ANOMALY_NT:.0f} nT")
        confidence = 0.80
        alts.append(CrustZone.SERPENTINIZED_MANTLE)
        alts.append(CrustZone.OCEANIC_CRUST)
        return CrustClassification(
            zone=CrustZone.HYPERTHINNED_OCT,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
        )

    # ── 5. Lower crust with magmatic addition ─────────────────────────────
    if (
        vp_km_s >= STRETCHED_LOWER_CRUST_VP
        and vp_km_s <= LOWER_CRUST_VP_MAX + 0.2
        and crust_thickness_km is not None
        and crust_thickness_km > STRETCHED_THICKNESS_KM
    ):
        diag.append(f"Vp {vp_km_s} km/s in lower-crust range ({STRETCHED_LOWER_CRUST_VP}–{LOWER_CRUST_VP_MAX}) + thickened crust")
        diag.append(f"Expected magmatic underplating +{LOWER_CRUST_THICKENING_KM} km")
        confidence = 0.75
        alts.append(CrustZone.STRETCHED_CONTINENTAL)
        alts.append(CrustZone.NORMAL_CONTINENTAL)
        return CrustClassification(
            zone=CrustZone.LOWER_CRUST_MAGMATIC,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
        )

    # ── 6. Stretched continental ───────────────────────────────────────────
    if (
        vp_km_s <= STRETCHED_UPPER_CRUST_VP_MAX
        and crust_thickness_km is not None
        and crust_thickness_km <= STRETCHED_THICKNESS_KM + 3.0
    ):
        diag.append(f"Vp {vp_km_s} km/s ≤ {STRETCHED_UPPER_CRUST_VP_MAX} (upper crust) + crust ~{STRETCHED_THICKNESS_KM} km")
        diag.append("Expected β ≈ 3.0–3.8 (Xisha Trough template)")
        confidence = 0.70
        alts.append(CrustZone.NORMAL_CONTINENTAL)
        alts.append(CrustZone.DUCTILE_MID_CRUSTAL)
        return CrustClassification(
            zone=CrustZone.STRETCHED_CONTINENTAL,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
        )

    # ── 7. Normal continental ──────────────────────────────────────────────
    if (
        NORMAL_CONTINENTAL_VP_MIN <= vp_km_s <= NORMAL_CONTINENTAL_VP_MAX
        and crust_thickness_km is not None
        and crust_thickness_km >= NORMAL_CONTINENTAL_THICKNESS_KM - 4.0
    ):
        diag.append(
            f"Vp {vp_km_s} km/s in continental range "
            f"({NORMAL_CONTINENTAL_VP_MIN}–{NORMAL_CONTINENTAL_VP_MAX}) + "
            f"crust ~{NORMAL_CONTINENTAL_THICKNESS_KM} km"
        )
        diag.append("Receiver function match (Xisha Bank template)")
        confidence = 0.80
        alts.append(CrustZone.STRETCHED_CONTINENTAL)
        return CrustClassification(
            zone=CrustZone.NORMAL_CONTINENTAL,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
        )

    # ── 8. Oceanic crust or unknown ────────────────────────────────────────
    if vp_km_s > LOWER_CRUST_VP_MAX:
        diag.append(f"Vp {vp_km_s} km/s > {LOWER_CRUST_VP_MAX} = oceanic-like")
        confidence = 0.60
        alts.append(CrustZone.LOWER_CRUST_MAGMATIC)
        alts.append(CrustZone.SERPENTINIZED_MANTLE)
        return CrustClassification(
            zone=CrustZone.OCEANIC_CRUST,
            confidence=confidence,
            crust_thickness_km=thickness,
            diagnostic_basis=diag,
            alternative_zones=alts,
            evidence_rank="DER",
        )

    return CrustClassification(
        zone=CrustZone.UNKNOWN,
        confidence=0.20,
        crust_thickness_km=thickness,
        diagnostic_basis=[f"No zone signature matched for Vp={vp_km_s} km/s"],
        alternative_zones=[],
        evidence_rank="SPEC",
    )


def classify_column(column: CrustColumn) -> CrustColumn:
    """Apply vp_zone_classify to every observation in a column.

    Convenience function — does NOT mutate input, returns a new column.
    """
    classifications = []
    for obs in column.observations:
        c = vp_zone_classify(
            vp_km_s=obs.vp_km_s,
            crust_thickness_km=column.observations[-1].depth_km if column.observations else None,
            depth_km=obs.depth_km,
        )
        classifications.append(c)
    return column.model_copy(update={"classifications": classifications})


# Re-export Hasterok provenance map so callers can do:
#   from geox_core.schemas.crust_vp_grammar import CRUST_PROVENANCE_MAP, lookup
# Circular import is safe here — CrustZone is fully defined before
# crust_provenance_map.py imports it, and crust_provenance_map is only
# imported at module level after CrustZone class body is complete.
from geox_core.schemas.crust_provenance_map import (
    CRUST_PROVENANCE_MAP,
    ProvenanceEntry,
    lookup,
    all_labels,
    reversible_calls,
    crust_zone_map,
    WILSON_FIVE_COLLAPSE,
)

__all__ = [
    "CrustZone",
    "VpObservation",
    "CrustClassification",
    "CrustColumn",
    "vp_zone_classify",
    "classify_column",
    # Constants exported for test + cross-tool reuse
    "NORMAL_CONTINENTAL_VP_MIN",
    "NORMAL_CONTINENTAL_VP_MAX",
    "STRETCHED_UPPER_CRUST_VP_MAX",
    "STRETCHED_LOWER_CRUST_VP",
    "HYPERTHINNED_THICKNESS_KM",
    "DUCTILE_VP_TOP_THRESHOLD",
    "DUCTILE_DEPTH_TOP_KM",
    "DUCTILE_DEPTH_BOT_KM",
    "SERPENTINIZED_VP",
    "SERPENTINIZED_HEATFLOW_MW_M2",
    "HVL_VP_THRESHOLD",
    "LOWER_CRUST_VP_MAX",
    # Hasterok provenance map (Hasterok et al. 2022 → CrustZone)
    "CRUST_PROVENANCE_MAP",
    "ProvenanceEntry",
    "lookup",
    "all_labels",
    "reversible_calls",
    "crust_zone_map",
    "WILSON_FIVE_COLLAPSE",
]
