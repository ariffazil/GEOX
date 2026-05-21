# Seismic Foundation Models — Vocabulary Reference
## PRISM · TGS · SAM-Fault — Canonical Research Anchors

**Seal:** DITEMPA BUKAN DIBERI

---

## Model Registry

### PRISM — Seismic Foundation Model
- **Full name:** PRISM: A Foundation Model for Seismic Data Processing and Interpretation
- **Citation:** Alwon (2025). SPE Digital Science Conference. `SPE-222223.MS`
- **URL:** `https://www.onepetro.org/content/SPE/SPE-222223.MS`
- **Model size:** ~1B parameters (PRISM-1B)
- **Training data:** Multi-basin 3D seismic volumes (unspecified volume)
- **License:** SPE digital (research use)
- **Benchmark datasets:** SPE salt body, TGS Salt Nexus, Penobscot 3D

| Task | PRISM-1B (zero-shot) | PRISM-Finetune |
|------|----------------------|----------------|
| Salt body Dice | 89.3% | 91.7% |
| Fault segmentation F1 | 76.1% | 79.4% |
| Horizon tracking MAE | 2.1 samples | 1.8 samples |

**Known failure modes:**
- OOD (North Sea): 15% degradation vs in-distribution
- Salt flank horizon errors: require multi-attribute voting
- Thin faults (< 10 samples): supplement with structural discontinuity attributes

---

### TGS Seismic Foundation Model
- **Full name:** TGS Open-Source Seismic Foundation Model
- **Citation:** TGS (2025). Offshore Magazine.
- **URL:** `https://www.offshore-magazine.com/article/tgs-launches-open-source-seismic-foundation-model-for-offshore-exploration`
- **Model size:** 650M parameters
- **Training data:** 50,000+ km² of 3D offshore seismic
- **License:** Open-source (research); commercial license required for production
- **Target tasks:** Salt interpretation, fault analysis, horizon picking
- **Benchmark:** 23% improvement over incumbent Gulf of Mexico workflow

**Known failure modes:**
- Synthetic training bias: cross-validate with real well ties before seismic-only claims
- Offshore-specific: performance on onshore data not validated

---

### SAM-Fault — Segment Anything for Faults
- **Full name:** SAM-Fault: Zero-Shot Semantic Segmentation of Fault Surfaces from Seismic Data
- **Citation:** Guo et al. (2024). `arxiv:2403.07802`
- **URL:** `https://arxiv.org/abs/2403.07802`
- **Model size:** ~600M parameters (SAM backbone + fault head)
- **Training data:** Three-basin seismic datasets with fault labels
- **License:** Apache 2.0 (research)
- **Zero-shot:** Tested on 3 held-out basins without fine-tuning

| Task | SAM-Fault (zero-shot) | Fully-Supervised U-Net |
|------|----------------------|------------------------|
| Fault IoU | 61.3% | 71.2% |
| Fault F1 | 67.8% | 75.6% |
| Fine-tuning gain | +8.1% IoU (100 labels) | N/A |

**Known failure modes:**
- Dense fault networks → over-segmented
- Salt-related faults → under-detected (supplement with TGS salt model)
- Subtle faults (< 2px throw) → use discontinuity attributes as proxy

---

## Vocabulary

| Term | Definition | GEOX Context |
|------|-----------|--------------|
| **Masked Patch Modeling (MPM)** | Self-supervised pretraining: mask random seismic patches and recover them | PRISM Stage 2 |
| **Seismo-stratigraphic Contrastive Learning (SsCL)** | Cross-patch contrastive: same-facies positive pairs | PRISM Stage 2, analogous to WLFM SCL |
| **Fault IoU** | Intersection-over-union for fault surface pixels | SAM-Fault primary metric |
| **Salt Dice** | Dice coefficient for salt body segmentation | PRISM primary offshore metric |
| **Horizon MAE** | Mean absolute error in samples for tracked horizons | PRISM horizon tracking metric |
| **OOD degradation** | Performance gap between in-distribution and out-of-distribution basins | PRISM failure mode |
| **Zero-shot transfer** | Apply pretrained model to unseen basin without fine-tuning | SAM-Fault core capability |
| **Prompt engineering (fault)** | Dip angle + azimuth + coherence cues as SAM fault prompts | SAM-Fault inference |
| **Multi-scale coherence voting** | Ensemble of coherence volumes at different windows to resolve dense faults | GEOX supplement for SAM-Fault |
| **Multi-attribute voting** | Combine amplitude, phase, curvature attributes for salt boundary | GEOX supplement for PRISM salt flank |

---

## Cross-Model Routing

```
geox_seismic_analyze_volume:
  IF offshore_basin AND salt_present:
    → TGS salt model (primary) + PRISM salt (secondary)
    → claim_limit: TGS 23% improvement floor

  IF fault_network_complexity > 0.7:
    → SAM-Fault (zero-shot) + PRISM fault ensemble
    → claim_limit: SAM IoU 61.3% zero-shot; over-segmented at high density

  IF horizon_continuity < 0.5:
    → PRISM horizon tracker
    → claim_limit: MAE 2.1 samples; salt flanks require multi-attribute voting

  IF out_of_distribution_basin:
    → 888_HOLD: PRISM OOD 15% degradation — local calibration required

  IF onshore_basin AND no_fine_tuning:
    → SAM-Fault zero-shot (generic seismic)
    → claim_limit: IoU 61.3% — dense fault networks need coherence voting
```

---

## Claim State Vocabulary

| Claim Level | Trigger Condition | Required Backing |
|-------------|-----------------|-----------------|
| **SEAL** | Local well tie + FM fine-tuned on basin | TGS benchmark + in-basin validation |
| **QUALIFY** | FM fine-tuned on adjacent basin | PRISM OOD 15% degradation acknowledged |
| **SABAR** | FM zero-shot, OOD signal detected | OOD claim_limit stated explicitly |
| **HOLD** | Seismic-only, no well tie, OOD confirmed | 888_HOLD: local calibration missing |
| **VOID** | Conflicting FM outputs | contradiction_scan across PRISM + SAM-Fault |

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
