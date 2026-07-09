# GENESIS/014 — Petrel / DSG Delta & Build Order

> FORGE screening memos reduce entropy (ΔS < 0).  
> They are **not** a shared earth model until LAS/SEG-Y math and spatial physics run.

---

## Diagnosis (correct)

| Plane | FORGE/NV memo today | Petrel / DSG |
|-------|---------------------|--------------|
| Logic / bid strategy | Strong (OBS/DER/INT/SPEC, Bid/No-Bid) | Weak on epistemic labels |
| EMV | Flat / first-pass | Log-normal MC on volume factors |
| ToAC | 1D depocenter flag | Must be local to prospect, not basin-wide |
| Risk | Weighted matrix | Spatial charge/seal distance |
| Earth model | Strings + JSON | Voxels / corner-point grids |
| Well-seismic | Cited data rooms | Impedance + wavelet convolution |

**Relaks tapi tajam:** smart document compiler ≠ shared earth model.

---

## Locked build order (no reverse-delegation)

Doctrine (GEOX-001 + GENESIS/013): **Orthogonal Base first.**

| Priority | Work | Status |
|----------|------|--------|
| **P0** | 1D LAS math — φ, Vsh, Sw, AI, RC from curves | **IN PROGRESS** — `geox_001_las_physics` |
| **P0** | Well-tie spine — preflight → synthetic → receipt | **LIVE** — GEOX-001 |
| **P1** | Probabilistic STOIIP/EMV (lognormal MC) → WEALTH bridge | **LIVE** — `volumetric_mc` |
| **P2** | Spatial ToAC — prospect-local, not basin depocenter alone | Next |
| **P3** | 3D corner-point / property upscale | Deferred until P0–P1 solid |
| **P4** | Darcy migration path receipts | Deferred |

**Not building Petrel UI.** Backend physics + receipts only.

---

## What just landed

1. **`compute_las_physics`** — density/sonic/neutron porosity, Vsh, AI, RC, optional Archie Sw from real LAS arrays.  
2. **Wired into `run_geox_001_real_las`** — receipt carries DER φ_e P10/P50/P90 + NTG from logs.  
3. **`stoiip_monte_carlo` + `emv_from_stoiip_mc`** — replaces flat EMV screening with volume MC (still not grid GRV).  

---

## Explicit non-goals (this cycle)

- Full Petrel-grade 3D structural framework UI  
- Basin-wide heat-flow for all blocks from one depocenter thickness  
- Claiming Petronas field calibration without Petronas LAS/SEG-Y  

---

*GENESIS 014 · 2026-07-09 · pairs 012–013*  
*DITEMPA BUKAN DIBERI*
