"""
claims.py — Claim & Evidence Models for EGS
=============================================
GEOX EGS: ClaimEnvelope, competing interpretations, claim lifecycle.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from geox.egs.models.provenance import EvidenceRef, ProvenanceRecord
from geox.egs.models.uncertainty import ConfidenceGrade, ScenarioSet, UncertainValue


# ═══════════════════════════════════════════════════════════════════════════════
# Claim Status Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════


class ClaimStatus(str, Enum):
    """The lifecycle status of a geological claim."""

    DRAFT = "draft"  # In progress, not yet submitted
    PROPOSED = "proposed"  # Submitted for review
    EVIDENCE_GATHERING = "evidence_gathering"  # Actively collecting evidence
    UNDER_REVIEW = "under_review"  # Being evaluated
    ACCEPTED = "accepted"  # Supported by sufficient evidence
    CHALLENGED = "challenged"  # Contradictory evidence received
    REVISED = "revised"  # Modified in response to challenge
    REJECTED = "rejected"  # Contradicted by evidence
    SUPERSEDED = "superseded"  # Replaced by a newer claim
    RETRACTED = "retracted"  # Withdrawn by author
    SEALED = "sealed"  # Finalized, immutable


class ClaimDomain(str, Enum):
    """The domain of the claim within earth science."""

    STRATIGRAPHY = "stratigraphy"
    STRUCTURE = "structure"
    PETROPHYSICS = "petrophysics"
    SEISMIC = "seismic"
    GEOCHEMISTRY = "geochemistry"
    GEOMECHANICS = "geomechanics"
    THERMAL = "thermal"
    PRESSURE = "pressure"
    PROSPECT = "prospect"
    RESOURCE = "resource"
    BASIN = "basin"
    GENERAL = "general"


# ═══════════════════════════════════════════════════════════════════════════════
# Claim Envelope
# ═══════════════════════════════════════════════════════════════════════════════


class ClaimEnvelope(BaseModel):
    """A structured claim about earth state with evidence and provenance.

    The fundamental unit of geological discourse in EGS. Every claim
    must declare what it asserts, what evidence supports it, what
    uncertainty accompanies it, and who made it.
    """

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    title: str = Field(..., min_length=1, max_length=200, description="Claim title")
    statement: str = Field(..., min_length=1, description="The claim itself — what is being asserted")
    domain: ClaimDomain = Field(default=ClaimDomain.GENERAL, description="Earth science domain")
    status: ClaimStatus = Field(default=ClaimStatus.DRAFT, description="Lifecycle status")
    grade: ConfidenceGrade = Field(default=ConfidenceGrade.NOT_GRADED, description="Confidence grade")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Numerical confidence")

    # Entity binding — what earth entity this claim is about
    entity_type: str | None = Field(default=None, description="Type of earth entity")
    entity_id: str | None = Field(default=None, description="ID of earth entity")

    # Evidence
    evidence_for: list[EvidenceRef] = Field(default_factory=list, description="Supporting evidence")
    evidence_against: list[EvidenceRef] = Field(default_factory=list, description="Contradicting evidence")

    # Uncertainty
    uncertainty: UncertainValue | None = Field(default=None, description="Quantified uncertainty")
    alternative_scenarios: ScenarioSet | None = Field(default=None, description="Alternative interpretations")

    # Provenance
    author: str = Field(default="", description="Who made this claim")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: list[ProvenanceRecord] = Field(default_factory=list, description="Change history")

    # Governance
    tags: list[str] = Field(default_factory=list)
    parent_claim_id: str | None = Field(default=None, description="If superseded, the previous claim ID")
    child_claim_ids: list[str] = Field(default_factory=list, description="Superseding claim IDs")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_evidence(self, evidence: EvidenceRef, supporting: bool = True) -> None:
        """Add evidence to this claim."""
        if supporting:
            self.evidence_for.append(evidence)
        else:
            self.evidence_against.append(evidence)
        self.updated_at = datetime.now(timezone.utc)
        # Auto-update status
        if len(self.evidence_against) > 0 and self.status not in (
            ClaimStatus.SEALED,
            ClaimStatus.RETRACTED,
        ):
            self.status = ClaimStatus.CHALLENGED

    def add_provenance(self, record: ProvenanceRecord) -> None:
        """Add a provenance record."""
        self.provenance.append(record)
        self.updated_at = datetime.now(timezone.utc)

    @property
    def evidence_balance(self) -> float:
        """Net evidence balance: for - against / total."""
        total = len(self.evidence_for) + len(self.evidence_against)
        if total == 0:
            return 0.0
        return (len(self.evidence_for) - len(self.evidence_against)) / total


# ═══════════════════════════════════════════════════════════════════════════════
# Competing Interpretations
# ═══════════════════════════════════════════════════════════════════════════════


class CompetingInterpretation(BaseModel):
    """A competing interpretation — an alternative claim about the same entity."""

    model_config = ConfigDict(extra="forbid")
    claim: ClaimEnvelope = Field(..., description="The alternative claim")
    proponent: str = Field(default="", description="Who advocates this interpretation")
    key_differences: list[str] = Field(default_factory=list, description="How it differs from the primary claim")
    key_similarities: list[str] = Field(default_factory=list, description="How it agrees with the primary claim")
    unresolved_questions: list[str] = Field(default_factory=list, description="What remains unknown")


class InterpretationSet(BaseModel):
    """A set of competing interpretations about the same earth entity."""

    model_config = ConfigDict(extra="forbid")
    entity_id: str = Field(..., description="Entity being interpreted")
    entity_type: str = Field(..., description="Entity type")
    primary_interpretation: ClaimEnvelope = Field(..., description="Currently preferred interpretation")
    alternatives: list[CompetingInterpretation] = Field(default_factory=list, description="Alternative interpretations")
    consensus_status: str = Field(
        default="contested",
        description="e.g. consensus, contested, unresolved",
    )

    def add_alternative(self, alt: CompetingInterpretation) -> None:
        self.alternatives.append(alt)
        if len(self.alternatives) > 0:
            self.consensus_status = "contested"
