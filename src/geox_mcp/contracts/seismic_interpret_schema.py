"""
🌊 GEOX Seismic Interpret — public re-export of the discriminated-union schema.

Canonical implementation lives at:
    `geox_mcp.domain.seismic_interpret.models`

This module re-exports for backward compatibility.

Discriminator: `mode` (Literal). 8+ live modes.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

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
    interpret_request_json_schema as generate_json_schema,
)

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
    "StructureValidateMode",
    "VolumeFrameMode",
    "generate_json_schema",
]