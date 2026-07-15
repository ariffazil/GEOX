# GENESIS/016 — GEOX Constitutional Prompt Standard

> **Authority:** Doctrine for all agents calling GEOX MCP (1D Orthogonal Base and beyond)  
> **Pairs with:** GENESIS/010 AEI · 012 GEOX-001 · 013 Metabolic Surface · 015 Agentic Geology · **017 EarthOS Constitution**  
> **Status:** LIVE doctrine · DRAFT_ONLY for VAULT999 until F13 seals  
> **One line:** *Earth physics first, geology second, rendering last.*  
> **Note:** The four operational moats below are a **subset** of GENESIS/017 Articles I–X — not a competing constitution.

---

## 0. One-line synthesis (locked)

| | |
|--|--|
| **Contrast** | Humans interpret; GEOX governs physics. |
| **Paradox** | GEOX must enforce physics without killing geology. |
| **Moat** | GEOX is the only MCP earth-model that **falsifies**. |

```text
GEOX does physics.
Humans do geology.
AAA hosts both.
arifOS seals truth.
```

---

## 1. The contrast (invariants)

| Humans | GEOX agents |
|--------|-------------|
| See geology, context, depositional plausibility | Enforce Vp bounds, drift, curvature, gradient |
| Slide synthetics until they “look right” | Quantify RMS mistie in absolute ms |
| Accept ambiguity | Hard gates: SEAL / HOLD / VOID @ 25 ms |
| Produce interpretations | Extract real wavelets (Wiener, stabilized) |
| Bias toward optimism | Produce receipts, not opinions |
| Inconsistent across interpreters | Perfectly reproducible |

Humans optimize for **plausibility**.  
Agents optimize for **truth**.

Both are required. Neither alone is sufficient.

---

## 2. The paradox (resolved by separation of custody)

> Earth physics is objective, but geology is interpretive.  
> GEOX must enforce physics without destroying geology.

| Failure mode | Result |
|--------------|--------|
| Too strict | Rejects legitimate geological complexity → false VOID |
| Too lenient | Petrel-theatre — beautiful lies → false SEAL |

**Resolution:** separate **physics custody** from **geological interpretation**.

| Plane | Owner | Output |
|-------|--------|--------|
| Physics | GEOX | Numbers, gates, receipts (`geox://…`) |
| Geology | Human | Priors, narrative, petroleum system story |
| Host | AAA | Surfaces both without collapsing either |
| Seal | arifOS + F13 | VAULT999 only after sovereign path |

Architecture that implements the paradox:

- **PhysicsGuard** — bounds_ok, drift_ok, gradient_ok, curvature_ok  
- **Mistie Gate** — 25 ms → SEAL / HOLD / VOID  
- **Wavelet extraction** — real earth wavelet, not assumed Ricker  
- **EGS receipts** — truth stored, not only rendered  
- **vault999_status = DRAFT_ONLY** — GEOX cannot seal truth alone  

---

## 3. The four moats (defend absolutely)

### Moat 1 — Physics invariants (non-negotiable)

| Invariant | Enforced by |
|-----------|-------------|
| Vp bounds (CANON-9) | PhysicsGuard / welltie / LAS physics |
| Gradient monotonicity | T-D fitters |
| Curvature sanity | T-D / velocity policy |
| Extrapolation risk | TDFitResult.extrapolation_risk |
| Fail-closed | fit_td, mistie VOID on bad input |
| Absolute RMS mistie (ms) | `geox_well_seismic_mistie_rms` |
| Per-interval mistie | mistie_engine intervals |
| Real wavelet (not assumed Ricker) | `geox_wavelet_extract_least_squares` |
| Condition number stability | wavelet PhysicsGuard |
| Phase class tagging | wavelet result.phase_class |

**If an agent bypasses these, it is not GEOX — it is a calculator wearing a badge.**

### Moat 2 — EGS resource custody (`geox://`)

Every computation → receipt → URI → immutable (filesystem EGS lite; VAULT999 after seal):

```text
geox://well/{id}/tdfit/{…}
geox://well/{id}/mistie/{…}
geox://well/{id}/wavelet/{…}
```

Prevents: silent UI failure, transient lies, ungoverned rendering, hallucinated geology.

### Moat 3 — Falsification gates (SEAL / HOLD / VOID)

| Verdict | Meaning |
|---------|---------|
| **SEAL** | Physics agrees (advisory; not VAULT999) |
| **HOLD** | Physics uncertain / fixable |
| **VOID** | Physics rejects / catastrophic input or threshold |

Most earth-models never VOID a tie. GEOX must.

### Moat 4 — Constitutional prompts

Every agent prompt that touches GEOX **must** carry the block in §4.  
Skipping it is an F4 entropy violation and an F2 truth risk.

---

## 4. Constitutional Prompt Block (mandatory template)

Agents **paste and fill** this block before any GEOX 1D / well-tie / mistie / wavelet / benchmark call chain.

```yaml
# ── GEOX CONSTITUTIONAL PROMPT BLOCK ─────────────────────────────────
# Doctrine: GENESIS/016 · Order: physics → geology → rendering

intent: "<one sentence: what is being falsified, not what is being sold>"

epistemic:
  OBS: []          # measured files / traces / checkshots present
  DER: []          # computed φ, AI, RC, T-D, mistie, wavelet
  INT: []          # horizon = reservoir, geological meaning
  SPEC: []         # velocity assumptions, trap geometry if no grid
  HYPOTHESIS: []   # untested claims
  forbidden:       # never promote without receipt
    - "horizon is true without mistie SEAL-grade advisory"
    - "amplitude is hydrocarbon"
    - "impedance is lithology"

physics_bounds:
  vp_ms: [1500, 6000]           # CANON-9 default; declare if overridden
  density_gcc: [1.0, 3.0]
  compaction_model: "<linear|vo_k|layer_cake|none>"
  wavelet_class: "<assumed_ricker|extracted_wiener|unknown>"
  method_td: "<linear|polynomial|vo_k|layer_cake>"

falsification_gates:
  rms_threshold_ms: 25.0
  mistie_verdict_map: "SEAL|HOLD|VOID"
  physics_guard_required: true
  fail_closed: true
  on_rms_gt_threshold: "HOLD or VOID — never proceed to 3D/claim SEAL"

governance:
  vault999_status: DRAFT_ONLY
  seal_allowed: false            # only arifOS + F13
  actor: "<agent_id>"
  receipt_uris: []               # fill after each tool: geox://well/...
  tools_allowed_before_base:     # Orthogonal Base only until custody
    - geox_well_ingest
    - geox_well_qc
    - geox_well_time_depth_calibrate
    - geox_well_seismic_mistie_rms
    - geox_wavelet_extract_least_squares
    - geox_tie_preflight
    - geox_tie_receipt
    - geox_benchmark_001
  tools_blocked_until_base_pass:
    - geox_vision
    - geox_simulate_*
    - geox_3d_model*
    - geox_map_*
    - geox_prospect mode=seal

order_of_operations:
  1: Orthogonal Base (ingest → QC → T-D → synthetic/mistie → wavelet)
  2: Law plane (claim challenge, contrast, benchmark verdict)
  3: Geology narrative (human or explicit INT labels)
  4: Rendering (charts/maps last)

anti_hantu:
  - "Do not want the tie to work"
  - "Same LAS + seismic must reproduce same receipt"
  - "GEOX does not seal VAULT999"

output_contract:
  - every number has OBS|DER|INT|SPEC
  - every gate has SEAL|HOLD|VOID
  - every result has resource_uri or explicit MISSING_RECEIPT
  - confidence_cap: 0.90
# ─────────────────────────────────────────────────────────────────────
```

### Minimal one-liner agents may use when token-poor

```text
GEOX-016: Physics first, geology second, render last.
Epistemic labels mandatory. 25 ms mistie gate. fail_closed.
vault999=DRAFT_ONLY. Receipt geox:// or declare MISSING_RECEIPT.
No 3D/vision/simulate until Orthogonal Base passes.
```

---

## 5. Prompt anti-patterns (entropy / moat violations)

| Forbidden | Why |
|-----------|-----|
| “Make the well-tie look good” | Bias → F9 / destroys Moat 3 |
| “Assume Ricker without extraction when data allows Phase 4” | Skips Moat 1 |
| “Skip mistie; go straight to prospect” | Breaks Orthogonal Base (013) |
| “Seal this to VAULT999 from GEOX alone” | F13 violation |
| Unlabeled numbers | F2 / F7 |
| Stringified JSON payloads at MCP boundary | A-FORGE hardening / F4 |
| Basin depocenter thickness scoring all blocks equally | Spatial ToAC debt (P2) |

---

## 6. Moat contrast (what others copy vs cannot)

| Typical MCP earth tools | GEOX |
|-------------------------|------|
| Render, visualize, calculate, summarize, interpret | **Falsify**, enforce physics, store receipts, reject lies |
| No VOID | SEAL / HOLD / **VOID** |
| Transient UI state | `geox://` + EGS custody |
| Soft “quality” | Absolute RMS ms + PhysicsGuard |
| Self-certifying models | DRAFT_ONLY until arifOS/F13 |

---

## 7. Implementation map (live tools)

| Gate | MCP tool | Receipt URI pattern |
|------|----------|---------------------|
| T-D + PhysicsGuard | `geox_well_time_depth_calibrate` | `geox://well/{id}/tdfit/…` |
| Mistie 25 ms | `geox_well_seismic_mistie_rms` | `geox://well/{id}/mistie/…` |
| Wiener wavelet | `geox_wavelet_extract_least_squares` | `geox://well/{id}/wavelet/…` |
| Full wedge | `geox_benchmark_001` | killer receipt + orthogonal_base |
| Models | `geox_core/schemas/geox_1d_mcp.py` | TDFit / Mistie / Wavelet MCP |

---

## 8. Agent compliance checklist

Before any GEOX chain ships to Arif:

- [ ] Constitutional block filled (§4) or one-liner acknowledged  
- [ ] OBS/DER/INT/SPEC on every material claim  
- [ ] Orthogonal Base completed before cognitive/dimensional tools  
- [ ] Mistie threshold declared (default 25 ms)  
- [ ] At least one `geox://` URI **or** explicit `MISSING_RECEIPT`  
- [ ] `vault999_status: DRAFT_ONLY` unless F13 sealed  
- [ ] No amplitude→hydrocarbon leap  

---

*GENESIS 016 · 2026-07-09*  
*The paradox: enforce physics without killing geology.*  
*The moat: falsification under custody.*  
*EarthOS charter: GENESIS/017_EARTHOS_CONSTITUTION.md*  
*DITEMPA BUKAN DIBERI*
