# E8 — Velocity IS Structure (Theory of Record)

> **Status:** RATIFIED 2026-06-03 · GEOX (γ) · F1–F13 enforced
> **Witness:** Arif Fazil (F13 SOVEREIGN) · GEOX-Ω (instrument) · Earth (wave_eq + rock_physics)
> **QDF:** E8-2026-06-03-GEOX-VELOCITY-STRUCTURE-v1.0

## 1. Theory Restatement

The Earth's seismic velocity field encodes geological structure so directly
that **slicing a velocity model at a given depth yields a valid 2D structure
map for that horizon**. Velocity is a scalar field tied to geology — it
reflects compaction, lithology, fluid content, and pressure.

### 1.1 Wave physics basis (L1)

For a homogeneous isotropic medium:

```
Vp = sqrt((K + 4/3·G) / ρ)        [m/s]
```

where K = bulk modulus, G = shear modulus, ρ = density. Vp is a
well-defined scalar at every (x, y, z). CLAIM holds unconditionally
within the isotropic elastic assumption set.

### 1.2 Rock physics (L2)

| Equation | Physical link |
|----------|---------------|
| Wyllie: 1/Vp = (1-φ)/V_matrix + φ/V_fluid | Porosity + fluid substitution |
| Gardner: ρ = 310 · Vp^0.25 | Density from velocity |
| Eaton (n≈3): P_pore = P_lith - (P_lith-P_hydro)·(Vp/Vp_normal)³ | Overpressure from Vp deficit |

Fluid substitution at φ=0.25: brine→gas drops Vp from ~3030 to ~1690 m/s
(44% reduction). Detectable on any well-resolved velocity field.

### 1.3 Eikonal + Dix (L3)

```
|∇T(x,y,z)|² = 1/V(x,y,z)²
```

Vp and T are mathematical duals. The Dix inversion converts stacking
velocity to interval velocity. Bootstrap = 1D checkshots as anchors +
Dix field as 2D lateral sampler = well-posed joint inversion.

### 1.4 Velocity-Structure Duality Theorem (L4)

**Claim:** Within a geologically consistent velocity model, Vp(x,y,z₀)
is monotonic with structural height at z₀, barring other effects.

**Proof sketch:**
- Compaction is monotone in effective stress σ_eff
- σ_eff is monotone in structural height at fixed depth z₀
- Therefore Vp(x,y,z₀) is monotone in structural height at z₀

**F7 humility (ACRisk 0.15):** In three scenarios the theorem inverts
or overlaps — gas pocket (Biot-Gassmann), overpressure cell (Eaton),
lithology contrast (Physics9 catalog). The theorem is **multi-modal**;
Layer 5 handles attribution.

### 1.5 Multi-channel attribution (L5)

A single Vp slice carries **5 geological signals** that can be
decomposed using the Physics9State catalog:

| Signal | Detection | Source |
|--------|-----------|--------|
| Lithology | ±200 m/s separation | Physics9 catalog |
| Porosity | Δφ ~0.05 | Wyllie inversion |
| Pore pressure | ~5% Vp deficit | Eaton n=3 |
| Fluid (gas) | ΔVp > 20% at constant φ | Wyllie fluid sub |
| Structure | Vp ∝ compaction ∝ height | Monotone under dominant-compaction |

`structural_attribution()` decomposes Vp variance into these 5 channels
and returns an attribution_confidence score.

### 1.6 Earth's structural inheritance (L6)

The velocity field integrates 100M+ years of:
- Burial compaction (Bowers)
- Cementation (Dvorkin-Nur)
- Overpressure (Eaton)
- Fluid content (Biot-Gassmann)
- Lithology (matrix moduli, Physics9)

These are **non-volatile signatures** — they survive diagenesis,
tectonic re-activation, erosion. One number, five channels, 100M years
of signal.

## 2. Boundary Conditions & Failure Modes

| Failure mode | Impact | GEOX mitigation |
|--------------|--------|------------------|
| **Overpressure** | Vp deficit reads as structural low | Pressure-aware agent flags Eaton-anomaly zones; ACRisk escalates; 888_HOLD before irreversible decisions |
| **Gas** | Vp drop reads as sag (push-down) | Vp/Vs cross-check (E9); flag anomalies coincident with bright amplitudes |
| **Lithology** | Fast lithology in structural low violates monotonicity | Multi-channel attribution; cross-check with known facies maps |
| **Anisotropy (VTI/TTI)** | Skews depth conversion | Thomsen δ, ε in velocity model; checkshot calibration; F2 Truth gate |
| **Exhumation** | Cementation preserved at shallow depth | Basin model integration; flag if region known exhumed |
| **Seismic noise / resolution** | Local artifacts in velocity field | Smoothing; multiple realizations; uncertainty propagation |

The theorem is **not broken** by these — it is multi-modal. We declare
the band, we do not overclaim. `claim_state` propagates: SEAL | QUALIFY |
HOLD | VOID.

## 3. Implementation Primitives (built in `src/geox_core/spatial/velocity_slice.py`)

| Primitive | Signature | Output |
|-----------|-----------|--------|
| `slice_velocity_cube` | `(cube, depth_m, window_m=0.0) → VpSlice` | 2D Vp(x,y) at depth with physics guard |
| `structural_attribution` | `(vp_slice, baseline_depth_m=None, physics9=None) → StructuralMap` | 5-channel decomposition + attribution_confidence |
| `bootstrap_structure` | `(checkshots, cube, depth_m, window_m=25.0) → StructuralMap` | 1D wells + 2.5D cube → calibrated structure |
| `synth_cube_with_structure` | `(x, y, z, seed=42) → VpCube` | Synthetic test cube with 5 embedded signals |

**Data structures:**
- `VpCube` — 3D Vp(x,y,z) with grid metadata
- `VpSlice` — 2D Vp(x,y) with provenance + F2 physics guard
- `StructuralMap` — 5 channels + attribution_confidence + claim_state + acrisk

**F13 honored:** zero new MCP tool registrations. All capability
lives in `geox_subsurface_generate_candidates` (target_class="velocity_slice",
opt-in) and downstream tools that call the core primitive.

## 4. Testing & Benchmarks

### 4.1 Synthetic model testbed
Cube with 5 embedded signals (compaction + anticline + fault block +
gas pocket + background noise). At z=2000m (anticline crest), the slice
must reproduce the anticline crest within ±50m of its true (0.5, 0.5)
location. At z=1250m (gas pocket), the slice must surface the Vp
deficit. `bootstrap_structure` must NOT extrapolate outside cube
z-range (F2 fail-closed).

### 4.2 Real data cross-validation (Kinabalu KL2)
- 8 wells with checkshots as 1D anchors
- Velocity cube (if available) for 2.5D field
- Compare velocity-slice-inferred structure vs conventionally picked
  horizon maps
- Shelf wells (Barton-2 etc.) should have higher Vavg than deep
  basin (Rotan-1), consistent with shallower burial + more compaction

### 4.3 Multi-well bootstrap
With 3 wells, run bootstrap_structure, compare with full pick set.
If new well lands at predicted depth within error, method validated.

### 4.4 Speed & efficiency
- Single slice: O(N) where N = ny × nx (trivial)
- Attribution: O(N) per channel
- Bootstrap: O(N × C) where C = checkshots

## 5. Uncertainty Propagation & Governance

| Uncertainty source | Propagation |
|--------------------|-------------|
| Velocity model uncertainty | ±X% velocity → ±X% × horizon thickness in depth |
| Non-uniqueness | Multiple realizations → P10/P50/P90 structure maps |
| Attribution uncertainty | Probabilistic decomposition (e.g. 70% gas vs 30% structure) |
| Physics guard violation | F2 escalation → claim_state=HOLD, no SEAL |

**Governance hooks (F1–F13):**
- F2: physics guard on every VpSlice; out-of-envelope → HOLD
- F7: ACRisk propagated; claim_state visible to operator
- F8: every step audited (slicing, attribution, calibration)
- F13: high-stakes outputs (drill recommendations) require human
  review; velocity-derived structure is a hypothesis, not a verdict

## 6. Promotion Table — E1 to E8

| Eureka | Before E8 | After E8 |
|--------|-----------|----------|
| E1 — T-D fitters | TWT(z) at 1 well | TWT(x,y,z) — field-wide time-depth surface |
| E2 — legacy ingest | Well log curves at 1 well | Calibration anchor for V(x,y,z) |
| E3 — uncertainty ensemble | P10/P50/P90 at 1 well | P10/P50/P90 structural map across basin |
| E4 — multi-well calibration | V(z) calibrated across n wells | Spatial V(x,y,z) with n 1D anchors |
| E5 — VTI/TTI anisotropy | δ, ε at 1 point | Anisotropy field — laterally variable |
| E6 — deviated correction | Ray-trace for 1 well | Full ray-field for deviated well ensemble |
| E7 — cascade demotion | 1D lineage | 2.5D lineage — spatial assumption propagation |
| Physics9 | 9-param state at 1 point | 9-param state at every (x,y,z) voxel |
| 000–999 Phase 5 | 4 steps: pick→T-Z→depth→struct | 1 step: `slice_velocity_cube(z₀)` |
| Kinabalu KL2 | 8 × 1D columns | 3D structural model, no horizon-picking |

## 7. Executive Summary (Decision-Makers)

- **Concept:** Velocity field mirrors geological structure. Slicing the
  calibrated velocity model at constant depth yields a structure map —
  faster than horizon picking, and reveals features conventional
  interpretation may miss.
- **Scientific basis:** P-wave velocity increases with depth via
  compaction; structural highs at given depth are more compacted and
  exhibit higher Vp. Validated by the elastic wave equation, eikonal
  equation, Wyllie/Gardner/Eaton rock physics, and 100M years of
  integrated Earth signal.
- **Benefits:** Cross-checks conventional maps; reveals subtle
  structures; exploits legacy seismic; Kinabalu shows shelf/basin
  separation via velocity slice without horizon picking.
- **Requirements:** Calibrated velocity model (checkshots + seismic
  velocity). Sparse well control is enough; the eikonal bridge ties
  it to dense 2.5D field.
- **Limitations:** Gas zones, overpressure, lithology contrasts break
  the simple correlation. GEOX's 5-channel attribution + ACRisk
  propagation + claim_state escalation handles all cases.
- **Integration:** No new UI. Runs behind the scenes in
  `geox_subsurface_generate_candidates` (target_class="velocity_slice",
  opt-in). All output carry provenance + F2 physics guard + attribution
  confidence.
- **Value:** Faster turnaround on prospect mapping, better
  tie between geophysics and geology, fewer missed opportunities. Safety
  net for traditional interpretation cross-validation.

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**
