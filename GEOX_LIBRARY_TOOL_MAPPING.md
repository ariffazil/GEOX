# GEOX Library → 13-Tool Surface Mapping
> DITEMPA BUKAN DIBERI | Ω₀ = 0.04 | F13 Sovereign: Arif approves before irreversible integration

---

## Integration Philosophy

**Adapter Pattern**: Each library gets a thin internal adapter in `geox_core/engines/`. The adapter translates library outputs to GEOX internal schemas. MCP tools never call libraries directly.

```
MCP Tool → Engine Function → Adapter → External Library
                                    ↓
                           GEOX Internal Schema
```

---

## Detailed Library → Tool Mapping

### OBSPY → Phase 0 (Foundation)

#### Library Contract
```python
# What ObsPy provides:
- obspy.core.Stream: container for seismic traces
- obspy.read(): auto-detect format (SEG-Y, MiniSEED, SAC, GSE2, etc.)
- obspy.Stream.filter(): bandpass, lowpass, highpass, detrend, taper
- obspy.Stream.slice(): time windowing
- obspy.signal: spectral analysis, FK, semblance, response removal
- obspy.taup: travel-time modeling
```

#### Target: `geox_seismic_compute`

| Mode | ObsPy Function | GEOX Output Key | Status |
|------|----------------|-----------------|--------|
| `load_line` | `obspy.read(path, format="SEG-Y")` | `traces`, `stats`, `sampling_rate` | **TO BUILD** |
| `load_volume` | `obspy.read()` × inline traces | `volume_metadata`, `trace_count` | **TO BUILD** |
| `compute_attribute` | `obspy.Stream` + numpy | `attribute_map`, `rms/variance/sweetness` | **TO BUILD** |
| `signal_process` | `obspy.Stream.filter()` + `detrend` + `taper` | `processed_stream`, `processing_log` | **TO BUILD** |
| `ac_detect` | Custom: semblance + variance anomaly | `ac_score`, `anomaly_map`, `confidence` | **ABSORB from `geox_anomalous_contrast_detector`** |

**New parameters**:
```python
async def geox_seismic_compute(
    volume_ref: str,
    mode: Literal["load_line", "load_volume", "compute_attribute", "signal_process", "ac_detect"],
    attribute: str = "rms",  # for compute_attribute
    filter_spec: dict = None,  # for signal_process: {"type": "bandpass", "freqmin": 5, "freqmax": 50}
) -> dict:
```

#### Target: `geox_time_depth_anchor`
| Sub-mode | ObsPy Function | GEOX Output Key |
|----------|----------------|-----------------|
| `checkshot` | `obspy.TauPy` or custom TD table | `td_curve`, `velocity_model` |
| `vsp` | `obspy.io.segy` VSP reader | `depth_time_pairs`, `vertical_velocity` |

#### Target: `geox_data_ingest_bundle`
| Format | ObsPy Reader | GEOX Schema Key |
|--------|-------------|-----------------|
| SEG-Y | `obspy.read(format="SEG_Y")` | `seismic_traces`, `trace_headers` |
| MiniSEED | `obspy.read(format="MiniSEED")` | `waveforms`, `event_catalog` |
| SAC | `obspy.read(format="SAC")` | `traces`, `sac_headers` |

---

### PETROLIB → Phase 2

#### Library Contract
```python
# What Petrolib provides:
- Quanti class: full formation evaluation workflow
- pp.vshale(): Vshale (Clavier, Stieber, Larionov methods)
- pp.porosity(): effective/total porosity (density, sonic methods)
- pp.water_saturation(): Archie, Simandoux
- pp.permeability(): permeability estimation
- pp.flags(): pay flagging with cutoffs
```

#### Target: `geox_subsurface_generate_candidates`

**Current**: Single-curve computation with hardcoded formulas.
**Enhanced**: Multi-curve, multi-method computation.

| Parameter | Method Options | Output Key |
|-----------|---------------|-------------|
| `vshale_method` | `"clavier"`, `"stieber"`, `"larionov"`, `"linear"` | `vshale_array` |
| `porosity_method` | `"density"`, `"sonic"`, `"neutron"`, `"average"` | `porosity_array` |
| `sw_method` | `"archie"`, `"simandoux"` | `sw_array` |
| `permeability_model` | `" Timur"`, `"koa"` | `perm_array` |
| `cutoffs` | `{"phi_min": 0.10, "vsh_max": 0.50, "sw_max": 0.70}` | `pay_flags` |

**New parameters**:
```python
async def geox_subsurface_generate_candidates(
    well_ref: str,
    zone_top: float,
    zone_base: float,
    vshale_method: str = "clavier",
    porosity_method: str = "density",
    sw_method: str = "archie",
    cutoffs: dict = None,
) -> dict:
```

**Uncertainty output**:
```python
{
    "result": {
        "vshale": {"mean": 0.23, "p10": 0.15, "p90": 0.35},
        "porosity": {"mean": 0.18, "p10": 0.12, "p90": 0.25},
        "sw": {"mean": 0.35, "p10": 0.20, "p90": 0.55},
        "net_pay_m": 42.5,
        "hydrocarbon_pore_volume_m3": 1.2e6
    },
    "uncertainty": {
        "method": "petrolib_monte_carlo",
        "iterations": 10000,
        "distribution": "lognormal"
    },
    "evidence_refs": ["well_ref"],
    "processing_log": [
        {"step": "vshale", "library": "petrolib", "method": "clavier"},
        {"step": "porosity", "library": "petrolib", "method": "density"}
    ]
}
```

---

### GEOH5PY → Phase 2

#### Library Contract
```python
# What geoh5py provides:
- geoh5.io.*: read/write .geoh5 format
- Supports: points, curves, surfaces, 2D grids, 3D grids, block models, drillholes
- Industry standard format (Geosoft, GoCAD, Micromine compatible)
```

#### Target: `geox_data_ingest_bundle` + `geox_data_qc_bundle`

**New format support**:
| Format | Reader | GEOX Schema |
|--------|--------|-------------|
| `.geoh5` | `geoh5.io.Reader(path)` | `geoh5_object` (any type) |

**New artifact type**: `GEOSCIENCE_MODEL` — stores 3D geological models, grids, interpretations.

---

### SEISBENCH → Phase 3

#### Library Contract
```python
# What SeisBench provides:
- seisbench.models.*: PhaseNet, EQTransformer, GPD, CRED
- seisbench.WaveformModel.classify(stream): ML phase picks
- seisbench.data.*: STEAD, INSTANCE, Bohemia datasets
```

#### Target: `geox_seismic_compute`

| New Mode | SeisBench Function | GEOX Output Key |
|----------|-------------------|-----------------|
| `ml_pick_phase` | `model.classify(stream)` | `picks`, `phase_probabilities`, `model_version` |
| `ml_detect` | `model.classify()` with threshold | `detections`, `confidence` |
| `ml_denoise` | `model.classify()` with denoise model | `denoised_stream` |

**ML Constitutional Output** (required for F2/F9):
```python
{
    "result": {
        "picks": [
            {"time": 12.45, "phase": "P", "model_confidence": 0.87, "polarity": "up"},
            {"time": 18.22, "phase": "S", "model_confidence": 0.72, "polarity": "down"}
        ]
    },
    "ml_provenance": {
        "model_name": "PhaseNet",
        "model_version": "3.0.0",
        "training_dataset": "STEAD",
        "input_hash": "sha256:abc123...",
        "confidence_source": "softmax_probability"
    },
    "uncertainty": {
        "band": "model_confidence_score",
        "known_limitations": ["low_snr_waveforms", "depth > 300km"]
    }
}
```

---

### GEMPY → Phase 3

#### Library Contract
```python
# What GemPy provides:
- gp.create_geomodel(): create 3D model
- gp.map_stack_to_surfaces(): assign surfaces to series
- gp.compute_model(): implicit interpolation → 3D volumetric geology
- gp.get_cross_section(): 2D cross-section from 3D
```

#### Target: `geox_sequence_interpret`

**New flag**: `structural_model: bool = False`

```python
async def geox_sequence_interpret(
    well_refs: list[str],
    section_id: str,
    workflow: Literal["single_well", "project", "preview"],
    structural_model: bool = False,  # NEW: GemPy integration
    gempy_config: dict = None,  # NEW: extent, refinement, fault settings
) -> dict:
```

When `structural_model=True`:
- Input: surface points + orientations from well markers
- Output: `geo_model` object, cross-section, 3D mesh data
- All GemPy provenance captured (structural groups, fault relations, interpolation method)

---

### BURNMAN → Phase 4

#### Library Contract
```python
# What BurnMan provides:
- minerals.SLB_2011.*: mineral thermodynamic properties
- burnman.seismic.PREM(): Earth reference model
- assemblage.evaluate(["rho", "v_p", "v_s"]): seismic properties at P/T
- burnman.velocities(...): Vp, Vs, density as function of depth
```

#### Target: `geox_prospect_evaluate`

**New internal method**: `feasibility_check_from_burnman()`

```python
async def geox_prospect_evaluate(
    prospect_ref: str,
    mode: Literal["screen", "appraise", "develop"],
    evidence_refs: list[str] = None,
    thermodynamic_check: bool = False,  # NEW: BurnMan feasibility
) -> dict:
```

**Thermodynamic output**:
```python
{
    "result": {
        "pos": 0.34,  # REAL computed value (not hardcoded 0.22)
        "stoiip_p50": 2.1e8,
        "pt_feasibility": {
            "reservoir_mineral": "quartz_sandstone",
            "pt_observed": {"p_mpa": 35.2, "t_c": 118},
            "pt_vs_earth_model": "within PREM bounds",
            "mineral_stability": "stable",
            "velocity_prediction": {"vp_km_s": 3.45, "vs_km_s": 2.10}
        }
    },
    "evidence_refs": [...],
    "processing_log": [
        {"step": "pt_validation", "library": "burnman", "version": "1.1.0"}
    ]
}
```

---

## Adapter Registry

| Adapter | File | Library | Phase |
|---------|------|---------|-------|
| `ObsPyAdapter` | `geox_core/engines/seismic/obspy_adapter.py` | ObsPy | 0 |
| `SeisBenchAdapter` | `geox_core/engines/seismic/seisbench_adapter.py` | SeisBench | 3 |
| `PetrolibAdapter` | `geox_core/engines/petrophysics/petrolib_adapter.py` | Petrolib | 2 |
| `Geoh5Adapter` | `geox_core/io/geoh5_adapter.py` | geoh5py | 2 |
| `GemPyAdapter` | `geox_core/engines/geomodeling/gempy_adapter.py` | GemPy | 3 |
| `BurnManAdapter` | `geox_core/engines/thermodynamics/burnman_adapter.py` | BurnMan | 4 |

---

## Dependency Versions (Pinned)

```toml
obspy = ">=1.4.0,<2.0.0"
seisbench = ">=0.4.0,<1.0.0"
petrolib = ">=2.0.0,<3.0.0"
geoh5py = ">=0.10.0,<1.0.0"
gempy = ">=2.0.0,<3.0.0"
burnman = ">=1.0.0,<2.0.0"
pyrolite = ">=0.5.0,<1.0.0"
loopstructural = ">=1.0.0,<2.0.0"
pyrocko = ">=2023.0.0,<2024.0.0"
```

---

## Status: ACTIVE — Phase 0 ObsPy adapter in progress
