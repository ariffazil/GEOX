"""
event_bus.py — IntelligenceAtom + NATS pub/sub for GEOX federation flow.

Quantum-level intelligence flow backbone (per FEDERATION_INTELLIGENCE_FLOW.md).
Wraps NATS JetStream context `arifos-governance`. Publishers send
IntelligenceAtoms; subscribers receive them.

DITEMPA BUKAN DIBEI — intelligence flows, not locks.

SOT-MANIFEST
owner: FORGE (000Ω) under F13 directive
last_verified: 2026-06-22
confidence: high
scope: /root/geox/src/geox_core/governance/event_bus.py
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

# Lazy NATS import — service must not fail to start if nats-py missing.
try:
    import nats  # type: ignore
    from nats.js.errors import NotFoundError  # type: ignore
    _NATS_AVAILABLE = True
except ImportError:
    _NATS_AVAILABLE = False
    nats = None  # type: ignore
    NotFoundError = Exception  # type: ignore


NATS_URL = os.environ.get("ARIFOS_NATS_URL", "nats://127.0.0.1:4222")
STREAM_NAME = "arifos-governance"


# ───────────────────────────── INTELLIGENCE ATOM ──────────────────────────────
@dataclass
class IntelligenceAtom:
    """The universal payload flowing across the federation.

    Every GEOX tool call produces or consumes an IntelligenceAtom.
    Carries PAI Receipt + epistemic state + VAULT999 lineage.
    """

    # Identity (canonical)
    atom_id: str = ""                          # sha256 of canonical payload
    tool_name: str = ""                        # e.g. "geox_joint_inversion"
    tool_version: str = ""                     # e.g. "geox-657b9eb0"

    # Payload (tool-specific)
    result: dict = field(default_factory=dict)

    # PAI Receipt — Provenance + Authority + Intent
    pai_receipt: dict = field(default_factory=dict)

    # Constitutional state
    epistemic_ladder_rung: int = 0              # 1-7
    godel_wall_state: str = "UNKNOWN"          # KNOWN/UNKNOWN/UNDECIDABLE_YET/VOID
    constitutional_verdict: str = ""           # SEAL/SABAR/HOLD/VOID (set by arifOS Ω)

    # Topology
    emitted_at: str = ""                       # ISO 8601 UTC
    emitted_by_organ: str = "geox"
    topic: str = ""
    parent_atom_id: str | None = None

    # History
    vault_ref: str | None = None
    consumed_by: list = field(default_factory=list)

    def compute_id(self) -> str:
        """SHA-256 of canonical payload (excludes atom_id itself)."""
        canonical = json.dumps({
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "result": self.result,
            "pai_receipt": self.pai_receipt,
            "parent_atom_id": self.parent_atom_id,
        }, sort_keys=True, default=str).encode()
        return "sha256:" + hashlib.sha256(canonical).hexdigest()

    def seal(self) -> None:
        """Fill in atom_id and emitted_at if not set."""
        if not self.atom_id:
            self.atom_id = self.compute_id()
        if not self.emitted_at:
            self.emitted_at = datetime.now(UTC).isoformat()
        if not self.topic:
            self.topic = f"arifos.{self.emitted_by_organ}.intel.atom.{self.tool_name}"

    def to_json(self) -> bytes:
        return json.dumps(asdict(self), default=str).encode()

    @classmethod
    def from_json(cls, data: bytes) -> IntelligenceAtom:
        d = json.loads(data.decode())
        return cls(**d)


# ───────────────────────────── EVENT BUS ────────────────────────────────────────
class EventBus:
    """NATS JetStream wrapper for IntelligenceAtom pub/sub.

    Lazy connection: connect() on first publish/subscribe.
    Graceful degradation: if NATS unavailable, log warning + return None.
    No blocking: publish/subscribe failures never break tool execution.
    """

    def __init__(self) -> None:
        self._nc = None
        self._js = None
        self._connected = False

    @property
    def available(self) -> bool:
        return _NATS_AVAILABLE

    @property
    def connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        """Open NATS connection + ensure stream exists. Returns True on success."""
        if not _NATS_AVAILABLE:
            return False
        if self._connected:
            return True
        try:
            self._nc = await nats.connect(NATS_URL, connect_timeout=2)
            self._js = self._nc.jetstream()
            # Ensure stream exists (idempotent)
            try:
                await self._js.add_stream(
                    name=STREAM_NAME,
                    subjects=["arifos.>"],
                )
            except Exception:
                pass  # stream likely exists already
            self._connected = True
            return True
        except Exception as e:  # noqa: BLE001
            # Graceful degradation: never break tool flow.
            print(f"[event_bus] WARN: NATS connect failed: {e}")
            return False

    async def disconnect(self) -> None:
        if self._nc is not None:
            try:
                await self._nc.close()
            except Exception:
                pass
            self._nc = None
            self._js = None
            self._connected = False

    async def publish_atom(self, atom: IntelligenceAtom) -> bool:
        """Publish atom to atom.topic. Returns True on success."""
        atom.seal()
        if not await self.connect():
            return False
        try:
            await self._js.publish(atom.topic, atom.to_json())
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[event_bus] WARN: publish_atom failed for {atom.topic}: {e}")
            return False

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[IntelligenceAtom], Awaitable[None]],
    ) -> bool:
        """Subscribe to subject pattern; handler invoked per atom."""
        if not await self.connect():
            return False
        try:
            async def _wrapped(msg):
                try:
                    atom = IntelligenceAtom.from_json(msg.data)
                    await handler(atom)
                    await msg.ack()
                except Exception as e:  # noqa: BLE001
                    print(f"[event_bus] WARN: handler error for {subject}: {e}")

            await self._js.subscribe(subject, cb=_wrapped)
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[event_bus] WARN: subscribe failed for {subject}: {e}")
            return False


# ───────────────────────────── PROCESS-LOCAL SINGLETON ─────────────────────────
_bus: EventBus | None = None


def get_bus() -> EventBus:
    """Return the process-local EventBus (lazy init)."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


# ───────────────────────────── TOPIC CONSTANTS ─────────────────────────────────
# Per docs/FEDERATION_INTELLIGENCE_FLOW.md
TOPIC_GEOX_ATOM_PREFIX = "arifos.geox.intel.atom"
TOPIC_VERDICT_PREFIX = "arifos.arifos.kernel.verdict"
TOPIC_WELL_OPERATOR = "arifos.well.operator"
TOPIC_WEALTH_SIGNAL = "arifos.wealth.signal"
TOPIC_AAA_UI_COMMAND = "arifos.aaa.ui.command"
TOPIC_TASK_PROGRESS = "arifos.geox.task.progress"
TOPIC_HOLD = "arifos.geox.hold"


def topic_for_tool(tool_name: str) -> str:
    """Construct the NATS topic for a GEOX tool's intelligence atom."""
    return f"{TOPIC_GEOX_ATOM_PREFIX}.{tool_name}"


__all__ = [
    "IntelligenceAtom",
    "EventBus",
    "get_bus",
    "topic_for_tool",
    "TOPIC_GEOX_ATOM_PREFIX",
    "TOPIC_VERDICT_PREFIX",
    "TOPIC_WELL_OPERATOR",
    "TOPIC_WEALTH_SIGNAL",
    "TOPIC_AAA_UI_COMMAND",
    "TOPIC_TASK_PROGRESS",
    "TOPIC_HOLD",
    "NATS_URL",
    "STREAM_NAME",
]