# WLFM Geological Vocabulary — GEOX Well-Log Foundation Model
## VQ Token Codebook Reference

**Source:** Qi et al. (2025). WLFM: A Well-Logs Foundation Model for Multi-Task and Cross-Well Geological Interpretation. arxiv:2509.18152.
**Status:** Research Reference — GEOX integration H4+

***

## Codebook Architecture

WLFM uses Vector-Quantized (VQ) tokenization to convert multi-curve log patches into discrete geological tokens.

```
Input: multi-curve log patch (C channels × L depth samples)
  ↓ Domain-aware encoder
  (curve-type embedding + relative-depth positional encoding)
  ↓ Vector Quantization
  → Discrete geological token from learned codebook E = {e_k, k=1..K}
```

**Codebook size:** K geological tokens (varies by model scale: WLFM-400, WLFM-600, WLFM-1200)

***

## Emergent Token Clusters (WLFM-1200)

WLFM produces emergent layer-awareness without explicit lithology labels. t-SNE visualization of token embeddings reveals distinct clusters aligned with lithofacies.

| Cluster | Lithofacies | GR Motif Signature | WLFM Token |
|---------|-------------|-------------------|------------|
| 1 | Massive sand | Blocky low-GR | `GEOL_SAND_BLOCKY` |
| 2 | Laminated sand-shale | Serrated GR | `GEOL_LAMINATED` |
| 3 | Shoreface | Coarsening-upward | `GEOL_SHF_COARSE_UP` |
| 4 | Mudstone | High-GR uniform | `GEOL_MUDSTONE` |
| 5 | Carbonate | Vp > 5.5 km/s, high AI | `GEOL_CARB` |
| 6 | Coal | Very low GR, low density | `GEOL_COAL` |

**Unsupervised clustering performance:** ARI = 0.78, Purity = 82.3% vs. lithofacies labels.

***

## Token-to-Geology Mapping Rules

These are emergent clusters — not hard rules. Always apply `geox_evidence_contradiction_scan`.

### GR Motif → WLFM Token Mapping

```
GR blocky low-GR (sharp top, sharp base) → GEOL_SAND_BLOCKY
  Evidence: clean sand, uniform energy, channel fill or shelf sand
  Confidence: HIGH if RT > 10 Ωm AND VCL < 0.15

GR serrated GR (variable, interbedded) → GEOL_LAMINATED
  Evidence: turbidite or delta front interbedding
  Confidence: MEDIUM — thinly interbedded prone to WLFM fragmentation failure

GR coarsening-upward (increasing energy) → GEOL_SHF_COARSE_UP
  Evidence: progradation, forced regression, shoreface
  Confidence: MEDIUM — needs multi-well correlation to confirm

GR fining-upward (decreasing energy) → GEOL_FINING_UP
  Evidence: transgression, channel abandonment, delta lobe switching
  Confidence: MEDIUM — same as above

GR high uniform (>75 API) → GEOL_MUDSTONE
  Evidence: condensed section, deepwater, maximum flooding surface nearby
  Confidence: HIGH if SP < -40mV AND RT < 5 Ωm

Vp > 5.5 km/s + high AI → GEOL_CARB
  Evidence: carbonate platform, limestone or dolomite
  Confidence: HIGH — CANON-9 physical bound (Vp carbonate range 3.5-7.0 km/s)
```

***

## Cross-Well Invariance (SCL — Stratigraphy-Aware Contrastive Learning)

WLFM's key property: tokens from the same stratigraphic interval form tight clusters **regardless of well identity**.

```
Same-layer positive pairs (from different wells):
  → WLFM token embeddings align in latent space
  → Enables cross-well lithology transfer without re-calibration
```

**Implication for GEOX:** Cross-well correlation using WLFM tokens should be more robust than raw curve matching.

***

## Limitations and Failure Modes

| Failure Mode | Symptom | Mitigation |
|-------------|---------|-----------|
| Thinly interbedded formations | Fragmented lithology predictions, poor continuity | Apply contradiction_scan; downweight B_cog |
| Noisy intervals | Erratic token assignment | Increase QC threshold before running foundation model |
| Shallow/ultra-deep | Systematic value offsets | Check depth range; flag if <500m or >5000m |
| Casing/sensor transitions | Artificial boundaries in log | Mask with CAL curve before foundation model run |
| Missing curves | WLFM modality dropout handles this | Use `geox_data_qc_bundle` to confirm curve completeness |

***

## GEOX Integration Points

| GEOX Layer | Integration |
|-----------|-----------|
| `geox_well_analyze_sequence` | WLFM token output as latent lithology representation |
| `geox_section_interpret_correlation` | Cross-well WLFM token invariance for correlation confidence |
| `geox_evidence_contradiction_scan` | B_cog penalty if thinly interbedded or noisy interval |
| `resources/ontology/wlfm_vocabulary.md` | This file — canonical token reference |

***

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
