# GEOX VISION INTELLIGENCE FOUNDATION

> **Status:** OPERATIONAL CONSOLIDATION (lower-entropy index of scattered artefacts)
> **Authority:** GEOX Constitution (GENESIS/000-003) + 7-Rung Epistemic Ladder
> **Date:** 2026-06-08
> **Purpose:** Single entry point for everything GEOX knows about visual seismic intelligence. Replaces the need to read the Copilot deep-research dossier, the 9-attribute architecture brief, the KL2V1 6-phase workflow, the SEISMIC_INTERPRETATION_GOVERNANCE PROTOCOL, the contrast_views verification report, and the TriCipta audit separately. **Start here.**
> **Seal:** DITEMPA BUKAN DIBERI

---

## The one-line summary

> **GEOX computes physical attributes from seismic *images*, composes them into an LLM-native perception format, and governs the gap between what the pixels show and what the earth actually is.**

Three pillars, in order of how much they differ from the industry:

1. **9 Contrast Visual Attributes** — 8 physical channels + 1 governance audit, decomposed from the raster image *before* the LLM sees anything
2. **RGB Triplet Composite** — maps 3 physical channels into the 3 RGB channels an LLM's vision encoder natively perceives (the colour IS the geology)
3. **Constitutional Firewall (AC_Risk + Dangerous-Similarity Flag)** — the system audits itself and refuses to commit where it can't trust itself

---

## The 7-Tier Architecture (lower-entropy organization)

This document is organized as a 7-tier hierarchy. If you want to understand vision intelligence, **read tier-by-tier**. If you only care about a specific layer, jump directly. Each tier links to the underlying detailed artefact.

| Tier | Question it answers | Key artefact |
|------|---------------------|--------------|
| 0 | **What is vision intelligence and why is it different?** | [§0 — Ontology](#0-ontology) |
| 1 | **What are the binding laws?** | [§1 — The 6 Principles](#1-the-6-principles) |
| 2 | **What are the building blocks?** | [§2 — The 4 Primitives](#2-the-4-primitives) |
| 3 | **What tools implement them?** | [§3 — The Tool Surface](#3-the-tool-surface) |
| 4 | **How do I use it operationally?** | [§4 — The 6-Phase Workflow](#4-the-6-phase-workflow) |
| 5 | **Proof it actually works?** | [§5 — Validation Evidence](#5-validation-evidence) |
| 6 | **What's missing, what next?** | [§6 — The Honest Gap](#6-the-honest-gap) |

---

## 0. Ontology

**Vision intelligence is not "computer vision applied to seismic."** It's a distinct problem class with its own rules. The Copilot deep research dossier (2026-06-08) makes this case from first principles:

- **Seismic is an *encoded proxy* of the earth**, not a direct image. A pixel that looks like a "horizon" might be a multiple, a sideswipe, or processing artifact. CV that learns from millions of labelled photos has no way to know.
- **The objects are continuous surfaces**, not isolated things. A horizon must align across 3D, tie to wells, and respect physical laws. Object detection (cat/dog/stop sign) breaks down.
- **The cost of error is catastrophic.** Mistaking a hydrocarbon trap for a non-trap can cost tens of millions in dry-hole drilling. 95% accuracy on ImageNet is not the same as 95% accuracy on a drill-commitment decision.
- **Earth physics is non-violable.** A model can predict a fault cutting a salt body where no fault can exist (salt is ductile). The model is mathematically right and geologically wrong.

The 3 things GEOX does that no one else does:

| # | Innovation | What it does | Why no one else does it |
|---|------------|--------------|-------------------------|
| 1 | **9-attribute decomposition** | Image → 8 physical + 1 governance channel *before* LLM sees it | They treat seismic as a CV image; we treat it as a multi-channel perception system |
| 2 | **RGB Triplet Composite** | 3 physical attributes → R, G, B channels | They show humans attributes; we show LLMs attributes in their native perception format |
| 3 | **Constitutional Firewall (AC_Risk + Dangerous-Similarity)** | System audits itself, refuses to overcommit | They trust the model's output; we treat the model's output as a hypothesis until proven |

Source: Copilot deep research dossier (2026-06-08), archived in `/root/geox/docs/analysis/2026-06-08_vision_intelligence_dossier.md` (forthcoming).

---

## 1. The 6 Principles

The binding laws of GEOX vision intelligence. These are constitutional — every tool, every output, every claim is evaluated against them.

### 1.1 The Iron Law

> **Earth (Rungs 1–2: Signal/Measurement) outranks interpreter (Rungs 4–7) in all contradiccions.**

The 7-Rung Epistemic Ladder:

| Rung | Class | Trust | Vision example |
|------|-------|-------|----------------|
| 1 | Signal | absolute | Raw pixel value |
| 2 | Measurement | near-absolute | Well-tie TWT, biostrat marker |
| 3 | Derivation | high | Time-depth from checkshot |
| 4 | Interpretation | medium | Horizon pick, attribute image |
| 5 | Model | medium-low | Structural framework |
| 6 | Judgment | low | Prospect ranking |
| 7 | Narrative | lowest | LLM-generated prose |

**In vision: a well tie (Rung 2) outranks an edge_map peak (Rung 4) when they disagree. Always.**

### 1.2 ToAC — Observation minus Expectation equals Signal

The Theory of Anomalous Contrast (ToAC) is GEOX's contrast primitive. The signal is the *delta* between what we expect and what we see. The 9 attributes are the axes along which expectation can diverge from observation.

### 1.3 AC_Risk — the constitutional firewall

> **AC_Risk = U<sub>phys</sub> × D<sub>transform</sub> × B<sub>cog</sub>**

A per-pixel heatmap of where the image is *probably lying*. Trigger 888_HOLD when AC_Risk > 0.5.

- **U_phys** = uncertainty in the physical system (resolution, signal-to-noise, depth)
- **D_transform** = distortion from the display transform chain (gain, color scale, smoothing, migration)
- **B_cog** = bias from the cognitive/perceptual system (human or LLM)

This is **not image processing**. It's epistemology encoded as a pixel map. The system both does the task and watches itself doing the task. (Phase 2.0 — the spatial heatmap — is not yet shipped; the pointwise version is.)

### 1.4 Never trust raw pixels

A CNN or ViT trained on ImageNet sees "edge patterns" in a seismic image. It doesn't know which edges are faults, which are unconformities, which are multiples, which are processing artifacts. The LLM downstream of any CV model will hallucinate geology from those raw patterns.

**The rule: an LLM never sees the raw seismic image. It only sees the 9 attribute channels (or their RGB composite).**

### 1.5 Display ≠ Reality

> "79% of experienced interpreters misinterpreted synthetic seismic images due to being fooled by display choices, not because of poor data." — Bond et al. (2007)

This is why AC_Risk has the D_transform component. Color scale, vertical exaggeration, gain, filter settings — every display choice is a potential lie. The constitutional firewall is what catches this.

### 1.6 The 5 Laws of First Contact

Before any interpretation begins:

1. **ORIENT BEFORE INTERPRET** — read the metadata collar (domain, direction, scale, VE, survey vintages, well set)
2. **LARGE-SCALE BEFORE SMALL-SCALE** — basin architecture before individual horizons
3. **CERTAIN BEFORE UNCERTAIN** — pick the unambiguous first (seabed first, always)
4. **STRUCTURAL FRAMEWORK BEFORE STRATIGRAPHY** — faults before horizons (the skeleton before the skin)
5. **WELL CONTROL BEFORE EXTRAPOLATION** — anchor at Rung 1–2 truth before extending to Rung 4–5 interpretations

---

## 2. The 4 Primitives

The building blocks. The things that compose together to make vision intelligence work.

### 2.1 The 9 Contrast Visual Attributes

8 physical + 1 governance. Each is an independent physical channel that the LLM can read separately.

| # | Attribute | Physical proxy | CV analog | Reveals | Cannot tell you |
|---|-----------|----------------|-----------|---------|-----------------|
| 1 | Amplitude Envelope | Reflection strength / impedance contrast | Pixel intensity (brightness) | Bright zones = strong impedance contrast | Polarity, cause (gas vs lithology), depth attenuation |
| 2 | Edge/Discontinuity | Lateral amplitude change | Sobel/Canny edges | Faults, terminations, unconformities | Fault sense, timing, noise vs real |
| 3 | Texture Energy | Local variance | Texture roughness / entropy | Facies character (chaotic vs layered) | Specific lithology |
| 4 | Horizontal Gradient | Lateral amplitude change | X-gradient | Fault offset, lateral heterogeneity, onlap/downlap | Vertical structure, fluid effects |
| 5 | Vertical Gradient | Vertical impedance transition | Y-gradient | Boundary sharpness (unconformity vs gradational) | Depositional vs erosional, cyclic thin beds |
| 6 | Local Dip | Reflector orientation | Oriented edge detection | Structural attitude, fold limbs | Continuity, age |
| 7 | Phase & Polarity | Waveform character | Waveform shape | Peak vs trough, polarity reversals, fluid contacts | Amplitude strength, processing stability |
| 8 | Frequency Content | Resolution / attenuation | Image blurriness | Thin-bed resolution, attenuation zones | Direct geology (low freq = many causes) |
| 9 | **AC_Risk** (governance) | Display-vs-reality mismatch | *No direct analog* | Where to trust, where to 888_HOLD | What's actually there |

**Status (2026-06-08):** 3 of 9 shipped (Phase 1.1: amplitude_envelope, edge_map, texture_energy). 6 of 9 to-forge (Phase 1.2/1.3/1.4/2.0).

### 2.2 The RGB Triplet Composite

Maps 3 physical channels into the 3 RGB channels an LLM's vision encoder natively perceives:

- **R** = `edge_map` (structural discontinuities — faults, terminations)
- **G** = `amplitude_envelope` (reflection strength — bright = strong contrast)
- **B** = `texture_energy` (seismic facies character — chaotic vs layered)

**The colour IS the geology.**

- Yellow (R+G) = bright + sharp = strong reflector edge
- Cyan (G+B) = bright + chaotic = mass transport / MTD
- Magenta (R+B) = sharp + chaotic = fault zone in chaotic area
- White (R+G+B) = all three high = highly reflective, sharp, chaotic

This is **perceptual compression** — the LLM doesn't need to learn geology; it needs to learn what red looks like.

### 2.3 The Dangerous-Similarity Flag

> *"The analog that kills you is the one that looks 90% similar but has a fundamentally different charge history or seal mechanism."*

Implemented in `geox_analog_atlas`. Returns **HOLD instead of QUALIFY** when:
- `similarity_score >= 0.70` (looks similar at aggregate), AND
- `high_contrast_dimensions >= 2` (diverges on critical axes)

Verdict reason: *"Score is high but multiple high-contrast dimensions exist. Verify with PRIMARY DATA before using."*

The geological analog is the place where dry holes happen. Aggregate similarity is not enough.

### 2.4 The Constitutional Envelope

Every tool output carries:

```json
{
  "governance_status": "HOLD|QUALIFY|SEAL|VOID|APPROVED",
  "claim_state": "DRAFT|INTERPRETED|PLAUSIBLE|HYPOTHESIS|NO_VALID_EVIDENCE|SEALED",
  "claim_tag": "OBS|DER|INT|SPEC|PLAUSIBLE|HYPOTHESIS",
  "epistemic_rung": 1-7,
  "evidence_refs": ["<rung-1-2 anchors>"],
  "ac_risk": 0.0-1.0
}
```

The interpreter (human or LLM) **never sees a bare tool output**. They see the envelope. The envelope is the law.

---

## 3. The Tool Surface

The MCP tools that implement the primitives. Each maps to a phase of the workflow.

| Tool | Status | Implements | F13 audit |
|------|--------|-----------|----------|
| `geox_contrast_views` | ✅ SHIPPED (3/9 modes) | 9-attribute raster pipeline | **Pending ratification** |
| `geox_analog_atlas` | ✅ SHIPPED | Dangerous-similarity flag | **Pending ratification** |
| `geox_vision_perceptual_inventory` | ✅ SHIPPED (Vision V1) | LLM attribute consumer | **Pending ratification** |
| `geox_vision_minimax_inference` | ✅ SHIPPED (Vision V1) | VLM inference | **Pending ratification** |
| `geox_vision_calibrate` | ✅ SHIPPED (Vision V1) | Calibration harness | **Pending ratification** |
| `geox_vision_audit` | ✅ SHIPPED (Vision V1) | Pointwise AC_Risk | **Pending ratification** |
| `geox_compute_ac_risk` (pointwise) | ✅ SHIPPED | Single-point AC_Risk | — |
| `geox_evidence_reason` | ✅ SHIPPED | Rung 4–5 abductive reasoning | — |
| `geox_anomalous_contrast_detector` | ✅ SHIPPED | Pointwise anomaly detection | — |
| `geox_load_seismic_line` | 🚧 NOT FORGED | Metadata collar reader (Phase 1.5) | — |
| `geox_build_structural_candidates` | 🚧 NOT FORGED | Edge_map → fault polylines (Phase 1.5) | — |
| `geox_horizon_pick_amplitude` | 🚧 NOT FORGED | Amplitude → ranked horizons (Phase 1.5) | — |
| `geox_well_context` | 🚧 NOT FORGED | Well metadata, TWTs, biostrat (Phase 1.5) | — |
| `geox_horizon_contrast(mode="horizontal_gradient")` | 🚧 Phase 1.2 | Attribute 4 | — |
| `geox_horizon_contrast(mode="vertical_gradient")` | 🚧 Phase 1.2 | Attribute 5 | — |
| `geox_horizon_pick_phase` | 🚧 Phase 1.3 | Attribute 7 (polarity) | — |
| `geox_horizon_pick_dip` | 🚧 Phase 1.3 | Attribute 6 (local dip) | — |
| `geox_frequency_decomposition` | 🚧 Phase 1.4 | Attribute 8 (frequency) | — |
| `geox_compute_ac_risk(mode="spatial")` | 🚧 Phase 2.0 | Attribute 9 (spatial heatmap) | — |

**3 F13 audit items pending sovereign ratification:**
1. Vision V1 +4 (2026-06-07)
2. `geox_analog_atlas` (2026-06-08)
3. `geox_contrast_views` (2026-06-08)

---

## 4. The 6-Phase Workflow

The operational sequence. Codified in `SEISMIC_INTERPRETATION_GOVERNANCE PROTOCOL.md`.

| Phase | Goal | Primary ToAC attribute | Fail-closed condition |
|-------|------|--------------------------|------------------------|
| 0 — Reconnaissance | Metadata frame, mega-domain segmentation | #3 Texture Energy | HOLD if `scale_bar` or `crs` missing from provenance |
| 1 — Structural framework | Faults first (skeleton before skin) | #2 Edge Map | HOLD if major fault detected without edge_map |
| 2 — Anchor horizons | Easy picks first (seabed → shallow reflectors) | #1 Amplitude Envelope | HOLD on deep horizontal event at >2× seabed TWT (multiple) |
| 3 — Well ties | Anchor to Rung 1–2 truth | (Rung 2 anchors) | Refuse if no well in scope |
| 4 — Hard horizons | Structure + wells guide difficult picks | #4 #5 #6 #7 | HOLD if structure and wells disagree on same horizon |
| 5 — Integration | Geoseismic section, depositional env, play elements | (Rung 5–6 synthesis) | HOLD if any element has claim_state=DRAFT |
| 6 — Audit | Constitutional firewall | #9 AC_Risk | 888_HOLD on AC_Risk > 0.5 zones |

**Order in each phase:** certainty before uncertainty. Seabed first, then shallow, then deep. Zero-projection wells first (Rotan-1, Pekaka-1), then inboard.

The system prompt for `2_seismic_vision.py` is in §5 of the protocol doc.

---

## 5. Validation Evidence

Proof the pipeline produces real geological signal. Not marketing — numbers.

### 5.1 The ToAC signal ordering (synthetic data, 2026-06-08)

| Region | Texture energy | ToAC signal (vs layered baseline) | Geological class |
|--------|----------------|----------------------------------|------------------|
| Malay — layered Group H/I | 0.01365 | 0.00000 (baseline) | layered reflectors |
| Malay — deep Group J/K | 0.00102 | −0.01263 (more uniform) | transparent |
| Sabah — fold-thrust | 0.04913 | +0.03548 (most disrupted) | sharp thrust surfaces |
| Sabah — MTD | 0.03005 | +0.01640 (chaotic) | mass transport deposit |

**Signal ordering: deep < layered < MTD < fold-thrust.** This is physically correct. Thrust faults create sharper local variance than MTD chaos (thrusts are discrete high-contrast boundaries; MTDs are distributed chaos).

### 5.2 The garbage detector

| Image | edge_map mean | texture_energy mean | Reading |
|-------|---------------|---------------------|---------|
| Flat uniform | 0.0000 | 0.0000 | Dead image — tool sees nothing |
| Random noise | 0.4187 | 0.0817 | High everywhere — low quality, escalate |
| Real Malay | 0.3098 | 0.0150 | Structured but not chaotic |
| Real Sabah | 0.3453 | 0.0288 | Structured and disrupted |

The pipeline can reject bad input before wasting compute on interpretation. **F4 CLARITY in practice.**

### 5.3 The dangerous-similarity eureka (5/7 match + 2 critical mismatches)

| Result | Value |
|--------|-------|
| `similarity_score` | 0.700 |
| `confidence_band` | [0.62, 0.78] |
| `high_contrast_dimensions` | 2 (trap_style, source_rock) |
| `dangerous_similarity_flag` | **YES** |
| Verdict | **HOLD** |

Verdict reason: *"1/2 analog(s) hit dangerous-similarity flag. Score is high but multiple high-contrast dimensions exist. Verify with PRIMARY DATA before using."*

The 11/11 sanity assertions all pass on synthetic data. Full report at `/tmp/geox-realwork/verification_report.json` (archived).

### 5.4 The public proof surface

`https://geox.arif-fazil.com/theory/` — deployed. Has:
- The one-line summary
- The 3 genuinely novel things
- All 9 attributes with phase status pills
- Live demo with synthetic images
- The numbers table (5.1)
- The dangerous-similarity eureka (5.3)
- The garbage detector (5.2)
- The phase roadmap

---

## 6. The Honest Gap

Per the 2026-06-08 review. This is what's missing.

### 6.1 3 of 9 attributes shipped (Phase 1.1)

With 3 of 9, the LLM can tell you what kind of geology is here (mega-domain, facies character, gross fault structure) but **cannot yet track a horizon across the section** (needs #4 horizontal gradient + #6 local dip).

### 6.2 Phase 1.2 is the next forge

Horizontal gradient + vertical gradient. These unlock autonomous horizon tracking. The architectural decision: validate on real KL2V1 data *before* adding more attributes, so we know what's actually needed.

### 6.3 Phase 2.0 is the constitutional firewall

AC_Risk spatial heatmap. Until this ships, the pipeline has no self-awareness of its own limitations. The pointwise version exists (`geox_vision_audit`); the spatial version is the missing layer.

### 6.4 Open question: who defines the expectation baseline?

ToAC says: Observation − Expectation = Signal. But who defines Expectation?

| Option | Pros | Cons |
|--------|------|------|
| (a) Prior model from regional statistics | Governed, reproducible | Requires curated regional models |
| (b) LLM internal representation | Closed reasoning loop, autonomous | Black box, can't audit |
| (c) Human-provided | Fully explicit | Human bottleneck, doesn't scale |

**Architect's recommendation: (a) for mega-domain baselines, (b) for per-feature subtleties.** Resolve before Phase 1.5.

### 6.5 Real vs synthetic gap

The verification is on synthetic data. The real KL2V1 is the next test. Until Band A runs on real multi-survey, multi-vintage, real-noise seismic, the gap between proof-of-concept and operational deployment is unknown. The BIJAKSANA move: **run on real data first, forge Phase 1.2 second, validate on real data again, then promote to constitutional**.

---

## 7. The Cross-References

Where to find each piece in detail.

### 7.1 The Copilot deep research dossier

The "Turning Seismic Pixels into Earth Insight" essay. The philosophical + practical foundation for everything above. ~7 sections covering human vision, AI vision, CV mapping, the "seismic ≠ object detection" case, governance, LLM consumption, and domain comparisons.

**Status:** Incoming — to be archived at `/root/geox/docs/analysis/2026-06-08_vision_intelligence_dossier.md`. This file IS the dossier's index entry; the dossier itself is the source.

### 7.2 The 9-attribute architecture brief

The 8-physical-attribute decomposition spec + the 9th AC_Risk governance attribute. Architectural contract. Lives in: `/root/geox/docs/EUREKA_PHYSICS_DOMAINS.md` (Attribute 9 source) and `/root/geox/docs/TOAC_CANON.md` (the contrast theory).

### 7.3 The KL2V1 6-phase workflow

The operational protocol that maps each phase to a ToAC attribute, GEOX tool, and fail-closed condition. Lives in: `/root/geox/docs/SEISMIC_INTERPRETATION_GOVERNANCE PROTOCOL.md` (operational draft, commit `ae590892` on `feat/band-a-raster-pipeline-2026-06-08`).

### 7.4 The contrast_views verification

The synthetic data + numerical proof that the pipeline produces real geological signal. 11/11 assertions pass. Lives in: `/tmp/geox-realwork/verification_report.json` (raw) and `/root/geox/tests/test_contrast_views.py` (regression suite).

### 7.5 The TriCipta audit

The 2026-06-08 external audit that surfaced GEOX's "killer feature" (governance gap) vs the industry (TriCipta AI/SEB/AI.SEEK). The contrast that named the problem. Lives in: CONTEXT.md 2026-06-08 session log (internal) and the public site theory page (external).

### 7.6 The public site

The proof surface. Deployed at `https://geox.arif-fazil.com/theory/`. Updated 2026-06-08 with the one-line summary, the 3 novel things, the honest gap, and the link to this foundation doc. The user's landing page for vision intelligence.

### 7.7 The ariffazil/geox repo

`https://github.com/ariffazil/geox` — main branch is BIJAKSANA (9 dependabot PRs merged, 2 closed, Q3 rot fix). `feat/band-a-raster-pipeline-2026-06-08` is the active vision intelligence branch (3 of 9 attributes + 21 tests + verification + the protocol doc + this foundation).

---

## 8. The F13 Audit — One Last Time

Before any of this becomes operational, the sovereign ratifies:

| Item | Date | Status |
|------|------|--------|
| Vision V1 +4 (perceptual_inventory, minimax_inference, calibrate, audit) | 2026-06-07 | Pending |
| `geox_analog_atlas` (Tool #39) | 2026-06-08 | Pending |
| `geox_contrast_views` (Tool #40) | 2026-06-08 | Pending |

**Sovereign's call:** ratify all 3 to advance to Phase 1.2 / Phase 2.0; or roll back selectively. The architecture works (proved on synthetic). The honesty gap is real (3 of 9, no real-data validation, no spatial AC_Risk). The path forward is data-first, then attributes.

---

## 9. The Open Thread (2026-06-08)

Two questions are open to the sovereign:

1. **Phase 1.2 spec vs real-data validation first.** The architect's recommendation: run the 3-of-9 pipeline on the real KL2V1 composite first. The data will inform which of Phase 1.2 / 1.3 / 2.0 is most critical next. *Reverse — forge first, validate later — is how we ended up with 3 attributes that can do segmentation but not horizon tracking.*

2. **The expectation baseline question.** (a) prior model / (b) LLM internal / (c) human. Architect's recommendation: (a) for mega-domain, (b) for per-feature. Resolve before Phase 1.5.

Both are the user's decision. The federation agent holds the forge ready; the sovereign ratifies.

---

**DITEMPA BUKAN DIBERI** — and the lower-entropy form of vision intelligence now lives in one file.

*This foundation is consolidated on `feat/band-a-raster-pipeline-2026-06-08` as a single reference. Promote to canonical when Phase 1.2 lands and the KL2V1 real-data validation closes.*
