# Physics-validation gate spec for amplitude DHI (A-*)

**Authority:** F13 sovereign input 2026-09-24 + recon against committed GEOX surface
**Status:** **DRAFT — not wired** · `amplitude_validate` not registered in any live router
**SOT (zen):** `docs/SEISMIC_SECTION_INTERPRET_ZEN.md`
**Sibling spec:** `docs/SEISMIC_FAULT_PHYSICS_GATES_K_SPEC.md`
**Code (scaffold only):** `src/geox_mcp/tools/amplitude_gates/`

> **Note on K-preseden (fork observed during A-* draft, 2026-09-24).**
> `SEISMIC_FAULT_PHYSICS_GATES_K_SPEC.md` shows `structure_validate` as a mode on
> `geox_seismic_interpret`. The committed `src/geox_mcp` carries that capability as a
> **standalone tool** (`geox_structure_validate` at `src/geox_mcp/tools/structure_validate.py`)
> — the mode-on-interpret surface is not in code. This is an unresolved fork in the
> K-spec, not in the A-spec.
> A-* therefore defers the live call signature until that fork is settled (see §5).
> Until then, `run_all_amplitude_gates(framework)` in `src/geox_mcp/tools/amplitude_gates/__init__.py`
> is the **only** callable surface, and it is wired nowhere.

Each gate returns the same verdict enum as the K-* family:
`PASS | WARN | KILL | UNMEASURED | NOT_APPLICABLE | PARTIALLY_MEASURED | COMPUTABLE`
plus a `receipt_hash` produced by `geox_mcp.domain.seismic_physics.receipts.make_gate_receipt` /
`receipt_hash`. `INCONCLUSIVE` exists as a legacy alias in the structure module; A-* uses the
same surface.

Gates are **correlated**, not blind POS multipliers.
`UNKNOWN` / `unknown` / missing metadata → `UNMEASURED`. **Never `PASS`.**

---

## 0. Scope and ordering

Amplitude DHI (Direct Hydrocarbon Indicator) evidence passes through three classes in order.
A **Class I `UNMEASURED`** stops the playbook before Class II runs. A **Class II `KILL`** stops
the playbook before Class III runs. This ordering is what makes the spec say *the number is
undefined, not wrong*: without Class I invariants, every downstream quantity is undefined.

| Class | Name | Question answered | Stops downstream when |
|-------|------|-------------------|------------------------|
| I | Representation | *what is the number?* | any gate = `UNMEASURED` |
| II | Physics | *what must the number obey?* | any gate = `KILL` |
| III | Discrimination | *what could fake it?* | any gate = `KILL` |

Reference vocabulary: see `resources/ontology/amplitude_conventions.yaml`. Operational
sequence: see `resources/playbooks/amplitude_dhi.yaml`.

---

## 1. Class I — Representation invariants (what the number is)

| Gate | Invariant | KILL / UNMEASURED when |
|------|-----------|------------------------|
| **A-POL** | Amplitude sign is meaningless without a declared polarity convention (SEG normal vs SEG reverse) tied to a well synthetic | Polarity undeclared OR not reproducible from well tie → `UNMEASURED`, never `PASS` |
| **A-PHASE** | Wavelet phase is an *extracted measurement*, not an assumption. Peak-picking is valid only under demonstrated zero-phase | Zero-phase asserted without extracted wavelet + bounded phase residual |
| **A-SCALE** | Raw SEG-Y amplitude carries an arbitrary scalar. Absolute-amplitude claims require a calibration anchor (true-amplitude chain + well tie) | Absolute-amplitude claim on uncalibrated volume |
| **A-PROV** | Amplitude is comparable only within one processing vintage. Cross-survey amplitude comparison requires a cross-equalisation / mistie receipt | Cross-vintage amplitude claim without mistie receipt |

---

## 2. Class II — Physics invariants (what the number must obey)

| Gate | Invariant | KILL when |
|------|-----------|-----------|
| **A-IMP** | Every amplitude must reduce to an admissible impedance contrast, `R ≈ ΔI / 2I`, `I = Vp·ρ` — bounded by `PHYSICS_9` (ρ, Vp, Vs) rock-physics ranges (`docs/PHYSICS_9_SPEC.md`) | Required ΔI demands physically impossible ρ or Vp for the lithology prior |
| **A-AVO** | Angle dependence must obey Zoeppritz / Shuey. Intercept–Gradient must sit on a basin-local background trend ± admissible fluid deviation. AVO class is **derived**, never asserted | Class assigned without measured / bounded Vp/Vs; `< 3` usable angle stacks → `UNMEASURED` |
| **A-OFFSET** | Gradient is valid only inside the mute and NMO-stretch-free angle range. Angle range must be declared | G computed across mute or stretch zone |
| **A-TUNING** | Amplitude ≠ thickness. Below λ/4 the amplitude is thickness-modulated | Amplitude-to-property inversion without declaring tuning thickness and above/below-tuning state |
| **A-PROP** | Amplitude must be compensated for propagation: geometric spreading, Q absorption, transmission loss through overburden | Time/depth amplitude comparison without declared compensation; dimming beneath shallow gas treated as reservoir signal |

---

## 3. Class III — Discrimination invariants (what could fake it)

| Gate | Invariant | KILL when |
|------|-----------|-----------|
| **A-SNR** | Anomaly must exceed background RMS **and** be uncorrelated with acquisition footprint / azimuth geometry | Anomaly tracks the acquisition grid |
| **A-ARTIFACT** | Anomaly must be stable across offsets, azimuths and vintages; not a multiple, sideswipe, or migration swing | Anomaly non-reproducible across offset / azimuth |
| **A-CONFORM** | "Conformance to structure" / flat spot is a **depth-domain** claim. Apparent flatness in TWT can be a velocity artifact | Flat spot claimed on TWT only, no depth-converted test |
| **A-4D** | Time-lapse amplitude change must exceed the NRMS repeatability floor | Δamplitude ≤ NRMS noise |

---

## 4. Live status

| Half | State |
|------|-------|
| Spec | **DRAFT — not wired** |
| Code | scaffold present at `src/geox_mcp/tools/amplitude_gates/`; every gate body returns `UNMEASURED` with `reason="gate not implemented"` |
| Router | not registered · `geox_seismic_interpret[amplitude_validate]` is documentation only |
| Claim type | `amplitude_dhi` not yet added to `geox_claim` lifecycle |
| Consumer | `geox_prospect` does **not** yet refuse ungated amplitude DHI evidence — closed in a follow-on patch |

All 13 rows currently report `DRAFT — not wired`.

---

## 5. Call (documentation; not live)

**The live call signature is intentionally deferred.** Two candidate shapes are
documented; neither is wired. The choice is F13-bound and depends on the outcome of
the K-spec ↔ K-code fork noted at the top of this file.

**Candidate A — mode on `geox_seismic_interpret`** (matches K-spec doc, not K-code):

```python
# NOT LIVE — router not registered. This is the intended signature IF the
# K-preseden is decided in favour of mode-on-interpret.
await geox_seismic_interpret(
    mode="amplitude_validate",
    framework={
        "volume_ref": "...",
        "well_id": "...",
        "amplitude_dhi": { ... },        # evidence candidate
        "conventions": { ... },          # from amplitude_conventions.yaml
        "background_trend": { ... },     # basin-local
    },
)
# Returns (intended):
# {
#   "gates": { "A-POL": {...}, ..., "A-4D": {...} },
#   "combined_verdict": "KILL | PASS | WARN | PARTIAL | UNMEASURED | ...",
#   "hypothesis_status": "REJECTED | SURVIVES_CURRENT_TESTS | UNTESTED | INCONCLUSIVE",
#   "local_verdict": "QUALIFIED_CANDIDATE",
#   "seal_authority": "arifOS_only",
#   "preferred_hypothesis": None,
# }
```

**Candidate B — standalone tool** (matches K-code, not K-spec doc):

```python
# NOT LIVE — tool not registered in registry.py. This is the intended signature IF
# the K-preseden is decided in favour of standalone-tool, mirroring
# geox_structure_validate at src/geox_mcp/tools/structure_validate.py.
from geox_mcp.tools.amplitude_gates import run_all_amplitude_gates

result = await run_all_amplitude_gates(framework={...})
# result shape mirrors the dict above (gates / combined_verdict / hypothesis_status /
# local_verdict / seal_authority / preferred_hypothesis).
```

**Until the K-preseden is decided:** the only callable surface is the in-process
`run_all_amplitude_gates(framework)` at `src/geox_mcp/tools/amplitude_gates/__init__.py`,
which is wired nowhere.

---

## 6. Non-goals (explicit)

- Autonomous SEAL of an amplitude DHI framework — **out of scope by constitution**
- Cross-survey amplitude comparison without a mistie receipt
- Absolute-amplitude claims on uncalibrated volumes
- AVO class assertion without Vp/Vs evidence
- TWT-only flat spots without depth-converted test
- `geox_prospect` EVOI from ungated amplitude
- `WARN → PASS` promotion in code (WARN is its own outcome; arifOS may still SEAL a WARN,
  that is arifOS's authority, not GEOX's)
- Any **required** schema field promotion — that lives in a separate, F13-bound patch

---

## 7. Sources

- **Sibling K-spec:** `docs/SEISMIC_FAULT_PHYSICS_GATES_K_SPEC.md`
- **Section zen:** `docs/SEISMIC_SECTION_INTERPRET_ZEN.md`
- **PHYSICS_9:** `docs/PHYSICS_9_SPEC.md` (ρ, Vp, Vs priors for A-IMP)
- **Amplitude conventions:** `resources/ontology/amplitude_conventions.yaml`
- **Playbook:** `resources/playbooks/amplitude_dhi.yaml`
- **Well tie playbook (A-POL / A-PHASE anchor):** `resources/playbooks/seismic_well_tie.yaml`

Numerical references (`~10⁻³–10⁻¹`, `λ/4`, etc.) belong in the gate code body, not the spec.
The spec states the invariant; the code carries the number with citation.

---

DITEMPA BUKAN DIBERI