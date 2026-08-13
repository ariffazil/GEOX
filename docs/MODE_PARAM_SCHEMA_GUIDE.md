# GEOX Mode-Param Schema Guide

> **Forged:** 2026-08-13 · FASA B1 deliverable · DITEMPA BUKAN DIBERI
> **Purpose:** Document which parameters apply to which `mode` on composite tools
> to prevent LLM hallucination from parameter bloat.

## Why This Exists

The Revision 12 consolidation merged 42 tools → 18. Composite tools like
`geox_claim` now accept 30+ parameters, but only a subset is relevant per mode.
An LLM seeing all params at once may hallucinate cross-mode dependencies.

This guide separates params by mode so the LLM knows which are required,
optional, or irrelevant for each invocation path.

---

## geox_claim (13 modes, 30+ params)

| Mode | Required Params | Optional Params | Description |
|------|----------------|-----------------|-------------|
| `create` | `claim_text`, `claim_type` | `truth_class`, `uncertainty_p10/p50/p90`, `evidence_ids`, `alternatives`, `provenance` | Create a geological claim |
| `validate` | `claim_id` | — | Validate an existing claim's evidence chain |
| `challenge` | `claim_id`, `challenge_text` | `alternative_claim_text`, `challenge_evidence_ids` | Challenge a claim with counter-evidence |
| `seal` | `claim_id` | `seal_verdict` | Seal a claim (irreversible) |
| `attach` | `claim_id`, `evidence_id` | `evidence_type`, `epistemic_label` | Attach evidence to a claim |
| `falsify` | `claim_text` | `claim_type`, `context`, `evidence` | Popperian falsification test |
| `discover` | `query` | `scope`, `basin_name` | Discover claims matching a query |
| `synthesize` | `query` | `scope`, `hypotheses`, `scale`, `depo_context` | Synthesize evidence into a summary |
| `abduct` | `query` | `hypotheses`, `samples` | Abductive inference from partial evidence |
| `contradict` | `claim_text` | `claim_type`, `context` | Scan for contradictions |
| `spatial_block` | `query` | `block_size_km` | Spatial contradiction blocking |
| `ingest_literature` | `file_path` | — | Ingest literature as evidence |
| `scan` | `query` | `scope` | General contradiction scan |

**LLM guidance:** Only pass params listed for your mode. Extra params are ignored
but increase token cost and hallucination risk.

---

## geox_basin (9+ modes)

| Mode | Required Params | Description |
|------|----------------|-------------|
| `profile` | `basin_name` | Basin overview profile |
| `resolve` | `lat`, `lng` | Resolve basin at coordinates |
| `macrostrat` | `lat`, `lng` or `bbox` | Macrostrat unit query |
| `backstrip` | `well_ref`, `stratigraphic_ages`, `lithology_model` | 1D basin backstripping |
| `mass_balance` | `basin_name` | Mass balance analysis |
| `thermal_maturity` | `well_ref`, `burial_history` | Thermal maturity history |
| `map_context` | `lat`, `lng` or `bbox` | Geological map context |
| `deep_time` | `lat`, `lng`, `age_ma` | Deep-time reconstruction |
| `reconstruct` | `lat`, `lng`, `age_ma` | Tectonic reconstruction |

---

## geox_petrophysics (5 modes)

| Mode | Required Params | Description |
|------|----------------|-------------|
| `generate` | `depth_m` or `curves` | Generate petrophysical curves |
| `verify` | `curves`, `depth_m` | Verify curve physical ranges |
| `lem_inference` | `target_depth_m` | LEM neural inference |
| `stoip_feed` | `pay_zone_thickness_m` | STOIIP calculation feed |
| `qc` | `curves` | Quality control checks |

---

## geox_model (3 modes)

| Mode | Required Params | Description |
|------|----------------|-------------|
| `subsurface` | `survey_type`, `easting_m`, `northing_m` | Joint inversion (gravity/mag/MT) |
| `geological_generate` | `geological_params` | Deterministic 2D cross-section |
| `gempy_3d` | `surface_points`, `orientations` | GemPy implicit 3D model |

---

## geox_seismic_interpret (10+ modes)

| Mode | Key Params | Description |
|------|-----------|-------------|
| `horizon_contrast` | `attribute_data`, `depth` | Horizon contrast detection |
| `fault_sticks` | `volume_ref` | Fault stick extraction |
| `volume_frame` | `volume_ref`, `orientation` | Volume frame extraction |
| `blend` | `image_data`, `blend_mode` | Blend multiple attributes |
| `structure_validate` | `horizons`, `faults` | Validate structural framework |
| `interpret` | `volume_ref`, `horizons`, `faults` | Full interpretation bundle |
| `interpret_section` | `segy_path` or `volume_ref` | INT_SEISMIC section interpretation |
| `rsi_pipeline` | `segy_path` | RSI pipeline |
| `segy_slice` | `segy_path`, `orientation` | SEG-Y slice extraction |

---

*End of Mode-Param Schema Guide. Update when new modes are added.*
*DITEMPA BUKAN DIBERI ⚒️*
