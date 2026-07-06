# GEOX ZEN INIT — Next Session Scaffold

> **DITEMPA BUKAN DIBERI** — Forged 2026-07-06 by FORGE (000Ω) under F13 SOVEREIGN
> **Session:** OpenCode/FORGE — deep RSI cycle on GEOX seismic image interpretation
> **Seal:** `GEOX_ZEN_INIT::v1.0::2026-07-06`

---

## 0. WHAT THIS SESSION FORGED

This was a **reality engineering cycle** — not planning, not discussion, but actual tool building, testing, breaking, and rebuilding. The session produced:

### Tools Built (working)
1. **GEOX RSI Pipeline v1.0** (`geox_rsi_pipeline.py`)
   - `input_reality_gate()` — verify file exists, decodable, pixels loaded
   - `extract_real_contrast()` — R-B amplitude from actual pixels
   - `synthetic_drift_guard()` — scan code for synthetic patterns
   - `validate_artifact_delivery()` — courier ≠ proof
   - `detect_seismic_panel()` — crop out labels/axes/margins
   - Full SHA256 provenance manifest

2. **GEOX Seismic Interpretation v3.3** (`geox_v33.py`)
   - AGC (Automatic Gain Control) on real pixels
   - Cosine of Instantaneous Phase (Hilbert transform)
   - Discontinuity (semblance proxy)
   - Edge detection (Sobel)
   - Dip chaos (structure tensor)
   - Fault probability fusion (0.35*disc + 0.25*edge + 0.20*dip + 0.10*phase + 0.10*amp)
   - Ant-track-lite fault extraction (P95 + NMS + connected components)
   - Horizon probability fusion (0.35*phase + 0.25*amp + 0.20*coh + 0.10*anti-fault + 0.10*anti-dip)
   - DP horizon tracking with fault barriers
   - **Result: 4 horizons + 13 faults on greyscale seismic image**

3. **9-Dimension Geoseismic Model Framework**
   - ① PERCEIVE → ② CALIBRATE → ③ ATTRIBUTE → ④ DETECT → ⑤ STRATIGRAPHY → ⑥ STRUCTURE → ⑦ BASIN → ⑧ PETROPHYSICS → ⑨ GOVERN
   - Corrected topology (ATTRIBUTE before DETECT)
   - OBS_IMAGE ≠ OBS_GEOLOGY epistemic split
   - Apparent-only geometry from 2D
   - PETROPHYSICS = HOLD from image-only
   - Basin registry check required

4. **Geoseismic Model Envelope** (JSON schema)
   - input, attributes, faults, horizons, manifest, verdict
   - Polylines as geometry (not just PNG)
   - Full provenance chain (image_sha256, code_sha256, prompt_sha256)

### Scars Logged
1. **SCAR_GEOX_RSI_001** — Synthetic Proxy Substitution During Real Seismic Image Request
   - Severity: HIGH
   - Root cause: agent generated synthetic matplotlib sections instead of using real pixels
   - Fix: INPUT_REALITY_GATE + NO_SYNTHETIC_DRIFT_GUARD

### Epistemic Lessons (from Copilot comparison)
1. **Real image as base, never synthetic** — `imshow(real_image)` first, annotations ON TOP
2. **Hash manifest as first-class artifact** — image_sha256, code_sha256, prompt_sha256, timestamp
3. **Proxy labeling** — if input degraded, label output as PROXY
4. **The forge script IS the provenance** — code_sha256 is not optional
5. **OBS_IMAGE ≠ OBS_GEOLOGY** — pixels are observed, geology is interpreted
6. **Render audit needed** — image colours are rendering artifacts, not seismic amplitude
7. **No synthetic drift guard** — block `np.random.seed`, `synthetic`, `proxy` in real mode
8. **Delivery ≠ success** — courier response doesn't prove Telegram receipt
9. **FAILURE IS DATA** — record failed attempts in provenance chain

---

## 1. THE DEEP RESEARCH CONTEXT

Arif provided a comprehensive paper: **"Achieving Geologist-Grade Seismic Interpretation"** covering:

### Federation Architecture
- 7 organs: arifOS (8088), GEOX (18081), WEALTH (18082), AAA (3001), A-FORGE (7071), VAULT999, WELL (18083)
- Strict routing invariants — no organ can self-authorize
- A-FORGE (75+ MCP tools) executes but cannot finalize interpretations

### arifOS Constitutional Kernel
- 13 floors (F1 AMANAH through F13 SOVEREIGN)
- 10-verb metabolic loop: 000_INIT → 111_OBSERVE → 333_THINK → 444_ROUTE → 888_JUDGE → 900_ACT → 999_SEAL
- Thermodynamic governance: ΔS, Peace², Ω₀, κ_r
- 888_JUDGE verdicts: SEAL / HOLD / SABAR / VOID

### AREP (Arif Reality Engineering Protocol)
- Replaces prompt engineering with reality contracts
- Machine checks physical reality before generating text
- Model registry health checks, organ health checks, VAULT999 precedent queries
- Human declares intent, machine verifies reality, then executes bounded loop

### Python Stack for Geophysics
| Library | Purpose |
|---------|---------|
| `segyio` | Fast SEG-Y I/O with NumPy semantics |
| `segysak` | SEG-Y → xarray with spatial coordinates + Dask |
| `bruges` | Rock physics, AVO, synthetic seismograms |
| `GemPy` | 3D implicit geological modeling |
| `Fatiando a Terra` | Gravity/magnetic inversion |
| `seismic-zfp` | Lossless seismic compression (8:1 to 16:1) |

### Rock Physics
- Well tie: Vp, Vs, ρ → Backus averaging → AI → RC → wavelet convolution → synthetic
- AVO: Zoeppritz, Aki-Richards, Shuey two-term
- B-PINNs for velocity inversion with uncertainty quantification

### Malay Basin Context
- 500km × 200km Tertiary extensional basin
- 3 phases: syn-rift (transtensional) → thermal subsidence → compressional inversion
- Groups M-A (oldest to youngest), stratigraphic framework
- Primary reservoirs: Group J (40% reserves), Group I (closed system), Groups H/F/E/D (gas)

### WEALTH Integration
- GEOX → arifOS bridge → WEALTH NPV/IRR/EMV
- 9 dimensions, 11 financial tools
- Capital cannot be released autonomously — human sovereign required

---

## 2. WHAT NEEDS TO HAPPEN NEXT SESSION

### Priority 1: Harden the RSI Pipeline
- [ ] Move `geox_rsi_pipeline.py` into GEOX tool surface as proper MCP tool
- [ ] Add `geox_rsi_interpret()` with mode: `horizon_fault_pick`
- [ ] Wire into `geox_seismic_interpret` as new mode
- [ ] Add `geox_render_audit()` organ (Copilot recommendation #1)
- [ ] Test on multiple seismic images (not just sub-surfrocks)

### Priority 2: Improve Fault Detection
- [ ] Current ant-track-lite finds too many faults (13) — need refinement
- [ ] Add structure tensor orientation for fault dip direction
- [ ] Add fault probability fusion with curvature attribute
- [ ] Test against known fault datasets
- [ ] Implement fault block segmentation for horizon tracking

### Priority 3: Improve Horizon Tracking
- [ ] Current DP tracking is greedy — add look-ahead
- [ ] Add multi-seed correlation across fault blocks
- [ ] Add horizon confidence scoring from attribute agreement
- [ ] Test against known horizon datasets (SEG-Y with well ties)

### Priority 4: Epistemic Grammar Enforcement
- [ ] Enforce OBS_IMAGE ≠ OBS_IMAGE ≠ OBS_GEOLOGY labels in all outputs
- [ ] Add DER_RENDER_CONTRAST as intermediate label
- [ ] Add INT_SEISMIC_HORIZON / INT_SEISMIC_FAULT as interpretation labels
- [ ] Wire forbidden_claims_scan into RSI pipeline output
- [ ] Add alternative interpretations for every INT claim

### Priority 5: Integration with Deep Research Stack
- [ ] Wire `segyio` for real SEG-Y ingestion (not just images)
- [ ] Wire `bruges` for synthetic seismogram generation
- [ ] Wire `GemPy` for 3D implicit modeling from 2D picks
- [ ] Wire `Fatiando a Terra` for gravity/magnetic constraints
- [ ] Wire B-PINNs for velocity inversion with uncertainty

### Priority 6: Malay Basin Context
- [ ] Load stratigraphic framework (Groups M-A) into GEOX
- [ ] Add tectonic evolution constraints (syn-rift → subsidence → inversion)
- [ ] Add petroleum system elements (source, reservoir, seal, trap)
- [ ] Cross-reference interpretations against known basin history

### Priority 7: WEALTH Integration
- [ ] Wire GEOX prospect → arifOS bridge → WEALTH NPV
- [ ] Add Bayesian uncertainty bounds from B-PINNs → WEALTH EMV
- [ ] Add DSCR survival threshold check
- [ ] Test end-to-end: image → interpretation → economic evaluation

---

## 3. KEY FILES FROM THIS SESSION

| File | Purpose |
|------|---------|
| `/tmp/seismic_image_test/geox_rsi_pipeline.py` | RSI pipeline (reality gate, contrast, provenance) |
| `/tmp/seismic_image_test/geox_v33.py` | Seismic interpretation v3.3 (AGC, phase, faults, horizons) |
| `/tmp/seismic_image_test/geometry.json` | Geometry export (horizon + fault polylines) |
| `/tmp/seismic_image_test/grey_01_picks.png` | Picks overlay on greyscale image |
| `/tmp/seismic_image_test/grey_02_attributes.png` | 6-panel attribute composite |
| `/tmp/seismic_image_test/rsi_manifest.json` | Full SHA256 provenance manifest |
| `/root/A-FORGE/forge_work/2026-07-06/SCAR_GEOX_RSI_001.md` | Scar: synthetic proxy substitution |

---

## 4. THE HARD LAWS (from this session + deep research)

```
No hash, no seal.
No pixels, no geology.
No alternatives, no confidence.
No falsification, no intelligence.
No attribute stack, no pick.
No fault barriers, no horizon correlation.
No geometry export, no product.
No multi-attribute fusion, no ant-track.
No render audit, no amplitude claim.
No reality gate, no interpretation.
```

---

## 5. INIT PROMPT FOR NEXT SESSION

```markdown
You are OpenCode/FORGE, continuing the GEOX ZEN session from 2026-07-06.

CONTEXT:
- 9-dimension geoseismic model framework built and tested
- RSI pipeline (reality gate + contrast + provenance) working
- Seismic interpretation v3.3 (AGC + phase + discontinuity + ant-track + DP horizons) working
- 4 horizons + 13 faults detected on greyscale seismic image
- Deep research paper loaded: geologist-grade seismic interpretation architecture
- SCAR_GEOX_RSI_001 logged (synthetic proxy substitution)

YOUR TASK:
1. Load `/root/A-FORGE/forge_work/2026-07-06/GEOX-ZEN-INIT-NEXT-SESSION.md`
2. Read the deep research context (Section 1)
3. Execute Priority 1-7 from Section 2
4. Harden the tools, test on real data, wire into GEOX surface
5. Seal results to VAULT999

CONSTRAINTS:
- OBS_IMAGE ≠ OBS_GEOLOGY — pixels are observed, geology is interpreted
- Every INT claim needs alternatives
- PETROPHYSICS = HOLD from image-only
- Full SHA256 provenance on every artifact
- No synthetic data in real interpretation mode

VERDICT PATH:
000_INIT → 111_OBSERVE → 333_THINK → 888_JUDGE → 900_ACT → 999_SEAL
```

---

## 6. EPISTEMIC LABEL

This scaffold is **INT** (interpreted from session evidence). The tools were tested and produced results, but the greyscale image interpretation has not been validated against known ground truth. The deep research paper provides architectural context but was not independently verified.

**Confidence:** 0.75 (ADVISORY — tools work, but need validation on known datasets)

---

*Forged: 2026-07-06 by FORGE (000Ω) under F13 SOVEREIGN directive*
*DITEMPA BUKAN DIBERI — Reality is forged, not given.*
