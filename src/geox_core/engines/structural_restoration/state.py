"""Restoration state schema — immutable scenario objects.

SR_INV_001: Never overwrite source geometry.
SR_INV_002: Every output references input object IDs and scenario ID.
SR_INV_003: Surface subtraction requires matching CRS/units/datum/polarity.
TECT-001: Restoration products are observations, not explanations.

Every restoration computation creates a NEW immutable scenario-derived object.
Source geometry is NEVER mutated.

Forged: 2026-09-14
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# Coordinate Reference System
# ═══════════════════════════════════════════════════════════════════════════


class ZConvention(StrEnum):
    """Z-axis polarity convention."""

    POSITIVE_UP = "positive_up"  # Elevation convention (topography)
    POSITIVE_DOWN = "positive_down"  # Depth convention (subsurface)


class CRSProof(BaseModel):
    """Coordinate reference system proof packet.

    SR_INV_003: Surface subtraction requires matching CRS, XY units,
    Z units, datum and polarity.
    """

    crs_epsg: int | None = Field(
        default=None, description="EPSG code (e.g., 4326, 32650)"
    )
    crs_name: str = Field(default="", description="CRS name (e.g., WGS84 / UTM50N)")
    xy_units: str = Field(
        default="m", description="XY units (m, ft, deg)"
    )
    z_units: str = Field(
        default="m", description="Z units (m, ft, ms TWT, s TWT)"
    )
    z_convention: ZConvention = Field(
        default=ZConvention.POSITIVE_DOWN,
        description="Z polarity: positive_up (elevation) or positive_down (depth)",
    )
    vertical_datum: str = Field(
        default="MSL",
        description="Vertical datum (MSL, MLLW, SRVD, KB, etc.)",
    )
    horizontal_datum: str = Field(
        default="WGS84", description="Horizontal datum"
    )

    def is_compatible_with(self, other: CRSProof) -> list[str]:
        """Check compatibility with another CRS proof. Returns list of mismatches."""
        mismatches: list[str] = []
        if self.crs_epsg != other.crs_epsg:
            mismatches.append(
                f"CRS EPSG mismatch: {self.crs_epsg} vs {other.crs_epsg}"
            )
        if self.xy_units != other.xy_units:
            mismatches.append(
                f"XY units mismatch: {self.xy_units} vs {other.xy_units}"
            )
        if self.z_units != other.z_units:
            mismatches.append(
                f"Z units mismatch: {self.z_units} vs {other.z_units}"
            )
        if self.z_convention != other.z_convention:
            mismatches.append(
                f"Z convention mismatch: {self.z_convention} vs {other.z_convention}"
            )
        if self.vertical_datum != other.vertical_datum:
            mismatches.append(
                f"Vertical datum mismatch: {self.vertical_datum} vs {other.vertical_datum}"
            )
        return mismatches


# ═══════════════════════════════════════════════════════════════════════════
# Surface / Fault Identity
# ═══════════════════════════════════════════════════════════════════════════


class SurfaceIdentity(BaseModel):
    """Identity and metadata for a geological surface.

    SR_INV_001: Source geometry is immutable.
    SR_INV_002: Every output references input object IDs.
    """

    surface_id: str = Field(..., description="Unique surface identifier")
    name: str = Field(..., description="Human-readable name (e.g., 'Top Crocker')")
    age_ma: float | None = Field(
        default=None, description="Interpreted age (Ma, 0=present)"
    )
    age_uncertainty_ma: float | None = Field(
        default=None, description="Age uncertainty (Ma)"
    )
    stratigraphic_unit: str = Field(
        default="", description="Stratigraphic unit name"
    )
    surface_type: str = Field(
        default="horizon",
        description="Type: horizon, unconformity, fault, basement, etc.",
    )
    is_source_geometry: bool = Field(
        default=True,
        description="True if this is original (immutable) source geometry",
    )
    crs: CRSProof = Field(default_factory=CRSProof)
    grid_extent: dict[str, float] = Field(
        default_factory=dict,
        description="Spatial extent: {xmin, xmax, ymin, ymax}",
    )
    grid_cells: int | None = Field(
        default=None, description="Number of grid cells"
    )
    cell_size_m: float | None = Field(
        default=None, description="Cell size in metres"
    )
    data_source: str = Field(
        default="", description="Origin: seismic_interp, well_tie, map_digitize, etc."
    )
    hash: str = Field(
        default="", description="SHA-256 of the surface grid data"
    )


class FaultIdentity(BaseModel):
    """Identity and metadata for a geological fault.

    TECT-004: Fault azimuth is evidence, not age.
    SR_INV_008: Fault generation from relational evidence.
    """

    fault_id: str = Field(..., description="Unique fault identifier")
    name: str = Field(default="", description="Human-readable fault name")
    mapped_azimuth_deg: float | None = Field(
        default=None, ge=0.0, lt=360.0, description="Mapped fault strike (degrees)"
    )
    proposed_generation: str | None = Field(
        default=None, description="Proposed tectonic generation"
    )
    active_interval_ma: tuple[float, float] | None = Field(
        default=None, description="(start, end) age range of activity"
    )
    reactivation_status: str = Field(
        default="unknown",
        description="Reactivation status: primary, reactivated, unknown",
    )
    confidence: str = Field(
        default="unknown", description="Confidence in generation assignment"
    )
    relational_evidence: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Relational evidence for generation: cross_cutting, "
            "termination, bending, segmentation, displacement, "
            "basement_trend, stress_comparison"
        ),
    )
    crs: CRSProof = Field(default_factory=CRSProof)


# ═══════════════════════════════════════════════════════════════════════════
# Compaction Scenario
# ═══════════════════════════════════════════════════════════════════════════


class EvidenceClass(StrEnum):
    """Parameter provenance classification (SR_INV_010)."""

    MEASURED = "MEASURED"  # Directly measured from data
    PUBLISHED = "PUBLISHED"  # From published literature
    EXTRAPOLATED = "EXTRAPOLATED"  # Extrapolated beyond measured support
    ASSUMED = "ASSUMED"  # Assumed without direct evidence


class CompactionScenario(BaseModel):
    """Compaction parameters with provenance.

    SR_INV_009: Compaction extrapolation must produce low, reference, high scenarios.
    SR_INV_010: Measured/published/extrapolated/assumed must be distinguishable.
    SR_INV_012: Uniform lithology must be declared.
    EUREKA-07: Compaction uncertainty propagates non-linearly.
    """

    scenario_name: str = Field(..., description="Scenario identifier")
    reference_curve: str = Field(
        ...,
        description=(
            "Named curve or dataset (e.g., 'Sclater & Christie 1980', "
            "'Dickinson 1953', 'in-house NW Sabah')"
        ),
    )
    measured_depth_limit_m: float | None = Field(
        default=None,
        description="Maximum depth with measured support (m)",
    )
    extrapolation_end_depth_m: float | None = Field(
        default=None,
        description="Depth to which curve is extrapolated beyond measured support (m)",
    )
    porosity_adjustment: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Porosity adjustment specification. "
            "Must distinguish absolute porosity points from relative %. "
            "e.g., {type: 'absolute_porosity_points', value: 5} "
            "or {type: 'relative_percent', value: 0.05}"
        ),
    )
    depth_interval_m: float | None = Field(
        default=None,
        description="Depth interval for uncertainty accumulation (m)",
    )
    surface_porosity: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Surface porosity (fraction)"
    )
    compaction_coefficient: float | None = Field(
        default=None, description="Compaction coefficient (1/m or 1/km)"
    )
    dominant_lithology: str = Field(
        default="sandstone",
        description="Dominant lithology for this scenario",
    )
    evidence_class: EvidenceClass = Field(
        default=EvidenceClass.ASSUMED,
        description="Provenance classification of the parameters",
    )
    uniform_lithology: bool = Field(
        default=True,
        description="True if single lithology across entire model (SR_INV_012)",
    )
    facies_domains: list[str] = Field(
        default_factory=list,
        description="If not uniform, list of facies domains",
    )


class UncertaintyEnvelope(BaseModel):
    """Uncertainty specification for a restoration product.

    SR_INV_013: All derived maps must carry uncertainty and provenance.
    EUREKA-08: Calibration confidence decays spatially.
    """

    numerical: dict[str, Any] = Field(
        default_factory=dict,
        description="Numerical uncertainty (e.g., {p10, p50, p90, std})",
    )
    spatial: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Spatial uncertainty specification: "
            "{control_points, distance_metric, growth_function, "
            "cutoff_distance_km, max_uncertainty_m, "
            "values_are_observed_or_assumed}"
        ),
    )
    geological: dict[str, Any] = Field(
        default_factory=dict,
        description="Geological uncertainty (facies, erosion, hiatus, etc.)",
    )
    compaction: dict[str, Any] = Field(
        default_factory=dict,
        description="Compaction scenario uncertainty (low/reference/high)",
    )


# ═══════════════════════════════════════════════════════════════════════════
# Restoration Scenario (the immutable state object)
# ═══════════════════════════════════════════════════════════════════════════


class RestorationScenario(BaseModel):
    """An immutable restoration scenario.

    SR_INV_001: Never overwrite source geometry.
    SR_INV_002: Every output references input object IDs and scenario ID.
    SR_INV_004: Restoration ages and stratigraphic ordering must be explicit.
    TECT-001: This is a geometric computation, not a tectonic explanation.

    Every restoration computation creates a NEW RestorationScenario.
    Source surfaces are NEVER mutated.
    """

    scenario_id: str = Field(
        ..., description="Unique scenario identifier (UUID or hash-based)"
    )
    name: str = Field(..., description="Human-readable scenario name")
    description: str = Field(default="", description="What this scenario represents")

    # Source and restored states
    source_state: SurfaceIdentity = Field(
        ..., description="Present-day or source state surface"
    )
    target_state: SurfaceIdentity = Field(
        ..., description="Restored or target state surface"
    )
    basement_source: SurfaceIdentity | None = Field(
        default=None, description="Basement surface in source state"
    )
    basement_target: SurfaceIdentity | None = Field(
        default=None, description="Basement surface in target state"
    )

    # Ages and stratigraphy
    source_age_ma: float = Field(
        ..., ge=0.0, description="Age of source state (Ma)"
    )
    target_age_ma: float = Field(
        ..., ge=0.0, description="Age of target state (Ma)"
    )
    stratigraphic_order: list[str] = Field(
        default_factory=list,
        description="Stratigraphic ordering from oldest to youngest",
    )

    # CRS verification (SR_INV_003)
    crs_proof: CRSProof = Field(
        default_factory=CRSProof,
        description="CRS proof for this scenario (must match between states)",
    )
    crs_mismatches: list[str] = Field(
        default_factory=list,
        description="Any CRS mismatches detected during validation",
    )

    # Compaction
    compaction_scenario: CompactionScenario | None = Field(
        default=None, description="Compaction scenario used"
    )

    # Faults
    faults: list[FaultIdentity] = Field(
        default_factory=list, description="Faults in this scenario"
    )

    # Uncertainty
    uncertainty: UncertaintyEnvelope = Field(
        default_factory=UncertaintyEnvelope,
        description="Uncertainty envelope for this scenario",
    )

    # Tectonic context (F0 layer)
    tectonic_event_id: str | None = Field(
        default=None,
        description="Tectonic event this restoration corresponds to (from F0 ontology)",
    )
    restoration_type: str = Field(
        default="2d_cross_section",
        description=(
            "Type: 2d_cross_section, 3d_surface, palinspastic, "
            "backstrip, kinematic"
        ),
    )

    # Audit
    created_at: str = Field(
        default="", description="ISO-8601 UTC creation timestamp"
    )
    created_by: str = Field(
        default="", description="Agent or human that created this scenario"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Full provenance chain: input data → computation → this scenario",
    )
    assumptions: list[str] = Field(
        default_factory=list, description="All assumptions used in this scenario"
    )

    # Immutability marker
    immutable: bool = Field(
        default=True,
        description="Always True — source geometry must never be overwritten",
    )
