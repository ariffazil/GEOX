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
