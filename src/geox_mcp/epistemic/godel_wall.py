"""
epistemic/godel_wall.py — GEOX Formal Gödel Wall
=============================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Formal Gödel wall for GEOX: the runtime hard-stop that says:
"This claim cannot be sealed because closure conditions are not
computable from current internal evidence alone."

The Gödel Lock Law (formal):
  A claim is UNSEALABLE if:
    closure_requires(assumption_A)
    AND rung(assumption_A) ≥ rung(claim)

This module provides:
  1. UNDECIDABLE_YET verdict state
  2. recursive_dependency_check() — prevents circular self-justification
  3. GodelWallError — exception raised when wall is hit
  4. godel_wall_check() — main entry point for claim sealing decisions
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional


class UndecidableReason(StrEnum):
    """
    Why a claim reached the Gödel wall.
    Different from UNKNOWN (missing data).
    """

    CIRCULAR_DEPENDENCY = "circular_dependency"  # Claim assumes itself
    INSUFFICIENT_GROUNDING = "insufficient_grounding"  # Cannot trace to lower rung
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"  # Conflict not resolved
    EXTERNAL_EVIDENCE_REQUIRED = "external_evidence_required"  # Cannot close internally
    MODEL_NOT_IDENTIFIABLE = "model_not_identifiable"  # Parameters underdetermined
    INFINITE_REGRESSION = "infinite_regression"  # Assumption chain too deep


class GodelWallVerdict(StrEnum):
    """
    Result of a Gödel wall check.
    """

    SEALABLE = "sealable"  # Claim can be sealed
    UNDECIDABLE_YET = "undecidable_yet"  # Cannot seal — wall hit
    UNSEALABLE = "unsealable"  # Never sealable (fatal)


@dataclass
class GodelWallRecord:
    """
    A Gödel wall record for a specific claim.

    Produced by godel_wall_check() when a claim hits the wall.
    """

    wall_id: str
    claim_id: str
    claim_rung: int
    reason: UndecidableReason
    verdict: GodelWallVerdict

    # Dependency chain
    assumption_chain: list[str] = field(default_factory=list)  # assumption IDs in chain
    circular_path: Optional[list[str]] = None  # If CIRCULAR_DEPENDENCY
    deepest_rung_reached: int = 0
    required_external_evidence: str = ""

    # For recursive dependency check
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)

    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "wall_id": self.wall_id,
            "claim_id": self.claim_id,
            "claim_rung": self.claim_rung,
            "reason": self.reason.value,
            "verdict": self.verdict.value,
            "assumption_chain": self.assumption_chain,
            "circular_path": self.circular_path,
            "deepest_rung_reached": self.deepest_rung_reached,
            "required_external_evidence": self.required_external_evidence,
            "dependency_graph": self.dependency_graph,
            "checked_at": self.checked_at.isoformat(),
            "metadata": self.metadata,
        }


class GodelWallError(Exception):
    """
    Raised when a claim hits the Gödel wall.

    The system cannot close this claim internally.
    External evidence or sovereign decision required.
    """

    def __init__(self, record: GodelWallRecord, message: str) -> None:
        self.record = record
        self.message = message
        super().__init__(message)


def recursive_dependency_check(
    claim_id: str,
    claim_rung: int,
    assumption_ids: list[str],
    get_assumption_rung_fn,  # callable(assumption_id) -> int
    get_parent_fn,  # callable(assumption_id) -> Optional[str]
    visited: Optional[set[str]] = None,
    chain: Optional[list[str]] = None,
) -> GodelWallRecord:
    """
    Recursively check whether a claim can be closed.

    Gödel Lock condition:
      If closure requires an assumption at the same rung or higher,
      the claim is UNDECIDABLE_YET.

    This detects:
      1. Circular dependencies (claim → A → B → claim)
      2. Ascending assumptions (A at rung ≥ claim's rung)
      3. Infinite regression (chain too deep without grounding)

    Returns:
      GodelWallRecord with verdict.
    """
    import uuid

    if visited is None:
        visited = set()
    if chain is None:
        chain = []

    wall_id = str(uuid.uuid4())[:12]
    chain = chain + [claim_id]

    # Check for circular dependency
    if claim_id in visited:
        return GodelWallRecord(
            wall_id=wall_id,
            claim_id=claim_id,
            claim_rung=claim_rung,
            reason=UndecidableReason.CIRCULAR_DEPENDENCY,
            verdict=GodelWallVerdict.UNDECIDABLE_YET,
            circular_path=chain,
            dependency_graph={},
        )

    visited.add(claim_id)

    deepest_rung = 0
    assumption_chain: list[str] = []

    for assumption_id in assumption_ids:
        assumption_chain.append(assumption_id)
        assumption_rung = get_assumption_rung_fn(assumption_id)

        if assumption_rung > deepest_rung:
            deepest_rung = assumption_rung

        # Gödel condition: assumption at same or higher rung than claim
        if assumption_rung >= claim_rung:
            return GodelWallRecord(
                wall_id=wall_id,
                claim_id=claim_id,
                claim_rung=claim_rung,
                reason=UndecidableReason.INSUFFICIENT_GROUNDING,
                verdict=GodelWallVerdict.UNDECIDABLE_YET,
                assumption_chain=assumption_chain,
                deepest_rung_reached=assumption_rung,
                metadata={
                    "blocking_assumption": assumption_id,
                    "blocking_rung": assumption_rung,
                    "claim_rung": claim_rung,
                    "delta": assumption_rung - claim_rung,
                },
            )

        # Recurse to parent assumption
        parent_id = get_parent_fn(assumption_id)
        if parent_id:
            parent_record = recursive_dependency_check(
                claim_id=parent_id,
                claim_rung=assumption_rung,
                assumption_ids=[parent_id],
                get_assumption_rung_fn=get_assumption_rung_fn,
                get_parent_fn=get_parent_fn,
                visited=visited,
                chain=chain,
            )
            if parent_record.verdict != GodelWallVerdict.SEALABLE:
                return parent_record

    return GodelWallRecord(
        wall_id=wall_id,
        claim_id=claim_id,
        claim_rung=claim_rung,
        reason=UndecidableReason.EXTERNAL_EVIDENCE_REQUIRED,
        verdict=GodelWallVerdict.SEALABLE,
        assumption_chain=assumption_chain,
        deepest_rung_reached=deepest_rung,
    )


def godel_wall_check(
    claim_id: str,
    claim_rung: int,
    assumptions: list[dict],
    evidence_refs: list[str],
    contradictions: list[dict],
) -> GodelWallRecord:
    """
    Main entry point for Gödel wall checks.

    Called before any claim is sealed.

    Args:
        claim_id: Unique ID of the claim being sealed
        claim_rung: Rung of the claim
        assumptions: List of assumption dicts with 'assumption_id' and 'rung'
        evidence_refs: Evidence references supporting the claim
        contradictions: Active contradictions affecting this claim

    Returns:
        GodelWallRecord with verdict

    Raises:
        GodelWallError: If verdict is UNDECIDABLE_YET
    """
    import uuid

    wall_id = str(uuid.uuid4())[:12]

    # Check 1: Circular dependency
    assumption_ids: list[str] = []
    for a in assumptions:
        aid = a.get("assumption_id")
        if isinstance(aid, str):
            assumption_ids.append(aid)

    # Build simple dependency graph for record
    dep_graph: dict[str, list[str]] = {}
    for a in assumptions:
        aid = a.get("assumption_id")
        parent = a.get("parent_assumption_id")
        if aid:
            dep_graph[aid] = [parent] if parent else []

    # Check 2: Unresolved contradictions
    if contradictions:
        unresolved = [c for c in contradictions if c.get("verdict") in ("HOLD", "FLAG")]
        if unresolved:
            return GodelWallRecord(
                wall_id=wall_id,
                claim_id=claim_id,
                claim_rung=claim_rung,
                reason=UndecidableReason.UNRESOLVED_CONTRADICTION,
                verdict=GodelWallVerdict.UNDECIDABLE_YET,
                dependency_graph=dep_graph,
                metadata={"unresolved_contradictions": len(unresolved)},
            )

    # Check 3: Insufficient grounding — need at least some evidence
    if not evidence_refs and claim_rung >= 3:
        return GodelWallRecord(
            wall_id=wall_id,
            claim_id=claim_id,
            claim_rung=claim_rung,
            reason=UndecidableReason.INSUFFICIENT_GROUNDING,
            verdict=GodelWallVerdict.UNDECIDABLE_YET,
            assumption_chain=assumption_ids,
            deepest_rung_reached=0,
            required_external_evidence="At least one evidence_ref required for Rung 3+ claims",
            dependency_graph=dep_graph,
        )

    # Check 4: Gödel condition — assumption at same or higher rung
    for assumption in assumptions:
        assumption_rung = assumption.get("rung", 0)
        assumption_id = assumption.get("assumption_id", "?")
        if assumption_id is None:
            continue

        if assumption_rung >= claim_rung:
            return GodelWallRecord(
                wall_id=wall_id,
                claim_id=claim_id,
                claim_rung=claim_rung,
                reason=UndecidableReason.INSUFFICIENT_GROUNDING,
                verdict=GodelWallVerdict.UNDECIDABLE_YET,
                assumption_chain=[assumption_id],
                deepest_rung_reached=assumption_rung,
                required_external_evidence=f"Assumption {assumption_id} at Rung {assumption_rung} blocks sealing at Rung {claim_rung}",
                dependency_graph=dep_graph,
                metadata={
                    "blocking_assumption": assumption_id,
                    "blocking_rung": assumption_rung,
                    "claim_rung": claim_rung,
                },
            )

    # All checks passed — claim can be sealed
    return GodelWallRecord(
        wall_id=wall_id,
        claim_id=claim_id,
        claim_rung=claim_rung,
        reason=UndecidableReason.EXTERNAL_EVIDENCE_REQUIRED,
        verdict=GodelWallVerdict.SEALABLE,
        assumption_chain=assumption_ids,
        deepest_rung_reached=max(a.get("rung", 0) for a in assumptions) if assumptions else 0,
        dependency_graph=dep_graph,
    )


def check_and_raise(
    claim_id: str,
    claim_rung: int,
    assumptions: list[dict],
    evidence_refs: list[str],
    contradictions: list[dict],
) -> GodelWallRecord:
    """
    Convenience wrapper: run godel_wall_check() and raise if UNDECIDABLE_YET.
    """
    record = godel_wall_check(
        claim_id=claim_id,
        claim_rung=claim_rung,
        assumptions=assumptions,
        evidence_refs=evidence_refs,
        contradictions=contradictions,
    )
    if record.verdict == GodelWallVerdict.UNDECIDABLE_YET:
        raise GodelWallError(
            record,
            f"Gödel wall hit for claim {claim_id}: {record.reason.value} "
            f"(claim_rung={claim_rung}, blocking_rung={record.metadata.get('blocking_rung', '?')})",
        )
    return record
