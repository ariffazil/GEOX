"""
claims.py — EGS Claim & Evidence MCP Tools
=============================================
GEOX EGS: Claim lifecycle and evidence management.
Extends existing geox_claim and geox_evidence tools with EGS-pedigreed modes.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastmcp import FastMCP

from geox.egs.models.claims import (
    ClaimDomain,
    ClaimEnvelope,
    ClaimStatus,
    CompetingInterpretation,
    InterpretationSet,
)
from geox.egs.models.provenance import (
    EvidenceKind,
    EvidenceRef,
    EvidenceStrength,
    ProvenanceAction,
    ProvenanceAgentKind,
    ProvenanceChain,
    ProvenanceRecord,
)
from geox.egs.models.uncertainty import ConfidenceGrade, UncertainValue
from geox.egs.tools.query import get_claims, get_provenance, get_graph

logger = logging.getLogger("geox.egs.tools.claims")


# ═══════════════════════════════════════════════════════════════════════════════
# Claim Lifecycle Tools
# ═══════════════════════════════════════════════════════════════════════════════


async def egs_claim_create(
    title: str,
    statement: str,
    domain: str = "general",
    author: str = "",
    entity_type: str | None = None,
    entity_id: str | None = None,
    confidence_score: float = 0.5,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new geological claim with full typed structure.

    MUTATE — Creates a new claim envelope.
    """
    claims = get_claims()

    domain_enum = ClaimDomain.GENERAL
    for d in ClaimDomain:
        if d.value == domain:
            domain_enum = d
            break

    claim = ClaimEnvelope(
        title=title,
        statement=statement,
        domain=domain_enum,
        status=ClaimStatus.DRAFT,
        grade=ConfidenceGrade.NOT_GRADED,
        confidence_score=min(max(confidence_score, 0.0), 1.0),
        entity_type=entity_type,
        entity_id=entity_id,
        author=author,
        tags=tags or [],
    )

    # Add provenance
    provenance = ProvenanceRecord(
        action=ProvenanceAction.CREATED,
        agent=author or "system",
        agent_kind=ProvenanceAgentKind.HUMAN if author else ProvenanceAgentKind.SYSTEM,
        description=f"Created claim: {title}",
        entity_type="claim",
        entity_id=claim.id,
        new_version=1,
    )
    claim.add_provenance(provenance)

    claims[claim.id] = claim

    return {
        "success": True,
        "claim_id": claim.id,
        "status": claim.status.value,
        "title": claim.title,
        "statement": claim.statement[:200],
        "domain": claim.domain.value,
        "evidence_for": 0,
        "evidence_against": 0,
        "provenance_record": provenance.model_dump(mode="json"),
    }


async def egs_claim_challenge(
    claim_id: str,
    challenge_statement: str,
    challenger: str = "",
    evidence_description: str = "",
    evidence_kind: str = "other",
) -> dict[str, Any]:
    """Challenge an existing claim with contradictory evidence.

    MUTATE — Updates claim status to CHALLENGED.
    """
    claims = get_claims()

    if claim_id not in claims:
        return {
            "success": False,
            "error": f"Claim '{claim_id}' not found",
            "errorCode": "GEOX_404_DATA",
            "recoverable": True,
        }

    claim = claims[claim_id]

    # Add contradicting evidence
    evidence_kind_enum = EvidenceKind.OTHER
    for ek in EvidenceKind:
        if ek.value == evidence_kind:
            evidence_kind_enum = ek
            break

    evidence = EvidenceRef(
        evidence_kind=evidence_kind_enum,
        strength=EvidenceStrength.SINGLE_LINE,
        description=evidence_description or challenge_statement,
        source=challenger or "unknown",
        supporting=False,
        created_by=challenger,
    )
    claim.add_evidence(evidence, supporting=False)

    # Add provenance
    provenance = ProvenanceRecord(
        action=ProvenanceAction.CHALLENGED,
        agent=challenger or "system",
        agent_kind=ProvenanceAgentKind.HUMAN if challenger else ProvenanceAgentKind.SYSTEM,
        description=f"Claim challenged: {challenge_statement[:200]}",
        entity_type="claim",
        entity_id=claim_id,
        evidence_refs=[evidence.id],
    )
    claim.add_provenance(provenance)

    # Update provenance chain
    provenance_chains = get_provenance()
    if claim_id not in provenance_chains:
        provenance_chains[claim_id] = ProvenanceChain(entity_id=claim_id, entity_type="claim")
    provenance_chains[claim_id].add_record(provenance)

    return {
        "success": True,
        "claim_id": claim_id,
        "new_status": claim.status.value,
        "evidence_against": len(claim.evidence_against),
        "evidence_id": evidence.id,
        "provenance_record": provenance.model_dump(mode="json"),
    }


async def egs_evidence_attach(
    claim_id: str,
    description: str,
    evidence_kind: str = "other",
    supporting: bool = True,
    source: str = "",
    created_by: str = "",
    strength: str = "single_line",
    url: str | None = None,
) -> dict[str, Any]:
    """Attach evidence to an existing claim.

    MUTATE — Appends evidence to claim.
    """
    claims = get_claims()

    if claim_id not in claims:
        return {
            "success": False,
            "error": f"Claim '{claim_id}' not found",
            "errorCode": "GEOX_404_DATA",
            "recoverable": True,
        }

    evidence_kind_enum = EvidenceKind.OTHER
    for ek in EvidenceKind:
        if ek.value == evidence_kind:
            evidence_kind_enum = ek
            break

    strength_enum = EvidenceStrength.SINGLE_LINE
    for es in EvidenceStrength:
        if es.value == strength:
            strength_enum = es
            break

    evidence = EvidenceRef(
        evidence_kind=evidence_kind_enum,
        strength=strength_enum,
        description=description,
        source=source,
        supporting=supporting,
        created_by=created_by,
        url=url,
    )

    claim = claims[claim_id]
    claim.add_evidence(evidence, supporting=supporting)

    provenance = ProvenanceRecord(
        action=ProvenanceAction.UPDATED,
        agent=created_by or "system",
        agent_kind=ProvenanceAgentKind.HUMAN if created_by else ProvenanceAgentKind.SYSTEM,
        description=f"Evidence attached to claim: {description[:200]}",
        entity_type="claim",
        entity_id=claim_id,
        evidence_refs=[evidence.id],
    )
    claim.add_provenance(provenance)

    return {
        "success": True,
        "claim_id": claim_id,
        "evidence_id": evidence.id,
        "supporting": supporting,
        "evidence_kind": evidence_kind,
        "evidence_strength": strength,
        "total_evidence_for": len(claim.evidence_for),
        "total_evidence_against": len(claim.evidence_against),
        "claim_status": claim.status.value,
    }


async def egs_evidence_reason(
    claim_id: str,
    reason_type: str = "synthesize",
    include_alternatives: bool = False,
) -> dict[str, Any]:
    """Reason about existing evidence for a claim.

    OBS — Read-only analysis of claim evidence.
    """
    claims = get_claims()

    if claim_id not in claims:
        return {
            "success": False,
            "error": f"Claim '{claim_id}' not found",
            "errorCode": "GEOX_404_DATA",
            "recoverable": True,
        }

    claim = claims[claim_id]

    if reason_type == "synthesize":
        # Synthesize all evidence
        summary = {
            "claim_id": claim_id,
            "claim_title": claim.title,
            "claim_status": claim.status.value,
            "evidence_for": [
                {
                    "id": e.id,
                    "kind": e.evidence_kind.value,
                    "strength": e.strength.value,
                    "description": e.description[:200],
                    "source": e.source,
                }
                for e in claim.evidence_for
            ],
            "evidence_against": [
                {
                    "id": e.id,
                    "kind": e.evidence_kind.value,
                    "strength": e.strength.value,
                    "description": e.description[:200],
                    "source": e.source,
                }
                for e in claim.evidence_against
            ],
            "evidence_balance": claim.evidence_balance,
            "total_evidence": len(claim.evidence_for) + len(claim.evidence_against),
        }
        return {"success": True, "reason_type": "synthesize", "result": summary}

    elif reason_type == "grade":
        # Grade the evidence quality
        total = len(claim.evidence_for) + len(claim.evidence_against)
        direct = sum(1 for e in claim.evidence_for if e.strength == EvidenceStrength.DIRECT_MEASUREMENT)
        multiple = sum(1 for e in claim.evidence_for if e.strength == EvidenceStrength.MULTIPLE_LINES)
        single = sum(1 for e in claim.evidence_for if e.strength == EvidenceStrength.SINGLE_LINE)
        analogue = sum(1 for e in claim.evidence_for if e.strength == EvidenceStrength.ANALOGUE_INFERRED)
        speculative = sum(1 for e in claim.evidence_for if e.strength == EvidenceStrength.SPECULATIVE)

        return {
            "success": True,
            "reason_type": "grade",
            "result": {
                "total_evidence": total,
                "direct_measurements": direct,
                "multiple_independent_lines": multiple,
                "single_line": single,
                "analogue_inferred": analogue,
                "speculative": speculative,
                "contradicting_evidence": len(claim.evidence_against),
                "suggested_grade": _suggest_grade(direct, multiple, single, analogue, speculative),
            },
        }

    else:
        return {"success": False, "error": f"Unknown reason_type: {reason_type}", "recoverable": True}


def _suggest_grade(direct: int, multiple: int, single: int, analogue: int, speculative: int) -> str:
    """Suggest a confidence grade based on evidence profile."""
    if direct >= 1:
        return "AA" if multiple >= 1 else "A"
    if multiple >= 2:
        return "A"
    if multiple >= 1 and single >= 1:
        return "B"
    if single >= 1:
        return "C"
    if analogue >= 1:
        return "D"
    return "not_graded"


# ═══════════════════════════════════════════════════════════════════════════════
# Tool Registry
# ═══════════════════════════════════════════════════════════════════════════════


EGS_CLAIM_TOOLS: dict[str, dict[str, Any]] = {
    "egs_claim_create": {
        "description": "Create a new geological claim with typed evidence structure and provenance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Claim title"},
                "statement": {"type": "string", "description": "The claim statement"},
                "domain": {
                    "type": "string",
                    "enum": [d.value for d in ClaimDomain],
                    "description": "Earth science domain",
                },
                "author": {"type": "string", "description": "Who made this claim"},
                "entity_type": {"type": "string", "description": "Type of earth entity"},
                "entity_id": {"type": "string", "description": "ID of earth entity"},
                "confidence_score": {"type": "number", "description": "0.0 to 1.0"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "statement"],
            "additionalProperties": False,
        },
        "handler": egs_claim_create,
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
    "egs_claim_challenge": {
        "description": "Challenge an existing claim with contradictory evidence. Updates status to CHALLENGED.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "description": "Claim ID to challenge"},
                "challenge_statement": {"type": "string", "description": "Why this claim is wrong"},
                "challenger": {"type": "string", "description": "Who is challenging"},
                "evidence_description": {"type": "string"},
                "evidence_kind": {
                    "type": "string",
                    "enum": [e.value for e in EvidenceKind],
                },
            },
            "required": ["claim_id", "challenge_statement"],
            "additionalProperties": False,
        },
        "handler": egs_claim_challenge,
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
    "egs_evidence_attach": {
        "description": "Attach evidence to an existing claim. Can be supporting or contradictory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "description": {"type": "string", "description": "What the evidence says"},
                "evidence_kind": {
                    "type": "string",
                    "enum": [e.value for e in EvidenceKind],
                },
                "supporting": {"type": "boolean", "description": "Does it support the claim?"},
                "source": {"type": "string", "description": "Where the evidence comes from"},
                "created_by": {"type": "string"},
                "strength": {
                    "type": "string",
                    "enum": [s.value for s in EvidenceStrength],
                },
                "url": {"type": "string"},
            },
            "required": ["claim_id", "description"],
            "additionalProperties": False,
        },
        "handler": egs_evidence_attach,
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    },
    "egs_evidence_reason": {
        "description": "Analyze evidence for a claim. Synthesize or grade the evidence quality.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string"},
                "reason_type": {
                    "type": "string",
                    "enum": ["synthesize", "grade"],
                    "description": "Analysis type",
                },
                "include_alternatives": {"type": "boolean"},
            },
            "required": ["claim_id"],
            "additionalProperties": False,
        },
        "handler": egs_evidence_reason,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
}


def register_claim_tools(mcp: FastMCP) -> None:
    """Register all EGS claim/evidence tools with the FastMCP server."""
    for tool_name, tool_def in EGS_CLAIM_TOOLS.items():
        mcp.tool(name=tool_name, description=tool_def["description"])(tool_def["handler"])
        logger.info(f"Registered EGS claim tool: {tool_name}")
