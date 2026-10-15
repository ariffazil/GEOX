"""
strat_mesh_ref.py — StratMeshRef (M2/FSM Forward Stratigraphic Modelling output)

Status: DRAFT_CANDIDATE — not frozen. Pending human acceptance of version,
  field semantics, and vocabulary mapping.

RULE-05 Chamberlin: >=3 competing scenarios. preferred_scenario always null.
RULE-03: isolation_mode records import (MIT/BSD) vs subprocess (GPL/LGPL/EUPL).

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


class StratMeshRef(BaseModel):
    """Reference to an FSM stratigraphic mesh + its competing scenarios."""

    epistemic_class: EpistemicClass = "HYPOTHESIS"
    lifecycle_state: LifecycleState = "DERIVED_CANDIDATE"
    explanation_class: ExplanationClass = "UNCLASSIFIED"
    authority_ceiling: str = AUTHORITY_CEILING
    constitutional_verdict: ConstitutionalVerdict | None = None

    mesh_ref: str | None = Field(
        default=None,
        description="Artifact/HDF5 reference to the stratigraphic mesh (not the mesh itself).",
    )
    scenarios: list[dict[str, Any]] = Field(
        default_factory=list,
        description=">=3 competing forward-stratigraphic scenarios (RULE-05).",
    )
    preferred_scenario: Any | None = Field(default=None, description="ALWAYS null.")

    engine: str | None = Field(default=None, description="e.g. fastscape, landlab, goSPL")
    isolation_mode: str = Field(
        default="subprocess",
        description="RULE-03: import (MIT/BSD) vs subprocess (GPL/LGPL/EUPL).",
    )

    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    reversal_conditions: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    receipt_id: str | None = Field(default=None)

    ui_resource_uri: str | None = Field(default=None)

    engine_version: str = "strat_forward/1.0.0"

    @model_validator(mode="after")
    def _enforce_invariants(self) -> StratMeshRef:
        if self.epistemic_class in FORBIDDEN_EPISTEMIC:
            raise ValueError(f"forbidden epistemic_class: {self.epistemic_class}")
        if self.preferred_scenario is not None:
            raise ValueError("preferred_scenario must be null — GEOX never preferences")
        if len(self.scenarios) < 3:
            raise ValueError(f"need >=3 competing scenarios (Chamberlin), got {len(self.scenarios)}")
        if not self.provenance:
            raise ValueError("provenance must not be empty")
        return self
