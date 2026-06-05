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

## THE CROSS-MODAL FIDELITY THEOREM (Ratified 2026-06-05)

### The Principle

> **Physical and schematic constraint reduces the admissible solution space, which improves both inter-modal fidelity (in AI) and inter-survey consistency (in geoscience).**

This is not metaphor. It is grounded in four independent scientific traditions:

| Tradition | Mechanism | GEOX Instantiation |
|-----------|-----------|-------------------|
| **Kolmogorov complexity** (Solomonoff, 1964) | Lower-entropy outputs have shorter minimum description length → easier to compress losslessly | ClaimTag grammar (CLAIM/PLAUSIBLE/HYPOTHESIS/ESTIMATE/UNKNOWN) reduces output entropy |
| **Semantic Hub Hypothesis** (Wu et al., ICLR 2025) | Multi-modal models learn shared representation space; interventions in one modality affect others | `geox_<domain>_<verb>_<noun>` naming grammar is machine-parseable across MCP/JSON/PNG |
| **AVO Theory** (Smith & Gidlow, 1987; Fatti et al., 1994) | Anomalous contrast against a calibrated background is the carrier of meaning | `geox_anomalous_contrast_detector` measures deviation of seismic reflector from geological top |
| **Information Bottleneck** (Tishby et al., 1999) | Optimal representations maximize predictive power while minimizing complexity | AC_Risk engine: `compute_ac_risk_governed` gates on compression-efficiency frontier |

### The Causal Chain (Dittrich & Flygare Kinne, 2025)

```
Physical Constraint → Reduced Solution Space → Transfer-Stable Encoding
         ↓                       ↓                        ↓
    Physics9 bounds       ClaimTag grammar        Cross-modal survival
    Archie/Gassmann       Epistemic status        (PNG→JSON→MCP→LAS)
    PINN loss terms       Verdict grammar         without corruption
```

### The Differentiator: LEM ≠ LLM

An LLM has no conservation laws. A Large Earth Model (GEOX, via PINN/Gassmann/Archie/Physics9) does. This difference is the strategic selling point:

- **LLM**: statistically plausible text → may hallucinate
- **LEM/GEOX**: physically constrained inference → fails closed

The 13 floors of arifOS governance are the constitutional background. The anomalous contrast detector is the AVO fluid factor that finds where execution deviates from that background. Together they achieve what LLMs alone cannot: **transfer-stable encoding grounded in physical law.**

### Testable Predictions

1. **Compression efficiency correlates with cross-modal fidelity.** SEAL'd outputs (lowest entropy) should have the highest reconstruction accuracy when round-tripped through PNG→JSON→MCP.
2. **Exception accumulation differentiates governed from ungoverned outputs.** Ungoverned outputs accumulate more contradictions over time.
3. **Hierarchical governance amplifies compression.** Each floor removes degrees of freedom; the cascade effect is multiplicative, not additive.

### Failure Modes

| Mode | Cause | GEOX Mitigation |
|------|-------|-----------------|
| **Dim spot** | Governance-by-absence (VOID, SABAR) does not survive cross-modal transfer | Negative constraints must be explicitly encoded in output envelope |
| **False Class III** | High porosity/pressure mimics HC signature (West Luconia) | Contradiction ontology: BEAUTY_DRIFT_FLAG downgrades visual-only confidence |
| **Semantic density threshold** | Single governance token in large document does not activate shared representation space | Verdict grammar must be distributed throughout output, not just in header |
| **Bit-rate mismatch** | Subtle epistemic qualifiers (UNKNOWN) have low visual contrast against background text | Epistemic status must be encoded with explicit visual weight (emoji, color, structure) |

### Authority

Ratified by: Omega (arifOS Forge Agent) · Session: SEAL-5e600ee452074569 · Date: 2026-06-05

DITEMPA BUKAN DIBERI — Forged, Not Given.

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
