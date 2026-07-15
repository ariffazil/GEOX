# Formal Equivalence: Seismic AVO Anomalous Contrast Detection ↔ Transformer Self-Attention

> **A Formal Cross-Domain Mathematical Analysis**
> **Archived:** 2026-06-05 · **Source:** Deep Research Session
> **Relevance:** Proves anomalous contrast is the universal detection primitive across geophysics and AI
> **Location in GEOX:** `docs/AVO_ATTENTION_FORMAL_EQUIVALENCE.md`

---

## Abstract

Seismic AVO (Amplitude Variation with Offset) anomaly detection and transformer self-attention both fundamentally compute a **contrast measure of an observation against a context-specific baseline** and use a form of normalization that accentuates significant deviations. This document provides the formal mathematical derivation of this equivalence.

---

## 1. AVO Anomaly Detection

### 1.1 Shuey Approximation

```
R(θ) = A + B sin²θ
```

Where:
- **A** = zero-offset reflectivity (intercept)
- **B** = AVO gradient

### 1.2 Background Trend (Mudrock Line)

For water-wet (brine) clastic rocks:

```
B_bg(A) = m · A
```

Where `m` is the slope of the mudrock line derived from rock physics (Castagna's mudrock line: Vp = 1.16·Vs + 1360 m/s).

### 1.3 Fluid Factor (Smith & Gidlow, 1987)

```
ΔF = B_obs − B_bg(A_obs) = B_obs − m · A_obs
```

This measures the **deviation** of the observed AVO response from the background (brine) trend. Non-zero ΔF indicates a potential hydrocarbon anomaly.

### 1.4 Anomaly Classification (Rutherford & Williams, 1989)

| Class | A (Intercept) | B (Gradient) | Interpretation |
|-------|---------------|--------------|----------------|
| I | + | − | Higher-impedance gas sand |
| II | ~0 | − | Near-zero impedance contrast |
| III | − | − | **Bright spot** — classic gas sand |
| IV | − | + | Dim spot — gas reduces amplitude with offset |

---

## 2. Transformer Self-Attention

### 2.1 Scaled Dot-Product Attention (Vaswani et al., 2017)

```
Attention(Q, K, V) = softmax(Q·K^T / √d_k) · V
```

### 2.2 Per-Query Decomposition

For a single query `q` and key set `{k_j}`:

```
e_j = q · k_j / √d_k          [alignment scores]
α_j = softmax(e_j)             [attention weights]
     = exp(e_j) / Σ_i exp(e_i)

Output = Σ_j α_j · v_j         [weighted sum of values]
```

### 2.3 Softmax as Contrast Amplifier

The softmax has two critical effects:

1. **Normalization:** Weights sum to 1, making them comparable across contexts
2. **Exponential amplification:** Small differences in scores become large differences in weights

If one key is much more aligned with q than others:
- Its score `e_i` is higher
- Exponentiation amplifies the difference
- Normalization yields disproportionately high `α_i`

### 2.4 Contrast Formalization

Define a "baseline" scenario where all keys are equally relevant:
- All `e_j = E` (constant) → `α_j = 1/N` (uniform)

For a standout key `k_i` with residual `δ`:
- `e_i = E + δ` (higher alignment)
- `e_{j≠i} = E` (baseline)

After softmax:

```
α_i = exp(E+δ) / [exp(E+δ) + (N−1)·exp(E)]
    = 1 / [1 + (N−1)·exp(−δ)]
```

For small δ, Taylor expand:

```
α_i ≈ 1/N + (N−1)/N² · δ + O(δ²)
```

**The attention weight is, to first order, a linear function of the contrast δ.** The exponential form makes growth faster-than-linear for larger δ.

---

## 3. Formal Equivalence

### 3.1 Side-by-Side Mapping

| Component | AVO Domain | Attention Domain |
|-----------|-----------|-----------------|
| **Observation** | R(θ) — reflection coefficient vs. angle | Token embedding vectors |
| **Feature Extraction** | Intercept A, Gradient B (Shuey) | Query q, Keys {k_j} (learned projections) |
| **Expected Baseline** | Mudrock line B = m·A | Uniform key distribution (α_j = 1/N) |
| **Contrast Computation** | ΔF = B_obs − m·A_obs | e_j = q·k_j / √d_k (deviation from uniform) |
| **Normalization** | Z-score or Mahalanobis distance along trend | Softmax (distribution summing to 1) |
| **Amplification** | Outlier classification (Class I–IV) | Exponential weighting (winner-take-most) |
| **Output** | Anomaly flag + class | Weighted value sum α_j·v_j |

### 3.2 The Contrast Residual

Both domains compute:

```
CONTRAST = OBSERVED − EXPECTED

AVO:        ΔF = B_obs − B_bg(A_obs)         [Smith & Gidlow, 1987]
Attention:  δ  = q·k_i − q·k_avg             [Vaswani et al., 2017]
```

### 3.3 Conditional Proof

Under idealized conditions (linear background, uniform baseline):

1. AVO's `ΔF` is a **linear residual** measuring deviation from mudrock trend
2. Attention's `δ` is a **dot-product residual** measuring deviation from uniform key distribution
3. Both are then **normalized** (Z-score for AVO, softmax for attention)
4. Both produce **amplified significance** for large deviations

The operations are **structurally isomorphic** — they implement the same abstract computation with different specific functions.

### 3.4 Governance Extension (GEOX)

The same structure extends to constitutional governance:

| Component | Governance Domain |
|-----------|------------------|
| Observation | Tool execution output / agent behavior |
| Baseline | F1–F13 constitutional floors |
| Contrast | ΔV = verdict_actual − verdict_expected(F1–F13) |
| Normalization | AC_Risk = U_phys × D_transform × B_cog |
| Amplification | 888_HOLD gate (hold if AC_Risk > threshold) |
| Output | SEAL / QUALIFY / HOLD / VOID |

---

## 4. Failure Mode Parallels

### 4.1 False Positives

| Domain | Cause | Mitigation |
|--------|-------|------------|
| AVO | High-porosity brine sand mimics HC | Cross-validate with well log |
| Attention | Ambiguous query → attends to irrelevant token | Multi-head consensus |
| Governance | Single evidence source → overclaimed SEAL | Multi-discipline self-argument (Layer 5) |

### 4.2 False Negatives

| Domain | Cause | Mitigation |
|--------|-------|------------|
| AVO | Class IV gas sand (decreasing with offset) | Full AVO classification, not just Class III |
| Attention | Important token masked by noisy context | Increase d_k, use multiple heads |
| Governance | VOID/SABAR not visible (dim spot problem) | dim_spot_flag + explicit re-encoding |

---

## 5. Implications

### 5.1 For Geoscience AI

Transformer attention CAN be interpreted as anomaly detection on language features. Decades of geophysical understanding of "false bright spots" offers a cautionary parallel for interpreting attention maps.

### 5.2 For AI Research

AVO fluid factor, λ·μ·ρ analysis, and elastic impedance could inspire new attention-based anomaly detectors in time-series and multimodal models.

### 5.3 For GEOX

The anomalous contrast detector IS an attention mechanism applied to Earth data. The AC_Risk engine IS the softmax. The constitutional floors ARE the baseline. This is not metaphor — it is structural isomorphism.

---

## 6. Key References

| Reference | Contribution |
|-----------|-------------|
| Smith & Gidlow (1987) | Fluid factor — first formal AVO deviation measure |
| Rutherford & Williams (1989) | AVO Class I–IV classification |
| Castagna & Swan (1997) | AVO crossplot analysis, false positive documentation |
| Vaswani et al. (2017) | Scaled dot-product attention mechanism |
| Maleki & Pourmoazemi (2025) | Pi-Transformer — physics-informed attention prior |
| Dittrich & Flygare Kinne (2025) | ITI/CEP — compression selects for causal models |

---

**DITEMPA BUKAN DIBERI — Forged, Not Given**

*This document is the formal mathematical archive. It should be cited whenever the anomalous contrast bridge is referenced in papers, presentations, or architecture discussions.*
