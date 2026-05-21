<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-05-20
valid_from: 2026-05-20
confidence: high
scope: /root/geox/GENESIS
-->

# GEOX — CONSTITUTIONAL ALIGNMENT (F1–F13)

## PURPOSE

This document maps:

- arifOS constitutional floors (F1–F13)
- to geological operations
- to GEOX system behaviour

Goal:

> Ensure GEOX is not only technically correct, but constitutionally aligned

---

## F01 — CLARITY

### Geological Meaning
- Observations vs interpretations must be explicitly separated

### GEOX Mapping
- Structured schema (well, log, facies, horizon)

### Enforcement
- Data models require explicit fields (observation / interpretation)

### STATUS
✅ PARTIAL — supported via schema discipline  
⚠️ Full enforcement depends on strict ingestion protocols

---

## F02 — TRUTH

### Geological Meaning
- Interpretation must be grounded in observable data

### GEOX Mapping
- Evidence-linked outputs
- traceable reasoning artifacts

### Enforcement
- Each interpretation must reference:
  - well logs
  - seismic
  - dataset source

### STATUS
✅ PARTIAL — evidence artifacts exist  
⚠️ Not all tools enforce mandatory evidence linkage

---

## F03 — STABILITY

### Geological Meaning
- Interpretations must be reproducible

### GEOX Mapping
- persistent state + versioning

### Enforcement
- same input → same output (agent determinism)

### STATUS
⚠️ UNKNOWN — full reproducibility across agents not proven

---

## F04 — EQUITY (ACCESS)

### Geological Meaning
- No geoscientist blocked by system access

### GEOX Mapping
- compute-on-demand model

### Enforcement
- no FCFS gating
- no seat-based limitation

### STATUS
⚠️ PARTIAL — removal of license constraint achieved conceptually  
❌ Infra still bounded (single VPS)

---

## F05 — MARUAH (DIGNITY)

### Geological Meaning
- Human expertise must not be dismissed by automation

### GEOX Mapping
- human-in-loop validation
- override capability

### Enforcement
- final decision always human

### STATUS
✅ STRONG — embedded via design philosophy  
⚠️ Requires continuous discipline in agent deployment

---

## F06 — STEWARDSHIP

### Geological Meaning
- Full utilisation of data and capability

### GEOX Mapping
- ingestion pipelines
- multi-source integration

### Enforcement
- no data left unused due to access constraints

### STATUS
✅ PARTIAL — ingestion exists  
⚠️ completeness of datasets UNKNOWN

---

## F07 — PARALLELISM

### Geological Meaning
- Multiple interpretations can coexist and be evaluated

### GEOX Mapping
- multi-agent reasoning
- concurrent execution

### Enforcement
- simultaneous workflows allowed

### STATUS
⚠️ PARTIAL — agent layer exists  
❌ full A2A orchestration not native in GEOX

---

## F08 — REFLECTION

### Geological Meaning
- System must self-check interpretations

### GEOX Mapping
- QC agents
- validation routines

### Enforcement
- contradiction detection
- alternative hypotheses

### STATUS
⚠️ PARTIAL — QC tools exist  
⚠️ not uniformly enforced

---

## F09 — ANTI-HANTU (NO FAKE INTELLIGENCE)

### Geological Meaning
- No black-box results without explanation

### GEOX Mapping
- explicit outputs
- structured reasoning

### Enforcement
- outputs must be explainable

### STATUS
✅ STRONG — design intent aligned  
⚠️ depends on agent discipline

---

## F10 — ONTOLOGY WALL

### Geological Meaning
- Prevent category confusion (e.g., observation mistaken as interpretation)

### GEOX Mapping
- schema separation

### Enforcement
- strict data types

### STATUS
✅ PARTIAL — schema supports separation  
⚠️ enforcement depends on ingestion discipline

---

## F11 — AUTHENTICITY

### Geological Meaning
- Intent must be declared, not hidden

### GEOX Mapping
- agent declarations
- tool-level clarity

### Enforcement
- every process has explicit purpose

### STATUS
✅ STRONG — visible in tool registry

---

## F12 — GOVERNANCE WALL

### Geological Meaning
- High-impact decisions must be controlled

### GEOX Mapping
- 888 / 999 gating (via arifOS)

### Enforcement
- irreversible decisions require confirmation

### STATUS
✅ STRONG (via arifOS integration)  
⚠️ GEOX alone does not enforce — relies on external governance layer

---

## F13 — HUMAN SOVEREIGNTY

### Geological Meaning
- Final judgement rests with human

### GEOX Mapping
- human approval points
- override capability

### Enforcement
- agents cannot self-seal critical outputs

### STATUS
✅ STRONG — embedded in design philosophy and control flows

---

## CROSS-OBSERVATION

GEOX alignment pattern:

- **Strong:** F05, F09, F11, F12, F13
- **Partial:** F01, F02, F04, F06, F07, F08, F10
- **Unknown:** F03 reproducibility

---

## CORE GAP

> GEOX is constitutionally aligned in philosophy,  
> but partially realised in infrastructure and enforcement

---

## FINAL LAW

GEOX must evolve until:

> no geological reasoning is blocked by access,  
> and no interpretation exists without traceable truth

---

## 999 — VERDICT

Alignment achieved at intent level.  
Execution maturity: in progress.  
Governance: dependent on arifOS.

System state:

> VALID — NOT COMPLETE
