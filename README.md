# GEOX — Earth Intelligence Engine

![GEOX-27 Canonical Tools](https://img.shields.io/badge/GEOX-26_Canonical_Tools-0b7285)
![port 8081](https://img.shields.io/badge/port-8081-0b7285)
![schema 2026.10.01](https://img.shields.io/badge/schema-2026.10.01-0b7285)
![authority 555_COMPUTE_ONLY](https://img.shields.io/badge/authority-555__COMPUTE__ONLY-0b7285)

> The badge URL above is **hand-maintained**. `generate_all_surfaces.py` rewrites the
> badge *alt-text* (`GEOX-27 Canonical Tools`) but its regex matches whitespace, not the
> underscores in the shields.io URL — so a stale count in the URL is invisible to the
> drift gate. Check it by eye when the count changes.

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

Every row below was read from the live organ, not from a design document. Re-probe before trusting it — this table is a snapshot, not an oracle.

| Fact | Live (observed 2026-10-01) |
|---|---|
| Health | `GET http://127.0.0.1:8081/health` → HTTP 200, `"status": "healthy"` |
| Kernel verdict | `"kernel_verdict": "HOLD"` — GEOX is compute-only and never self-seals; judgment belongs to arifOS |
| Port | `8081` (local), public MCP at `https://geox.arif-fazil.com/mcp` |
| Process | `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081` |
| Unit | `geox-mcp.service` |
| Source repo | `/root/GEOX` → `github.com/ariffazil/GEOX` |
| Runtime | `/opt/geox` (FHS). Source ≠ runtime until deploy. |
| **Canonical MCP tools** | **26** (`registry.py::CANONICAL_PUBLIC_TOOLS` — the only truth) |
| **Live tools observed** | **26** on `:8081/drift` — `canonical_count=26`, `live_count=26`, `drift_count=0`, `gap_count=0`, `ok=true` |
| **Generated surfaces** | `tools.json`, `tools_sot.yaml`, `llms.txt`, `CANONICAL_PUBLIC_SURFACE.json`, `contracts/tools.yaml`, this `README.md`'s badge — all **26**, gated by CI |
| Surface drift | **false** — source surface and live surface agree at 26 |
| Internal / ghost names | 22 in `CANONICAL_PUBLIC_SURFACE.json` internal set — executable in-process, never on `tools/list` |
| Runtime commit lag | live `git_version: geox-3f344b84` (2026-09-30); source HEAD `17802197` (2026-10-01) — 105 commits behind, but the **tool surface already agrees**, so this lag is not a surface defect |
| Authority | `555_COMPUTE_ONLY` — Earth evidence only. Judgment is arifOS. Mutation is A-FORGE. |
| Domain law | `NATURAL_LAW` |
| Contract epoch | `2026-10-01-GEOX-26TOOLS-ZEN` · `schema_version: 2026.10.01` |

**Truth rule.** Live `:8081/health` and `:8081/drift` beat any static count in this file. `registry.py::CANONICAL_PUBLIC_TOOLS` beats every committed surface. If the live count disagrees with the SOT count, **redeploy** — the gap means the runtime hasn't caught up with this code, not that the SOT is wrong.

**On `deployment_drift`.** `/health` also reports `deployment_drift: {drift: false, status: "aligned"}`. Read it carefully: its own `source` field says `arifOS:/api/build-info + /root/arifOS/.git HEAD`, and its commit (`297abcb`) is **not in this repository**. That field measures the arifOS tree, not GEOX — it cannot corroborate a GEOX source↔runtime claim, and this README does not lean on it. The honest GEOX-side lag signal is the `git_version` row above. The `build_info_handler` oracle defect is tracked separately as **Step 4, HELD**; see `/root/AAA/federation/geox_steps_1_3_repair_receipt_2026-10-01.md`.

**There is no longer a tool-count gap.** An earlier revision of this file described a 5-tool gap between an SOT of 31 and a live surface of 25. Both numbers were wrong. The canonical surface is **26**, the live surface is **26**, and the five evidence-spine tools (`calibration_register_witness`, `extract_display_proxy`, `extract_native_trace`, `list_registered_sources`, `register_native_source`) are live and counted. The `31` was a stale `public_count_target` in `tools_manifest.yaml`, not a real surface — see "Open defects" below.

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
│ :8081  ·  MCP  ·  26 public tools  ·  555_COMPUTE_ONLY       │
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

26 tools, grouped by the manifest's `family` field. Tier mix is `A / B / C` (A = default-visible core, B = specialist, C = research). This table is derived from `registry.py` + `tools_manifest.yaml`; regenerate rather than hand-edit.

| Family | Tools | Tier mix |
|---|---:|---|
| Evidence | 7 (`basin`, `claim`, `deep_time`, `paleobiodb_query`, `source`, `spatial`, `temporal`) | A·A·A·B·A·A·A |
| Interpret | 6 (`contrast_metabolize`, `geomechanics`, `petrophysics`, `seismic_compute`, `seismic_interpret`, `well`) | B·B·A·B·A·A |
| Seismic (evidence spine) | 4 (`extract_display_proxy`, `extract_native_trace`, `list_registered_sources`, `register_native_source`) | B·B·B·B |
| Ingest | 3 (`seismic_ingest`, `well_ingest`, `well_qc`) | B·B·A |
| View | 2 (`map`, `surface_status`) | A·A |
| Model | 1 (`geox_model`) | A |
| Prospect | 1 (`geox_prospect`) | A |
| Structural | 1 (`calibration_register_witness`) | B |
| Research | 1 (`geox_glof`) | C |
| **Total** | **26** | 14 A · 11 B · 1 C |

For tool-by-tool authority requirements, see `contracts/tools.yaml`.

> **The GLOF collapse (2026-09-19).** Seven `geox_glof_cascade_*` tools were folded into a
> single mode-dispatched **`geox_glof`** (`run` · `inverse` · `mcmc` · `propagate` · `phase`).
> The seven originals still exist as `visibility: internal` in-process plumbing — they are **not**
> on the public surface and are not counted in the 26. An earlier revision of this README listed
> them as public; that was the arithmetic behind the phantom "31".

---

## Canonical truth and surface drift

`src/geox_mcp/registry.py::CANONICAL_PUBLIC_TOOLS` is the **only** truth about the GEOX
tool surface. It is not a mirror of the manifest, a cache, or a convenience list — it is
the list the middleware gate enforces, so it is the list that decides whether a call is
admitted. Nothing else in this repository is allowed to have an opinion.

Every published surface is **generated** from it by `scripts/generate_all_surfaces.py`.
There are six: `tools.json`, `tools_sot.yaml`, `llms.txt`, `contracts/tools.yaml`,
`src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json`, and this README's badge. Hand-editing
any of them is how a repository comes to disagree with itself while every file still looks
authoritative.

Drift is **gated, not hoped for**. `.github/workflows/surface-drift-gate.yml` regenerates all
six surfaces in memory and compares each against the committed artifact; any mismatch, missing
artifact, or generator crash fails the build closed. It hashes *timestamp-normalised* content,
because five of the six generators embed a wall-clock stamp — without normalisation the gate
would be permanently red and would train everyone to ignore red.

```bash
# regenerate all six surfaces after any registry.py change
python3 scripts/generate_all_surfaces.py

# verify without writing (what CI runs) — exit 0 = in sync
python3 scripts/generate_all_surfaces.py --check
```

Run `--check` before you commit. If it is red, the fix is to regenerate, never to edit the
generated file into agreement — that is the drift reasserting itself by hand.

*Receipt: `/root/AAA/federation/geox_steps_1_3_repair_receipt_2026-10-01.md` (Lane 333d, Step 1 — gate design, timestamp-normalisation rationale, and both positive/negative controls).*

---

## RT1 recovery

RT1 is the guard that rejects a tool name which is not on the canonical surface. Rejecting is
only half the job — the caller still has to be told what to call instead.

The recovery suggestion is **derived from the registry at call time**, not a hardcoded string.
That distinction is the whole point: a literal recommendation is an unfalsifiable claim. If the
named tool is later renamed, ghosted, or dropped from every pack, the literal keeps recommending
something the caller cannot actually reach. That is exactly what happened — RT1 said "use
`geox_surface_status`" while that tool sat in **no capability pack**, invisible under all four
discovery profiles. The instruction was syntactically valid and semantically void.

Derivation is in `registry.py::derive_recovery_tool`, and the invariant
**`recommended_next ⊆ callable_surface`** is enforced in code at
`src/geox_mcp/geox_middleware.py`. A candidate must be in `public_tool_names()`, non-mutating
(`OBSERVE` class), and match a discovery-shaped name pattern. If nothing qualifies, the response
carries **`recommended_next: null`** and says so is a registry defect — it never invents a name.
Derivation failing open is also refused: if derivation raises, RT1 **still blocks**. A missing
hint must not open the gate.

Covered by `tests/test_rt1_recovery_derivation.py` (287 lines, 18 tests), including a
no-literal regression guard that asserts `geox_surface_status` does not appear in the RT1 block,
and an end-to-end test asserting the derived tool is genuinely discoverable — the two facts that
disagreed during the incident now agree permanently, by assertion rather than by convention.

*Receipt: `/root/AAA/federation/geox_steps_1_3_repair_receipt_2026-10-01.md` (Lane 333d, Steps 2–3).*

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

All **26** tools on the public MCP surface, grouped by family. The canonical list is the gate — additions and removals require an `arifOS` seal. Names below are exactly as they appear in `registry.py::CANONICAL_PUBLIC_TOOLS`; `tools/list` must equal this set.

### Basin / Evidence (7)
- `geox_basin` — Mode-dispatched basin profile. Modes: overview · petroleum_system · stratigraphy · play_fairway · risk · contradiction_scan · macrostrat_units · macrostrat_columns · macrostrat_lithologies · macrostrat_strat_names · macrostrat_intervals · macrostrat_fossils · macrostrat_geologic_map · macrostrat_cache_warm. The basin directory contains the **NW Borneo Collision System** ontology (parent + 5 positions) — read `resources/basins/nw_borneo_collision_system/basin_profile.yaml` for the event registry.
- `geox_claim` — Unified claim engine (create · validate · challenge · seal · attach · falsify · discover · synthesize · abduct · contradict · spatial_block · ingest_literature · scan). F3 honesty: present tense is a claim, not status. **`LIMITED_MUTATE`** in seal mode — the only public tool that can mutate.
- `geox_deep_time` — DDE Ontology + Macrostrat neuro-symbolic reasoning for stratigraphic queries.
- `geox_paleobiodb_query` — Paleobiology Database (PBDB v1.2) taxa / occurrences / biozones / age intervals.
- `geox_source` — Source rock (TOC, kerogen, maturity, ΔlogR) + diagenesis compaction models.
- `geox_spatial` — H3 hexagonal indexing, LanceDB vector store, STAC catalog query.
- `geox_temporal` — Decline curves, reserve replacement ratio, basin lifecycle, licensing cadence.

### Interpret (6)
- `geox_contrast_metabolize` — ISOLATE → MEASURE → CLASSIFY (≥3 stratigraphic trap hypotheses).
- `geox_geomechanics` — Bulk/shear/Young modulus, Poisson ratio, acoustic impedance, stress polygon.
- `geox_petrophysics` — Vsh / porosity / Sw / permeability / net pay / LEM inference / QC. Mode-dispatched.
- `geox_seismic_compute` — AVO forward modelling (Zoeppritz / Shuey / LMR / Castagna).
- `geox_seismic_interpret` — One semantic capability: horizon_contrast, fault_sticks, volume_frame, blend, structure_validate, interpret (≥3 hypotheses), interpret_section, rsi_pipeline, segy_slice. Includes the J-space manifold drift guard.
- `geox_well` — Mode-dispatched well operations (view · desk).

### Ingest (3)
- `geox_seismic_ingest` — SEG-Y inspection + metadata extraction.
- `geox_well_ingest` — LAS / SEG-Y / DST / deviation / tops ingest. `overwrite=true` escalates it to `LIMITED_MUTATE`.
- `geox_well_qc` — Quality control (depth monotonicity, null %, physical ranges).

### View (2)
- `geox_map` — Geological map pipeline (layers_list · scene_plan · render_preview · export_package).
- `geox_surface_status` — Canonical registry probe: public surface truth (count, `canonical_tools`, verdict). Self-witness for the surface SOT, and the tool RT1 derives as the recovery path. **Pinned in `earth_core`** so it is visible under every discovery profile. *(Added to this inventory 2026-10-01 — it was callable but undocumented, and unpacked; see "RT1 recovery".)*

### Model / Prospect (2)
- `geox_model` — Joint inversion (gravity/mag), MT forward, deterministic 2D cross-section, GemPy 3D implicit structural modeling.
- `geox_prospect` — Volumetrics, POS, EVOI, risk (screen · evaluate).

### Structural (1)
- `geox_calibration_register_witness` — Register a `CalibrationWitness` for structural interpretation. Validates schema, checks completeness blockers (missing axes, depth-without-velocity). Returns `VOID` on bad input, `HOLD` on missing calibration.

### Seismic evidence spine (4) — Sep 15, 2026, PR #177
- `geox_register_native_source` — Register a native SEG-Y source for trace extraction. Validates file existence, computes SHA256, extracts binary header metadata. Authority downgrade: `OPERATOR_APPROVED` without an actor → `UNVERIFIED`.
- `geox_list_registered_sources` — List registered native sources with classification, authority, trace count, sample metadata.
- `geox_extract_native_trace` — Extract a native seismic trace with full provenance (`NativeTraceRef` with permitted/prohibited downstream uses). `HOLD` for unverified authority, restricted data, or missing source.
- `geox_extract_display_proxy` — Pixel-derived proxy array from a raster seismic image (`DISPLAY_DERIVED_PROXY` — explicitly NOT usable for amplitude preservation, AVO classification, phase certification, native seismic-to-well tie acceptance, or quantitative prospect/fault-seal decisions).

### Research (1)
- `geox_glof` — Unified GLOF multi-phase cascade simulation. Modes: `run` (full cascade in one call) · `inverse` (Bayesian grid-search) · `mcmc` (MCMC posterior) · `propagate` (Saint-Venant 1D) · `phase` (yield-surface debug). Multi-phase physics: solid dam → granular debris → liquid flood (Mohr-Coulomb + Saint-Venant + 33D zen-33 state). Tier C, `MUTATE`, visible only under `research` / `full` profiles.
  - The seven `geox_glof_cascade_*` tools it replaced are retained as **internal** in-process plumbing (2026-09-19 collapse, 333 ARCHITECT). They are not on the public surface, not discoverable, and not part of the 26.

### Not on the public surface
22 internal / ghost names are executable inside GEOX but hidden from `tools/list` — see the `internal` set in `src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json`. `geox_contradiction_scan` is deliberately absent from the canonical list (F13 2026-09-22): audit-internal-only, with no external consumer. RT1 rejecting an external call to it is the design, not a bug — do not "fix" it by adding it.

### Capability packs and discovery profiles

Packs are declared in `tools_manifest.yaml:capability_packs`; visibility policy lives in `registry/capability_registry.yaml`.

| Pack | Tier | Tools | Contents |
|---|---|---:|---|
| `earth_core` | A | **14** | Default discovery surface, visible to every agent. Includes `geox_surface_status` (pinned). |
| `earth_specialist` | B | **6** | Opt-in after task declaration: seismic computation, geomechanics, data ingestion, paleobiology. |
| `earth_research` | C | **1** | Advanced/experimental: `geox_glof` cascade simulation and Bayesian inversion. |

| Profile | Visible packs | Tools |
|---|---|---:|
| `default` | `earth_core` | **14** |
| `specialist` | + `earth_specialist` | **20** |
| `research` | + `earth_research` | **21** |
| `full` | alias of `research` | **21** |

`geox_surface_status` is pinned in `earth_core` precisely so it is visible to **every** profile — that is what makes the RT1 recovery instruction resolvable.

Five public tools belong to **no pack** and are therefore invisible under all four profiles, the same defect class that hid `geox_surface_status`: `geox_calibration_register_witness`, `geox_extract_display_proxy`, `geox_extract_native_trace`, `geox_list_registered_sources`, `geox_register_native_source`. They are callable (RT1 admits them) but not discoverable. Packing them is a discovery-policy decision, held for the sovereign — see "Open defects".

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

# 4. surface regen (when you add a tool) — then verify
uv run python scripts/generate_all_surfaces.py
uv run python scripts/generate_all_surfaces.py --check   # exit 0 = in sync; this is what CI runs

# 5. federation gate (constitutional hygiene)
bash scripts/governance-gate.sh

# 6. tests (includes the RT1 recovery derivation suite)
PYTHONPATH=src pytest tests/ -q --tb=short
PYTHONPATH=src pytest tests/test_rt1_recovery_derivation.py -q   # 18 tests
```

Live MCP endpoint: https://geox.arif-fazil.com/mcp

CI enforces surface agreement on every push and pull request via `.github/workflows/surface-drift-gate.yml`. Regenerate before you commit; a red gate means your surfaces disagree with `registry.py`.

---

## Open defects (known, held, not papered over)

Documented so this README does not imply a cleaner repository than the one that exists. Each is held because fixing it touches canonical records or deploy surface — F13-class, the sovereign's call. Full detail in `/root/AAA/federation/geox_steps_1_3_repair_receipt_2026-10-01.md` §7.

| Defect | State | Why it is held |
|---|---|---|
| `public_count_target: 31` in `tools_manifest.yaml` | Live invariant failing continuously — `surface_attestation()` returns `ok=False, error=SURFACE_COUNT_DRIFT` on every call | Real surface is 26. Nothing gates on it. Correcting the target edits a canonical record. This stale 31 is the origin of the phantom count this README used to carry. |
| `capability_registry.yaml` advertises `research → 26` | Code returns **21** | The `tool_count` fields are read by no Python (grep-verified) — pure prose that drifted. Closing the gap means deciding pack contents, a discovery-policy call. |
| `registry.py::tools_for_profile` docstring | Repeats the same wrong `13 / 19 / 26` numbers | Docstring only; the code is correct. Fix is trivial but lives next to canonical surface logic. |
| 5 public tools in no capability pack | Callable but undiscoverable under all four profiles | Same defect class as the `geox_surface_status` bug that Step 2 fixed. `geox_list_registered_sources` in particular looks like it should be discoverable. Packing them is policy. |
| `build_info_handler` `/health` oracle tautology | **Step 4 — HELD** | `/health` reports `deployment_drift.drift: false` while reading a commit (`297abcb`) that is not in this repository — it measures the arifOS tree, so it cannot corroborate a GEOX source↔runtime claim. Not touched by Lane 333d; not touched here. |
| `.github/workflows/09-boundary-ratchet.yml` | Committed **git merge-conflict markers** (lines 26, 32) since `79e372e5` | Invalid YAML — the workflow cannot parse, so the boundary ratchet has been silently not running. Scar-class: a broken gate looks identical to a passing one. Two-line fix, but it needs a ruling on which action versions survive. |
| 12 pre-existing test failures | Unchanged by Steps 1–3 (baseline 12 / after 12, +18 new passing) | Most trace to `public_count_target: 31` and a ZEN-24 frozen-count assertion. Fixing them means changing canonical counts. |

---

## Provenance (sources of truth, ordered by freshness)

1. `:8081/health` and `:8081/drift` — runtime truth, beats prose
2. `registry.py::CANONICAL_PUBLIC_TOOLS` — gate-enforced surface, the only truth
3. `CANONICAL_PUBLIC_SURFACE.json`, `tools.json`, `tools_sot.yaml`, `contracts/tools.yaml`, `llms.txt` — all generated from (2), all CI-gated against it
4. `FEDERATION_CONTRACT.md` — GEOX's contract with the federation
5. `arifOS/docs/FEDERATION.md` — canonical federation source
6. This README — explainer; the gates above still beat it

When something disagrees, follow the order top-down. Note that `deployment_drift` inside `/health` is **not** a GEOX source-of-truth (see "Open defects") — use `git_version` for the runtime-lag signal.

---

## Recent changes (2026-10-01)

- **Surface truth repaired to 26** (Lane 333d, Steps 1–3): CI surface-drift gate added (`.github/workflows/surface-drift-gate.yml`) with timestamp-normalised hashing and both positive/negative controls proven; `geox_surface_status` pinned into `earth_core` so it is discoverable under all four profiles; RT1's recovery suggestion replaced with registry-derived lookup enforcing `recommended_next ⊆ callable_surface`. 287-line derivation test suite added (18 tests). Full regression baseline compared, not assumed: **12 failures before, 12 after — same names, zero new**; +18 new passing.
- **This README refreshed to canonical truth** (Lane 888a): badge, live-reality table, both inventories, capability packs, provenance order, and a new "Open defects" register. The previous revision claimed **31** canonical tools, listed seven `geox_glof_cascade_*` names that are internal plumbing, and omitted the live `geox_glof` and `geox_surface_status`. It also described a 5-tool SOT↔live gap that does not exist — live and canonical are both 26.
- **NW Borneo Collision System registry** (2026-09-30, Arif ENTERPRISE synthesis relay): 6 basin entities, one-system-three-positions ontology, parent + 5 positions (lower plate / foredeep / upper plate / crustal province / fossil trench). Event registry with one event → three expressions per position. Live in `resources/basins/nw_borneo_collision_system/`.
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

Last regenerated: 2026-10-01 (Lane 333d surface-drift-gate green; surface in sync with registry.py)

Canonical count: **26** · `schema_version: 2026.10.01` · `contract_epoch: 2026-10-01-GEOX-26TOOLS-ZEN` · source HEAD `17802197`

DITEMPA BUKAN DIBERI — Forged, Not Given.
