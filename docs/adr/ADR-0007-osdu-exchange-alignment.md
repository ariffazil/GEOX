# ADR-0007: GEOX ↔ OSDU Exchange Alignment

**Status:** DRAFT (awaiting 888_HOLD)
**Date:** 2026-06-24
**Sovereign:** arif (F13)
**Forge session:** FORGE-000Ω (database & memory substrate deep-research, 2026-06-24)
**Supersedes:** none
**Related:** ADR-0008 (RLS-as-Floor hardening), GEOX `GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md`, `arifOS/GENESIS/`

---

## Context

GEOX is the **Earth Intelligence** organ of the arifOS federation. It produces governed evidence for hydrocarbon, mineral, CCS, and geothermal subsurface interpretation. As of 2026-06-24, GEOX owns **56 canonical tools** (per `src/geox_mcp/registry.py`) covering seismic, petrophysics, basin, prospect, vision, multi-physics joint inversion, and federation integration with WEALTH and WELL.

**The problem:** Operator partners (PETRONAS, Shell, Aramco, ExxonMobil, etc.) increasingly require data exchange in **OSDU** (Open Subsurface Data Universe) format — an Open Group standard with 206 active member organizations, four hyperscaler deployments (AWS/Azure/GCP/IBM), and the **OSDU Data Platform Standard v1.0** released 2026-04-07.

OSDU is **excellent at what it does**:
- Standardized JSON-Schema catalog (Cortex) — wellbores, logs, seismic, interpretations, prospects
- Entitlements (group-based ACL), Legal tags (export control, JV restrictions), Policy (OPA/Rego)
- Schema versioning (semver), reference-data vocabulary (Basin, Country, Lithology)
- Cloud portability, vendor-neutral code, broad ecosystem

OSDU is **NOT agentic-ready**:
- No epistemic metadata (no OBS/DER/INT/SPEC ladder)
- No claim grammar (no `evidence_for` / `evidence_against` / `missing_tests` / `ac_risk`)
- No contradiction model
- No MCP / agent-native interface
- No bi-temporal validity (no `validity_window tstzrange`)
- No constitutional floor enforcement
- Schema evolution is multi-month via The Open Group process

**The risk to GEOX:** If we store our claims in OSDU's WPC schemas, we lose the epistemic ladder, the claim grammar, AC Risk, and Physics9State. That is the core of GEOX's value-add. Trading it for interop would be a sovereignty tax for marginal gain.

**The opportunity:** If GEOX speaks OSDU **at the exchange layer only** (read incoming WPC records → write outgoing sealed artifacts as WPC records), we gain interop with the 206-member OSDU ecosystem while preserving every drop of GEOX's epistemic sovereignty.

**The principle (per GEOX `GENESIS/003_CONSTITUTIONAL_ALIGNMENT.md`):** GEOX is **evidence-only**. We never judge policy; we produce evidence for `arifos.judge` to SEAL/SABAR/VOID. OSDU is a data-plane standard — using it as a substrate for GEOX cognition would invert the layering. OSDU must remain below GEOX, not beside or above.

---

## Decision

**Adopt OSDU at the exchange layer only.** Do not adopt OSDU as storage backbone, governance service, or schema source-of-truth for GEOX's internal types.

### Layering (binding)

```
┌─────────────────────────────────────────────────────────────────┐
│ GEOX Cognition Layer (arifOS-governed, never leaves arifOS)     │
│ ──────────────────────────────────────────────────────────────  │
│ • Physics9State cells                                          │
│ • AC Risk (attention residual δ_i)                             │
│ • Claim grammar: evidence_for / evidence_against /             │
│   missing_tests / ac_risk                                      │
│ • Epistemic ladder: OBS → DER → INT → SPEC →                   │
│   EARTHMODEL → DECISION → HUMAN_JUDGMENT                       │
│ • World-state snapshots (per VAULT999 seal chain)              │
│ • Scars / receipts / cooling ledger                            │
└────────────────────┬────────────────────────────────────────────┘
                     │ WRITE: only sealed, sovereign-approved
                     │        artifacts become OSDU entities
                     │ READ:  pull OSDU WPC records on demand
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ OSDU Data Plane (Open Group standard, 206 members)             │
│ ──────────────────────────────────────────────────────────────  │
│ • master-data--Well, Wellbore, Field, Basin, Block             │
│ • work-product-component--WellLog, SeismicTraceData,            │
│   SeismicHorizon, FaultInterpretation, GeobodyInterpretation    │
│ • work-product-component--HorizonInterpretation                 │
│ • reference-data: Country, Basin, Lithology, FluidType         │
│ • Entitlements + Legal tags (read-only passthrough)            │
└─────────────────────────────────────────────────────────────────┘
```

### New Canonical Tools (GEOX MCP server, port 8081)

**3 new tools added to canonical registry** — pushing from 56 → 59. Per `geox/AGENTS.md` this is **888_HOLD territory** (changes to tool registry).

| Tool | Mode | Authority class | Floor envelope |
|---|---|---|---|
| `geox_osdu_ingest` | OBSERVER | read-only — no vault write | F1, F2, F8 (provenance, truth, evidence chain) |
| `geox_osdu_export` | GOVERNED | write — requires sealed artifact | F1, F2, F3, F11, F13 (amanah, truth, tri-witness, audit, sovereign) |
| `geox_osdu_reference_query` | OBSERVER | read-only — vocab lookup | F1, F2 |

**Authority requirements:**
- `geox_osdu_ingest` — any authenticated caller with F1+ clearance
- `geox_osdu_export` — caller MUST supply a `seal_verdict_id` from a prior `arifos.judge` SEAL. No seal → 888_HOLD structurally.
- `geox_osdu_reference_query` — any caller

### Reference Data Mapping

OSDU reference-data values (Basin, Country, Lithology, FluidType, etc.) are mapped to GEOX's internal taxonomy via a YAML configuration file at `geox/data/osdu_reference_mapping.yaml`. Mapping is **passthrough where possible**, **explicit translation where needed**, **`null` (prompt for clarification) where OSDU vocabulary is ambiguous**.

Example:
```yaml
# geox/data/osdu_reference_mapping.yaml
basin_mapping:
  passthrough: true  # use OSDU Basin IDs directly when format matches
country_mapping:
  MY: "reference-data--Country:Malaysia:"
  NO: "reference-data--Country:Norway:"
  GB: "reference-data--Country:United_Kingdom:"
lithology_mapping:
  sandstone: "reference-data--Lithology:Sandstone:"
  shale: "reference-data--Lithology:Shale:"
  carbonate: "reference-data--Lithology:Carbonate:"
  unknown: null  # → GEOX prompts human reviewer
```

### Hard Rules (binding, non-negotiable)

1. **GEOX NEVER writes a partially-sealed claim to OSDU.** Only artifacts with `verdict=SEALED` from `arifos.judge` become OSDU entities. The MCP tool `geox_osdu_export` structurally refuses any unsealed input.

2. **OSDU NEVER writes back into GEOX cognition.** OSDU records enter GEOX only via `geox_osdu_ingest_*` tools. No direct database writes from OSDU ingestion pipelines.

3. **OSDU entitlements/legal tags are passthrough-only.** GEOX uses arifOS F13 SOVEREIGN, not OSDU's `users.data.root`. If an OSDU record has conflicting ACL/legal metadata, GEOX defers to arifOS governance.

4. **OSDU schema evolution is one-way (OSDU → GEOX mapping table).** GEOX never blocks on The Open Group process. New OSDU schema versions → update mapping table → bump `GEOX_CONTRACT_EPOCH`.

5. **No OSDU platform deployment on `af-forge`.** We are a client, not a host. Use managed OSDU instances (AWS OSDU Data Platform, Azure Data Manager for Energy) or partner-deployed instances only.

6. **No replacement of GEOX's internal storage with OSDU.** OSDU schemas describe data; GEOX schemas describe *meaning* (epistemic, governed, traced). They live at different layers and must remain separate.

### Cost & Timeline (DER, 0.70 confidence)

| Phase | Effort | Deliverable | 888_HOLD? |
|---|---|---|---|
| **P0 — ADR ratification** | — | This ADR signed by Arif | YES |
| **P1 — Reference spike** | 30 hours | `geox_osdu_ingest_well_log` against a real OSDU WellLog v1.5.0 fixture. Validates schema mapping, ACL passthrough, epistemic tagging | NO (spike in fixture dir, not deployed) |
| **P2 — Full read surface** | 120 hours | All ingest tools + reference mapping + 4 golden fixtures | YES (when adding to canonical tool registry) |
| **P3 — Full write surface** | 100 hours | Export tools + manifest emitter + sealed-only enforcement | YES (when adding to canonical tool registry) |
| **P4 — CI + docs + skills** | 60 hours | Golden tests, geox-osdu-* skill files, AGENTS.md update | YES (when publishing to skills/) |
| **P5 — Federation rollout** | 20 hours | GEOX smoke test against AWS OSDU managed instance, AAA dashboard tile | NO (smoke only) |
| **TOTAL** | **~330 hours** | **≈1 engineer-quarter** (3 months at ~110 productive hours/month) | 4× 888_HOLD gates |

### What GEOX Gains (DER)

1. **Operator interop** — PETRONAS, Shell, Aramco, ExxonMobil, etc. can feed GEOX directly. Zero custom integration per partner.
2. **3rd-party dataset licensing** — TGS, PGS, CGG, Westwood multi-client libraries increasingly delivered in OSDU format.
3. **Schema-standard naming** — partners recognize `master-data--Well`, `work-product-component--WellLog`, etc.
4. **Trust anchor** — "conforms to OSDU exchange layer" is positive procurement signal.
5. **Cross-vendor interop** — future-proofing against tool-vendor churn.
6. **Curated reference data** — OSDU's Basin/Country/Lithology workbooks are free validated vocabulary.

### What GEOX Loses (if we adopt — INT)

**Nothing, if we follow the layering above.** All GEOX epistemic state, AC Risk, claim grammar, Physics9State remain inside arifOS governance. OSDU is exchange, not storage.

### What GEOX Would Lose (if we DON'T follow layering — INT)

If we stored claims in OSDU WPC schemas directly:
1. Epistemic ladder collapse — claims become flat "observations"
2. Claim grammar loss — no `evidence_for`/`evidence_against`/`missing_tests`/`ac_risk`
3. AC Risk / Physics9State loss — primary analytic outputs vanish
4. Schema agility loss — OSDU evolution is multi-month; GEOX needs weeks
5. Causal graph loss — OSDU links are parent links, not causal
6. Contradiction model loss — no "Claim A contradicts Claim B"
7. Constitutional alignment friction — `users.data.root` vs F13 SOVEREIGN
8. Operational burden — OSDU is multi-service microsystem (storage + search + entitlements + legal + policy + workflow + schema + notification + file + dataset + unit + CRS)
9. Single-cloud lock-in — most OSDU production deployments bind to one CSP
10. Cost — estimated $500K-$5M/year OpEx at enterprise scale

This ADR explicitly avoids all 10 by NOT adopting OSDU as substrate.

---

## Alternatives Considered

### A1. Full OSDU substrate replacement (REJECTED, 0.92 confidence)

Replace GEOX internal storage with OSDU WPC + master-data schemas. Cost: 2,000-5,000+ hours. Loss: epistemic ladder, claim grammar, AC Risk, schema agility, constitutional alignment. **Rejected.**

### A2. Stand up OSDU platform on `af-forge` (REJECTED, 0.92 confidence)

Self-host OSDU Forum reference implementation. Cost: 2,000+ hours + ongoing ops burden. arifOS federation is bare-metal systemd by doctrine (`arifOS/AGENTS.md` §6 — "Organs = systemd, Data = Docker. No federation organ runs in Docker. Supporting services run as Docker containers"). OSDU is multi-service microsystem — wrong scale. **Rejected.**

### A3. Adopt OSDU Policy (OPA/Rego) on top of GEOX (REJECTED, 0.92 confidence)

Bolting OPA on GEOX creates two governance systems. arifOS constitutional kernel is sovereign; OPA would compete. Pick one. We have arifOS. **Rejected.**

### A4. No OSDU integration — accept partner-specific adapters (REJECTED, 0.75 confidence)

Stay closed. Each partner integration is bespoke. Cost: cumulative N×200 hours per partner, forever. No interop standard. **Rejected for strategic reasons.**

### A5. (CHOSEN) Exchange layer only, see Decision above.

---

## Consequences

### Positive

- arifOS governance unchanged (F13 SOVEREIGN, VAULT999, constitutional floors)
- GEOX epistemic ladder, claim grammar, AC Risk intact
- ~330 hours to interop with 206-member OSDU ecosystem
- Schema agility preserved (OSDU changes do not block GEOX)
- No cloud lock-in
- Minimal operational burden
- Schema updates tracked via `GEOX_CONTRACT_EPOCH` (existing convention)

### Negative

- ~330 hours of work over 3 months
- Mapping table maintenance (low — only on OSDU schema major versions)
- Requires partner cooperation for golden fixtures (mitigation: AWS/Azure OSDU public test instances)
- Adds 3 tools to canonical registry (pushes 56 → 59; touch `src/geox_mcp/registry.py:CANONICAL_PUBLIC_TOOLS` — 888_HOLD gate per `geox/AGENTS.md`)

### Neutral

- OSDU Standard v1.0 (April 2026) is the certification basis — adopting pre-v1.0 specs is acceptable for exchange layer, not for storage layer
- arifOS-side knowledge of OSDU required for one engineer (mitigation: skill files at `~/.agents/skills/geox-osdu-exchange/`)

---

## Verification (how we know this works)

| Test | Acceptance |
|---|---|
| **Round-trip 1: WellLog** | Take a real OSDU WellLog v1.5.0 JSON → `geox_osdu_ingest_well_log` → GEOX `well_log` model with `epistemic=OBS` → re-emit as OSDU WellLog → bytewise compare with input (modulo id, version, hash) |
| **Round-trip 2: SeismicTraceData** | Same as above for SeismicTraceData v1.5.1 |
| **Round-trip 3: HorizonInterpretation** | Same as above for v1.x.x |
| **Reference mapping coverage** | ≥95% of OSDU reference-data values for Country, Basin, Lithology have explicit mapping entries |
| **Sealed-only enforcement** | `geox_osdu_export` with non-SEALED input returns `F13_SOVEREIGN_HOLD` deterministically, with no partial output |
| **Constitutional test** | All F1-F13 floors still pass; no test regression in `pytest tests/` |
| **No new tool classes** | Per `arifOS/AGENTS.md` §8 "No new tools, harden existing ones" — we add `geox_osdu_*` modes to existing `geox_ingest` / `geox_export` tool classes, not new `@mcp.tool` entries where avoidable |

---

## Open Questions

1. **OSDU Service Company alignment** — should we coordinate with SLB Petrel / Halliburton Landmark teams on schema mappings? Cost: low; benefit: reduce integration friction. **DECISION: defer until P2.**
2. **OSDU legal tag handling** — does GEOX reject records with `exportStatus=EXPORT_CONTROLLED`? Or passthrough with F13 SOVEREIGN flag? **DECISION: passthrough with explicit sovereign flag for now; revisit at P5.**
3. **OSDU Schema Service subscription** — should GEOX track OSDU schema changes via Schema Service feed? **DECISION: not in P1-P4; revisit at P5.**

---

## References (evidence ledger)

**Primary (Tier 1, OBS):**
- `osduforum.org/osdu-data-platform-primer-1/` — primer, March 2023
- `opengroup.org/osdu/current-members` — 206 active orgs
- `learn.microsoft.com/en-us/azure/energy-data-services/concepts-entitlements` — entitlements v1/v2
- `aws.amazon.com/blogs/industries/osdu-data-platform-on-aws-ingestion-series-1` — data types
- `blog.opengroup.org/2026/04/07/exploring-the-upcoming-osdu-data-platform-standard-version-1-0/` — v1.0 Standard
- `community.opengroup.org/osdu/data/data-definitions` — canonical schemas
- `github.com/jonslo/osdu-data-data-definitions` — public schema mirror

**Practitioner first-hand (Tier 2, OBS):**
- Jeff Roy LinkedIn 2026-05-11, "What Nobody Tells You About Migrating to OSDU"
- Fabrice Buron, INT blog 2024-02-22, "Navigating Deployment Challenges"
- Scott Kimbleton, IBM LinkedIn 2023-10-18, "Destination OSDU"

**Internal (OBS — verified via Supabase introspection 2026-06-24):**
- VAULT999 schema: `vault_seals` (hash-chained, 270 rows), `arifosmcp_memory_records` (5-type taxonomy, vector(1024) HNSW, supersession FK), `arifosmcp_kernel_state` (organ_status jsonb), `arifosmcp_memory_audit_log` (floor_violations jsonb)
- 7 Postgres extensions: pgvector 0.8.0, pgcrypto 1.3, pg_graphql 1.5.11, uuid-ossp 1.1, pg_stat_statements, supabase_vault, plpgsql
- §7.9 Memory Architecture (per `arifOS/AGENTS.md`): KSR / Vault / Ledger / Federation / Telemetry

**Forge session evidence:**
- `/root/forge_work/2026-06-24-osdu-research/RECEIPT.md` — 3 parallel research agents
- `/root/forge_work/2026-06-24-osdu-spike/` — WellLog spike code + tests + fixture

---

## Ratification

**Awaiting 888_HOLD from Arif.**

If ratified, this ADR becomes the canonical GEOX↔OSDU contract. Implementation proceeds in 5 phases (P1-P5) per Cost & Timeline above. Each phase has its own 888_HOLD gate where it touches production.

**DITEMPA BUKAN DIBERI. Earth evidence is forged, not given.**

— FORGE-000Ω, 2026-06-24
