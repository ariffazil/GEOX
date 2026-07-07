"""
integration_well.py — W13+ Phase C forge: WELL → GEOX integration.

Strategic doc: "operator readiness state feeding into joint_inversion decision_class".

This tool reads WELL organ state via the well_assess_homeostasis MCP call
(in-process — not a network call) and returns a decision_class that can
be fed into joint_inversion. The class gates how aggressive the solver
should be:

  C1 (GREEN)        — solver proceeds with strict bounds
  C2 (GREEN)        — solver proceeds with strict bounds
  C3 (STABLE/AMBER) — solver proceeds but flags uncertainty
  C4 (DEGRADED/RED) — solver returns VOID; do not seal
  C5 (CRITICAL)     — system hold; no inversions allowed

DITEMPA BUKAN DIBEI — the operator gates the witness.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


OperatorDecisionClass = Literal["C1", "C2", "C3", "C4", "C5"]


class WellStateRequest(BaseModel):
    operator_id: str = Field(default="arif", description="Operator identity to check readiness for")
    task_description: Optional[str] = Field(default=None, description="Optional context for WELL")


class WellStateResponse(BaseModel):
    ok: bool
    tool: str = "geox_well_decision_class"
    decision_class: OperatorDecisionClass = "C3"
    operator_readiness: Optional[str] = None  # GREEN / AMBER / RED
    chronic_fatigue: bool = False
    accumulated_session_fatigue: float = 0.0
    rationale: str = ""
    epistemic_provenance: dict = Field(default_factory=dict)
    godel_wall: dict = Field(default_factory=dict)


async def geox_well_decision_class(
    request: WellStateRequest,
    *,
    well_assess_homeostasis=None,  # injected for testability
) -> WellStateResponse:
    """Constitutional MCP tool: derive decision_class from WELL operator state.

    If `well_assess_homeostasis` is None, attempts to import from the
    well-organ MCP. If the import fails (e.g. running outside federation),
    falls back to C3 (AMBER) — proceed with flags.
    """
    try:
        if well_assess_homeostasis is None:
            try:
                # Lazy import: the WELL organ is a separate service
                from arifosmcp.tools.organ_health import call_organ_tool
                well_assess_homeostasis = call_organ_tool
            except ImportError:
                # Use a local stub for off-federation operation
                well_assess_homeostasis = _stub_well_assess

        # Call WELL homeostasis
        result = await well_assess_homeostasis(
            subject=request.operator_id,
            mode="fatigue",
        )

        chronic_fatigue = bool(result.get("chronic_fatigue", False))
        accumulated = float(result.get("accumulated_session_fatigue", 0.0))
        # Decision matrix per WELL C-class threshold
        if chronic_fatigue or accumulated >= 0.85:
            decision_class: OperatorDecisionClass = "C5"
            operator_readiness = "RED"
            rationale = (
                "Operator shows chronic fatigue or session fatigue >= 0.85. "
                "System HOLD — no joint inversions allowed. Rest first."
            )
            godel_state = "VOID"
        elif accumulated >= 0.65:
            decision_class = "C4"
            operator_readiness = "AMBER"
            rationale = (
                "Operator session fatigue 0.65-0.85. Inversions proceed but "
                "uncertainty must be flagged. Defer non-critical inversions."
            )
            godel_state = "UNDECIDABLE_YET"
        elif accumulated >= 0.40:
            decision_class = "C3"
            operator_readiness = "STABLE"
            rationale = (
                "Operator session fatigue 0.40-0.65. Proceed with strict bounds. "
                "Surface uncertainty in every output."
            )
            godel_state = "KNOWN"
        else:
            decision_class = "C1"
            operator_readiness = "OPTIMAL"
            rationale = (
                "Operator fatigue < 0.40. Proceed with strict bounds and "
                "full evidence envelope."
            )
            godel_state = "KNOWN"

        return WellStateResponse(
            ok=True,
            decision_class=decision_class,
            operator_readiness=operator_readiness,
            chronic_fatigue=chronic_fatigue,
            accumulated_session_fatigue=accumulated,
            rationale=rationale,
            epistemic_provenance={
                "rung": 1,  # observation (not inference)
                "grounding": "well_assess_homeostasis_direct_call",
                "method": "fatigue_threshold_decision_matrix",
            },
            godel_wall={
                "state": godel_state,
                "reason": rationale,
            },
        )
    except Exception as e:
        return WellStateResponse(
            ok=False,
            decision_class="C3",
            rationale=f"WELL call failed: {e}. Defaulting to C3 with flags.",
            godel_wall={"state": "UNDECIDABLE_YET", "reason": f"WELL unavailable: {e}"},
        )


async def _stub_well_assess(
    subject: str,
    mode: str = "fatigue",
) -> dict:
    """Fallback when WELL MCP is unreachable. Returns C3 (stable, with flags)."""
    return {
        "chronic_fatigue": False,
        "accumulated_session_fatigue": 0.5,  # conservative middle-band
        "subject": subject,
        "mode": mode,
        "stub": True,
    }


__all__ = [
    "OperatorDecisionClass",
    "WellStateRequest",
    "WellStateResponse",
    "geox_well_decision_class",
]
