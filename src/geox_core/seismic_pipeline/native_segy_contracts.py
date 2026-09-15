"""Native SEG-Y contracts — source registration, trace reference, QC receipts.

Establishes the physical witness: registered native SEG-Y source →
header/QC receipt → bounded trace extraction with full provenance.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceAuthority(str, Enum):
    OPERATOR_APPROVED = "OPERATOR_APPROVED"
    PUBLIC_VERIFIED = "PUBLIC_VERIFIED"
    SYNTHETIC_VERIFIED = "SYNTHETIC_VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class DataClassification(str, Enum):
    SYNTHETIC = "synthetic"
    PUBLIC = "public"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class VerticalDomain(str, Enum):
    TWT = "TWT"
    DEPTH = "DEPTH"
    UNKNOWN = "UNKNOWN"


class AmplitudeIntegrity(str, Enum):
    PRESERVED = "PRESERVED"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


class PhaseIntegrity(str, Enum):
    KNOWN = "KNOWN"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class PolarityState(str, Enum):
    SEG_NORMAL = "SEG_NORMAL"
    SEG_REVERSE = "SEG_REVERSE"
    UNKNOWN = "UNKNOWN"


# ── Source Registration ──────────────────────────────────────────────────────


class SeismicSourceRef(BaseModel):
    """Reference to a registered native seismic data source."""
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_uri: Optional[str] = None
    source_hash: Optional[str] = None  # SHA256 of file bytes
    classification: DataClassification = DataClassification.UNKNOWN
    authority: SourceAuthority = SourceAuthority.UNVERIFIED
    survey_id: Optional[str] = None
    line_id: Optional[str] = None
    crs: str = "CRS_UNKNOWN"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registered_by: Optional[str] = None


class SeismicDatasetManifest(BaseModel):
    """Manifest of a registered SEG-Y dataset with header metadata."""
    model_config = ConfigDict(extra="forbid")

    source_ref: SeismicSourceRef
    file_size_bytes: Optional[int] = None
    segy_revision: str = "unknown"  # rev1, rev2, unknown
    trace_count: Optional[int] = None
    samples_per_trace: Optional[int] = None
    sample_interval_us: Optional[int] = None
    sample_interval_ms: Optional[float] = None
    data_sample_format: Optional[int] = None  # segyio format code
    sorting: str = "unknown"  # inline, crossline, unknown
    vertical_domain: VerticalDomain = VerticalDomain.UNKNOWN
    vertical_unit: str = "unknown"
    inline_range: Optional[tuple[int, int]] = None
    crossline_range: Optional[tuple[int, int]] = None
    cdp_range: Optional[tuple[int, int]] = None
    amplitude_integrity: AmplitudeIntegrity = AmplitudeIntegrity.UNKNOWN
    phase_integrity: PhaseIntegrity = PhaseIntegrity.UNKNOWN
    polarity_state: PolarityState = PolarityState.UNKNOWN
    processing_lineage: str = "UNKNOWN"


# ── QC Receipt ───────────────────────────────────────────────────────────────


class SeismicQCReceipt(BaseModel):
    """Quality control receipt from SEG-Y header inspection."""
    model_config = ConfigDict(extra="forbid")

    source_id: str
    status: str = "PASS"  # PASS | WARN | HOLD | ERROR
    parsed_fields: dict[str, Any] = {}
    missing_fields: list[str] = []
    parse_warnings: list[str] = []
    amplitude_integrity: AmplitudeIntegrity = AmplitudeIntegrity.UNKNOWN
    phase_integrity: PhaseIntegrity = PhaseIntegrity.UNKNOWN
    polarity_state: PolarityState = PolarityState.UNKNOWN
    permitted_uses: list[str] = []
    prohibited_uses: list[str] = []
    required_next: list[str] = []
    tool_version: str = "v0.1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Native Trace Extraction ─────────────────────────────────────────────────


class NativeTraceRef(BaseModel):
    """Reference to an extracted native seismic trace."""
    model_config = ConfigDict(extra="forbid")

    trace_ref_id: str
    source_id: str
    source_hash: str
    trace_index: int
    cdp: Optional[int] = None
    inline: Optional[int] = None
    crossline: Optional[int] = None
    n_samples: int
    sample_interval_us: int
    sample_interval_ms: float
    vertical_domain: VerticalDomain = VerticalDomain.TWT
    vertical_unit: str = "ms"
    representation: str = "NATIVE_TRACE"
    amplitude_integrity: AmplitudeIntegrity = AmplitudeIntegrity.UNKNOWN
    phase_integrity: PhaseIntegrity = PhaseIntegrity.UNKNOWN
    polarity_state: PolarityState = PolarityState.UNKNOWN
    processing_lineage: str = "UNKNOWN"
    epistemic_tag: str = "OBS"
    extraction_tool: str = "geox_extract_native_trace"
    extraction_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NativeTraceReceipt(BaseModel):
    """Receipt from native trace extraction with QC reference."""
    model_config = ConfigDict(extra="forbid")

    trace_ref: NativeTraceRef
    qc_receipt_id: Optional[str] = None
    permitted_uses: list[str] = [
        "quantitative_amplitude_analysis",
        "avo_classification",
        "native_trace_well_tie",
        "seismic_inversion",
        "attribute_computation",
        "visual_interpretation",
    ]
    prohibited_uses: list[str] = []
    limitations: list[str] = []
    status: str = "OK"
