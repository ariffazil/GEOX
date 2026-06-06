"""
PAI Receipt — Provenance + Authority + Intent
═══════════════════════════════════════════════════════════════════
GEOX local mirror of the canonical PAI Receipt schema.

CANONICAL SOURCE: arifOS/arifosmcp/schemas/pai_receipt.py (Ratified 2026-06-06)
                 This file is the GEOX-local copy. Same schema, same contract.
                 When the canonical schema changes, this file must be updated
                 to match. Run `diff` against the canonical periodically.

GEOX-specific usage:
  - Every `geox_claim_create` and `geox_claim_seal` call must attach a PAI receipt.
  - The `geox_data_qc_bundle` and `geox_evidence_reason` outputs carry a PAI
    provenance receipt (T2 INTERNAL) — same as the tool surface.
  - Sealed claims (geox_claim_seal) must carry a T3+ PAI receipt with
    human_root = did:web:arif-fazil.com. Otherwise → HOLD.

DITEMPA BUKAN DIBERI — the boundary object, forged.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
#  ENUMS (mirror of canonical)
# ═══════════════════════════════════════════════════════════════════════════════


class ProducerType(StrEnum):
    HUMAN = "human"
    AI = "ai"
    HUMAN_ASSISTED_AI = "human_assisted_ai"
    TOOL = "tool"
    UNKNOWN = "unknown"
    MIXED = "mixed"


class Organ(StrEnum):
    ARIFOS = "arifOS"
    GEOX = "GEOX"
    WEALTH = "WEALTH"
    WELL = "WELL"
    A_FORGE = "A-FORGE"
    APEX = "APEX"
    AAA = "AAA"
    EXTERNAL = "EXTERNAL"


class IntentAction(StrEnum):
    DRAFT = "draft"
    ANALYZE = "analyze"
    PUBLISH = "publish"
    SPEND = "spend"
    TRADE = "trade"
    ALLOCATE = "allocate"
    INVEST = "invest"
    PRICE = "price"
    TRANSFER = "transfer"
    DELETE = "delete"
    DEPLOY = "deploy"
    SEAL = "seal"
    MODIFY_TREASURY = "modify_treasury"
    ADVISORY = "advisory"


class RiskClass(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ATOMIC = "atomic"


class Reversibility(StrEnum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class Tier(StrEnum):
    DRAFT = "draft"
    INTERNAL = "internal"
    EXTERNAL_CLAIM = "external_claim"
    CONSEQUENTIAL = "consequential"
    ATOMIC = "atomic"


# ═══════════════════════════════════════════════════════════════════════════════
#  CANONICAL CONSTANTS (mirror)
# ═══════════════════════════════════════════════════════════════════════════════

PAI_RECEIPT_TYPE = "arifOS.PAI.v1"
CANONICAL_HUMAN_ROOT = "did:web:arif-fazil.com"

RISK_TO_TIER: dict[RiskClass, Tier] = {
    RiskClass.LOW: Tier.DRAFT,
    RiskClass.MEDIUM: Tier.EXTERNAL_CLAIM,
    RiskClass.HIGH: Tier.CONSEQUENTIAL,
    RiskClass.ATOMIC: Tier.ATOMIC,
}

INTENT_MIN_TIER: dict[IntentAction, Tier] = {
    IntentAction.DRAFT: Tier.DRAFT,
    IntentAction.ANALYZE: Tier.INTERNAL,
    IntentAction.ADVISORY: Tier.INTERNAL,
    IntentAction.PUBLISH: Tier.EXTERNAL_CLAIM,
    IntentAction.PRICE: Tier.EXTERNAL_CLAIM,
    IntentAction.SEAL: Tier.EXTERNAL_CLAIM,
    IntentAction.SPEND: Tier.CONSEQUENTIAL,
    IntentAction.TRADE: Tier.CONSEQUENTIAL,
    IntentAction.ALLOCATE: Tier.CONSEQUENTIAL,
    IntentAction.INVEST: Tier.CONSEQUENTIAL,
    IntentAction.TRANSFER: Tier.CONSEQUENTIAL,
    IntentAction.MODIFY_TREASURY: Tier.ATOMIC,
    IntentAction.DEPLOY: Tier.CONSEQUENTIAL,
    IntentAction.DELETE: Tier.ATOMIC,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  PAI RECEIPT MODEL (mirror)
# ═══════════════════════════════════════════════════════════════════════════════


class PAIOrigin(BaseModel):
    producer_type: ProducerType
    producer_id: str
    organ: Organ
    model_id: Optional[str] = None
    tool_id: Optional[str] = None


class PAIAuthority(BaseModel):
    human_root: str = CANONICAL_HUMAN_ROOT
    delegate: str
    authority_chain: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    subdelegation_allowed: bool = False


class PAIIntent(BaseModel):
    action: IntentAction
    scope: str
    risk_class: RiskClass
    external_effect: bool
    reversibility: Reversibility = Reversibility.FULL
    requires_human_intent: bool = False
    requires_888_hold: bool = False

    @model_validator(mode="after")
    def _enforce_intent_floor(self) -> "PAIIntent":
        tier = RISK_TO_TIER[self.risk_class]
        if tier in (Tier.CONSEQUENTIAL, Tier.ATOMIC) and not self.requires_human_intent:
            object.__setattr__(self, "requires_human_intent", True)
        if tier == Tier.ATOMIC and not self.requires_888_hold:
            object.__setattr__(self, "requires_888_hold", True)
        if self.requires_888_hold and self.reversibility == Reversibility.FULL:
            object.__setattr__(self, "reversibility", Reversibility.NONE)
        return self


class PAIEvidence(BaseModel):
    sources: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    confidence: str = "unknown"
    human_reviewed: bool = False
    reviewer_id: Optional[str] = None


class PAIAudit(BaseModel):
    destination: str = "VAULT999"
    previous_receipt: Optional[str] = None
    receipt_hash: Optional[str] = None
    signature: Optional[str] = None
    vault_ref: Optional[str] = None


class PAIReceipt(BaseModel):
    receipt_type: str = PAI_RECEIPT_TYPE
    object_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    origin: PAIOrigin
    authority: PAIAuthority
    intent: PAIIntent
    evidence: PAIEvidence = Field(default_factory=PAIEvidence)
    audit: PAIAudit = Field(default_factory=PAIAudit)

    @model_validator(mode="after")
    def _enforce_receipt_type(self) -> "PAIReceipt":
        if self.receipt_type != PAI_RECEIPT_TYPE:
            raise ValueError(f"receipt_type must be '{PAI_RECEIPT_TYPE}', got {self.receipt_type!r}")
        return self


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS (mirror)
# ═══════════════════════════════════════════════════════════════════════════════


def tier_of(receipt: PAIReceipt | dict[str, Any]) -> Tier:
    if isinstance(receipt, dict):
        risk = receipt.get("intent", {}).get("risk_class", "low")
        action = receipt.get("intent", {}).get("action", "draft")
    else:
        risk = receipt.intent.risk_class
        action = receipt.intent.action
    declared_tier = RISK_TO_TIER[RiskClass(risk)]
    min_tier = INTENT_MIN_TIER[IntentAction(action)]
    tier_order = [Tier.DRAFT, Tier.INTERNAL, Tier.EXTERNAL_CLAIM, Tier.CONSEQUENTIAL, Tier.ATOMIC]
    if tier_order.index(min_tier) > tier_order.index(declared_tier):
        return min_tier
    return declared_tier


def content_hash(obj: Any) -> str:
    canonical = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mint_pai_receipt(
    *,
    object_id: str,
    producer_type: ProducerType,
    producer_id: str,
    organ: Organ,
    action: IntentAction,
    scope: str,
    risk_class: RiskClass,
    external_effect: bool = False,
    reversibility: Reversibility = Reversibility.FULL,
    delegate: str = "anonymous",
    authority_chain: Optional[list[str]] = None,
    expires_at: Optional[datetime] = None,
    subdelegation_allowed: bool = False,
    sources: Optional[list[str]] = None,
    tool_calls: Optional[list[str]] = None,
    confidence: str = "unknown",
    human_reviewed: bool = False,
    reviewer_id: Optional[str] = None,
    model_id: Optional[str] = None,
    tool_id: Optional[str] = None,
    previous_receipt: Optional[str] = None,
    destination: str = "VAULT999",
    signature: Optional[str] = None,
) -> PAIReceipt:
    intent = PAIIntent(
        action=action,
        scope=scope,
        risk_class=risk_class,
        external_effect=external_effect,
        reversibility=reversibility,
    )
    authority = PAIAuthority(
        delegate=delegate,
        authority_chain=authority_chain or ["root"],
        expires_at=expires_at,
        subdelegation_allowed=subdelegation_allowed,
    )
    evidence = PAIEvidence(
        sources=sources or [],
        tool_calls=tool_calls or [],
        confidence=confidence,
        human_reviewed=human_reviewed,
        reviewer_id=reviewer_id,
    )
    audit = PAIAudit(destination=destination, previous_receipt=previous_receipt, signature=signature)
    origin = PAIOrigin(
        producer_type=producer_type,
        producer_id=producer_id,
        organ=organ,
        model_id=model_id,
        tool_id=tool_id,
    )
    receipt = PAIReceipt(
        object_id=object_id,
        origin=origin,
        authority=authority,
        intent=intent,
        evidence=evidence,
        audit=audit,
    )
    receipt.audit.receipt_hash = content_hash(receipt.model_dump(exclude={"audit"}))
    return receipt


def attach_pai_to_payload(payload: dict[str, Any], receipt: PAIReceipt) -> dict[str, Any]:
    """Attach a PAI Receipt to a tool's output payload (the standard envelope injection)."""
    out = dict(payload)
    out["_pai_receipt"] = receipt.model_dump()
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  GEOX-SPECIFIC HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def geox_claim_receipt(
    *,
    claim_id: str,
    claim_type: str,
    truth_class: str,  # FACT | INTERPRETATION | SPECULATION
    evidence_refs: list[str],
    interpreter: str = "GEOX_ENGINE",
    model_id: str = "geox_petrophysics_v1",
    tool_id: str = "geox_claim_create",
    human_reviewed: bool = False,
    reviewer_id: Optional[str] = None,
) -> PAIReceipt:
    """Standard PAI receipt for a GEOX claim. Truth class → risk class.

    - FACT         → LOW (T2 INTERNAL analysis)
    - INTERPRETATION → MEDIUM (T3 EXTERNAL_CLAIM)
    - SPECULATION   → HIGH (T4 CONSEQUENTIAL — must have human intent)
    """
    risk_map = {
        "FACT": (RiskClass.LOW, IntentAction.ANALYZE, Reversibility.FULL),
        "INTERPRETATION": (RiskClass.MEDIUM, IntentAction.PUBLISH, Reversibility.FULL),
        "SPECULATION": (RiskClass.HIGH, IntentAction.PUBLISH, Reversibility.PARTIAL),
    }
    risk_class, action, reversibility = risk_map.get(
        truth_class.upper(), (RiskClass.MEDIUM, IntentAction.PUBLISH, Reversibility.FULL)
    )
    return mint_pai_receipt(
        object_id=claim_id,
        producer_type=ProducerType.HUMAN_ASSISTED_AI if human_reviewed else ProducerType.AI,
        producer_id=interpreter,
        organ=Organ.GEOX,
        action=action,
        scope=f"claim:{claim_type}:{claim_id}",
        risk_class=risk_class,
        external_effect=True,
        reversibility=reversibility,
        delegate=interpreter,
        sources=evidence_refs,
        tool_calls=[tool_id],
        confidence=truth_class.lower(),
        human_reviewed=human_reviewed,
        reviewer_id=reviewer_id,
        model_id=model_id,
        tool_id=tool_id,
    )


__all__ = [
    "PAI_RECEIPT_TYPE",
    "CANONICAL_HUMAN_ROOT",
    "RISK_TO_TIER",
    "INTENT_MIN_TIER",
    "ProducerType",
    "Organ",
    "IntentAction",
    "RiskClass",
    "Reversibility",
    "Tier",
    "PAIOrigin",
    "PAIAuthority",
    "PAIIntent",
    "PAIEvidence",
    "PAIAudit",
    "PAIReceipt",
    "tier_of",
    "content_hash",
    "mint_pai_receipt",
    "attach_pai_to_payload",
    "geox_claim_receipt",
]
