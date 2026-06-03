# TODO — GEOX Earth Intelligence

> **Roadmap:** ARIFOS_NEXT_HORIZON_2026  
> **Execution Status:** ACTIVE  
> **Last Updated:** 2026-06-03  
> **Seal:** DITEMPA BUKAN DIBERI

---

## ✅ SESSION 2026-06-03 — E8/E9 Forge (SEALED @ d71edae5)

> VAULT999 line 2597: `GEOX-E8E9-FORGE-SEAL-2026-06-03`

- [x] **E8 formalisation doc** — 9.9KB / 210 lines — canonical theory of record, 6-pillar physics chain + 6 failure modes
- [x] **E9 `avo_forward.py`** — 13.3KB / 397 lines — `zoeppritz_rpp`, `shuey_avo`, `lmr_decompose` + 2 dataclasses
- [x] **E8 `velocity_slice.py`** — CONFIRMED FINAL (federated team, 2026-06-03 17:55 MYT) — 6 symbols (slice_velocity_cube, structural_attribution, bootstrap_structure + 3 support). Not overwritten.
- [x] **F13 honored** — 0 new MCP tools. Tool count: 20 canonical. E8/E9 wire into existing tools via opt-in `target_class` / `mode` params.
- [x] **Physics9 gap identified** — `lambda_rho`, `mu_rho`, `vp_vs_ratio`, `avo_class` not yet in Physics9 state
- [x] **F2 delta recorded** — ghost-write pattern (Write tool silent failure) — bash heredoc fallback confirmed working

### E9 Physics Chain Sealed
- Vs field: `vs: 1100–3400 m/s` — already in Physics9State ✅
- Zoeppritz exact (4×4 system) → Shuey linearisation (θ < 30°) → Intercept/Gradient crossplot → AVO Class I/II/III/IV
- LMR: `λρ = ρ²(Vp²−2Vs²)` (fluid), `μρ = ρ²Vs²` (rigidity/lithology) — Goodway 1997
- E8 reads **structure**. E9 reads **fluid**. Same Earth, orthogonal slices.

---

## ✅ Embodiment Attestation (Completed Earlier)

- [x] arifOS embodiment contracts deployed
- [x] Model registry fix
- [x] EUREKA validation (Layang-Layang stress test)
- [x] Physics engine (Archie, Simandoux, Indonesia models)

---

## 🔴 NEXT FORGE — Immediate Queue

> Ordered by dependency and data-readiness.

### 888_HOLD (Arif decision required)
- [ ] **Caddyfile port misrouting** — `/api/organs/geox/health → :18081` should be `:8081`. Infrastructure change. **Awaiting Arif go-ahead.**
- [ ] **E9 full MCP wire** — `geox_seismic_compute mode="avo_forward"` — **requires DTS + pre-stack data confirmation from Arif**
- [ ] **DTS/pre-stack data audit** — Kinabalu 8 wells: confirm dipole sonic (DTS) availability + NMO angle gathers. If DTS missing → Gassmann forward-model Vs (ACRisk +0.20)

### P0 — Physics9 Patch (2-line fix, no MCP change)
- [ ] Add `lambda_rho`, `mu_rho`, `vp_vs_ratio`, `avo_class` as derived fields to `physics/parameters.py`
- [ ] Update Physics9State Pydantic schema to carry LMR fields
- [ ] Add Physics9 → AVO class boundary constants to `physics/state.py`

### P0 — MCP Integration (E8/E9 wire into existing 20 tools)
- [ ] `geox_subsurface_generate_candidates` — add `target_class: "velocity_slice"` (mode 11)
- [ ] `geox_map_context_scene` — accept `VpSlice` as scene input type
- [ ] `geox_prospect_evaluate` — accept `structural_map` as derived input
- [ ] `geox_seismic_compute` — add `mode: "avo_forward"` → calls `shuey_avo`
- [ ] `geox_subsurface_generate_candidates` — add `target_class: "lmr_map"`
- [ ] `geox_evidence_reason` — register AVO class as contradiction-scannable evidence type

### P0 — Stale Docs (Tier 1 — reversible, do + report)
- [ ] **README.md** — fix: `28 tools → 20`, `GEOX_PORT 18081 → 8081`, test count, `Last Verified: 2026-06-03`
- [ ] **AGENTS.md** — fix: `21 sovereign tools → 20`
- [ ] **INVARIANTS.md** — fix: port note (`18081` is arifosd.py, NOT geox)
- [ ] **arifOS/FEDERATION_STATUS.md** — fix: `18081, 28 tools → 8081, 20 tools`

### P1 — Queued Eurekas (ordered)
- [ ] **E4 — Multi-well calibration** — V(z) spatial calibration across Kinabalu 8 wells (data ready)
- [ ] **E3 — Uncertainty ensemble** — promote P10/P50/P90 to spatial field (needs E8 velocity slice)
- [ ] **E2 — Legacy ingest** — well log calibration anchor map
- [ ] **E5 — Anisotropy VTI/TTI** — δ, ε as spatial fields (needs multi-well)
- [ ] **E6 — Deviated well correction** — ray-trace spatial ensemble (needs E5)

### P1 — WELL Biometric Injection
- [ ] WELL sovereign module — 800h+ stale. Needs Arif review + reset.

### P2 — CI Rot
- [ ] GEOX CI workflow 0-jobs rot — pre-existing, unchanged this session. Fix `.github/workflows/`.

---

## 🟠 P1 — Horizon 1: Security + Session Spine

**Gate: Every output has source, timestamp, uncertainty, method, confidence.**

### Evidence Schemas
- [ ] **Create `/schemas/earth_evidence.schema.json`**
- [ ] **Create `/schemas/prospect_uncertainty.schema.json`**
- [ ] Evidence provenance enforcement — `source`, `timestamp`, `method`, `confidence`, `coverage_ratio`

### Sensor Bridge
- [ ] MQTT adapter — IoT seismometers, GPS, pressure gauges
- [ ] OSC adapter — seismic instruments
- [ ] HTTP/REST polling — weather stations, satellite feeds
- [ ] WebSocket — near-real-time satellite data

---

## 🟡 P2 — Horizon 2: Deterministic Judge

**Gate: Every GEOX output consumable by arifOS without prompt translation.**

### Ontology + Sunset
- [ ] **Create `/ontology/sweet_map.yaml`**
- [ ] **Legacy alias sunset** — fully migrate 37 → 15 canonical tools
- [ ] **Evidence contract tests** — `/tests/evidence_contract_tests.py`

### Physics Solver Integration
- [ ] OpenFOAM — reservoir simulation CFD (Level 1 validation)
- [ ] SeisSol — dynamic earthquake rupture
- [ ] Specfem — seismic wave propagation
- [ ] Validation loop: GEOX output → physics solver → compare → flag Δ > 2σ

---

## 🟢 P3 — Horizon 3: Semantic Federation

**Gate: One GEOX uncertainty produces one WEALTH risk witness without manual prompt glue.**

### GEOX → WEALTH Bridge
- [ ] Define bridge contract
- [ ] `earth_evidence.schema.json` export format
- [ ] SWEET mapping v1
- [ ] First cross-domain demo: subsurface uncertainty → capital risk witness

### Pipeline
- [ ] GEOX detects subsurface uncertainty
- [ ] arifOS requests evidence
- [ ] WEALTH calculates EMV / downside / option value
- [ ] arifOS judges
- [ ] A-FORGE executes report generation only
- [ ] VAULT999 seals trace

---

## 🔵 P4 — Horizon 4: Self-Healing + Release

**Gate: GEOX evidence feeds causal decision intelligence.**

- [ ] Causal template integration — GEOX → WEALTH reservoir uncertainty affects EMV
- [ ] Proof-carrying evidence — full justification trace for arifOS 888_JUDGE
- [ ] Public docs cleanup
- [ ] Release tag `vNext-Horizon-0`

---

*Last session: 2026-06-03 18:06 MYT | 999 SEAL ALIVE*  
**DITEMPA BUKAN DIBERI — Earth intelligence is forged, not given.**
