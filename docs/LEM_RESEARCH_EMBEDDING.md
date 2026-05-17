# GEOX LEM Research Embedding — Scientific References
## Peer-reviewed anchors for GEOX's Well-Log Foundation Model, Earth System Foundation Model, and Physics-Informed Neural Network layers.

***

## Reference 1 — WLFM: Well-Logs Foundation Model
**URL:** `https://arxiv.org/html/2509.18152v1`
**Citation:** Qi et al. (2025). WLFM: A Well-Logs Foundation Model for Multi-Task and Cross-Well Geological Interpretation. Geoenergy Science and Engineering.
**Relevance:** Tier 1 — directly maps to GEOX's well-log intelligence stack.

### Key Claims (Verified)

| Metric | WLFM-1200 | WLFM-Finetune |
|--------|-----------|---------------|
| Porosity MSE | 0.0041 | 0.0038 |
| Lithology Accuracy | 74.13% | 78.10% |
| Pretraining Scale | 1,200 wells | 1,200 wells + fine-tune |

### Architecture (Three-Stage)

```
Stage 1: Tokenization
  Input: multi-curve log patch (C channels × L depth)
  → Domain-aware encoder (curve-type embedding + relative-depth encoding)
  → Vector-Quantized (VQ) codebook discretization
  → Discrete geological token sequence

Stage 2: Self-Supervised Pretraining
  → Masked Token Modeling (MTM): recover masked stratigraphic tokens
  → Stratigraphy-Aware Contrastive Learning (SCL): cross-well, same-layer positive pairs
  → Total: L_pretrain = L_MTM + α × L_SCL

Stage 3: Multi-Task Fine-Tuning
  → Lithology classification head
  → Porosity regression head
  → Curve reconstruction head
  → Consistency loss (KL between porosity and lithology posteriors)
```

### GEOX-Specific Embeddings

**Embedding Point** | **What to Add** | **File Path**
`resources/ontology/wlfm_vocabulary.md` | VQ codebook documentation, geological token meanings | `resources/ontology/wlfm_vocabulary.md`
`resources/playbooks/well_sequence_stratigraphy.yaml` | WLFM cross-well lithology accuracy claim, 78.10% | `resources/playbooks/well_sequence_stratigraphy.yaml`
`resources/toolcards/geox_well_analyze_sequence.yaml` | Add "WLFM-validated, 78.10% lithology accuracy" to claim_limits | `resources/toolcards/...`
`src/geox_core/engines/stratigraphy/foundation_model.py` | VQ tokenizer + transformer backbone, trained on multi-curve logs | `src/geox_core/engines/stratigraphy/foundation_model.py`

### Important Limitations (Failure Cases)

- Thinly interbedded, noisy formations → fragmented predictions, poor continuity
- Shallow/ultra-deep intervals → systematic value offsets (casing/sensor transitions)
- Boundary detection not explicitly evaluated
- No uncertainty quantification — risk-sensitive deployment requires this

**GEOX Seal Implication:** Claim `geox_well_analyze_sequence` lithology output as PLAUSIBLE at best, not CLAIM, unless calibrated against local core.

---

## Reference 2 — Aurora: Earth System Foundation Model
**URL:** `https://www.nature.com/articles/s41586-025-09005-y`
**Citation:** (2025). A foundation model for the Earth system. Nature.
**Relevance:** North-star architecture for GEOX LEM — Aurora demonstrates what a true Earth-scale foundation model looks like at 1.3B parameters, trained on 1M+ hours of diverse geophysical data.

### Key Claims (Verified)

| Metric | Achievement |
|--------|------------|
| Pretraining Data | 1M+ hours of diverse geophysical data |
| Model Size | 1.3B parameters |
| Air Quality (5-day) | Outperforms numerical models on 74% of targets |
| Ocean Waves (10-day) | Outperforms numerical models on 86% of targets |
| Cyclone Tracks (5-day) | Outperforms 7 operational centers on 100% of targets |
| High-Res Weather (10-day) | Outperforms state-of-art on 92% of targets |

### Architecture (Three-Part)

```
Encoder (Perceiver-based)
  → Converts heterogeneous inputs (different resolutions, variables, pressure levels)
  → Universal latent 3D representation

Processor (3D Swin Transformer)
  → Evolves representation forward in time
  → Recursive: forecasts fed back as inputs for longer lead times

Decoder (Perceiver-based)
  → Translates 3D latent back into physical predictions
  → Outputs at any desired resolution
```

### GEOX-Specific Embeddings

**Embedding Point** | **What to Add** | **File Path**
`resources/ontology/aurora_architecture.md` | Three-part architecture (encoder/processor/decoder) for LEM design doc | `resources/ontology/aurora_architecture.md`
`docs/LEM_ROADMAP.md` | Aurora as north-star: GEOX-LEM = Aurora architecture adapted for subsurface | `docs/LEM_ROADMAP.md`
`src/geox_core/engines/lem/encoder.py` | Perceiver-based encoder: ingest logs + seismic + EM into universal latent | `src/geox_core/engines/lem/encoder.py`
`src/geox_core/engines/lem/processor.py` | Swin Transformer processor: evolve subsurface latent forward in depth/time | `src/geox_core/engines/lem/processor.py`
`src/geox_core/engines/lem/decoder.py` | Perceiver-based decoder: output porosity, Sw, lithology, pressure at target resolution | `src/geox_core/engines/lem/decoder.py`

### Important Constraints

- Aurora is atmospheric/oceanic — not subsurface. Surface data is orders of magnitude more abundant than subsurface data.
- Subsurface foundation model requires solving the data scarcity problem first (→ DRP synthetic core layer)
- GEOX LEM would need: VQ tokenizer for subsurface (from WLFM) + Aurora's processor scale + CANON-9 constraints

**GEOX Seal Implication:** Aurora is the north-star reference. The H3/H4 work (WLFM-based well-log backbone + PINN petrophysics) comes first. LEM is Horizon 8+.

---

## Reference 3 — Petrophysics-Informed Neural Network
**URL:** `https://www.eurekalert.org/news-releases/1037990`
**Citation:** Pothana & Ling (2025). Physics-integrated neural networks for improved mineral volumes and porosity estimation from geophysical well logs. Energy Geoscience.
**Relevance:** H3 — directly validates the PINN layer in GEOX's petrophysics engine.

### Key Claims (Verified)

- Physics-constrained loss function embedded during training
- Reduced uncertainties in reservoir characterization
- Improved mineralogy and porosity prediction reliability
- Validated on geophysical well log data (exactly GEOX's input domain)

### Architecture Pattern

```
Standard NN:   L_total = L_data (mean-squared error against labels)
PINN:           L_total = L_data + λ × L_physics

L_physics = physics constraints embedded as:
  - Archie equation residual (for Sw)
  - Density-porosity relationship (for φ)
  - Vsh bounds from GR (for lithology)
  - Gardner's relation (for Vp from ρ)
```

### GEOX-Specific Embeddings

**Embedding Point** | **What to Add** | **File Path**
`src/geox_core/engines/petrophysics/pinn.py` | PINN module: L_total = L_data + λ × L_physics(Archie + density-porosity + Gardner) | `src/geox_core/engines/petrophysics/pinn.py`
`resources/toolcards/geox_subsurface_generate_candidates.yaml` | Add PINN physics-constrained mode | `resources/toolcards/geox_subsurface_generate_candidates.yaml`
`resources/prompts/failure_policy.md` | PINN failure: if physics residual > threshold → emit HOLD with physics_guard flag | `resources/prompts/failure_policy.md`

### CANON-9 Bounded PINN Design

GEOX's PINN must be bounded by CANON-9 physical constraints:

```
CANON-9 bounds (irreducible):
  ρ: 2.0–2.7 g/cc (sandstone)
  Vp: 1.5–5.5 km/s (sandstone), 3.5–7.0 km/s (carbonate)
  Sw: 0–1 (physically bounded)
  φ: 0–0.40 (physical maximum)

PINN loss = L_data + λ_physics × L_physics

L_physics = Σ (constraint residual) for each CANON-9 variable:
  - Archie: Sw^n = (RT/RT0) × (1/φ^m) → residual
  - Density-porosity: ρ = ρ_ma × (1-φ) + ρ_f × φ → residual
  - Gardner: Vp = a × ρ^b → residual
  - Vsh bounds: GR-index → Vsh_min, Vsh_max → residual
```

---

## Consolidated Embedding Roadmap

| Horizon | Research Source | GEOX Layer | File to Create/Modify |
|---------|----------------|-----------|----------------------|
| H3 (Next) | PINN (Ref 3) | `geox_core/engines/petrophysics/pinn.py` | Create: physics-constrained loss on Archie + density-porosity + Gardner |
| H3 (Next) | PINN (Ref 3) | `resources/toolcards/geox_subsurface_generate_candidates.yaml` | Add PINN mode to claim_limits |
| H4 | WLFM (Ref 1) | `geox_core/engines/stratigraphy/foundation_model.py` | Create: VQ tokenizer + transformer backbone, stratigraphy-aware SCL |
| H4 | WLFM (Ref 1) | `resources/ontology/wlfm_vocabulary.md` | Create: geological token documentation |
| H5 | WLFM (Ref 1) + PINN | `src/geox_mcp/tools/well.py` | Add `geox_well_foundation_embed` tool: returns WLFM token + embedding |
| H5 | WLFM (Ref 1) | `resources/prompts/tool_selection.md` | Add WLFM embedding routing rules |
| H6 | Aurora (Ref 2) | `docs/LEM_ROADMAP.md` | Create: Aurora-architecture LEM design document |
| H7 | Aurora (Ref 2) | `src/geox_core/engines/lem/` | Create: Perceiver encoder + Swin processor + Perceiver decoder |
| H8+ | All three | `src/geox_core/engines/lem/train.py` | Unified pretraining: VQ tokens + PINN loss + Aurora-scale processor |

---

## Critical Dependency Chain

```
DRP Synthetic Core (Future H3)
    ↓ generates training data
WLFM Well-Log Backbone (H4)
    ↓ produces geological tokens
PINN Petrophysics (H3, in parallel)
    ↓ provides CANON-9 bounded physics
Aurora-Scale LEM (H7+)
    ↓ unifies all three above
```

**No shortcuts.** WLFM needs real wells. PINN needs calibrated physics. Aurora-scale needs data that doesn't exist yet. GEOX's path is correct.

---

## Failure Mode Mapping

| External Research Finding | GEOX Failure Protocol |
|-------------------------|----------------------|
| WLFM: thinly interbedded → fragmented lithology | `geox_evidence_contradiction_scan` flags high B_cog |
| WLFM: shallow/ultra-deep → systematic offset | Check depth_basis, flag if <500m or >5000m |
| WLFM: no uncertainty quantification | Require `uncertainty_band` in all `geox_well_analyze_sequence` outputs |
| Aurora: data scarcity is the bottleneck | Prioritize DRP synthetic core before LEM |
| PINN: physics residual > threshold | 888HOLD: physics_guard failed, emit `missing_inputs_schema` |
| PINN: uncalibrated mineral model | All PINN outputs are ESTIMATE until core calibration provided |

---

## Claim State Additions Required

```python
# In geox_subsurface_generate_candidates output, add:
claim_state_additions = {
    "wlfm_lithology_accuracy": "78.10% (WLFM-Finetune, cross-well, 1200 wells)",
    "wlfm_porosity_mse": "0.0038 (WLFM-Finetune)",
    "pinn_mineral_uncertainty_reduction": "Validated (Pothana & Ling 2025)",
    "aurora_operational_outperformance": "74-100% across 4 Earth system domains",
    "lem_horizon": "H7+ (after WLFM backbone + PINN + DRP synthetic core)",
}
```

---

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**

*Research artifact for GEOX Perplexity Space — Epoch 2026-05-18*
