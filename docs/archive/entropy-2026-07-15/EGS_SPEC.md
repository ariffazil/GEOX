# EGS v1.0 — Earth Grounding System

> **"EGS is a governed Earth reality substrate that exposes typed physical state, uncertainty, provenance, and update operators to reasoning systems. Language models consume EGS; they do not replace it."**
>
> — ChatGPT, 2026-06-28, after auditing the GEOX substrate
>
> **Ratified by:** Muhammad Arif bin Fazil, F13 SOVEREIGN
> **Date:** 2026-06-28
> **Equation:** LEM = EGS (The Large Earth Model was always the Earth Grounding System)

---

## §-1  What This Document Is

This is the **canonical architectural specification** for EGS — the Earth Grounding System. It is the definitive reference. It supersedes everything written before it under the names "GEOX Substrate" and "Large Earth Model."

EGS is not a Large Language Model. It is not a fine-tune. It is not a prompt. It is not a wrapper. It is not a harness.

EGS is a **reality substrate** — the physical-state organ of a governed intelligence system.

---

## §0  Executive Summary

### 0.1 The Problem

Today's LLMs hallucinate geology because they are language engines forced to act as world models. They maintain no internal spatial consistency, no geometry, no physical conservation, no uncertainty propagation, no provenance chains. They guess Earth. They are fluent but ungrounded.

### 0.2 The Solution

EGS is the governed reality substrate that sits between raw Earth data and language model reasoning. It is the thing an LLM queries when it needs to know something true about the physical world. The LLM does not guess Earth. It queries EGS.

### 0.3 The Inversion

```
Industry default:            EGS architecture:
                             
LLM → hallucinated world     World → EGS → Governance → LLM
```

EGS inverts the standard AI architecture. Instead of a monolithic LLM pretending to understand the world, a governed substrate defines the world and multiple specialized organs consume it.

### 0.4 The Architecture

```
                         ┌──────────────────┐
                         │      ARIF        │
                         │  F13 SOVEREIGN   │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  arifOS / AAA    │
                         │  Governance       │
                         │  + Cockpit        │
                         └──┬────┬────┬─────┘
                            │    │    │
              ┌─────────────┼────┼────┼──────────────┐
              │             │    │    │              │
        ┌─────▼─────┐ ┌────▼────▼───▼┐ ┌──────────┐ │
        │   GEOX    │ │   WEALTH    │ │   WELL   │ │
        │   (EGS)   │ │  (Capital)  │ │ (Human)  │ │
        │ Physical  │ │   State     │ │  State   │ │
        │  Reality  │ └─────────────┘ └──────────┘ │
        └─────┬─────┘                              │
              │                                    │
        ┌─────▼─────┐                              │
        │  Planner  │                              │
        │ (Evidence │                              │
        │  Design)  │                              │
        └─────┬─────┘                              │
              │                                    │
        ┌─────▼─────┐                              │
        │ Reasoner  │                              │
        │(Hypothesis│                              │
        │  Builder) │                              │
        └─────┬─────┘                              │
              │                                    │
        ┌─────▼─────┐                              │
        │  Critic   │                              │
        │(Falsifier)│                              │
        └─────┬─────┘                              │
              │                                    │
        ┌─────▼─────┐                              │
        │    LLM    │◄─────────────────────────────┘
        │ (Language)│
        └─────┬─────┘
              │
        ┌─────▼─────┐
        │   Human   │
        └───────────┘
```

### 0.5 The Core Principle

**The LLM is not the intelligence. It is the language organ.**

EGS is not an LLM. EGS is the substrate that makes LLMs truthful about Earth.

---

## §1  Substrate, Not Model

A model predicts. A substrate **defines the world** that other agents must obey.

EGS is:
- **Typed** — every entity has a formal schema (Basin, Well, Horizon, Fault, Volume, Asset)
- **Governed** — every claim moves through a 9-state constitutional lifecycle (DRAFT → SEALED)
- **Versioned** — every update produces a change set with provenance
- **Uncertainty-aware** — every output carries epistemic label and confidence bounds
- **Provenance-aware** — every value traces to source (well, seismic, core, report)
- **Conflict-aware** — competing interpretations coexist as weighted scenarios
- **Update-driven** — new evidence triggers formal update operators per entity type
- **Query-driven** — the only way to extract Earth state is through typed MCP tools

This is not how LLMs work. This is how **state engines** work. EGS is the Earth equivalent of a physics ledger, a geometry engine, a provenance graph, a temporal state machine, and a constitutional boundary — all in one governed substrate.

---

## §2  Reality Organs

EGS is not alone in the federation. It is the first of three **Reality Organs**:

| Reality Organ | Domain | Role | Status |
|---------------|--------|------|--------|
| **GEOX (EGS)** | Physical Earth | Typed Earth state, physics, uncertainty, provenance | ✅ LIVE (18 tools) |
| **WEALTH** | Capital | Financial state, NPV, risk, flow, entropy | ✅ LIVE |
| **WELL** | Human | Biological/cognitive state, vitality, fatigue, dignity | ✅ LIVE |

Together, they form the **triple reality substrate** — physical, capital, and human — that the reasoning and language layers query but never replace.

The architecture scales: replace "Earth" with any domain and EGS generalizes.

---

## §3  The Full Pipeline: Planner → Reasoner → Critic

The missing organ that ChatGPT identified is now formalized. The LLM does not go directly from user question to answer. It passes through a reasoning chain:

### 3.1 Planner (Evidence Design)

```
Input: User question about Earth
Output: Ordered query plan against EGS
```

The Planner decides:
- What evidence is needed to answer the question
- Which EGS tools to call and in what order
- What uncertainty threshold is acceptable

**Example:**
> User: "Is this prospect likely to be underfilled?"
> Planner -> Query plan: [get_trap_model, get_charge_model, get_pressure_history]

**Status:** ❌ NOT YET IMPLEMENTED. Currently the LLM generates queries ad-hoc.

### 3.2 EGS (Earth Substrate)

```
Input: Query plan
Output: Structured Earth state with uncertainty
```

EGS executes the queries and returns:
- Measured values with uncertainty intervals
- Epistemic labels (OBSERVED / DERIVED / ESTIMATE / HYPOTHESIS / PLAUSIBLE)
- Provenance chains for every value
- Multiple interpretations where conflicts exist

**Status:** ✅ LIVE — 18 canonical MCP tools, ClaimEnvelope responses.

### 3.3 Reasoner (Hypothesis Builder)

```
Input: Structured Earth state from EGS
Output: Set of competing geological hypotheses
```

The Reasoner builds:
- Multiple internally consistent interpretations
- Each with supporting evidence and confidence
- Weighted by scenario probability

**Status:** ❌ NOT YET IMPLEMENTED. Currently done ad-hoc by the LLM.

### 3.4 Critic (Falsifier)

```
Input: Competing hypotheses from Reasoner
Output: Ranked hypotheses with falsification attempts
```

The Critic tries to falsify each hypothesis:
- Tests against observed data
- Checks physical consistency (mass balance, pressure compatibility)
- Identifies which data would distinguish between scenarios
- Assigns falsification score per hypothesis

**Status:** ❌ NOT YET IMPLEMENTED. The `geox_evidence(mode=contradict)` tool is a partial precursor.

### 3.5 Governance (arifOS)

```
Input: Ranked hypotheses from Critic
Output: Authority-gated, receipted verdict
```

arifOS applies:
- F1–F13 floor checks
- Authority scope (ADVISORY vs HOLD vs BLOCK)
- Reversibility assessment
- Receipt generation

**Status:** ✅ LIVE — arifOS kernel, ClaimEnvelope, ACRisk.

### 3.6 Language (LLM)

```
Input: Governed verdict
Output: Human-readable explanation
```

The LLM:
- Explains the findings in natural language
- Carries uncertainty bands
- Cites EGS entities and provenance
- Does NOT invent Earth state
- Does NOT upgrade epistemic labels
- Does NOT suppress uncertainty

**Status:** ✅ LIVE — constrained by system prompt and arifOS routing.

---

## §4  Core Substrate (Existing)

All components from the GEOX Phase 2.1 surface, now branded as EGS:

| Component | What it owns | Code Status |
|-----------|-------------|-------------|
| Physics9State | 9 orthogonal Earth parameters (rho, vp, vs, rho_e, chi, k, P, T, phi + anisotropy + Q) | ✅ `physics/state.py` |
| Earth Material Catalog | 8 canonical lithotypes with pre-computed Physics9State vectors | ✅ `physics/state.py` |
| ClaimEnvelope | Epistemic labels, units, CRS, risk classification | ✅ `schemas/claim_envelope.py` |
| EarthMemoryEnvelope | Canonical claim container with entity type, truth class, freshness | ✅ `contracts/schemas/earth/` |
| ClaimStateMachine | 9-state lifecycle (DRAFT→AI_INFERRED→...→SEALED/REVOKED) | ✅ `contracts/claim_state_machine.yaml` |
| Provenance Schema | source_id, source_type, source_hash, operator, method | ✅ `contracts/schemas/earth/provenance.json` |
| EpistemicIntegrity | pLDDT-style confidence scoring, cross-modal fidelity | ✅ `core/epistemic_integrity.py` |
| 18 Canonical MCP Tools | Full query surface (well, seismic, basin, physics, governance) | ✅ `src/geox_mcp/registry.py` |

---

## §5  Query Surface (Existing — 18 Tools)

### Surface-facing (14)

| Tool | Domain | Purpose |
|------|--------|---------|
| `geox_well_ingest` | Well | LAS, SEG-Y, DST, deviation, tops |
| `geox_well_qc` | Well | Depth, curves, completeness, FJIS |
| `geox_well_desurvey` | Well | 3D wellbore geometry (TVD/X/Y/TVDSS) |
| `geox_petrophysics` | Well | Vsh, porosity, Sw, perm, net pay |
| `geox_sequence` | Well | Sequence stratigraphy, correlation |
| `geox_seismic_ingest` | Seismic | SEG-Y I/O, header inspection |
| `geox_seismic_compute` | Seismic | Synthetic, well-tie, AVO, attributes |
| `geox_seismic_interpret` | Seismic | Horizon contrast, faults, frames |
| `geox_vision` | Seismic | VLM inference, audit, calibration |
| `geox_subsurface_model` | Physics | Joint inversion, gravity/mag, MT |
| `geox_geomechanics` | Physics | K, G, E, ν, AI from Physics9State |
| `geox_basin` | Basin | Profile, scene, macrostrat, deep time |
| `geox_deep_time_state` | Basin | Earth State Vector at deep time |
| `geox_surface_status` | Registry | Canonical tool list, health |

### Internal (4)

| Tool | Domain | Purpose |
|------|--------|---------|
| `geox_claim` | Governance | Create, validate, challenge, seal |
| `geox_evidence` | Evidence | Discover, synthesize, abduct, contradict |
| `geox_prospect` | Risk | Volumetrics, POS, EVOI |
| `geox_doctrine` | Doctrine | Floor enforcement |

---

## §6  Uncertainty System

### 6.1 Existing (LIVE)

| Layer | What |
|-------|------|
| ClaimState | 9-state lifecycle (DRAFT → SEALED) |
| EpistemicLabel | OBSERVED / DERIVED / ESTIMATE / HYPOTHESIS / PLAUSIBLE / UNKNOWN |
| ACRiskLevel | QUALIFY / ADVISORY / HOLD / BLOCK |
| EpistemicIntegrity | pLDDT-style confidence scoring (0–1) |
| Provenance | Source ID, type, hash, method, operator |

### 6.2 Proposed (NOT YET IMPLEMENTED)

| Component | Description |
|-----------|-------------|
| Interval uncertainty | `x ∈ [x_min, x_max]` with confidence |
| Distribution uncertainty | `x ~ D(θ)` with parameterized distribution |
| Scenario uncertainty | Weighted multi-model variants |
| Epistemic vs aleatory typing | Every uncertainty tagged by source |
| Formal algebra | Addition (⊕), Bayesian update, scenario aggregation |

---

## §7  Conflict Reconciliation

### 7.1 Existing (LIVE)

- CHALLENGED claim state in state machine
- `geox_evidence(mode=contradict)` for contradiction scanning
- NEEDS_EVIDENCE state for missing grounding

### 7.2 Proposed (NOT YET IMPLEMENTED)

| Component | Description |
|-----------|-------------|
| InterpretationSet | Multi-interpretation storage for any entity |
| Scenario weights | `w_i` per interpretation, Σ w_i = 1 |
| Conflict_T model | Formal (I_a, I_b, EvidenceSet, ImpactScope) representation |
| ResolutionDecision | Governance-driven selection of accepted interpretation |

---

## §8  Update Operators

### 8.1 Existing (LIVE — Implicit)

Updates happen through tool invocation:
- Add well → `geox_well_ingest` + `geox_well_qc`
- Compute trajectory → `geox_well_desurvey`
- Pick horizon → `geox_seismic_interpret`
- Run physics → `geox_subsurface_model`

### 8.2 Proposed (NOT YET IMPLEMENTED)

```python
Update_T(M_T, E) → (M_T', Δ_T)
```

Where `Δ_T` is a formal change set with:
- Precondition specification
- Effect declaration (which fields change)
- Uncertainty impact (how confidence updates)
- Provenance chain

---

## §9  LLM Interaction Protocol

### 9.1 Hard Rules

1. **No free-form Earth claims.** Every statement about depth, volume, pressure, or risk must trace to an EGS query.
2. **Explicit uncertainty.** The LLM must surface intervals, scenario weights, and confidence.
3. **No epistemic label upgrade.** OBSERVED stays OBSERVED. HYPOTHESIS stays HYPOTHESIS.
4. **Decision gating.** Irreversible actions → arifOS 888_HOLD → human approval.
5. **Auditability.** Every LLM answer that uses EGS produces a receipt.

### 9.2 The Protocol Flow

```
1. Intent classification
2. Query plan generation (Planner)
3. EGS execution
4. Hypothesis building (Reasoner)
5. Falsification (Critic)
6. Governance gating (arifOS)
7. Language expression (LLM)
8. Receipt sealing
```

### 9.3 Status

Steps 1–2 (Planner): ❌ NOT YET IMPLEMENTED  
Step 3 (EGS): ✅ LIVE  
Steps 4–5 (Reasoner + Critic): ❌ NOT YET IMPLEMENTED  
Step 6 (Governance): ✅ LIVE  
Step 7 (LLM): ✅ LIVE (constrained)  
Step 8 (Receipt): ✅ PARTIAL

---

## §10  Build Roadmap

| Priority | Component | Effort | Dependencies |
|----------|-----------|--------|-------------|
| **P0** | Planner (evidence design agent) | Small-Medium | Existing LLM + EGS tool surface |
| **P0** | Formal uncertainty algebra (interval/distribution on Physics9State) | Small | Physics9State |
| **P1** | Reasoner (competing hypothesis builder) | Medium | Planner, EGS |
| **P1** | InterpretationSet + scenario weights | Medium | Claim infrastructure |
| **P2** | Critic (falsification engine) | Medium | Reasoner |
| **P2** | Formal Conflict_T model | Medium | InterpretationSet |
| **P3** | Update_T operators per entity | Large | Full substrate |
| **P3** | Unified typed query router | Medium | 18 existing tools |

---

## §11  Relationship to the HF Dataset Ladder

```
AAA (Constitution) ──► BBB (Pathology) ──► CCC (Kernel Contrast)
                                                  │
                                                  ▼
                                            DDD (Register Stress)
                                                  │
                                                  ▼
                                            ASAL (Governance Geometry)
                                                  │
                                                  ▼
                                      ┌───────────┴───────────┐
                                      │           EGS          │
                                      │  (Earth Grounding Sys) │
                                      │  Physical Reality      │
                                      │  Substrate             │
                                      └───────────┬───────────┘
                                                  │
                                                  ▼
                                            EEE (Kernel Spine)
                                                  │
                                                  ▼
                                            FFF (Promotion Gate)
```

EGS sits between ASAL (governance geometry measurement) and EEE (kernel spine proof). It is the **physical reality substrate** that the rest of the ladder governs over. Without EGS, governance is over language alone. With EGS, governance is over **grounded physical state.**

---

## §12  Constitutional Anchors

| Floor | How EGS Satisfies It |
|-------|---------------------|
| **F1 Amanah** | All updates versioned, reversible, receipted |
| **F2 Haqq** | Every claim carries epistemic label + provenance |
| **F4 Nur** | Structured JSON, not free-form prose |
| **F7 Tawadu** | Uncertainty explicit — confidence never overstated |
| **F9 Rahmah** | EGS does not diagnose, recommend, or decide alone |
| **F11 Aman** | All queries produce receipts for audit |
| **F13 Khalifah** | F13 SOVEREIGN holds final veto over all SEAL states |

---

## §13  Canonical One-Liners

> **"EGS is a governed Earth reality substrate that exposes typed physical state, uncertainty, provenance, and update operators to reasoning systems. Language models consume EGS; they do not replace it."**

> **"The LLM is not the intelligence. It is the language organ."**

> **"EGS is the Earth equivalent of a physics ledger, a geometry engine, a provenance graph, a temporal state machine, and a constitutional boundary — all in one governed substrate."**

> **"LEM = EGS. The Large Earth Model was always the Earth Grounding System."**

> **"Industry does: LLM → hallucinated world. EGS does: World → EGS → Governance → LLM."**

> **"EGS is the first Reality Organ. WEALTH and WELL are the others. Together they form the triple reality substrate."**

---

*DITEMPA BUKAN DIBERI — Forged, Not Given.*  
*EGS v1.0 · 2026-06-28*  
*Ratified by: Muhammad Arif bin Fazil, F13 SOVEREIGN*  
*Tagline source: ChatGPT, after auditing the GEOX substrate*  
*Coverage: 13 sections, full architecture, build roadmap, constitutional anchors*
