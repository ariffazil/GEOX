# GEOX LEM Roadmap — Layer Architecture Toward Earth Foundation Model
## North Star: Aurora (Nature 2025) × GEOX Subsurface Domain

**Aurora Reference:** `https://www.nature.com/articles/s41586-025-09005-y`
**Status:** North Star Architecture — not yet reachable; requires H3–H7 prerequisites

***

## Why Aurora Is GEOX's North Star

Aurora demonstrates that a single foundation model can outperform multiple specialized operational systems across diverse Earth system domains — at orders of magnitude lower compute cost.

| Aurora Achievement | GEOX Equivalent |
|-------------------|-----------------|
| 1M+ hours pretraining data | Subsurface analog: millions of wells + seismic volumes |
| 1.3B parameters | GEOX target: ~100M–1B for subsurface backbone |
| 74–100% outperformance vs. operational systems | GEOX target: outperform human-led well log + seismic interpretation |
| Encoder → Processor → Decoder (3-part) | GEOX: Ingest → LEM Processor → CANON-9 Bounded Output |
| Fine-tuning adapts cheaply to downstream | GEOX: Few-shot adaptation to new basins/formations |

**Key insight from Aurora:** The same backbone handles air quality, ocean waves, cyclone tracks, and weather — different physical domains, same architecture. GEOX's LEM should handle well logs, seismic, EM, gravity, and pressure data with one backbone.

***

## Three-Part LEM Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GEOX LEM                                               │
│                                                         │
│  Encoder (Perceiver-based)                             │
│  → Ingest: logs (GR/RT/RHOB/NPHI), seismic (Vp/Vs),  │
│    EM (resistivity), gravity (density), pressure (MWD)  │
│  → Universal latent 3D representation: (depth × time ×  │
│    physical_property)                                   │
│  → Outputs: heterogeneous inputs → fixed-dim latent    │
│                                                         │
│  Processor (3D Swin Transformer)                       │
│  → Evolve latent forward in depth (proxy for time)     │
│  → Self-attention across depth intervals                │
│  → Multi-scale: patch-level → well-level → basin-level │
│  → Output: evolved latent at each depth horizon        │
│                                                         │
│  Decoder (Perceiver-based)                              │
│  → Universal latent → task-specific output              │
│  → Porosity head (regression)                          │
│  → Lithology head (classification)                      │
│  → Sw head (regression)                                │
│  → Pressure head (regression)                          │
│  → Sequence surface head (detection)                    │
└─────────────────────────────────────────────────────────┘
```

***

## Prerequisites Before LEM (Dependency Chain)

```
Phase 0: Data Infrastructure
  □ DRP synthetic core generation (GAN super-resolution for micro-CT)
    → Generates training data for WLFM backbone
  □ Federated well log database (>1,200 wells for WLFM pretraining)
  □ Seismic volume catalog with well ties

Phase 1: Well-Log Foundation (WLFM)
  → Stage 1: VQ tokenizer for subsurface logs
  → Stage 2: Transformer backbone with SCL pretraining
  → Stage 3: Fine-tune on porosity/lithology/sequence tasks
  → Output: cross-well invariant geological token embeddings

Phase 2: Physics-Informed Constraint (PINN)
  → L_total = L_data + λ × L_physics
  → L_physics = Archie + density-porosity + Gardner + Vp bounds
  → Output: CANON-9 bounded petrophysical estimates

Phase 3: LEM Encoder + Processor (Aurora Architecture)
  → Multi-modal encoder (Perceiver): logs + seismic + EM + pressure
  → 3D Swin Transformer processor
  → Universal latent across all subsurface physical domains

Phase 4: LEM Decoder + Tasks
  → Perceiver decoder
  → Multi-task heads: porosity, Sw, lithology, pressure, sequence
  → Fine-tuning protocol for new basins

Phase 5: LEM Production Integration
  → GEOX MCP tool: geox_lem_predict
  → Claim state: SEAL / QUALIFY / HOLD / VOID
  → ACRisk computation from epistemic + aleatoric uncertainty
```

***

## Critical Data Constraint

Aurora was trained on **1M+ hours** of atmospheric/oceanic data. This data abundance does not exist for subsurface.

**GEOX's data strategy:**
1. **Real wells:** Target 1,200+ for WLFM pretraining (achievable with federated data)
2. **DRP synthetic core:** GAN-generated micro-CT → training pairs for rock physics
3. **Seismic volumes:** Transfer learning from seismic foundation models (existing research)
4. **Physics constraints:** PINN provides implicit data augmentation via physics priors

**No shortcut.** Aurora-scale subsurface intelligence requires solving the subsurface data scarcity problem first.

***

## Near-Term H3 Actions (0–6 months)

| Action | Research Source | Output |
|--------|---------------|--------|
| Build `geox_core/engines/petrophysics/pinn.py` | PINN (Pothana & Ling 2025) | Physics-constrained Sw/porosity estimator |
| Add PINN mode to `geox_subsurface_generate_candidates` | PINN | Toggle between statistical and physics-constrained |
| Create VQ tokenizer prototype | WLFM | Tokenize GR/RT/RHOB/NPHI into geological tokens |
| Integrate WLFM token output into `geox_well_analyze_sequence` | WLFM | Latent lithology representation + cluster |
| Add contradiction_scan with WLFM failure mode flags | WLFM | B_cog penalty for thinly interbedded zones |
| Add seismic FM routing to `geox_seismic_analyze_volume` | PRISM + TGS + SAM-Fault | Offshore/salt/fault multi-model routing |
| Add SAM-style fault prompts to `geox_seismic_analyze_volume` | SAM-Fault (arxiv:2403.07802) | Zero-shot fault segmentation via prompt cues |

***

## Horizon Mapping

| Horizon | GEOX Action | Research Anchor |
|---------|-------------|----------------|
| H3 | PINN petrophysics engine | Pothana & Ling (2025) — EurekAlert |
| H3 | Async tasks (`task=True`) | FastMCP 3.0 SEP-1686 |
| H3 | Seismic FM routing | PRISM (SPE-222223) + SAM-Fault (arxiv:2403.07802) |
| H4 | WLFM well-log backbone | Qi et al. (2025) — arxiv:2509.18152 |
| H4 | VQ geological tokenizer | WLFM |
| H4 | TGS offshore seismic transfer | TGS Open-Source FM (Offshore Magazine 2025) |
| H5 | Foundation model tool integration | WLFM + PINN + PRISM |
| H6 | LEM encoder prototype | Aurora (Nature 2025) |
| H7 | LEM processor prototype | Aurora |
| H8 | LEM decoder + multi-task heads | Aurora |
| H9 | Federated data at scale | WLFM 1,200+ wells + TGS 50,000 km² seismic |

***

## Failure Mode Inheritance from Research

| Source | Finding | GEOX Implication |
|--------|---------|----------------|
| WLFM | Thinly interbedded → fragmented predictions | contradiction_scan must flag this before any lithology claim |
| WLFM | No uncertainty quantification | PINN should include epistemic uncertainty (dropout or ensemble) |
| Aurora | Pretraining is expensive (2.5 weeks on 32 A100s) | Start small: WLFM-400 before WLFM-1200 |
| PINN | Uncalibrated mineral model → unreliable | Require core calibration before PINN Sw claims |
| PRISM | OOD degradation: 15% on North Sea | Validate on local basin before using OOTB weights |
| PRISM | Salt flank horizon errors | Multi-attribute voting near salt boundaries |
| SAM-Fault | Dense fault networks → over-segmented | Multi-scale coherence voting |
| SAM-Fault | Salt-related faults → under-detected | Supplement with TGS salt model for offshore |
| TGS | Synthetic training bias | Cross-validate with real well ties before seismic-only claims |

***

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**

*Design artifact for GEOX LEM — Epoch 2026-05-18*
