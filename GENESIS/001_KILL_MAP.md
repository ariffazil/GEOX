<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-14
valid_from: 2026-06-14
valid_until: 2026-07-14
confidence: high
scope: /root/geox/GENESIS
-->

# DSG → GEOX ARCHITECTURAL KILL MAP

## PURPOSE

This document defines:

- what DSG does
- why it fails structurally
- how GEOX replaces it

---

## 1 — SYSTEM CLASS

| Layer | DSG | GEOX |
|------|-----|------|
| Model | Centralised | Distributed |
| Access | License (FCFS) | Compute-on-demand |
| Mode | Session-based | Persistent state |
| Execution | Manual | Agent-driven |

---

## 2 — CORE FAILURE MODES (DSG)

### FM1 — Access bottleneck

- Fixed number of seats
- Queue-based access

→ breaks cognitive flow

---

### FM2 — Serial execution

- Single-user session
- Non-parallel workflows

→ mismatch with subsurface complexity

---

### FM3 — Tool-centric validation

- Output accepted only if generated inside system

→ suppress alternative intelligence pathways

---

### FM4 — Feature underutilisation

- Advanced modules exist
- Not embedded in daily workflow

→ cost without value

---

## 3 — GEOX REPLACEMENT MODEL

### R1 — Compute Layer

Replace:
> License-based access

With:
> Scalable compute layer

---

### R2 — State Layer

Replace:
> Session workspace

With:
> Persistent geological state model

---

### R3 — Execution Layer

Replace:
> Manual interpretation

With:
> Agent orchestration

---

### R4 — Output Layer

Replace:
> Tool-rendered outputs

With:
> Structure-driven outputs (machine + human readable)

---

## 4 — FUNCTIONAL MAPPING

| DSG Function | GEOX Equivalent |
|-------------|----------------|
| Interpretation workspace | Earth Intelligence Graph |
| Fault interpretation tool | Agent: STRUCTURAL_DETECTOR |
| Well correlation view | Multi-well reasoning engine |
| Data loading | Continuous ingestion pipeline |

---

## 5 — WHAT IS NOT REPLACED

GEOX does NOT remove:

- domain expertise
- geological judgement
- interpretation ownership

It removes:

> artificial constraints on accessing intelligence

---

## 6 — KILL DECISION

DSG is not broken.

DSG is:

> architecturally limited

GEOX does not fix DSG.

GEOX bypasses it.

---

## 999 — VERDICT

Transition is not migration.

It is:

> system replacement at paradigm level
