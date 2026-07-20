"""
subscriber.py — listens for upstream events and adapts GEOX state.

Per docs/FEDERATION_INTELLIGENCE_FLOW.md, GEOX is entangled with:
- WELL (operator readiness) → gates reasoning aggressiveness
- arifOS Ω (kernel verdicts) → applies F1-F13 to outputs
- WEALTH (capital signals) → flags prospects that drop below threshold

This module maintains an in-memory shared state (the GEOX "quantum state")
that downstream tool calls read on invocation.

DITEMPA BUKAN DIBEI — listen before you speak.

SOT-MANIFEST
owner: FORGE (000Ω) under F13 directive
last_verified: 2026-06-22
confidence: high
scope: /root/geox/src/geox_mcp/events/subscriber.py
"""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass, field

from geox_core.governance.event_bus import (
    TOPIC_HOLD,
    TOPIC_VERDICT_PREFIX,
    TOPIC_WEALTH_SIGNAL,
    TOPIC_WELL_OPERATOR,
    IntelligenceAtom,
    get_bus,
)


# ───────────────────────────── QUANTUM STATE ────────────────────────────────────
@dataclass
class QuantumState:
    """In-memory shared state populated by subscribers, read by tools."""

    # From WELL
    operator_decision_class: str = "C3"  # default conservative middle
    operator_fatigue: float = 0.5
    operator_actor_id: str | None = None
    operator_updated_at: str | None = None

    # From arifOS Ω
    latest_kernel_verdict: str = ""  # SEAL / SABAR / HOLD / VOID
    latest_kernel_verdict_atom_id: str | None = None
    kernel_verdict_updated_at: str | None = None

    # From WEALTH
    latest_capital_signal: str = ""  # REJECT / DEFER / ADVANCE
    latest_capital_asset_id: str | None = None
    capital_signal_updated_at: str | None = None

    # Global HOLD
    global_hold: bool = False
    global_hold_reason: str = ""
    global_hold_at: str | None = None

    # Atoms consumed (for audit / replay)
    consumed_atom_ids: list = field(default_factory=list)

    def is_global_hold(self) -> bool:
        return self.global_hold

    def operator_is_c5(self) -> bool:
        return self.operator_decision_class == "C5"

    def summary(self) -> dict:
        return {
            "operator_decision_class": self.operator_decision_class,
            "operator_fatigue": self.operator_fatigue,
            "operator_actor_id": self.operator_actor_id,
            "operator_updated_at": self.operator_updated_at,
            "latest_kernel_verdict": self.latest_kernel_verdict,
            "latest_kernel_verdict_atom_id": self.latest_kernel_verdict_atom_id,
            "kernel_verdict_updated_at": self.kernel_verdict_updated_at,
            "latest_capital_signal": self.latest_capital_signal,
            "latest_capital_asset_id": self.latest_capital_asset_id,
            "capital_signal_updated_at": self.capital_signal_updated_at,
            "global_hold": self.global_hold,
            "global_hold_reason": self.global_hold_reason,
            "global_hold_at": self.global_hold_at,
            "atoms_consumed": len(self.consumed_atom_ids),
        }


# Process-local singleton
_state = QuantumState()
_state_lock = threading.Lock()


def get_state() -> QuantumState:
    """Return the process-local quantum state."""
    return _state


def apply_atom(atom: IntelligenceAtom) -> None:
    """Update state from a received atom.

    Pattern-matches on atom.tool_name or atom.godel_wall_state.
    Idempotent — re-applying the same atom has no effect.
    """
    global _state
    with _state_lock:
        # Track consumption
        if atom.atom_id and atom.atom_id not in _state.consumed_atom_ids:
            _state.consumed_atom_ids.append(atom.atom_id)
            # Cap history at 1000 atoms to bound memory
            if len(_state.consumed_atom_ids) > 1000:
                _state.consumed_atom_ids = _state.consumed_atom_ids[-500:]

        # WELL operator state
        if "well" in atom.topic.lower() and "operator" in atom.topic.lower():
            r = atom.result or {}
            decision = r.get("decision_class") or atom.godel_wall_state
            fatigue = r.get("accumulated_session_fatigue", 0.5)
            actor = r.get("operator_actor_id") or atom.pai_receipt.get("actor_id")
            _state.operator_decision_class = decision or "C3"
            _state.operator_fatigue = float(fatigue)
            _state.operator_actor_id = actor
            _state.operator_updated_at = atom.emitted_at
            # C5 = auto-HOLD
            if decision == "C5":
                _state.global_hold = True
                _state.global_hold_reason = f"WELL operator {actor} at C5 (fatigue={fatigue:.2f})"
                _state.global_hold_at = atom.emitted_at

        # arifOS kernel verdict
        if atom.topic.startswith(TOPIC_VERDICT_PREFIX):
            # Prioritize constitutional_verdict (the actual arifOS verdict)
            # over godel_wall_state (the GEOX-internal epistemic state).
            _state.latest_kernel_verdict = atom.constitutional_verdict or atom.godel_wall_state
            _state.latest_kernel_verdict_atom_id = atom.atom_id
            _state.kernel_verdict_updated_at = atom.emitted_at

        # WEALTH capital signal
        if "wealth" in atom.topic.lower() and "signal" in atom.topic.lower():
            r = atom.result or {}
            _state.latest_capital_signal = r.get("verdict", "")
            _state.latest_capital_asset_id = r.get("asset_id") or atom.pai_receipt.get("asset_id")
            _state.capital_signal_updated_at = atom.emitted_at

        # Direct HOLD event
        if atom.topic == TOPIC_HOLD:
            _state.global_hold = True
            _state.global_hold_reason = atom.result.get("reason", "888_HOLD")
            _state.global_hold_at = atom.emitted_at

        # UNDO HOLD if verdict is SEAL (only arifOS can undo)
        if (
            atom.topic.startswith(TOPIC_VERDICT_PREFIX)
            and atom.constitutional_verdict == "SEAL"
            and _state.global_hold_reason.startswith("WELL operator")
        ):
            # WELL fatigue recovered → CLEAR_HOLD on next SEAL
            _state.global_hold = False
            _state.global_hold_reason = ""


# ───────────────────────────── SUBSCRIBER LIFECYCLE ────────────────────────────
class Subscriber:
    """Manages the GEOX quantum-flow subscriber lifecycle."""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> bool:
        """Subscribe to upstream topics; return True on success."""
        if self._running:
            return True

        bus = get_bus()
        if not await bus.connect():
            return False

        self._tasks.append(asyncio.create_task(bus.subscribe(f"{TOPIC_WELL_OPERATOR}.*", _on_well_operator)))
        self._tasks.append(asyncio.create_task(bus.subscribe(f"{TOPIC_VERDICT_PREFIX}.*", _on_kernel_verdict)))
        self._tasks.append(asyncio.create_task(bus.subscribe(f"{TOPIC_WEALTH_SIGNAL}.*", _on_wealth_signal)))
        self._tasks.append(asyncio.create_task(bus.subscribe(TOPIC_HOLD, _on_hold)))
        self._running = True
        return True

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()
        self._running = False


async def _on_well_operator(atom: IntelligenceAtom) -> None:
    apply_atom(atom)


async def _on_kernel_verdict(atom: IntelligenceAtom) -> None:
    apply_atom(atom)


async def _on_wealth_signal(atom: IntelligenceAtom) -> None:
    apply_atom(atom)


async def _on_hold(atom: IntelligenceAtom) -> None:
    apply_atom(atom)


# ───────────────────────────── MODULE SINGLETON ────────────────────────────────
_subscriber: Subscriber | None = None


def get_subscriber() -> Subscriber:
    global _subscriber
    if _subscriber is None:
        _subscriber = Subscriber()
    return _subscriber


__all__ = [
    "QuantumState",
    "get_state",
    "apply_atom",
    "Subscriber",
    "get_subscriber",
]
