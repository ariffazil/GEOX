"""
geox_core.governance.cascade_demotion — Eureka 7: The Gödel Closure

Implements GAP 4 (Self-Audit Recursion Layer) + GAP X (Assumption Identity &
Lineage) from `GEOX_FOUNDATIONAL_GAPS_AND_GODEL_LOCK.md` — both WAJIB.

Four primitives:

  1. AssumptionLineage — every assumption gets an identity
     (id, parent_id, rung_origin, introduced_by, current_status).

  2. cascade_demote(assumption_id) — given a falsified assumption, find
     every downstream claim that inherited it. Demote their certainty.

  3. honest_vs_lucky(seal_history, falsification_history) — for a chain
     of SEALs, what fraction were eventually falsified? If high → the SEAL
     process is "lucky". If low → the SEAL process is "honest".

  4. reseal_with_history(prev_seal_hash, new_state, lineage) — write
     a new VAULT entry whose `prev_leaf` is the prior seal, so the
     chain is auditable. The "calibration history" is preserved.

This module does NOT write to VAULT999 directly. It produces the
*envelope* that the vault-seal tool will write. arifOS 888_JUDGE is
still the constitutional authority.

DITEMPA BUKAN DIBERI — the Earth falsifies. The model remembers.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────


class AssumptionStatus(StrEnum):
    """The lifecycle of an assumption in the lineage."""

    ACTIVE = "active"
    FALSIFIED = "falsified"
    INHERITED = "inherited"  # carried by a derived claim
    DEMOTED = "demoted"  # downgraded after falsification of an ancestor
    SUPERSEDED = "superseded"  # replaced by a newer model version


class RungOrigin(int, Enum):
    """Epistemic Rung where the assumption was introduced.

    Mirrors the Ladder in `GEOX_FOUNDATIONAL_GAPS_AND_GODEL_LOCK.md` Part III.
    """

    RUNG_1_SIGNAL = 1
    RUNG_2_MEASUREMENT = 2
    RUNG_3_DERIVATION = 3
    RUNG_4_INTERPRETATION = 4
    RUNG_5_MODEL = 5
    RUNG_6_JUDGMENT = 6
    RUNG_7_NARRATIVE = 7


# ── Assumption Identity & Lineage (GAP X) ───────────────────────────────────


@dataclass
class Assumption:
    """One assumption, fully traceable."""

    id: str
    parent_id: str | None
    rung_origin: RungOrigin
    introduced_by: str  # tool name or agent id
    description: str
    status: AssumptionStatus = AssumptionStatus.ACTIVE
    falsified_by: str | None = None  # evidence_ref that falsified it
    falsified_at: float | None = None  # epoch
    dependents: set[str] = field(default_factory=set)  # other assumption ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "rung_origin": int(self.rung_origin),
            "introduced_by": self.introduced_by,
            "description": self.description,
            "status": self.status.value,
            "falsified_by": self.falsified_by,
            "falsified_at": self.falsified_at,
            "dependents": sorted(self.dependents),
        }


class AssumptionLineage:
    """The registry of all assumptions in a derivation chain.

    Every T-D function, every well tie, every depth conversion can register
    its assumptions here. cascade_demote() walks the parent_id graph to
    find all claims that inherit a given assumption.
    """

    def __init__(self) -> None:
        self._assumptions: dict[str, Assumption] = {}
        self._by_parent: dict[str, set[str]] = {}  # parent_id → child ids
        self._clock = time.time

    def register(
        self,
        description: str,
        rung: RungOrigin,
        introduced_by: str,
        parent_id: str | None = None,
        assumption_id: str | None = None,
    ) -> str:
        """Register a new assumption. Returns its id.

        Auto-generates id if not provided (sha256 of description + time).
        """
        if assumption_id is None:
            seed = f"{description}|{introduced_by}|{self._clock()}"
            assumption_id = "as_" + hashlib.sha256(seed.encode()).hexdigest()[:12]
        if assumption_id in self._assumptions:
            raise ValueError(f"Assumption {assumption_id} already registered.")
        a = Assumption(
            id=assumption_id,
            parent_id=parent_id,
            rung_origin=rung,
            introduced_by=introduced_by,
            description=description,
        )
        self._assumptions[assumption_id] = a
        if parent_id is not None:
            if parent_id not in self._assumptions:
                raise ValueError(f"Parent assumption {parent_id} not registered.")
            self._assumptions[parent_id].dependents.add(assumption_id)
            self._by_parent.setdefault(parent_id, set()).add(assumption_id)
        return assumption_id

    def falsify(
        self,
        assumption_id: str,
        evidence_ref: str,
        by: str = "earth_falsification",
    ) -> list[str]:
        """Mark an assumption as falsified. Returns the cascade list
        (all dependent claims that should be demoted).

        The cascade is computed as a transitive closure over parent_id.
        """
        if assumption_id not in self._assumptions:
            raise KeyError(f"Assumption {assumption_id} not in lineage.")
        a = self._assumptions[assumption_id]
        a.status = AssumptionStatus.FALSIFIED
        a.falsified_by = evidence_ref
        a.falsified_at = self._clock()

        # Cascade: walk all dependents
        cascade = self._walk_descendants(assumption_id)
        for cid in cascade:
            if self._assumptions[cid].status == AssumptionStatus.ACTIVE:
                self._assumptions[cid].status = AssumptionStatus.DEMOTED
        return sorted(cascade)

    def _walk_descendants(self, root_id: str) -> set[str]:
        """BFS over the parent_id graph from `root_id`."""
        visited: set[str] = set()
        queue: list[str] = list(self._by_parent.get(root_id, set()))
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._by_parent.get(current, set()))
        return visited

    def get(self, assumption_id: str) -> Assumption | None:
        return self._assumptions.get(assumption_id)

    def all_active(self) -> list[Assumption]:
        return [a for a in self._assumptions.values() if a.status == AssumptionStatus.ACTIVE]

    def all_falsified(self) -> list[Assumption]:
        return [a for a in self._assumptions.values() if a.status == AssumptionStatus.FALSIFIED]

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_total": len(self._assumptions),
            "n_active": len(self.all_active()),
            "n_falsified": len(self.all_falsified()),
            "assumptions": [a.to_dict() for a in self._assumptions.values()],
        }


# ── Cascade Demotion (GAP 4) ────────────────────────────────────────────────


@dataclass
class CascadeResult:
    """The output of a cascade_demote call."""

    falsified_assumption_id: str
    evidence_ref: str
    cascaded_count: int
    demoted_assumption_ids: list[str]
    affected_seal_ids: list[str]
    cascade_risk: float  # 0.0–1.0; how much of the model is now suspect

    def to_dict(self) -> dict[str, Any]:
        return {
            "falsified_assumption_id": self.falsified_assumption_id,
            "evidence_ref": self.evidence_ref,
            "cascaded_count": self.cascaded_count,
            "demoted_assumption_ids": self.demoted_assumption_ids,
            "affected_seal_ids": self.affected_seal_ids,
            "cascade_risk": float(self.cascade_risk),
        }


def cascade_demote(
    lineage: AssumptionLineage,
    falsified_assumption_id: str,
    evidence_ref: str,
    affected_seal_ids: list[str] | None = None,
) -> CascadeResult:
    """Given a falsified assumption, compute the cascade and return a
    `CascadeResult` for the calling tool to surface in its envelope.

    `cascade_risk` = demoted_count / (active_count + demoted_count).
    A value near 1.0 means the falsification brought down most of the
    active model. A value near 0.0 means the falsification was isolated.
    """
    if falsified_assumption_id not in [a.id for a in lineage.all_falsified()] and falsified_assumption_id not in [
        a.id for a in lineage.all_active()
    ]:
        raise KeyError(f"Assumption {falsified_assumption_id} not in lineage.")
    demoted = lineage.falsify(falsified_assumption_id, evidence_ref)
    n_active = len(lineage.all_active()) + len(demoted)  # before demotion
    risk = (len(demoted) / max(n_active, 1)) if demoted else 0.0
    return CascadeResult(
        falsified_assumption_id=falsified_assumption_id,
        evidence_ref=evidence_ref,
        cascaded_count=len(demoted),
        demoted_assumption_ids=demoted,
        affected_seal_ids=affected_seal_ids or [],
        cascade_risk=min(1.0, max(0.0, float(risk))),
    )


# ── Honest vs Lucky (the honest/lucky ratio) ───────────────────────────────


@dataclass
class HonestLuckyReport:
    """For a chain of seals, what fraction were eventually falsified?"""

    n_seals: int
    n_falsified: int
    honesty_ratio: float  # 0.0 = all lucky, 1.0 = all honest
    lucky_seal_ids: list[str]
    honest_seal_ids: list[str]
    cascade_history: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_seals": self.n_seals,
            "n_falsified": self.n_falsified,
            "honesty_ratio": float(self.honesty_ratio),
            "lucky_seal_ids": self.lucky_seal_ids,
            "honest_seal_ids": self.honest_seal_ids,
            "cascade_history": self.cascade_history,
        }


def honest_vs_lucky(
    seal_history: list[dict[str, Any]],
    falsifications: list[dict[str, Any]],
) -> HonestLuckyReport:
    """Compute the honest/lucky ratio from a chain of seals and the
    list of falsifications that have occurred since.

    Each `seal_history` entry: {"seal_id": str, "claim_summary": str, ...}
    Each `falsifications` entry: {"falsified_seal_id": str, "evidence_ref": str, ...}
    """
    falsified_seal_ids: set[str] = {f.get("falsified_seal_id") for f in falsifications if f.get("falsified_seal_id")}
    lucky: list[str] = []
    honest: list[str] = []
    for s in seal_history:
        sid = s.get("seal_id")
        if sid is None:
            continue
        if sid in falsified_seal_ids:
            lucky.append(str(sid))
        else:
            honest.append(str(sid))
    n_seals = max(len(seal_history), 1)
    ratio = len(honest) / n_seals
    return HonestLuckyReport(
        n_seals=len(seal_history),
        n_falsified=len(lucky),
        honesty_ratio=ratio,
        lucky_seal_ids=lucky,
        honest_seal_ids=honest,
        cascade_history=falsifications,
    )


# ── Reseal with History (closes the 990 → 400 loop) ─────────────────────────


@dataclass
class ResealEnvelope:
    """The envelope for a re-seal that references the prior seal.

    `prev_leaf` is the merkle_leaf of the prior seal. `calibration_history`
    is the chain of (seal_id, falsifications_since) tuples. arifOS
    `arif_vault_seal` uses this envelope to write the new VAULT entry
    with proper prev_leaf linking.
    """

    new_state_summary: str
    prev_leaf: str | None
    new_assumption_ids: list[str]
    demoted_assumption_ids: list[str]
    calibration_history: list[dict[str, Any]]
    cascade_risk: float
    honest_lucky_report: dict[str, Any]
    timestamp: float
    new_payload_hash: str  # sha256 of the new state

    def to_dict(self) -> dict[str, Any]:
        return {
            "new_state_summary": self.new_state_summary,
            "prev_leaf": self.prev_leaf,
            "new_assumption_ids": self.new_assumption_ids,
            "demoted_assumption_ids": self.demoted_assumption_ids,
            "calibration_history": self.calibration_history,
            "cascade_risk": float(self.cascade_risk),
            "honest_lucky_report": self.honest_lucky_report,
            "timestamp": float(self.timestamp),
            "new_payload_hash": self.new_payload_hash,
            "eureka": "E7_cascade_demotion_2026_06_03",
        }


def reseal_with_history(
    new_state: dict[str, Any],
    prev_leaf: str | None,
    lineage: AssumptionLineage,
    cascade: CascadeResult | None,
    seal_history: list[dict[str, Any]],
    falsifications: list[dict[str, Any]],
) -> ResealEnvelope:
    """Build the envelope for a re-seal that preserves history.

    Callers (typically the geox_compare or geox_learning tools in the
    900-999 reality loop) construct a `new_state` (the calibrated T-D
    function after the new well's data) and pass the lineage + cascade
    + history. This function returns the envelope that the vault-seal
    tool will write.
    """
    hl = honest_vs_lucky(seal_history, falsifications)
    new_ids = [a.id for a in lineage.all_active()]
    demoted_ids = cascade.demoted_assumption_ids if cascade else []
    risk = cascade.cascade_risk if cascade else 0.0
    payload = json.dumps(new_state, sort_keys=True, default=str).encode()
    payload_hash = "sha256:" + hashlib.sha256(payload).hexdigest()
    calibration_history = [{"seal_id": s.get("seal_id"), "falsified_since": s.get("falsified_since", 0)} for s in seal_history]
    return ResealEnvelope(
        new_state_summary=str(new_state.get("summary", "no summary")),
        prev_leaf=prev_leaf,
        new_assumption_ids=new_ids,
        demoted_assumption_ids=demoted_ids,
        calibration_history=calibration_history,
        cascade_risk=risk,
        honest_lucky_report=hl.to_dict(),
        timestamp=time.time(),
        new_payload_hash=payload_hash,
    )


# ── Convenience: attach lineage to any envelope ─────────────────────────────


def attach_lineage_to_envelope(
    envelope: dict[str, Any],
    lineage: AssumptionLineage,
    cascade: CascadeResult | None = None,
) -> dict[str, Any]:
    """Mutate (and return) an existing envelope dict to include the
    `assumption_lineage` block + (optional) `cascade_risk`.

    This is the wiring helper that existing tool envelopes should call
    just before returning. Eureka 7 makes every GEOX tool lineage-aware
    without any surface bloat.
    """
    envelope["assumption_lineage"] = lineage.to_dict()
    if cascade is not None:
        envelope["cascade_risk"] = cascade.cascade_risk
        envelope["cascade"] = cascade.to_dict()
    return envelope
