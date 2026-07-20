"""
doctrine.py — MCP tool wrappers for the doctrine layer (W2-W4 forge).

Constitutional MCP surface for:
- Assumption Lineage (Gap X)
- Anti-Beautiful-One detector (Gap 3)
- Gödel Wall runtime hard-stop (Gap 5)

These tools are JUDGMENT-lane (lease + session + 888 required). They wrap the
doctrine engines in GEOX_FOUNDATIONAL_GAPS_AND_GODEL_LOCK.md Part IV.

DITEMPA BUKAN DIBEI — the doctrine is forged, not given; it is auditable.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from geox_core.anti_beautiful_one import audit, decompose
from geox_core.assumption_lineage import (
    Assumption,
    AssumptionRegistry,
    get_default_registry,
)
from geox_core.godel_wall import GodelWall


# ───────────────────────────── ASSUMPTION LINEAGE ─────────────────────────────────
class AssumptionRegisterRequest(BaseModel):
    introduced_by: str = Field(..., min_length=1, description="Tool name that introduces this assumption")
    rung_origin: int = Field(..., ge=1, le=7)
    description: str = Field(..., min_length=1)
    parent_assumption_id: str | None = None
    inherited_from: str | None = None
    epistemic_label: str = Field(default="DER", pattern="^(OBS|DER|INT|SPEC)$")


class AssumptionRegisterResponse(BaseModel):
    ok: bool
    tool: str = "geox_doctrine_assumption_register"
    assumption: Assumption | None = None
    error: str | None = None


async def geox_doctrine_assumption_register(
    request: AssumptionRegisterRequest,
    *,
    registry: AssumptionRegistry | None = None,
) -> AssumptionRegisterResponse:
    """JUDGMENT-lane MCP tool: register an assumption in the lineage."""
    try:
        r = registry or get_default_registry()
        a = r.register(
            introduced_by=request.introduced_by,
            rung_origin=request.rung_origin,
            description=request.description,
            parent_assumption_id=request.parent_assumption_id,
            inherited_from=request.inherited_from,
            epistemic_label=request.epistemic_label,
        )
        return AssumptionRegisterResponse(ok=True, assumption=a)
    except Exception as e:
        return AssumptionRegisterResponse(ok=False, error=str(e))


# ───────────────────────────── ANTI-BEAUTIFUL-ONE ─────────────────────────────────
class BeautyAuditRequest(BaseModel):
    text: str = Field(..., description="The claim text to audit")
    grounding_evidence_count: int = Field(default=0, ge=0)
    grounding_evidence_rungs: list[int] = Field(default_factory=list)
    threshold: float = Field(default=1.5, gt=0.0)
    include_decomposition: bool = Field(default=True)


class BeautyAuditResponse(BaseModel):
    ok: bool
    tool: str = "geox_doctrine_anti_beautiful_one"
    decomposition_required: bool = False
    decomposition_prompt: str | None = None
    audit: dict = Field(default_factory=dict)


async def geox_doctrine_anti_beautiful_one(request: BeautyAuditRequest) -> BeautyAuditResponse:
    """JUDGMENT-lane MCP tool: run Anti-Beautiful-One audit on a claim."""
    if request.include_decomposition:
        d = decompose(
            request.text,
            grounding_evidence_count=request.grounding_evidence_count,
            grounding_evidence_rungs=request.grounding_evidence_rungs,
            threshold=request.threshold,
        )
        return BeautyAuditResponse(
            ok=True,
            decomposition_required=d["decomposition_required"],
            decomposition_prompt=d.get("decomposition_prompt"),
            audit=d["audit"],
        )
    a = audit(
        request.text,
        grounding_evidence_count=request.grounding_evidence_count,
        grounding_evidence_rungs=request.grounding_evidence_rungs,
        threshold=request.threshold,
    )
    return BeautyAuditResponse(
        ok=True,
        decomposition_required=(a.verdict == "BEAUTIFUL_ONE_DRIFT"),
        audit={
            "verdict": a.verdict,
            "action": a.action,
            "beauty_overreach_score": (None if a.beauty_overreach_score == float("inf") else a.beauty_overreach_score),
            "certainty_gradient": a.certainty_gradient,
            "grounding_gradient": a.grounding_gradient,
            "matched_certainty": list(a.matched_certainty),
            "explanation": a.explanation,
        },
    )


# ───────────────────────────── GÖDEL WALL ──────────────────────────────────────────
class GodelClaimRequest(BaseModel):
    rung: int = Field(..., ge=1, le=7)
    description: str = Field(..., min_length=1)
    depends_on_assumption_ids: list[str] = Field(default_factory=list)


class GodelSealRequest(BaseModel):
    claim_id: str = Field(..., min_length=1)
    action: str = Field(default="review", pattern="^(review|seal|void)$")
    void_reason: str | None = None


class GodelResponse(BaseModel):
    ok: bool
    tool: str
    verdict: dict | None = None
    claim: dict | None = None
    error: str | None = None


async def geox_doctrine_godel_register_claim(
    request: GodelClaimRequest,
    *,
    wall: GodelWall | None = None,
) -> GodelResponse:
    """JUDGMENT-lane MCP tool: register a claim for Gödel Wall review."""
    try:
        w = wall or GodelWall(get_default_registry())
        c = w.register_claim(
            rung=request.rung,
            description=request.description,
            depends_on_assumption_ids=request.depends_on_assumption_ids,
        )
        return GodelResponse(ok=True, tool="geox_doctrine_godel_register_claim", claim=c.model_dump())
    except Exception as e:
        return GodelResponse(ok=False, tool="geox_doctrine_godel_register_claim", error=str(e))


async def geox_doctrine_godel_review(
    request: GodelSealRequest,
    *,
    wall: GodelWall | None = None,
) -> GodelResponse:
    """JUDGMENT-lane MCP tool: review / seal / void a claim via Gödel Wall."""
    try:
        w = wall or GodelWall(get_default_registry())
        if request.action == "seal":
            v = w.seal(request.claim_id)
        elif request.action == "void":
            v = w.void(request.claim_id, request.void_reason or "operator override")
        else:
            v = w.is_sealable(request.claim_id)
        return GodelResponse(ok=True, tool="geox_doctrine_godel_review", verdict=v.model_dump())
    except Exception as e:
        return GodelResponse(ok=False, tool="geox_doctrine_godel_review", error=str(e))


__all__ = [
    "AssumptionRegisterRequest",
    "AssumptionRegisterResponse",
    "geox_doctrine_assumption_register",
    "BeautyAuditRequest",
    "BeautyAuditResponse",
    "geox_doctrine_anti_beautiful_one",
    "GodelClaimRequest",
    "GodelSealRequest",
    "GodelResponse",
    "geox_doctrine_godel_register_claim",
    "geox_doctrine_godel_review",
]
