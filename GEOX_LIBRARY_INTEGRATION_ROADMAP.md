# GEOX Library Integration Roadmap
> **DITEMPA BUKAN DIBERI** — Intelligence is forged, not given.
> Phase 0-1: ObsPy Foundation | Phase 2: Petrolib + geoh5py | Phase 3: SeisBench + GemPy | Phase 4: BurnMan + Pyrolite
> Status: PROPOSED | Ω₀ = 0.04 | F13 Sovereign: Arif approves before execution

---

## Architecture Principle

**Library-as-Engine, Tool-as-Interface + Judge-as-Governor.**

```
geox_mcp/tools/          ← MCP surface (13 tools, stable)
        ↓ calls
geox_core/engines/       ← Computation engines (enhance this layer)
        ↓ calls
geox_core/engines/seismic/obspy_adapter.py  ← NEW: ObsPy bridge
geox_core/engines/seismic/seisbench_adapter.py  ← NEW: SeisBench bridge
geox_core/engines/petrophysics/petrolib_adapter.py  ← NEW: Petrolib bridge
```

No library is ever exposed directly as an MCP tool. Heavy computation stays inside the engine layer.

---

## Phase 0 — ObsPy Foundation (IMMEDIATE)

### Goal
Kill `PENDING_ENGINE` stub in `geox_seismic_analyze_volume`. Enable real seismic I/O and signal processing.

### Dependencies
- `obspy` ≥ 1.4 — seismic data I/O, signal processing
- `SEGYY` or built-in ObsPy SEG-Y reader

### New Files
```
src/geox_core/engines/seismic/obspy_adapter.py   ← ObsPy bridge
src/geox_core/io/segy_reader.py                  ← SEG-Y ingestion
```

### Tool Enhancements

#### `geox_seismic_compute` — Enhanced Modes
| Mode | Before | After |
|------|--------|-------|
| `load_line` | stubs | ObsPy reads SEG-Y, MiniSEED, SAC |
| `load_volume` | stubs | ObsPy 3D volume load |
| `compute_attribute` | PENDING_ENGINE | Real RMS, variance, coherence, sweetness via ObsPy |
| `signal_process` | N/A | bandpass filter, detrend, taper, FK, semblance |
| `anomalous_contrast` | separate tool | absorbed as `mode="ac_detect"` |

#### `geox_data_ingest_bundle` — New Formats
- LAS, CSV, base64 (existing)
- **NEW**: SEG-Y via ObsPy
- **NEW**: MiniSEED, SAC

### Output Schema Enhancement
All seismic outputs must include:
```python
{
    "result": { ... },
    "uncertainty": { "band": "P10/P50/P90", "source": "ObsPy computed" },
    "evidence_refs": [...],
    "processing_log": [
        { "step": "load", "library": "obspy", "version": "1.4.0", "params": {...} },
        { "step": "filter", "library": "obspy", "version": "1.4.0", "params": {...} }
    ],
    "parameters_hash": "sha256:...",
    "library_versions": { "obspy": "1.4.0", "numpy": "2.0.0" }
}
```

### Internal Adapter Contract
```python
class ObsPyAdapter:
    """Strict schema translator: ObsPy Stream → GEOX internal dict."""
    def load_seismic(self, path: str, format: str) -> dict: ...
    def compute_attribute(self, stream: dict, attribute: str) -> dict: ...
    def filter_stream(self, stream: dict, filter_spec: dict) -> dict: ...
    def detect_anomalous_contrast(self, stream: dict) -> dict: ...
```

---

## Phase 1 — Petrophysics + Data Exchange

### Goal
Replace stub computations in `geox_subsurface_generate_candidates` with real petrophysics. Establish geoh5 as the exchange format.

### Dependencies
- `petrolib` ≥ 2.0 — formation evaluation (Vsh, porosity, Sw, permeability, net pay)
- `geoh5py` ≥ 0.10 — industry-standard geoscience data exchange

### New Files
```
src/geox_core/engines/petrophysics/petrolib_adapter.py
src/geox_core/io/geoh5_adapter.py
```

### Tool Enhancements
#### `geox_subsurface_generate_candidates` → gains multi-curve support
- GR + RHOB + RT + NPHI + DT natively via Petrolib
- Proper uncertainty propagation (Monte Carlo)
- Cutoff-based net pay flagging

#### `geox_data_ingest_bundle` + `geox_data_qc_bundle` → geoh5 support
- Read/write `.geoh5` files
- GEOX ↔ WEALTH ↔ external software exchange

---

## Phase 2 — ML Interpretation + 3D Modeling

### Goal
Add ML-assisted seismic interpretation and 3D geological modeling as internal engines.

### Dependencies
- `seisbench` ≥ 0.4 — ML waveform classification, phase picking
- `gempy` ≥ 2.0 — implicit 3D geological modeling

### New Files
```
src/geox_core/engines/seismic/seisbench_adapter.py
src/geox_core/engines/geomodeling/gempy_adapter.py
```

### Tool Enhancements
#### `geox_seismic_compute` → New ML Modes
- `mode="pick_phase"` — ML phase picking (PhaseNet, EQTransformer)
- `mode="detect_events"` — ML event detection

#### `geox_sequence_interpret` → Structural Modeling
- `structural_model=True` flag → uses GemPy under the hood
- Input: surface points + orientations from well markers
- Output: 3D volumetric geological model

### Constitutional Constraint
ML outputs must carry:
- `model_name`, `model_version`, `training_dataset`
- `input_hash` — SHA of the data fed to the model
- `confidence` — per-pick or per-interpretation confidence
- `uncertainty_reasoning` — why the model is confident/uncertain

---

## Phase 3 — Thermodynamics + Geochemistry

### Goal
Make feasibility checks honest. Add geochemical reasoning.

### Dependencies
- `burnman` ≥ 1.0 — mineral thermodynamics, seismic velocity prediction
- `pyrolite` ≥ 0.5 — geochemical plotting, compositional transforms

### New Files
```
src/geox_core/engines/thermodynamics/burnman_adapter.py
src/geox_core/engines/geochemistry/pyrolite_adapter.py
```

### Tool Enhancements
#### `geox_prospect_evaluate` → Thermodynamic Feasibility
- BurnMan validates PT conditions against known Earth models (PREM)
- Mineral stability check — is the claimed reservoir mineralogy physically possible?
- Real PT path integration (not hardcoded POS=0.22)

#### `geox_evidence_reason` → Geochemical Reasoning
- Pyrolite spider diagrams for fluid typing
- Provenance analysis from geochemical fingerprints

---

## Phase 4 — Advanced Seismic + Structural

### Goal
Deepen seismology and 3D modeling capabilities.

### Dependencies
- `pyrocko` — crustal tomography, receiver functions, ambient noise
- `loopstructural` — alternative implicit 3D modeling with fault kinematics

### Notes
- Use selectively. Pyrocko for crustal work. LoopStructural only if GemPy proves insufficient for fault kinematics.
- Do NOT create new top-level tools. These are engine-only additions.

---

## Cross-Cutting Rules

### Dependency Management
```toml
# pyproject.toml — sovereign pinning
obspy = ">=1.4.0,<2.0.0"
seisbench = ">=0.4.0,<1.0.0"
gempy = ">=2.0.0,<3.0.0"
burnman = ">=1.0.0,<2.0.0"
petrolib = ">=2.0.0,<3.0.0"
geoh5py = ">=0.10.0,<1.0.0"
pyrolite = ">=0.5.0,<1.0.0"
```

### Docker Layer
```dockerfile
# Optional extras tag — keeps core light
RUN pip install "geox[seismic]"   # ObsPy + SeisBench
RUN pip install "geox[petrophysics]"  # Petrolib + geoh5py
RUN pip install "geox[modeling]"   # GemPy + LoopStructural + BurnMan
RUN pip install "geox[full]"      # All of the above
```

### Constitutional Checkpoints
| Action | Trigger | Required |
|--------|---------|---------|
| New library addition | `pip install` any new dep | 888_JUDGE |
| ML model integration | SeisBench or any trained model | 888_JUDGE + F9 Anti-Hantu |
| Prospect verdict with real POS | `geox_prospect_evaluate` with computed POS | 888_JUDGE + F1 Ack |
| Drilling-relevant output | Any output that could influence drilling decision | 888_JUDGE |

### Test Requirements
- Unit tests for each adapter (obspy_adapter, seisbench_adapter, etc.)
- Golden dataset tests: real SEG-Y sample + known expected output
- Contradiction scan: C1-C12 checks against library output
- `geox_system_registry_status` → reports library versions loaded

---

## Status: ACTIVE DEVELOPMENT
> Ω₀ = 0.04 | Next action: Execute Phase 0 — forge `obspy_adapter.py`
