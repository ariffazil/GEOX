# GEOX Readiness Specification v0.1

> **DITEMPA BUKAN DIBERI** — Forged, Not Given
>
> Canonical readiness gate for GEOX systems built on Model Context Protocol (MCP).

**Author:** Muhammad Arif bin Fazil (F13 SOVEREIGN)  
**Canonical location:** `geox/docs/GEOX_READINESS_SPEC_v0_1.md`  
**Status:** SEALED (2026-06-15)  
**Supersedes:** None (first edition)  
**Next review:** 2026-07-15 or upon any MCP protocol version bump

---

## 1. Purpose

This specification formalizes a readiness gate for GEOX systems built on Model Context Protocol (MCP), especially GEOX MCP Core, GEOX MCP UI, and GEOX MCP Apps intended for subsurface workflows.[^1][^2][^3]

The goal is to prevent premature promotion of prototype-grade geoscience tooling into production authority before identity, governance, evidence lineage, review flow, and safety constraints are demonstrably in place.[^4][^5][^6][^3]

---

## 2. Scope

This specification applies to five assessment layers:

| Layer | Scope |
|-------|-------|
| **GEOX MCP Core** | Domain-native tool surface, evidence gates, physics governance |
| **GEOX MCP UI** | Visual review, interpretation visibility, human approval controls |
| **GEOX MCP Apps** | Packaged governed workflows, app manifest, session continuity |
| **Subsurface workflow readiness** | End-to-end flow, scenario analysis, uncertainty expression |
| **Production authority readiness** | Identity, asset scoping, approval enforcement, audit completeness |

It is designed for internal and enterprise deployments where GEOX supports interpretation, QC, evidence reasoning, prospect evaluation, scenario comparison, and governed human review.[^1][^5][^7][^3]

---

## 3. Assessment Model

Each layer is scored from **0 to 100** using weighted criteria. The resulting numbers are **decision-support estimates**, not external industry certifications, because no public standard currently defines a universal benchmark for subsurface MCP production readiness.[^4][^5][^3]

### 3.1 Readiness Bands

| Score band | Status | Meaning |
|:---:|---|---|
| 0–24 | **Blocked** | Unsafe or structurally incomplete; cannot be used beyond isolated experimentation. |
| 25–49 | **Prototype** | Fit for exploration only; not suitable for delegated authority. |
| 50–69 | **Internal alpha** | Useful for governed internal trials with explicit limits and human supervision. |
| 70–84 | **Controlled beta** | Suitable for expanded internal usage with audit, review, and rollback controls. |
| 85–100 | **Production authority** | Suitable for production decisions within declared scope and policy envelope. |

### 3.2 Score Semantic

All scores are **ESTIMATE** class (F2 TRUTH). They are calibration tools for go/no-go decisions, not metrics. A score of 72 means "our calibrated judgement places this layer at Controlled beta threshold" — it is not a measurement with instrument precision.

---

## 4. Normative Principles

A GEOX system **SHALL** satisfy the following principles before any production-authority classification is granted:[^4][^8][^6][^3]

| # | Principle | Fiqh class |
|---|-----------|------------|
| P1 | Every action that changes state SHALL be attributable to an actor identity and session context.[^4][^6][^3] | **Wajib** |
| P2 | Every subsurface claim SHALL reference evidence or explicitly declare that valid evidence is absent.[^6][^3] | **Wajib** |
| P3 | Every AI-derived interpretation SHALL remain challengeable, reversible, and visibly labeled as `AI_INFERRED` until human approval is recorded. | **Wajib** |
| P4 | Every official sealing or irreversible promotion step SHALL require explicit human acknowledgement. | **Wajib** |
| P5 | Every asset-facing workflow SHALL carry asset, basin, and discipline context. | **Wajib** |
| P6 | No operational-control pathway SHALL be exposed through GEOX MCP unless a separate safety-certified control architecture exists. | **Haram** |
| P7 | Every CRS-bearing coordinate SHALL carry source CRS, target CRS, datum, and round-trip tolerance proof. | **Wajib** |
| P8 | Every tool SHALL declare its safety tier (Tier 0–3) and fiqh class (wajib/sunat/makruh/haram). | **Sunat** |
| P9 | No state-changing action SHALL execute with `actor_id` = null/anonymous outside sandbox mode. | **Wajib** |
| P10 | Every visual claim SHALL carry `CRS + datum` where spatial context applies. | **Wajib** |

---

## 5. Layer Scorecards

### 5.1 GEOX MCP Core

Measures the depth and governance of the domain-native tool surface.

| # | Criterion | Weight | Required condition | Fiqh |
|---|-----------|:------:|-------------------|:----:|
| C1 | **Domain semantics** | 20 | Tools expose geoscience-native capabilities: ingest, QC, log/seismic inspection, interpretation, scenario analysis, coordinate handling. | Wajib |
| C2 | **Schema discipline** | 15 | Inputs and outputs are typed, validated, and versioned. | Wajib |
| C3 | **Evidence gating** | 20 | Fail-closed behavior when evidence is missing or insufficient. | Wajib |
| C4 | **Provenance** | 15 | Tool outputs preserve source artifacts, versions, and lineage. | Wajib |
| C5 | **Physics governance** | 15 | Constraint checks for units, CRS, datum, domain plausibility. | Wajib |
| C6 | **Reversibility** | 15 | Mutations are diffable, auditable, and rollback-capable. | Sunat |

**Minimum production threshold for GEOX MCP Core: 80**

### 5.2 GEOX MCP UI

Measures whether the system presents subsurface truth in a form that experts can inspect, challenge, and approve.[^1][^2][^9]

| # | Criterion | Weight | Required condition | Fiqh |
|---|-----------|:------:|-------------------|:----:|
| U1 | **Evidence visualization** | 20 | UI renders evidence references, QC state, and artifact lineage. | Wajib |
| U2 | **Interpretation visibility** | 15 | UI shows claim class, uncertainty, contradictions, and alternatives. | Wajib |
| U3 | **Domain visual panel** | 20 | UI supports logs, sections, overlays, or equivalent review visuals. | Wajib |
| U4 | **Diff and comparison** | 15 | Before/after changes and scenario comparisons are visible. | Sunat |
| U5 | **Human review controls** | 20 | Approve, reject, request-evidence, and seal actions are explicit. | Wajib |
| U6 | **Accessibility and host fit** | 10 | UI works within MCP Apps host constraints and remains usable in conversation contexts. | Sunat |

**Minimum production threshold for GEOX MCP UI: 75**

### 5.3 GEOX MCP Apps

Measures the packaging of governed workflows into MCP-compatible app surfaces.[^1][^2][^10]

| # | Criterion | Weight | Required condition | Fiqh |
|---|-----------|:------:|-------------------|:----:|
| A1 | **App manifest completeness** | 20 | App declares asset, basin, discipline, safety tier, reversibility, and review requirements. | Wajib |
| A2 | **Host compatibility** | 15 | App functions in supported MCP Apps-compatible hosts. | Sunat |
| A3 | **Permission mapping** | 20 | App actions map to explicit user and admin permissions. | Wajib |
| A4 | **Session continuity** | 15 | Actor and session context persist across UI and tool transitions. | Wajib |
| A5 | **Review packaging** | 20 | App produces a coherent review artifact for expert validation. | Wajib |
| A6 | **Deployment operability** | 10 | Versioning, rollback, and environment isolation are in place. | Sunat |

**Minimum production threshold for GEOX MCP Apps: 78**

### 5.4 Subsurface Workflow Readiness

Measures whether GEOX supports credible end-to-end subsurface workflows rather than disconnected utilities.

| # | Criterion | Weight | Required condition | Fiqh |
|---|-----------|:------:|-------------------|:----:|
| S1 | **End-to-end flow** | 20 | Workflow covers evidence ingest through reviewable output. | Wajib |
| S2 | **Scenario analysis** | 20 | Low/base/high or equivalent scenario views are available. | Sunat |
| S3 | **Uncertainty expression** | 20 | Claims distinguish fact, interpretation, and speculation. | Wajib |
| S4 | **Cross-discipline coherence** | 20 | Geology, geophysics, petrophysics, and evaluation states remain consistent. | Sunat |
| S5 | **Review traceability** | 20 | Workflow preserves who changed what, when, and why. | Wajib |

**Minimum production threshold for subsurface workflow readiness: 80**

### 5.5 Production Authority Readiness

Determines whether the system may influence official model branches, sanctioned interpretations, or comparable authoritative outputs.[^4][^5][^6][^3]

| # | Criterion | Weight | Required condition | Fiqh |
|---|-----------|:------:|-------------------|:----:|
| P1 | **Identity propagation** | 20 | No action executes with null or anonymous actor/session context. | **Wajib** |
| P2 | **Asset and lease scoping** | 15 | Every action binds to declared basin, asset, and applicable scope. | **Wajib** |
| P3 | **Approval enforcement** | 20 | Irreversible steps require explicit human acknowledgement. | **Wajib** |
| P4 | **Audit completeness** | 15 | Logs are complete, queryable, and tamper-evident. | **Wajib** |
| P5 | **Error semantics** | 10 | Failures are structured, interpretable, and recoverable. | Sunat |
| P6 | **Tool budgeting and rate control** | 10 | Runaway or unbounded tool use is constrained. | Sunat |
| P7 | **Safety boundary** | 10 | No direct operational-control exposure exists through GEOX MCP. | **Haram** |

**Minimum production threshold for production authority readiness: 85**

---

## 6. Mandatory Gates

A GEOX system **MUST** fail readiness promotion if any of the following conditions is true:[^4][^8][^6][^3]

| Gate | Condition | Layer |
|------|-----------|-------|
| **G1** | `actor_id` is null, anonymous, or missing for any state-changing action. | Production authority |
| **G2** | `session_id` is null, anonymous, or missing for any app-mediated review action. | Production authority |
| **G3** | `asset_id` or `basin_id` is absent from asset-scoped workflows. | Production authority |
| **G4** | An AI interpretation can be promoted without visible evidence references. | Core / Subsurface |
| **G5** | An irreversible seal or vault action can occur without explicit acknowledgement. | Core |
| **G6** | A visual claim lacks CRS, datum, or equivalent spatial context where required. | UI / Subsurface |
| **G7** | GEOX exposes direct operational control to physical systems through unconstrained MCP tools. | Production authority |

---

## 7. Minimum Viable GEOX Review Workbench

A production-track GEOX UI **SHALL** include a Review Workbench, because MCP Apps provide general support for dashboards, forms, and visual flows, but high-authority domains require domain-specific governance above the base protocol.[^1][^2][^6][^3]

### 7.1 Required Panels

| Panel | Minimum content | Fiqh |
|-------|----------------|:----:|
| **Evidence** | LAS, tops, DST, seismic, faults, checkshot, PVT. QC state: RAW / INGESTED / QC_FAILED / QC_VERIFIED / NO_VALID_EVIDENCE. Provenance chain. | Wajib |
| **Interpretation** | Claim text, claim type, truth_class (FACT/INTERPRETATION/SPECULATION), uncertainty (P10/P50/P90), contradictions, alternatives, evidence references. | Wajib |
| **Visual** | Section/log/image view, AI overlay, confidence band, attribution flag or explicit `NO_SALIENCY_AVAILABLE`. | Wajib |
| **Scenario** | Base/low/high cases, perturbation results, sensitivity ranking, value movement (OOIP/GIIP/EUR/POS). | Sunat |
| **Seal** | Reject, request more evidence, approve as interpretation, seal to VAULT999, export review pack. Irreversible acknowledgement required for seal. | Wajib |

### 7.2 Workbench Architecture

```
MCP Host
  ↓
GEOX MCP App Shell
  ↓
GEOX Review Workbench UI  ←── UI sits BEFORE authority
  ↓
arifOS Constitutional Gate
  ↓
GEOX MCP Tool Surface
  ↓
Evidence Registry + Artifact Store
  ↓
Digital Twin / Sandbox Model
  ↓
Human Approval
  ↓
Official Model Branch / Sealed Claim
```

**Design law:** UI is not decoration. For GEOX, UI is governance. The workbench sits between agent reasoning and model authority.

---

## 8. Readiness Output Schema

Each readiness run **SHOULD** emit a machine-readable record:

```yaml
spec_version: geox-readiness/v0.1
system_id: geox-main
assessment_timestamp: 2026-06-15T01:53:00+08:00
scores:
  geox_mcp_core: 72
  geox_mcp_ui: 42
  geox_mcp_apps: 50
  subsurface_readiness: 61
  production_readiness: 45
status:
  geox_mcp_core: controlled_beta
  geox_mcp_ui: prototype
  geox_mcp_apps: internal_alpha
  subsurface_readiness: internal_alpha
  production_readiness: prototype
blocking_findings:
  - code: MISSING_IDENTITY_PROPAGATION
    severity: critical
    layer: production_authority
  - code: MISSING_REVIEW_WORKBENCH
    severity: critical
    layer: geox_mcp_ui
  - code: INCOMPLETE_ACCESS_SCOPING
    severity: high
    layer: production_authority
findings:
  - layer: geox_mcp_core
    statement: Domain-native tool surface exists.
  - layer: geox_mcp_ui
    statement: Visual review cockpit is incomplete.
  - layer: geox_mcp_apps
    statement: App shell possible, packaged governance incomplete.
decision:
  overall_score: 58
  readiness_band: internal_alpha
  production_authority_allowed: false
```

---

## 9. Decision Rules

| Condition | Result |
|-----------|--------|
| Overall ≥ 25 AND all blocking findings documented | Internal experimentation allowed |
| Overall ≥ 50 AND no mandatory gate violated for tested workflow subset | Governed internal alpha allowed |
| Overall ≥ 70 AND all layer thresholds except P.A. met AND rollback + audit proven | Controlled beta allowed |
| **All mandatory gates pass AND production authority readiness ≥ 85** | **Production authority allowed** |

---

## 10. Build-Priority Mappings

| Priority | Spec reference | Action | Fiqh |
|:--------:|---------------|--------|:----:|
| **P0** | P1 + G1 + G2 | End-to-end identity and session propagation across host, app shell, tool surface, and artifact store.[^4][^6][^3] | **Wajib** |
| **P1** | §7 + U1–U5 | Build GEOX Review Workbench v0 with evidence, interpretation, visual, scenario, and seal panels.[^1][^2][^9] | **Wajib** |
| **P2** | A1 + A3 + S2 | App manifest enforcement for asset, basin, discipline, reversibility, and review requirements. | **Wajib** |
| **P3** | C6 + S5 | Before/after diff generation for all reviewable model mutations. | Sunat |
| **P4** | §8 + P4 | Machine-readable readiness reports in CI/CD before deployment promotion.[^5][^3] | Sunat |

---

## 11. Fiqh Classification Guide

| Fiqh class | Meaning in readiness context | Action if unmet |
|------------|------------------------------|----------------|
| **Wajib** | Required for production authority. Cannot be skipped. | Block promotion. |
| **Sunat** | Strongly recommended. Significantly raises safety/stability. | Document gap, flag for next cycle. |
| **Makruh** | Discouraged pattern. May work short-term but causes long-term debt. | Actively refactor away. |
| **Haram** | Absolutely forbidden. Safety/boundary violation. | Immediate rollback if deployed. |

---

## 12. References

[^1]: Anthropic. "MCP Apps: UI Extension for Model Context Protocol." 2026.  
[^2]: Thoughtworks Technology Radar. "MCP Apps: Interactive UI Extensions for AI Tools." 2026.  
[^3]: arifOS Federation. "F1–F13 Constitution + Fiqh MCP Canon." 2026.  
[^4]: Deployment Patterns for MCP Production Paper. "Identity, Tool Budgeting, Error Semantics Gaps." 2026.  
[^5]: Enterprise MCP Adoption Study. "Fragmentation, Coordination, State, Fault Diagnosis." 2026.  
[^6]: MCP Safety & Security SoK. "Gating, Approval, Audit, Identity Requirements." 2026.  
[^7]: MCP Best Practices Guide. "Tool Design, Invocation, and Security Patterns." 2026.  
[^8]: CABP/ATBA/SERF Protocol Extensions for MCP Production Safety. 2026.  
[^9]: Anthropic. "MCP Apps UI Demonstration — Dashboard and Form Patterns." 2026.  
[^10]: MCP Apps Tutorial. "Packaging Static + Interactive Content into MCP App Manifests." 2026.  
[^11]: Seismic Attribute Families Literature. 2026.  
[^12]: Geospatial Safety Practice — CRS/Datum Standards. 2026.  
[^13]: MCP Ecosystem Maturity Report. 2026.

---

## 13. Amendment Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-06-15 | v0.1 | Initial specification. Five-layer model, mandatory gates, Review Workbench spec, build priorities. | Arif (F13) + FORGE (000Ω) |

---

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
