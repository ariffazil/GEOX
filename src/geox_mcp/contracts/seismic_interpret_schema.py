"""
🌊 GEOX Seismic Interpret — public re-export of the discriminated-union schema.

Canonical implementation lives at:
    `geox_mcp.domain.seismic_interpret.models`

This module re-exports for backward compatibility.

Discriminator: `mode` (Literal). 8+ live modes.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Any

from geox_mcp.domain.seismic_interpret.models import (
    BlendMode,
    Calibration as ImageCalibration,
    EarthConstraints,
    FaultSticksMode,
    HorizonContrastMode,
    InterpretBundleMode,
    InterpretRequest as SeismicInterpretRequest,
    InterpretRequestFlags,
    SectionImageMode,
    SegySliceMode,
    StructureValidateMode,
    VolumeFrameMode,
    interpret_request_json_schema as _interpret_request_json_schema,
)
from pydantic import BaseModel, ConfigDict, TypeAdapter


class StrictInterpretRequest(BaseModel):
    """Strict wrapper that rejects unknown fields at the union level.

    Pydantic's `Annotated[..., Field(discriminator=...)]` does NOT propagate
    `extra="forbid"` from inner branches up to the union wrapper, so unknown
    keys would be silently dropped. This wrapper catches that.

    Per F13 doctrine: every schema field is owned; unknowns must fail loudly.
    """

    model_config = ConfigDict(extra="forbid")

    request: SeismicInterpretRequest


def generate_json_schema() -> dict[str, Any]:
    """Return the discriminated-union JSON schema (per branch extra='forbid')."""
    return _interpret_request_json_schema()


# Backward-compat alias — older callers expect RsiPipelineMode
RsiPipelineMode = SectionImageMode

__all__ = [
    "BlendMode",
    "EarthConstraints",
    "FaultSticksMode",
    "HorizonContrastMode",
    "ImageCalibration",
    "InterpretBundleMode",
    "InterpretRequestFlags",
    "RsiPipelineMode",
    "SectionImageMode",
    "SegySliceMode",
    "SeismicInterpretRequest",
    "StrictInterpretRequest",
    "StructureValidateMode",
    "VolumeFrameMode",
    "generate_json_schema",
]
