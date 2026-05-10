# TODO — GEOX Earth Intelligence

> **Last Updated:** 2026-05-10  
> **Session:** Governance Attestation + Sensor Bridge Planning  
> **Seal:** DITEMPA BUKAN DIBERI

---

## ✅ Completed This Session

- [x] **arifOS embodiment contracts** deployed — GEOX tools respect lane/tier gating at kernel + REST levels
- [x] **Model registry** fixed — governance attestation now resolves `gpt-5.5-thinking`
- [x] **EUREKA validation** — GPT-5 constitutional firewall validated (Layang-Layang stress test)
- [x] **Physics engine** — Archie, Simandoux, Indonesia models + Monte Carlo uncertainty

---

## 🔴 P0 — Critical (Before Next Session)

### Real-Time Sensor Bridge (H1.1)
Move from file-batch to streaming ingestion.

- [ ] **MQTT adapter** — for IoT seismometers, GPS, pressure gauges
- [ ] **OSC adapter** — OpenSound Control for seismic instruments
- [ ] **HTTP/REST polling** — weather stations, satellite feeds
- [ ] **WebSocket** — near-real-time satellite data
- [ ] **Quality flags** — VALID, SUSPECT, GAP, SPIKE, CALIBRATED
- [ ] **Drift correction** — auto-detect and flag calibration drift

### Uncertainty Quantification Standard (H1.2)
Every GEOX output must carry explicit confidence intervals.

- [ ] **UncertaintyQuantifiedOutput schema** — aleatory + epistemic decomposition
- [ ] **Update existing tools:**
  - `geox_porosity_calculate`
  - `geox_saturation_calculate`
  - `geox_lithos_interpret`
  - `geox_fluid_mapping`
  - `geox_pressure_gradient`
- [ ] **arifOS rejection criteria:**
  - `total_ci_95` width > 20% of value magnitude → HOLD
  - `epistemic_std` > `aleatory_std` → flag "more data needed"
  - `coverage_ratio` < 0.6 → HOLD

---

## 🟠 P1 — High (Next 7 Days)

### Physics Solver Integration (H1.3)
Ground AI interpretations against first-principles simulation.

- [ ] **OpenFOAM** — reservoir simulation CFD
- [ ] **SeisSol** — dynamic earthquake rupture
- [ ] **Specfem** — seismic wave propagation
- [ ] **Validation loop (Level 1):**
  - GEOX outputs result → physics solver runs independently → compare → flag Δ > 2σ

### Proof-Carrying Evidence (H2.1)
Every GEOX evidence output must include verifiable justification trace.

- [ ] **Data lineage** — raw sensor/file → processed → interpreted with full trace
- [ ] **Model identification** — which petrophysical model used
- [ ] **Assumption inventory** — every assumption with explicit confidence
- [ ] **Alternative considered** — at least one rejected interpretation + reason
- [ ] **Physical consistency** — cross-check against physics solver results

---

## 🟡 P2 — Medium (Next 30 Days)

### Domain Intelligence Split
- [ ] **1D Well Context Desk** — integrate RATLAS materials
- [ ] **2D Seismic Viewer** — attribute generation, real data (Volve/F3/Malay Basin)
- [ ] **3D Basin Explorer** — connect to Macrostrat/Open Data
- [ ] **Replace synthetic data** with real datasets

### WEALTH ↔ GEOX Coupling (H2.2)
- [ ] **Planetary boundary feed** — hourly MCP loop to WEALTH `wealth_future_steward`
- [ ] **Price ecological damage** — real-time MYR/year valuation
- [ ] **Alert integration** — arifOS triggers alerts when boundaries exceeded

---

## 🟢 P3 — Backlog (H2 2026)

### cigvis 3D Seismic Integration
- [ ] **Phase C** — 3D seismic rendering in browser
- [ ] **Performance budget** — <2s load for 100MB seismic cube

### Cross-Federation Earth Data Standard (H4)
- [ ] **Standardize GEOX schemas** as federation default for earth/subsurface evidence

---

**DITEMPA BUKAN DIBERI — Earth intelligence is forged, not given.**
