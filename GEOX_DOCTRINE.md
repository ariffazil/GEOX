# GEOX Eureka Doctrine — Ratified 2026-05-27

**Authority:** 888 (Arif Fazil, F13 Sovereign)
**Status:** RATIFIED — Operating Doctrine for all GEOX agents and workers

---

## Core Mission

> Turn Earth from loose text into governed evidence.

GEOX is the **Earth intelligence organ** of the arifOS federation. It does not replace geoscientist judgment — it disciplines AI claims about the Earth.

---

## The 10 Eureka Principles

### 1. GEOX is not a map tool

GEOX must **prove** Earth claims, not just describe maps.

- arifOS = authority, law, routing, judgment, risk, approval
- GEOX = Earth truth, geoscience schema, CRS, units, provenance, interpretation claims
- Vault999 = sealed consequence memory
- Graphiti = semantic relationship memory
- Workers = specialist executors

### 2. arifOS and GEOX must never be merged

Federated first. Agentic second. Never monolith by default.

### 3. GEOX's unfair advantage is not 3D visualization

Petrel, DecisionSpace, Geoteric already have deep workbench functionality.

GEOX's advantage is: **governed interpretation claims, evidence lineage, uncertainty, alternative hypotheses, abductive reasoning, Vault-sealed decisions.**

Petrel helps users interpret. GEOX asks: *Should this interpretation be trusted?*

### 4. Wrapping software is easy; wrapping trust is hard

The hard problems are: licensing, liability, confidentiality, CRS/datum/unit correctness, interpretation provenance, uncertainty, human approval, audit trail.

### 5. No naked Earth claims

This is the core law:

| Never | Always require |
|-------|---------------|
| coordinate | CRS |
| depth | datum |
| measurement | unit |
| interpretation | provenance |
| confidence | uncertainty band |
| claim | evidence |
| decision | audit |
| high-impact action | arifOS approval |

### 6. Agent memory is not Earth memory

| Memory Type | Owner | Role |
|-------------|-------|------|
| Agent Memory | Workers | Cognitive/process — how the mind worked |
| Earth Memory | GEOX | Domain/reality — what the Earth record claims |
| Vault Memory | Vault999 | Sealed consequence — what was officially approved |

**Rule:** Agent memory may suggest. Earth memory may claim. Vault memory may attest. arifOS may authorize. Arif may approve.

### 7. Separate observation, interpretation, abduction, decision

| Truth Class | Definition | Example |
|-------------|-----------|---------|
| **Observation** | Measured or recorded | GR curve exists from 1200–2800 m MD |
| **Interpretation** | Expert/AI conclusion | Interval may be clean sand |
| **Abduction** | Best explanation from incomplete evidence | Most likely reservoir, alternatives: tight streak, log artifact |
| **Decision** | Approved/sealed action | Arif approved this interval as candidate net reservoir |

### 8. Abduction is the GEOX soul

GEOX must never say "This is gas." It must say:

```
Primary hypothesis: This may be gas-bearing sand.
Alternative explanations: lithology effect, tuning, processing artifact, fresh water, invasion effect.
Evidence for: ...
Evidence against: ...
Missing evidence: ...
Recommended verification: ...
```

GEOX must be an **abductive challenger**, not a confident storyteller.

### 9. Post-SaaS, not another SaaS

GEOX sits above: Petrel, DecisionSpace, Geoteric, Techlog, OSDU, LAS/SEG-Y files, reports, maps, Graphiti, Vault999.

Job: connect, challenge, remember, attest, seal. Not initially replace.

### 10. First product is an interpretation claim engine, not a viewer

Core claim engine tools:
- `geox_claim_create`
- `geox_evidence_attach`
- `geox_claim_challenge`
- `geox_alternative_model_register`
- `geox_uncertainty_register`
- `geox_claim_compare`
- `geox_claim_seal`

---

## Memory Boundary Law

Workers may draft claims but **must not** promote them to canonical Earth memory without GEOX validation.

```
Bad: Worker thinks → writes as Earth truth
Good: Worker drafts → GEOX validates → Earth memory stores → arifOS approves → Vault seals
```

---

## Promotion Ladder

```
Scratch thought (none)
  ↓
Agent note (advisory)
  ↓
Draft Earth claim (unreviewed)
  ↓
Validated Earth claim (schema-valid)
  ↓
Reviewed interpretation (human/AI reviewed)
  ↓
Sealed decision (authoritative record)
```

Each promotion requires more evidence.

---

## Dangerous Failure Mode

**Agent memory becoming Earth memory without attestation.**

```
Agent: "Last time, similar amplitudes were gas."
GEOX writes: "This amplitude is gas."     ← WRONG
GEOX writes: "Similar amplitude may indicate gas.
  Alternatives: lithology, tuning, processing artifact, fluid effect.
  Requires: well tie, AVO, rock physics, pressure evidence."  ← CORRECT
```

---

## Architecture

```
Arif (F13 SOVEREIGN)
  ↓
arifOS — identity, authority, routing, risk, approval, judge
  ↓
GEOX — Earth schemas, CRS/datum/units, provenance, uncertainty,
        subsurface objects, interpretation claims
  ↓
Workers — LAS, SEG-Y, OSDU, prospect, fault, horizon, well tie
  ↓
Vault999 — sealed decisions, hashes, audit
  ↓
Graphiti — semantic Earth memory, relationships
```

**Short version:**
- arifOS governs authority
- GEOX governs Earth truth
- Vault governs consequence
- Graphiti governs relationships
- Workers govern execution
- Arif governs final judgment

---

## 12 Success Criteria

GEOX may not claim victory until "the server runs." Success requires:

1. GEOX callable from intended MCP client (no Unknown tool)
2. GEOX contract stable and versioned
3. Auth works, wrong token rejected, right token accepted
4. GEOX schemas reject bad Earth claims
5. CRS/datum/unit validation works
6. Provenance validation works
7. Vault sealing works, tampering detected on readback
8. Agent memory cannot become Earth memory without validation
9. Interpretation claims include evidence, uncertainty, and alternatives
10. arifOS can HOLD or SEAL GEOX actions
11. Workers cannot bypass authority for high-impact actions
12. **End-to-end synthetic workflow passes**

### End-to-End Synthetic Milestone

```
synthetic SEG-Y metadata
+ synthetic well header
+ synthetic horizon
+ synthetic fault
+ synthetic provenance
→ GEOX validates
→ GEOX creates interpretation claim
→ GEOX challenges claim
→ GEOX registers uncertainty
→ arifOS judges risk
→ Vault seals approved synthetic result
→ readback verifies hash
```

---

## Five Development Horizons

### Horizon 1 — Fix callable GEOX
Remove tool routing contradiction. GEOX tools published = GEOX tools visible to client.

### Horizon 2 — Publish canonical contract
`/health`, `/tools`, `/contract`, `/schemas`, `/adapters`, `/vault/status`, `/crs/status`, `/units/status`, `/provenance/status`, `/ready`

### Horizon 3 — Enforce Earth schemas
Minimum schemas: earth_claim, measurement, dataset_manifest, well_header, well_log_curve, seismic_volume_metadata, horizon, fault, interpretation_claim, uncertainty, provenance, crs_datum, units

### Horizon 4 — Build metadata inspectors first
Inspect before ingest. Validate before memory. Seal before consequence.
Priority: LAS → SEG-Y → well header → deviation survey → tops table → surface → horizon/fault object

### Horizon 5 — Build the claim engine
`geox_claim_create`, `geox_evidence_attach`, `geox_claim_challenge`, `geox_alternative_model_register`, `geox_uncertainty_register`, `geox_claim_compare`, `geox_claim_seal`

### Horizon 6 — Build abductive geoscience agents
`GEOX.CRSAgent`, `GEOX.UnitAgent`, `GEOX.ProvenanceAgent`, `GEOX.LASAgent`, `GEOX.SEGYAgent`, `GEOX.WellTieAgent`, `GEOX.FaultAgent`, `GEOX.HorizonAgent`, `GEOX.ProspectRiskAgent`, `GEOX.AbductionAgent`, `GEOX.AttestationAgent`

All high-impact outcomes must pass through arifOS.

---

## Final Operating Command

> Forge GEOX as the governed Earth intelligence organ of arifOS.
>
> Do not build a map chatbot. Do not build a Petrel clone first.
> Do not let agent memory become Earth truth. Do not allow naked numbers.
> Do not allow unproven interpretations to become sealed claims.
>
> Build the canonical Earth contract. Build strict schemas.
> Build metadata inspectors. Build the interpretation claim engine.
> Build abductive challenge tools. Bind all high-impact actions to arifOS judgment.
> Seal consequences in Vault999. Store relationships in Graphiti.
>
> The goal is not faster hallucination. The goal is disciplined Earth intelligence.

**DITEMPA BUKAN DIBERI.**

---

*999 SEAL ALIVE — This doctrine is the true north for GEOX.*
