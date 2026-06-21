# Physics9 Earth Witness — Multi-Physics Joint Inversion

> **Last verified:** 2026-06-21 (W13+ Phase C FORGE, commit `657b9eb0`)
> **Audience:** Geophysicists, federation architects, agent builders
> **Status:** `geox_joint_inversion` live (IRLS baseline). Bayesian upgrade deferred.

---

## What This Is

The **Physics9 Earth Witness** is the strategic centerpiece of GEOX as of the W2-W13+ FORGE. It fuses N independent geophysical modalities — seismic, gravity, magnetic, CSEM/MT, plus optional well priors — into **one Physics9State per cell**.

The output is **not** a map. It is a **governed state field** the arifOS kernel can trust.

```
              ┌────────────────────────────────────────┐
              │       EARTH — multi-physics reality     │
              └───────┬───────────┬───────────┬─────────┘
                      │           │           │
                      ▼           ▼           ▼
              ┌──────────┐ ┌────────┐ ┌──────────────┐
              │  SEISMIC │ │ GRAVITY│ │  CSEM / MT   │
              │  (Vp/Vs) │ │  (Δg)  │ │    (ρₑ)     │
              │     ρ    │ │   χ    │ │              │
              └────┬─────┘ └───┬────┘ └──────┬───────┘
                   │           │            │
                   ▼           ▼            ▼
              ┌────────────────────────────────────────┐
              │      GEOX JOINT INVERSION ENGINE       │
              │   (IRLS, Physics9-bounded, fusion)    │
              └────────────────────┬───────────────────┘
                                   │
                                   ▼
              ┌────────────────────────────────────────┐
              │      ONE Physics9State PER CELL        │
              │   (ρ, Vp, Vs, ρₑ, χ, k, P, T, φ)     │
              │      graded RAW or AAA · evidence-    │
              │      wrapped · godel-attested          │
              └────────────────────────────────────────┘
```

---

## The Physics9State — The 9-Dial Canon

Every Earth cell is fully described by 9 orthogonal physics parameters:

| Dial | Symbol | Units | Physical Meaning |
|------|--------|-------|------------------|
| **ρ** | density | kg/m³ | Bulk density (controls gravity + acoustic impedance) |
| **Vp** | compressional velocity | m/s | P-wave velocity (seismic, sonic logs) |
| **Vs** | shear velocity | m/s | S-wave velocity (seismic, dipole sonic) |
| **ρₑ** | electrical resistivity | Ω·m | Resistivity (CSEM, MT, induction logs) |
| **χ** | magnetic susceptibility | SI | Magnetization response (magnetic surveys) |
| **k** | thermal conductivity | W/m·K | Heat flow (geothermal) |
| **P** | pore pressure | Pa | Effective stress (drilling, geomechanics) |
| **T** | temperature | K | Subsurface thermal regime (maturation) |
| **φ** | porosity | 0–1 | Fluid storage capacity (reservoir quality) |

Plus anisotropic extensions (Thomsen ε, δ, γ) and attenuation (Qp, Qs) — but the **9 are the canonical irreducible**.

Earth-bound on each dial:

```
1000 ≤ ρ ≤ 5000    kg/m³
1500 ≤ Vp ≤ 6000   m/s
500  ≤ Vs ≤ 4000   m/s
0.1  ≤ ρₑ ≤ 1e7   Ω·m
0    ≤ χ ≤ 0.1     SI
0.1  ≤ k ≤ 10     W/m·K
1e5  ≤ P ≤ 200e6   Pa
250  ≤ T ≤ 600     K
0    ≤ φ ≤ 0.45
```

If any dial violates bounds → `grade = RAW` → `godel_wall.state = UNDECIDABLE_YET` → **never SEAL**.

---

## The Forward Models (one per modality)

| Modality | Forward Operator | Inputs | Output |
|----------|------------------|--------|--------|
| `seismic_impedance` | `Z = ρ · Vp` | (ρ, Vp) | Acoustic impedance (kg·m⁻²·s⁻¹) |
| `seismic_vpvs` | `Vp / Vs` | (Vp, Vs) | Vp/Vs ratio (dimensionless) |
| `gravity` | Point-mass Bouguer approximation | (ρ, depth) | Bouguer anomaly (mGal) |
| `magnetic` | Dipole TMI approximation | (χ, inclination, depth) | Total field anomaly (nT) |
| `mt_resistivity` | `ρₑ` directly | (ρₑ) | MT apparent resistivity (Ω·m) |

All forward operators are **deterministic, physics-bound, and explainable**. No neural networks in the forward path.

---

## The Inverse Solver (IRLS)

`geox_joint_inversion` solves the **inverse problem**: given N observations, find the Physics9State that minimizes the weighted L2 residual across all modalities.

```
minimize  Σ_i  w_i · (obs_i - forward_i(state))² / σ_i²
subject to  state.dial ∈ bounds[dial]   for each dial
```

**Algorithm:** Iteratively Reweighted Least-Squares (IRLS) with finite-difference gradient. Each iteration:
1. Compute per-modality residual.
2. Compute gradient of L2 loss w.r.t. each of the 9 dials.
3. Step state in negative-gradient direction.
4. Clip to Earth-bounds.
5. Re-evaluate.

Convergence: `residual_rms < tolerance` (default 1e-3) OR `max_iter` reached (default 50).

**Why IRLS, not full Bayesian?**
- IRLS is **deterministic** — every run on the same input gives the same output. No MCMC burn-in.
- IRLS is **fast** — 50 iterations × 9 dials × 5 modalities = 2250 forward evals. Sub-second per cell.
- IRLS is **explainable** — the residual per modality tells you which data disagrees.
- Bayesian upgrade (proper covariance propagation) is **deferred to W14+**.

---

## Biostrat Time-Facies Constraints

`geox_biostrat_constraint` enforces that the cell's Physics9State is consistent with the biostratigraphic zone at its age.

Built-in zone catalog:

| Zone | Age (Ma) | Environment | Admissible Materials |
|------|----------|-------------|---------------------|
| Quaternary_Alluvium | 0 – 2.6 | fluvial | Sandstone, Shale |
| Miocene_Reef | 5.3 – 23.0 | reef | Limestone, Dolomite |
| Cretaceous_Shale | 66 – 145 | marine_shelf | Shale, Limestone |
| Jurassic_Sabkha | 145 – 201 | sabkha | Anhydrite, Salt, Dolomite |
| Carboniferous_Coal | 298.9 – 358.9 | deltaic | Coal, Shale, Sandstone |
| Precambrian_Basement | 541 – 4000 | basement | Basement |

Zone matches if `age_top_ma ≤ age ≤ age_base_ma`. Returns consistency verdict (TRUE / FALSE) with reason notes.

---

## CSEM/MT 1D Forward — Filling the ρₑ Gap

`geox_mt_forward` computes 1D magnetotelluric apparent resistivity + phase via **Wait's recursion** through a layered Earth.

```python
result = await geox_mt_forward({
    "layers": [
        {"thickness_m": 500, "resistivity_ohm_m": 10},
        {"thickness_m": 200, "resistivity_ohm_m": 100},
        {"thickness_m": 1e9, "resistivity_ohm_m": 20},  # halfspace
    ],
    "frequencies_hz": [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
})
# Returns: frequencies_hz, apparent_resistivity_ohm_m, phase_deg
```

Per-frequency algorithm:
1. Start at bottom halfspace with intrinsic impedance.
2. Walk up through layers using Wait's recursion.
3. Compute `ρ_a(ω) = |Z(ω)|² / (ωμ₀)` and `φ(ω) = atan2(Im Z, Re Z)`.

**1D limitation:** real MT requires 2D/3D + static-shift correction. The 1D baseline is the gateway; 2D/3D upgrade is on the roadmap.

---

## PINN Seismic Inversion — 1D Baseline

`geox_seismic_inversion` recovers acoustic impedance from a 1D reflectivity series using a PINN-style physics prior:

1. **Recursive impedance:** `AI[i+1] = AI[i] · (1+R[i]) / (1-R[i])`
2. **Faust velocity:** `Vp = 2.288 · (Z · Rt)^(1/6)` (depth × resistivity prior)
3. **Gardner density:** `ρ ≈ 310 · Vp^0.25` (empirical)
4. **Re-synthesize AI** = ρ × Vp (Pinn-consistent)
5. **Residual** = observed AI vs predicted AI (per sample)

Enforces Physics9 bounds on every dial. Returns depth profile, Vp, ρ, AI, residual RMS.

The "PINN" element is the **soft prior**: the recovered AI is constrained to be consistent with Faust + Gardner physical relations, not just any recursive solution. Full PINN training (neural network that learns the constraint) is deferred to W14+.

---

## Output Envelope — What the Kernel Sees

```json
{
  "ok": true,
  "state": {
    "rho": 2350.0, "vp": 2950.0, "vs": 1680.0, "rho_e": 20.0,
    "chi": 0.0001, "k": 2.8, "P": 20000000.0, "T": 320.0, "phi": 0.25,
    "epsilon": 0.0, "delta": 0.0, "gamma": 0.0, "qp": 100.0, "qs": 50.0
  },
  "grade": "AAA",
  "residual_rms": 0.0023,
  "iterations": 12,
  "modality_count": 5,
  "observation_count": 5,
  "per_modality": {
    "seismic_impedance": [{"observed": 6.93e6, "predicted": 6.92e6, "relative_error": 0.0014}],
    "seismic_vpvs": [{"observed": 1.756, "predicted": 1.757, "relative_error": 0.0006}],
    "gravity": [...],
    "magnetic": [...],
    "mt_resistivity": [...]
  },
  "observation_hash": "sha256:...",
  "epistemic_provenance": {
    "rung": 5,
    "grounding": "joint_inversion_under_physics9_bounds",
    "method": "irls_with_bounded_clipping",
    "caveat": "Solver is IRLS with finite-difference gradient; weights are user-supplied. Not a substitute for production-grade Bayesian joint inversion (e.g. JIMAS, BERT)."
  },
  "godel_wall": {
    "state": "KNOWN",
    "reason": "Physics9 bounds satisfied (AAA grade)."
  }
}
```

---

## Constitutional Truth

GEOX **never** seals an inversion. It testifies via the envelope. The kernel adjudicates.

```
GEOX joint_inversion  →  Physics9State + envelope  →  arifOS 888 JUDGE
                                                       ↓
                                            SEAL / SABAR / HOLD / VOID
                                                       ↓
                                                    VAULT999
```

The Iron Law (Gap 5): lower rungs always beat higher rungs in contradiction. If the joint inversion produces a state that contradicts a lower-rung observation, the joint inversion must be **demoted** (not the observation).

---

## Why This Is Different from Foundation Models

Frontier foundation models (Prithvi-EO-2.0, TerraMind, Clay, Aurora) deliver **multimodal embeddings** but do not enforce physical consistency per cell. GEOX's joint inversion is **complementary**:

- **Foundation models** → fast pretraining, broad generalization, weak per-cell physical guarantees.
- **GEOX joint inversion** → deterministic, physics-bound per cell, slow (no GPU needed), strong guarantees.

The right pattern is:
1. Use FM for fast regional screening (which cells are interesting?).
2. Use GEOX joint inversion on the interesting cells (what does Earth physically say?).
3. Hand the verified state to the kernel.

`geox_prithvi_eo_inference` is the FM backing engine. `geox_joint_inversion` is the physics-bound witness. They are the same pipeline with different epistemic profiles.

---

## Files

- [`src/geox_core/physics/joint_inversion.py`](../src/geox_core/physics/joint_inversion.py) — IRLS solver
- [`src/geox_core/physics/state.py`](../src/geox_core/physics/state.py) — Physics9State canonical
- [`src/geox_core/engines/geophysics/mt_forward.py`](../src/geox_core/engines/geophysics/mt_forward.py) — Wait's recursion
- [`src/geox_core/engines/geophysics/biostrat_constraint.py`](../src/geox_core/engines/geophysics/biostrat_constraint.py) — time-facies
- [`src/geox_core/seismic/pinn_inversion.py`](../src/geox_core/seismic/pinn_inversion.py) — PINN baseline
- [`src/geox_mcp/tools/multi_physics.py`](../src/geox_mcp/tools/multi_physics.py) — MCP wrappers
- [`src/geox_mcp/tools/seismic_inversion.py`](../src/geox_mcp/tools/seismic_inversion.py) — PINN wrapper
- [`tests/test_phase_c_w13.py`](../tests/test_phase_c_w13.py) — 19 tests
- [`tests/test_pinn_w13.py`](../tests/test_pinn_w13.py) — 9 tests

---

## Future (W14+)

- **Bayesian joint inversion** — replace IRLS with proper MCMC covariance (e.g. `emcee`).
- **2D/3D MT forward** — beyond Wait's 1D recursion.
- **Full PINN training** — neural network that learns the constraint, not just enforces it.
- **Live Prithvi-EO-2.0 weights** — fuse FM embeddings as a soft prior on joint inversion.
- **Voxel-scale batch inversion** — currently per-cell; production needs hierarchical voxel hierarchy.

---

**DITEMPA BUKAN DIBEI — the cell is forged. The witness testifies. The kernel judges.**
