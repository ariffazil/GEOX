"""
godel_wall.py — Gap 5 (WAJIB)

GEOX_FOUNDATIONAL_GAPS_AND_GODEL_LOCK.md Part IV Gap 5:

  A claim is UNSEALABLE if:
    closure_requires(assumption_A) AND rung(A) >= rung(claim)

The Godel Wall is the runtime hard-stop. It prevents circular
self-justification by detecting recursive dependency cycles
between a claim and its supporting assumptions.

Three states must be preserved:
  KNOWN          — grounded and traceable
  UNKNOWN        — insufficiently grounded
  UNDECIDABLE_YET — not false, not true, currently unresolved

DITEMPA BUKAN DIBERI — Earth is unfinished, so GEOX must track its incompleteness.
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

# ───────────────────────────── RUNG CONSTANTS (mirror assumption_lineage) ────────
RUNG_SIGNAL = 1
RUNG_MEASUREMENT = 2
RUNG_DERIVATION = 3
RUNG_INTERPRETATION = 4
RUNG_MODEL = 5
RUNG_JUDGMENT = 6
RUNG_NARRATIVE = 7


# Imports kept lazy so this module is testable without geox_core deps.
def _rung_of_assumption(assumption_registry, assumption_id: str) -> int:
    """Look up an assumption's rung via the supplied registry."""
    a = assumption_registry.get(assumption_id)
    if a is None:
        raise KeyError(f"unknown assumption_id: {assumption_id}")
    return a.rung_origin


# ───────────────────────────── MODELS ──────────────────────────────────────────────
SealState = Literal["KNOWN", "UNKNOWN", "UNDECIDABLE_YET", "SEALED", "VOID"]


class Claim(BaseModel):
    """A claim pending seal review."""

    claim_id: str = Field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:12]}")
    rung: int = Field(..., ge=1, le=7)
    description: str = Field(..., min_length=1)
    depends_on_assumption_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    seal_state: SealState = "UNKNOWN"


class SealVerdict(BaseModel):
    """The result of a Godel Wall review."""

    claim_id: str
    state: SealState
    recursive_dependency: bool = False
    cycle_path: list[str] = Field(default_factory=list)
    reason: str
    can_seal: bool = False
    required_evidence: list[str] = Field(default_factory=list)
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ───────────────────────────── GÖDEL WALL ─────────────────────────────────────────
class GodelWall:
    """Runtime hard-stop for self-referential or under-grounded claims."""

    def __init__(self, assumption_registry) -> None:
        self._registry = assumption_registry
        self._lock = threading.RLock()
        self._claims: dict[str, Claim] = {}

    # ── claim registration ───────────────────────────────────────────────────
    def register_claim(
        self,
        rung: int,
        description: str,
        *,
        depends_on_assumption_ids: list[str] | None = None,
        claim_id: str | None = None,
    ) -> Claim:
        if not (1 <= rung <= 7):
            raise ValueError(f"rung must be 1..7, got {rung}")
        if not description.strip():
            raise ValueError("description cannot be empty")

        c = Claim(
            claim_id=claim_id or f"CLM-{uuid.uuid4().hex[:12]}",
            rung=rung,
            description=description,
            depends_on_assumption_ids=list(depends_on_assumption_ids or []),
        )
        with self._lock:
            if c.claim_id in self._claims:
                raise ValueError(f"duplicate claim_id: {c.claim_id}")
            self._claims[c.claim_id] = c
        return c

    # ── core check ───────────────────────────────────────────────────────────
    def is_sealable(self, claim_id: str) -> SealVerdict:
        """Determine whether the claim can be SEALED.

        Unsealable conditions (in order):
          1) UNDECIDABLE_YET — claim depends on assumption(s) at rung >= claim rung
             (Iron Law: lower rungs always beat higher rungs in contradiction;
              so a claim cannot be closed by an assumption at the same or
              higher rung).
          2) UNKNOWN — claim has no grounding assumptions at all.
          3) KNOWN — claim is grounded at lower rungs only → can_seal=True.
          4) Recursive cycle detected → recursive_dependency=True, UNDECIDABLE_YET.
        """
        with self._lock:
            claim = self._claims.get(claim_id)
            if claim is None:
                raise KeyError(f"unknown claim_id: {claim_id}")

            # 0. Recursive dependency check
            cycle = self._detect_cycle(claim)
            if cycle:
                v = SealVerdict(
                    claim_id=claim_id,
                    state="UNDECIDABLE_YET",
                    recursive_dependency=True,
                    cycle_path=cycle,
                    reason=(
                        "Recursive dependency detected — claim cannot be closed by assumptions that themselves depend on it."
                    ),
                    can_seal=False,
                )
                self._claims[claim_id] = claim.model_copy(update={"seal_state": v.state})
                return v

            deps = claim.depends_on_assumption_ids

            # 1. UNKNOWN — no grounding at all
            if not deps:
                v = SealVerdict(
                    claim_id=claim_id,
                    state="UNKNOWN",
                    reason=("Claim has no grounding assumptions. Attach at least one Rung 1-3 observation before sealing."),
                    can_seal=False,
                    required_evidence=["RUNG_2_OBSERVATION"],
                )
                self._claims[claim_id] = claim.model_copy(update={"seal_state": v.state})
                return v

            # 2. UNDECIDABLE_YET — any dependency at rung >= claim.rung
            invalid: list[str] = []
            for asm_id in deps:
                try:
                    rung = _rung_of_assumption(self._registry, asm_id)
                except KeyError:
                    invalid.append(f"unknown_assumption:{asm_id}")
                    continue
                if rung >= claim.rung:
                    invalid.append(f"{asm_id}@rung{rung}>=claim_rung{claim.rung}")

            if invalid:
                v = SealVerdict(
                    claim_id=claim_id,
                    state="UNDECIDABLE_YET",
                    reason=(
                        "Closure requires assumption(s) at rung >= claim rung: "
                        + ", ".join(invalid)
                        + ". Iron Law: lower rungs always beat higher rungs. "
                        "Ground at lower rung or downgrade claim."
                    ),
                    can_seal=False,
                    required_evidence=["RUNG_LOWER_THAN_CLAIM"],
                )
                self._claims[claim_id] = claim.model_copy(update={"seal_state": v.state})
                return v

            # 3. All deps are at lower rung → KNOWN, sealable
            v = SealVerdict(
                claim_id=claim_id,
                state="KNOWN",
                reason=(f"All {len(deps)} grounding assumption(s) sit at rung < {claim.rung}. Iron Law satisfied. Sealable."),
                can_seal=True,
            )
            self._claims[claim_id] = claim.model_copy(update={"seal_state": v.state})
            return v

    # ── cycle detection ──────────────────────────────────────────────────────
    def _detect_cycle(self, claim: Claim) -> list[str]:
        """Detect if claim.depends_on_assumption_ids → ... → claim.

        Walks the assumption parent_assumption_id chain. If we encounter a
        self-reference (direct or indirect) for this claim_id, return cycle path.
        """
        if not claim.depends_on_assumption_ids:
            return []

        # Build children index lazily from registry.
        children_idx: dict[str, list[str]] = {}
        for a in self._registry.all():
            if a.parent_assumption_id:
                children_idx.setdefault(a.parent_assumption_id, []).append(a.assumption_id)

        # Treat claim_id as a synthetic node; if any dependency chain leads back
        # to claim_id via parent links, we have a cycle.
        visited: set[str] = set()
        stack: list[tuple[str, list[str]]] = [(cid, [cid]) for cid in claim.depends_on_assumption_ids]
        while stack:
            node, path = stack.pop()
            if node == claim.claim_id and len(path) > 1:
                return path
            if node in visited:
                continue
            visited.add(node)
            for child in children_idx.get(node, []):
                stack.append((child, path + [child]))
        return []

    # ── seal action ──────────────────────────────────────────────────────────
    def seal(self, claim_id: str) -> SealVerdict:
        """Mark a claim SEALED if is_sealable returns can_seal=True."""
        v = self.is_sealable(claim_id)
        if v.can_seal:
            v = v.model_copy(update={"state": "SEALED"})
            with self._lock:
                c = self._claims.get(claim_id)
                if c is not None:
                    self._claims[claim_id] = c.model_copy(update={"seal_state": "SEALED"})
        return v

    def void(self, claim_id: str, reason: str) -> SealVerdict:
        """Force a claim to VOID with a documented reason."""
        with self._lock:
            c = self._claims.get(claim_id)
            if c is None:
                raise KeyError(f"unknown claim_id: {claim_id}")
            self._claims[claim_id] = c.model_copy(update={"seal_state": "VOID"})
        return SealVerdict(claim_id=claim_id, state="VOID", reason=reason, can_seal=False)

    # ── diagnostics ──────────────────────────────────────────────────────────
    def get(self, claim_id: str) -> Claim | None:
        with self._lock:
            return self._claims.get(claim_id)

    def all(self) -> list[Claim]:
        with self._lock:
            return list(self._claims.values())

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_claims": len(self._claims),
                "by_state": {
                    s: sum(1 for c in self._claims.values() if c.seal_state == s)
                    for s in ("KNOWN", "UNKNOWN", "UNDECIDABLE_YET", "SEALED", "VOID")
                },
            }


__all__ = [
    "Claim",
    "SealVerdict",
    "SealState",
    "GodelWall",
    "RUNG_SIGNAL",
    "RUNG_MEASUREMENT",
    "RUNG_DERIVATION",
    "RUNG_INTERPRETATION",
    "RUNG_MODEL",
    "RUNG_JUDGMENT",
    "RUNG_NARRATIVE",
]
