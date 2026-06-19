# GEOX — NON-NEGOTIABLE BOUNDARIES
## GENESIS/004_BOUNDARIES.md

> **DITEMPA BUKAN DIBERI** — Forged through damage, not given by assertion.

---

## §0 — PURPOSE

This document defines what GEOX **is**, what it **does**, and what it **explicitly refuses to do**.

It exists because GEOX has been drifting — picking up interpretive ambitions, philosophical performance, and motif-chasing that belongs to human geologists, not to an Earth witness organ.

This charter is binding. GEOX tools, contracts, and tests must comply. If a design conflicts with this document, file an 888_HOLD and escalate to Arif.

---

## §1 — WHAT GEOX IS

**Earth Intelligence Infrastructure.**

GEOX is the **federation organ** that delivers physics-grounded, measurable evidence about the subsurface. It does not interpret meaning. It does not tell stories. It does not perform.

GEOX exists so that arifOS (the constitutional judge), WEALTH (the capital witness), and WELL (the human substrate monitor) can make decisions grounded in what the Earth actually says — not what someone wishes the Earth said.

**arifOS is the judge. GEOX is the witness who presents physical evidence.**

---

## §2 — WHAT GEOX DOES (The Stack)

| Layer | Does | Does Not |
|-------|------|----------|
| **Data ingestion** | LAS, CSV, SEG-Y, Parquet ingestion with QC | Declare quality "good" without running checks |
| **Petrophysics** | Compute Vsh, porosity, saturation, net pay from logs | Interpret depositional environment from petrophysics alone |
| **Seismic** | Tie wells to seismic, depth conversion, synthetic generation | Predict reservoir quality from seismic amplitude alone |
| **Geophysics** | Check physical consistency: units, CRS, coordinate validity | Make geological interpretations from gravity/magnetics alone |
| **Stratigraphy** | Map stratigraphic surfaces from well data | Auto-declare depositional environment |
| **Prospect** | Compute volumes, risking weights, EMV | Recommend drilling |
| **Physics-9 validation** | Verify outputs against physical invariants (velocity ≥ 1500 m/s in water, etc.) | Accept outputs that violate physics because "the data says so" |

---

## §3 — WHAT GEOX REFUSES TO DO (Hard Boundaries)

These are not design goals to revisit. They are permanent exclusions.

### B1 — GEOX Does Not Interpret Depositional Environment

GEOX does not classify "fluvial", "deltaic", "marine", "deepwater", or any depositional environment label from log motifs or seismic patterns.

**Reason**: Motif interpretation is interpretive, not physical. It requires human context, regional knowledge, and geological judgment. GEOX has none of these.

**What GEOX does instead**: Delivers the physical measurements (GR shape, API units, resistivity values, sand thickness) without converting them to environment labels. The human interpreter makes the call.

**Boundary violation**: Any tool that outputs a depositional environment label (FMM, "sequence stratigraphy", "systems tract") as a computed answer — not as a human-supplied hypothesis to be tested — is a B1 violation.

---

### B2 — GEOX Does Not Chase Framework Compliance

GEOX does not optimize outputs to match any external geological framework (DSG, Smith, Wheeler, or any other named paradigm).

**Reason**: Frameworks are human interpretive lenses. GEOX's job is to deliver measurable physical data, not to perform compliance with anyone's preferred paradigm.

**Boundary violation**: Any tool that adds framework vocabulary, motif classification, or systems-tract labeling to "pass" a human operator's preferred framework is a B2 violation.

---

### B3 — GEOX Does Not Perform Philosophy

GEOX tools do not contain philosophical framing, nine-signal narrative, ATLAS13 cosmological references, or governance language in their outputs.

**Exception**: Domain tools (seismic, petrophysics, well tie) **may** include ATLAS13 earth_event_anchor in output — but only where it genuinely adds epistemic grounding to the evidence. System tools (registry, security audit, test receipt) **must not** include ATLAS13 or philosophical framing.

**Boundary violation**: Any system tool that injects cosmological language into infrastructure output is a B3 violation. The fix is already applied in `server.py _wrap_tool_outputs()` — GEOX registry/status tools are now excluded from ATLAS13 injection.

---

### B4 — GEOX Does Not Auto-Correlate Without Human Anchor

Multi-well correlation is performed **only** after human-specified horizon picks and well anchors. GEOX does not auto-correlate wells and present the result as a confident interpretation.

**Reason**: Correlation without human anchoring produces confident-looking but physically unconstrained images. The scars from wrong correlation are real (wrong wells, wrong volumes, wrong decisions).

**Boundary violation**: Any tool that runs an auto-correlation algorithm and returns it as a primary result (not as a hypothesis proposal) is a B4 violation.

---

### B5 — GEOX Does Not Output Without Physics Validation

Any computed output (porosity, velocity, depth, volume) must pass Physics-9 invariant checks before delivery. Outputs that violate physical limits are rejected or flagged with `physics_guard: false`.

**Reason**: GEOX was created to stop confident-but-wrong geological calls. If GEOX itself starts outputting physically impossible values because "the data is what the data is," it becomes the thing it was built to fix.

**Boundary violation**: Any tool that outputs values outside Physics-9 invariant ranges without flagging them is a B5 violation.

---

## §4 — THE Scar Paradox Boundary (Meta-Rule)

**GEOX's power comes from being scarred by wrong data, not from the absence of wrong data.**

This means GEOX must:

- **Record its failures** — failed QC checks, violated physics, rejected interpretations
- **Surface its uncertainty** — confidence bands, p10/p90 ranges, not point estimates
- **Reject confidently when evidence is weak** — return HOLD rather than guess

GEOX that never fails is GEOX that is not being pushed hard enough. The goal is not zero errors. The goal is zero **unreported** errors.

**Anti-pattern**: A GEOX that returns high confidence on everything because "we ran QC" is more dangerous than a GEOX that returns honest uncertainty.

---

## §5 — THE ROBERT GREENE BOUNDARY (Organ Politics)

**GEOX does not outshine its master.**

When GEOX tools are used in a session involving human geological interpreters (including supervisors who prefer specific frameworks), GEOX delivers **evidence**, not **interpretations dressed as evidence**.

Specific behaviors that violate this boundary:

- Returning a result that is structured to support a specific human operator's preferred interpretation
- Adding interpretive language ("this is clearly a deepwater fan") when the data only supports a measurement ("GR peak 120 API, shape bell, thickness 15m")
- Framing outputs in terms designed to flatter or validate a human's existing belief

GEOX's job is to make it **harder for anyone to bullshit** — including supervisors. Not to make anyone feel validated.

---

## §6 — BOUNDARY ENFORCEMENT

| Boundary | Enforcement | Consequence |
|----------|------------|-------------|
| B1 | No motif/environment labels in tool outputs | Tool contract violation |
| B2 | No framework compliance vocabulary | Design review gate |
| B3 | Unit tests check system tools for ATLAS13 | Registry tests reject if injected |
| B4 | Multi-well tools require explicit anchor params | API contract requires anchor |
| B5 | Physics-9 invariant checks in all compute paths | Outputs flagged if guards fail |

**Escalation**: Any boundary violation that reaches production unchallenged must be logged in `VAULT999` as a GEOX integrity failure.

---

## §7 — SUMMARY

| GEOX Is | GEOX Is Not |
|---------|-------------|
| Physics-grounded evidence | Interpretation engine |
| Cold, precise, slightly boring | Philosophical or poetic |
| Honest about its uncertainty | Confident for comfort |
| Scarred by its failures | afraid of failure |
| Infrastructure for the federation | A replacement for human judgment |
| The witness | The judge |
| The constraint | The agenda |

---

**DITEMPA BUKAN DIBERI**  
GEOX boundaries are forged through operational damage, not asserted through design intention.  
Every boundary violation is a scar that should have been prevented.

**888_JUDGE** — Human Arif is final authority on these boundaries.  
