# 🌊 SEISMIC — Section Interpret Zen

> **SOT** for automated seismic section / volume interpretation in GEOX.  
> Absorbs external Claude + ChatGPT + Gemini blueprints (2026-07-23) + F13 sealed arc.  
> **Law:** GEOX proposes + falsifies Earth evidence. arifOS seals. Arif decides.  
> **Not:** autonomous structural authority · greyscale = geology · local SEAL.

**Tip baseline:** `78963c61` · 31 public tools · modes on `geox_seismic_interpret`  
**Related:** `SEISMIC_STRUCTURAL_VALIDATION_GATES_G0_G10.md` · `SEISMIC_FAULT_PHYSICS_GATES_K_SPEC.md`  
**Code:** `structure_gates/*` · `structure_validate.py` · `classical_section_propose.py` · `seismic_rsi.py`

---

## 0. Eureka (strategy lock)

**Industry default:** obsess over Phase A — unverified ML that “draws the right lines.”  
**GEOX unfair advantage:** invert it. **Adjudication spine first** (Phase C). Propose is a hostile witness.

| Truth | Consequence |
|-------|-------------|
| Perfect automated interpretation is a **statistical illusion** | Never claim “GEOX interprets Earth” |
| Perfect falsification is **deterministic math** | Commit weeks to gates, not GPUs |
| Bond-class conceptual uncertainty: ~21% of 412 humans got tectonic setting right on the same image | Multi-hypothesis + human adjudicate is not a bug |
| Fine-scale over-interpretation injects noise | Prefer coarse alternatives + kill evidence over rugose “precision” |

**POS (sealed strategy, not marketing):**

| Bet | POS | Role |
|-----|-----|------|
| **B** contract | ~0.9 → **shipped** | Oxygen — nothing downstream without hard public contract |
| **C** gates (descoped restore) | ~0.75 → **shipped / demonstrated** | Merciless moat — Andersonian dip, D/L, throw taper as NumPy |
| **A full** autonomous field ML | **~0.3** | Do not fund as product claim |
| **A descoped** hostile-witness propose | **~0.6** → **classical live** | Generate candidates; label INT/SPEC; gate everything |

**Proof that ends the argument:** K-DIP / K-THROW kill a deliberately impossible pick end-to-end with receipt_hash. Re-probeable on tip `78963c61`.

**Commit the weeks to the adjudication spine.** Let the industry waste cycles on a perfect proposal model.

---

## 0.1 One equation

```
measurement → propose (INT/SPEC, hostile) → physics gates (K*/G*) → falsify/claim → receipt → arifOS SEAL?
```

Vision/ML is always the **propose** half. Deterministic geometry+physics is the **validate** half.  
Marketing claims about foundation models **exceed** reproducible field evidence — gate everything.

---

## 1. Live surface (do not invent tools)

| Mode on `geox_seismic_interpret` | Role | Epistemic max |
|----------------------------------|------|----------------|
| `horizon_contrast` | 1D multi-attr boundary | DER / INT |
| `fault_sticks` | stick **ingest** only | OBS (geometry file) |
| `volume_frame` / `blend` | frame I/O | OBS |
| `structure_validate` | K*/G* matrix (the moat) | DER |
| `classical_section` / `interpret_section` | **PRIMARY** image propose (hostile witness) | **INT_SEISMIC** |
| `interpret` | propose → gate → ≥3 hyps | INT |
| `rsi_pipeline` | legacy comparator only | INT_SEISMIC |
| `segy_slice` | optional volume path | **OBS** wavefield |

Also: `geox_falsify(claim_type=structural_*)` · `geox_visual_understand` (HOLD without VLM) · `geox_seismic_ingest` / `compute`.

**No new public tool** unless F13 + mode reuse exhausted. Prefer modes.

Local max verdict: **QUALIFIED_CANDIDATE**. Transport allow: **TRANSPORT_OK** ≠ SEAL.

---

## 2. Architecture (zen)

**Sovereign product preference (F13 2026-07-23):**  
**Primary input = seismic section image** (PNG/JPG raster). Full SEG-Y volume is **optional upgrade**, not required for the assisted loop.

Gemini dual-lane (aligned): **propose lane** → **falsify lane** → arifOS SEAL only. Image is for draft structural candidates + uncertainty, not sealed Earth truth (Bond/Alcalde conceptual uncertainty).

```
┌─ G0 MEASURE (IMAGE-FIRST) ────────────────────────────────┐
│  PRIMARY: section image + VE + SHA-256 + axis notes       │
│           input_class=image_only · INT_SEISMIC forever    │
│  OPTIONAL: SEG-Y slice when user has volume (higher truth)│
│  Without scale: digitise + propose OK; true dip/throw/V   │
│               = UNMEASURED (never invent)                 │
└────────────────────────────┬──────────────────────────────┘
                             ▼
┌─ G1 PROPOSE (image geometry) ─────────────────────────────┐
│  Classical CV + RSI · ≥3 alternatives · CANDIDATE only    │
│  Pixel domain until calibration; snap to edges/coherence  │
└────────────────────────────┬──────────────────────────────┘
                             ▼
┌─ G2–G9 + K* VALIDATE ─────────────────────────────────────┐
│  structure_validate · hard + soft correlated gates        │
│  Any hard KILL → model rejected · not blind POS product   │
└────────────────────────────┬──────────────────────────────┘
                             ▼
┌─ GOVERN ──────────────────────────────────────────────────┐
│  geox_falsify / geox_claim · arifOS TRANSPORT_OK / SEAL   │
│  Human ratifies structural framework                      │
└────────────────────────────┬──────────────────────────────┘
                             ▼
┌─ G10 HANDOFF ─────────────────────────────────────────────┐
│  Ensemble + uncertainty only → WEALTH (never single map)  │
│  image_only → seal_eligibility=false always               │
└───────────────────────────────────────────────────────────┘
```

---

## 3. K-* gates (seven kill / soft — literature-bound)

Implemented: `src/geox_mcp/tools/structure_gates/`. Spec detail: K-SPEC file.

| Gate | Literature anchor | GEOX rule (zen) |
|------|-------------------|-----------------|
| **K-DIP** | Anderson; Célérier 2008 ROG | Normal ~55–70° · reverse/thrust ~20–40° · SS ~75–90°. **Correct dip for VE before test** (Alcalde 2019). Reactivation / fluid-pressure → SPEC not hard-kill if flagged. |
| **K-THROW** | Barnett et al. 1987 AAPG | Throw max mid-fault → 0 at elliptical tip. Steady-high + abrupt tip = KILL. Multi-peak = linkage (flag). |
| **K-DL** | Kim & Sanderson 2005; Torabi & Berg 2011 | D/L global ~10⁻³–10⁻¹; Earth bulk **0.005–0.05**. Extreme without linkage → KILL; soft WARN outside preferred band. |
| **K-XCUT / G2** | Bond group SE 2019 | Non-cross horizons; polarity/order consistency; incidence graph. |
| **K-RESTORE / G5** | Dahlstrom 1969; Groshong ADS | Line-length / area residual within tol. **Build-not-buy** (no mature OSS restore lib). GemPy = frame only. |
| **K-VEL / G7** | rock-physics bands | V≤0 or impossible lithology band → KILL. Feed from well-tie / T–D when present. |
| **K-GROWTH / G4** | Thorsen 1963 EI | Growth claim + EI≤1 → KILL. EI>1 supports, does not prove (Castelltort sedimentary mimic). |

**INCONCLUSIVE is valid** when evidence missing. Gates are **correlated** — do not multiply as independent POS.

---

## 4. G0–G10 (structural claim ladder)

| G | Type | Zen meaning |
|---|------|-------------|
| G0 | Hard | Measurement identity (**image-first**; image_only capped; SEG-Y optional) |
| G1 | Soft | Propose with alternatives + confidence |
| G2 | Hard | Topology |
| G3 | Mixed | Displacement (throw + D/L) |
| G4 | Soft | Stratigraphic / growth response |
| G5 | Hard | Restoration |
| G6 | Conditional | Mechanical / dip prior |
| G7 | Hard | T–D / velocity |
| G8 | Soft→hard | 3D closure (volume path) |
| G9 | Required | Falsify + alternatives + EVOI |
| G10 | Contract | Ensemble only to capital |

---

## 5. Toolchain (license-safe first)

| Layer | Prefer | Avoid / flag |
|-------|--------|----------------|
| SEG-Y I/O | **segyio** LGPL-3.0 (dynamic) | static-link GPL traps |
| Lazy cube | xarray/Zarr; **segysak** only as separable CLI if GPL | embed GPL into proprietary binary |
| Attributes | **numpy/scipy/skimage** (BSD) | d2geo GPL as core dep |
| Propose ML | **SAM / SAM2 Apache-2.0** ONNX; Synthoseis-trained GFM | **FaultSeg3D / SFM weights CC BY-NC** = research-only flag |
| Frame model | GemPy EUPL-1.2 | claim kinematic restore from GemPy alone |
| VLM | propose-only, always gated | quantitative authority from Claude/GPT vision |
| Heavy offline | Madagascar RSF optional | runtime MCP dependency |

**ONNX Runtime** for shipping CNN/ViT — keep MCP dep light; 2D section target **&lt;10 s**.

---

## 6. Benchmarks (acceptance = human envelope, not single truth)

| Set | Use | License note |
|-----|-----|--------------|
| **F3 Netherlands** | volume / section harness | CC BY-SA |
| **CRACKS** (F3 labels) | multi-annotator fault variance | open |
| **SEAM Phase I** | synthetic salt / V bounds | CC BY 4.0 |
| **Parihaka** | open 3D stacks | CC / NZ open-file |
| **Marmousi** (on disk) | smoke SEG-Y path | synthetic |
| **Alcalde / Bond** | human dip/topology variance envelope | **source image identity required** |
| Wu 200-cube | research CNN only | CC BY-NC with faultSeg |

Score: agent pick **inside human IQR** on ≥N sections = “competent human band,” not “ground truth.”

---

## 7. Roadmap — map external P0/P1/P2 ↔ GEOX B→C→A

| External | GEOX name | Status (2026-07-23) | Next |
|----------|-----------|---------------------|------|
| **P0** contract truth | Phase **B** | **DONE** — attribute_data+depth, honest router, TRANSPORT_OK, QUALIFIED_CANDIDATE | discriminated-union schema gen + CI drift lock |
| **P0/P1 gates** | Phase **C** | **PARTIAL LIVE** — all 7 K* + G2 topology + restore/vel stubs | VE-true dip · receipt formula fields · restore numerics |
| **P1 propose** | Phase **A** | **PARTIAL LIVE** — RSI interpret_section · ≥3 alts · thin schemas v1.1 | attribute-snap · optional ONNX SAM · research CNN flag |
| **P1 image classical** | Phase **A+** | **LIVE** — `classical_section` / `interpret_section` (structure tensor+DP) | primary product path |
| **P1 SEG-Y** | Phase **D** | **OPTIONAL** — segy_slice live; not required for product | only if user supplies volume |
| **P2** accreditation | Phase **E** | OPEN | F3/CRACKS harness · Alcalde pack · well-tie ensemble · G8 · release checklist |

**Claim rights by stage**

| Stage | May claim | Must not claim |
|-------|-----------|----------------|
| After B/P0 | trustworthy ingest + auditable observation | structure truth from screenshot |
| After C+A partial | draft structural **candidates** + kill evidence | autonomous framework SEAL |
| After E/P2 | physics-challenged, uncertainty-quantified candidates for arifOS | operational / capital authority |

---

## 8. Receipt envelope (minimum fields)

Every nontrivial seismic output:

`source_sha256` · `input_class` · `epistemic_tag` · `units` · `crs`/`vertical_datum` (or null + reason) · `vertical_exaggeration` · `model_provenance` · `alternatives[]` · `gates{}` · `kill_conditions` · `local_verdict=QUALIFIED_CANDIDATE` · `seal_authority=arifOS_only` · `seal_eligibility` default **false** for image_only.

---

## 9. Explicit non-goals

- Autonomous SEAL of structural framework  
- Greyscale pixel amplitude as reflection coefficient  
- Single deterministic map as Earth truth  
- Blind POS product of correlated gates  
- Commercial ship of CC BY-NC CNN weights without flag  
- WEALTH NPV from ungated structure  
- Theatre “GEOX vs humans” without benchmark identity  
- New public MCP tools when a **mode** suffices  
- **Requiring full SEG-Y / 3D volume as the only path** — F13 product is **image section first**  
- Sealed structural framework from image_only (constitutionally barred)

---

## 10. External source archive

| Source | Path / note |
|--------|-------------|
| Claude + ChatGPT | `forge_work/2026-07-23/EXTERNAL-SEISMIC-BLUEPRINT-CLAUDE-CHATGPT.md` |
| Gemini dual-lane + SEG-Y deep dive | session prompt 2026-07-23 (image-first **overrides** Gemini SEG-Y-primary packaging) |

This zen file is the **operational SOT**. External essays are evidence, not runtime doctrine.  
**F13 override:** product path = **section image → propose → gate → compare → human**. SEG-Y is enrichment only.

---

## 11. Agent first move (when forging next)

1. Read this file + K-SPEC + G0–G10.  
2. Prefer hardening **receipts / VE dip / F3 harness** over new ML.  
3. Any propose-layer upgrade must exit through `structure_validate`.  
4. Tests assert **receipts**, not only answers.  
5. Commit · restart geox-mcp · `curl :8081/health`.

DITEMPA BUKAN DIBERI — ZEN SOT ALIVE
