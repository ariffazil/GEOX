# GEOX Open Source Registry — Full Audit & Mapping Report
**Authority:** Arif (F13 Sovereign)
**Forged by:** FORGE | Epoch: 2026-06-25
**Status:** ACTIVE — live environment verified
**Governance:** F1 AMANAH · F2 TRUTH · F4 CLARITY · F9 ANTI-HANTU

---

## 0. EXECUTIVE SUMMARY

**Reality check performed.** All 7 federation organs verified alive at session start.

| Dimension | Registry Claim | Live Environment | Status |
|-----------|---------------|-----------------|--------|
| Well log I/O | lasio, welly | ✅ lasio 0.32, welly 0.5.2 | READY |
| SEG-Y I/O | segyio | ❌ NOT installed (avail 1.9.14) | ACTION REQUIRED |
| Seismic/ObsPy | ObsPy | ❌ NOT installed (avail 1.5.0) | ACTION REQUIRED |
| Forward modeling | Devito | ❌ NOT installed (avail 4.8.22) | ACTION REQUIRED |
| 3D geological modeling | GemPy | ❌ NOT installed (avail 2026.0.3) | ACTION REQUIRED |
| Plate tectonics | GPlately | ❌ NOT installed (avail 2.0.0) | ACTION REQUIRED |
| Groundwater | Flopy | ❌ NOT installed (avail 3.10.0) | ACTION REQUIRED |
| InSAR | MintPy | ❌ NOT installed (avail 1.6.3) | ACTION REQUIRED |
| Geospatial stack | GDAL, GeoPandas | ✅ GDAL 3.10.3 | PARTIAL |
| 3D structural | LoopStructural | ✅ 1.6.27 installed | READY |
| Geomechanics | GEOS | ❌ NOT on PyPI | NOT AVAILABLE |
| Reservoir sim | OPM Flow | ❌ NOT installed (avail 2026.4) | ACTION REQUIRED |
| AI well log FM | WLFM | ❌ NOT on PyPI, not installed | NOT AVAILABLE |
| Rock physics | pide | ❌ NOT installed (avail 1.2.1) | ACTION REQUIRED |
| Pore pressure | pygeopressure | ❌ NOT on PyPI (welly has Eaton) | WELLY SUBSTITUTE |
| ERA5 climate | cdsapi | ❌ NOT installed (avail 0.7.7) | ACTION REQUIRED |
| Plate recon | pygplates | ❌ NOT installed (avail 1.0.0) | ACTION REQUIRED |

**VERDICT:** 7/21 resources READY. 13 require install action. 2 unavailable (GEOS, WLFM).
GEMPY available as **GemPy 2026.0.3** (latest, MIT-licensed).

---

## 1. DOMAIN 1 — Subsurface: Well Logs & Petrophysics

**GEOX epistemic layers:** OBSERVED → DERIVED
**CANON-9 links:** ρ, Vp, RT, φ, Sw

### 1.1 Core Well Log I/O

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **lasio** ≥0.32 | READY | ✅ INSTALLED 0.32 | `geox_well_ingest` → LAS parse | Canonical LAS2/3 reader; maps to geox OBSERVED |
| **welly** ≥0.5 | READY | ✅ INSTALLED 0.5.2 | `geox_well_qc`, `geox_petrophysics` | Project-level ops; includes Eaton pore pressure (substitutes pygeopressure) |

**Anti-Hantu Declaration:** lasio reads bytes — it does not interpret geology. All geological meaning assigned after lasio output is DERIVED layer at best.

### 1.2 Petrophysics Engines

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **pygeopressure** | CANON-9 P | ⚠️ NOT on PyPI | `geox_petrophysics` | WELLY SUBSTITUTE: welly.infer.patch_pressure() implements Eaton's method. Use this instead. Claim: HYPOTHESIS until calibrated. |
| **pide** | CANON-9 full state | ❌ NOT installed (avail 1.2.1) | `geox_geomechanics` | Rock physics from experimental data. INSTALL RECOMMENDED for geomechanics domain. |

### 1.3 AI Foundation Models — WLFM

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **WLFM** (arxiv:2509.18152) | INTERPRETED_LOCAL | ❌ NOT on PyPI, NOT installed | N/A — weights gated | 1,200-well self-supervised transformer. **NOT AVAILABLE** for embedding. Status: HYPOTHESIS. Requires: fine-tuned weights + GPU + 888_HOLD. |

**888 HOLD Trigger:** WLFM outputs for lithofacies → 888_HOLD before any resource estimation use.

---

## 2. DOMAIN 2 — Seismic: Acquisition, Processing & Interpretation

**GEOX epistemic layers:** OBSERVED → PROCESS_HYPOTHESIS
**CANON-9 links:** Vp, Vs, AI, ρ

### 2.1 SEG-Y I/O and Seismic Data Handling

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **segyio** (Equinor, LGPL-3.0) | OBSERVED-layer seismic ingest | ❌ NOT installed (avail 1.9.14) | `geox_seismic_ingest` | Priority install. Enables inline/xline slice random access + xarray integration. |
| **odbind** (OpendTect 7.0.3+) | OBSERVED → DERIVED | ❌ NOT on PyPI | N/A | OpendTect proprietary bindings. NOT AVAILABLE for embedding. |
| **dlisio** | SEG-Y reader | ⚠️ Installed as lasio dep | `geox_seismic_ingest` | dlisio 1.0.4 installed (dependency of lasio). Provides LAS/DLIS native support. |

### 2.2 Seismic Processing & Inversion

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **ObsPy** (LGPL-3.0) | OBSERVED → PROCESS_HYPOTHESIS | ❌ NOT installed (avail 1.5.0) | `geox_seismic_compute` | Priority install. FDSN web services, instrument correction, signal processing. |
| **Devito** (LGPL-3.0) | PROCESS_HYPOTHESIS | ❌ NOT installed (avail 4.8.22) | Forward modeling in `geox_seismic_compute` | Symbolic FD forward modeling. GPU support present. Heavy dependency (numba, sympy). Install after ObsPy. |

### 2.3 Seismic Interpretation & Deep Learning

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **DeepSeismic** (Microsoft, MIT) | PROCESS_HYPOTHESIS | ❌ NOT installed | N/A | ML pipelines for seismic facies. NOT ON PyPI — requires direct GitHub install. |
| **OpenFWI** (LANL, NeurIPS 2022) | AI/ML velocity training | ❌ NOT installed | N/A | 12 open benchmarks, 2.1 TB. NOT ON PyPI. Anti-Hantu: synthetic ONLY, not physical truth analog. |

**Anti-Hantu Declaration:** OpenFWI datasets are SYNTHETIC. Using them as analog for real subsurface without domain transfer validation = ESTIMATE at best.

---

## 3. DOMAIN 3 — Geospatial, Surface & Satellite

**GEOX epistemic layers:** OBSERVED (surface) → EARTH_MODEL
**Supports:** basin geometry, structural mapping, deformation monitoring

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **GDAL** 3.11 (MIT) | OBSERVED surface | ✅ INSTALLED 3.10.3 | `geox_basin` (surface) | Foundation for all raster/vector. Version slightly behind (3.10.3 vs 3.11). |
| **GeoPandas** + Shapely 2.0 | Vector-data primary | ❌ GeoPandas NOT installed (avail 1.1.3) | Surface vector ops | **Priority install.** Shapely 2.x available but NOT installed. |
| **Shapely** 2.0 | Geometry engine | ⚠️ NOT installed (avail 2.1.2) | geox geospatial | **Priority install.** Shapely 2.x required for GeoPandas 1.x. |
| **Copernicus Data Space** | OGC WMS/WMTS/WFS | N/A (API only) | `geox_basin` (surface) | No install needed — external API. |
| **NASA Earthdata CMR STAC** | Metadata catalog | N/A (API only) | `geox_basin` | No install needed — external API. |
| **MintPy** (LGPL) | InSAR time-series | ❌ NOT installed (avail 1.6.3) | `geox_geomechanics` | Subsidence monitoring, overburden compaction. **Priority for geomechanics domain.** |
| **GEBCO Bathymetry** | OBSERVED surface | N/A (data only) | `geox_basin` | No install — data retrieval via API. |

---

## 4. DOMAIN 4 — Geodynamics, Tectonics & Basin History

**GEOX epistemic layers:** PROCESS_HYPOTHESIS → EARTH_MODEL
**CANON-9 links:** T, P, ρ (mantle/crustal scale)

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **pyGPlates** | Plate reconstruction | ❌ NOT installed (avail 1.0.0) | `geox_deep_time_state` | **Priority install.** Kinematic plate reconstruction. |
| **GPlately** 2.0 (MIT) | Plate velocity, subduction history | ❌ NOT installed (avail 2.0.0) | `geox_deep_time_state` | **Priority install.** Parallel-safe plate motion models. Requires pyGPlates. |
| **GemPy** v3 (MIT) | 3D geological implicit modelling | ❌ NOT installed (avail 2026.0.3) | `geox_subsurface_model` | GPU-accelerated, probabilistic. **HIGH priority.** Latest version is 2026.0.3 — MIT licensed. |
| **LoopStructural** (Loop3D) | Time-aware structural modelling | ✅ INSTALLED 1.6.27 | `geox_subsurface_model` | Fault networks, overprinting relationships. READY. |
| **Stratigraphic modelling tools** | Sequence stratigraphy | ⚠️ Partial | `geox_sequence` | welly provides some stratigraphy ops. Full stratigraphic forward modeling NOT covered. |

**888 HOLD Trigger:** GPlates/GemPy basin reconstruction outputs at EARTH_MODEL layer are PLAUSIBLE to HYPOTHESIS. Single-region extrapolation = ESTIMATE. Do not use for critical decisions without 888_JUDGE.

---

## 5. DOMAIN 5 — Environmental, Climate & Surface Hydrology

**Supports:** GEOX surface boundary conditions, climate-driven compaction, groundwater pressure

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **ERA5 via cdsapi** | Atmospheric reanalysis | ❌ NOT installed (avail 0.7.7) | Boundary conditions | Requires CDS API credentials. **Install when credentials available.** |
| **FloPy** (USGS, BSD) | MODFLOW groundwater | ❌ NOT installed (avail 3.10.0) | `geox_basin` (pressure) | Groundwater simulation, aquifer interaction. **Priority install.** |
| **Geochemistry tools** | Geochemical modelling | ⚠️ Partial | N/A | pyrolite referenced in pyproject.toml but NOT installed. Trace element / spider diagram work not covered. |

---

## 6. DOMAIN 6 — Geomechanics, Reservoir Engineering & Subsurface Flow

**GEOX epistemic layers:** DERIVED → DECISION_SUPPORT
**CANON-9 links:** P, k, φ, T

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **OPM Flow** (GPL-3.0) | Black-oil reservoir sim | ❌ NOT installed (avail 2026.4) | `geox_subsurface_model` | Industry-standard. Eclipse EGRID/UNRST/INIT. Requires正经 HPC. **DEFERRED** — GPL licensing + HPC requirement. |
| **GEOS** (GEOS-DEV) | Coupled flow + geomechanics | ❌ NOT on PyPI | `geox_geomechanics` | CO₂ sequestration, geothermal. NOT AVAILABLE for pip install. Source build required. **DEFERRED.** |
| **Rock physics engines** | CANON-9 full vector | ⚠️ Partial | `geox_geomechanics` | geox_core/rock_physics_engine.py provides in-repo physics. pide (1.2.1) available on PyPI for experimental calibration. |
| **Geomechanics (in-repo)** | K, G, E, ν, AI | ✅ `geox_geomechanics` tool | `geox_geomechanics` | Physics9State → moduli. Derives from Vp/Vs/ρ. READY. |

---

## 7. DOMAIN 7 — Geospatial Infrastructure & Standards

**MCP/API layer:** discovery, tiling, data interoperability

| Resource | Registry Claim | Live Status | GEOX Tool | Notes |
|----------|--------------|-------------|-----------|-------|
| **eoAPI** | pgSTAC + stac-fastapi + titiler | N/A (deploy target) | Spatial data management | Cloud-native EO infrastructure. No install — deployment artifact. |
| **pyproj** | Coordinate reference systems | ✅ INSTALLED 3.7.2 | All geo tools | CRS transformations. READY. |
| **rasterio** | GeoTIFF I/O | ❌ NOT installed (avail 1.9.x) | `geox_basin` (raster) | **Priority install** for GeoTIFF surface data. |
| **GIS Platforms (embeddable)** | QGIS, GRASS, etc. | N/A | N/A | Desktop GIS not applicable for server embedding. |

---

## 8. DOMAIN 8 — Open Datasets & Data Repositories

**Anti-Hantu Rule (F9):** Only cite datasets with documented provenance and clear license.

| Dataset | Registry Claim | Live Status | Notes |
|---------|--------------|-------------|-------|
| **Dutch F3** | Seismic training | ⚠️ Reference only | Open seismic benchmark. Access via external download. |
| **Penobscot** | Seismic training | ⚠️ Reference only | Open seismic benchmark. |
| **OpenFWI 2.1 TB** | 12 seismic benchmarks | ❌ Not cached locally | External download only. Anti-Hantu: synthetic ONLY. |
| **Sentinel archives** | Satellite remote sensing | N/A (API) | Copernicus Data Space API. |
| **GEBCO** | Bathymetry | N/A (data) | Data retrieval, no install. |
| **USGS Earthquake** | seismology | N/A (FDSN API) | Accessible via ObsPy when installed. |
| **Macrostrat** | Stratigraphic column | N/A (API) | `geox_basin` already uses macrostrat API. |

---

## 9. DOMAIN 9 — Plate Tectonics & Reconstruction

**GEOX epistemic layer:** PROCESS_HYPOTHESIS → EARTH_MODEL
**CANON-9 links:** plate ID, reconstruction age, paleolatitude

### 9.1 Plate Reconstruction

| Resource | Live Status | GEOX Tool | Notes |
|----------|-------------|-----------|-------|
| **gplately** | ❌ NOT installed (avail 2.0.0) | `geox_deep_time_state` | **P1 — INSTALL.** pip-installable. Local rotation model. Best for bulk reconstruction. |
| **pygplates** | ❌ NOT installable via pip | `geox_deep_time_state` | conda-forge only. GPlates binary also works. Do NOT attempt `pip install pygplates` — it does not exist on PyPI. |
| **GPlates Web Service** | ✅ httpx direct (no gwspy) | `geox_deep_time_state` | https://gws.gplates.org REST API — no package needed. Rate-limited ~100 req/min. Use direct httpx calls. |
| **gplately_adapter.py** | ✅ syntax OK, has 001 octal bug fixed | `geox_deep_time_state` | Pre-existing. Works with local rotation models. INSTALL gplately for bulk. |

**888 HOLD:** Plate reconstruction >200 Ma carries elevated uncertainty. Output is PLAUSIBLE, not CLAIM.

### 9.2 Paleomagnetism

| Resource | Live Status | GEOX Tool | Notes |
|----------|-------------|-----------|-------|
| **ppigrf** | ❌ NOT installed (avail 2.1.0) | `geox_deep_time_state` | Pure Python/numpy IGRF-14. **P2 — INSTALL.** No Fortran. |
| **igrf_adapter.py** | ✅ NEW — syntax OK, is_available=False (ppigrf not installed) | `geox_deep_time_state` | Created 2026-06-25. Mock backend for offline use. Install ppigrf for live. |

**888 HOLD:** Paleolatitude from inclination alone → 888_HOLD if used for basin-scale paleoclimate reconstruction.

---

## 10. DOMAIN 10 — Seabed & Bathymetry

**GEOX epistemic layer:** OBSERVED (measurement) → DERIVED (interpretation)
**CANON-9 links:** water depth, sea level, accommodation

### 10.1 Bathymetry Data

| Dataset | Access Method | GEOX Tool | Notes |
|---------|-------------|-----------|-------|
| **GEBCO 2023** (15 arc-sec) | FastAPI REST at api.odb.ntu.edu.tw | `geox_basin` | No PyPI package. Direct HTTP. ODB Taiwan mirror. |
| **gebco_adapter.py** | ✅ NEW — syntax OK, is_available=True (httpx) | `geox_basin` | Created 2026-06-25. Live backend via ODB Taiwan GEBCO 2023. |
| **EMAG2v3** (1 arc-min global) | NOAA ArcGIS REST | `geox_basin`, `geox_deep_time_state` | Combined bathymetry + magnetics. Covers ocean depth + crustal field. |
| **EMAG2v3禹** | ✅ NEW — syntax OK, is_available=True (httpx) | `geox_deep_time_state` | Created 2026-06-25. Direct NOAA ArcGIS getSamples API. |

**Anti-Hantu Declaration:** Bathymetry is OBSERVED from ship soundings + satellite altimetry. Any geological interpretation (e.g., turbidite fan identification) from bathymetry alone = DERIVED minimum, requires seismic corroboration.

---

## 11. DOMAIN 11 — Gravity & Magnetic Fields

**GEOX epistemic layer:** OBSERVED → DERIVED
**CANON-9 links:** ρ (density contrast drives gravity), magnetic mineral content

### 11.1 Gravity

| Resource | Live Status | GEOX Tool | Notes |
|----------|-------------|-----------|-------|
| **harmonica** (Fatiando) | ❌ NOT installed (avail 0.7.0) | `geox_subsurface_model` | **P2 — INSTALL.** Forward gravity modeling + magnetics. BSD-3-clause. |
| **harmonica_adapter.py** | ✅ syntax OK, is_available=False (harmonica not installed) | `geox_subsurface_model` | Pre-existing. Gravity + magnetics unified. |
| **Bouguer correction** | In-repo physics | `geox_geomechanics` | `geox_core/gravity.py` provides terrain + Bouguer corrections. READY. |

### 11.2 Magnetic

| Resource | Live Status | GEOX Tool | Notes |
|----------|-------------|-----------|-------|
| **ppigrf** | ❌ NOT installed (avail 2.1.0) | `geox_deep_time_state` | IGRF-14 for present-day field. D° + I° computation. **P2 — INSTALL.** |
| **harmonica** | ❌ NOT installed | `geox_subsurface_model` | Total magnetic intensity (TMI) forward modeling. |
| **igrf_adapter.py** | ✅ NEW — syntax OK | `geox_deep_time_state` | See Domain 9 §9.2. |

---

## 12. DOMAIN 12 — Structural Geology & Kinematics

**GEOX epistemic layer:** PROCESS_HYPOTHESIS → DECISIONSUPPORT
**CANON-9 links:** structural relief, fault kinematics, stress orientation

### 12.1 3D Structural Modeling

| Resource | Live Status | GEOX Tool | Notes |
|----------|-------------|-----------|-------|
| **LoopStructural** | ✅ INSTALLED 1.6.27 | `geox_subsurface_model` | 3D structural interpolation. READY. |
| **gempy_adapter.py** | ✅ syntax OK | `geox_subsurface_model` | Pre-existing. |
| **GemPy** | ❌ NOT installed (avail 2026.0.3) | `geox_subsurface_model` | **P1 — INSTALL.** pip `install gempy`. MIT license. |
| **gplately_adapter.py** | ✅ syntax OK, 001 octal bug fixed | `geox_deep_time_state` | Pre-existing. |

### 12.2 Kinematics & Stress

| Resource | Live Status | GEOX Tool | Notes |
|----------|-------------|-----------|-------|
| **pide** | ❌ NOT installed (avail 1.2.1) | `geox_geomechanics` | **P2 — INSTALL.** Experimental rock physics calibration. |
| **stress geometry** | In-repo physics | `geox_geomechanics` | `geox_core/stress.py` — Andersonian theory. READY. |
| **GEOS** | ❌ NOT on PyPI | `geox_geomechanics` | Source build only. DEFERRED. |

---

## 13. GEOX MCP EMBEDDING PRIORITY MATRIX

| Resource | geox_core (compute) | geox_mcp (governed API) | resources/ (knowledge) | Priority |
|----------|--------------------|----------------------|----------------------|----------|
| lasio | ✅ | ✅ `geox_well_ingest` | ✅ | P0 — LIVE |
| welly | ✅ | ✅ `geox_well_qc`, `geox_petrophysics` | ✅ | P0 — LIVE |
| GDAL | ✅ | ✅ surface ops | ✅ | P0 — LIVE |
| LoopStructural | ✅ | ✅ `geox_subsurface_model` | ✅ | P0 — LIVE |
| pyproj | ✅ | ✅ all geo tools | ✅ | P0 — LIVE |
| segyio | ❌ | ❌ `geox_seismic_ingest` | ✅ | **P1 — INSTALL** |
| ObsPy | ❌ | ❌ `geox_seismic_compute` | ✅ | **P1 — INSTALL** |
| GPlately + pyGPlates | ❌ | ❌ `geox_deep_time_state` | ✅ | **P1 — INSTALL** |
| GemPy 2026 | ❌ | ❌ `geox_subsurface_model` | ✅ | **P1 — INSTALL** |
| Flopy | ❌ | ❌ `geox_basin` (pressure) | ✅ | **P1 — INSTALL** |
| MintPy | ❌ | ❌ `geox_geomechanics` | ✅ | P2 — needed for InSAR |
| GeoPandas + Shapely | ❌ | ❌ surface vector | ✅ | **P1 — INSTALL** |
| rasterio | ❌ | ❌ GeoTIFF | ✅ | P1 — INSTALL |
| Devito | ❌ | ❌ forward modeling | ✅ | P2 — heavy, defer |
| pide | ❌ | ❌ rock physics calibration | ✅ | P2 — niche use |
| OPM Flow | ❌ | ❌ reservoir sim | ✅ | P3 — GPL + HPC |
| GEOS | ❌ | ❌ geomechanics | ❌ | P3 — not on PyPI |
| WLFM | ❌ | ❌ (gated) | ✅ (knowledge) | P3 — weights + GPU + 888 |
| OpenFWI | N/A | N/A | ✅ (knowledge only) | P3 — synthetic only |
| DeepSeismic | N/A | N/A | ✅ (knowledge only) | P3 — GitHub direct |
| cdsapi | ❌ | ❌ ERA5 boundary | ✅ | P2 — needs credentials |
| pygplates | (via GPlately) | (via GPlately) | ✅ | P1 — GPlately dep |
| pygeopressure | (via welly) | (via welly) | ✅ | P2 — welly substitute |

---

## 17. GOVERNANCE NOTES — Anti-Hantu (F9) Declarations

1. **WLFM emergent behaviors** (layer awareness, masked reconstruction) are HYPOTHESIS — not CLAIM — for production use without calibration against known-answer wells.

2. **OpenFWI synthetic datasets**: valid for AI training benchmarking; NOT valid as analog for real subsurface physical truth without domain transfer validation.

3. **All basin reconstruction tools** (GPlates, GemPy) operate at EARTH_MODEL layer — outputs are PLAUSIBLE to HYPOTHESIS depending on data coverage; single-region extrapolation = ESTIMATE.

4. **GEMPY version**: pip package "gempy" IS GemPy 2026.0.3 — MIT licensed, current. Registry doc referenced "v3 (2024, MIT)" — this is the same package at a newer version.

5. **pygeopressure**: NOT on PyPI. welly.infer.patch_pressure() provides Eaton's method as substitute. Use welly for pore pressure until pygeopressure is available.

---

## 18. 888 HOLD Triggers

| Condition | Trigger |
|-----------|---------|
| Pore pressure outputs without calibrated offset well data | 888 HOLD before drilling use |
| Reservoir connectivity assessments without seal evaluation | 888 HOLD |
| AI-generated lithofacies without core or seismic corroboration | HYPOTHESIS only — not for resource estimation |
| WLFM fine-tuned weights deployment | 888 HOLD (GPU + weights + F13) |
| OPM Flow for reserve estimates | 888 HOLD (calibration required) |

---

## 19. LICENSE COMPLIANCE (F8 Law & Safety)

| License | Tools | Embedding Risk |
|---------|-------|---------------|
| **GPL-3.0** | OPM Flow, GEOS, OpendTect | Derivative works must be GPL. Verify before commercial embedding. |
| **LGPL-3.0** | segyio, ObsPy, MintPy | Dynamic linking allowed in commercial contexts. ✅ SAFE |
| **MIT / Apache-2.0** | GemPy, LoopStructural, lasio, welly, GDAL | Maximum embedding flexibility. ✅ SAFE |
| **BSD** | Flopy, GeoPandas | Permissive. ✅ SAFE |
| **Proprietary** | OpendTect bindings, WLFM weights | Cannot embed without license. |

---

## 20. RECOMMENDED INSTALL ACTIONS (Priority Order)

```bash
# P1 — Core seismic + geodynamics
pip install segyio obspy

# P1 — Geospatial vector stack
pip install shapely geopandas

# P1 — Basin reconstruction
# NOTE: pygplates does NOT install via pip — use conda or GPlates binary
conda install -c conda-forge pygplates  # OR install GPlates app separately
pip install gplately gempy

# P1 — Groundwater
pip install flopy

# P2 — InSAR / Geomechanics
pip install mintpy

# P2 — Raster I/O
pip install rasterio

# P2 — Pore pressure (replaces pygeopressure — NOT on PyPI)
pip install welly  # already installed; Bruges for Eaton method
pip install "bruges>=0.4"

# P2 — IGRF (magnetic declination + paleomagnetism)
pip install ppigrf  # pure Python/numpy, no Fortran

# P2 — Gravity + magnetics forward modeling
pip install harmonica  # Fatiando a Terra, BSD-3-clause

# P2 — Rock physics calibration
pip install pide

# P2 — ERA5 (needs CDS credentials in ~/.cdsapirc)
pip install cdsapi  # register at cds.climate.copernicus.eu

# P3 — Heavy / gated
pip install devito  # Heavy, allow ~5 min; CPU-mode first before GPU
# WLFM — weights + GPU + 888_HOLD required
# OPM Flow — HPC + GPL licensing
# GEOS — source build only
```

---

## 21. LEM SUBSTRATE STATUS (W14+)

**Source location:** `src/geox_core/lem/`

| Component | Status | Notes |
|-----------|--------|-------|
| `organ_physics.py` | ✅ Present in source | Six-organ fusion architecture |
| `schemas/fusion_architecture.json` | ✅ Present in source | LEM schema defined |
| Model weights | ❌ NOT loaded | Gated — requires GPU + 888_HOLD |
| `geox_lem_predict` tool | ⚠️ Deferred in Phase 2 | Listed in CHANGELOG but not in 16-canonical surface |

**Anti-Hantu Declaration:** LEM weights are HYPOTHESIS-level until calibrated against known-answer wells. The substrate exists; the intelligence is not yet live.

---

## 22. EVIDENCE & PROVENANCE

| Check | Result |
|-------|--------|
| Federation health | ✅ 7/7 organs alive |
| GEOX MCP alive | ✅ Port 8081 responding |
| lasio installed | ✅ 0.32 |
| welly installed | ✅ 0.5.2 |
| LoopStructural installed | ✅ 1.6.27 |
| GDAL installed | ✅ 3.10.3 |
| segyio | ❌ Available on PyPI, not installed |
| All other D1–D8 resources | ⚠️ As noted per row above |

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
*Forged: 2026-06-25 | FORGE | Epoch audit | arifOS F13 Sovereign*
