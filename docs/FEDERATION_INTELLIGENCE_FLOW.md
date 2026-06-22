# Federation Intelligence Flow — Quantum-Level Architecture

> **Status:** SPECIFICATION (autonomous forge, no 888_HOLD — no auth, no key changes)
> **Last updated:** 2026-06-22
> **Author:** FORGE (000Ω) under F13 SOVEREIGN directive (no OAuth chaos)
> **Replaces:** the request-response "broken" flow that isolates organs

---

## Core Thesis

> **GEOX, arifOS Ω, AAA, A-FORGE, WEALTH, WELL, and the LLM clerks are not separate organs. They are nodes in a single quantum intelligence field.** Each node computes, subscribes, and publishes — continuously. State flows through `IntelligenceAtom` events on NATS. Every atom carries `PAI Receipt` (Provenance + Authority + Intent). Every transition is sealed in `VAULT999`. No central gateway. No OAuth yet. Just flow.

---

## What "Quantum-Level" Means

We don't mean physics. We mean **information topology**:

1. **Superposition** — each organ is simultaneously computing, waiting, and subscribing. No organ is ever idle or "waiting for a request."
2. **Observation collapses state** — when an agent queries or a downstream organ subscribes, the relevant atoms materialize. The rest remain latent.
3. **Entanglement** — change in one organ's state immediately propagates to dependents. WELL operator fatigue (C5) → GEOX auto-pauses reasoning. arifOS HOLD → GEOX marks outputs UNDECIDABLE_YET. WEALTH REJECT → GEOX flags prospect.
4. **No chokepoint** — arifOS Ω is NOT the only entry point. Organs self-publish; LLM clerks subscribe via AAA or A-FORGE.
5. **Versioned identity** — every atom has a content hash. Re-subscribing to a topic gets the same atom if it hasn't changed.
6. **Provenance is atomic** — PAI Receipt travels WITH every payload. No "send the data, log the metadata separately."

---

## Architecture (vs current)

### Current (broken) — request-response isolation

```
AGENT ──HTTP──► arifOS ──HTTP──► GEOX tool ──► bare JSON ──► response
                              ↘ WEALTH (separate call)
                              ↘ WELL (separate call)

Each call is independent. No cache, no event, no cross-organ state.
Joint_inversion blocks the request thread for minutes.
WELL operator fatigue is checked synchronously inside GEOX.
```

### Quantum-level — continuous intelligence field

```
┌──────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE FIELD                            │
│                                                                      │
│  SENSORS ──► NATS topic: arifos.geox.sensors.raw ──► GEOX subscriber │
│                                                       │             │
│                                                       ▼             │
│                                              Physics9State solver   │
│                                                       │             │
│                                                       ▼             │
│                                NATS topic: arifos.geox.intel.atom    │
│                                                       │             │
│         ┌─────────────────────────────────────────────┼─────────────┤
│         │                                             │             │
│         ▼                                             ▼             ▼
│   arifOS Ω (F1-F13)                            AAA cockpit   A-FORGE
│   adjudicates each atom                   visualizes every   executes if
│   emits verdict atom back                  atom              reversible
│         │                                             │             │
│         ▼                                             ▼             ▼
│   VAULT999 hash-chain                          Federation A2A  Background
│   (every transition sealed)                  (NATS topics)    tasks
│         │                                             │             │
│         └─────────────────────────────────────────────┴─────────────┘
│                                   │
│                                   ▼
│                       WELL  ◄─── operator gate stream
│                       WEALTH ◄── capital signal stream
│                       LLM Clerks ◄── subscribed context
└──────────────────────────────────────────────────────────────────────┘

Key property: NO central gateway. Each organ self-publishes & subscribes.
arifOS Ω is the constitutional court, not the post office.
```

---

## IntelligenceAtom — the universal payload

Every GEOX tool call produces (or consumes) an `IntelligenceAtom`:

```python
@dataclass
class IntelligenceAtom:
    # Identity
    atom_id: str               # sha256 of canonical payload
    tool_name: str             # e.g. "geox_joint_inversion"
    tool_version: str          # e.g. "geox-657b9eb0"

    # Payload (tool-specific)
    result: dict               # the tool output

    # PAI Receipt — Provenance + Authority + Intent
    pai_receipt: PAIReceipt    # who, what, why, when, with what authority

    # Constitutional state
    epistemic_ladder_rung: int      # 1-7
    godel_wall_state: str           # KNOWN / UNKNOWN / UNDECIDABLE_YET / VOID
    constitutional_verdict: str     # SEAL / SABAR / HOLD / VOID (set by arifOS Ω)

    # Topology
    emitted_at: datetime
    emitted_by_organ: str           # "geox" | "arifos" | "wealth" | "well" | "aaa" | "a-forge"
    topic: str                      # NATS topic
    parent_atom_id: Optional[str]   # lineage

    # History
    vault_ref: Optional[str]        # VAULT999 chain ref
    consumed_by: list[str]          # organs that have subscribed
```

---

## NATS Topic Map (quantum flow backbone)

| Topic | Direction | Publisher | Subscriber | Payload |
|-------|-----------|-----------|------------|---------|
| `arifos.geox.intel.atom.{tool_name}` | publish | GEOX | arifOS, AAA, A-FORGE, WEALTH, WELL | IntelligenceAtom |
| `arifos.geox.intel.verdict.{atom_id}` | publish | arifOS Ω | GEOX, downstream | Verdict (SEAL/SABAR/HOLD/VOID) |
| `arifos.well.operator.{operator_id}` | publish | WELL | GEOX, AAA | OperatorState (fatigue, C1-C5) |
| `arifos.wealth.signal.{asset_id}` | publish | WEALTH | GEOX, AAA | CapitalSignal (NPV, REJECT, ADVANCE) |
| `arifos.arifos.kernel.verdict.{session_id}` | publish | arifOS Ω | GEOX, all organs | F1-F13 verdict |
| `arifos.aaa.ui.command.{operator_id}` | publish | AAA cockpit | GEOX, A-FORGE | UICommand (refresh, drill-down) |
| `arifos.geox.task.progress.{task_id}` | publish | GEOX (long jobs) | arifOS, AAA | TaskProgress (epoch, loss, ETA) |
| `arifos.geox.hold.{actor_id}` | publish | any organ | arifOS, all organs | HOLD event (888) |

These topics are READ from NATS — not from application-layer HTTP. The subscription is the API.

---

## Concrete Behavior Changes

### Before (current GEOX tool call)

```python
# Agent calls geox_joint_inversion(...) over HTTP
# GEOX blocks for 30 seconds
# Returns bare JSON envelope
# No event published
# No cache hit if same input was computed yesterday
# WELL operator fatigue not checked (until next call)
# No cross-organ state propagation
```

### After (quantum-level)

```python
# Agent calls geox_joint_inversion(...)
# GEOX checks Qdrant cache: HIT? return cached atom (ms)
#                    MISS? compute in background, return task_id immediately
# Publishes IntelligenceAtom to arifos.geox.intel.atom.geox_joint_inversion
# Subscribes to arifos.well.operator.{operator_id} — if C5, returns HOLD
# Subscribes to arifos.arifos.kernel.verdict.{session_id} — applies F1-F13
# Stores result in Qdrant with 1-hour TTL
# VAULT999 chain: emit "atom_emitted" event with sha256 hash
# Subscribers (arifOS, AAA, A-FORGE, WEALTH, WELL) react in parallel
# Each emits their own verdict/decision atom back
# GEOX subscribes to its own topic for verdict events → updates atom state
```

---

## What This Replaces / Augments

| Current Pattern | Quantum Replacement | Authority |
|-----------------|---------------------|-----------|
| `geox_claim_seal` → arifOS → SEAL | Same. PLUS: atom emitted to NATS; AAA subscribes and visualizes the SEAL event live; WEALTH auto-recomputes NPV on new SEAL | Auto |
| `geox_well_decision_class` (sync call) | Same. PLUS: WELL publishes operator state continuously; GEOX subscribes and adapts in-flight | Auto |
| `geox_wealth_feed` (sync call) | Same. PLUS: WEALTH publishes capital signal continuously; GEOX flags prospects that drop below threshold | Auto |
| 888_HOLD (sync error) | Same. PLUS: HOLD event published to NATS; all organs see it and adapt; AAA surfaces it in cockpit immediately | Auto |
| `geox_joint_inversion` (blocks 30s+) | Same. PLUS: returns task_id immediately; streams progress via SSE/NATS; resumes from cache if interrupted | Auto |
| `geox_seismic_inversion` (1D, fast) | Same. PLUS: cacheable; idempotent; results publish to NATS for other organs | Auto |
| 4 isolated organs | 1 intelligence field; organs are nodes; flow is the API | Auto |

---

## Infrastructure Reuse (no new components)

GEOX does NOT need any new infrastructure. Everything is already running:

| Component | Currently | New Role |
|-----------|-----------|----------|
| **NATS** (port 4222, `arifos-governance` stream) | ✅ Running, mostly unused | Quantum flow backbone (pub/sub for all atoms) |
| **Qdrant** (port 6333) | ✅ Running, mostly unused | IntelligenceAtom vector cache (semantic retrieval of prior atoms) |
| **Postgres** (port 5432) | ✅ Running, Supabase pooler | Atom metadata + lineage (parent_atom_id chains) |
| **VAULT999** (ports 8100/5001) | ✅ Running | Atom hash sealing (every emit triggers vault_seal) |
| **PAI Receipt** schema | ✅ Defined in `pai_receipt.py` | Universal envelope for every atom (was: defined but not wired) |
| **ACP** (`acp_logic.py`) | ✅ Defined, not imported | Agent Control Plane (A2A coordination; was: defined but not used) |
| **GEOX tools** (54 canonical) | ✅ Live | Each tool emits IntelligenceAtom (was: bare JSON only) |

---

## Concrete Code Changes (this forge)

### 1. `src/geox_core/governance/event_bus.py` (new — 200 lines)

```python
"""
event_bus.py — NATS pub/sub wrapper for the GEOX intelligence field.

Wraps `arifos-governance` JetStream context. Publishers send IntelligenceAtoms;
subscribers receive them. Subscriptions are content-addressed (atom_id) so
re-subscribing to the same topic gets the same atom if unchanged.

DITEMPA BUKAN DIBEI — intelligence flows, not locks.
"""

import json
import os
import asyncio
from typing import Callable, Awaitable

import nats
from nats.js.api import StreamConfig

from geox_mcp.pai_receipt import PAIReceipt


NATS_URL = os.environ.get("ARIFOS_NATS_URL", "nats://127.0.0.1:4222")
STREAM_NAME = "arifos-governance"


class IntelligenceAtom:
    """The universal payload flowing across the federation."""
    # ... (full schema in implementation)


class EventBus:
    """NATS JetStream wrapper for IntelligenceAtom pub/sub."""
    
    def __init__(self):
        self.nc = None
        self.js = None
    
    async def connect(self):
        self.nc = await nats.connect(NATS_URL)
        self.js = self.nc.jetstream()
        # Ensure stream exists (idempotent)
        try:
            await self.js.add_stream(StreamConfig(name=STREAM_NAME, subjects=["arifos.>"]))
        except Exception:
            pass  # already exists
    
    async def publish_atom(self, atom: IntelligenceAtom):
        """Publish an atom to the appropriate topic."""
        topic = atom.topic  # e.g. "arifos.geox.intel.atom.geox_joint_inversion"
        payload = atom.model_dump_json().encode()
        await self.js.publish(topic, payload)
    
    async def subscribe(
        self,
        subject: str,  # e.g. "arifos.>" or "arifos.well.operator.*"
        handler: Callable[[IntelligenceAtom], Awaitable[None]],
    ):
        """Subscribe to a subject pattern; handler invoked per atom."""
        async def _wrapped(msg):
            data = json.loads(msg.data.decode())
            atom = IntelligenceAtom(**data)
            await handler(atom)
            await msg.ack()
        
        await self.js.subscribe(subject, cb=_wrapped)


# Module-level singleton
_bus: EventBus | None = None

async def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
        await _bus.connect()
    return _bus
```

### 2. PAI Receipt wiring into universal envelope (`src/geox_mcp/tools/_register.py`)

The existing `_make_receipt_wrapper` already wraps tool outputs. Extend it to attach a PAI Receipt to every successful output.

### 3. Event subscriber for cross-organ entanglement (`src/geox_mcp/events/subscriber.py`)

```python
"""
subscriber.py — listens for upstream events and adapts GEOX state.

Subscribes to:
- arifos.well.operator.{operator_id}  → if C5, set global HOLD
- arifos.wealth.signal.{asset_id}     → if REJECT, flag affected prospects
- arifos.arifos.kernel.verdict.{id}    → apply F1-F13 verdict to all current atoms

DITEMPA BUKAN DIBEI — listen before you speak.
"""
```

### 4. Event publisher for tool outputs (`src/geox_mcp/events/publisher.py`)

```python
"""
publisher.py — emits IntelligenceAtom for every GEOX tool call.

Wraps the existing `_make_receipt_wrapper` so every successful tool
output produces an atom on `arifos.geox.intel.atom.{tool_name}`.

DITEMPA BUKAN DIBEI — every tool is a publisher.
"""
```

---

## Migration Path (this turn + next)

| Phase | Action | Authority | Effort |
|-------|--------|-----------|--------|
| **W14-α** (this turn) | Forge `event_bus.py` + `publisher.py` + `subscriber.py`; wire PAI receipt into envelope; add `docs/FEDERATION_INTELLIGENCE_FLOW.md`; commit + push | Auto | 4-6 hr |
| **W14-β** (next session) | Refactor 3 tools (joint_inversion, subsurface_generate, seismic_compute) to be cacheable + emit atoms | Auto | 1 day |
| **W14-γ** | Add Qdrant-backed semantic retrieval for prior atoms | Auto | 1 day |
| **W14-δ** | Background tasks for long jobs (joint_inversion, lem_pretrain) using MCP Tasks spec | 888_HOLD | 2 days |
| **W14-ε** | Cross-organ entanglement tests (WELL C5 → GEOX pauses; arifOS HOLD → GEOX marks outputs) | Auto | 1 day |
| **W15** | OPTIONAL: OAuth 2.1 + PKCE on all surfaces (only after the flow itself is coherent) | 888_HOLD | 3-5 days |

The OAuth layer is W15, not W14. Auth before coherence is auth-on-a-broken-door.

---

## What Stays The Same (no change)

- 54 canonical tools (unchanged)
- Physics9 bounds (unchanged)
- Steel Security Layer (non-blocking, no pre-commit hooks)
- F1-F13 floors (unchanged)
- GENESIS doctrine (unchanged)
- VAULT999 chain (unchanged)
- LAN-only auth posture (Cloudflare Tunnel for public; no per-organ OAuth yet)

---

## What I am NOT Doing (Copilot's wrong turns)

| Wrong | Why |
|-------|-----|
| OAuth 2.1 + PKCE | Auth before coherence is auth-on-a-broken-door. Defer to W15. |
| `arifOS Ω as canonical gateway` for all calls | Centralized chokepoint. Contradicts quantum flow. Organs self-publish. |
| `clerk → arifOS → organ` only | Clerks should be able to subscribe to GEOX directly via AAA or A-FORGE (read-only). |
| mTLS for VPS-side organ calls | Adds complexity without solving the actual problem (intelligence doesn't flow). |
| Production hardening before flow coherence | Wrong order. Flow first, harden second. |

---

## Verification (live, after W14-α)

```bash
# Subscribe to GEOX intelligence atoms
nats sub 'arifos.geox.intel.atom.>' --stream=arifos-governance

# Trigger a GEOX tool call
curl -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{
    "name":"geox_subsurface_generate_candidates",
    "arguments":{"cell_states":[...]}
  }}'

# Expect: atom appears on NATS topic
# {
#   "atom_id": "sha256:abc...",
#   "tool_name": "geox_subsurface_generate_candidates",
#   "pai_receipt": {...},
#   "godel_wall_state": "KNOWN",
#   "topic": "arifos.geox.intel.atom.geox_subsurface_generate_candidates"
# }

# WELL publishes operator C5 → GEOX subscriber should pause
nats pub arifos.well.operator.arif '{"fatigue": 0.9, "decision_class": "C5"}'

# Expect: subsequent GEOX tool calls return VOID/HOLD until WELL resets
```

---

## References

- **Copilot's diagnosis:** `/root/CONTEXT.md` references + previous turn
- **AGENTS.md:** `/root/geox/AGENTS.md` (Steel Security Layer, 54 tools, F13 SOVEREIGN)
- **PAI Receipt:** `/root/geox/src/geox_mcp/pai_receipt.py`
- **ACP (Agent Control Plane):** `/root/geox/src/geox_core/governance/acp_logic.py`
- **NATS topic conventions:** `arifos.{organ}.{stream_type}.{subject}` (existing convention)
- **MCP_TRANSPORT_SURFACE.md:** `/root/geox/docs/MCP_TRANSPORT_SURFACE.md` (companion doc)
- **AGENTICS_INTEGRATION.md:** `/root/geox/docs/AGENTICS_INTEGRATION.md` (companion doc)

---

**DITEMPA BUKAN DIBEI — intelligence flows. The organs are nodes in one field. The flow IS the API.**