# GENESIS/006 — The AGI Loop: An Architectural Primitive
## Vision → LLM → World Model → Verifier → Gap Elicitor → Governor → Vault → Human

**Forged 2026-06-13. DITEMPA BUKAN DIBERI.**

---

## 0. PRIMITIVE, NOT EVERYTHING

This document defines one thing: **the governed epistemic loop as a
first-class architectural primitive.** It does not attempt to define all
of AGI. It defines the minimum structure that makes the loop auditable,
attestable, and resistant to self-ratification.

The loop is domain-invariant. GEOX is its first fully-implemented instance.
WEALTH, WELL, MEDX, SAFEX — any future organ — instantiates the same
primitive for its domain.

**Grounded in 41 papers across neuroscience, AI/LLM, and geoscience AI.**
See `GENESIS/005_AGI_LOOP_RESEARCH.md` for the full bibliography.

---

## 1. THE EIGHT ROLES (THREE LAYERS)

Roles are **capabilities**, not binaries. One organ may implement multiple
roles for low-stakes flows. For high-stakes flows, the Governor MUST reject
role multiplexing between Verifier and Governor in the same decision chain
(see §4.2).

### Perception Layer

| # | Role | Function | Question Answered |
|---|---|---|---|
| R0 | **Sensor** | Raw input ingestion. Non-visual telemetry: logs, DST readings, market data, vitals, seismic traces. | "What entered the system?" |
| R1 | **Vision** | Perceptual feature extraction from images/raster data. Edge detection, segmentation, anomaly flagging. | "What patterns are visible?" |

### Epistemic Layer

| # | Role | Function | Question Answered |
|---|---|---|---|
| R2 | **Language Cortex** | Hypothesis generation, naming, questioning, planning. The LLM. Produces structured claims from perceptual input. | "What might this be?" |
| R3 | **World Model** | Structured domain state. The Large Earth Model for geology, market state for WEALTH, patient model for MEDX. Grounds hypotheses in accumulated knowledge. | "What do we already know?" |
| R4 | **Verifier** | Physics/rules/constraints check. GEOX-class organ. Tests hypotheses against domain invariants. Returns claim_class, supporting evidence, contradictions, and gaps. | "Does this survive reality?" |
| R5 | **Gap Elicitor** | Explicit missing_inputs_schema emission. The formal encoding of "what we don't know yet." Drives the re-questioning arrow. | "What are we missing?" |

### Governance Layer

| # | Role | Function | Question Answered |
|---|---|---|---|
| R6 | **Governor** | Consequence gate. arifOS-class organ. Judges whether a verified claim may proceed to action. Applies constitutional floors. Issues SEAL, HOLD, or DENY. | "Should we act on this?" |
| R7 | **Vault** | Immutable witness. VAULT999-class organ. Records sealed claims, preserves dissent, maintains hash chain. | "What was decided?" |

### The Ninth Position

| Position | Function |
|---|---|
| **Human** | Sovereign. Outside the loop. Receives governance recommendations. Decides. The loop feeds evidence; the human owns the consequence. |

---

## 2. THE CANONICAL STATE MACHINE

### 2.1 States

```text
PERCEPTION:
  S0  RAW_INPUT         — unprocessed sensor data, images, documents
  S1  FEATURES          — extracted perceptual features, segmented regions

EPISTEMIC:
  S2  HYPOTHESIS        — named candidate(s) from Language Cortex
  S3  GROUNDED_STATE    — hypothesis resolved against World Model
  S4  VERIFICATION      — Verifier output: claim_class, evidence, contradictions
  S5  GAP_REPORT        — Gap Elicitor output: missing_inputs_schema

GOVERNANCE:
  S6  GOVERNANCE_DECISION — Governor output: ALLOW | HOLD | DENY | DEFER
  S7  SEALED_RECORD       — Vault output: immutable claim with hash pointer
```

### 2.2 Allowed Transitions

```text
S0 → S1    Perception: raw → features
S1 → S2    Language Cortex: features → hypothesis
S2 → S3    World Model query: hypothesis → grounded state
S3 → S4    Verification: grounded state → verification result
S4 → S5    Gap elicitation: verification → gap report

S5 → S2    RE-QUESTION LOOP  ← THE ANTI-MIRROR-LOOP INVARIANT
           Zero or more iterations. Each iteration MUST produce
           new information (new evidence, narrower uncertainty,
           or explicit confirmation that no further evidence exists).

S4 → S6    Governance gate: verification → decision
           Only when Verifier returns claim_state ∈ {VERIFIED, QUALIFIED}
           AND Gap Elicitor reports no blocking missing inputs.

S6 → S7    Seal: decision → immutable record
           Only when Governor returns SEAL. HOLD and DENY are recorded
           but not sealed.

S6 → S2    Appeal: decision → re-question
           When Governor returns HOLD with specific re-question instructions.

S6 → Human Final authority. All SEAL decisions are advisory to the sovereign.
           The Human may accept, reject, or defer.
```

### 2.3 Forbidden Transitions

```text
S4 → S2  WITHOUT S5    Verifier output must pass through Gap Elicitor
                       before re-questioning. Skipping S5 is the
                       Mirror Loop — syntactic reformulation without
                       epistemic update.

S4 → S6  WITHOUT S5    Verifier output must declare what is missing
                       before governance can judge sufficiency.

S2 → S6  (direct)      Ungrounded hypotheses must never reach governance.
                       The Verifier is a mandatory gate.
```

### 2.4 The Anti-Mirror-Loop Invariant

> S5 → S2 is NON-OPTIONAL for any high-stakes domain.
>
> Each re-question iteration MUST introduce new information:
> - New evidence acquired
> - Uncertainty band narrowed
> - Alternative interpretation explicitly excluded
> - Confirmation that no further evidence is obtainable
>
> If an iteration produces no new information, the loop TERMINATES
> at S5 with `claim_too_certain_flag: true` and escalates to HUMAN.

This invariant is the architectural answer to the Mirror Loop problem
(arXiv:2510.21861). Without an independent verifier providing real
information gain, self-critique collapses to self-paraphrase. The
Gap Elicitor (S5) is the formal mechanism that guarantees each
re-questioning cycle is epistemically productive.

---

## 3. THE THREE ENVELOPE SCHEMAS

### 3.1 HypothesisEnvelope (S2 → S3 → S4)

Emitted by Language Cortex. Consumed by World Model and Verifier.

```text
HypothesisEnvelope {
  // Identity
  envelope_type: "HypothesisEnvelope"
  envelope_version: "1.0.0"
  session_id: str
  actor_id: str
  role: "LanguageCortex"

  // Content
  hypothesis: str                    // natural language claim
  hypothesis_class: enum[            // machine-parseable type
    "EXPLANATION"                    // "this is why X happened"
    "PREDICTION"                     // "given Y, Z will happen"
    "CLASSIFICATION"                 // "this thing is of type T"
    "RELATION"                       // "A is related to B by relation R"
    "QUANTITY"                       // "the value of V is within range [L, U]"
  ]
  domain: str                        // geology | medicine | finance | robotics
  confidence_prior: float            // 0.0–1.0, before verification

  // Evidence
  perceptual_input_refs: [str]       // pointers to S0/S1 artifacts
  prior_claim_refs: [str]            // pointers to previously sealed claims

  // Provenance
  organ_id: str                      // which LLM
  model_id: str                      // model version
  timestamp_utc: str
  identity_anchor_type: str          // e.g. "language_model"
  identity_anchor_hash: str          // SHA-256 of model manifest
}
```

### 3.2 VerificationEnvelope (S4 → S5 → S6)

Emitted by Verifier (GEOX-class organ). Consumed by Gap Elicitor and Governor.

```text
VerificationEnvelope {
  // Identity
  envelope_type: "VerificationEnvelope"
  envelope_version: "1.0.0"
  session_id: str
  actor_id: str
  role: "Verifier"

  // Reference
  hypothesis_ref: str                // pointer to HypothesisEnvelope
  world_model_ref: str               // pointer to GroundedState (S3)

  // Verdict
  claim_class: enum[
    "FACT"                           // directly observed; no interpretation
    "INTERPRETATION"                 // derived from physics/consistency
    "SPECULATION"                    // inferred from analogy/statistics
  ]
  claim_state: enum[
    "VERIFIED"                       // all constraints satisfied
    "QUALIFIED"                      // constraints satisfied with caveats
    "HYPOTHESIS"                     // plausible but unverified
    "HOLD"                           // cannot verify — missing evidence
    "VOID"                           // contradicted by evidence
  ]

  // Evidence
  supporting_evidence: [EvidenceRef] // typed refs with provenance
  contradicting_evidence: [EvidenceRef]
  alternative_interpretations: [str] // competing hypotheses with evidence

  // Physics / Rules
  domain_law: str                    // NATURAL_LAW | CAPITAL_LAW | SUBSTRATE_LAW
  invariants_checked: [str]          // which domain invariants were tested
  invariants_violated: [str]         // which invariants were violated
  physics_guard_version: str         // hash of the invariant set used

  // Uncertainty
  uncertainty: {
    p10: float
    p50: float
    p90: float
    distribution: str                // lognormal | normal | triangular | uniform
    epistemic_source: str            // measurement | model | sampling | expert
  }

  // Identity anchor
  identity_anchor_type: str          // e.g. "physics_manifest"
  identity_anchor_hash: str          // SHA-256 of GENESIS manifest

  // Provenance
  organ_id: str
  timestamp_utc: str
}
```

### 3.3 GovernanceEnvelope (S6 → S7 → Human)

Emitted by Governor (arifOS-class organ). Consumed by Vault and Human.

```text
GovernanceEnvelope {
  // Identity
  envelope_type: "GovernanceEnvelope"
  envelope_version: "1.0.0"
  session_id: str
  actor_id: str
  role: "Governor"

  // Reference
  verification_ref: str              // pointer to VerificationEnvelope
  gap_report_ref: str                // pointer to GapReport (S5)

  // Decision
  decision: enum[
    "ALLOW"                          // proceed — sufficient evidence
    "HOLD"                           // pause — more evidence or review needed
    "DENY"                           // blocked — violates floors
    "DEFER"                          // escalate — beyond scope, route to human
  ]

  // Consequence
  consequence_class: enum[
    "CAPITAL"                        // financial/resource commitment
    "SAFETY"                         // physical harm risk
    "REPUTATIONAL"                   // institutional trust risk
    "SOVEREIGN"                      // jurisdictional/legal risk
    "NONE"                           // advisory only, no consequence
  ]
  blast_radius: enum[LOW | MEDIUM | HIGH | CRITICAL]

  // Floors hit
  floors_checked: [str]              // F1–F13, which were evaluated
  floors_triggered: [str]            // which floors fired
  floor_reasoning: str               // human-readable explanation

  // Identity
  identity_anchor_type: str          // "constitution_hash"
  identity_anchor_hash: str          // SHA-256 of 000_KERNEL_CANON.md

  // Seal
  seal_pointer: str | null           // VAULT999 entry ID, if sealed
  requires_human_ack: bool           // true if blast_radius ≥ MEDIUM

  // Provenance
  organ_id: str
  timestamp_utc: str
  human_acknowledged: bool
  human_acknowledged_at: str | null
}
```

---

## 4. IDENTITY AND MANIFEST INVARIANTS

### 4.1 Every Role MUST Expose

```text
role_identity {
  role_type: R0 | R1 | R2 | R3 | R4 | R5 | R6 | R7
  identity_anchor_type: str          // domain-specific law type
  identity_anchor_hash: str          // SHA-256 of canonical manifest
  domain_law: str                    // NATURAL_LAW | CAPITAL_LAW | SUBSTRATE_LAW | CONSTITUTION_LAW
}
```

### 4.2 Role Multiplexing Rule

```text
For any decision chain with consequence_class ∈ {CAPITAL, SAFETY, SOVEREIGN}:

  NO SINGLE ORGAN MAY IMPLEMENT BOTH:
    - R4 (Verifier) AND R6 (Governor) in the same chain

  Rationale: The MAR finding (arXiv:2512.20845) and Mirror Loop paper
  (arXiv:2510.21861) both demonstrate that single-model self-ratification
  produces rubber-stamping. Separating verifier from governor at the
  identity level prevents this failure mode at the architectural level.

For consequence_class ∈ {REPUTATIONAL, NONE}:
  Role multiplexing is permitted but MUST be declared in the audit trail.
```

### 4.3 Identity Anchor Registry

```text
Organ    | Role | domain_law      | Manifest File                      | Hash
─────────┼──────┼─────────────────┼────────────────────────────────────┼─────
arifOS   | R6   | CONSTITUTION_LAW| GENESIS/000_KERNEL_CANON.md        | sha256:...
GEOX     | R4   | NATURAL_LAW     | GENESIS/003a_PHYSICS_MANIFEST.md    | sha256:b51811b1...
WEALTH   | R4   | CAPITAL_LAW      | canon/001_CAPITAL_MANIFEST.md       | sha256:9e5c55b4...
WELL     | R4   | SUBSTRATE_LAW    | GENESIS/012_SUBSTRATE_MANIFEST.md    | sha256:fd21db85...
VAULT999 | R7   | IMMUTABLE_LAW    | (vault hash chain)                  | sha256:...
```

Each Verifier-class organ answers to a DIFFERENT kind of law. They are
not interchangeable. A physics verdict cannot govern. A capital verdict
cannot diagnose. The domain_law field enforces this separation.

---

## 5. CROSS-DOMAIN GENERALISATION

The loop is a primitive. GEOX is the first worked instance. The same
roles map to any domain with a verifiable world model.

```text
Domain    | World Model          | Verifier | Governor | Example Gate
──────────┼──────────────────────┼──────────┼──────────┼──────────────────────
Geology   | Large Earth Model    | GEOX     | arifOS   | drill / capital alloc
Medicine  | Patient/Anatomy FM   | MEDX*    | arifOS   | treatment / surgery
Finance   | Market State / Books | WEALTH   | arifOS   | trade / portfolio shift
Robotics  | Spatial World Model  | SAFEX*   | arifOS   | unsafe motion veto
Climate   | Earth System Model   | CLIMX*   | arifOS   | emission / intervention
Legal     | Corpus Juris / Precedent | LEX* | arifOS   | filing / liability

* denotes future organ
```

Each row is the same loop. Each Verifier enforces a different kind of law.
The Governor (arifOS) is the universal gate — it adjudicates consequence,
not domain truth.

---

## 6. GEOX AS THE WORKED EXAMPLE

### 6.1 GEOX Role Map

```text
R0 (Sensor):     LAS ingestion, SEG-Y reading, DST ingestion
R1 (Vision):     Seismic section VLM interpretation, fault stick extraction
R3 (World Model): LEM — structured subsurface state, basin profiles
R4 (Verifier):   GEOX — Physics9 invariants, claim taxonomy, evidence cross-check
R5 (Gap Elicitor): missing_inputs_schema in VerificationEnvelope
```

GEOX does NOT implement:
- R2 (Language Cortex) — that's the LLM's role
- R6 (Governor) — that's arifOS
- R7 (Vault) — that's VAULT999

### 6.2 GEOX Loop Trace (Concrete Example)

```text
S0: Raw SEG-Y cube + well LAS files ingested
S1: Seismic attributes computed; VLM identifies amplitude anomalies
S2: LLM generates hypothesis: "Bright spot at inline 4200, TWT 2.1s
    is a gas-bearing channel sand of Group H age"
S3: LEM resolves hypothesis against basin stratigraphy, nearby well tops,
    regional depositional model
S4: GEOX verifies:
    - AVO class III match? ✓
    - Depth consistent with Group H burial? ✓
    - Nearby DST shows gas? ✗ (nearest DST 5 km away, oil only)
    - Structural closure present? ✓
    → claim_class: INTERPRETATION
    → claim_state: QUALIFIED (DST gap)
S5: Gap Elicitor emits missing_inputs_schema:
    - "DST or MDT sample within 2 km of prospect"
    - "Seismic inversion for acoustic impedance at target"
S5 → S2: LLM re-questions:
    "Given the DST gap and the qualified verification, what alternative
     interpretations exist? Could this be an oil leg? A fizz-water sand?
     What additional data would discriminate?"
S2 → S3 → S4: Second pass with alternative hypotheses
S4 → S5: Updated gap report. Uncertainty narrowed but DST gap remains.
S4 → S6: Governance gate. Claim state = QUALIFIED. Gap = DST still missing.
S6: arifOS judges:
    - Consequence class: CAPITAL (drill decision)
    - Blast radius: HIGH (dry hole cost + reputational)
    - Floor F4 (reversibility): DRILL IS IRREVERSIBLE
    - Decision: HOLD — acquire DST or seek human waiver
S6 → Human: "Prospect is physics-consistent but uncalibrated.
    Dry-hole risk is unquantified without DST. Recommended: acquire
    offset DST before drilling. Human may override with explicit
    acknowledgment of uncalibrated risk."
```

### 6.3 GEOX Tool Surface → Loop State Mapping

```text
geox_data_ingest_bundle       → S0 (Sensor)
geox_seismic_compute           → S1 (Vision)
geox_vision_minimax_inference  → S1 (Vision)
geox_basin_profile             → S3 (World Model)
geox_claim_create              → S2 → S4 (Hypothesis → Verification)
geox_claim_validate            → S4 (Verification)
geox_claim_challenge           → S4 (Verification — adversarial)
geox_evidence_reason           → S4 (Verification)
geox_subsurface_verify_integrity → S4 (Verification — Physics9 gate)
geox_evidence_discover         → S5 (Gap Elicitor — what's missing)
geox_prospect_evaluate         → S4 → S6 (Verification → Governance boundary)
arif_judge                    → S6 (Governor)
arif_seal                     → S7 (Vault)
```

---

## 7. INVARIANTS (THE SHORT FORM)

1. **Verifier Independence.** R4 (Verifier) and R6 (Governor) must be
   separate organs for high-stakes decisions.

2. **Gap Gate.** S5 MUST precede any S4 → S6 transition. You cannot
   govern what you haven't declared missing.

3. **Re-Question with Information Gain.** S5 → S2 iterations must produce
   new information or terminate.

4. **Domain Law Separation.** Verifier organs answer to different laws
   (NATURAL_LAW ≠ CAPITAL_LAW ≠ SUBSTRATE_LAW). Cross-domain conflation
   is a constitutional error.

5. **Human Is Outside the Loop.** The loop feeds evidence. The human
   decides. No SEAL bypasses the sovereign.

6. **Identity Anchor Chain.** Every envelope carries the emitting organ's
   identity_anchor_type + identity_anchor_hash. The chain is auditable
   from S0 to S7.

7. **Provenance Over Assertion.** `claim_class` is determined by evidence
   type and verification result, not by model confidence. An LLM that is
   99% confident in a hallucination produces SPECULATION, not FACT.

---

## 8. RELATIONSHIP TO EXISTING GENESIS FILES

```text
000_KERNEL_CANON.md       — arifOS constitution. Governs R6.
003a_PHYSICS_MANIFEST.md  — GEOX domain law. Governs R4 for geology. (was 004, now redirects)
005_AGI_LOOP_RESEARCH.md  — Literature grounding (41 papers, 3 domains).
006_AGI_LOOP.md           — THIS FILE. The loop as architectural primitive.
```

---

## 9. VERSION

```text
Version:      1.0.0
Status:       FORGED
Hash:         sha256:<computed on seal>
Predecessor:  005_AGI_LOOP_RESEARCH.md
Successor:    (none — this is the current head of the AGI loop lineage)

DITEMPA BUKAN DIBERI — Forged, Not Given.
```
