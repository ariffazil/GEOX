<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
federation_release: v2026.09.15
last_verified: 2026-09-15T09:15:00Z
source_commit: e68ae5e2
apex_zen: A2A delegates ⊥ MCP equips ⊥ ACT mutates ⊥ arifOS governs ⊥ F13 decides
live_health: healthy · 555_COMPUTE_ONLY · evidence only
live_runtime: /opt/geox · systemd geox-mcp.service · 127.0.0.1:8081
tools_live: 31 (canonical, live-witnessed via :8081/health — 5 evidence spine tools added 2026-09-15)
mcp_apps_ui: 13 (GEOX_APPS keys well_desk…calibration-witness)
authority_ceiling: 555_COMPUTE_ONLY
domain_law: NATURAL_LAW
truth_rule: live :8081/health beats any static count in this file
evidence_spine: Phase 0+1+2A+2B deployed+verified E2E (PR #177, 10 commits on main, 35 tests + 5 live MCP calls)
-->

# GEOX — Earth Intelligence Engine

![GEOX-31 Canonical Tools](https://img.shields.io/badge/GEOX-31_Canonical_Tools-0b7285)

Physics-grounded geological intelligence for exploration, hazard assessment, and earth science.

GEOX transforms subsurface data — seismic, wells, basin models — into auditable geological evidence. Every claim is traceable. Observation, derivation, and interpretation stay separate. **GEOX computes. It does not adjudicate. It does not seal.**

**Licensed under the Business Source License 1.1 (BSL-1.1).** Production use requires a license from the author.

| Audience | What you get |
|---|---|
| **Human / earth team** | A specialist that keeps uncertainty labelled. Not a generic chat about rocks |
| **Agent / A2A** | MCP evidence tools only. No publish. No field control. No silent escalation to A-FORGE write |
| **Institution** | A bounded subsurface organ you can plug in: physics in, evidence out, kernel still holds the gavel |

Live MCP: `https://geox.arif-fazil.com/mcp`

---

## Live reality (probe this, do not trust prose)

| Fact | Live 2026-09-15 |
|---|---|
| Health | `GET http://127.0.0.1:8081/health` → `healthy` |
| Process | `/opt/geox/.venv/bin/python3 -m geox_mcp.server --host 127.0.0.1 --port 8081` |
| Unit | `geox-mcp.service` |
| Source repo | `/root/GEOX` → `github.com/ariffazil/GEOX` |
| Runtime | `/opt/geox` (FHS). Source ≠ runtime until deploy. |
| Canonical MCP tools | **31** (`tools_loaded` / `canonical_tools` on `/health`) |
| Ghost / internal names | 22 ghosted in `geox_mcp.registry` — not on the public surface |
| Authority | `555_COMPUTE_ONLY` — Earth evidence only. Judgment is arifOS. Mutation is A-FORGE. |
| Domain law | `NATURAL_LAW` |
| Public MCP | `https://geox.arif-fazil.com/mcp` |

Stale counts still circulating in other repos (AAA `ORGAN.md` / `organs.yaml` snapshot 2026-07-30 said **33** tools; this README previously said **19** then **26**). **Live health wins.**

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
│ :8081  ·  MCP  ·  31 public tools  ·  555_COMPUTE_ONLY       │
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

## Evidence Spine — Calibration & Structural Interpretation

**Core principle:** GEOX has the physics. It needs evidence-preserving orchestration plus human physical grounding — not another library.

### Native vs Display Data Lanes

| Property | NATIVE_TRACE | DISPLAY_DERIVED_PROXY |
|---|---|---|
| Input | Registered SEG-Y | PNG, JPEG, screenshot |
| Amplitude | CONDITIONAL (never PRESERVED without proof) | DISPLAY_TRANSFORMED |
| Well tie | Permitted with true trace | Exploratory visual only |
| AVO / quantitative | Possible under proper conditioning | **BLOCKED** |
| Coverage cap | 1.0 | 0.25 |

### Calibration Witness

`ui://geox/calibration-witness` — MCP App for interactive measurement acquisition.

Human geologist clicks reference points → agent computes scale → structural gates advance:

```
UNMEASURED → CALIBRATED_INPUT_AVAILABLE → COMPUTABLE → PASS|WARN|KILL|HOLD
```

Calibration never auto-PASSes physical gates. Each K-gate (K-DIP, K-DL, K-THROW, K-RESTORE, K-VEL) independently states evidence consumed, conversions applied, uncertainty, and remaining blockers.

### SGR (Shale Gouge Ratio)

Pure computation kernel. **NOT a seal verdict.** No universal thresholds.

```
SGR = Σ(Vsh × Δz) / throw × 100%
```

Output states `NOT_A_SEAL_VERDICT`. Thresholds are basin/play-specific, configured with evidence and a reviewer.

### Gate Statuses

| Status | Meaning |
|---|---|
| UNMEASURED | No calibration or evidence available |
| CALIBRATED_INPUT_AVAILABLE | Calibration present, interpretation inputs pending |
| COMPUTABLE | All inputs present, computation possible |
| PARTIALLY_MEASURED | Some gates measured, some not |
| PASS | All criteria met |
| WARN | Passed with caveats |
| KILL | Failed — interpretation rejected |
| HOLD | Blocked — requires resolution |

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

## Canonical public tools (31)

### Capability Graph

```
L0  Tools                    ✅  (26 public, 54 internal)
L1  Family Taxonomy          ✅  (7 families)
L2  Tier Taxonomy            ✅  (A=13 Core, B=6 Specialist, C=7 Research)
L3  Capability Packs         ✅  (earth_core, earth_specialist, earth_research)
L4  Discovery Filtering      ✅  (default=13, specialist=19, research=26)
L5  Workflow Orchestration   ✅  (4 geological workflows)
L6  Earth Capability Graph   ✅  (26 nodes, 32 edges, 6 hub tools)
```

### By Family

| Family | Tools | Tier |
|---|---|---|
| **Evidence** | `geox_basin` · `geox_claim` · `geox_deep_time` · `geox_paleobiodb_query` · `geox_source` · `geox_spatial` · `geox_temporal` | A + B |
| **Ingest** | `geox_well_ingest` · `geox_well_qc` · `geox_seismic_ingest` | A + B |
| **Interpret** | `geox_well` · `geox_petrophysics` · `geox_seismic_interpret` · `geox_seismic_compute` · `geox_geomechanics` · `geox_contrast_metabolize` | A + B |
| **Model** | `geox_model` | A |
| **Prospect** | `geox_prospect` | A |
| **View** | `geox_map` | A |
| **Research** | `geox_glof_cascade_{initialize,step,phase,inverse,metabolize,mcmc_inverse,propagate}` | C |

### Discovery Profiles

| Profile | Packs | Tools |
|---|---|---|
| `default` | earth_core | 13 |
| `specialist` | core + specialist | 19 |
| `research` | all packs | 26 |

### Workflows

| Workflow | Steps | Output |
|---|---|---|
| `well_to_correlation` | basin → well → well_qc → petrophysics → deep_time → model → map | CorrelationPackage |
| `seismic_to_prospect` | basin → seismic_ingest → seismic_compute → seismic_interpret → geomechanics → model → prospect → claim | ProspectEvidencePackage |
| `basin_screening` | basin → spatial → temporal → source → deep_time → claim → prospect → map | PlayFairwaySummary |
| `glof_uncertainty` | initialize → propagate → phase → inverse → mcmc_inverse → metabolize | UncertaintyReport |

### Hub Tools (cross-workflow convergence)

| Hub | Workflows | Role |
|---|---|---|
| `geox_basin` | 3 | Universal context provider |
| `geox_model` | 2 | Integration convergence |
| `geox_prospect` | 2 | Decision convergence |
| `geox_claim` | 2 | Evidence registration |
| `geox_map` | 2 | Presentation convergence |
| `geox_deep_time` | 2 | Temporal framework |

### Flat list (for reference)

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
- [AAA](https://github.com/ariffazil/AAA) — Attention Plane / routing
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
