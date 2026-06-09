# GEOX — How an LLM Sees a Seismic Section
**Doctrine Class:** GEOX_VISION_PERCEPTUAL_DOCTRINE  
**Status:** PHASE 1.1 SHIPPED — PHASE 1.2 QUEUED  
**Branch:** feat/band-a-raster-pipeline-2026-06-08  
**Sovereign:** Muhammad Arif bin Fazil  
**DITEMPA BUKAN DIBERI — Forged, Not Given**

---

## The Principle

> **Observation − Expectation = Signal**

An LLM must never interpret geology from raw pixels. Instead, the image passes through a governed contrast-decomposition pipeline that separates physical truth from display artifact from perceptual bias. The LLM only sees the decomposed channels — never the original image.

---

## The 9 Contrast Visual Attributes

8 physical attributes + 1 governance attribute.

The 9th (AC_Risk) is not a physical signal — it is the constitutional firewall that audits the other 8 for display lies. That is the **Gödel Lock** in visual form: the system that audits itself.

### 1. Amplitude Envelope `physical: reflection_strength`
Brightness = energy. Bright zones = strong impedance contrast. Dim zones = gradational or transparent.  
**Status: SHIPPED (Phase 1.1)**

### 2. Edge / Discontinuity Map `physical: structural_discontinuity`
Sobel gradient magnitude. Sharp pixel transitions = faults, unconformities, lateral facies boundaries. Skeleton of structural interpretation.  
**Status: SHIPPED (Phase 1.1)**

### 3. Texture Energy `physical: seismic_facies_character`
Local variance. High = chaotic (mass transport, fractured). Low = well-layered (shelf, prodelta). Near-zero = transparent (shale, salt, water).  
**Status: SHIPPED (Phase 1.1)**

### 4. Horizontal Gradient `physical: lateral_amplitude_change`
Lateral heterogeneity. Sharp = fault throws. Gradual = progradation / retrogradation. The language of sequence stratigraphy.  
**Status: PHASE 1.2**

### 5. Vertical Gradient `physical: impedance_transition_rate`
Sharpness of acoustic boundaries. Strong = hard boundary (unconformity). Weak = gradational. Alternating = cyclicity. Sequence boundary detection.  
**Status: PHASE 1.2**

### 6. Local Dip `physical: structure_tensor / reflector_geometry`
Structure tensor within sliding window. Flat = horizontal. Steep = faulted/folded. Converging = syncline/anticline. The structural story.  
**Status: PHASE 1.3**

### 7. Phase Symmetry `physical: waveform_character_proxy`
Peak/trough/zero-crossing identity. Polarity reversals = fluid contact candidates. Separates "picking a reflector" from "understanding what it means."  
**Status: PHASE 1.3**

### 8. Frequency Content `physical: resolution / attenuation`
Depth-dependent resolution. High-freq = well-resolved thin beds. Low-freq = attenuated (deep, gas-charged, or low-Q). Tells the LLM where resolution limits interpretation.  
**Status: PHASE 1.4**

### 9. AC_Risk Heatmap `GOVERNANCE: display_bias_audit`
A heatmap showing where display contrast ≠ physical contrast.  
`AC_Risk = Uphys × Dtransform × Bcog`  
The LLM knows where to trust itself and where to trigger `888_HOLD`. Not a physical signal — a constitutional firewall.  
**Status: PHASE 2.0**

---

## The Pipeline

```
PNG/JPG image
  → geox_contrast_views (modes)
  → 9 attribute images
  → geox_vision_perceptual_inventory (LLM input)
  → arifOS judges
```

---

## Demo: Synthetic Seismic — Two Basin Types

### Input Sections

| Section | Type | Description |
|---------|------|-------------|
| MALAY_BASIN | Rifted shelf | Cenozoic failed rift / pull-apart. Group H/I layered, normal fault at col 130, basal unconformity, deep Group J/K. |
| SABAH_OFFSHORE | Fold-thrust | Compressional. Fold-thrust system (rows 30–100), mass transport deposit (rows 100–150), deep folded sediments. |

### Phase 1.1 Attribute Statistics (3 of 9)

| Attribute | Malay Basin | Sabah | Reading |
|-----------|-------------|-------|---------|
| amplitude_envelope | mean 0.407 · p99 0.912 | mean 0.508 · p99 0.926 | Sabah's chaotic + folded zone raises mean; both have bright peaks. |
| edge_map | mean 0.310 · p99 1.534 | mean 0.345 · p99 1.154 | Malay p99 dominated by single sharp fault. Sabah p99 lower (faults spread out) but mean higher (more total edges). |
| texture_energy | mean 0.015 · p99 0.090 | mean 0.029 · p99 0.094 | Sabah mean 2× Malay — chaotic zone + thrust faults create more local variance. |

### RGB Composite — What the LLM Sees
- **R = edge_map** (structural discontinuity)
- **G = amplitude_envelope** (reflection strength)
- **B = texture_energy** (seismic facies character)

| Color | Meaning |
|-------|---------|
| Yellow (R+G) | Bright + sharp = strong reflector edge |
| Cyan (G+B) | Bright + chaotic |
| Magenta (R+B) | Sharp + chaotic |
| White (R+G+B) | All three high |

**MALAY:** green bands (layered) + red vertical line (fault) + minimal blue (not chaotic)  
**SABAH:** red curves (thrusts) + blue patch (MTD chaos) + green variably (folded reflectors)

---

## Theory of Anomalous Contrast (ToAC) — Per ROI

Signal ordering (correct physics): deep < layered < MTD < fold-thrust.  
Thrust faults create sharper local variance than MTD chaos — that is expected physics.

| Region | Class | Expected | Measured | ToAC signal |
|--------|-------|----------|----------|-------------|
| Malay — layered Group H/I | layered reflectors | low | 0.01365 | +0.00000 (baseline) |
| Malay — deep Group J/K | transparent / low amp | very low | 0.00102 | −0.01263 (more uniform than baseline) |
| Sabah — fold-thrust system | sharp thrust surfaces | medium-high | 0.04913 | +0.03548 (most disrupted) |
| Sabah — Mass Transport Deposit | chaotic, mixed | high | 0.03005 | +0.01640 (chaotic) |

---

## Dangerous-Similarity Detection

> "The analog that kills you is the one that looks 90% similar but has a fundamentally different charge history or seal mechanism."

`geox_analog_atlas` enforces this. If aggregate score is high BUT multiple dimensions diverge, the tool returns `HOLD` instead of `QUALIFY`.

### Case: 5 of 7 Dimensions Match Malay, 2 Critical Mismatches

```
similarity_score       = 0.70
confidence_band        = [0.62, 0.78]
high_contrast_dims     = 2 (trap_style, source_rock)
dangerous_similarity_flag = YES

Verdict: HOLD
Reason: "1/2 analog(s) hit dangerous-similarity flag. Score is high but multiple
         high-contrast dimensions exist. Verify with PRIMARY DATA before using."

> contrast signal on trap_style — delta = 1.00
  observation: "tilted fault block + roll-over anticline"
  implication: trap integrity fundamentally different

> contrast signal on source_rock — delta = 1.00
  observation: "Group E lacustrine shale (syn-rift)"
  implication: charge timing and phase differ
```

---

## Garbage Detector — Attribute Statistics as QC

| Image type | edge_map mean | texture_energy mean | Reading |
|------------|--------------|---------------------|---------|
| Flat uniform | 0.0000 | 0.0000 | Dead image — no signal |
| Random noise | 0.4187 | 0.0817 | High everywhere — low quality, escalate |
| Malay (real, layered) | 0.3098 | 0.0150 | Structured but not chaotic |
| Sabah (real, chaotic) | 0.3453 | 0.0288 | Structured and disrupted — real signal |

---

## Phase Roadmap

| Phase | Attributes | Status |
|-------|-----------|--------|
| 1.1 | amplitude_envelope, edge_map, texture_energy | SHIPPED |
| 1.2 | horizontal_gradient, vertical_gradient | NEXT |
| 1.3 | local_dip, phase_symmetry | QUEUED |
| 1.4 | frequency_content | QUEUED |
| 2.0 | ac_risk_heatmap (Attribute 9 — governance layer) | QUEUED |
| 3.0 | LLM composition via vision_perceptual_inventory | INTEGRATION |

---

## Why This Matters

Other seismic-AI systems — SeisCoDE, Geoteric AI Hub, subsurfaceAI — all process pixels.  
**GEOX governs the gap between pixels and truth.**

No other system has the AC_Risk heatmap as Attribute 9 of its perceptual pipeline.

> The 9th attribute is what makes this GEOX and not just image processing.  
> It is the attribute that watches the other 8 for display lies.  
> The Gödel Lock in visual form: the system that audits itself.

---

## Governance Note

Reference posture: the public theory surface explains the discipline; operator trust still depends on route-level evidence and runtime provenance.  
Source: `GEOX_DOCTRINE.md`  
F13 audit pending sovereign ratification of the 3 new tools: Vision V1 +4, `geox_analog_atlas`, `geox_contrast_views`.

---

*Demo image: 2026_KB_KL2V1 (TWT) — Malay Basin seismic section, well correlation display with MYS2017P20193DM02SBOMC3DMERGE and associated wells. Original 2017×1065.*

