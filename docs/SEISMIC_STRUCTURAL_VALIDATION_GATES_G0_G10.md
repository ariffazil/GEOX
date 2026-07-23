# GEOX Structural Validation Gates G0–G10

**Source:** F13 sovereign verdict 2026-07-23 · zen SOT 2026-07-23  
**Status:** **PARTIAL LIVE** — G2 + K* matrix via `structure_validate`; G0/G1/G10 policy live in contracts  
**SOT:** `docs/SEISMIC_SECTION_INTERPRET_ZEN.md`  
**Posture:** HOLD autonomous structural interpretation — propose + falsify only

Not blind POS multiplication — checks are correlated.

```
Hard physical invariants
  + Conditional probabilistic tests
  + Competing structural models
  + Explicit falsification
```

| Gate | Type | Purpose | Live? |
|------|------|---------|-------|
| **G0** Measurement identity | Hard veto | SEG-Y preferred; geometry, polarity, processing, VE, SHA-256. Screenshot = OBS_IMAGE / INT_SEISMIC | partial (`segy_slice`, RSI provenance) |
| **G1** Proposal boundary | Soft | Horizons/faults/confidence/≥3 alternatives; INT_SEISMIC not OBS_GEOLOGY | partial (RSI alts pad) |
| **G2** Horizon topology | Hard veto | Non-cross, order, negative thickness | **yes** (`topology.py`) |
| **G3** Fault displacement | Mixed | Throw/heave, tip taper, D–L | **yes** (K-THROW, K-DL) |
| **G4** Stratigraphic response | Soft | Growth, drag, truncation | **partial** (K-GROWTH) |
| **G5** Restoration | Hard veto | Close balance, no self-intersection | **stub** (K-RESTORE) |
| **G6** Mechanical context | Conditional prior | Dip plausibility — VE-corrected | **yes** (K-DIP) |
| **G7** Time–depth integrity | Hard veto | Positive V, monotonic T–D | **partial** (K-VEL) |
| **G8** 3D closure | Soft→hard volume | Adjacent lines, loop closure | open |
| **G9** Falsification | Required | Strongest alternative + kill + EVOI | **partial** (falsify structural_*) |
| **G10** Capital handoff | Contract | Ensemble + uncertainty only to WEALTH | policy |

## Related

- K-* : `docs/SEISMIC_FAULT_PHYSICS_GATES_K_SPEC.md`
- Zen SOT: `docs/SEISMIC_SECTION_INTERPRET_ZEN.md`
- Benchmark: F3 · CRACKS · SEAM · Alcalde **with source identity** · Bond 2007 with provenance

DITEMPA BUKAN DIBERI
