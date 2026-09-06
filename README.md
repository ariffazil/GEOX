<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
federation_release: v2026.08.26
last_verified: 2026-09-06T15:05:00Z
source_commit: e16c95cb+ (this README commit supersedes)
live_runtime: /opt/geox · systemd geox-mcp.service · 127.0.0.1:8081
tools_live: 26 (canonical, live-witnessed via :8081/health)
mcp_apps_ui: 12 (GEOX_APPS keys well_desk…workspace_v1)
authority_ceiling: 555_COMPUTE_ONLY
domain_law: NATURAL_LAW
truth_rule: live :8081/health beats any static count in this file
-->

# GEOX — Earth Intelligence Engine

Physics-grounded geological intelligence for exploration, hazard assessment, and earth science.

GEOX transforms subsurface data — seismic, wells, basin models — into auditable geological evidence. Every claim is traceable. Observation, derivation, and interpretation stay separate. **GEOX computes. It does not adjudicate. It does not seal.**

**Licensed under the Business Source License 1.1 (BSL-1.1).** Production use requires a license from the author.

---

## Live reality (probe this, do not trust prose)

| Fact | Live 2026-09-06 |
|---|---|
| Health | `GET http://127.0.0.1:8081/health` → `healthy` |
| Process | `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081` |
| Unit | `geox-mcp.service` |
| Source repo | `/root/GEOX` → `github.com/ariffazil/GEOX` |
| Runtime | `/opt/geox` (FHS). Source ≠ runtime until deploy. |
| Canonical MCP tools | **26** (`tools_loaded` / `canonical_tools` on `/health`) |
| Ghost / internal names | 22 ghosted in `geox_mcp.registry` — not on the public surface |
| Authority | `555_COMPUTE_ONLY` — Earth evidence only. Judgment is arifOS. Mutation is A-FORGE. |
| Domain law | `NATURAL_LAW` |
| Public MCP | `https://geox.arif-fazil.com/mcp` |

Stale counts still circulating in other repos (AAA `ORGAN.md` / `organs.yaml` snapshot 2026-07-30 said **33** tools; this README previously said **19**). **Live health wins.**

---

## The Problem

Traditional earth science workflows are slow, siloed, and dependent on scarce domain expertise. GEOX encodes that work into a system that can:

- Process seismic and interpret structures with physics guards
- Run petrophysics on LAS consistently
- Profile basins from local evidence (Malay Basin is the richest local pack)
- Assess geohazards (GLOF cascade family) without pretending to be a court
- Query paleobiology with spatial-temporal context

It will also **refuse**. A 33° map bbox is too big — that is a design constraint, not a crash. Macrostrat 500 is “no data,” not a fabricated column. Empty SUCCESS is a lie; GEOX is not allowed to stamp `ok: true` on an empty basin envelope.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ GEOX Earth Intelligence                                      │
│ :8081  ·  MCP  ·  26 public tools  ·  555_COMPUTE_ONLY       │
├──────────────────────────────────────────────────────────────┤
│  Well / Petrophysics │ Seismic │ Basin │ Map │ Deep time     │
│  Geomechanics        │ Source  │ Claim │ GLOF cascade        │
│                                                              │
│  Witness layer (Δ·Ω·Ψ)                                       │
│  OBS (observed) → DER (derived) → INT (interpreted)          │
└──────────────────────────┬───────────────────────────────────┘
                           │ MCP (evidence only)
                    ┌──────▼──────┐
                    │ arifOS      │  :8088  JUDGE_ONLY
                    │ A-FORGE     │  :7071/:7072  execute after seal
                    └─────────────┘
```

APEX `G = (A·P·E·X)^(1/4)` is the federation feasibility envelope. GEOX feeds **Earth evidence** into that envelope. It is not APEX. A false SUCCESS from GEOX contaminates the E-dial.

---

## Quick Start

### Live VPS (this machine — truth)

```bash
systemctl status geox-mcp.service
curl -sf http://127.0.0.1:8081/health
```

Entry point is `python3 -m geox_mcp.server`, **not** `geox.server`.

### Local development

```bash
git clone https://github.com/ariffazil/GEOX.git
cd GEOX
pip install -e .
python -m geox_mcp.server --host 127.0.0.1 --port 8081
```

Docker Compose exists for portable builds. **It is not how KVM8 runs GEOX.** Live is systemd + `/opt/geox`.

---

## Canonical public tools (26)

`geox_well_ingest` · `geox_well_qc` · `geox_well` · `geox_petrophysics` · `geox_seismic_ingest` · `geox_seismic_compute` · `geox_seismic_interpret` · `geox_basin` · `geox_map` · `geox_deep_time` · `geox_geomechanics` · `geox_source` · `geox_spatial` · `geox_temporal` · `geox_model` · `geox_claim` · `geox_prospect` · `geox_paleobiodb_query` · `geox_contrast_metabolize` · `geox_glof_cascade_{initialize,step,phase,inverse,metabolize,mcmc_inverse,propagate}`

`geox_workspace` was removed from the public manifest (2026-09-06 Z2). Do not document it as live.

### 2026-09-06 surface repair (witness, not theatre)

| Tool | Failure | Live after repair |
|---|---|---|
| `geox_map` | `NameError: _map_layers_list` | layers_list returns catalogue |
| `geox_basin` | `ok: true` on empty envelope | Malay Basin PASS with observed/derived/interpreted; unknown basin is honest ERROR |
| `geox_deep_time` | nested kwargs / empty | `tectonic_context` returns Sunda Arc plate setting; Macrostrat 500 is `ok: false` |
| `geox_geomechanics` | hard-fail / moduli buried | Physics9 moduli at top-level; missing state + `depth_m` → Zoback polygon, labelled |

---

## Malay Basin (what GEOX actually holds)

Local pack under `resources/basins/malay_basin/` (Madon 1999/2004/2010/2021): rift-to-sag, Groups A–M, dual overpressure compartments (centre ~1900–2000 m Group E/F; flank ~2600–3000 m Group L), ~40% of Malaysia hydrocarbons in the review period.

**Not in this organ:** Malay LAS time-series, live GNSS strain, QC’d pre-eruptive thermal. Demo LAS on disk is Volve / Sandakan, not Malay. Coverage 0 is not a pressure correlation.

Arc volcanism (Sunda) and back-arc petroleum (Malay) share a plate family and **do not share a magma kitchen**. Elevated arc activity is not a drill trigger.

---

## Epistemic labels

| Label | Meaning |
|---|---|
| **OBS** | Directly observed from data |
| **DER** | Derived via known physical laws |
| **INT** | Interpreted |
| **SPEC** | Hypothesis, needs validation |

Confusing speculation with observation is how dry holes and fake seals are born.

---

## Federation role

GEOX is the **earth witness**. Outputs are evidence for arifOS (F1–F13). Sister repos:

- [arifOS](https://github.com/ariffazil/arifOS) — kernel / judgment
- [AAA](https://github.com/ariffazil/AAA) — control plane / routing
- [A-FORGE](https://github.com/ariffazil/A-FORGE) — execution
- [WEALTH](https://github.com/ariffazil/WEALTH) — capital compute
- [WELL](https://github.com/ariffazil/WELL) — vitality mirror
- [arifFlow](https://github.com/ariffazil/arifFlow) — metabolism

Topology SOT: `/root/AAA/federation/organs.yaml` (machine) and `/root/AAA/docs/ORGAN.md` (human). **Live `/health` still beats both.**

---

## Documentation

- [SOT audit 2026-09-06](docs/SOT_AUDIT_2026-09-06.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)
- [Security](SECURITY.md)

## License

**Business Source License 1.1 (BSL-1.1)** — see [LICENSE](LICENSE). Production licensing: arifbfazil@gmail.com.

**DITEMPA BUKAN DIBERI** — Forged, Not Given.
