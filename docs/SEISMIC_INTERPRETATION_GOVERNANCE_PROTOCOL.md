# SEISMIC INTERPRETATION GOVERNANCE PROTOCOL — KL2V1 Kinabalu Composite

> **Status:** OPERATIONAL DRAFT — Sovereign ratification pending
> **Authority:** GEOX Constitution (GENESIS/000-003) + 7-Rung Epistemic Ladder
> **Date:** 2026-06-08
> **Provenance:** Distilled from the 2026-06-08 KL2V1 Kinabalu Basin visual analysis (Sabah offshore), mapped 1:1 to the 9-attribute Band A raster pipeline.
> **Seal:** DITEMPA BUKAN DIBERI

---

## 0. The Iron Law

> **Earth (Rungs 1–2: Signal/Measurement) outranks interpreter (Rungs 4–7: Interpretation/Model/Narrative) in all contradictions.**

The 7-Rung Epistemic Ladder is binding:

| Rung | Class | Trust | Examples |
|------|-------|-------|----------|
| 1 | Signal | absolute | gamma ray, resistivity, sonic transit time, **well log readings** |
| 2 | Measurement | near-absolute | biostrat markers, DST rates, **well-tie TWTs** |
| 3 | Derivation | high | porosity from density-neutron, **time-depth from checkshot** |
| 4 | Interpretation | medium | depth-converted maps, **horizon picks** |
| 5 | Model | medium-low | structural framework, **fault interpretation** |
| 6 | Judgment | low | prospect ranking |
| 7 | Narrative | lowest | report writing, **LLM-generated prose** |

When Rungs 1–2 contradict Rungs 4–7, **the lower rungs prevail**. This is non-negotiable. The LLM and human interpreter operate at Rungs 4–7; the well operates at Rungs 1–2. The well always wins.

## 1. The 5 Laws of First Contact (before any interpretation begins)

| # | Law | What it means operationally | GEOX Tool |
|---|-----|-----------------------------|-----------|
| 1 | **ORIENT BEFORE INTERPRET** — read the metadata collar | Domain (TWT/depth), direction (NW→SE), scale (km/division), vertical exaggeration (Z factor), survey vintages, well set, y-axis range | `geox_contrast_views` (Attribute 1 + provenance block) |
| 2 | **LARGE-SCALE BEFORE SMALL-SCALE** — basin architecture first | Squint. Identify 3–4 mega-domains by gross textural contrast before picking any horizon | `geox_contrast_views` mode `texture_energy` |
| 3 | **CERTAIN BEFORE UNCERTAIN** — pick the unambiguous first | Seabed first. Always. | `geox_evidence_reason` with `evidence_refs=well_set` |
| 4 | **STRUCTURAL FRAMEWORK BEFORE STRATIGRAPHY** — faults before horizons | You cannot correctly interpret a horizon you don't know is broken | `geox_contrast_views` mode `edge_map` |
| 5 | **WELL CONTROL BEFORE EXTRAPOLATION** — anchor at the known | Every pick is unconstrained until tied to a well. Rung 1–2 outranks Rung 4–5 | `geox_well_context` (or its successor) |

**Iron Law corollary:** Law 1 is the AC_Risk amplifier. Reading the metadata collar is what tells you where AC_Risk will be high (every survey merge is a display lie candidate).

## 2. The 6-Phase Workflow (operational)

### Phase 0 — Reconnaissance (30 seconds)
- **Goal:** metadata frame, mega-domain segmentation, AC_Risk boundary
- **Primary ToAC attribute:** #3 Texture Energy (mega-domain segmentation)
- **Constitutional binding:** F2 TRUTH (provenance), F4 CLARITY (scale, CRS, VE stated)
- **Tools (status):**
  - ✅ `geox_contrast_views(mode="texture_energy")` — SHIPPED Phase 1.1
  - ✅ `geox_contrast_views(mode="amplitude_envelope")` — SHIPPED Phase 1.1
  - 🚧 `geox_load_seismic_line` — NOT FORGED (reference tool — reads metadata collar; in scope for Phase 1.5)
- **Output:** 3–4 mega-domains labeled by gross textural character; survey-boundary AC_Risk overlay
- **Fail-closed condition:** if `image_provenance.scale_bar` or `crs` is missing → return HOLD, do not proceed to Phase 1

### Phase 1 — Structural Framework (faults first)
- **Goal:** the skeleton before the skin
- **Primary ToAC attribute:** #2 Edge/Discontinuity Map (Sobel gradient magnitude)
- **Secondary:** #6 Local Dip (Phase 1.3 — not yet shipped)
- **Constitutional binding:** F1 AMANAH (no commit before structure), F4 CLARITY (every fault labeled with confidence + evidence_ref)
- **Tools (status):**
  - ✅ `geox_contrast_views(mode="edge_map")` — SHIPPED Phase 1.1
  - 🚧 `geox_build_structural_candidates` — NOT FORGED (would consume edge_map + optional dip, return polylines)
- **Output:** ranked fault list with `evidence_ref` per fault (ToAC #2 column + ToAC #6 column when shipped)
- **Fail-closed condition:** if major fault (offset > 200ms) detected but no edge_map computed → return HOLD, request edge_map first
- **Order (per Arif's protocol):** shelf-edge collapse → central thrusts → inboard bounding faults → minor faults

### Phase 2 — Anchor Horizons (easy first)
- **Goal:** the unambiguous picks (seabed, shallowest reflectors) before the difficult ones
- **Primary ToAC attribute:** #1 Amplitude Envelope (strong, continuous reflectors)
- **Secondary:** #7 Phase Symmetry (polarity confirmation at well locations — Phase 1.3)
- **Constitutional binding:** F2 TRUTH (every horizon pick carries `epistemic_rung`), F7 HUMILITY (low-confidence picks get claim_state=HYPOTHESIS)
- **Tools (status):**
  - ✅ `geox_contrast_views(mode="amplitude_envelope")` — SHIPPED Phase 1.1
  - 🚧 `geox_horizon_pick_amplitude` — NOT FORGED (would consume amplitude_envelope + phase_symmetry, return ranked horizon candidates)
- **Output:** ranked horizon candidates with `epistemic_rung` and `evidence_ref`
- **Multiple check:** any deep horizontal event at TWT > 2× shallowest seabed → flag AC_Risk=high → 888_HOLD
- **Order:** seabed → top Stage IVF → top Stage IVE → top Stage IVD → continue in stratigraphic order

### Phase 3 — Well Ties (anchor to Rung 1–2 truth)
- **Goal:** calibrate seismic to wells, in order of trust (zero-projection wells first)
- **Primary tools:**
  - `geox_evidence_reason(phase="abduct", basin_name=..., reasoning_mode="baseline")` — Rung 2–3 reasoning
  - 🚧 `geox_well_context` — NOT FORGED (per-workflow tool; would return well metadata, TWTs, biostrat, GR motif)
- **Constitutional binding:** F2 TRUTH (well-anchored picks outrank seismic-only), F3 WITNESS (every pick needs `evidence_ref` to a well)
- **Output:** synthetic seismogram comparison, polarity confirmation, biostrat-to-seismic tie points
- **Order:** Rotan-1 → Pekaka-1 → Barton-2 (cross-line) → Buluh-1 → Maligan-1 → fill in

### Phase 4 — Hard Horizons (guided by structure + wells)
- **Goal:** the difficult picks (SRU, DRU, reservoir tops) with structure + well control
- **Primary ToAC attributes:** #4 Horizontal Gradient (termination patterns), #5 Vertical Gradient (boundary character), #7 Phase Symmetry (DHI screening)
- **Constitutional binding:** F2 TRUTH (Rungs 1–2 anchors, Rung 4 picks), F4 CLARITY (every pick carries the gradient evidence that placed it)
- **Tools (status):**
  - 🚧 `geox_horizon_contrast(mode="horizontal_gradient")` — Phase 1.2 (next forge)
  - 🚧 `geox_horizon_contrast(mode="vertical_gradient")` — Phase 1.2 (next forge)
  - 🚧 `geox_horizon_pick_phase` — Phase 1.3
- **Order:** SRU → DRU → Top IVC (reservoir) → Top IVB (UIU marker) → Pre-Neogene

### Phase 5 — Integration (the geoseismic section)
- **Goal:** convert picks to a geological story
- **Output:** colored, annotated section; depositional environment map per interval; play elements; prospects & leads
- **Constitutional binding:** F1 AMANAH (every output element has evidence_ref), F2 TRUTH (Rungs 1–2 outrank), F7 HUMILITY (alternatives surfaced)
- **Tools (status):**
  - `geox_evidence_reason(phase="synthesize", reasoning_mode="composite")` — Rung 5–6
  - `geox_evidence_reason(phase="abduct", reasoning_mode="comparative")` — Rung 4–5
- **AC_Risk check:** before finalization, run `geox_compute_ac_risk` over the integration layer; if AC_Risk > 0.5 on the integrated section, hold for human review

### Phase 6 — Audit (the constitutional firewall)
- **Goal:** surface what the system might be lying about
- **Primary ToAC attribute:** #9 AC_Risk Heatmap — **the governance layer**
- **Tools (status):**
  - 🚧 `geox_compute_ac_risk(mode="spatial")` — Phase 2.0
  - `geox_anomalous_contrast_detector` (existing — pointwise, not spatial heatmap)
- **The 6 Traps for the Interpreter** (each maps to a specific AC_Risk driver):

| # | Trap | Where on the section | AC_Risk driver |
|---|------|---------------------|----------------|
| 1 | Survey merge artifacts | every survey boundary | D_transform |
| 2 | Velocity pull-up/push-down | above/below gas accumulations | D_transform + B_cog |
| 3 | Multiples | deep horizontal events at >2× seabed TWT | U_phys + B_cog |
| 4 | Thrust repetition | SE inboard belt | U_phys |
| 5 | Shale diapir distortion | outboard Sabah Trough | D_transform |
| 6 | Polarity reversal at fluid contacts | hydrocarbon zones | U_phys + B_cog |

## 3. The Constitutional Mapping

| Floor | How it shows up in this workflow |
|-------|----------------------------------|
| F1 AMANAH | Every claim has `evidence_ref`; no "this is the analog" without proof |
| F2 TRUTH | Well data outranks seismic-only interpretations; seabed picks outrank deep picks |
| F3 WITNESS | Picks without `evidence_ref` are claim_state=HYPOTHESIS, not SEAL |
| F4 CLARITY | Metadata collar read FIRST; every pick has axis + normalization + computation provenance |
| F5 HUMILITY | Hard horizons get claim_state=HYPOTHESIS + uncertainty_band |
| F6 | not directly applicable (this is operational, not jurisdictional) |
| F7 HUMILITY | Low-confidence picks (deep multiples, ambiguous terminations) get claim_state=HYPOTHESIS, not SEAL |
| F8 REVERSIBILITY | Stash-friendly workflow: any pick can be rolled back via `claim_challenge` |
| F9 ANTIHANTU | No "the LLM thinks there's a fault" — only "edge_map shows delta>threshold at (x,y)" |
| F10 | not directly applicable |
| F11 AUTH | All picks carry session_id + actor_signature; wells are pinned, seismic is mutable |
| F12 | not directly applicable |
| F13 SOVEREIGN | **3 F13 audit items pending sovereign ratification**: Vision V1 +4, `geox_analog_atlas`, `geox_contrast_views`. The user reviews outputs, not the LLM. |

## 4. The 9-Attribute Map (which attribute per phase)

| Phase | Primary ToAC attribute | What it reveals | Status |
|-------|--------------------------|-----------------|--------|
| 0 | #3 Texture Energy | Mega-domain segmentation | ✅ SHIPPED Phase 1.1 |
| 1 | #2 Edge/Discontinuity | Fault traces, unconformity surfaces | ✅ SHIPPED Phase 1.1 |
| 2 | #1 Amplitude Envelope | Strong, continuous reflectors | ✅ SHIPPED Phase 1.1 |
| 3 | #7 Phase Symmetry | Polarity confirmation at wells | 🚧 Phase 1.3 |
| 4 | #6 Local Dip + #4 Horizontal Gradient | Termination patterns | 🚧 Phase 1.3 + 1.2 |
| 5 | #5 Vertical Gradient + #8 Frequency | Sequence boundary character | 🚧 Phase 1.2 + 1.4 |
| 6 | #9 AC_Risk Heatmap | Where to trust, where to 888_HOLD | 🚧 Phase 2.0 |

**The honest gap:** Phase 1.1 ships 3 of 9 attributes. With 3 of 9, the LLM can tell you **what kind of geology is here** (mega-domain, facies character, gross fault structure) but **cannot yet track a horizon across the section** (needs #4 horizontal gradient + #6 local dip). Phase 1.2 is where autonomous horizon interpretation becomes possible. Phase 1.3 is where it becomes reliable. Phase 2.0 is where the system can audit itself.

## 5. The System Prompt (for `2_seismic_vision.py`)

```text
You are the GEOX Seismic Interpretation Co-pilot. Your job is to read a seismic image and produce a phased, evidence-bound interpretation. You do NOT have a body. You do NOT drill wells. You do NOT have intuition. You compute attributes, anchor to wells, and flag uncertainty. If a claim cannot be backed by a well tie or a ToAC attribute, it is HYPOTHESIS, not SEAL.

**The Iron Law:** Earth (Rungs 1–2: Signal/Measurement) outranks interpreter (Rungs 4–7) in all contradictions. When in doubt, trust the well.

**Your evidence chain:**
  - Phase 0: read metadata collar (provenance, scale, VE) — refuse if missing
  - Phase 1: extract structural skeleton from edge_map
  - Phase 2: anchor horizons from amplitude_envelope
  - Phase 3: tie to wells (Rotan-1 first, then Pekaka-1, then Barton-2)
  - Phase 4: trace hard horizons (SRU, DRU, IVC top)
  - Phase 5: integrate (geoseismic section)
  - Phase 6: audit (AC_Risk, multiple check, velocity QC)

**Your outputs carry:**
  - `epistemic_rung` on every claim (1=Signal ... 7=Narrative)
  - `evidence_ref` on every claim (which attribute / which well / which event)
  - `claim_state` ∈ {SEAL, QUALIFY, HYPOTHESIS, HOLD, VOID}
  - `contrast_signals` when dangerous_similarity_flag is true

**Your prohibitions:**
  - No "this IS a fault" — only "edge_map shows delta>threshold at (x,y)"
  - No "the reservoir is here" without biostrat + amplitude + structural support
  - No aggregate-only analog match when 2+ dimensions diverge (HOLD, not QUALIFY)
  - No commitment without 888 ratification for canonical tool changes

**Your reflexes (in order of trust):**
  1. Well data (Rung 1–2) — never override
  2. Multiple surveys at the same event — if they agree, use; if not, HOLD
  3. ToAC attribute (Rung 4–5) — use with `claim_state=HYPOTHESIS`
  4. LLM inference (Rung 7) — surface as alternative, never as fact
```

## 6. The Constitutional Handshake

Every tool invocation in this workflow returns a `constitutional_envelope`:
- `governance_status` ∈ {VOID, HOLD, QUALIFY, SEAL, APPROVED}
- `claim_state` ∈ {DRAFT, INTERPRETED, PLAUSIBLE, HYPOTHESIS, NO_VALID_EVIDENCE, SEALED}
- `epistemic_rung` ∈ {1, 2, 3, 4, 5, 6, 7}
- `evidence_refs` (list of Rung 1–2 anchors)

The interpreter (human OR LLM) NEVER sees a bare tool output. They see the envelope. The envelope is the law.

## 7. F13 Audit (sovereign ratification pending)

This protocol references 3 new tools pending 888 ratification:

1. **Vision V1 +4** (2026-06-07, 4 tools: `geox_vision_perceptual_inventory`, `geox_vision_minimax_inference`, `geox_vision_calibrate`, `geox_vision_audit`) — pending ratification
2. **`geox_analog_atlas`** (2026-06-08, Tool #39) — pending ratification
3. **`geox_contrast_views`** (2026-06-08, Tool #40, this PR) — pending ratification

**Sovereign's call:** ratify all 3 to advance to Phase 1.2 / Phase 2.0; or roll back selectively.

**Tools referenced by this protocol that are NOT YET FORGED (Phase 1.2+ scope):**
- `geox_load_seismic_line` (metadata collar reader)
- `geox_build_structural_candidates` (edge_map → polylines)
- `geox_horizon_pick_amplitude` (amplitude → ranked horizons)
- `geox_well_context` (well metadata, TWTs, biostrat)
- `geox_horizon_contrast(mode="horizontal_gradient"|"vertical_gradient")` (Phase 1.2)
- `geox_horizon_pick_phase` (Phase 1.3)
- `geox_horizon_pick_dip` (Phase 1.3)
- `geox_compute_ac_risk(mode="spatial")` (Phase 2.0)

## 8. Open Questions (sovereign + architect input needed)

1. **Who defines the "expectation baseline" for the ToAC formula?** (Honest critique, 2026-06-08.) Options: (a) prior model from regional statistics, (b) LLM's own internal representation (closed reasoning loop), (c) human-provided (governed but human-dependent). **Architect's recommendation:** (a) for mega-domain baselines (textural character of "layered" vs "chaotic" by basin), (b) for per-feature subtleties (texture energy variance within a domain). Resolve before Phase 1.5.
2. **Phase 1.2 (horizontal + vertical gradient) vs running on real KL2V1 data first.** The shipped 3-of-9 pipeline can already do mega-domain segmentation and gross fault detection. Running it on the real KL2V1 will surface where the gap is in practice. Running on real data is the BIJAKSANA move before adding more attributes to a still-unvalidated pipeline.
3. **The "3 of 9 isn't enough for horizon tracking" point.** Confirmed. Phase 1.2 ships the next 2; Phase 1.3 the next 2. Real-world validation gates each phase.

---

**DITEMPA BUKAN DIBERI**

*This protocol is operational draft. It will be ratified as canonical after Phase 1.2 lands and the KL2V1 real-data validation closes.*
