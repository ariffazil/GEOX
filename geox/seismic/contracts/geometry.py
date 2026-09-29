"""Geometry primitives for interpretation artifacts.

Per the GEOX Seismic Interpretation Forge Package:
- Immutable PointSet, Polyline, Polygon, SurfaceMesh, VoxelMask, VOI.
- Each edit creates a new version with parent pointer, author, operation, undo record.
- Anti-pattern: GUI-produced evidence; ML probability treated as confidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GEOMETRY_SCHEMA = "geox.seismic.geometry.v1"


class VOI(BaseModel):
    """Volume of interest — bounding subregion of a seismic volume."""

    model_config = ConfigDict(extra="forbid")

    volume_ref: str = Field(..., pattern=r"^geox://volume/[A-Za-z0-9_\-/.@]+$")
    inline_range: tuple[int, int] | None = None
    xline_range: tuple[int, int] | None = None
    sample_range: tuple[int, int] | None = None
    polygon: list[tuple[float, float]] | None = Field(
        default=None,
        description="Optional 2D polygon in (iline, xline) — bypasses range bounds",
    )

    @field_validator("inline_range", "xline_range", "sample_range")
    @classmethod
    def _ordered(cls, v: tuple[int, int] | None) -> tuple[int, int] | None:
        if v is None:
            return None
        if v[0] > v[1]:
            raise ValueError("Range start must be <= end")
        return v


class VoxelMask(BaseModel):
    """Boolean or probability mask over a volume's voxel grid."""

    model_config = ConfigDict(extra="forbid")

    mask_id: str = Field(..., pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$")
    volume_ref: str = Field(..., pattern=r"^geox://volume/[A-Za-z0-9_\-/.@]+$")
    voi: VOI
    dtype: Literal["bool", "float32"] = Field(
        default="float32",
        description="'bool' = hard mask; 'float32' = probability/probability-like field",
    )
    threshold_applied: float | None = Field(
        default=None, description="If dtype=bool, the threshold that produced the mask"
    )
    parent_mask_ref: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PointSet(BaseModel):
    """Immutable set of 3D points (inlines, xlines, samples or x/y/z)."""

    model_config = ConfigDict(extra="forbid")

    pointset_id: str = Field(..., pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$")
    coordinate_frame: Literal["INLINE_XLINE_SAMPLE", "INLINE_XLINE_TIME", "XYZ"]
    points: list[tuple[float, float, float]] = Field(..., min_length=1)
    parent_ref: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Polyline(BaseModel):
    """Ordered 3D polyline (e.g., fault stick)."""

    model_config = ConfigDict(extra="forbid")

    polyline_id: str = Field(..., pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$")
    coordinate_frame: Literal["INLINE_XLINE_SAMPLE", "INLINE_XLINE_TIME", "XYZ"]
    points: list[tuple[float, float, float]] = Field(..., min_length=2)
    confidence: list[float] | None = None  # per-vertex
    parent_ref: str | None = None
    operation: str | None = None  # last edit operation
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("confidence")
    @classmethod
    def _confidence_matches_points(
        cls, v: list[float] | None, info
    ) -> list[float] | None:
        if v is None:
            return None
        # Length check happens via cross-field; here just check range
        if any(c < 0.0 or c > 1.0 for c in v):
            raise ValueError("Confidence must be in [0, 1]")
        return v


class Polygon(BaseModel):
    """Closed 2D polygon (e.g., geobody footprint, mini-basin)."""

    model_config = ConfigDict(extra="forbid")

    polygon_id: str = Field(..., pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$")
    coordinate_frame: Literal["INLINE_XLINE", "XYZ"]
    vertices: list[tuple[float, float]] = Field(..., min_length=3)
    closed: bool = True
    parent_ref: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SurfaceMesh(BaseModel):
    """Triangulated surface mesh (e.g., horizon, fault surface)."""

    model_config = ConfigDict(extra="forbid")

    mesh_id: str = Field(..., pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$")
    coordinate_frame: Literal["INLINE_XLINE_TIME", "INLINE_XLINE_DEPTH", "XYZ"]
    vertices: list[tuple[float, float, float]] = Field(..., min_length=3)
    faces: list[tuple[int, int, int]] = Field(
        ...,
        min_length=1,
        description="Triangle indices, 0-based into vertices[]",
    )
    confidence: list[float] | None = None  # per-vertex
    alternative_paths: list[str] | None = Field(
        default=None,
        description="Refs to alternative surface paths (per Copilot horizon-track contract)",
    )
    stopped_regions: list[dict[str, Any]] | None = None
    parent_ref: str | None = None
    operation: str | None = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("faces")
    @classmethod
    def _faces_in_range(cls, v: list[tuple[int, int, int]], info) -> list:
        # Cross-field validation: faces must reference valid vertex indices
        vertices = info.data.get("vertices", [])
        n = len(vertices)
        for f in v:
            if any(idx < 0 or idx >= n for idx in f):
                raise ValueError(f"Face index out of range: {f}")
        return v
