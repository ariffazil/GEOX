# GEOX Physics Domains (Eureka E7)

> **Source:** Copilot "Physical Earth Reality Physics" brief (2026-06-03)
> **Author:** omega-forge-agent
> **Status:** DRAFT — not yet wired to MCP (Tier 3, 888_HOLD pending)

GEOX's physics modules organize into **6 first-class physics domains** (Copilot) plus **2 cross-cutting** domains. Each maps to specific tools in the live MCP.

## 6 First-Class Physics Domains

### 1. Tectonics & Solid Earth Mechanics
**Physics:** Plate tectonics, continuum mechanics, Mohr–Coulomb, isostasy, heat flow in lithosphere.
**Invariants:** Mass conservation (volume balance), force equilibrium.
**Live tools:** `geox_seismic_compute` (synthetic), `geox_subsurface_generate_candidates(t=structure)`, `geox_subsurface_verify_integrity` (Physics9 paradox detector).
**Gap:** No dedicated `geox_tectonic_forward_model` — current scope is structural candidates, not basin subsidence curves.

### 2. Basin Thermodynamics & Geochemical Cycling
**Physics:** Fourier heat conduction, Arrhenius kerogen kinetics, mass balance.
**Invariants:** Energy conservation, mass balance (generated = expelled + retained + lost).
**Live tools:** `geox_header_inspect` (calibration), `geox_dst_ingest_test` (DST data), `geox_prospect_evaluate` (uses thermal history).
**Gap:** No `geox_burial_history` or `geox_maturity_model` tool — only via private Python modules.

### 3. Fluid Flow & Migration Physics
**Physics:** Darcy's Law, buoyancy, capillary pressure, multiphase flow, pressure diffusion.
**Invariants:** Mass continuity (in = out + storage).
**Live tools:** `geox_prospect_evaluate` (volumetrics), `geox_subsurface_generate_candidates` (ensemble flow).
**Gap:** No forward migration simulator; only static volumetrics.

### 4. Surface, Ocean & Atmosphere Interactions
**Physics:** Hydrology, ocean dynamics, atmospheric forcing.
**Invariants:** Mass, energy at the air-sea interface.
**Live tools:** `geox_map_context_scene` (geographic context only).
**Gap (EUREKA E5):** No metocean-gated SAR anomaly detection. Layang-Layang example needs `mode=sar_seep_check` with wind_speed input.

### 5. Wave Physics for SAR Remote Sensing
**Physics:** Electromagnetic scattering, capillary wave damping by oil films, Bragg scattering.
**Invariants:** Energy conservation in backscatter.
**Live tools:** None — pure gap.
**Gap (EUREKA E5):** Need new tool `geox_sar_seep_check(artifact_ref, wind_speed_ms, ...)` that returns credible/not-credible for a SAR dark patch.

### 6. Geochemistry & Mass Balance
**Physics:** Mass conservation, chemical thermodynamics (Peng–Robinson), kinetics.
**Invariants:** Mass, isotope balance.
**Live tools:** `geox_dst_ingest_test` (fluid composition), `geox_las_inspect` (log data).
**Gap:** No integrated PVT / isotope balance tool.

## 2 Cross-Cutting Domains

### 7. Cross-Verification & Governance (Tier 4)
**Physics:** ToAC (Theory of Anomalous Contrast), contradiction scanning, falsifiability.
**Invariants:** Conservation of audit (action ⇒ witness).
**Live tools:** `geox_evidence_reason(p=contradict)`, `geox_claim_challenge`, `geox_claim_seal`.
**Internal module:** `geox/core/ac_risk.py` (GAP-1 — not yet exposed as MCP tool).

### 8. Uncertainty & Scale
**Physics:** Probability, error propagation, multi-scale integration.
**Invariants:** Conservation of total probability.
**Live tools:** `geox_subsurface_generate_candidates(realizations=N)` for Monte Carlo.
**Gap (EUREKA E4):** No `scale` metadata in envelope — modules can return basin-scale result with no warning that downstream consumer is at log scale.

## 6 Physics Domains → Tool Coverage Matrix

| Domain | Live tools | Gap |
|---|---|---|
| 1. Tectonics | 3 | No forward basin subsidence model |
| 2. Thermodynamics | 3 (indirect) | No burial/maturity tool |
| 3. Fluid flow | 2 | No forward migration simulator |
| 4. Surface/Ocean | 1 (passive) | No metocean gating (E5) |
| 5. Wave/SAR | 0 | Full gap — new tool needed (E5) |
| 6. Geochemistry | 2 | No PVT/isotope balance |
| 7. Governance | 3 + 1 internal | ac_risk not exposed (GAP-1) |
| 8. Uncertainty | 1 (ensemble) | No scale metadata (E4) |

## Eurekas to embed

| ID | Eurekaness | Tier | Status |
|---|---|---|---|
| E1 causal_chain | HIGH | 1 | ✅ Schema def added |
| E2 falsification_tests | HIGH | 1 | ✅ Schema def added |
| E3 toac_pair | HIGH | 1 | ✅ Schema def added |
| E4 scale_metadata | HIGH | 1 | ✅ Schema def added |
| E5 sar_seep_check | HIGH | 3 | ⏸ Awaiting 888_HOLD |
| E6 cross_validate | MED | 3 | ⏸ Awaiting 888_HOLD |
| E7 this resource | MED | 3 | ⏸ Awaiting 888_HOLD |
| E8 conservation_laws | LOW | 3 | ⏸ Awaiting 888_HOLD |

## Next steps (888_HOLD)

To wire E5–E8, server.py needs:
- New `@mcp.resource` decorators for E7 (architecture/physics_domains) and E8 (physics/conservation_laws)
- New `@mcp.tool` decorators for E5 (geox_sar_seep_check), E6 (geox_cross_validate)
- Update existing tool return-types to include the new envelope fields (E1, E2, E3, E4)
- Expose ac_risk as MCP tool (already proposed as GAP-1)

Cost estimate: 1–2 days focused work. Fully reversible (additive, no breaking changes).

---

**DITEMPA BUKAN DIBERI** — Physics over narrative.
