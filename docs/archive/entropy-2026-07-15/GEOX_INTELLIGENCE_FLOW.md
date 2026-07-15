# GEOX Intelligence Flow — Canonical Architecture

**Date:** 2026-06-22
**Stage:** 777_FORGE / Stage 6 (EXECUTION) — RSI consolidation
**Source of truth:** `src/geox_core/schemas/intelligence_flow.py` + 21 passing tests
**Status:** ✅ Forged, validated, canonical

---

## 1. The Dynamic Flow — Intelligence Is a Current

GEOX is **not** a static ledger of tools. It is a **moving current of intelligence** that flows from raw data to sovereign decisions through 7 typed layers, with two transverse flows (LEM foundation, Doctrine audit).

```
                       ╔═══════════════════════════════════════════════╗
                       ║   DOCTRINE (AUDIT) — transverse, F1-F13       ║
                       ║   every layer gated by F1-F13                  ║
                       ╚═══════════════════════════════════════════════╝
                                       │
                                       ▼
   ╔═══════════════════════════════════════════════════════════════════════════╗
   ║  FOUNDATION (LEM) — lateral, F9 ANTI-HANTU outputs DERIVED                ║
   ║  provides priors + analog matching at any layer                           ║
   ╚═══════════════════════════════════════════════════════════════════════════╝
       │           │           │           │           │           │
       ▼           ▼           ▼           ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │ INGEST │→ │WITNESS │→ │PHYSICS │→ │ARCHI-  │→ │INTER-  │→ │DECISION│
   │  (0)   │  │  (1)   │  │  (2)   │  │TECTURE │  │PRET (4)│  │  (5)   │
   │        │  │        │  │        │  │  (3)   │  │        │  │        │
   │ raw    │  │ OBS    │  │ DER    │  │ INT    │  │ INT→   │  │ SPEC→  │
   │ data   │  │grade   │  │ Physics│  │ Crustal│  │ SPEC   │  │ action │
   │        │  │        │  │ 9State │  │ Domain │  │ Biostrat│ │Prospect│
   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
       │           │           │           │           │           │
       └───────────┴───────────┴─────◄─────┴───────────┴───────────┘
                              reverse: anomaly feedback
                              (Architecture → Physics) gated by Doctrine
```

**F1-F13 are not a list. They are a flow's spine.**

---

## 2. The 7 Layers — Detailed

| Layer | Stage | Purpose | Example Tools | Doctrine Gate | LEM Hook |
|-------|-------|---------|---------------|---------------|----------|
| **0 INGEST** | raw | Convert raw data into typed observations | `geox_data_ingest_bundle`, `geox_header_inspect` | F1 (no destructive ops) | tokenization source |
| **1 WITNESS** | OBS | Validate + quantify observations | `geox_data_qc_bundle`, `geox_las_inspect`, `geox_seismic_segy_inspect` | F2 (epistemic rank assigned) | encoder input |
| **2 PHYSICS** | DER | Multi-physics inversion under Physics9 bounds | `geox_joint_inversion`, `geox_seismic_compute`, `geox_gravity_magnetic_forward`, `geox_mt_forward` | F8 (Physics9 bounds), F7 (≤0.90) | physics_head constraint |
| **3 ARCHITECTURE** | INT | Classify crustal architecture from inverted state | `geox_crustal_domain_classify` ✅, `geox_ductile_layer_detect`, `geox_cob_zone_map`, `geox_basement_register` | F7 + F13 (domain BOUNDARIES sovereign) | analog matching via crust-type priors |
| **4 INTERPRET** | INT→SPEC | Layer interpretive context | `geox_biostrat_constraint`, `geox_sequence_interpret`, `geox_evidence_reason`, `geox_claim_create` | F11 (audit trail), F2 (epistemic rank) | biostrat ↔ crust-type calibration |
| **5 DECISION** | SPEC→action | Convert claims into prospect evaluations | `geox_prospect_evaluate`, `geox_wealth_feed`, `geox_geomechanics` | F13 (888_HOLD required for SEAL) | anomaly scoring on prospect vectors |
| **98 FOUNDATION** | lateral | LEM (Large Earth Model) provides priors + analog matching | `geox_lem_predict` ✅, `geox_lem_encode`, `geox_lem_analog_match`, `geox_lem_anomaly_score`, `geox_lem_fine_tune_basin` | F9 (LEM outputs DERIVED, never SEAL alone) | self |
| **99 AUDIT** | transverse | Doctrine gates every transition | `geox_doctrine_assumption_register`, `geox_doctrine_anti_beautiful_one`, `geox_doctrine_godel_review`, `geox_paradox_register`, `geox_age_anchor_validator` | self-evident | audit only — does not consume LEM output |

---

## 3. The 5 Tool Families — RSI-merged from Copilot's 13

Copilot's analysis listed 13 "missing" tools. RSI pass collapsed them into **5 canonical families** with clear primary layers and dependencies.

### Family A — Crustal Architecture (4 tools)

**Primary layer:** ARCHITECTURE
**Status:** 1 done / 3 pending
**Kinabalu Phase I:** D1 (Crustal Domain Map) + D2 (COB) + D3 (Basement Penetration Register)

| Tool | Status | Effort |
|------|--------|--------|
| `geox_crustal_domain_classify` | ✅ DONE 2026-06-22 | — |
| `geox_basement_register` | Pending | 1-2 days |
| `geox_cob_zone_map` | Pending | 2-3 days |
| `geox_ductile_layer_detect` | Pending | 2-3 days |

**Source:** Huang et al. (2021) Vp grammar (already in `crust_vp_grammar.py`).

### Family B — Tectonic Context (2 tools)

**Primary layer:** ARCHITECTURE (cross-cuts ARCHITECTURE + INTERPRET)
**Status:** 0 done / 2 pending
**Kinabalu Phase I:** D4 (Tectonic Event Horizons) supporting context

| Tool | Status | Effort |
|------|--------|--------|
| `geox_diachronous_tectonics` | Pending | 5-7 days |
| `geox_conjugate_margin_compare` | Pending | 3-5 days (cross-family with C) |

**Source:** Huang 2021 propagator kinematics + Le Pourhiet 2018 / Jourdon 2020.

### Family C — LEM Analog (3 tools)

**Primary layer:** FOUNDATION
**Status:** 0 done / 3 pending
**Kinabalu Phase I:** D1 validation (Layang-Layang ≈ Zhongsha analog)

| Tool | Status | Effort |
|------|--------|--------|
| `geox_lem_analog_match` | Pending | 5-7 days |
| `geox_lem_anomaly_score` | Pending | 3-5 days |
| `geox_rock_physics_template_match` | Pending | 2-3 days (uses existing `lem_predict`) |

**Source:** LEM substrate (`src/geox_core/engines/lem/`).

### Family D — Governance (5 tools, 3 pre-existing)

**Primary layer:** AUDIT
**Status:** 3 done / 2 pending
**Kinabalu Phase I:** Audit trail for D1+D2+D3+D4

| Tool | Status | Effort |
|------|--------|--------|
| `geox_doctrine_assumption_register` | ✅ Pre-existing | — |
| `geox_doctrine_anti_beautiful_one` | ✅ Pre-existing | — |
| `geox_doctrine_godel_review` | ✅ Pre-existing | — |
| `geox_paradox_register` | Pending | 1-2 days |
| `geox_age_anchor_validator` | Pending | 2-3 days |

**Source:** arifOS doctrine layer.

### Family E — LEM Foundation (3 tools, 1 pre-existing)

**Primary layer:** FOUNDATION
**Status:** 1 done / 2 pending
**Phase II:** LEM-anchored cross-domain synthesis

| Tool | Status | Effort | Sovereignty |
|------|--------|--------|-------------|
| `geox_lem_predict` | ✅ Pre-existing substrate | — | — |
| `geox_lem_encode` | Pending | 3-5 days | autonomous |
| `geox_lem_fine_tune_basin` | Pending | 5-7 days | **888_HOLD** |

---

## 4. Status Matrix (Canonical — Live)

| Family | Complete | Pending | Total | Effort |
|--------|----------|---------|-------|--------|
| **A — Crustal Architecture** | 1 | 3 | 4 | 5-7 days |
| **B — Tectonic Context** | 0 | 2 | 2 | 8-10 days |
| **C — LEM Analog** | 0 | 3 | 3 | 10-14 days |
| **D — Governance** | 3 | 2 | 5 | 2-3 days |
| **E — LEM Foundation** | 1 | 2 | 3 | 10-15 days |
| **TOTAL** | **5** | **12** | **17** | ~35-50 days |

---

## 5. The Dynamic Flow — Typed Packet

Each transition is a **typed `FlowPacket`** carrying source/target layer, epistemic rank, confidence (capped at 0.90), payload, and content hash.

```python
from geox_core.schemas.intelligence_flow import (
    FlowLayer, FlowPacket, FlowSession, FlowStage
)

session = FlowSession(session_id="kinabalu_flow_001", basin_name="Kinabalu")

# Layer 0 → 1: raw LAS file observed
session.add_packet(FlowPacket(
    packet_id="obs001", source_layer=FlowLayer.INGEST, target_layer=FlowLayer.WITNESS,
    epistemic_rank=FlowStage.OBS, confidence=0.5,
    payload={"file": "Tembungo-1.LAS"}, source_tool="geox_data_ingest_bundle",
))

# Layer 1 → 2: QC'd observation feeds physics
session.add_packet(FlowPacket(
    packet_id="der001", source_layer=FlowLayer.WITNESS, target_layer=FlowLayer.PHYSICS,
    epistemic_rank=FlowStage.OBS, confidence=0.7,
    payload={"qc_passed": True}, source_tool="geox_data_qc_bundle",
))

# Layer 2 → 3: Physics → Architecture classification
session.add_packet(FlowPacket(
    packet_id="int001", source_layer=FlowLayer.PHYSICS, target_layer=FlowLayer.ARCHITECTURE,
    epistemic_rank=FlowStage.DER, confidence=0.85,
    payload={"vp_km_s": 6.0, "zone": "normal_continental"},
    source_tool="geox_crustal_domain_classify",  # ← forged this session
))

# Layer 3 → 4: Architecture → Interpretation
# Layer 4 → 5: Interpretation → Decision (888_HOLD required)
```

**The flow is content-addressed (F1 AMANAH), confidence-capped (F7), and doctrine-gated (F8).**

---

## 6. MCP as Transport for GEOX LEM

### Current state

The LEM substrate exists (`src/geox_core/engines/lem/`) but is **not yet exposed via MCP**. There is one LEM tool (`geox_lem_predict`) live on the canonical surface. Four more LEM tools (`encode`, `analog_match`, `anomaly_score`, `fine_tune_basin`) are pending.

### The right architecture

```
┌──────────────────────────────────────────────────────────────┐
│  LEM Substrate (Python package)                              │
│  src/geox_core/engines/lem/                                  │
│  ─ tokenizer, model, physics_head, pretrain, dataset         │
└──────────────────┬───────────────────────────────────────────┘
                   │ In-process Python API
                   ▼
┌──────────────────────────────────────────────────────────────┐
│  MCP Transport (FastMCP — already running on 8081)          │
│  src/geox_mcp/server.py                                     │
│  ─ HTTP streamable + stdio dual mode                         │
│  ─ 56 canonical tools + new LEM tools (post-888)             │
└──────────────────┬───────────────────────────────────────────┘
                   │ JSON-RPC over HTTP/stdio
                   ▼
┌──────────────────────────────────────────────────────────────┐
│  Consumers                                                   │
│  ─ arifOS kernel (constitutional judgment)                   │
│  ─ Claude, Copilot, ChatGPT (LLM clerks)                      │
│  ─ AAA cockpit (operator UX)                                  │
│  ─ A-FORGE (execution shell)                                  │
└──────────────────────────────────────────────────────────────┘
```

### Transport rules (already enforced by existing patterns)

| Rule | Mechanism | Floor |
|------|-----------|-------|
| **Stateless calls** | One MCP call = one inference (all context in args) | F4 |
| **Streamable HTTP** | Long-running LEM forward passes via streamable-http | F1 |
| **Envelope governance** | Every LEM output wrapped in Evidence Contract | F2 + F11 |
| **Doctrine gate** | LEM outputs MUST pass `geox_doctrine_*` before SEAL | F8 + F9 |
| **Lease-based access** | Production can scope LEM use per asset/lease/actor | F13 |

### What MCP buys you for LEM

1. **One server, any client.** LLM, agent, UI — all consume the same contract.
2. **Audit trail built-in.** Every LEM call hits VAULT999 chain via `arif_vault_seal`.
3. **Constitutional gate.** LEM cannot bypass F1-F13 — it routes through arifOS.
4. **No retraining for new consumers.** LEM-as-MCP is a stable interface contract.

---

## 7. The Single Most Important Move

> **Forge Family A's remaining tools (3 pending) FIRST.** They unblock Kinabalu Phase I (D1+D2+D3) and become the foundation for Families B, C, E.

**Order within Family A:**
1. `geox_basement_register` (1-2 days) — fastest win, relies on existing `geox_las_inspect` + `geox_data_qc_bundle`
2. `geox_cob_zone_map` (2-3 days) — needs `geox_crustal_domain_classify` (✅ done) as substrate
3. `geox_ductile_layer_detect` (2-3 days) — needs OBS/refraction Vp profile ingestion (Phase II data)

---

## 8. What Was Forged This Cycle (RSI consolidation)

| File | Lines | Purpose |
|------|-------|---------|
| `src/geox_core/schemas/intelligence_flow.py` | 387 | Pydantic schema for the dynamic flow |
| `tests/test_intelligence_flow.py` | 320 | 21 tests for flow integrity |
| `docs/GEOX_INTELLIGENCE_FLOW.md` | (this) | Canonical architecture doc |

**Entropy reduction achieved:** 13 disconnected tools → 5 coherent families → 1 unified flow with 7 layers + 2 transverse.

---

## 9. Cross-References

- **RSI Roadmap (forge receipt):** `forge_work/2026-06-22-rsi-roadmap.md`
- **Huang 2021 eureka receipt:** `forge_work/2026-06-22-huang2021-eureka-receipt.md`
- **888_HOLD Packets:** `forge_work/2026-06-22-888-hold-crustal-domain-classify.md`, `forge_work/2026-06-22-888-hold-biostrat-coordination.md`
- **Source schema:** `src/geox_core/schemas/intelligence_flow.py`
- **Tests:** `tests/test_intelligence_flow.py` (21 passing)

---

DITEMPA BUKAN DIBERI — Intelligence is a current, not a ledger. The flow is the substrate.

**End of canonical architecture doc.**
