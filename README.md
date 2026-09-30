# GEOX — Earth Intelligence Engine

Physics-grounded geological intelligence for exploration, hazard assessment, and earth science.

GEOX transforms subsurface data — seismic, wells, basin models — into auditable geological evidence. Every claim is traceable. Observation, derivation, and interpretation stay separate. GEOX computes. It does not adjudicate. It does not seal.

**Licensed under the Business Source License 1.1 (BSL-1.1).** Production use requires a license from the author.

| Audience          | What you get                                                                                  |
|-------------------|-----------------------------------------------------------------------------------------------|
| Human / earth team | A specialist that keeps uncertainty labelled. Not a generic chat about rocks                |
| Agent / A2A       | MCP evidence tools only. No publish. No field control. No silent escalation to A-FORGE write |
| Institution       | A bounded subsurface organ you can plug in: physics in, evidence out, kernel still holds the gavel |

Live MCP: https://geox.arif-fazil.com/mcp

---

## Live reality (probe this, do not trust prose)

| Fact | Live |
|---|---|
| Health | `GET http://127.0.0.1:8081/health` → `healthy` |
| Process | `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081` |
| Unit | `geox-mcp.service` |
| Source repo | `/root/GEOX` → `github.com/ariffazil/GEOX` |
| Runtime | `/opt/geox` (FHS). Source ≠ runtime until deploy. |
| **Canonical MCP tools** | **31** (`registry.py::CANONICAL_PUBLIC_TOOLS` — the gate-enforced SOT) |
| **Live tools observed** | **25** on `:8081/drift` — runtime is on an older commit (`e8e6f93`, not on this branch); redeploy catches up |
| **Generated manifests** | `tools.json`, `tools_sot.yaml`, `CANONICAL_PUBLIC_SURFACE.json`, `contracts/tools.yaml` — all **31** after `scripts/generate_all_surfaces.py` |
| Drift | `live==canonical` on the runtime that is deployed (`drift_count=0`, `gap_count=0`, `ok=true`) |
| Ghost / internal names | 22 in `CANONICAL_PUBLIC_SURFACE.json` internal set — not on the public surface |
| Authority | `555_COMPUTE_ONLY` — Earth evidence only. Judgment is arifOS. Mutation is A-FORGE. |
| Domain law | `NATURAL_LAW` |
| Public MCP | https://geox.arif-fazil.com/mcp |

**Truth rule.** Live `:8081/health` and `:8081/drift` beat any static count in this file. If the live count disagrees with the SOT count, **redeploy** — the gap means the runtime hasn't caught up with this code, not that the SOT is wrong.

**How the 5-tool gap between SOT (31) and live (25) arose.** Phase 2A/2B of the evidence-spine roadmap (PR #177, merged Sep 15) added 5 tools to `registry.py` and the public surface gate:
- `geox_calibration_register_witness`
- `geox_extract_display_proxy`
- `geox_extract_native_trace`
- `geox_list_registered_sources`
- `geox_register_native_source`

The runtime on `:8081` was built before these landed. Once `/opt/geox` is rebuilt from this branch, drift goes to 0 with `canonical=live=31`.

---

## The Problem

Traditional earth science workflows are slow, siloed, and dependent on scarce domain expertise. GEOX encodes that work into a system that can:

- Process seismic and interpret structures with physics guards
- Run petrophysics on LAS consistently
- Profile basins from local evidence (Malay Basin is the richest local pack)
- Assess geohazards (GLOF cascade family) without pretending to be a court
- Query paleobiology with spatial-temporal context

It will also **refuse**. A 33° map bbox is too big — that is a design constraint, not a crash. Macrostrat 500 is "no data," not a fabricated column. Empty SUCCESS is a lie; GEOX is not allowed to stamp `ok: true` on an empty basin envelope.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ GEOX Earth Intelligence                                      │
│ :8081  ·  MCP  ·  31 public tools  ·  555_COMPUTE_ONLY       │
├──────────────────────────────────────────────────────────────┤
│  Well / Petrophysics │ Seismic │ Basin │ Map │ Deep time     │
│  Geomechanics        │ Source  │ Claim │ GLOF cascade        │
│  Evidence spine      │ LEM     │ Prospect │ Spatial           │
│                                                              │
│  Witness layer (Δ·Ω·Ψ)                                       │
│  OBS (observed) → DER (derived) → INT (interpreted)          │
└──────────────────────────┬───────────────────────────────────┘
                           │ MCP (evidence only)
                    ┌──────▼──────┐
                    │ arifOS 888  │ ← judgment, seal
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ A-FORGE 000 │ ← execution, mutation
                    └─────────────┘
```

GEOX is bounded:
- No publish (no writing to databases the federation owns)
- No field control (no actuator surfaces)
- No authority above `555_COMPUTE_ONLY`
- No silent escalation — every call carries provenance

---

## Public surface (SOT)

| Family | Tools | Tier mix |
|---|---:|---|
| Basin | 1 (`geox_basin`) | A |
| Seismic | 3 (`compute`, `ingest`, `interpret`) | A, B, B |
| Well | 3 (`well`, `well_ingest`, `well_qc`) | A, B, B |
| Map | 1 (`geox_map`) | A |
| Petrophysics | 1 | A |
| Source | 1 | A |
| Geomechanics | 1 | A |
| Deep time | 1 | A |
| Temporal | 1 | B |
| Spatial | 1 | A |
| Paleobiology | 1 | B |
| Prospect | 1 | A |
| Model | 1 | A |
| Claim | 1 | A |
| Contrast | 1 | B |
| GLOF cascade | 7 (`initialize`, `inverse`, `mcmc_inverse`, `metabolize`, `phase`, `propagate`, `step`) | C |
| **Evidence spine** (Sep 15, 2026) | 5 (`calibration_register_witness`, `extract_display_proxy`, `extract_native_trace`, `list_registered_sources`, `register_native_source`) | B |

For tool-by-tool authority requirements, see `contracts/tools.yaml`.

---

## Authority floor

Every tool has a minimum required authority band (`OBSERVE_ONLY < OPERATOR < LIMITED_MUTATE < FULL < SOVEREIGN`).
The connector admits or rejects calls based on the band in the session token. GEOX never grants; it only enforces the floor declared in the manifest.

| Action class | Required authority |
|---|---|
| `OBSERVE` | `OBSERVE_ONLY` |
| `MUTATE` | `LIMITED_MUTATE` |
| `EXECUTE` | `LIMITED_MUTATE` |

Override table exists for tools whose effective action depends on call-time arguments (`geox_well_ingest` with `overwrite=true` is a `MUTATE` despite the manifest declaring `OBSERVE`).

---

## Epistemic labels

| Label | Meaning |
|---|---|
| `OBS` | Directly observed from data |
| `DER` | Derived via known physical laws |
| `INT` | Interpreted |
| `SPEC` | Hypothesis, needs validation |

Confusing speculation with observation is how dry holes and fake seals are born.

---

## Federation role

GEOX is the earth witness. Outputs are evidence for arifOS (F1–F13). Sister repos:

- arifOS — kernel / judgment
- AAA — Attention Plane / routing
- A-FORGE — execution
- WEALTH — capital compute
- WELL — vitality mirror
- arifFlow — metabolism

Topology SOT: `/root/AAA/federation/organs.yaml` (machine) and `/root/AAA/docs/ORGAN.md` (human). Live `/health` still beats both.

---

## Documentation

- SOT audit 2026-09-06
- Architecture
- Deployment
- Changelog
- Security

---

## License

Business Source License 1.1 (BSL-1.1) — see LICENSE. Production licensing: arifbfazil@gmail.com.

DITEMPA BUKAN DIBERI — Forged, Not Given.

---

## Tool inventory (canonical names from `registry.py`)

All 31 tools on the public MCP surface, grouped by family. The canonical list is the gate — additions and removals require an `arifOS` seal.

### Basin
- `geox_basin` — Mode-dispatched basin profile. Modes: overview · petroleum_system · stratigraphy · play_fairway · risk · contradiction_scan · macrostrat_units · macrostrat_columns · macrostrat_lithologies · macrostrat_strat_names · macrostrat_intervals · macrostrat_fossils · macrostrat_geologic_map · macrostrat_cache_warm. The basin directory contains the **NW Borneo Collision System** ontology (parent + 5 positions) — read `resources/basins/nw_borneo_collision_system/basin_profile.yaml` for the event registry.

### Seismic
- `geox_seismic_compute` — AVO forward modelling (Zoeppritz / Shuey / LMR / Castagna).
- `geox_seismic_ingest` — SEG-Y inspection + metadata extraction.
- `geox_seismic_interpret` — One semantic capability: horizon_contrast, fault_sticks, volume_frame, blend, structure_validate, interpret (≥3 hypotheses), interpret_section, rsi_pipeline, segy_slice. Includes the J-space manifold drift guard.

### Well
- `geox_well` — Mode-dispatched well operations.
- `geox_well_ingest` — LAS / SEG-Y / DST / deviation / tops ingest.
- `geox_well_qc` — Quality control (depth monotonicity, null %, physical ranges).

### Map / Spatial
- `geox_map` — Geological map pipeline (layers_list · scene_plan · render_preview · export_package).
- `geox_spatial` — H3 hexagonal indexing, LanceDB vector store, STAC catalog query.

### Petrophysics / Source / Geomechanics / Model
- `geox_petrophysics` — Vsh / porosity / Sw / permeability / net pay / LEM inference / QC. Mode-dispatched.
- `geox_source` — Source rock (TOC, kerogen, maturity, ΔlogR) + diagenesis compaction models.
- `geox_geomechanics` — Bulk/shear/Young modulus, Poisson ratio, acoustic impedance, stress polygon.
- `geox_model` — Joint inversion (gravity/mag), MT forward, deterministic 2D cross-section, GemPy 3D implicit structural modeling.

### Temporal / Deep time / Paleobiology
- `geox_temporal` — Decline curves, reserve replacement ratio, basin lifecycle, licensing cadence.
- `geox_deep_time` — DDE Ontology + Macrostrat neuro-symbolic reasoning for stratigraphic queries.
- `geox_paleobiodb_query` — Paleobiology Database (PBDB v1.2) taxa / occurrences / biozones / age intervals.

### Prospect / Claim / Contrast
- `geox_prospect` — Volumetrics, POS, EVOI, risk (screen · evaluate).
- `geox_claim` — Unified claim engine (create · validate · challenge · seal · attach · falsify · discover · synthesize · abduct · contradict · spatial_block · ingest_literature · scan). F3 honesty: present tense is a claim, not status.
- `geox_contrast_metabolize` — ISOLATE → MEASURE → CLASSIFY (≥3 stratigraphic trap hypotheses).

### GLOF cascade family (7)
- `geox_glof_cascade_initialize`
- `geox_glof_cascade_step`
- `geox_glof_cascade_phase`
- `geox_glof_cascade_inverse`
- `geof_glof_cascade_mcmc_inverse`
- `geox_glof_cascade_metabolize`
- `geox_glof_cascade_propagate`

Multi-phase physics: solid dam → granular debris → liquid flood (Mohr-Coulomb + Saint-Venant + 33D zen-33 state).

### Evidence spine (Sep 15, 2026, PR #177)
- `geox_calibration_register_witness` — Register calibration witness for structural interpretation.
- `geox_register_native_source` — Register a native SEG-Y source for trace extraction.
- `geox_list_registered_sources` — List registered native sources.
- `geox_extract_native_trace` — Extract a native seismic trace with full provenance (NativeTraceRef with permitted/prohibited downstream uses).
- `geox_extract_display_proxy` — Pixel-derived proxy array from a raster seismic image (DISPLAY_DERIVED_PROXY — explicitly NOT usable for amplitude preservation, AVO classification, phase certification, native seismic-to-well tie acceptance, or quantitative prospect/fault-seal decisions).

---

## Integration with the federation

GEOX sits at plane **L3 DOMAIN** under `arifOS`. The contract:

1. **arifOS** owns judgment. Every GEOX claim is `OBS` / `DER` / `INT` / `SPEC` and travels with provenance. arifOS's `arif_judge` is the only path to SEAL.
2. **A-FORGE** owns execution. GEOX never writes; it returns evidence envelopes. A-FORGE decides what (if anything) to mutate.
3. **WEALTH** owns capital math. GEOX never issues resource estimates; STOIIP / reserves flow through `capital_primitive` and `geox_prospect` cooperatively.
4. **WELL** owns the substrate mirror. GEOX emits ΔS entropy events (`entropy_observe`, `entropy_route`) that WELL ingests.
5. **arifFlow** is the receipt accountant. Every GEOX tool call posts a step receipt (FQ = verify/execute ratio).
6. **HERMES** is the inbound gateway. Telegram / inbound signals route here; GEOX never answers humans directly.
7. **AAA** owns attention. The arifOS governance gate (`geox-evidence-postcondition-v1`) enforces `observed / derived / interpreted / process_hypotheses` keys on every primary_artifact — GEOX tools always carry these.

### Contracts on disk
- `FEDERATION.md` — pointer (this repo) + canonical source in `arifOS/docs/FEDERATION.md`
- `FEDERATION_CONTRACT.md` — GEOX's specific contract
- `CANONICAL_PUBLIC_SURFACE.json` — generated SOT for tools
- `contracts/tools.yaml` — per-tool authority requirements

---

## Failure model (what GEOX refuses to do)

- GEOX will not return `ok: true` on an empty basin envelope. Empty SUCCESS is a lie.
- GEOX will not fabricate a claim for a 33° map bbox — that is a design constraint, not a crash.
- GEOX will not paper over Macrostrat 500 — that is "no data," not a fabricated column.
- GEOX will not raise a verdict — it issues signals only. arifOS seals.
- GEOX will not propagate ghost capabilities. Surfaces are gated (`SURFACE_DRIFT` middleware); raw_live > canonical means the runtime hasn't caught up — **redeploy**, do not paper over.

---

## Quickstart (engineer)

```bash
# 1. clone + install
git clone https://github.com/ariffazil/GEOX
cd GEOX
uv sync

# 2. local MCP (port 8081)
uv run python -m geox_mcp.server --host 127.0.0.1 --port 8081

# 3. verify the public surface
curl -s http://127.0.0.1:8081/health
curl -s http://127.0.0.1:8081/drift

# 4. surface regen (when you add a tool)
uv run python scripts/generate_all_surfaces.py

# 5. federation gate (constitutional hygiene)
bash scripts/governance-gate.sh

# 6. tests
PYTHONPATH=src pytest tests/ -q --tb=short
```

Live MCP endpoint: https://geox.arif-fazil.com/mcp

---

## Provenance (sources of truth, ordered by freshness)

1. `:8081/health` and `:8081/drift` — runtime truth, beats prose
2. `registry.py::CANONICAL_PUBLIC_TOOLS` — gate-enforced surface
3. `CANONICAL_PUBLIC_SURFACE.json` — generated from (2)
4. `FEDERATION_CONTRACT.md` — GEOX's contract with the federation
5. `arifOS/docs/FEDERATION.md` — canonical federation source
6. This README — explainer; the gates above still beat it

When something disagrees, follow the order top-down.

---

## Recent changes (2026-09-30)

- **NW Borneo Collision System registry** (Arif ENTERPRISE synthesis relay): 6 basin entities, one-system-three-positions ontology, parent + 5 positions (lower plate / foredeep / upper plate / crustal province / fossil trench). Event registry with one event → three expressions per position. Live in `resources/basins/nw_borneo_collision_system/`.
- **Copilot review fixes** (`27bdfbaa`): event registry hoisted to top-level lane so it survives MCP 4 KB compaction; aliases added for DG / Kinabalu / NWB Trough / Layang Basin / operator-colloquial names; cross-basin evidence paths fixed (`../nw_borneo_collision_system/` not `../../`); `crystalline_bassment_default` → `crystalline_basement_default` typo corrected.

---

## Compliance / lawful use

- **License.** BSL-1.1. Production use needs a paid license from the author.
- **No publish to sovereign DBs.** GEOX reads and computes; it never writes to a DB the federation owns.
- **No field control.** GEOX has no actuator surfaces. Any tool suggesting otherwise is miscategorised.
- **Authority ceiling.** `555_COMPUTE_ONLY`. Anything above that requires arifOS + A-FORGE + the sovereign.

---

## Pointers to federation siblings

- `arifOS` — kernel (judgment, seal). `github.com/ariffazil/arifOS`
- `AAA` — Attention Plane. `github.com/ariffazil/AAA`
- `A-FORGE` — execution (mutation after SEAL). `github.com/ariffazil/A-FORGE`
- `WEALTH` — capital compute. `github.com/ariffazil/WEALTH`
- `WELL` — vitality mirror. `github.com/ariffazil/WELL`
- `HERMES` — inbound gateway (sovereign runtime home). `github.com/ariffazil/HERMES`
- `arifFlow` — receipt metabolism. `github.com/ariffazil/arifFlow`
- `FRAME` — independent observer. `github.com/ariffazil/FRAME`

Topology SOT: `/root/AAA/federation/organs.yaml` (machine) + `/root/AAA/docs/ORGAN.md` (human). Live `/health` still beats both.

---

DITEMPA BUKAN DIBERI — Forged, Not Given.
