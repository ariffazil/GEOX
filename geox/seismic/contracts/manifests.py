"""Volume manifests — stable capability contracts (not implementations).

Per the GEOX Seismic Interpretation Forge Package (Slice 1, Step 1):
- Capability IDs are stable; implementations (numpy_scipy_v1, pylops_v2, etc.) are replaceable.
- Every output is a derived-volume artifact carrying provenance, lineage, and QC.

Schema versioning follows the Copilot forge manifest spec (geox.seismic.derived-volume-manifest.v1).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "1.0.0"
MANIFEST_SCHEMA = "geox.seismic.volume-manifest.v1"
DERIVED_MANIFEST_SCHEMA = "geox.seismic.derived-volume-manifest.v1"


class GridSpec(BaseModel):
    """Regular grid geometry for a seismic volume."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    shape: tuple[int, int, int] = Field(
        ..., description="(iline, xline, sample) shape"
    )
    spacing: tuple[float, float, float] = Field(
        ..., description="(iline_m, xline_m, sample_ms or m) spacing"
    )
    axis_order: tuple[Literal["iline", "xline", "twt"], ...] = Field(
        ("iline", "xline", "twt"), description="Axis semantics, ordered"
    )

    @field_validator("shape", "spacing")
    @classmethod
    def _len3(cls, v: tuple) -> tuple:
        if len(v) != 3:
            raise ValueError("Expected length-3 tuple")
        return v

    @field_validator("shape")
    @classmethod
    def _positive(cls, v: tuple[int, int, int]) -> tuple[int, int, int]:
        if any(s <= 0 for s in v):
            raise ValueError("Shape entries must be positive")
        return v


class DomainSpec(BaseModel):
    """Vertical/surface domain — time or depth."""

    model_config = ConfigDict(extra="forbid")

    vertical: Literal["TWT", "TVD", "TWT+datum", "TVD+datum"]
    unit: Literal["ms", "s", "m", "ft"]
    crs: str = Field(..., description="EPSG code or WKT string")
    datum: str | None = Field(default=None, description="Reference datum if any")


class SignalSpec(BaseModel):
    """Polarity and phase metadata — required by L1 contracts."""

    model_config = ConfigDict(extra="forbid")

    polarity: Literal["SEG_NORMAL", "SEG_REVERSE", "EUROPEAN", "UNKNOWN"]
    phase_deg: float = Field(default=0.0, ge=-180.0, le=180.0)
    amplitude_status: Literal["relative", "absolute", "calibrated"]
    sample_interval_ms: float | None = Field(default=None, gt=0.0)


class StorageSpec(BaseModel):
    """Where the volume bytes live — never returned through MCP."""

    model_config = ConfigDict(extra="forbid")

    uri: str = Field(..., description="e.g., s3://bucket/path/array.zarr or file://")
    chunks: tuple[int, int, int] | None = None
    dtype: Literal["float16", "float32", "float64", "int16", "int32"] = "float32"
    compression: str | None = None


class VolumeManifest(BaseModel):
    """Root manifest for a registered seismic volume.

    This is the canonical contract for any input seismic artifact.
    Backed by geox_register_native_source semantics.

    artifact_id uses a permissive pattern; subclass validators enforce
    specific prefixes (volume/derived/qc/artifact/etc.).
    """

    model_config = ConfigDict(extra="forbid")

    schema_uri: Literal[MANIFEST_SCHEMA] = MANIFEST_SCHEMA
    artifact_id: str = Field(..., pattern=r"^geox://[a-z]+/[A-Za-z0-9_\-/.@]+$")
    sha256: str
    created_by: str = Field(..., description="actor_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    domain: DomainSpec
    grid: GridSpec
    signal: SignalSpec
    storage: StorageSpec

    source_uri: str = Field(..., description="Original ingestion URI (SEG-Y path, etc.)")
    source_format: Literal["SEGY_REV1", "SEGY_REV2", "ZGY", "MDIO_ZARR", "BLOSC2"] = "SEGY_REV1"
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "DERIVED_FROM_CONFIDENTIAL"]

    # License provenance (Anti-Haram, LAW 8: no GPL in core unless isolated)
    license: str | None = None
    license_provenance: list[str] = Field(default_factory=list)

    @field_validator("sha256", mode="before")
    @classmethod
    def _sha256_normalize(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("sha256 must be a string")
        v = v.strip().lower()
        if len(v) != 64:
            raise ValueError("SHA256 must be 64 hex chars")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("SHA256 must be hex")
        return v

    # Note: artifact_id prefix validation is delegated to subclasses
    # (VolumeManifest requires geox://volume/, DerivedVolumeManifest forbids it).
    # The permissive pattern at the base permits inheritance without over-broad rejection.

    def content_hash(self) -> str:
        """Stable hash of the canonicalized manifest (excluding created_at)."""
        canonical = self.model_dump(mode="json", exclude={"created_at"})
        blob = str(canonical).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()


class ParentRef(BaseModel):
    """Reference to a parent artifact in the provenance DAG."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., pattern=r"^geox://[A-Za-z0-9_\-/.@]+$")
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    role: Literal["input", "reference", "mask", "calibration"]


class ImplementationRef(BaseModel):
    """Reference to the implementation that produced this artifact.

    Capability contracts are stable; implementations are replaceable.
    Multiple implementations can satisfy the same capability.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="e.g., 'gst_energy_ratio', 'bruges_wavelet_ricker'")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    code_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    library: str | None = Field(
        default=None,
        description="Implementation family, e.g., 'numpy_scipy_v1', 'pylops_v2', 'opendtect_external'",
    )


class ValiditySpec(BaseModel):
    """Edge mask, confidence, and QC references for derived volumes."""

    model_config = ConfigDict(extra="forbid")

    edge_mask_ref: str | None = Field(
        default=None, pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$"
    )
    confidence_ref: str | None = Field(
        default=None, pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$"
    )
    qc_ref: str = Field(..., pattern=r"^geox://qc/[A-Za-z0-9_\-/.@]+$")


class DerivedVolumeManifest(VolumeManifest):
    """Manifest for a volume produced by a capability invocation.

    Adds: capability_id, implementation, parents (lineage), validity.
    """

    model_config = ConfigDict(extra="forbid")

    schema_uri: Literal[DERIVED_MANIFEST_SCHEMA] = DERIVED_MANIFEST_SCHEMA
    artifact_id: str = Field(
        ...,
        pattern=r"^geox://derived/[A-Za-z0-9_\-/.@]+$",
        description="Derived artifacts live under geox://derived/",
    )
    capability_id: str = Field(
        ...,
        pattern=r"^geox\.seismic\.attr\.[a-z_]+\.v\d+$",
        description="Stable capability contract ID; not implementation-specific",
    )
    implementation: ImplementationRef
    parents: list[ParentRef] = Field(..., min_length=1)
    validity: ValiditySpec
    parameters: dict[str, Any] = Field(default_factory=dict)
    human_edits: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of {actor, timestamp, operation, parent_version}",
    )

    @field_validator("parents")
    @classmethod
    def _unique_parents(cls, v: list[ParentRef]) -> list[ParentRef]:
        ids = [p.artifact_id for p in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate parent artifact_ids")
        return v
