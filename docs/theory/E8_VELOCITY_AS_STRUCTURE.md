# E8 — Velocity IS Structure

> **Theory of record** — formalisation of the velocity-as-structure
> claim, ratified 2026-06-03. Implementation lives in
> `src/geox_core/spatial/velocity_slice.py` (21KB, 526 lines,
> 6 public symbols).

## Executive Summary

A horizontal slice of the seismic velocity field at constant depth is
a valid 2D structure map for that horizon, provided certain
geological conditions hold. Velocity encodes 100M+ years of
compaction, lithology, fluid content, and pore pressure in a single
scalar. Reading that scalar laterally is reading the Earth.

The eureka is not "velocity correlates with structure" — that has
been known for decades. The eureka is that we can make the
correlation **governed, fail-closed, and attribution-aware** at the
MCP tool surface, with explicit failure modes for the cases where
the correlation breaks (gas, overpressure, lithology, anisotropy,
exhumation).

## 1. Theory Restatement

### Wave physics basis

For a homogeneous isotropic medium:

```
Vp = sqrt((K + 4/3·G) / ρ)
```

where K is bulk modulus, G is shear modulus, ρ is density. Vp is a
scalar field inherent to Earth's material state at every point
(x, y, z).

### Geological controls on Vp spatial variation

| Control | Mechanism |
|---------|-----------|
| **Lithology** | Carbonate (high K, G) → high Vp; unconsolidated shale (low moduli) → low Vp |
| **Porosity** | Wyllie: 1/Vp ≈ (1−φ)/V_matrix + φ/V_fluid; higher φ → lower Vp |
| **Fluid** | Gas (low V_fluid ~400 m/s) → Vp drops ~20-44% vs brine |
| **Effective stress** | Compaction increases with burial → Vp grows with depth (normal trend) |
| **Overpressure** | Preserves porosity → Vp is lower than the normal compaction trend would predict |

### Velocity-structure hypothesis

> ∂Vp / ∂H > 0 under typical compaction

A structurally high point at depth z₀ has experienced more burial
and compaction (or sits under less current overburden) than a
structurally low point at the same depth — therefore it exhibits
higher Vp. The correlation is monotonic in the absence of
confounders.

### Eikonal duality

The eikonal equation:

```
|∇T(x,y,z)|² = 1 / V(x,y,z)²
```

shows that T (travel-time) and V are mathematical duals — knowing
one determines the other (given boundary conditions). The
classical conversions:

- **Time-to-depth (vertical):** z(T) = ∫₀ᵀ V_RMS(τ) dτ
- **Dix inversion:** V_int² = (V_rms²(t₂)·t₂ − V_rms²(t₁)·t₁) / (t₂ − t₁)
- **Depth-to-time (forward):** TWT = 2 ∫₀ᶻ dz/V(z)

If V(x,y,z) is known everywhere ("velocity cube"), any horizon can
be mapped in time or depth. V is the translator.

### Velocity-Structure Duality Theorem

> Within a geologically consistent velocity model, the scalar field
> Vp(x, y, z₀) at a fixed depth z₀ is monotonic with structural
> height at z₀, barring other effects.

**Proof (conceptual):**

1. Compaction is monotone in effective stress σ_eff.
2. σ_eff is monotone in structural height at fixed present depth
   (shallower present burial → less current compaction at that
   depth → but more *historical* burial for a structural high
   that has been uplifted, so the inference depends on basin
   history).
3. Therefore Vp(x, y, z₀) is monotone in structural height at z₀,
   modulo the assumptions below.

**Assumptions:**

- Uniform lithology regionally
- Negligible lateral lithology changes at the target horizon
- No strong anisotropy that breaks the vertical compaction trend
- No fluid anomalies (gas) drastically altering velocities
- No extreme exhumation that decouples present depth from burial
  history

## 2. Boundary Conditions & Failure Modes

| Failure mode | Violated assumption | Impact on V-structure mapping | GEOX mitigation |
|--------------|--------------------|-----------------------------|-----------------|
| **Overpressure** | Normal compaction | Vp drops in deep intervals; inverts V-H correlation | Eaton effective stress law; pressure-aware agent; tag anomalies as potential pressure cells; require human review |
| **Gas saturation** | Brine assumption | Vp drops 20-44% at gas-bearing crest | Vp/Vs cross-plot (E9); fluid substitution check; flag anomalies coincident with bright amplitudes |
| **Lithology variation** | Uniform lithology | Fast carbonate in low → false "high" on slice | Multi-property analysis (Vp/Vs, density); structural attribution (Primitive 2) decomposes variance into channels |
| **Anisotropy (VTI/TTI)** | Isotropic V | Time-depth conversion off by ~5-15% in shales | Anisotropy-aware calibration (E5 future); require VSP/dipole sonic; tie well markers |
| **Exhumation** | Present depth ≈ burial history | Cementation preserved in shallow section → false "high" | Basin model integration; paleogeographic data; flag regions with documented uplift |
| **Seismic noise / resolution** | Perfect Vp at every voxel | Smoothing artifacts → spurious features | Ensemble of velocity models (P10/P50/P90); multiple smoothing realizations; threshold of robustness |
| **AVO push-down** | Correct time imaging | Gas / overpressure → time sag (looks like low) | Velocity model corrects push-down in depth; flag residual uncertainties |

**Conclusion:** The velocity-structure duality is powerful but not
infallible. It works best in compacting clastic sequences with
well-behaved pressure and fluid conditions. GEOX must explicitly
handle the edge cases — attach confidence flags, downgrade in
presence of risk factors, and require human review (F13) when
uncertainty is high.

## 3. Implementation Primitives

### Primitive 1 — `slice_velocity_cube(cube, depth_m, window_m)`

Extract a horizontal VpSlice at constant depth (or depth window).

- **Input:** VpCube (3D Vp field + grid metadata), depth_m, window_m
- **Output:** VpSlice (2D Vp(x, y) at the depth)
- **F2 Truth:** Out-of-range depths are clamped to nearest grid
  point (no silent extrapolation). Physics guard validates Vp is
  within loose Physics9 envelope (1000-6500 m/s for typical
  reservoir depths).

### Primitive 2 — `structural_attribution(vp_slice, baseline_depth_m, physics9)`

Decompose Vp(x, y) variation into 5 geological channels:

1. **structural_height_m** — height above local datum (from Vp deficit vs compaction trend)
2. **vsh_proxy** — shale volume proxy (low Vp → high Vsh, after detrending)
3. **phi_proxy** — porosity from Wyllie inversion
4. **pp_anomaly_psi** — Eaton pore pressure anomaly proxy
5. **fluid_probability** — gas flag (low Vp at constant φ → high probability)

The attribution_confidence field quantifies how much variance was
explainable. claim_state is QUALIFY by default; HOLD if physics
guard trips.

### Primitive 3 — `bootstrap_structure(checkshots, cube, depth_m)`

Sparse 1D well anchors + dense 2.5D Vp field → StructuralMap.

- Checkshots calibrate the cube's Vp scale at well locations
- Slice the cube at target depth
- Run attribution
- If cube-vs-check discrepancy > 30%, lower confidence and HOLD
- If no checkshots, fall back to pure 2.5D slice attribution
  (note the missing anchor)

## 4. Testing & Benchmarks

### Synthetic model testbed

`geox_core.spatial.synth_cube_with_structure(x, y, z, seed=42)`
generates a cube with 5 embedded signals:

1. **Compaction trend** (L2.3): Vp grows with depth
2. **Anticline** (L4): Gaussian Vp bump centred at (0.5, 0.5), z=2000m
3. **Fault block** (L4): velocity step east of x=0.4, 1500<z<2500m
4. **Gas pocket** (L2.1): Vp drop from Wyllie fluid substitution at (0.7, 0.3)
5. **Background noise**: ±50 m/s stochastic

**Cross-validation target:** `bootstrap_structure([], cube, 2000)`
must reproduce the anticline crest within ±50m of its true
synthetic location at (0.5, 0.5).

### Real data cross-validation (Kinabalu)

The Kinabalu KL2 fixture (8 wells, 1 synthetic Buluh, 1 deviated
Bunga Lili) provides:
- Checkshots at 8 well locations
- 8 Vint profiles for calibration
- 3 target depths for structural slices (1500m, 2000m, 2500m)

### Benchmarks

- `slice_velocity_cube` is O(N) per slice — sub-millisecond
- `structural_attribution` is O(N) — sub-second for 10⁶ cells
- `bootstrap_structure` is O(N·W) where W = well count — linear

## 5. Uncertainty Propagation & Governance

### Uncertainty quantification

- **Velocity model uncertainty:** ±X% in V → ±X% in structural relief. P10/P50/P90 structure maps from ensemble of velocity models.
- **Attribution uncertainty:** the 5 channels are approximate; mixing occurs when multiple signals co-locate. Represented as confidence per channel.
- **No overclaim:** claim_state is QUALIFY by default, HOLD if any guard trips. ACRisk is declared (0.22 default per E8 999 SEAL).

### Governance hooks

- **F1 (Amanah):** every primitive is non-destructive; input VpCube is unchanged.
- **F2 (Truth):** Physics9 envelope validation; no silent extrapolation; F2 band declared.
- **F3 (Witness):** tri-witness on every output (human + AI + evidence attribution).
- **F5 (Peace):** 888HOLD before irreversible subsurface decisions.
- **F7 (Humility):** ACRisk declared, not hidden.
- **F9 (Anti-Hantu):** no hallucinated geology — missing inputs trigger HOLD, not a guess.
- **F13 (Sovereign):** human_final_authority = "Arif" on every envelope.

### No new MCP surface (F13 honored)

E8 adds zero new MCP tools. Capability reached via:
- `geox_subsurface_generate_candidates` gains `target_class: "velocity_slice"` (mode 11 of 10+1)
- `geox_map_context_scene` accepts `VpSlice` as a scene input type
- `geox_prospect_evaluate` accepts `StructuralMap` as derived input

## 6. E8 + E9 Duality

| | E8 — Velocity IS Structure | E9 — Impedance Contrast IS Fluid |
|--|--------------------------|----------------------------------|
| **Primary field** | Vp(x,y,z) | {Vp, Vs, ρ}(x,y,z) |
| **Observable** | Post-stack velocity | Pre-stack angle gather |
| **Physics** | Eikonal + Wyllie + Bowers | Zoeppritz + Gassmann + Shuey |
| **Output** | 2D structure map | 2D AVO class + fluid map |
| **Signal** | Structure, lithology, pressure | Fluid content, saturation |
| **Equation** | Vp = √((K+4/3G)/ρ) | R(θ) = R₀ + G·sin²θ |
| **Fluid sensitivity** | Indirect | Direct (G discriminates) |

**E8 reads what the rock is. E9 reads what the pore space contains.**

## 7. DITEMPA BUKAN DIBERI

The velocity is the earth, integrated over time. The slice is the
map. The structure emerges from the physics.

DITEMPA BUKAN DIBERI — Forged, Not Given.
