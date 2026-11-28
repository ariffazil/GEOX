"""Polarity and phase register — the universal prerequisite for L0/L1 contracts.

Per the GEOX Seismic Interpretation Forge Package:
- Polarity/phase register is a governance primitive; built native.
- Without it, every contrast measurement is UNKNOWN.
- Convention per SEG: SEG_NORMAL = peak = positive amplitude (black on variable-area display).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

POLARITY_SCHEMA = "geox.seismic.polarity-phase-register.v1"

# Allowed conventions (per SEG polarity standards)
PolarityConvention = Literal[
    "SEG_NORMAL",       # Peak = positive, trough = negative (default)
    "SEG_REVERSE",      # Peak = negative, trough = positive
    "EUROPEAN",         # Variable-area black = trough
    "UNKNOWN",          # Cannot determine — gates everything to HOLD/UNKNOWN
]

# Polarity sign flip relative to SEG_NORMAL
POLARITY_SIGN = {
    "SEG_NORMAL": 1.0,
    "SEG_REVERSE": -1.0,
    "EUROPEAN": -1.0,  # treat as SEG_REVERSE for amplitude arithmetic
    "UNKNOWN": None,
}


class PhaseShiftEstimate(BaseModel):
    """Single estimate of phase shift for a survey/volume."""

    model_config = ConfigDict(extra="forbid")

    method: Literal[
        "amplitude_spectrum_max",
        "kurtosis_max",
        "cross_correlation_with_well",
        "visual_inspection",
        "external_calibration_witness",
    ]
    phase_deg: float = Field(..., ge=-180.0, le=180.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    sample_size: int | None = Field(default=None, ge=1)
    notes: str | None = None


class PolarityPhaseRegister(BaseModel):
    """Canonical polarity/phase register for a seismic survey or volume.

    Per Copilot forge: "Phase/polarity register is a BUILD native governance primitive;
    required before any L0 attribute is computed."

    If polarity=UNKNOWN, all L0 contrast measurements → behavior: UNKNOWN (per Canon #0).
    """

    model_config = ConfigDict(extra="forbid")

    schema_uri: Literal[POLARITY_SCHEMA] = POLARITY_SCHEMA
    register_id: str = Field(..., pattern=r"^geox://artifact/[A-Za-z0-9_\-/.@]+$")

    # The registered scope — what this register applies to
    survey_id: str | None = None
    volume_ref: str | None = Field(
        default=None, pattern=r"^geox://volume/[A-Za-z0-9_\-/.@]+$"
    )

    # The core declaration
    polarity: PolarityConvention = Field(
        default="UNKNOWN",
        description="If UNKNOWN, all downstream L0 contracts behave as UNKNOWN.",
    )
    constant_phase_deg: float = Field(default=0.0, ge=-180.0, le=180.0)
    time_shift_ms: float = Field(default=0.0)

    # Supporting evidence — at least one estimate, or polarity=UNKNOWN is forced
    phase_estimates: list[PhaseShiftEstimate] = Field(default_factory=list)
    external_witness_ref: str | None = Field(
        default=None,
        description="geox_calibration_register_witness ID if from external authority",
    )

    # Provenance
    registered_by: str
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    superseded_by: str | None = Field(
        default=None,
        description="If this register was replaced, ref to the new register",
    )

    @field_validator("phase_estimates")
    @classmethod
    def _estimate_codes_unique(cls, v: list[PhaseShiftEstimate]) -> list:
        methods = [e.method for e in v]
        if len(methods) != len(set(methods)):
            raise ValueError("Duplicate phase estimation methods")
        return v

    def is_actionable(self) -> bool:
        """Returns False if polarity is UNKNOWN — caller must HOLD/UNKNOWN."""
        return self.polarity != "UNKNOWN"

    def polarity_sign(self) -> float | None:
        """Sign multiplier for amplitude arithmetic. None if UNKNOWN."""
        return POLARITY_SIGN[self.polarity]
