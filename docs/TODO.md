# TODO — GEOX Earth Intelligence

> **Roadmap:** ARIFOS_NEXT_HORIZON_2026
> **Execution Status:** HOLD until contracts frozen
> **Last Updated:** 2026-06-03 18:30 MYT
> **Seal:** DITEMPA BUKAN DIBERI

---

## ✅ Eureka Forge (Completed 2026-06-03)

- [x] E1 — T-D fitters (linear, polynomial, Vo-K, layer-cake) — 28 tests
- [x] E2 — Legacy ingest (3 Excel formats + OCR hook) — 1 test (`geox_core.ingest.legacy_ingest`)
- [x] E7 — Cascade demotion (Gödel closure) — 28 tests
- [x] **E8 — Velocity IS Structure** (Vp slice + 5-channel attribution) — 37 tests
- [x] **E9 — Impedance IS Fluid** (Zoeppritz Bortfeld + Shuey + LMR) — 29 kernel + 4 MCP wiring tests
- [x] E9 Castagna mudrock fallback (DTS absent path) — integrated into `geox_core.avo.castagna`
- [x] `target_class="lmr_map"` added to `geox_subsurface_generate_candidates` (no new MCP tool, F13 honored)
- [x] F13 honored: 0 new MCP tools, all 20 canonical tools unchanged

---

## ✅ Embodiment Attestation (Completed Earlier Today)

- [x] arifOS embodiment contracts deployed
- [x] Model registry fix
- [x] EUREKA validation (Layang-Layang stress test)
- [x] Physics engine (Archie, Simandoux, Indonesia models)

---

## 🔴 P0 — Horizon 0: Canon Lock (Days 0–14)

**Gate: No new features until contracts are frozen.**

### Authority Freeze
- [ ] **Create `REPO_AUTHORITY_MATRIX.md`** — what GEOX may own / must not own
- [ ] **Tool inventory** — 15 canonical tools + alias sunset plan
- [ ] **Schema inventory** — map all evidence schemas
- [ ] **Legacy alias audit** — plan sunset for 37 legacy aliases

---

## 🟠 P1 — Horizon 1: Security + Session Spine (Days 15–45)

**Gate: Every output has source, timestamp, uncertainty, method, confidence.**

### Evidence Schemas
- [ ] **Create `/schemas/earth_evidence.schema.json`** — structured earth evidence object
- [ ] **Create `/schemas/prospect_uncertainty.schema.json`** — uncertainty quantification
- [ ] **Evidence provenance enforcement** — every output carries:
  - `source` — where the data came from
  - `timestamp` — when evidence was gathered
  - `method` — which model/algorithm was used
  - `confidence` — epistemic/aleatory uncertainty decomposition
  - `coverage_ratio` — spatial/data coverage

### Sensor Bridge
- [ ] **MQTT adapter** — IoT seismometers, GPS, pressure gauges
- [ ] **OSC adapter** — seismic instruments
- [ ] **HTTP/REST polling** — weather stations, satellite feeds
- [ ] **WebSocket** — near-real-time satellite data

---

## 🟡 P2 — Horizon 2: Deterministic Judge (Days 46–90)

**Gate: Every GEOX output consumable by arifOS without prompt translation.**

### Ontology + Sunset
- [ ] **Create `/ontology/sweet_map.yaml`** — SWEET-compatible concept map
- [ ] **Legacy alias sunset** — fully migrate 37 → 15 canonical tools
- [ ] **Evidence contract tests** — `/tests/evidence_contract_tests.py`

### Physics Solver Integration
- [ ] **OpenFOAM** — reservoir simulation CFD (Level 1 validation)
- [ ] **SeisSol** — dynamic earthquake rupture
- [ ] **Specfem** — seismic wave propagation
- [ ] **Validation loop:** GEOX output → physics solver → compare → flag Δ > 2σ

---

## 🟢 P3 — Horizon 3: Semantic Federation (Days 91–135)

**Gate: One GEOX uncertainty produces one WEALTH risk witness without manual prompt glue.**

### GEOX → WEALTH Bridge
- [ ] **Define bridge contract** — GEOX evidence maps to WEALTH evidence
- [ ] **`earth_evidence.schema.json`** — export format for cross-domain use
- [ ] **SWEET mapping v1** — semantic concept alignment
- [ ] **First cross-domain demo** — real subsurface uncertainty → capital risk witness

### Pipeline
- [ ] GEOX detects subsurface uncertainty
- [ ] arifOS requests evidence
- [ ] WEALTH calculates EMV / downside / option value
- [ ] arifOS judges
- [ ] A-FORGE executes report generation only
- [ ] VAULT999 seals trace

---

## 🔵 P4 — Horizon 4: Self-Healing + Release (Days 136–180)

**Gate: GEOX evidence feeds causal decision intelligence.**

- [ ] **Causal template integration** — GEOX → WEALTH reservoir uncertainty affects EMV
- [ ] **Proof-carrying evidence** — full justification trace for arifOS 888_JUDGE
- [ ] **Public docs cleanup**
- [ ] **Release tag `vNext-Horizon-0`**

---

**DITEMPA BUKAN DIBERI — Earth intelligence is forged, not given.**

---

## ✅ Session 2026-06-03 — E8 + E9 Forge (Sealed)

**Commit:** `d71edae5` on `origin/main` (pushed with ARIFOS_HOLD_ACK=1)
**VAULT999 seal:** `GEOX-E8E9-FORGE-SEAL-2026-06-03` @ line 2597

### Shipped
- [x] **E8 formalisation doc** — `docs/theory/E8_VELOCITY_AS_STRUCTURE_THEORY.md` (9.9KB / 210 lines). 6-pillar physics chain, 6 failure modes, F2 Truth bands.
- [x] **E9 avo_forward.py** — `src/geox_core/avo/avo_forward.py` (13.3KB / 397 lines). 3 primitives: `zoeppritz_rpp` (exact, ACRisk 0.05), `shuey_avo` (R0/G/AVO class, ACRisk 0.12), `lmr_decompose` (Goodway 1997, ACRisk 0.08). 2 dataclasses + 1 helper.
- [x] **F13 honored** — zero new MCP tool registrations. E8 capability stays in `geox_subsurface_generate_candidates` (opt-in `target_class="velocity_slice"`); E9 in `geox_seismic_compute` (opt-in `mode="avo_forward"`).
- [x] **Federated E8 acknowledged** — `src/geox_core/spatial/velocity_slice.py` was ALREADY FINAL (2026-06-03 17:55 MYT). I was about to overwrite it with a redundant copy — Arif caught the F2 delta. `git checkout --` restored the working tree, `git rm --cached` dropped the redundant copy from the commit.

### Open for next forge
- [ ] **MCP tool integration** — wire `velocity_slice` into `geox_subsurface_generate_candidates` (target_class=velocity_slice) and `avo_forward` into `geox_seismic_compute` (mode=avo_forward) in a follow-up commit.
- [ ] **E9 full forge** — pending DTS + pre-stack data confirmation (Arif to confirm Kinabalu well inventory).
- [ ] **5 queued eurekas** — E2 legacy_ingest, E3 uncertainty, E4 multi_well, E5 anisotropy, E6 deviated_correction.
- [ ] **E8 + E9 test suites** — partially built (`tests/test_e8_velocity_slice.py`); field-name mismatch from sed passes queued for follow-up.

### Cross-federation open (unchanged)
- [ ] Caddyfile port misrouting — `/api/organs/geox/health` → `:18081` (arifosd) instead of `:8081` (geox). 888_HOLD.
- [ ] GEOX CI workflow 0-jobs rot — `ci.yml` last touched 228e2906, pre-existing.
- [ ] WELL biometric injection — sovereign territory, 800h+ stale.
