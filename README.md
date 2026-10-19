<!-- SOT-MANIFEST
mcp_tools_live: dynamic_from_tools_list
truth_rule: live :18081/health + tools/list beat any static count in prose
-->

<p align="center">
  <img src="docs/assets/geox-hero.png" alt="GEOX — subsurface uncertainty in, physics-grounded labelled evidence out, governed handoff to the judge (compute only)" width="100%">
</p>

# GEOX

### Evidence before verdict.

**GEOX is a physics-grounded earth intelligence organ.** It turns subsurface data — seismic, well logs, basin models, rock images — into labelled, falsifiable geological evidence and hands it to the federation's judge. It never seals anything itself.

[What works](#what-works-today) · [30-second proof](#30-second-proof) · [What GEOX does](#what-geox-does) · [Connect](#connect-an-mcp-client) · [Current verified state](#current-verified-state) · [Known gaps](#evidence--gaps) · [Security](#license--security)

| Earth team | Agent / A2A | Developer | Institution / auditor | Researcher |
|---|---|---|---|---|
| A specialist that keeps uncertainty labelled — competing hypotheses with falsifiers, never "the" answer | MCP evidence tools only: no publish, no field control, no silent escalation | Clone → `uv sync` → local organ on port 18081; every surface generated from one registry | A bounded subsurface organ: physics in, evidence out, provenance-scanned data packs, [gaps published](#evidence--gaps) | Deep time, paleobiology (PBDB), basin packs — every claim labelled `OBS`/`DER`/`INT`/`SPEC`/`UNKNOWN` |

[![License](https://img.shields.io/badge/license-BSL--1.1-blue?style=flat-square)](./LICENSE)
[![MCP](https://img.shields.io/badge/MCP-streamable__HTTP-0b7285?style=flat-square)](#connect-an-mcp-client)
[![GEOX-27 Canonical Tools](https://img.shields.io/badge/GEOX-27_Canonical_Tools-0b7285?style=flat-square)](#current-verified-state)
[![Surface drift gate](https://img.shields.io/github/actions/workflow/status/ariffazil/GEOX/surface-drift-gate.yml?label=surface-drift-gate&style=flat-square)](https://github.com/ariffazil/GEOX/actions/workflows/surface-drift-gate.yml)
[![Security](https://img.shields.io/badge/security-reporting-green?style=flat-square)](./SECURITY.md)

<!-- Badge note: the GEOX-NN Canonical Tools badge is GENERATED from registry.py and CI-gated by surface-drift-gate.yml — do not hand-edit its count. -->

> **It computes. It does not adjudicate. It does not seal.**
> Authority ceiling `555_COMPUTE_ONLY` · domain law: natural law (geology, geophysics, physics, stratigraphy) · [BSL-1.1](#license--security) (evaluation use free; production needs a license).

---

## What works today

- **Seismic interpretation bundles with physics gates.** Every bundle carries ≥3 rival stratigraphic hypotheses with explicit falsifiers; `preferred_hypothesis` is always `null` — GEOX qualifies candidates, arifOS seals ([contracts/tools.yaml](./contracts/tools.yaml)).
- **Petrophysics behind QC.** LAS ingest → depth/physical-range QC → Vsh, porosity, Sw, net-pay. Logs that fail physical range checks are refused, not interpreted.
- **Earth Witness v1 — image evidence (`geox_observe`).** Rock / core / outcrop / fossil / seismic-display image → governed `EarthObservationPacket`: competing hypotheses **with their falsifiers**, and `INPUT_REQUIRED` when diagnostics (scale, acid test, polarity) are missing — never a guess. EarthBench 7/7, forbidden-claim rate 0 ([report](./reports/earth_witness/04_earthbench.md)).
- **Surface honesty is gated, not hoped.** CI regenerates every published surface from `registry.py` and compares on each push ([surface-drift-gate.yml](./.github/workflows/surface-drift-gate.yml)); the live organ's `/drift` measured canonical == live at the probe below.
- **Refusals are real outputs.** Oversized map bboxes, Macrostrat 500s, and empty basin envelopes come back as refusals — empty `ok: true` is not permitted.
- **Deterministic Evidence-to-Decision Chain (`geox_core.evidence_chain`).** Schema-governed evidence objects (`schemas/earth/evidence_chain.schema.json`) with spatial CRS, vertical datum, and explicit $\pm \sigma$ uncertainty envelopes. Performs mathematical model discrimination and kill tests (PASS/FAIL/INDETERMINATE) with tri-witness hash ledger (`ARTIFACT_IDENTITY`, `EXECUTION_WITNESS`, `SCIENTIFIC_WARRANT`). Known-answer tested against North Borneo Moho constraint (Sidek et al. 2016; Madon 2025).

## What is not yet proven

- External security evaluation — none published ([SECURITY.md](./SECURITY.md)).
- Earth Witness chat is local-only; public exposure is a pending Class-B decision.
- Five public tools belong to no capability pack — callable but undiscoverable ([gap row](#evidence--gaps)).
- GitHub may still serve dangling pre-rewrite commit SHAs from the 2026-10-08 history purge (follow-up open).
- Whether `geox_temporal` production analytics belong to GEOX or WEALTH — a held federation-policy decision.

Every row, with evidence and why it is held: [Evidence & gaps](#evidence--gaps). We publish what passed, what failed, and what remains unknown — we do not claim maturity beyond our evidence.

---

## 30-second proof

One read-only command against the public organ (verified live 2026-10-16; exact transcript = the block below):

```bash
curl -s https://geox.arif-fazil.com/health | python3 -m json.tool | head -n 12
```

```json
{
    "status": "healthy",
    "kernel_verdict": "HOLD",
    "service": "geox-unified",
    "version": "v2026.10.03",
    "federation_schema_version": "2.0.0",
    "profile": "full",
    "identity": {
        "algorithm": "sha256",
        "value": "geox-70d84f7d",
        "git_version": "geox-70d84f7d",
        "verified": true,
```

What this proves: the organ answers on the **public wire** (`status`), it identifies itself against its own git version (`identity.verified`), and its constitutional posture is `kernel_verdict: HOLD` — GEOX issues signals, judgment belongs to arifOS. Full dev transcript: [docs/QUICKSTART.md](./docs/QUICKSTART.md).

---

## What GEOX does

Five jobs, one rule: **uncertainty labelled at every step**.

| Job | What happens | Tools |
|---|---|---|
| **Seismic evidence** | SEG-Y ingest → native traces → impedance / AVO physics → structural interpretation behind physics gates, ≥3 rival hypotheses (Chamberlin). Raster display extracts stay quarantined as `DISPLAY_DERIVED_PROXY` — never fed to AVO or well-ties without a calibration witness. | `geox_seismic_ingest` · `geox_extract_native_trace` · `geox_seismic_compute` · `geox_seismic_interpret` · `geox_contrast_metabolize` · `geox_extract_display_proxy` · `geox_calibration_register_witness` · `geox_register_native_source` · `geox_list_registered_sources` |
| **Wells & petrophysics** | LAS ingest → QC (depth monotonicity, physical ranges) → Vsh · porosity · Sw · net-pay. QC before interpretation, always. | `geox_well_ingest` · `geox_well_qc` · `geox_well` · `geox_petrophysics` |
| **Basin & deep time** | Macrostrat / ICS context, backstripping, thermal maturity, paleobiology (PBDB), GLOF hazard cascade — "no data" is returned as "no data", never as a fabricated column. | `geox_basin` · `geox_source` · `geox_deep_time` · `geox_paleobiodb_query` · `geox_glof` · `geox_model` · `geox_geomechanics` |
| **Prospect & production math** | Volumetrics, POS, EVOI, decline/RRR as **DER/SPEC advisory ranges with uncertainty** — never booked resources (booking is a WEALTH + human institution act). | `geox_prospect` · `geox_temporal` · `geox_spatial` · `geox_map` |
| **Claims & image evidence** | Claim lifecycle (create → challenge → falsify) and governed image observation: hypotheses + falsifiers + demanded human tests. | `geox_claim` · `geox_observe` · `geox_surface_status` |

Machine surface: [`tools.json`](./tools.json) · per-tool authority: [`contracts/tools.yaml`](./contracts/tools.yaml) · full name inventory: `tools_sot.yaml` — all generated from `registry.py`.

---

## Connect an MCP client

**Endpoint (authenticated):** `https://geox.arif-fazil.com/mcp` — Caddy enforces `P3_AUTH_LITE`: full connectors do OAuth 2.1 + DPoP; simple connectors (Claude.ai, ChatGPT, Cloudflare Workers) send a pre-registered `X-MCP-Client-Id` validated against `oauth/static_clients.yaml`. There is no anonymous `tools/list`. Loopback `127.0.0.1:8081` is unauthenticated on the host only.

```json
{
  "mcpServers": {
    "geox": {
      "url": "https://geox.arif-fazil.com/mcp",
      "headers": { "X-MCP-Client-Id": "<your-registered-client-id>" }
    }
  }
}
```

Every response is an evidence envelope — competing hypotheses **with falsifiers**, explicit `INPUT_REQUIRED` instead of a guess, provenance on every step (real `geox_observe` run, abbreviated):

```json
"hypotheses": [
  { "label": "Limestone (Micrite)", "confidence": 0.72,
    "falsifiers": ["no effervescence with dilute HCl"] },
  { "label": "Dolostone", "confidence": 0.65,
    "falsifiers": ["effervescence on cold unpowdered rock"] }
],
"epistemic": { "claim_tag": "INTERPRET", "state": "INPUT_REQUIRED", "verdict": "PARTIAL",
  "provenance": [ { "step": "geox_observe_intake", "hash": "…" } ] }
```

---

## Current verified state

**Observed at: 2026-10-16T08:49:38Z** · method: `curl -s http://127.0.0.1:8081/health` (runtime self-measurement; the same endpoint is served publicly at `https://geox.arif-fazil.com/health` — probed separately at 08:57Z, same values).

- Organ `geox-unified` reported **healthy**; identity `sha256:geox-70d84f7d` **verified** against its own `git_version`.
- Authority ceiling measured on the wire: `555_COMPUTE_ONLY` — the runtime agrees with its constitution.
- Surface drift `ok: true` (canonical == live, drift 0) — measured via `:8081/drift` at the same probe.
- Probe freshness: `fresh` (age 0 s at probe time).
- `kernel_verdict: HOLD` at probe time — GEOX signals, arifOS adjudicates; GEOX adjudicates nothing itself.

<!-- GEOX:GENERATED:STATUS:START -->
<!-- GENERATED by scripts/generate_readme_status.py — 2026-10-19T18:13Z. Probe beats this snapshot; regenerate rather than hand-edit. -->

- Canonical surface: **27** tools (`registry.py::CANONICAL_PUBLIC_TOOLS` — gate-enforced SOT)
- Live organ (`:8081/drift`): canonical **27** · live **27** · drift **0** · gap **0** · ok **true**
- Runtime commit: `geox-0c62f150` · source HEAD `0c62f150` (`main`) · `main` at `0c62f150` — runtime == source HEAD (deployed current)
- Discovery profiles: default **15** · specialist **21** · research **22** (pack policy, not the gate)
- Internal (hidden, executable in-process): **39** names — `registry.py::INTERNAL_TOOLS`, never on `tools/list`
- Surface attestation: `ok=True` · public_count 27 == target 27 (31-target phantom retired 2026-10-03, commit 78604549)
- Generated surfaces in sync: **run `scripts/generate_all_surfaces.py --check`** (CI-gated; this block is not one of them)
<!-- GEOX:GENERATED:STATUS:END -->

Dynamic state is generated by probe. If this section conflicts with the live endpoint, the endpoint wins.

---

## How it works

```
   seismic · wells · basins · outcrops · images     (raw earth data)
                        │
                        ▼
   ┌────────────────────────────────────────────┐
   │  GEOX compute · 555_COMPUTE_ONLY            │
   │  OBS → DER → INT → SPEC → UNKNOWN           │  physics gates · ≥3 rival
   │  uncertainty labelled at every step         │  hypotheses · falsifiers
   └───────────────────────┬────────────────────┘
                           │ evidence envelope (MCP)
                           ▼
        arifOS judges (SEAL/HOLD/VOID) → A-FORGE executes → VAULT999 receipt
```

### Epistemic labels

Every artifact carries one — confusing speculation with observation is how dry holes and fake seals are born:

| `OBS` | `DER` | `INT` | `SPEC` | `UNKNOWN` |
|---|---|---|---|---|
| observed from data | derived via known physics | interpreted | hypothesis awaiting falsification | no data — GEOX says so instead of guessing |

Cross-system mapping to the federation's `primary_artifact` keys: [pre-doctrine archive](./docs/archive/README-2026-10-16-pre-doctrine.md#epistemic-labels).

### Physics limits GEOX will not pretend away

Non-uniqueness (returns the candidate set with falsifiers, never "the" answer) · resolution/tuning (thin beds below tuning are invisible, not absent) · time ≠ depth (unconverted depth claims refused) · fluid ambiguity (amplitude ≠ hydrocarbon — enforced in code) · equifinality (different processes, identical geology — GEOX names which could produce the observation) · sparse wells (between wells is DER/SPEC, never OBS) · erased time at unconformities (absence of record is not evidence of absence). Full table: [pre-doctrine archive](./docs/archive/README-2026-10-16-pre-doctrine.md#what-geox-refuses-and-what-it-cannot-know). A reply claiming to overcome any of these has failed the constitution.

### Boundaries

No publish to federation databases · no field control (no actuator surfaces) · no authority above `555_COMPUTE_ONLY` · no silent escalation — every call carries provenance. **Writes, precisely:** two tools mutate *local* state only — `geox_well_ingest(overwrite=true)` writes the local ingest workspace, and `geox_claim(mode='seal')` records an organ-local claim-ledger transition (bookkeeping, not judgment — constitutional SEAL belongs to `arif_judge` alone). Full write policy: [pre-doctrine archive](./docs/archive/README-2026-10-16-pre-doctrine.md#authority-floor).

### Images & multimodal

**Image ≠ Specimen ≠ Measurement ≠ Earth.** A photo records surface reflectance and display transforms — never the subsurface entity. `geox_observe` returns evidence only; hypotheses need field tests or petrophysics to survive; the local verdict ceiling is `QUALIFIED_CANDIDATE`. Design canon: `contracts/IMAGE_METABOLIZER_DESIGN.md` §10.

---

## Evidence & gaps

Known, held, not papered over.

| Gap | State | Why it is held |
|---|---|---|
| Internal well-evaluation data once committed (Kinabalu pack, 2026-10-01) | **PURGED 2026-10-08 (F13 sovereign decision)** — values removed from tree and git history; wells de-identified (DW-A, INB-1..n); synthesis retained | Residual: GitHub may serve dangling pre-rewrite commit SHAs until a support-side cache purge — **follow-up open**; originals + identity ledger in a private VPS store outside all repos |
| 5 public tools in no capability pack | Callable but undiscoverable under all discovery profiles | Packing them is a discovery-policy decision, held for the sovereign |
| `/health.deployment_drift` measures the arifOS tree, not GEOX | HELD (observed 2026-10-08) | It cannot corroborate a GEOX source↔runtime claim — use the runtime-commit line in [Current verified state](#current-verified-state) instead |
| Runtime vs source currency | See the generated runtime-commit line above | Operational, not a code defect — redeploy from `main` closes it |
| `geox_temporal` (decline/RRR) vs WEALTH ownership | HELD decision | Which organ owns production-analytics is a federation-policy call, not a code fix |
| `capability_registry.yaml` prose drift (stale profile counts in comments) | Observed 2026-10-08 | Read by no Python; trivial fix living next to canonical logic |
| Pre-existing full-suite test failures | Baseline 12 (2026-10-01); targeted battery **55/55 green** (surface gates, RT1, Earth Witness, fastmcp, live parity, EarthBench, chat) | Full-suite count is CI's job, not this README's |

*(Resolved 2026-10-03: the 31-target phantom count retired, `surface_attestation()` returns `ok=True`; the `09-boundary-ratchet.yml` conflict-marker breakage fixed. Full defect history: [pre-doctrine archive](./docs/archive/README-2026-10-16-pre-doctrine.md#open-defects-known-held-not-papered-over).)*

### Data provenance & confidentiality

| Pack | Provenance | Status |
|---|---|---|
| Macrostrat · PBDB · ICS charts | Public APIs | CC / public domain |
| Malay Basin · NW Borneo · Sabah · Dangerous Grounds families | Public literature + enterprise synthesis relay; internal references de-referenced 2026-10-08 | ⚠ scan-flagged relay signatures — review before external use |
| Kinabalu Basin | Internal well-evaluation values **purged 2026-10-08 (F13)**; synthesis and reasoning retained | Originals + identity ledger: private store outside all repos |
| Earth Witness fixtures / EarthBench | Synthetic (deterministic mock) | Clean — zero confidential data |

Full file-by-file scan: [`reports/readme_harden/2026-10-03_confidentiality_scan.md`](./reports/readme_harden/2026-10-03_confidentiality_scan.md). **Read it before relying on any basin pack for external work.**

---

## Development

```bash
git clone https://github.com/ariffazil/GEOX.git
cd GEOX && uv sync
uv run python -m geox_mcp.server --host 127.0.0.1 --port 18081   # dev port; 8081 is the production organ
curl -s http://127.0.0.1:18081/health
uv run python scripts/generate_all_surfaces.py --check          # CI-equivalent; exit 0 = in sync
PYTHONPATH=src pytest tests/ -q --tb=short
```

**Add a tool →** `src/geox_mcp/registry.py` first; `scripts/generate_all_surfaces.py` regenerates every published surface (`tools.json`, `tools_sot.yaml`, `llms.txt`, `contracts/tools.yaml`, plus this README's generated tool-count badge). Hand-editing a generated surface is how a repository comes to disagree with itself while every file still looks authoritative. `registry.py::CANONICAL_PUBLIC_TOOLS` is the only truth about the tool surface.

**Status block →** `PYTHONPATH=src python3 scripts/generate_readme_status.py` (needs the organ reachable). **Redeploy** (procedure, verification, rollback): [DEPLOYMENT.md](./DEPLOYMENT.md) — verification is two checks, `/drift` *and* runtime commit vs intended source commit. **RT1 recovery** suggestions are derived from the registry at call time, never hardcoded (`tests/test_rt1_recovery_derivation.py`). Changelog: [CHANGELOG.md](./CHANGELOG.md).

### Operational gates

| Gate | Workflow |
|---|---|
| Published surfaces match `registry.py` | [surface-drift-gate.yml](./.github/workflows/surface-drift-gate.yml) |
| Test CI | [geox-ci.yml](./.github/workflows/geox-ci.yml) |
| Federation governance gate | [governance-gate.yml](./.github/workflows/governance-gate.yml) |
| Boundary ratchet | [09-boundary-ratchet.yml](./.github/workflows/09-boundary-ratchet.yml) |
| OpenSSF Scorecards | [scorecards.yml](./.github/workflows/scorecards.yml) |
| Repo hygiene (weekly) | [repo-hygiene-weekly.yml](./.github/workflows/repo-hygiene-weekly.yml) |

### Machine-readable surfaces

`llms.txt` · [`tools.json`](./tools.json) · `tools_sot.yaml` · [`AGENTS.md`](./AGENTS.md) · `.well-known/agent-card.json` (A2A card) — generated from `registry.py`, CI-gated on the round-trip.

---

## License & security

- **License — Business Source License 1.1.** Change Date **2029-06-29**, Change License **Apache-2.0**. Additional Use Grant: non-production / evaluation / academic use. Production use in commercial undertakings (including petroleum exploration, CCS, geothermal, SaaS) requires a separate paid commercial license (arifbfazil@gmail.com). [LICENSE](./LICENSE)
- **Security reporting:** [SECURITY.md](./SECURITY.md). No external security evaluation has been published — we say so rather than imply one.
- **Confidentiality:** Earth data packs are screened by provenance scan (above); uploads to the local-only Earth Witness chat are stripped of EXIF/GPS and never persisted.

---

## Federation identity

<!-- FEDERATION-STANDARD v2026-10-15 START :: 333-AGI audit :: source: organs.yaml + git + live probes :: regenerate: re-run audit -->
| Field | Value |
|---|---|
| Organ | `geox` · CORE · domain_evidence |
| Ports | 8081 |
| Unit | geox-mcp.service |
| Authority ceiling | COMPUTE_ONLY |
| Live (SOT probe @audit) | UP |
| Repo HEAD @audit | `d69a6374 2026-10-14` |
| Public MCP | https://geox.arif-fazil.com/mcp |
| Rollback | — |
| Flow graph | [FEDERATION_MAP.md](https://github.com/ariffazil/AAA/blob/main/docs/FEDERATION_MAP.md) — peta semua organ + repo |
<!-- FEDERATION-STANDARD v2026-10-15 END -->

Siblings: [arifOS](https://github.com/ariffazil/arifOS) (judge) · [A-FORGE](https://github.com/ariffazil/A-FORGE) (execution) · [WEALTH](https://github.com/ariffazil/WEALTH) (capital) · [WELL](https://github.com/ariffazil/WELL) (vitality) · [AAA](https://github.com/ariffazil/AAA) (attention) · [arifFlow](https://github.com/ariffazil/arifFlow) (receipts) · [HERMES](https://github.com/ariffazil/HERMES) (gateway) · [FRAME](https://github.com/ariffazil/FRAME) (observer). Contract: [FEDERATION_CONTRACT.md](./FEDERATION_CONTRACT.md).

DITEMPA BUKAN DIBERI — Forged, Not Given.
