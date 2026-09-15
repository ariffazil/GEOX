"""Calibration Witness contracts for GEOX structural interpretation.

The CalibrationWitness is the bridge between human calibration clicks
and structural gate computation. It records what was clicked, what
physical value was asserted, what source supports it, and where
uncertainty enters.

DITEMPA BUKAN DIBERI.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class WitnessStatus(str, Enum):
    DRAFT = "DRAFT"
    VALID = "VALID"
    HOLD = "HOLD"
    SUPERSEDED = "SUPERSEDED"


class CalibrationPurpose(str, Enum):
    DIP_MEASUREMENT = "dip_measurement"
    DISPLACEMENT_ESTIMATION = "displacement_estimation"
    FAULT_THROW_ESTIMATION = "fault_throw_estimation"
    STRUCTURAL_RESTORATION = "structural_restoration"


class DataClassification(str, Enum):
    SYNTHETIC = "synthetic"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class AuthorityState(str, Enum):
    OPERATOR_APPROVED = "OPERATOR_APPROVED"
    PUBLIC_VERIFIED = "PUBLIC_VERIFIED"
    SYNTHETIC_VERIFIED = "SYNTHETIC_VERIFIED"
    UNVERIFIED = "UNVERIFIED"


class VerticalDomain(str, Enum):
    TWT = "TWT"
    DEPTH = "DEPTH"
    MIXED = "MIXED"


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: str
    dataset_version_hash: Optional[str] = None
    source_uri: Optional[str] = None
    classification: DataClassification = DataClassification.SYNTHETIC
    authority_state: AuthorityState = AuthorityState.UNVERIFIED


class AnchorPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pixel_x: float
    pixel_y: float
    world_x: Optional[float] = None
    world_y: Optional[float] = None
    value: Optional[float] = None  # for TWT/depth ticks


class AxisCalibration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: str = "two_point"  # two_point | header | navigation | checkshot_tie
    anchor_a: AnchorPoint
    anchor_b: AnchorPoint
    scale_per_pixel: Optional[float] = None
    unit: str = "unknown"
    uncertainty: Optional[dict[str, Any]] = None
    residual: Optional[float] = None


class HorizontalCalibration(AxisCalibration):
    domain: str = "distance_m"  # distance_m | inline | crossline | cdp


class VerticalCalibration(AxisCalibration):
    domain: str = "TWT"  # TWT | depth_m


class VelocityEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str = "checkshot"  # checkshot | VSP | velocity_model | time_depth_curve
    id: Optional[str] = None
    version_hash: Optional[str] = None
    validity_domain: str = "TWT_to_TVDSS"
    uncertainty_band_pct: Optional[float] = None


class Pick(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pick_id: str
    kind: str  # fault_trace | horizon | dip_segment | throw_pair | well_location
    coordinates: list[dict[str, float]] = []
    epistemic_tag: str = "INTERPRETED"
    observer: str = "unknown"
    uncertainty: Optional[dict[str, Any]] = None


class DisplayDomain(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vertical_domain: VerticalDomain = VerticalDomain.TWT
    vertical_units: str = "ms"
    horizontal_domain: str = "inline_crossline"
    crs: Optional[str] = None
    vertical_exaggeration: Optional[float] = None


class CalibrationWitness(BaseModel):
    """The complete calibration witness package."""

    model_config = ConfigDict(extra="forbid")
    calibration_witness_id: str
    status: WitnessStatus = WitnessStatus.DRAFT
    purpose: list[CalibrationPurpose] = []
    evidence_ref: EvidenceRef
    display_domain: DisplayDomain
    axis_calibration_h: Optional[HorizontalCalibration] = None
    axis_calibration_v: Optional[VerticalCalibration] = None
    velocity_or_td_ref: Optional[VelocityEvidenceRef] = None
    picks: list[Pick] = []
    observer: str = "unknown"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: dict[str, Any] = {}


class CalibrationReceipt(BaseModel):
    """Receipt produced when a witness is sealed/validated."""

    model_config = ConfigDict(extra="forbid")
    witness_id: str
    validation_status: str
    gates_consumed: list[str] = []
    remaining_blockers: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
