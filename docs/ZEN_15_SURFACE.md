# GEOX ZEN-15 Public Surface

> **SOT:** live `tools/list` + `CANONICAL_PUBLIC_SURFACE.json` · **Count:** 15  
> **License:** BSL-1.1 · **domain_law:** NATURAL_LAW · **Port:** `:8081`

## The 15 public tools

| Tool | Physics / domain basis | Epistemic output | Handoff |
|------|------------------------|------------------|---------|
| `geox_well_ingest` | LAS / well bundle I/O | OBS | Internal store |
| `geox_well_qc` | Depth/null/range QC | OBS/DER | Operator |
| `geox_petrophysics` | Vsh φ Sw Physics9 | DER | WEALTH feed (volumes) |
| `geox_sequence` | GR packages / systems tracts | INT | Operator |
| `geox_well_desk` | Well-desk OBSERVE UI | OBS+UI | AAA host |
| `geox_seismic_ingest` | SEGY / volume meta | OBS | Internal |
| `geox_seismic_compute` | Attributes / transforms | DER | Operator |
| `geox_seismic_interpret` | Horizons / frames | INT | Operator |
| `geox_basin` | Basin context / engines | DER/INT | Operator |
| `geox_deep_time_state` | Deep-time earth state | DER | Operator |
| `geox_geomechanics` | Elastic / rock mechanics | DER | Operator |
| `geox_subsurface_model` | Structural candidates | INT | Operator |
| `geox_claim` | Claim lifecycle (judgment lane) | CLAIM | arifOS bridge |
| `geox_prospect` | Prospect compute (judgment lane) | DER/INT | WEALTH capital (not GEOX price) |
| `geox_surface_status` | Registry / health | META | Agents first-call |

> Exact names may vary slightly by registry alias; **runtime tools/list wins**.

## Epistemic ladder

`OBSERVED → DERIVED → INTERPRETED → SPEC/HYPOTHESIS`  
Type-guard on `uncertainty` (string band / scalar / dict) sealed in `kernel/_evidence.py` + `tests/test_evidence_type_guard.py`.

## Naming

- **well-log domain package:** `geox.welllog` (canonical)  
- **`geox.well`:** DeprecationWarning shim (not WELL organ)

## Bridges

- GEOX → WEALTH: adapter / feed only (`geox_wealth_bridge` paths; public capital tools deregistered)  
- Law: arifOS only  

**DITEMPA BUKAN DIBERI**
