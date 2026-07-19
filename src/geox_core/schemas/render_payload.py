"""
RenderPayload — Standardized Render Contract for GEOX Visual Engine
====================================================================
Every GEOX visual output must conform to this schema.
It is the contract between GEOX compute and the generative UI layer.

Modalities covered:
  map         — GeoJSON FeatureCollection with CRS + MARUAH
  section     — Well correlation panel with log tracks + tops + pay
  cube_slice  — 2D frame from 3D volume with attribute overlay
  surface     — 3D mesh (horizon, fault, closure) with optional hull
  log_track   — Single well log curve with depth axis
  scatter     — 3D point cloud (well tops, DST points, pressure)
  uncertainty — P10/P50/P90 envelope volume/surface
  claim       — Visual claim overlay with evidence links

Binary data moves through MCP resource URIs, not inline JSON.
This schema carries pointers + metadata; heavy arrays live at resource URIs.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class RenderModality(StrEnum):
    """The visual modality of the render payload."""
    MAP = "map"
    SECTION = "section"
    CUBE_SLICE = "cube_slice"
    SURFACE = "surface"
    LOG_TRACK = "log_track"
    SCATTER = "scatter"
    UNCERTAINTY = "uncertainty"
    CLAIM = "claim"


class LodLevel(StrEnum):
    """Level of detail — supports progressive loading."""
    COARSE = "coarse"
    MEDIUM = "medium"
    FINE = "fine"
    FULL = "full"


class GeometryType(StrEnum):
    """How geometry is encoded (all via resource URI, not inline)."""
    GEOJSON = "geojson"           # Map features
    NUMPY_NPZ = "numpy_npz"       # 2D/3D arrays as .npz
    GLTF = "gltf"                 # 3D mesh/surface
    PLY = "ply"                   # Point cloud
    WELLLOG = "welllog"           # LAS-derived curve arrays
    BINARY_F32 = "binary_f32"     # Flat Float32Array (little-endian)
    BINARY_U16 = "binary_u16"     # Flat Uint16Array (index buffer)


class CRSInfo(BaseModel):
    """Coordinate reference system metadata."""
    horizontal: str = Field(default="EPSG:4326", description="Horizontal CRS (EPSG code or WKT)")
    vertical: str = Field(default="", description="Vertical CRS (e.g., EPSG:5703 for MSL height)")
    depth_basis: str = Field(default="TVDSS", description="MD | TVD | TVDSS | TWT")
    depth_datum: str = Field(default="MSL", description="KB | DF | MSL | LAT")
    well_datum: str | None = Field(default=None, description="Local well datum if different from field datum")


class BoundingBox(BaseModel):
    """Spatial extent of the render payload."""
    min_x: float = Field(default=0.0, description="Minimum X / Longitude")
    min_y: float = Field(default=0.0, description="Minimum Y / Latitude")
    max_x: float = Field(default=0.0, description="Maximum X / Longitude")
    max_y: float = Field(default=0.0, description="Maximum Y / Latitude")
    min_z: float | None = Field(default=None, description="Minimum Z / Depth / Time")
    max_z: float | None = Field(default=None, description="Maximum Z / Depth / Time")
    crs: str = Field(default="EPSG:4326", description="CRS of this bounding box")


class BinaryResource(BaseModel):
    """Pointer to binary data via MCP resource URI.
    
    The binary data itself is NOT in the JSON payload.
    It lives at resource_uri, to be fetched via MCP resources/streamable HTTP.
    This keeps the tool response small and governance-focused.
    """
    resource_uri: str = Field(description="MCP resource URI (e.g., geox://surfaces/horizon_A_2024.npz)")
    geometry_type: GeometryType = Field(description="How to decode the binary data")
    shape: list[int] = Field(default_factory=list, description="Array shape [nx, ny] or [nx, ny, nz]")
    dtype: str = Field(default="float32", description="NumPy-compatible dtype string")
    byte_offset: int = Field(default=0, description="Byte offset into resource (for chunked access)")
    byte_length: int | None = Field(default=None, description="Total byte length (None = entire resource)")
    lod: LodLevel = Field(default=LodLevel.FULL, description="Level of detail of this binary payload")


class LODInfo(BaseModel):
    """Level-of-detail metadata for a cube."""
    level: int = Field(default=0, ge=0, le=10, description="LOD level (0=coarsest, N=fines)")
    stride: int = Field(default=4, description="Decimation stride relative to full resolution")
    brick_shape: list[int] = Field(default=[64, 64, 64], description="Brick voxel shape at this LOD")
    data_type: str = Field(default="int16", description="NumPy dtype for this LOD (e.g. int16, uint8, float32)")
    compression: str = Field(default="none", description="Compression algorithm (none | zstd | wavelet)")
    value_range: list[float] = Field(default=[], description="[min, max] amplitude range at this LOD")


class BrickAddress(BaseModel):
    """Canonical brick address in a 3D brick grid."""
    ix: int = Field(ge=0, description="Brick index along X/inline axis")
    iy: int = Field(ge=0, description="Brick index along Y/crossline axis")
    iz: int = Field(ge=0, description="Brick index along Z/depth/time axis")


class BrickResource(BaseModel):
    """A single brick of a 3D cube at a specific LOD.
    
    The binary data lives at resource_uri — never inline in JSON.
    """
    brick: BrickAddress
    lod: int = Field(default=0, description="LOD level of this brick")
    resource_uri: str = Field(description="MCP resource URI (e.g., geox://render/cubes/CUBE123/lod/1/brick/0/0/0)")
    byte_length: int = Field(default=0, description="Byte length of this brick's binary data")
    data_type: str = Field(default="float32", description="NumPy dtype for this brick")
    compression: str = Field(default="none", description="Compression (none | zstd | wavelet)")
    hash: str = Field(default="", description="SHA-256 of brick bytes for integrity verification")


class CubeManifest(BaseModel):
    """Cube Manifest — defines a 3D seismic volume for binary streaming.
    
    This is the FIRST thing a client fetches before requesting any bricks.
    It describes the cube's grid, LOD pyramid, CRS, and where to find bricks.
    
    The tool envelope carries just the manifest_uri + governance.
    All heavy data moves through the manifest → brick resource chain.
    """
    # Identity
    cube_id: str = Field(description="Canonical cube identifier")
    name: str = Field(default="", description="Human-readable cube name")
    
    # Dimensions
    dims: list[int] = Field(default=[0, 0, 0], description="Full voxel dimensions [nx, ny, nz]")
    brick_shape: list[int] = Field(default=[64, 64, 64], description="Brick shape [bx, by, bz]")
    brick_grid_shape: list[int] = Field(default=[0, 0, 0], description="Grid shape [nx//bx, ny//by, nz//bz]")
    
    # Spatial
    crs: str = Field(default="EPSG:4326")
    bbox_origin: list[float] = Field(default=[0, 0, 0], description="[inline_0, xline_0, time_ms_0]")
    bbox_max: list[float] = Field(default=[0, 0, 0], description="[inline_max, xline_max, time_ms_max]")
    sample_spacing: list[float] = Field(default=[1, 1, 4], description="[di, djl, dt_ms]")
    time_depth_domain: str = Field(default="TWT", description="TWT | DEPTH_M | DEPTH_FT")
    
    # LOD pyramid
    lod_count: int = Field(default=1, ge=1, le=10, description="Number of LOD levels")
    lods: list[LODInfo] = Field(default_factory=list, description="Per-LOD metadata")
    
    # Data
    primary_attribute: str = Field(default="amplitude", description="Main attribute name")
    available_attributes: list[str] = Field(default_factory=list, description="All available attributes")
    data_origin: str = Field(default="SEG-Y", description="Source format (SEG-Y, ZGY, VDS, etc.)")
    
    # Resource URI templates
    brick_uri_template: str = Field(
        default="geox://render/cubes/{cube_id}/lod/{lod}/brick/{ix}/{iy}/{iz}",
        description="URI template for brick fetches. Client fills in cube_id, lod, ix, iy, iz."
    )
    manifest_uri: str = Field(
        default="",
        description="URI of this manifest document itself (for caching)"
    )
    
    # Governance
    claim_tag: str = Field(default="COMPUTED", description="Epistemic classification")
    acrisk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    arifos_verdict: str = Field(default="QUALIFY")
    artifact_ref: str = Field(default="", description="Source artifact hash")
    
    # Timestamp
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class RenderPayload(BaseModel):
    """Canonical render contract — every GEOX visual output conforms to this.
    
    This replaces all ad-hoc render fields across GEOX tools.
    Binary data is OUT-OF-BAND via MCP resource URIs.
    Governance metadata stays IN-BAND in the JSON tool response.
    
    For 3D cubes, the RenderPayload carries a CubeManifest pointer instead of 
    inline arrays. The client fetches bricks progressively from the manifest.
    """
    # Identity
    render_id: str = Field(default_factory=lambda: f"geox-render-{uuid4().hex[:12]}")
    modality: RenderModality = Field(description="What type of visual this is")
    render_type: str = Field(default="map", description="Human-readable sub-type (e.g., basin_map, well_panel)")
    
    # Spatial context
    crs: CRSInfo = Field(default_factory=CRSInfo)
    bbox: BoundingBox | None = Field(default=None, description="Spatial extent of this render")
    
    # Binary data pointers (out-of-band)
    resources: list[BinaryResource] = Field(default_factory=list, description="Binary data at MCP resource URIs")
    cube_manifest: CubeManifest | None = Field(default=None, description="Cube manifest for 3D volume streaming")
    
    # Governance
    claim_tag: Literal["OBSERVED", "COMPUTED", "INTERPRETED", "SYNTHESIZED", "VERIFIED",
                        "CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"] = "HYPOTHESIS"
    claim_refs: list[str] = Field(default_factory=list, description="Claim IDs that this render supports")
    arifos_verdict: Literal["SEAL", "QUALIFY", "HOLD", "VOID", "888_HOLD"] = "QUALIFY"
    acrisk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="ACRisk composite score")
    human_review_required: bool = Field(default=False, description="F13 gate: does this need Arif?")
    
    # Lightweight inline data (for small payloads that don't need binary transport)
    inline_geojson: dict[str, Any] | None = Field(default=None, description="Inline GeoJSON for small map features")
    inline_stats: dict[str, float] | None = Field(default=None, description="Inline statistics (mean, std, p10, p90)")
    
    # Source provenance
    source_tool: str = Field(default="", description="GEOX tool that produced this render")
    source_artifact_refs: list[str] = Field(default_factory=list, description="Artifact hashes that this render is derived from")
    
    # Timestamp
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    
    # Visual Engine metadata
    visual_artifact_id: str = Field(default_factory=lambda: f"sha256:geox-render-{uuid4().hex[:16]}")
    maruah_flag: Any = Field(default=None, description="MARUAH territory check result")


# ── Modality-specific render builders ──────────────────────────────────────────

def render_map(
    geojson: dict[str, Any],
    bbox: list[float] | None = None,
    crs: str = "EPSG:4326",
    claim_tag: str = "OBSERVED",
    maruah_flag: Any = None,
) -> RenderPayload:
    """Build a map modality RenderPayload from a GeoJSON FeatureCollection."""
    xmin, ymin, xmax, ymax = bbox if bbox else [0, 0, 0, 0]
    return RenderPayload(
        modality=RenderModality.MAP,
        render_type="geojson_map",
        crs=CRSInfo(horizontal=crs),
        bbox=BoundingBox(min_x=xmin, min_y=ymin, max_x=xmax, max_y=ymax, crs=crs) if bbox else None,
        inline_geojson=geojson,
        claim_tag=claim_tag,
        maruah_flag=maruah_flag,
    )


def render_surface(
    resource_uri: str,
    geometry_type: GeometryType = GeometryType.NUMPY_NPZ,
    shape: list[int] | None = None,
    bbox: list[float] | None = None,
    claim_tag: str = "INTERPRETED",
) -> RenderPayload:
    """Build a surface modality RenderPayload — mesh/horizon via MCP resource."""
    xmin, ymin, xmax, ymax = bbox if bbox else [0, 0, 0, 0]
    return RenderPayload(
        modality=RenderModality.SURFACE,
        render_type="horizon_mesh",
        bbox=BoundingBox(min_x=xmin, min_y=ymin, max_x=xmax, max_y=ymax) if bbox else None,
        resources=[
            BinaryResource(
                resource_uri=resource_uri,
                geometry_type=geometry_type,
                shape=shape or [],
            )
        ],
        claim_tag=claim_tag,
    )


def render_cube_slice(
    resource_uri: str,
    shape: list[int],
    orientation: str = "inline",
    slice_index: int = 0,
    bbox: list[float] | None = None,
    attribute: str = "amplitude",
    claim_tag: str = "COMPUTED",
    cube_manifest: CubeManifest | None = None,
) -> RenderPayload:
    """Build a cube_slice modality RenderPayload — 2D frame from 3D volume.
    
    For slice-level access, a single BinaryResource is sufficient.
    For progressive 3D access, pass a CubeManifest and bricks are fetched
    via the brick_uri_template.
    """
    return RenderPayload(
        modality=RenderModality.CUBE_SLICE,
        render_type=f"{orientation}_slice_{attribute}",
        claim_tag=claim_tag,
        cube_manifest=cube_manifest,
        resources=[
            BinaryResource(
                resource_uri=resource_uri,
                geometry_type=GeometryType.BINARY_F32,
                shape=shape,
            )
        ] if resource_uri else [],
        inline_stats={"orientation": 0, "slice_index": float(slice_index), "attribute": 0},
    )
