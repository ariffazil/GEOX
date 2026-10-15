"""
charge_result.py — ChargeResult (M3/PSM Petroleum System Modelling output)

Status: DRAFT_CANDIDATE — not frozen. Pending human acceptance of version,
  field semantics, and vocabulary mapping.

RULE-05 Chamberlin: >=3 competing thermal histories. preferred always null.
Never self-seals an HC decision — constitutional_verdict is arifOS-owned.

NOT part of claim_envelope.py. Internal engine output schema; the MCP tool
  wraps this into the live claim envelope.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from geox_core.schemas.bundle_common import (
    AUTHORITY_CEILING,
    FORBIDDEN_EPISTEMIC,
    ConstitutionalVerdict,
    EpistemicClass,
    ExplanationClass,
    LifecycleState,
)


class ChargeResult(BaseModel):
    """PSM output: burial + thermal + maturity + charge timing."""

    epistemic_class: EpistemicClass = "HYPOTHESIS"
    lifecycle_state: LifecycleState = "DERIVED_CANDIDATE"
    explanation_class: ExplanationClass = "UNCLASSIFIED"
    authority_ceiling: str = AUTHORITY_CEILING
    constitutional_verdict: ConstitutionalVerdict | None = None

    thermal_histories: list[dict[str, Any]] = Field(
        default_factory=list,
        description=">=3 competing thermal histories (RULE-05).",
    )
    preferred_thermal_history: Any | None = Field(default=None, description="ALWAYS null.")

    maturity_metric: str | None = Field(default=None, description="e.g. EasyRo, TTI — from native thermal_maturity engine.")
    calibration_status: str = Field(
        default="UNCALIBRATED",
        description="CALIBRATED only when measured Ro/BHT validate the model; else UNCALIBRATED.",
    )
    charge_timing_valid: bool | None = Field(default=None, description="charge_ma <= trap_ma (BasinChargeSimulator timing).")

    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    reversal_conditions: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    receipt_id: str | None = Field(default=None)

    ui_resource_uri: str | None = Field(default=None)

    engine_version: str = "petroleum_system/1.0.0"

    @model_validator(mode="after")
    def _enforce_invariants(self) -> "ChargeResult":
        if self.epistemic_class in FORBIDDEN_EPISTEMIC:
            raise ValueError(f"forbidden epistemic_class: {self.epistemic_class}")
        if self.preferred_thermal_history is not None:
            raise ValueError("preferred_thermal_history must be null — GEOX never preferences")
        if len(self.thermal_histories) < 3:
            raise ValueError(f"need >=3 competing thermal histories (Chamberlin), got {len(self.thermal_histories)}")
        if not self.provenance:
            raise ValueError("provenance must not be empty")
        return self
