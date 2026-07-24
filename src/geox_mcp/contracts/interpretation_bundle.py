"""
🌊 GEOX Interpretation Bundle — public re-export (PR-B3 reconciled).

Canonical implementation lives at:
    `geox_mcp.domain.seismic_interpret.models`     (Pydantic models)
    `geox_mcp.domain.seismic_interpret.bundle`     (builder)

This module re-exports for backward compatibility so existing callers
importing from `geox_mcp.contracts.interpretation_bundle` keep working.

Doctrine (F13):
  - preferred_hypothesis is always None from GEOX — human only.
  - seal_authority = arifOS_only. Image-only → seal_eligibility=False.
  - Bundle is auditable, not "correct Earth model."

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from geox_mcp.domain.seismic_interpret.bundle import build_interpretation_bundle
from geox_mcp.domain.seismic_interpret.models import (
    Calibration,
    EarthConstraints,
    GateResultModel,
    HypothesisModel,
    InterpretationBundle,
    InterpretBundleMode,
    InterpretRequest,
    InterpretRequestFlags,
    LimitationsModel,
    ProvenanceModel,
    bundle_json_schema,
    interpret_request_json_schema,
)

__all__ = [
    "Calibration",
    "EarthConstraints",
    "GateResultModel",
    "HypothesisModel",
    "InterpretationBundle",
    "InterpretBundleMode",
    "InterpretRequest",
    "InterpretRequestFlags",
    "LimitationsModel",
    "ProvenanceModel",
    "build_interpretation_bundle",
    "bundle_json_schema",
    "interpret_request_json_schema",
]
