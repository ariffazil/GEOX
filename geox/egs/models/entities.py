"""
entities.py — Typed Earth Graph Models
========================================
GEOX EGS: Basin, Play, StratUnit, Horizon, Fault, Volume, Well, Survey.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

if TYPE_CHECKING:
    from geox.egs.models.sts import StateGraph
    from geox.egs.models.translation import TranslationLayer

# ═══════════════════════════════════════════════════════════════════════════════
# Geometry Primitives
# ═══════════════════════════════════════════════════════════════════════════════


class Point3D(BaseModel):
    """A 3D point in a specified coordinate reference system."""

    model_config = ConfigDict(extra="forbid")
    x: float = Field(..., description="Easting / longitude")
    y: float = Field(..., description="Northing / latitude")
    z: float = Field(..., description="Elevation / depth / time")
    crs: str = Field(default="EPSG:4326", description="Coordinate reference system")
    domain: Literal["depth_m", "tvdss_m", "twt_ms", "time_s"] = Field(default="depth_m", description="Vertical domain")


class SurfaceMesh3D(BaseModel):
    """Triangulated surface mesh representation."""

    model_config = ConfigDict(extra="forbid")
    vertices: list[Point3D] = Field(..., description="Mesh vertices")
    triangles: list[tuple[int, int, int]] = Field(..., description="Triangle vertex indices (i,j,k)")

    @computed_field
    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @computed_field
    @property
    def num_triangles(self) -> int:
        return len(self.triangles)

    @field_validator("triangles")
    @classmethod
    def _validate_triangle_indices(cls, v: list) -> list:
        for tri in v:
            if len(tri) != 3:
                raise ValueError(f"Each triangle must have 3 indices, got {len(tri)}")
            if any(i < 0 for i in tri):
                raise ValueError(f"Negative vertex index in triangle {tri}")
        return v


class StructuredGrid3D(BaseModel):
    """Regularly sampled 3D grid (e.g., seismic volume)."""

    model_config = ConfigDict(extra="forbid")
    origin: Point3D
    step_i: float = Field(..., gt=0, description="Inline step")
    step_j: float = Field(..., gt=0, description="Crossline step")
    step_k: float = Field(..., gt=0, description="Vertical step")
    dims: tuple[int, int, int] = Field(..., description="Grid dimensions (ni, nj, nk)")
    rotation_deg: float = Field(default=0.0, description="Grid rotation in degrees")
    crs: str = Field(default="EPSG:4326")


# ═══════════════════════════════════════════════════════════════════════════════
# Topology Primitives
# ═══════════════════════════════════════════════════════════════════════════════


class ContactRelation(StrEnum):
    """Stratigraphic contact relationships."""

    CONFORMABLE = "conformable"
    UNCONFORMABLE = "unconformable"
    EROSIONAL = "erosional"
    FAULTED = "faulted"
    ONLAP = "onlap"
    DOWNLAP = "downlap"
    TOPLAP = "toplap"
    TRUNCATED = "truncated"
    INTRUSIVE = "intrusive"
    GRADATIONAL = "gradational"
    UNKNOWN = "unknown"


class ConnectivityGraph(BaseModel):
    """Graph describing spatial/temporal connectivity between entities."""

    model_config = ConfigDict(extra="forbid")
    edges: list[tuple[str, str, str]] = Field(
        default_factory=list,
        description="List of (source_id, target_id, relationship) tuples",
    )
    directed: bool = Field(default=True, description="Whether edges are directed")


# ═══════════════════════════════════════════════════════════════════════════════
# Typed Earth Graph Entities
# ═══════════════════════════════════════════════════════════════════════════════


class EarthEntity(BaseModel):
    """Base class for all typed earth graph entities."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = Field(..., description="Human-readable entity name")
    description: str = Field(default="", description="Free-text description")
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = Field(default=1, description="Entity version number")
    active: bool = Field(default=True, description="Soft-delete flag")


class Basin(EarthEntity):
    """A sedimentary basin — the top-level geological container."""

    entity_type: Literal["basin"] = "basin"
    plays: list[str] = Field(default_factory=list, description="IDs of plays within this basin")
    bounding_box: tuple[float, float, float, float] | None = Field(
        default=None, description="(min_lon, min_lat, max_lon, max_lat)"
    )
    age_range_ma: tuple[float, float] | None = Field(default=None, description="(oldest_ma, youngest_ma)")
    basin_type: str = Field(default="", description="e.g. rift, passive_margin, foreland")
    tectonic_setting: str = Field(default="", description="e.g. extensional, compressional")


class Play(EarthEntity):
    """A petroleum play — a family of geologically related prospects."""

    entity_type: Literal["play"] = "play"
    basin_id: str = Field(..., description="Parent basin ID")
    leads: list[str] = Field(default_factory=list, description="IDs of leads/prospects")
    reservoir_units: list[str] = Field(default_factory=list, description="StratUnit IDs")
    seal_units: list[str] = Field(default_factory=list, description="StratUnit IDs")
    source_units: list[str] = Field(default_factory=list, description="StratUnit IDs")
    play_type: str = Field(default="", description="e.g. structural, stratigraphic, combination")
    key_risk_factors: list[str] = Field(default_factory=list)


class StratUnit(EarthEntity):
    """A stratigraphic unit (formation, member, sequence)."""

    entity_type: Literal["strat_unit"] = "strat_unit"
    basin_id: str = Field(..., description="Parent basin ID")
    rank: str = Field(default="formation", description="e.g. formation, member, group, sequence")
    age_top_ma: float | None = Field(default=None, description="Top age in Ma")
    age_base_ma: float | None = Field(default=None, description="Base age in Ma")
    lithology: str = Field(default="", description="Dominant lithology")
    environment: str = Field(default="", description="Depositional environment")
    thickness_mean_m: float | None = Field(default=None)
    thickness_range_m: tuple[float, float] | None = Field(default=None)
    contact_above: ContactRelation = ContactRelation.UNKNOWN
    contact_below: ContactRelation = ContactRelation.UNKNOWN


class Horizon(EarthEntity):
    """An interpreted stratigraphic or structural horizon surface."""

    entity_type: Literal["horizon"] = "horizon"
    basin_id: str = Field(..., description="Parent basin ID")
    strat_unit_id: str | None = Field(default=None, description="Associated strat unit")
    surface: SurfaceMesh3D | None = Field(default=None, description="3D surface geometry")
    interpretation_type: str = Field(default="seismic", description="e.g. seismic, well_marker, conceptual")
    interpreter: str = Field(default="", description="Who or what interpreted this")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    is_faulted: bool = Field(default=False)
    is_angular: bool = Field(default=False)


class Fault(EarthEntity):
    """A structural fault surface."""

    entity_type: Literal["fault"] = "fault"
    basin_id: str = Field(..., description="Parent basin ID")
    surface: SurfaceMesh3D | None = Field(default=None, description="Fault surface geometry")
    fault_type: str = Field(default="", description="e.g. normal, reverse, strike_slip")
    dip_deg: float | None = Field(default=None, ge=0.0, le=90.0)
    strike_deg: float | None = Field(default=None, ge=0.0, le=360.0)
    throw_m: float | None = Field(default=None)
    heave_m: float | None = Field(default=None)
    interpreted_by: str = Field(default="")


class Volume(EarthEntity):
    """A 3D volume of earth properties (seismic, properties, attributes)."""

    entity_type: Literal["volume"] = "volume"
    basin_id: str = Field(..., description="Parent basin ID")
    grid: StructuredGrid3D | None = Field(default=None, description="Spatial sampling")
    property_type: str = Field(default="", description="e.g. seismic_amplitude, porosity, velocity")
    unit: str = Field(default="", description="Physical unit")
    data_hash: str | None = Field(default=None, description="Hash of underlying data")
    survey_id: str | None = Field(default=None, description="Associated survey ID")


class Well(EarthEntity):
    """A wellbore — the primary source of ground truth."""

    entity_type: Literal["well"] = "well"
    basin_id: str = Field(default="", description="Parent basin ID")
    uwi: str = Field(default="", description="Unique Well Identifier")
    location: Point3D | None = Field(default=None, description="Wellhead location")
    total_depth_m: float | None = Field(default=None)
    status: str = Field(default="", description="e.g. active, abandoned, suspended")
    well_type: str = Field(default="", description="e.g. exploration, appraisal, production")
    log_curves: list[str] = Field(default_factory=list, description="Available log mnemonics")
    marker_ids: list[str] = Field(default_factory=list, description="IDs of well markers")
    trajectory: list[Point3D] = Field(default_factory=list, description="Deviation survey")


class Survey(EarthEntity):
    """A geophysical survey (seismic, gravity, magnetic, EM)."""

    entity_type: Literal["survey"] = "survey"
    basin_id: str = Field(default="", description="Parent basin ID")
    survey_type: str = Field(default="seismic", description="e.g. seismic_3d, seismic_2d, gravity")
    grid: StructuredGrid3D | None = Field(default=None, description="Survey grid geometry")
    volume_ids: list[str] = Field(default_factory=list, description="Associated volume IDs")
    acquisition_year: int | None = Field(default=None)
    processing_flow: str = Field(default="", description="Processing description")
    quality_flag: str = Field(default="unknown")


# ═══════════════════════════════════════════════════════════════════════════════
# Container — The Earth Graph
# ═══════════════════════════════════════════════════════════════════════════════


class EarthGraph(BaseModel):
    """The typed earth graph — a container of all entities with topology."""

    model_config = ConfigDict(extra="forbid")
    basins: dict[str, Basin] = Field(default_factory=dict)
    plays: dict[str, Play] = Field(default_factory=dict)
    strat_units: dict[str, StratUnit] = Field(default_factory=dict)
    horizons: dict[str, Horizon] = Field(default_factory=dict)
    faults: dict[str, Fault] = Field(default_factory=dict)
    volumes: dict[str, Volume] = Field(default_factory=dict)
    wells: dict[str, Well] = Field(default_factory=dict)
    surveys: dict[str, Survey] = Field(default_factory=dict)
    connectivity: ConnectivityGraph = Field(default_factory=ConnectivityGraph)
    # STS model — state machine graphs (Phase 2.5)
    sts_graphs: dict[str, StateGraph] = Field(default_factory=dict)
    translation_layers: dict[str, TranslationLayer] = Field(default_factory=dict)
    version: int = Field(default=1, description="Graph version")

    def add_entity(self, entity: EarthEntity) -> str:
        """Add an entity to the graph by its type. Returns entity ID."""
        entity_id = entity.id
        if isinstance(entity, Basin):
            self.basins[entity_id] = entity
        elif isinstance(entity, Play):
            self.plays[entity_id] = entity
        elif isinstance(entity, StratUnit):
            self.strat_units[entity_id] = entity
        elif isinstance(entity, Horizon):
            self.horizons[entity_id] = entity
        elif isinstance(entity, Fault):
            self.faults[entity_id] = entity
        elif isinstance(entity, Volume):
            self.volumes[entity_id] = entity
        elif isinstance(entity, Well):
            self.wells[entity_id] = entity
        elif isinstance(entity, Survey):
            self.surveys[entity_id] = entity
        else:
            raise ValueError(f"Unknown entity type: {type(entity).__name__}")
        self.version += 1
        return entity_id

    def get_entity(self, entity_id: str) -> EarthEntity | None:
        """Look up an entity by ID across all entity types."""
        for collection in [
            self.basins,
            self.plays,
            self.strat_units,
            self.horizons,
            self.faults,
            self.volumes,
            self.wells,
            self.surveys,
        ]:
            if entity_id in collection:
                return collection[entity_id]
        return None

    def remove_entity(self, entity_id: str) -> bool:
        """Soft-remove an entity by marking inactive."""
        entity = self.get_entity(entity_id)
        if entity is None:
            return False
        entity.active = False
        self.version += 1
        return True
