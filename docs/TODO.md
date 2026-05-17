# TODO — GEOX Earth Intelligence

> **Roadmap:** ARIFOS_NEXT_HORIZON_2026  
> **Execution Status:** HOLD until contracts frozen  
> **Last Updated:** 2026-05-10  
> **Seal:** DITEMPA BUKAN DIBERI

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
