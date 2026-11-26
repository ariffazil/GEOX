"""GEOX Seismic capability contracts — stable schemas, replaceable implementations.

Per the APEX-ZEN doctrine:
- Capability ≠ Authority
- Govern capabilities, not implementations
- BUILD → VERIFY → JUDGE → SEAL → ACT → WITNESS

These schemas define the public capability surface. Adapters (numpy_scipy_v1,
pylops_v2, opendtect_external, cuda_v1) implement them.
"""
from geox.seismic.contracts.manifests import (
    DERIVED_MANIFEST_SCHEMA,
    MANIFEST_SCHEMA,
    DerivedVolumeManifest,
    DomainSpec,
    GridSpec,
    ImplementationRef,
    ParentRef,
    SCHEMA_VERSION,
    SignalSpec,
    StorageSpec,
    ValiditySpec,
    VolumeManifest,
)
from geox.seismic.contracts.qc import (
    QC_SCHEMA,
    FailureMode,
    QCReceipt,
    ValidationCheck,
)
from geox.seismic.contracts.geometry import (
    GEOMETRY_SCHEMA,
    PointSet,
    Polygon,
    Polyline,
    SurfaceMesh,
    VOI,
    VoxelMask,
)
from geox.seismic.contracts.polarity import (
    POLARITY_SCHEMA,
    POLARITY_SIGN,
    PhaseShiftEstimate,
    PolarityPhaseRegister,
    PolarityConvention,
)

__all__ = [
    # Manifests
    "SCHEMA_VERSION",
    "MANIFEST_SCHEMA",
    "DERIVED_MANIFEST_SCHEMA",
    "VolumeManifest",
    "DerivedVolumeManifest",
    "DomainSpec",
    "GridSpec",
    "SignalSpec",
    "StorageSpec",
    "ParentRef",
    "ImplementationRef",
    "ValiditySpec",
    # QC
    "QC_SCHEMA",
    "QCReceipt",
    "ValidationCheck",
    "FailureMode",
    # Geometry
    "GEOMETRY_SCHEMA",
    "VOI",
    "VoxelMask",
    "PointSet",
    "Polyline",
    "Polygon",
    "SurfaceMesh",
    # Polarity
    "POLARITY_SCHEMA",
    "POLARITY_SIGN",
    "PolarityPhaseRegister",
    "PhaseShiftEstimate",
    "PolarityConvention",
]
