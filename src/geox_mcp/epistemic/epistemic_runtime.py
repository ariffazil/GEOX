"""
epistemic/epistemic_runtime.py — GEOX Epistemic Metabolism Engine
================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Records rung transitions as first-class runtime events.
This transforms GEOX from a static rung classifier into a
dynamic epistemic metabolism system.

Event types:
  - RUNG_ASCENT      : Tool output reached higher rung than input
  - RUNG_DESCENT     : Interpretation pushed back toward observation (falsification)
  - ASSUMPTION_ADDED : New assumption introduced during ladder climb
  - ASSUMPTION_FALSIFIED : Existing assumption rejected by contradicting evidence
  - CONTRADICTION_SURFACED : Conflicting evidence detected between claims
  - MODEL_DEMOTED    : Model output reverted to lower-rung observation
  - CLAIM_VOIDED     : Claim declared void due to iron law violation
  - BEAUTY_DRIFT_FLAG : Rhetorical confidence exceeds evidentiary density

Every tool invocation should emit the relevant events.
The event log enables retrospective epistemic audit.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class EpistemicEventType(StrEnum):
    RUNG_ASCENT = "RUNG_ASCENT"
    RUNG_DESCENT = "RUNG_DESCENT"
    ASSUMPTION_ADDED = "ASSUMPTION_ADDED"
    ASSUMPTION_FALSIFIED = "ASSUMPTION_FALSIFIED"
    CONTRADICTION_SURFACED = "CONTRADICTION_SURFACED"
    MODEL_DEMOTED = "MODEL_DEMOTED"
    CLAIM_VOIDED = "CLAIM_VOIDED"
    BEAUTY_DRIFT_FLAG = "BEAUTY_DRIFT_FLAG"
    IRON_LAW_TRIGGERED = "IRON_LAW_TRIGGERED"
    EVIDENCE_CHAIN_EXTENDED = "EVIDENCE_CHAIN_EXTENDED"
    UNDECIDABLE_REACHED = "UNDECIDABLE_REACHED"


@dataclass
class EpistemicEvent:
    """
    A single epistemic event in the GEOX runtime event log.

    Represents a state transition in the epistemic metabolism of
    a reasoning chain. Immutable once created.
    """

    event_id: str  # Unique ID for this event
    event_type: EpistemicEventType
    tool_name: str  # Tool that triggered this event
    session_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Rung context (for RUNG_ASCENT / RUNG_DESCENT)
    from_rung: int | None = None
    to_rung: int | None = None
    rung_delta: int | None = None

    # Assumption context (for ASSUMPTION_ADDED / FALSIFIED)
    assumption_id: str | None = None
    assumption_type: str | None = None
    parent_assumption_id: str | None = None
    falsified_by: str | None = None  # Evidence_ref that caused falsification

    # Contradiction context
    contradiction_type: str | None = None
    claim_a: str | None = None
    claim_b: str | None = None
    winning_rung: int | None = None
    losing_rung: int | None = None

    # Beauty drift context
    beauty_score: float | None = None  # rhetorical_coherence / evidentiary_density
    overreach_ratio: float | None = None

    # Iron law context
    iron_law_verdict: str | None = None  # VOID | FLAG | HOLD

    # General metadata
    description: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            self.event_id = str(uuid.uuid4())[:12]

    def to_dict(self) -> dict:
        """Serialize to dict for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "tool_name": self.tool_name,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "from_rung": self.from_rung,
            "to_rung": self.to_rung,
            "rung_delta": self.rung_delta,
            "assumption_id": self.assumption_id,
            "assumption_type": self.assumption_type,
            "parent_assumption_id": self.parent_assumption_id,
            "falsified_by": self.falsified_by,
            "contradiction_type": self.contradiction_type,
            "claim_a": self.claim_a,
            "claim_b": self.claim_b,
            "winning_rung": self.winning_rung,
            "losing_rung": self.losing_rung,
            "beauty_score": self.beauty_score,
            "overreach_ratio": self.overreach_ratio,
            "iron_law_verdict": self.iron_law_verdict,
            "description": self.description,
            "metadata": self.metadata,
        }


class EpistemicRuntime:
    """
    Thread-safe event ledger for GEOX epistemic metabolism.

    Maintains a chronological log of all epistemic events across
    all tool invocations within a session.

    Enables:
      - Retrospective epistemic audit of any reasoning chain
      - Detecting patterns of assumption accumulation
      - Tracking contradiction frequency and resolution
      - Beauty drift monitoring over time
      - Falsification cascade detection
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._lock = threading.RLock()
        self._events: list[EpistemicEvent] = []

    @property
    def session_id(self) -> str:
        return self._session_id

    def emit(
        self,
        event_type: EpistemicEventType,
        tool_name: str,
        description: str = "",
        **kwargs,
    ) -> EpistemicEvent:
        """
        Emit a new epistemic event into the runtime log.

        Returns the created EpistemicEvent.
        Thread-safe.
        """
        event = EpistemicEvent(
            event_type=event_type,
            tool_name=tool_name,
            session_id=self._session_id,
            description=description,
            **kwargs,
        )
        with self._lock:
            self._events.append(event)
        return event

    def emit_rung_ascent(
        self,
        tool_name: str,
        from_rung: int,
        to_rung: int,
        assumption_ids: list[str] | None = None,
    ) -> EpistemicEvent:
        """Emit a RUNG_ASCENT event."""
        return self.emit(
            EpistemicEventType.RUNG_ASCENT,
            tool_name,
            description=f"Rung {from_rung} → {to_rung} (+{to_rung - from_rung})",
            from_rung=from_rung,
            to_rung=to_rung,
            rung_delta=to_rung - from_rung,
            metadata={"assumption_ids": assumption_ids or []},
        )

    def emit_rung_descent(
        self,
        tool_name: str,
        from_rung: int,
        to_rung: int,
        reason: str,
    ) -> EpistemicEvent:
        """Emit a RUNG_DESCENT event (falsification path)."""
        return self.emit(
            EpistemicEventType.RUNG_DESCENT,
            tool_name,
            description=f"Rung {from_rung} → {to_rung} ({reason})",
            from_rung=from_rung,
            to_rung=to_rung,
            rung_delta=to_rung - from_rung,
        )

    def emit_assumption_added(
        self,
        tool_name: str,
        assumption_id: str,
        assumption_type: str,
        rung_origin: int,
        parent_assumption_id: str | None = None,
    ) -> EpistemicEvent:
        """Emit an ASSUMPTION_ADDED event."""
        return self.emit(
            EpistemicEventType.ASSUMPTION_ADDED,
            tool_name,
            description=f"Assumption {assumption_id} ({assumption_type}) added at Rung {rung_origin}",
            assumption_id=assumption_id,
            assumption_type=assumption_type,
            parent_assumption_id=parent_assumption_id,
            metadata={"rung_origin": rung_origin},
        )

    def emit_assumption_falsified(
        self,
        tool_name: str,
        assumption_id: str,
        assumption_type: str,
        falsified_by: str,
    ) -> EpistemicEvent:
        """Emit an ASSUMPTION_FALSIFIED event."""
        return self.emit(
            EpistemicEventType.ASSUMPTION_FALSIFIED,
            tool_name,
            description=f"Assumption {assumption_id} falsified by {falsified_by}",
            assumption_id=assumption_id,
            assumption_type=assumption_type,
            falsified_by=falsified_by,
        )

    def emit_contradiction(
        self,
        tool_name: str,
        contradiction_type: str,
        claim_a: str,
        claim_b: str,
        winning_rung: int,
        losing_rung: int,
        verdict: str,
    ) -> EpistemicEvent:
        """Emit a CONTRADICTION_SURFACED event."""
        return self.emit(
            EpistemicEventType.CONTRADICTION_SURFACED,
            tool_name,
            description=f"Contradiction ({contradiction_type}): Rung {winning_rung} beats Rung {losing_rung}",
            contradiction_type=contradiction_type,
            claim_a=claim_a,
            claim_b=claim_b,
            winning_rung=winning_rung,
            losing_rung=losing_rung,
            iron_law_verdict=verdict,
        )

    def emit_beauty_drift(
        self,
        tool_name: str,
        beauty_score: float,
        overreach_ratio: float,
    ) -> EpistemicEvent:
        """Emit a BEAUTY_DRIFT_FLAG event."""
        return self.emit(
            EpistemicEventType.BEAUTY_DRIFT_FLAG,
            tool_name,
            description=f"Beauty drift detected: score={beauty_score:.2f}, overreach={overreach_ratio:.2f}",
            beauty_score=beauty_score,
            overreach_ratio=overreach_ratio,
        )

    def emit_iron_law(
        self,
        tool_name: str,
        higher_claim: str,
        higher_rung: int,
        lower_claim: str,
        lower_rung: int,
        verdict: str,
    ) -> EpistemicEvent:
        """Emit an IRON_LAW_TRIGGERED event."""
        return self.emit(
            EpistemicEventType.IRON_LAW_TRIGGERED,
            tool_name,
            description=f"Iron law: Rung {higher_rung} ({higher_claim[:50]}) VOIDed by Rung {lower_rung} ({lower_claim[:50]})",
            claim_a=higher_claim,
            claim_b=lower_claim,
            winning_rung=lower_rung,
            losing_rung=higher_rung,
            iron_law_verdict=verdict,
            metadata={"higher_rung": higher_rung, "lower_rung": lower_rung},
        )

    def events(
        self,
        event_type: EpistemicEventType | None = None,
        tool_name: str | None = None,
        limit: int = 100,
    ) -> list[EpistemicEvent]:
        """
        Retrieve events, optionally filtered by type or tool.

        Returns most recent events first (up to limit).
        """
        with self._lock:
            results = self._events
            if event_type:
                results = [e for e in results if e.event_type == event_type]
            if tool_name:
                results = [e for e in results if e.tool_name == tool_name]
            return results[-limit:][::-1]  # Most recent first

    def rung_deltas(self) -> list[int]:
        """Return all rung delta values for this session (for analysis)."""
        with self._lock:
            return [e.rung_delta for e in self._events if e.rung_delta is not None]

    def assumption_count(self) -> dict[str, int]:
        """Return counts of assumption events by type."""
        with self._lock:
            added = sum(1 for e in self._events if e.event_type == EpistemicEventType.ASSUMPTION_ADDED)
            falsified = sum(1 for e in self._events if e.event_type == EpistemicEventType.ASSUMPTION_FALSIFIED)
            return {"added": added, "falsified": falsified}

    def beauty_events(self) -> list[EpistemicEvent]:
        """Return all beauty drift events."""
        return self.events(event_type=EpistemicEventType.BEAUTY_DRIFT_FLAG)

    def iron_law_events(self) -> list[EpistemicEvent]:
        """Return all iron law triggered events."""
        return self.events(event_type=EpistemicEventType.IRON_LAW_TRIGGERED)

    def summary(self) -> dict:
        """
        Return a summary of the epistemic runtime state for this session.
        """
        with self._lock:
            by_type: dict[str, int] = {}
            for e in self._events:
                by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1

            deltas = [e.rung_delta for e in self._events if e.rung_delta is not None]
            ascents = sum(1 for d in deltas if d > 0)
            descents = sum(1 for d in deltas if d < 0)

            return {
                "session_id": self._session_id,
                "total_events": len(self._events),
                "events_by_type": by_type,
                "rung_ascents": ascents,
                "rung_descents": descents,
                "assumptions_added": by_type.get(EpistemicEventType.ASSUMPTION_ADDED.value, 0),
                "assumptions_falsified": by_type.get(EpistemicEventType.ASSUMPTION_FALSIFIED.value, 0),
                "contradictions": by_type.get(EpistemicEventType.CONTRADICTION_SURFACED.value, 0),
                "iron_law_triggers": by_type.get(EpistemicEventType.IRON_LAW_TRIGGERED.value, 0),
                "beauty_drift_flags": by_type.get(EpistemicEventType.BEAUTY_DRIFT_FLAG.value, 0),
            }


# ─── Global singleton registry ────────────────────────────────────────────────

_RUNTIME_REGISTRY: dict[str, EpistemicRuntime] = {}
_RUNTIME_REGISTRY_LOCK = threading.Lock()


def get_or_create_runtime(session_id: str) -> EpistemicRuntime:
    """Get or create an EpistemicRuntime for the given session ID."""
    with _RUNTIME_REGISTRY_LOCK:
        if session_id not in _RUNTIME_REGISTRY:
            _RUNTIME_REGISTRY[session_id] = EpistemicRuntime(session_id)
        return _RUNTIME_REGISTRY[session_id]


def get_runtime(session_id: str) -> EpistemicRuntime | None:
    """Get an existing runtime, or None if not found."""
    with _RUNTIME_REGISTRY_LOCK:
        return _RUNTIME_REGISTRY.get(session_id)
