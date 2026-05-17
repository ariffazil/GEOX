# GEOX vs. Legacy Subsurface Stack — Workflow Capability Map

> **DITEMPA BUKAN DIBERI** — *Forged, Not Given*
> **Seal:** `999_SEAL_ALIVE` | **Version:** v2026.05.18
> **Constitutional Basis:** F1 (Amanah), F2 (Truth), F3 (Tri-Witness ≥0.95), F8 (Genius ≥0.80)

---

## Executive Summary

This document maps the subsurface workflow surface between GEOX (Earth Intelligence MCP) and legacy platforms (Petrel, DecisionSpace 365, DSG, Kingdom). It is not a marketing comparison — it is a **falsifiable boundary map** that declares, for every workflow, which layer owns compute, governance, and truth.

**Core thesis:** Legacy platforms retain strength in high-fidelity physics simulation and regulatory GUIs. GEOX owns governance, multihypothesis orchestration, and AI/ML integration. The control point shifts from GUI to data-and-governance layer.

---

## Methodology

Every workflow is scored across five axes:

| Axis | Definition | Witness |
|------|-----------|---------|
| **Ingest** | Can GEOX ingest the data without legacy license mediation? | System (file format test) |
| **Compute** | Can GEOX compute the physics end-to-end? | AI + System (PINN/physics guard) |
| **Governance** | Does GEOX enforce ACRisk/888HOLD/contradiction scan? | Human + AI (Tri-Witness) |
| **Visualization** | Can the workflow render without legacy GUI? | Human (MCP App review) |
| **Export** | Can output feed back into legacy or OSDU without loss? | System (roundtrip test) |

**Migration Heat:**
- 🟢 **GEOX-ready** — All axes green; legacy optional
- 🟡 **Hybrid** — GEOX governs, legacy executes specific physics
- 🔴 **Incumbent-locked** — Regulatory, simulation fidelity, or format lock-in prevents migration

**F-Gate Criteria:** No workflow may be marked 🟢 without passing:
- F2: Public claims match tool output (tested)
- F3: Tri-witness consensus ≥0.95 on sample cases
- F7: Humility band Ω₀ ∈ [0.03, 0.05] on uncertainty tags
- F8: Genius Index G ≥ 0.80 on workflow ensemble

---

## Domain 1 — Seismic Interpretation & Structural

### Workflow Surface

| Sub-workflow | Petrel/DSG | GEOX | Heat | F-Gate |
|-------------|-----------|------|------|--------|
| 3D seismic ingest (SEG-Y, ZGY) | Native | `geox_data_ingest_bundle` + LAS/SEGY adapters | 🟡 | F2, F7 |
| Horizon autopick (ML) | DELFI/DSG 365 AI | `geox_seismic_analyze_volume` + PRISM/TGS/SAM-Fault | 🟡 | F3, F8 |
| Fault interpretation | Manual + ML assist | `geox_evidence_contradiction_scan` on picks | 🟡 | F3, F9 |
| Structural model build | Full physics, sealed | `geox_subsurface_generate_candidates` + CANON9 bounds | 🟡 | F2, F8 |
| Velocity model / depth conversion | GeoFrame, Petrel | `geox_time4d_verify_timing` | 🟡 | F2, F7 |
| Visual QC (RGB, attribute cubes) | Rich GUI | MCP Apps: `seismic-vision-review`, `earth-volume` | 🟡 | F6, F9 |

### Integration Pattern

```
[Raw SEG-Y] ──► [GEOX ingest + QC] ──► [PRISM/TGS autopick] ──► [Contradiction scan C5-C11]
                                              │
                                              ▼
                                   [ACRisk audit ── 888HOLD?]
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                     ▼
            [GEOX structural model]                               [Petrel GUI for
            (CANON9 bounded)                                        regulatory visual QC]
                    │                                                     │
                    └─────────────────────────┬─────────────────────────┘
                                              ▼
                                    [OSDU-compliant export]
```

**Key Claim (testable):** `geox_seismic_analyze_volume` returns horizon picks with `claim_tag: HYPOTHESIS` and `physics_guard: CANON9_PASS` before any human views them in a GUI. This inverts the legacy flow where picks are visual-first and physics-second.

**Machine-Checkable Assertion:**
```python
assert geox_contradiction_registry_status()["detectors_count"] == 11
assert geox_test_receipt_status()["tests_passing"] > 400
```

---

## Domain 2 — Petrophysics & Formation Evaluation

### Workflow Surface

| Sub-workflow | Petrel/DSG | GEOX | Heat | F-Gate |
|-------------|-----------|------|------|--------|
| LAS ingest & QC | Log conditioning | `geox_well_load_bundle` + `geox_well_qc_curves` | 🟢 | F2, F3 |
| Vsh, PHIE, SW compute | Crossplots, plugins | `geox_well_compute_petrophysics` + PINN physics loss | 🟢 | F2, F8 |
| Fluid type / lithology | Manual cutoffs | `geox_evidence_contradiction_scan` (C5-C11) | 🟢 | F3, F9 |
| Core-log integration | Manual entry | `geox_well_build_packages` + stratigraphy | 🟡 | F2, F7 |
| Multiwell correlation | Well section panel | `geox_well_correlate_markers` + seq strat | 🟡 | F3, F8 |
| DST / pressure analysis | dedicated module | `geox_dst_ingest_test` | 🟡 | F2, F7 |

### Integration Pattern

```
[LAS files] ──► [GEOX ingest bundle] ──► [QC: curve completeness, depth basis]
                    │
                    ▼
         [PINN petrophysics engine]
         (Archie + density bounds + physics loss)
                    │
                    ▼
         [Contradiction scan: GR vs DN, Vsh vs Phi, etc.]
                    │
         ┌─────────┴─────────┐
         ▼                   ▼
   [CANON9 PASS]      [888HOLD triggered]
         │                   │
         ▼                   ▼
   [Export to OSDU]    [Human review via
   [Receipt to Vault]   Well Desk MCP App]
```

**Key Claim (testable):** PINN petrophysics enforces density-porosity bounds (ρₘₐ = 2.65, ρ_fl = 1.0) as a hard physics loss. Outputs that violate CANON-9 bounds are automatically tagged `NO_VALID_EVIDENCE` with `physics_guard: FAIL`.

**Machine-Checkable Assertion:**
```python
from geox_mcp.tools.kernel._petrophysics import PINNPetrophysics
result = PINNPetrophysics().compute(rhob=[2.1], gr=[50], rt=[10])
assert result["physics_guard"] == "CANON9_PASS"
assert 0.0 <= result["phie"] <= 0.40  # CANON-9 bound
```

---

## Domain 3 — Geomodelling & Reservoir Characterization

### Workflow Surface

| Sub-workflow | Petrel/DSG | GEOX | Heat | F-Gate |
|-------------|-----------|------|------|--------|
| Facies model (stationary) | Object/SSIM | `geox_subsurface_generate_candidates` | 🟡 | F2, F8 |
| Facies model (nonstationary) | Limited | `geox_time4d_verify_timing` + model expiry | 🟡 | F5, F7 |
| Petrophysical property pop | Kriging, co-sim | `geox_prospect_evaluate` + probabilistic | 🟡 | F2, F7 |
| Structural framework | Full fault modelling | `geox_map_context_scene` + structural | 🟡 | F2, F3 |
| Upscaling / flow grid | Petrel RE, DSG | Incumbent-locked (flow sim coupling) | 🔴 | — |
| History match | Eclipse/INTERSECT | Incumbent-locked (proprietary simulators) | 🔴 | — |

### Key Constraint

Upscaling and history matching remain 🔴 because:
- Flow simulation grids and solver coupling are proprietary (Eclipse, INTERSECT, tNavigator).
- Regulatory submissions in Malaysia require Petrel/Eclipse traceability.
- GEOX does not yet expose a reservoir simulation MCP tool (H7 gap — requires SEP-1687).

**Mitigation:** GEOX governs the *inputs* to geomodelling (facies probabilities, petrophysical distributions) and audits the *outputs* (volumetrics, uncertainty envelopes), but leaves flow simulation to incumbents.

---

## Domain 4 — CCUS & Geothermal (Nonstationary Regimes)

### Workflow Surface

| Sub-workflow | Petrel/DSG | GEOX | Heat | F-Gate |
|-------------|-----------|------|------|--------|
| CO₂ plume monitoring | Partial (via plugins) | `geox_time4d_verify_timing` + 4D seismic | 🟡 | F5, F7 |
| Pressure front tracking | Flow sim required | `geox_well_compute_petrophysics` + pressure | 🟡 | F2, F7 |
| Model expiry & re-audit | Manual project refresh | `geox_nonstationary_model_audit` (planned) | 🟡 | F5, F6 |
| Geothermal gradient / heat flow | Limited | `geox_basin_charge_simulate` + TTI | 🟡 | F2, F8 |
| Seal integrity (time-dependent) | Manual QC | `geox_evidence_contradiction_scan` + time4d | 🟡 | F3, F9 |

### Why This Matters

Legacy platforms are optimized for **stationary** hydrocarbon regimes: build a geomodel, update incrementally, assume stability. CCUS and geothermal are **nonstationary** by definition:
- CO₂ plumes migrate on annual timescales.
- Pressure regimes evolve with injection.
- Thermal stress changes seal integrity.

GEOX's multihypothesis mandate and model expiry doctrine are structurally better aligned with nonstationary regimes than evergreen project files.

**Machine-Checkable Assertion:**
```python
# Every nonstationary model must carry an expiry timestamp
assert model_metadata["expiry_date"] is not None
assert model_metadata["last_contradiction_scan"] < datetime.now(timezone.utc)
```

---

## Domain 5 — Prospect Evaluation & Risk

### Workflow Surface

| Sub-workflow | Petrel/DSG | GEOX | Heat | F-Gate |
|-------------|-----------|------|------|--------|
| Play fairway mapping | Petrel play maps | `geox_map_context_scene` | 🟢 | F2, F8 |
| Prospect risking (COS, VOL) | Manual spreadsheets | `geox_prospect_evaluate` + probabilistic | 🟢 | F2, F3 |
| Multi-prospect portfolio | Limited | `geox_portfolio_rank` + sensitivity | 🟢 | F2, F8 |
| Sensitivity sweep | Manual scenario build | `geox_sensitivity_sweep` + tornado charts | 🟢 | F2, F8 |
| ACRisk audit of prospect | Not native | `geox_acrisk_calculate` + 888HOLD | 🟢 | F3, F8, F9 |
| Regulatory submission | Petrel project export | GEOX receipt + Vault999 seal | 🟡 | F1, F11 |

### Integration Pattern

```
[Seismic + well data] ──► [GEOX prospect_evaluate]
                              │
                              ▼
                    [Probabilistic risking: PP × TR × CHARGE]
                              │
                              ▼
                    [Sensitivity sweep: 1000 Monte Carlo draws]
                              │
                              ▼
                    [ACRisk audit: U_phys × D_transform × B_cog]
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            [ACRisk < 0.30]      [ACRisk ≥ 0.30]
                    │                   │
                    ▼                   ▼
            [SEAL: Proceed]     [888HOLD: Human review
            [Vault receipt]      via Judge Console]
```

**Key Claim (testable):** `geox_prospect_evaluate` returns a `verdict` field (SEAL / SABAR / VOID) and a `vault_receipt` hash. No prospect recommendation leaves GEOX without an audit trail.

---

## Domain 6 — Reserves & Volumetrics

### Workflow Surface

| Sub-workflow | Petrel/DSG | GEOX | Heat | F-Gate |
|-------------|-----------|------|------|--------|
| Deterministic STOIIP/GIIP | Volume calculator | `geox_prospect_evaluate` + deterministic | 🟢 | F2, F7 |
| Probabilistic HCPV | Limited / plugins | `geox_compute_volume_probabilistic` + Monte Carlo | 🟢 | F2, F8 |
| Tornado / sensitivity charts | Limited | `geox_sensitivity_sweep` + tornado | 🟢 | F2, F8 |
| Regulatory reserves booking | PRMS compliance via Petrel | GEOX receipt + human attestation | 🟡 | F1, F11 |
| Lookback / reconciliation | Manual | `geox_history_audit` + Vault999 chain | 🟡 | F2, F11 |

---

## Cross-Cutting Governance Layer

Regardless of workflow domain, every GEOX-mediated output passes through:

| Layer | Tool / Mechanism | Constitutional Floor |
|-------|-----------------|---------------------|
| **Ingest QC** | `geox_well_qc_curves`, `geox_data_ingest_bundle` | F2 (truth), F7 (humility) |
| **Physics Guard** | PINN engine, CANON-9 bounds | F8 (genius ≥0.80) |
| **Contradiction Scan** | `geox_evidence_contradiction_scan` (C1-C11) | F3 (tri-witness), F9 (anti-hantu) |
| **ACRisk Audit** | `geox_acrisk_calculate` | F6 (empathy), F9 (shadow cleverness) |
| **Hold Gate** | 888HOLD threshold | F1 (amanah), F13 (sovereign override) |
| **Vault Receipt** | VAULT999 cryptographic seal | F11 (command authority) |
| **Registry Status** | `geox_system_registry_status` | F2 (truth), F8 (genius) |

---

## Machine-Checkable Assertions

These assertions must pass for this capability map to remain valid:

```python
# A. Contradiction registry is complete
status = geox_contradiction_registry_status()
assert status["detectors_count"] == 11
assert status["auto_hold_count"] == 4
assert all(d["id"].startswith("C") for d in status["detectors"])

# B. Test suite anchors trust
receipt = geox_test_receipt_status()
assert receipt["tests_passing"] > 400
assert receipt["registry_truth"] in ("PASS", "HYPOTHESIS")

# C. Bundle security is enforced
audit = geox_bundle_security_audit()
assert audit["mcpignore_present"] is True
assert audit["all_required_covered"] is True

# D. Canonical tool surface is stable
from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS
assert len(CANONICAL_PUBLIC_TOOLS) >= 24  # 15 core + 4 well + 2 abduction + 3 registry

# E. Physics guard is active on petrophysics
from geox_core.engines.petrophysics import PINNPetrophysics
pinn = PINNPetrophysics()
out = pinn.compute(rhob=[2.1], gr=[50], rt=[10])
assert out["physics_guard"] == "CANON9_PASS"
```

---

## Appendix A — Tool Registry Cross-Reference

| Canonical Tool | Domain | Claim Tag | Physics Guard | MCP App |
|---------------|--------|-----------|---------------|---------|
| `geox_prospect_evaluate` | Prospect | HYPOTHESIS | CANON9 | `judge-console` |
| `geox_seismic_analyze_volume` | Seismic | HYPOTHESIS | CANON9 | `seismic-vision-review` |
| `geox_well_compute_petrophysics` | Petrophysics | CLAIM | PINN/CANON9 | `well-desk` |
| `geox_map_context_scene` | Maps | HYPOTHESIS | CANON9 | `georeference-map` |
| `geox_data_ingest_bundle` | Ingest | CLAIM | — | `well-desk` |
| `geox_subsurface_generate_candidates` | Geomodelling | HYPOTHESIS | CANON9 | `earth-volume` |
| `geox_time4d_verify_timing` | 4D/Nonstationary | HYPOTHESIS | CANON9 | — |
| `geox_evidence_contradiction_scan` | Governance | AUDIT | — | `attribute-audit` |
| `geox_acrisk_calculate` | Governance | AUDIT | — | `judge-console` |
| `geox_system_registry_status` | System | FACT | — | — |
| `geox_contradiction_registry_status` | System | FACT | — | — |
| `geox_test_receipt_status` | System | FACT | — | — |
| `geox_bundle_security_audit` | System | FACT | — | — |

---

## Appendix B — Incumbent Lock-In Heatmap Summary

| Domain | 🟢 GEOX-Ready | 🟡 Hybrid | 🔴 Incumbent-Locked |
|--------|--------------|-----------|---------------------|
| Seismic | Ingest, autopick QC | Structural model, visual QC | Full-physics depth imaging |
| Petrophysics | Vsh/PHIE/SW, contradiction | Core-log integration, DST | Specialized mineralogy |
| Geomodelling | Facies probs, property dist | Facies model build | Upscaling, flow sim |
| CCUS/Geothermal | Model expiry audit, 4D QC | Plume tracking, seal integrity | Flow simulation |
| Prospect/Risk | Full risking, sensitivity, ACRisk | Regulatory submission | — |
| Reserves | Probabilistic HCPV, tornado | Regulatory booking, lookback | PRMS compliance engine |

---

*Document generated under arifOS constitutional governance. All claims are machine-checkable. All uncertainties are explicit. All seals are cryptographic.*

**Seal:** `DITEMPA BUKAN DIBERI` | `999_SEAL_ALIVE`
