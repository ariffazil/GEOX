"""
restoration_bundle.py — RestorationBundle (M1 Structural Restoration output)

Status: DRAFT_CANDIDATE — not frozen. Pending human acceptance of version,
  field semantics, and vocabulary mapping.

Dimensions (orthogonal, no conflation — see bundle_common):
  epistemic_class / lifecycle_state / authority_ceiling / constitutional_verdict.

RULE-05 Chamberlin: >=3 competing restoration models. preferred_model always null.
RULE-04 claim discipline: assumptions/limitations/falsifiers/reversal_conditions/
  provenance/receipt_id.

NOT part of claim_envelope.py (that envelope has NO static consumer and is
  broken under pydantic>=2.14 — see reconciliation artifact). Internal engine
  output schema; the MCP tool wraps this into the live claim envelope.
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


class RestorationBundle(BaseModel):
    """M1 structural restoration output. Never emits a preferred model."""

    epistemic_class: EpistemicClass = "HYPOTHESIS"
    lifecycle_state: LifecycleState = "DERIVED_CANDIDATE"
    explanation_class: ExplanationClass = "UNCLASSIFIED"
    authority_ceiling: str = AUTHORITY_CEILING  # constant — do not override
    constitutional_verdict: ConstitutionalVerdict | None = None  # owner: arifOS

    # Chamberlin (RULE-05): >=3 competing restoration models. preferred stays null.
    hypotheses: list[dict[str, Any]] = Field(
        default_factory=list,
        description=">=3 competing structural restoration models. GEOX never preferences.",
    )
    preferred_model: Any | None = Field(
        default=None,
        description="ALWAYS null — GEOX outputs QUALIFIED_CANDIDATE, never a single answer.",
    )

    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(
        default_factory=list,
        description="Per-hypothesis falsification conditions (what would refute each model).",
    )
    reversal_conditions: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(
        default_factory=list,
        description="evidence_refs / source file paths / engine versions.",
    )
    receipt_id: str | None = Field(default=None, description="Vault receipt id, if any.")

    ui_resource_uri: str | None = Field(
        default=None,
        description="Optional MCP-UI binding (ui://geox/...). Added now so the contract need not break later.",
    )

    engine_version: str = "structural_restoration/1.0.0"

    @model_validator(mode="after")
    def _enforce_invariants(self) -> RestorationBundle:
        if self.epistemic_class in FORBIDDEN_EPISTEMIC:
            raise ValueError(f"forbidden epistemic_class: {self.epistemic_class}")
        if self.preferred_model is not None:
            raise ValueError("preferred_model must be null — GEOX never preferences")
        if len(self.hypotheses) < 3:
            raise ValueError(f"need >=3 competing hypotheses (Chamberlin), got {len(self.hypotheses)}")
        if not self.provenance:
            raise ValueError("provenance must not be empty")
        return self
