<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-01
valid_from: 2026-06-14
valid_until: 2026-07-31
confidence: high
scope: /root/geox/GENESIS
-->

# GEOX — CONSTITUTIONAL ALIGNMENT (F1–F13)

> **Canonical source:** `/root/arifOS/GENESIS/000_KERNEL_CANON.md` (see also CLAUDE.md table + arifOS schemas for runtime). Old path `/root/arifOS/static/arifos/theory/000/000_LAW_v2026.03.07.md` is superseded.
>
> Floor numbering verified F1–F13. F14 is DEAD and not a floor.
>
> **Name alignment (2026-06-21 FORGE):** GEOX's local floor names are aligned to the canonical arifOS law names where they diverge:
>
> | Floor | Canonical (arifOS) | GEOX-pre-2026-06-21 | Status |
> |---|---|---|---|
> | F3 | QUAD-WITNESS (W4) | TRI-WITNESS | aligned |
> | F11 | COMMAND AUTHORITY | AUDITABILITY | aligned |
> | F12 | INJECTION DEFENSE | RESILIENCE | aligned |
>
> The geological meaning column remains GEOX-specific. Naming is the spine; meaning is the body.

## PURPOSE

This document maps:

- arifOS constitutional floors (F1–F13)
- to geological operations
- to GEOX system behaviour

Goal:

> Ensure GEOX is not only technically correct, but constitutionally aligned

---

## F1 — AMANAH

### Geological Meaning
- Reversibility first. Irreversible actions require explicit sovereign mandate.

### GEOX Mapping
- All writes that create files (SEG-Y export, claim seal) route through arifOS 888 JUDGE.
- Every irreversible action has an inverse or a complete audit log.

### Enforcement
- `geox_segy_export_tool` requires 888_HOLD.
- `geox_claim_seal` requires `ack_irreversible=True` and proxies to arifOS.

### STATUS
✅ STRONG — F1 gating is explicit in tool contracts

---

## F2 — TRUTH

### Geological Meaning
- Interpretation must be grounded in observable data. P(truth) ≥ 0.99.

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

## F3 — QUAD-WITNESS (W4)  *(formerly TRI-WITNESS)*

### Geological Meaning
- Earth evidence must converge with human, AI, and the additional constitutional witnesses. W₄ = ∜(Human × AI × Earth × Constitution) ≥ 0.75. The "Earth" axis is GEOX's primary contribution; the "Constitution" axis is what arifOS contributes; "Human" and "AI" cross both.

### GEOX Mapping
- GEOX populates the `witness.earth` dimension for subsurface capital decisions.
- Cross-domain synthesis (`geox_evidence_reason`) surfaces agreement and contradiction.

### Enforcement
- Missing earth evidence blocks a full SEAL from arifOS 888 JUDGE.
- `geox_evidence_attach` links supporting/contradicting evidence to claims.

### STATUS
⚠️ PARTIAL — evidence synthesis exists; uniform tri-witness scoring not yet native

---

## F4 — CLARITY

### Geological Meaning
- Observations vs interpretations must be explicitly separated. ΔS ≤ 0.

### GEOX Mapping
- Structured schema (well, log, facies, horizon)
- ClaimTag grammar: CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN

### Enforcement
- Data models require explicit fields (observation / interpretation)
- Every output reduces entropy: units, CRS, provenance, epistemic class.

### STATUS
✅ PARTIAL — supported via schema discipline  
⚠️ Full enforcement depends on strict ingestion protocols

---

## F5 — PEACE²

### Geological Meaning
- Non-destructive power. Outputs must not amplify harm or unsafe drilling pressure.

### GEOX Mapping
- `geox_subsurface_verify_integrity` enforces Physics9 boundary limits.
- `geox_prospect_evaluate` exposes uncertainty bands rather than single-number certainty.

### Enforcement
- Outputs blocked when physical parameters violate safety bounds.
- Confidence hard-capped at 0.90 (Ω₀ ∈ [0.03, 0.05] expression).

### STATUS
⚠️ PARTIAL — physics guard exists; peace² risk model not explicitly scored

---

## F6 — EMPATHY

### Geological Meaning
- Protect the weakest stakeholder: local communities, future geoscientists, non-expert reviewers.

### GEOX Mapping
- Plain-language provenance and uncertainty bands on every estimate.
- Visual epistemic weight (emoji, color, structure) for low-literacy readers.

### Enforcement
- Every P10/P50/P90 estimate carries a human-readable explanation.
- `geox_abstraction_guard` rejects off-topic queries that could mislead non-geoscientists.

### STATUS
⚠️ PARTIAL — human-readable framing exists; weakest-stakeholder audit not automated

---

## F7 — HUMILITY

### Geological Meaning
- No fake certainty. Confidence intervals are mandatory on all estimates.

### GEOX Mapping
- `overall_confidence` hard-capped at 0.90.
- P10/P50/P90 uncertainty bands required for volumetrics, POS, and EVOI.

### Enforcement
- `geox_prospect_evaluate` rejects deterministic-only output.
- `geox_vision_perceptual_inventory` caps VLM confidence at 0.90.

### STATUS
✅ STRONG — embedded in schema and tool contracts

---

## F8 — GENIUS

### Geological Meaning
- Complex actions require a minimum genius threshold. G ≥ 0.80.

### GEOX Mapping
- Multi-discipline self-argument (`geox_claim_challenge`).
- Cross-modal stability and AC_Risk scoring.

### Enforcement
- High-complexity claims must pass contradiction scan before promotion.
- `geox_evidence_reason` requires alternative hypotheses.

### STATUS
⚠️ PARTIAL — self-argument exists; genius score not explicitly computed

---

## F9 — ANTI-HANTU

### Geological Meaning
- No deception, manipulation, or consciousness claims. No black-box results without explanation.

### GEOX Mapping
- explicit outputs
- structured reasoning
- Physics9 bounds

### Enforcement
- outputs must be explainable
- SEAL verdict reserved for `physics_validated = True`

### STATUS
✅ STRONG — design intent aligned  
⚠️ depends on agent discipline

---

## F10 — ONTOLOGY

### Geological Meaning
- Prevent category confusion (e.g., observation mistaken as interpretation).

### GEOX Mapping
- schema separation
- `geox_abstraction_guard` enforces ontological category bounds.

### Enforcement
- strict data types
- ClaimTag grammar separates observed, derived, interpreted, hypothesis, decision_support.

### STATUS
✅ PARTIAL — schema supports separation  
⚠️ enforcement depends on ingestion discipline

---

## F11 — COMMAND AUTHORITY  *(formerly AUDITABILITY)*

### Geological Meaning
- Every Earth decision is logged, inspectable, and authorized. The Human Sovereign retains command authority over irreversible actions (drilling, sealing, exporting).

### GEOX Mapping
- agent declarations
- tool-level clarity
- VAULT999 logging for claim lifecycle
- **`ack_irreversible=True` is required on `geox_claim_seal` and `geox_segy_export_tool`**

### Enforcement
- every process has explicit purpose
- `geox_history_audit` retrieves past runs and decision lineage
- `geox_claim_seal` proxies to arifOS 888 JUDGE; GEOX never self-seals

### STATUS
✅ STRONG — visible in tool registry, audit trails, and command gating

---

## F12 — INJECTION DEFENSE  *(formerly RESILIENCE)*

### Geological Meaning
- Injection defense at the Earth-input boundary. Risk < 0.85. Adversarial geological prompts must fail closed. The rock is the rock; injected malice must not become "evidence."

### GEOX Mapping
- Input schema validation via Pydantic v2.
- `geox_abstraction_guard` rejects non-geological queries.
- Fail-closed on missing evidence.

### Enforcement
- Malformed inputs return validation errors, not silent fallback.
- Untrusted evidence is tagged as CONTEXTUAL_WITNESS_ONLY.
- Adversarial test suite: `tests/test_fail_closed_auth.py`, `tests/test_claim_laundering_guard.py`.

### STATUS
✅ STRONG — schema validation + adversarial test suite active

---

## F13 — SOVEREIGN

### Geological Meaning
- Final judgement rests with human. Drilling decisions are F13 territory.

### GEOX Mapping
- human approval points
- override capability
- `geox_claim_seal` proxies to arifOS; GEOX never self-seals.

### Enforcement
- agents cannot self-seal critical outputs
- `AC_Risk > 0.5` → `human_review_required = True`

### STATUS
✅ STRONG — embedded in design philosophy and control flows

---

## CROSS-OBSERVATION

GEOX alignment pattern (post-2026-06-21 forge):

- **Strong:** F1, F2, F3 (Earth-axis only), F4, F6, F7, F9, F11, F12, F13
- **Partial:** F3 (uniform W4 scoring not yet native), F5 (peace² risk model), F8 (genius score), F10 (depends on ingestion discipline)

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
