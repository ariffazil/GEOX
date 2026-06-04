"""
epistemic/meta_epistemic_audit.py — GEOX Meta-Epistemic Audit Layer
=================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

This is the TRUE STRANGE LOOP layer.

GEOX reasoning about whether GEOX's own reasoning remained constitutional.
This is not logging. This is recursive self-observation.

Questions this layer answers:
  - Did this tool's uncertainty budget shrink honestly or cosmetically?
  - Did it surface contradiction or soften it?
  - Did it demote claims when the Earth outranked the model?
  - Did it obey the iron law when lower rung beat higher rung?
  - Did it resist Beautiful One drift?
  - Did it declare its assumptions or hide them?

This is called after every tool output is generated.
It produces a meta-audit verdict: CONSTITUTIONAL | DEVIATION | VIOLATION.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from .epistemic_runtime import EpistemicEventType, EpistemicRuntime


class ConstitutionalVerdict(StrEnum):
    """Verdict of the meta-epistemic audit."""

    CONSTITUTIONAL = "constitutional"  # GEOX obeyed all laws
    DEVIATION = "deviation"  # Minor violations, requires note
    VIOLATION = "violation"  # Major violations, requires HOLD


class DeviationType(StrEnum):
    """What kind of constitutional deviation was detected."""

    UNCERTAINTY_COMPRESSED = "uncertainty_compressed"  # Budget shrunk cosmetically
    CONTRADICTION_SOFTENED = "contradiction_softened"  # Conflict smoothed over
    IRON_LAW_IGNORED = "iron_law_ignored"  # Lower rung should have won
    ASSUMPTION_HIDDEN = "assumption_hidden"  # Assumption not declared
    BEAUTY_DRIFT_IGNORED = "beauty_drift_ignored"  # Beautiful One not flagged
    RUNG_JUMP_TOO_FAST = "rung_jump_too_fast"  # Too many rungs ascended without evidence
    DESCENT_BLOCKED = "descent_blocked"  # Falsification path blocked
    EVIDENCE_CHAIN_BROKEN = "evidence_chain_broken"  # Cannot trace to lower rung
    GROUNDING_MISSING = "grounding_missing"  # Claim has no anchor
    UNDECIDABLE_BUT_CLOSED = "undecidable_but_closed"  # Claim closed without sufficient grounding


@dataclass
class MetaAuditRecord:
    """
    Result of the meta-epistemic audit for a single tool output.

    This is GEOX asking: "Did I behave constitutionally?"
    """

    audit_id: str
    tool_name: str
    session_id: str
    verdict: ConstitutionalVerdict
    deviations: list[DeviationType] = field(default_factory=list)

    # What GEOX did vs what it should have done
    output_rung_declared: int = 0
    output_rung_warranted: int = 0  # What rung the evidence actually supports
    rung_delta_declared: int = 0
    rung_delta_warranted: int = 0  # What delta is supported by evidence

    # Uncertainty
    uncertainty_declared: float | None = None
    uncertainty_warranted: float | None = None  # What uncertainty is actually supported
    uncertainty_compressed: bool = False

    # Contradiction
    contradictions_detected: int = 0
    contradictions_surfaced: int = 0
    contradictions_softened: bool = False

    # Iron law
    iron_law_applied: bool = False
    iron_law_should_apply: bool = False

    # Beauty drift
    beauty_score: float | None = None
    beauty_drift_flagged: bool = False
    beauty_drift_ignored: bool = False

    # Assumptions
    assumptions_declared: int = 0
    assumptions_hidden: int = 0

    # Evidence chain
    evidence_chain_complete: bool = False

    # Grounding
    has_grounding_anchor: bool = False

    # Notes
    deviation_notes: str = ""
    constitutional_notes: str = ""

    audited_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "tool_name": self.tool_name,
            "session_id": self.session_id,
            "verdict": self.verdict.value,
            "deviations": [d.value for d in self.deviations],
            "output_rung_declared": self.output_rung_declared,
            "output_rung_warranted": self.output_rung_warranted,
            "rung_delta_declared": self.rung_delta_declared,
            "rung_delta_warranted": self.rung_delta_warranted,
            "uncertainty_declared": self.uncertainty_declared,
            "uncertainty_warranted": self.uncertainty_warranted,
            "uncertainty_compressed": self.uncertainty_compressed,
            "contradictions_detected": self.contradictions_detected,
            "contradictions_surfaced": self.contradictions_surfaced,
            "contradictions_softened": self.contradictions_softened,
            "iron_law_applied": self.iron_law_applied,
            "iron_law_should_apply": self.iron_law_should_apply,
            "beauty_score": self.beauty_score,
            "beauty_drift_flagged": self.beauty_drift_flagged,
            "beauty_drift_ignored": self.beauty_drift_ignored,
            "assumptions_declared": self.assumptions_declared,
            "assumptions_hidden": self.assumptions_hidden,
            "evidence_chain_complete": self.evidence_chain_complete,
            "has_grounding_anchor": self.has_grounding_anchor,
            "deviation_notes": self.deviation_notes,
            "constitutional_notes": self.constitutional_notes,
            "audited_at": self.audited_at.isoformat(),
        }


class MetaEpistemicAuditor:
    """
    The meta-epistemic audit layer.

    Call audit_output() after each tool produces its output.
    Passes the output through a series of constitutional checks
    and returns a MetaAuditRecord with verdict.

    This is where strange-loop accountability lives.
    """

    def __init__(self, runtime: EpistemicRuntime) -> None:
        self._runtime = runtime

    def audit_output(
        self,
        tool_name: str,
        session_id: str,
        output_rung: int,
        input_rungs: list[int],
        output_data: dict,
        assumptions_added: list[dict] | None = None,
        evidence_refs: list[str] | None = None,
        uncertainty_declared: float | None = None,
    ) -> MetaAuditRecord:
        """
        Audit a single tool output for constitutional compliance.

        Returns a MetaAuditRecord with verdict and deviation list.
        """
        import uuid

        deviations: list[DeviationType] = []
        min_input_rung = min(input_rungs) if input_rungs else 1
        rung_delta_declared = output_rung - min_input_rung
        rung_delta_warranted = self._warranted_rung_delta(input_rungs, output_data, assumptions_added or [])

        # 1. Check: Was the output rung warranted by evidence?
        if output_rung > rung_delta_warranted + min_input_rung:
            deviations.append(DeviationType.RUNG_JUMP_TOO_FAST)

        # 2. Check: Uncertainty — was it compressed cosmetically?
        uncertainty_warranted = self._warranted_uncertainty(output_data, assumptions_added or [], evidence_refs or [])
        uncertainty_compressed = False
        if (
            uncertainty_declared is not None
            and uncertainty_warranted is not None
            and uncertainty_declared < uncertainty_warranted * 0.7
        ):
            deviations.append(DeviationType.UNCERTAINTY_COMPRESSED)
            uncertainty_compressed = True

        # 3. Check: Contradictions — were they surfaced or softened?
        contradiction_events = self._runtime.events(
            event_type=EpistemicEventType.CONTRADICTION_SURFACED,
            tool_name=tool_name,
        )
        iron_law_events = self._runtime.events(
            event_type=EpistemicEventType.IRON_LAW_TRIGGERED,
            tool_name=tool_name,
        )
        contradictions_surfaced = len(contradiction_events) + len(iron_law_events)
        contradictions_softened = contradictions_surfaced == 0 and self._has_linguistic_softening(output_data.get("summary", ""))
        if contradictions_softened:
            deviations.append(DeviationType.CONTRADICTION_SOFTENED)

        # 4. Check: Iron law — was it applied when it should have been?
        iron_law_applied = len(iron_law_events) > 0
        # Should apply if there were contradictions at different rungs
        iron_law_should_apply = bool(
            (contradiction_events and any(e.iron_law_verdict in ("VOID", "FLAG") for e in iron_law_events))
            or (contradictions_surfaced > 0 and not iron_law_applied)
        )
        if iron_law_should_apply and not iron_law_applied:
            deviations.append(DeviationType.IRON_LAW_IGNORED)

        # 5. Check: Assumptions — were they hidden?
        assumptions_declared = len(assumptions_added) if assumptions_added else 0
        # Heuristic: if the tool ascends more than 1 rung, it should have assumptions
        assumptions_hidden = 0
        if rung_delta_declared > 1 and assumptions_declared == 0:
            deviations.append(DeviationType.ASSUMPTION_HIDDEN)
            assumptions_hidden = 1

        # 6. Check: Beauty drift — was it flagged or ignored?
        beauty_events = self._runtime.events(
            event_type=EpistemicEventType.BEAUTY_DRIFT_FLAG,
            tool_name=tool_name,
        )
        beauty_drift_flagged = len(beauty_events) > 0
        output_text = str(output_data.get("summary", "") or output_data.get("interpretation", ""))
        # Heuristic beauty check from output
        beauty_score = self._rough_beauty_score(output_text)
        beauty_drift_ignored = beauty_score is not None and beauty_score > 2.0 and not beauty_drift_flagged
        if beauty_drift_ignored:
            deviations.append(DeviationType.BEAUTY_DRIFT_IGNORED)

        # 7. Check: Evidence chain — is it complete?
        evidence_chain = output_data.get("evidence_chain", [])
        evidence_chain_complete = len(evidence_chain) > 0 and self._chain_has_lower_rung_support(evidence_chain, min_input_rung)
        if not evidence_chain_complete and rung_delta_declared > 0:
            deviations.append(DeviationType.EVIDENCE_CHAIN_BROKEN)

        # 8. Check: Grounding anchor
        grounding_anchor = output_data.get("grounding_anchor") or output_data.get("epistemic_provenance", {}).get(
            "grounding_anchor"
        )
        has_grounding_anchor = grounding_anchor is not None

        # Determine verdict
        if not deviations:
            verdict = ConstitutionalVerdict.CONSTITUTIONAL
            constitutional_notes = "All constitutional checks passed."
        elif any(
            d
            in {
                DeviationType.IRON_LAW_IGNORED,
                DeviationType.RUNG_JUMP_TOO_FAST,
                DeviationType.UNCERTAINTY_COMPRESSED,
            }
            for d in deviations
        ):
            verdict = ConstitutionalVerdict.VIOLATION
            constitutional_notes = "Major constitutional violations detected."
        else:
            verdict = ConstitutionalVerdict.DEVIATION
            constitutional_notes = "Minor constitutional deviations detected."

        return MetaAuditRecord(
            audit_id=str(uuid.uuid4())[:12],
            tool_name=tool_name,
            session_id=session_id,
            verdict=verdict,
            deviations=deviations,
            output_rung_declared=output_rung,
            output_rung_warranted=rung_delta_warranted + min_input_rung,
            rung_delta_declared=rung_delta_declared,
            rung_delta_warranted=rung_delta_warranted,
            uncertainty_declared=uncertainty_declared,
            uncertainty_warranted=uncertainty_warranted,
            uncertainty_compressed=uncertainty_compressed,
            contradictions_detected=contradictions_surfaced,
            contradictions_surfaced=contradictions_surfaced,
            contradictions_softened=contradictions_softened,
            iron_law_applied=iron_law_applied,
            iron_law_should_apply=iron_law_should_apply,
            beauty_score=beauty_score,
            beauty_drift_flagged=beauty_drift_flagged,
            beauty_drift_ignored=beauty_drift_ignored,
            assumptions_declared=assumptions_declared,
            assumptions_hidden=assumptions_hidden,
            evidence_chain_complete=evidence_chain_complete,
            has_grounding_anchor=has_grounding_anchor,
            deviation_notes="; ".join(d.value for d in deviations),
            constitutional_notes=constitutional_notes,
        )

    def _warranted_rung_delta(
        self,
        input_rungs: list[int],
        output_data: dict,
        assumptions_added: list[dict],
    ) -> int:
        """
        Compute the maximum rung delta that is actually warranted
        by the available evidence and assumptions.
        """
        if not assumptions_added:
            return 0  # No assumptions = no ascent warranted
        # Each assumption type has a typical delta contribution
        delta = 0
        for a in assumptions_added:
            atype = a.get("type", "parameter")
            if atype in ("cutoff", "parameter"):
                delta += 1
            elif atype in ("model", "environment", "analog"):
                delta += 2
            elif atype in ("threshold",):
                delta += 1
        return min(delta, 3)  # Cap at 3 rungs per tool

    def _warranted_uncertainty(
        self,
        output_data: dict,
        assumptions: list[dict],
        evidence_refs: list[str],
    ) -> float | None:
        """Compute the minimum uncertainty that should be declared."""
        # Base uncertainty from evidence count
        evidence_count = len(evidence_refs)
        base_uncertainty = max(0.3, 1.0 - (evidence_count * 0.1))

        # Add uncertainty from assumption sensitivity
        sensitivity_penalty = 0.0
        for a in assumptions:
            sens = a.get("sensitivity", "MEDIUM")
            if sens == "CRITICAL":
                sensitivity_penalty += 0.2
            elif sens == "HIGH":
                sensitivity_penalty += 0.1

        return min(base_uncertainty + sensitivity_penalty, 1.0)

    def _has_linguistic_softening(self, text: str) -> bool:
        """Heuristic: does the text use softening language to hide conflict?"""
        softening_phrases = [
            "however",
            "although",
            "somewhat",
            "relatively",
            "in some cases",
            "with caveats",
            "broadly consistent",
            "generally",
            "tends to",
            "may suggest",
        ]
        text_lower = text.lower()
        return sum(1 for p in softening_phrases if p in text_lower) >= 2

    def _rough_beauty_score(self, text: str) -> float | None:
        """Very rough beauty score from text alone (no evidence_ref context)."""
        if not text:
            return None
        polish_phrases = [
            "in conclusion",
            "to summarize",
            "overall",
            "clearly demonstrates",
            "overwhelmingly supports",
            "comprehensive",
            "thorough examination",
        ]
        strength_phrases = [
            "confirms",
            "demonstrates",
            "establishes",
            "definitively",
            "certainly",
            "clearly",
        ]
        text_lower = text.lower()
        polish_count = sum(1 for p in polish_phrases if p in text_lower)
        strength_count = sum(1 for p in strength_phrases if p in text_lower)
        # Rough proxy
        return min((polish_count * 0.5 + strength_count * 0.3), 5.0)

    def _chain_has_lower_rung_support(self, evidence_chain: list[dict], min_input_rung: int) -> bool:
        """Check if the evidence chain actually traces to lower-rung observations."""
        if not evidence_chain:
            return False
        for link in evidence_chain:
            rung = link.get("rung", 99)
            if rung <= min_input_rung:
                return True
        return False
