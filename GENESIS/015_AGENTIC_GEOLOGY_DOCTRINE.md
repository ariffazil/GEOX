# GENESIS/015 — Agentic Geology Doctrine

> **Human interpreters provide geological priors.**  
> **Agentic intelligence provides physical falsification.**  
> **Truth emerges only when both agree.**

---

## 1. The Inversion

Traditional interpretation places the burden on the geologist: prove the tie is *wrong*.  
GEOX inverts this: physics must prove the tie is *right*.

| Traditional (Petrel/DSG) | Agentic (GEOX) |
|---------------------------|-----------------|
| Geologist justifies what they *disbelieve* | Physics justifies what it *accepts* |
| "Looks okay" is admissible | "Looks okay" is a HOLD — needs a number |
| Ricker wavelet is default | Earth's actual wavelet is extracted |
| Tie quality is subjective | Mistie RMS is a falsifiable number |
| Interpretations accumulate | Receipts accumulate |
| Model = interpretation | Model = falsifiable hypothesis |

This is not a UI difference. It is a constitutional one. Petrel's architecture assumes
the interpreter is right until proven wrong. GEOX's architecture assumes the physics
is the gate — the interpreter supplies priors, but the physics renders the verdict.

---

## 2. The Human–Agent Contract

```
HUMAN  →  Geological priors, basin context, depositional intuition
AGENT  →  Physical falsification, mistie quantification, wavelet truth
JOINT  →  Governed subsurface truth — SEAL only when both converge
```

### What Humans Do (That Agents Cannot)

- Integrate basin history across millions of years
- Recognize depositional patterns from sparse data
- Apply analogs from other basins
- Feel when a tie "doesn't make geological sense" even if the numbers pass
- Understand the petroleum system as a story, not just a grid

### What Agents Do (That Humans Cannot)

- Compute mistie RMS to 0.1 ms precision, every time, without fatigue
- Extract the earth's actual wavelet via Wiener deconvolution — never assuming a Ricker
- Enforce velocity bounds, compaction models, and Voigt-Reuss-Hill rock physics
- Flag extrapolation risk when checkshots don't cover the full depth range
- Produce immutable receipts — the tie is auditable forever
- Never be fooled by seismic amplitude into seeing geology that isn't there

---

## 3. The Gate Architecture

Every well-tie passes through four constitutional gates:

| Gate | Tool | Threshold | Verdict |
|------|------|-----------|---------|
| **G1** | 25-Point Preflight | 25 checks | GO / HOLD / VOID |
| **G2** | Time-Depth Calibrate | 4 fitters + PhysicsGuard | TDFitResult + extrapolation_risk |
| **G3** | Mistie RMS | 25 ms | SEAL / HOLD / VOID |
| **G4** | Wavelet Extraction | condition_number ≤ 100, correlation ≥ 0.60 | SEAL / HOLD / VOID |

**G3 is the hard falsification gate.** 25 ms is not arbitrary — it represents the tuning
thickness limit below which seismic interpretation cannot resolve individual beds.
A mistie above 25 ms means horizon picks are unreliable for structural mapping.
The gate is binary. No negotiation. No "looks okay." No optimism.

---

## 4. Contrast — How Humans and Agents Differ

```
Humans tie wells visually.          Agents tie wells physically.
Humans optimize for plausibility.   Agents optimize for truth.
Humans tolerate ambiguity.          Agents enforce gates.
Humans produce interpretations.     Agents produce receipts.
Humans create narratives.           Agents create invariants.
Humans can be fooled by seismic.    Agents cannot be fooled by amplitude.
Humans see geology.                 Agents see physics.
```

**Both are needed.**

A human geologist integrates basin history, depositional systems, tectonics, analogs,
and petroleum system logic. An agentic intelligence enforces the physics that prevents
the geologist from lying to themselves. Together, they produce governed subsurface truth.

---

## 5. The Three Laws of Agentic Geology

### First Law — Physics Precedes Interpretation

> No geological claim may be made until the physics that supports it has been falsified.

A horizon is not a horizon until the tie proves it. An amplitude is not a hydrocarbon
indicator until the AVO Class is computed. A prospect is not a prospect until the
STOIIP Monte Carlo has run and the EMV receipt has been generated.

### Second Law — The Gate Is Binary, the Verdict Is Constitutional

> Every quantitative gate produces exactly one of three verdicts: SEAL, HOLD, VOID.
> There is no "maybe." There is no "looks okay." There is no "probably fine."
> SEAL means the number passes. HOLD means the number fails but can be fixed.
> VOID means the number is catastrophic and the line of inquiry is dead.

### Third Law — Every Decision Leaves a Receipt

> No well-tie, mistie, wavelet, or prospect evaluation may be used for downstream
> interpretation without an immutable receipt in the Evidence Governance System.
> The receipt carries the inputs, the computation, the verdict, the threshold,
> the actor, the timestamp, and the anti-hantu flags. What is not receipted
> does not exist for the purpose of constitutional judgment.

---

## 6. What GEOX Is Not

- **Not a Petrel replacement.** GEOX does not build 3D structural frameworks, does
  not render seismic volumes, does not provide a GUI for interpretation. It provides
  physics-grounded evidence for the interpreter to use.

- **Not a decision-maker.** GEOX computes, arifOS judges, Arif decides. GEOX's verdicts
  (SEAL/HOLD/VOID) are evidence gates, not capital allocation decisions.

- **Not a geologist.** GEOX has no intuition, no basin narrative, no depositional
  imagination. It will flag a mistie but it will not tell you *why* the mistie matters
  for the petroleum system. That is the human's domain.

- **Not sealed until Arif seals.** GEOX produces DRAFT_ONLY receipts. Only arifOS
  888_JUDGE, with sovereign authority, can seal a receipt to VAULT999.

---

## 7. The Moat vs Petrel

Petrel's architecture assumes the interpreter is sovereign. The software is a tool —
it does whatever the geologist tells it, including building 3D models on pure speculation
without flagging the epistemic gap.

GEOX's architecture is constitutional. The physics is the gate. The interpreter
supplies priors, but the tool renders verdicts. The interpreter cannot proceed to
3D modeling until the 1D well-tie has been falsified and the mistie receipt has
been SEALed.

```
Petrel:     Interpreter → Tool → Model  (no gate)
GEOX:       Interpreter → Physics → Gate → Receipt → Model  (constitutional)
```

This is the moat. Not better algorithms. Not more data. Constitutional architecture
that prevents the user from building castles on sand.

---

## 8. Alignment with Constitutional Floors

| Floor | Obligation |
|-------|-----------|
| **F2 TRUTH** | Every claim anchored to a falsifiable number. Mistie RMS, not "looks okay." |
| **F3 WITNESS** | Every receipt witnessed by physics (AI channel), human (interpreter channel), and external (data channel). |
| **F7 HUMILITY** | Confidence capped at 0.90. GEOX never claims certainty where physics is underdetermined. |
| **F9 ANTI-HANTU** | No "I think the tie looks good." No hallunicated geology. No soul claims. |
| **F11 AUDIT** | Every gate computation logged. Every receipt attributable. Every verdict inspectable. |
| **F13 SOVEREIGN** | GEOX drafts receipts. arifOS judges. Arif seals. The human holds final veto. |

---

## 9. Build Order (from GENESIS/014)

```
P0  1D LAS physics — φ, Vsh, AI, RC from curves              ✅ DONE
P0  Well-tie spine — preflight → synthetic → mistie receipt  ✅ DONE
P1  Probabilistic STOIIP/EMV (lognormal MC) → WEALTH bridge  ✅ DONE
P2  Spatial ToAC — prospect-local contrast detection          NEXT
P3  3D corner-point / property upscale                        DEFERRED
P4  Darcy migration path receipts                             DEFERRED
```

---

## 10. Paradox, four moats, prompt standard, EarthOS

See **GENESIS/016_CONSTITUTIONAL_PROMPT_STANDARD.md** for:

- The paradox: enforce physics without killing geology  
- Moats: Physics invariants · EGS `geox://` · Falsification gates · Constitutional prompts  
- **Mandatory prompt block** agents must use before GEOX MCP chains  
- Loadable YAML: `prompts/GEOX_CONSTITUTIONAL_PROMPT_BLOCK.yaml`

See **GENESIS/017_EARTHOS_CONSTITUTION.md** for the compressed EarthOS charter:

- Articles I–X (physics → sovereign seal)  
- LIVE / PARTIAL / ABSENT gap matrix  
- 777_FORGE build order (multi-well coherence before basin matrix)  
- 999_SEAL receipt fields (always DRAFT_ONLY from GEOX)

One-line: *Humans interpret; GEOX governs; arifOS seals.*

---

*GENESIS 015 · 2026-07-09 · Forged from Marmousi2 ground truth*  
*Pairs: GENESIS/014 (Petrel Delta), GENESIS/016 (Prompt Standard), GENESIS/017 (EarthOS), GENESIS/000 (Manifesto)*  
*DITEMPA BUKAN DIBERI — The gate is physics. The verdict is constitutional.*
