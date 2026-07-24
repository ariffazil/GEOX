# GEOX ZEN-15 Public Surface

> **SOT:** `src/geox_mcp/tools_manifest.yaml` (= `surface.yaml`) → `CANONICAL_PUBLIC_SURFACE.json`  
> **surface_version:** `geox-zen15-2026.07.24` · **Count:** **15** (enforced)  
> **Attestation:** `geox_surface_status` → `surface_attestation` · CI: `scripts/check_registry_truth.py`  
> **Law:** runtime registry == manifest == docs. Drift = constitutional failure.  
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
| `geox_seismic_interpret` | Horizons / faults / gates / render | INT | Operator |
| `geox_basin` | Basin context / engines | DER/INT | Operator |
| `geox_deep_time_state` | Deep-time earth state | DER | Operator |
| `geox_geomechanics` | Elastic / rock mechanics | DER | Operator |
| `geox_subsurface_model` | Structural candidates | INT | Operator |
| `geox_claim` | Claim lifecycle (judgment lane) | CLAIM | arifOS bridge |
| `geox_prospect` | Prospect compute (judgment lane) | DER/INT | WEALTH capital (not GEOX price) |
| `geox_surface_status` | Registry / health / surface attestation | META | Agents first-call |

## Doctrine (FIX BRIEF v2)

- **Do not redesign to 8.** Consolidate below 15 only after routing-failure telemetry + shared noun + lifecycle.
- Demoted (internal/organ-private, not on `tools/list`): workspace, falsify, evidence, map suite, visual_*, gravmag, basin_backstrip, thermal, sediment, lem, claim_graph, contradiction, to_wealth_bridge, …
- Internal tools remain executable for organ-private paths; public agents route via ZEN-15 modes.
- Seismic happy path: `arif_init` → `geox_seismic_interpret(mode=interpret)` → compact QUALIFIED_CANDIDATE + render_ref.

## Epistemic ladder

`OBSERVED → DERIVED → INTERPRETED → SPEC/HYPOTHESIS`

## Bridges

- GEOX → WEALTH: adapter / feed only (public capital tools deregistered)
- Law: arifOS only

**DITEMPA BUKAN DIBERI**
