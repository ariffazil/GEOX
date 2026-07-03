# GEOX RSI — Deep Research Scaffold

> **Objective:** Map every resource, architecture component, data source, and intelligence flow
> needed for GEOX to independently solve all 9 Malaysia basin dilemmas.
> **Class:** RSI (Refactoring/System Intelligence)
> **Authority:** AUDITOR (DeepSeek V4 Pro) or PLAN (Kimi K2.7 Code)
> **Status:** SCAFFOLD — ready for execution

---

## The 9 Dilemmas (Recap)

| # | Dilemma | Current GEOX Status | Blocker |
|---|---------|---------------------|---------|
| D1 | Malay Basin rift vs wrench | Claim created, challenged | No structural restoration engine |
| D2 | Charge kitchens | Claim created | No basin modelling / maturity engine |
| D3 | High CO₂ origin | Claim created, evidence attached | No isotope geochemistry pipeline |
| D4 | Fault seal vs leak | Claim created | No SGR/SSGR/clay smear calculator |
| D5 | Inversion vs charge | Claim created | No thermal history (AFT/VR) engine |
| D6 | Deep basement play | CHALLENGED | No fracture connectivity model |
| D7 | Sarawak carbonate | CHALLENGED | No diagenesis / Lucia classification |
| D8 | Sabah deepwater | Claim created | No seismic geomorphology engine |
| D9 | CCS containment | Claim created, geomechanics SESSION_REQUIRED | No coupled geo-mechanical-reservoir sim |

---

## Research Axes

### AXIS 1: Data Sources (What GEOX Needs to Ingest)

For each dilemma, identify the **specific data types, formats, and sources** that would enable GEOX to generate evidence, not just claims.

| Dilemma | Data Type | Format | Source | GEOX Ingestion Tool | Status |
|---------|-----------|--------|--------|---------------------|--------|
| D1 | Structural maps, fault polygons | Shapefile/GeoJSON | PETRONAS/NOCS | `geox_well_ingest` (extended) | ❌ No structural data ingestion |
| D1 | Depocentre migration maps | GIS raster | Academic | `geox_basin` (extended) | ❌ No temporal spatial analysis |
| D2 | Source rock geochemistry (TOC, HI, Tmax) | LAS/CSV | Well data | `geox_well_ingest` | ❌ No geochemistry curves |
| D2 | Burial history models | 1D/2D model output | Basin modelling software | `geox_subsurface_model` | ❌ No petroleum system modelling |
| D3 | Gas composition (C1-C5, CO₂, N₂) | CSV/PVT report | Well tests | `geox_well_ingest` (extended) | ❌ No PVT ingestion |
| D3 | Isotope data (δ13C, ³He/⁴He, noble gases) | CSV | Geochem labs | New tool needed | ❌ No isotope tool |
| D4 | Fault juxtaposition diagrams | Seismic + well data | Interpretation | `geox_seismic_interpret` | ⚠️ Partial |
| D4 | Shale gouge ratio / SGR | Computed from Vcl | Well + fault | New tool needed | ❌ No fault seal calculator |
| D5 | Apatite fission track data | CSV | AFT lab | New tool needed | ❌ No thermal history tool |
| D5 | Vitrinite reflectance | CSV/LAS | Well data | `geox_well_ingest` (extended) | ❌ No VR curve support |
| D6 | Image log data (FMI/UBI) | DLIS/LAS | Wireline | `geox_well_ingest` (extended) | ❌ No image log processing |
| D6 | Core fracture description | CSV/photo | Core data | New tool needed | ❌ No core description ingestion |
| D7 | Thin section descriptions | Photo/microscope | Lab | `geox_vision` (extended) | ⚠️ VLM can describe, no Lucia |
| D7 | Core plug porosity-permeability | CSV | Core lab | `geox_well_ingest` (extended) | ❌ No core plug ingestion |
| D8 | Seismic amplitude maps | SEG-Y/GIS | Seismic processing | `geox_seismic_compute` | ⚠️ Partial |
| D8 | Well test interference data | CSV/PDM | Production | New tool needed | ❌ No well test analysis |
| D9 | Caprock characterization | Well + seismic | Multi-source | `geox_geomechanics` | ⚠️ SESSION_REQUIRED |
| D9 | Pressure data (RFT/MDT) | CSV/LAS | Wireline | `geox_well_ingest` (extended) | ❌ No pressure data ingestion |

### AXIS 2: Computational Engines (What GEOX Needs to Compute)

| Engine | Purpose | Dilemmas Served | Current Status | Architecture |
|--------|---------|-----------------|----------------|-------------|
| **Fault Seal Calculator** | SGR, SSGR, clay smear, juxtaposition analysis | D4 | ❌ Not built | Python module in `geox_core/engines/`. Input: Vcl log + fault geometry. Output: seal capacity profile. |
| **Basin Modelling Bridge** | 1D burial history, maturity, charge timing | D2, D5 | ❌ Not built | Bridge to PetroMod/TemisFlow OR simplified 1D thermal model. Input: strat column + heat flow. Output: maturity + timing. |
| **Thermal History Engine** | AFT/VR inversion, time-temperature paths | D5 | ❌ Not built | Python module. Input: AFT ages + VR data. Output: T-t path + inversion timing. |
| **Isotope Geochemistry** | δ13C-CO₂ classification, ³He/⁴He mantle indicator | D3 | ❌ Not built | Classification module. Input: isotope ratios. Output: source classification + confidence. |
| **Fracture Connectivity** | Discrete fracture network, connectivity index | D6 | ❌ Not built | Stochastic DFN model. Input: image logs + stress field. Output: connectivity + storage. |
| **Carbonate Diagenesis** | Lucia classification, porosity-permeability transforms | D7 | ❌ Not built | Classification + transform module. Input: thin section + core plugs. Output: reservoir quality map. |
| **Seismic Geomorphology** | Amplitude extraction, geomorphologic classification | D8 | ❌ Not built | Extends `geox_seismic_compute`. Input: seismic volume + horizon. Output: geomorphology map. |
| **Coupled GeoMech-Reservoir** | Pressure buildup, plume migration, containment | D9 | ❌ Not built | Bridge to TOUGH2/CMG OR simplified analytical model. Input: reservoir + caprock properties. Output: containment assessment. |
| **Structural Restoration** | Palinspastic reconstruction, extension estimates | D1 | ❌ Not built | Bridge to Move/2DMove OR simplified flexural model. Input: cross-section + fault data. Output: restored geometry + extension. |
| **Petroleum System Model** | Charge kitchen mapping, migration pathways | D2 | ❌ Not built | Bridge to Trinity/PetroMod OR simplified migration model. Input: source + carrier + seal. Output: kitchen maps + migration vectors. |

### AXIS 3: Architecture (How GEOX Flows Intelligence)

#### Current Flow (What Works Now)
```
User intent → geox_egs_claim_create → claim stored in EGS
                                    ↓
              geox_egs_evidence_attach → evidence linked to claim
                                    ↓
              geox_egs_claim_challenge → counter-evidence attached
                                    ↓
              geox_egs_evidence_reason → synthesize/grade evidence
                                    ↓
              geox_egs_scenario_audit → identify competing models
                                    ↓
              geox_forbidden_claims_scan → enforce epistemic discipline
```

#### Target Flow (What Needs to Be Built)
```
LAS/SEG-Y/PVT/Core/Geochem data
        ↓
[DATA INGESTION LAYER]
  geox_well_ingest (LAS, DST, deviation, tops, core, PVT)
  geox_seismic_ingest (SEG-Y, horizons, faults)
  geox_geochem_ingest (isotopes, biomarkers, gas composition) ← NEW
  geox_core_ingest (plug data, thin sections, photos) ← NEW
  geox_pressure_ingest (RFT/MDT/wireline pressure) ← NEW
        ↓
[COMPUTATION LAYER]
  geox_petrophysics (Vsh, porosity, Sw, perm)
  geox_fault_seal (SGR, clay smear, juxtaposition) ← NEW
  geox_basin_model (1D burial, maturity, charge) ← NEW
  geox_thermal_history (AFT/VR inversion) ← NEW
  geox_isotope_classify (CO₂ source, noble gases) ← NEW
  geox_fracture_network (DFN, connectivity) ← NEW
  geox_carbonate_quality (Lucia, diagenesis) ← NEW
  geox_seismic_geomorph (amplitude, classification) ← NEW
  geox_structural_restore (palinspastic) ← NEW
  geox_ccs_containment (geo-mech coupled) ← NEW
        ↓
[EVIDENCE GOVERNANCE LAYER]
  geox_egs_claim_create → hypothesis
  geox_egs_evidence_attach → evidence linked
  geox_egs_claim_challenge → counter-evidence
  geox_egs_scenario_audit → competing models
  geox_egs_evidence_reason → synthesis + grading
  geox_forbidden_claims_scan → epistemic safety
        ↓
[JUDGMENT LAYER]
  geox_prospect → volumetrics, POS, EVOI
  geox_claim → validate, challenge, seal
  → arifOS 888_JUDGE → SEAL/HOLD/SABAR/VOID
        ↓
[DECISION]
  Arif decides.
```

### AXIS 4: External Integrations (Bridges to Existing Software)

| Software | Purpose | Integration Type | Priority |
|----------|---------|-----------------|----------|
| **PetroMod / TemisFlow** | Basin modelling | API bridge or CLI wrapper | HIGH (D2, D5) |
| **Trinity** | Petroleum systems | CSV import/export | MEDIUM |
| **Move / 2DMove** | Structural restoration | CLI bridge | MEDIUM (D1) |
| **Petrel / RMS** | Reservoir modelling | SEG-Y/LAS import (already partial) | LOW |
| **TOUGH2 / CMG** | CCS simulation | CLI bridge or analytical proxy | MEDIUM (D9) |
| **Image log software** | Fracture analysis | DLIS import + processing | HIGH (D6) |
| **GPlates** | Plate reconstruction | Already referenced in deep_time | LOW |
| **Macrostrat** | Stratigraphic database | Already integrated in geox_basin | ✅ LIVE |
| **ICS Chart** | Geological time scale | Already integrated in deep_time | ✅ LIVE |

### AXIS 5: Priority Roadmap

| Phase | Scope | Tools | Dilemmas Unblocked | Est. Effort |
|-------|-------|-------|-------------------|-------------|
| **Phase 3.1** | Data ingestion | geochem_ingest, core_ingest, pressure_ingest | D2, D3, D4, D5, D6, D7, D9 | 2-3 weeks |
| **Phase 3.2** | Fault seal + isotope | fault_seal, isotope_classify | D3, D4 | 1-2 weeks |
| **Phase 3.3** | Basin modelling bridge | basin_model, thermal_history | D2, D5 | 2-4 weeks (depends on external software) |
| **Phase 3.4** | Fracture + carbonate | fracture_network, carbonate_quality | D6, D7 | 2-3 weeks |
| **Phase 3.5** | Seismic geomorph + CCS | seismic_geomorph, ccs_containment | D8, D9 | 2-3 weeks |
| **Phase 3.6** | Structural restoration | structural_restore | D1 | 2-4 weeks (depends on external software) |

---

## Research Questions for AUDITOR

1. **Data availability:** Which of these data types exist in open/public databases for Malaysian basins? (e.g., BGS, NOGS, academic publications, PETRONAS annual reports)
2. **Open-source engines:** Are there open-source alternatives to PetroMod, Move, TOUGH2 that GEOX could integrate?
3. **Simplifications:** For each engine, what is the minimum viable computation that would distinguish competing hypotheses? (e.g., 1D burial history vs full 3D basin model)
4. **Existing GEOX leverage:** Which current GEOX tools (petrophysics, seismic_compute, geomechanics) can be extended vs which need new engines?
5. **Constitutional constraints:** Which of these engines would need 888_HOLD to register? (all compute tools = judgment lane?)

---

## Execution Instructions

1. **Load this scaffold** into AUDITOR (DeepSeek V4 Pro) or PLAN (Kimi K2.7 Code)
2. **Research each axis** using web search, academic databases, and existing GEOX codebase
3. **Produce a detailed report** with specific tool specs, data source URLs, and architecture diagrams
4. **Prioritize** by: (a) number of dilemmas unblocked, (b) data availability, (c) implementation complexity
5. **Present to Arif** for 888_HOLD approval before any Phase 3 implementation

---

*DITEMPA BUKAN DIBERI — The basin is still arguing back. GEOX must learn to argue louder.*
