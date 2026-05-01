# GEOX Sovereign 13 Contract
> Version: v2026.05.01
> Doctrine: Physics before Narrative. F1–F13 Governed.
> Epoch: 2026-05-01
> Seal: DITEMPA BUKAN DIBERI

## 1. Executive Architecture
GEOX is the subsurface reasoning Ψ (Psi) node of arifOS. The repository has been refactored into a high-grade AGI kernel, collapsing 49 fragmented legacy endpoints into **exactly 13 canonical tools.**

### 1.1 Canonical Sovereignty
- **One Kernel:** `control_plane/fastmcp/server.py` is the only valid entrypoint.
- **Fail-Closed Auth:** Server aborts if `GEOX_SECRET_TOKEN` is missing.
- **Dimensional Registry:** `contracts/tools/unified_13.py` serves as the single source of truth.

## 2. The Sovereign 13 Surface
Agents must use these 13 tools. All scientific interpretations (Petrophysics, Structural Modeling) MANDATE the return of **Ensembles** and **Residual Maps**.

| # | Canonical Tool Name | Purpose | Absorbs Legacy |
| :--- | :--- | :--- | :--- |
| 1 | `geox_data_ingest_bundle` | Lazy ingest LAS/SEG-Y/JSON | `well_ingest`, `seismic_load` |
| 2 | `geox_data_qc_bundle` | Unified header/unit/CRS QC | `well_qc`, `map_verify` |
| 3 | `geox_subsurface_generate_candidates` | Ensemble realiz. + Residuals | `petro_cand`, `model_geom` |
| 4 | `geox_subsurface_verify_integrity` | Physics9 / structural checks | `well_verify`, `struct_verify` |
| 5 | `geox_seismic_analyze_volume` | Attributes + Slice extraction | `seismic_compute`, `render_slice` |
| 6 | `geox_section_interpret_correlation` | Multi-well stratigraphy | `interpret_strata` |
| 7 | `geox_map_context_scene` | Spatial bbox + Causal render | `context_summary`, `render_scene` |
| 8 | `geox_time4d_analyze_system` | Burial, maturity, regime shift | `simulate_burial`, `verify_timing` |
| 9 | `geox_prospect_evaluate` | Volumetrics + POS evaluation | `evaluate`, `compute_stoiip` |
| 10 | `geox_prospect_judge_verdict` | 888_JUDGE Gateway | `judge_verdict` |
| 11 | `geox_evidence_summarize_cross` | Cross-domain evidence synthesis | `summarize_evidence` |
| 12 | `geox_system_registry_status` | Health, skills, discovery | `list_skills`, `health_check` |
| 13 | `geox_history_audit` | VAULT999 Decision retrieval | `audit_history` |

## 3. Migration & Compatibility
- **Alias Bridge:** Legacy names (dotted and underscores) are aliased to the 13 canonicals.
- **Deprecation:** Response metadata includes `_meta.deprecation` warnings.
- **Sunset Date:** Legacy names will be removed after `2026-06-01`.

## 4. Operational Health
- **Runtime:** VPS port 8081.
- **Blockers:** 502 Operational SABAR on VPS telemetry due to proxy/firewall (Kernel itself is SEALED).

---
⬡ GEOX SOVEREIGN 13 SEALED ⬡
