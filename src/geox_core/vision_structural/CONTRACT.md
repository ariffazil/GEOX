# FROZEN INTERFACE CONTRACT — GEOX Deterministic Structural Vision Layer
> Version: v1.0 · Frozen 2026-09-18 · Owner: Hermes (curator) · Authority: F13 Arif
> **NO AGENT MAY EDIT THIS FILE.** Build to it. If it is wrong, report it — do not silently deviate.

## 0. Why this layer exists

An LLM must never read spatial metrics off a picture. Language models hallucinate geometry.
The agent calls a Tool; the Tool runs deterministic CV; the Tool returns **numbers with
coverage and uncertainty**. The agent may only reason over returned numbers.

**Hard prohibition:** no function in this layer may return a probability, confidence, or
`P(truth)` it invented. Emit *measurement* quantities (n_samples, coverage, residuals,
uncertainty bounds). F7 HUMILITY caps any downstream confidence at 0.90.

## 1. Probe results (env truth — build to THESE, not to assumptions)

| Package | Status |
|---|---|
| numpy 2.4.3 | present |
| scipy 1.18.0 | present |
| scikit-image 0.26.0 | present → **use this as the CV engine** |
| segyio | present |
| fastmcp 3.4.6 | present |
| **cv2 (OpenCV)** | **ABSENT — do not import** |
| **torch** | **ABSENT — do not import** |
| **dtw lib** | **ABSENT — implement DTW in numpy** |

Existing surfaces that MUST be respected:
- `src/geox_mcp/servers/vision.py` — the VLM lane (MiniMax). It is a *perception* lane capped at 0.90.
  **It is NOT the structural-metric lane.** Do not extend it for spatial metrics; build alongside it.
- `src/geox_mcp/tools/_register.py` — canonical registration + floor enforcement + evidence envelope.
- `src/geox_mcp/tools/structure_gates/tectonic_regime.py` — the K-REGIME falsification engine
  (7 regimes, 27 passing tests). **Reuse it. Do not reimplement it.**
- `src/geox_mcp/tools/structural_restoration/wiring.py` — restoration tools, status PLANNED, unwired.

## 2. Package layout (new files only — disjoint ownership)

```
src/geox_core/vision_structural/__init__.py
src/geox_core/vision_structural/types.py          # dataclasses, enums, Measurement
src/geox_core/vision_structural/structure_tensor.py   # Axis A
src/geox_core/vision_structural/isopach.py            # Axis B
src/geox_core/vision_structural/orientation.py        # Axis C
src/geox_core/vision_structural/terminations.py       # Axis D
src/geox_core/vision_structural/calibration.py        # VE / time-depth correction helpers
```

## 3. The Measurement envelope — EVERY extractor returns this

```python
from dataclasses import dataclass, field
from typing import Any, Literal

ExtractionStatus = Literal["MEASURED", "PARTIAL", "UNMEASURED"]

@dataclass(frozen=True)
class Measurement:
    """One measured quantity. Never a probability. Never a verdict."""
    value: float | None              # None iff status == UNMEASURED
    unit: str                        # "deg" | "m" | "ratio" | "count" | "deg_azimuth"
    status: ExtractionStatus
    n_samples: int = 0               # how many samples produced this number
    coverage: float | None = None    # 0..1 fraction of the horizon with VALID input
    method: str = ""                 # the algorithm actually run, named
    uncertainty: dict[str, Any] = field(default_factory=dict)  # window, residuals, bounds
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status == "MEASURED" and self.value is None:
            raise ValueError("MEASURED requires a value")
        if self.status == "UNMEASURED" and self.value is not None:
            raise ValueError("UNMEASURED must not carry a value")
        if self.status == "MEASURED" and self.coverage is None:
            raise ValueError("MEASURED requires coverage — confidence without coverage is invalid")
```

**Rule:** `status == "UNMEASURED"` is never upgraded in transit. Downstream must treat
UNMEASURED as *not tested*, never as PASS and never as KILL.

## 4. Function signatures — FROZEN

### Axis A — Shape (`structure_tensor.py`)

```python
def compute_dip_field(
    section: np.ndarray,            # 2-D float array, shape (n_samples_z, n_traces)
    *, dz_m: float, dx_m: float, ve: float = 1.0, sigma: float = 1.0,
) -> dict[str, Measurement]:
    """Structure-tensor dip/azimuth field over the whole section.

    Returns keys: "dip_deg", "dip_azimuth_deg", "curvature".
    MUST apply the VE correction: tan(theta_true) = tan(theta_apparent) / ve.
    """

def extract_axis_a(
    section: np.ndarray,
    horizon_mask: np.ndarray,       # bool, same shape; True where the horizon is picked
    *, dz_m: float, dx_m: float, ve: float = 1.0,
) -> dict[str, Measurement]:
    """Per-horizon shape metrics: dip_deg_mean, dip_deg_p95, curvature_mean,
    dip_azimuth_deg, plus a Measurement for geometry_class_fired (value None/1).

    `geometry_class` is NOT free text. It may be emitted ONLY by a declared rule
    (planar / listric / kinked) with the rule named in `Measurement.method`, and only
    when its decision inputs are MEASURED. Otherwise status=UNMEASURED and value=None.
    "listric" is an INTERPRETATION — never a raw CV output.
    """
```

### Axis B — Differential (`isopach.py`)

```python
def dtw_align_traces(
    a: np.ndarray, b: np.ndarray, *, band: int | None = None,
) -> dict[str, Any]:
    """Numpy DTW. Returns {"path": int ndarray (n,2), "distance": float,
    "warp_stretch_profile": float ndarray, "band": int}.

    NOTE: DTW measures RELATIVE WARPING between two traces. It does NOT measure
    thickness. Thickness needs horizon picks on both traces. Do not conflate them.
    """

def compute_isopach(
    top_mask: np.ndarray, bot_mask: np.ndarray, *, dz_m: float,
) -> dict[str, Measurement]:
    """Per-trace thickness from two picked horizons. Keys: "thickness_m", "coverage".
    Returns UNMEASURED where either pick is absent — never interpolate silently over a gap
    without recording it in `Measurement.notes` and lowering `coverage`.
    """

def expansion_index(
    thickness_hangingwall: np.ndarray, thickness_footwall: np.ndarray,
) -> dict[str, Measurement]:
    """EI = hw/fw per trace, then reduced. Keys: "expansion_index", "n_pairs".
    If either array has no valid entries -> UNMEASURED (NOT 1.0, NOT 0.0).
    **Absence of a growth wedge does not kill extension** — see CONTRACT §7.
    """

def isopach_differential(
    thickness_map: np.ndarray, *, structure_axis: int = 1,
) -> dict[str, Measurement]:
    """The tectonic test: does the SAME interval change thickness ACROSS the structure?
    Keys: "differential_ratio" (across-structure spread / along-structure spread).
    value ~1.0 => uniform => favours eustatic/supply (the NULL hypothesis).
    """
```

### Axis C — Orientation (`orientation.py`)

```python
def extract_fault_azimuths(
    fault_polylines: list[np.ndarray], *, x_origin_m: float = 0.0, y_origin_m: float = 0.0,
) -> dict[str, Measurement]:
    """Azimuth of each polyline's end-to-end chord. Keys: "azimuth_deg" (circular mean),
    "azimuth_rosenbusch" (list), "n_polylines".

    Azimuth is CIRCULAR. Never average azimuths linearly — use a circular mean
    (atan2 of the summed unit vectors). Linear averaging of 350 deg and 10 deg gives
    180 deg, which is 170 deg wrong.
    """

def azimuth_population_stats(
    azimuths: np.ndarray,
) -> dict[str, Measurement]:
    """Keys: "circular_mean_deg", "circular_std_deg", "r_vector_length" (0..1, how
    concentrated), "n". r_vector_length near 0 => no preferred orientation; say so.
    """

def conjugate_pair_test(
    azimuths: np.ndarray,
) -> dict[str, Any]:
    """Detect a conjugate pair. Retained ONLY as observation.
    The acute bisector IS sigma1 (Anderson) — but this function does NOT emit sigma1.
    It emits {"pair_detected": bool, "bisector_acute_deg": float|None,
    "dihedral_acute_deg": float|None, "evidence": str}. Emitting a stress axis is
    arifOS's job, and only with fault-slip data (CONTRACT §7, K-REGIME-CEILING).
    """
```

### Axis D — Superposition (`terminations.py`)

```python
def detect_terminations(
    section: np.ndarray, *, do_smoothing: bool = True, method: str = "sobel",
) -> dict[str, Any]:
    """Edge detection + contour logic. Returns {"onlap_contacts": list[tuple[float,float]],
    "truncation_contacts": list, "n_candidates", "method": str}.
    These are CANDIDATE contacts. Interface with `horizon_mask` to decide onlap vs truncation
    (onlap = younger beds terminate against an older surface; truncation = older beds are cut).
    A bare gradient edge is NOT a termination.
    """

def build_cross_cutting_table(
    terminations: dict[str, Any], horizons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Relative chronology: a feature is younger than the youngest horizon it offsets,
    older than the oldest that drapes it. Returns {"relations": list[dict], "n": int}.
    NOTE this is the CROSS-CUTTING principle (Steno 1669 / Hutton 1795 / Lyell 1830),
    explicitly NOT Walther's Law (which governs conformable facies succession).
    """
```

### Calibration (`calibration.py`)

```python
def apply_ve_correction(dip_apparent_deg: float, ve: float) -> float:
    """tan(theta_true) = tan(theta_apparent) / ve. Returns degrees."""

def time_to_depth(twt_ms: float, interval_velocity_m_s: float) -> float:
    """Returns depth in metres. Raises ValueError on non-positive velocity."""

def declare_calibration_state(
    *, vertical_exaggeration: float | None, velocity_model_present: bool,
    time_domain: bool,
) -> dict[str, Any]:
    """Returns {"dips_trustworthy": bool, "problems": list[str]}.
    dips_trustworthy is False unless ve == 1.0 (or corrected) AND (not time_domain or
    velocity_model_present). Mirrors K-REGIME-DISPLAY in tectonic_regime.py.
    """
```

## 5. Output bundle — what the MCP tool returns to the agent

```python
{
  "axes": {
    "A_shape":        {"dip_deg_mean": <Measurement.asdict()>, ...},
    "B_differential": {"expansion_index": {...}, "isopach_differential": {...}, ...},
    "C_orientation":  {"azimuth_deg": {...}, "population": {...}},
    "D_superposition":{"n_candidates": int, "relations": [...]},
  },
  "coverage": <float|None>,          # aggregate — MANDATORY alongside any number
  "calibration_state": {...},        # from declare_calibration_state
  "decompaction_declared": <bool>,   # was decompaction applied before thickness?
  "method_receipt": {...},           # algorithms run, versions, parameters
  "status": "MEASURED" | "PARTIAL" | "UNMEASURED",
  "local_verdict": "QUALIFIED_CANDIDATE",
  "seal_authority": "arifOS_only",
  "preferred_hypothesis": None,      # ALWAYS None
}
```

**Forbidden in the bundle:** `confidence`, `reliability`, `P(truth)`, `score`, any
self-assigned probability. If a caller needs confidence it comes from coverage + n_samples
and is capped at 0.90 by F7.

## 6. Wiring the falsifier — reuse `tectonic_regime.run_regime_falsification`

The vision tool's job is to FILL the `framework` dict that `run_regime_falsification`
already consumes. Mapping:

| Vision output | framework key consumed by |
|---|---|
| `A_shape.dip_deg_p95` | `horizons[].geometry.dip_deg` → K-NULL-DIP (angle-of-repose), K-REGIME-DISPLAY |
| `B_differential.isopach_differential` | `intervals[].spatial_differential` → K-REGIME-DIFFERENTIAL |
| `B_differential.expansion_index` | `intervals[].expansion_index` / `growth.expansion_index` → K-EXT-GROWTH |
| `decompaction_declared` | `intervals[].decompacted` → K-REGIME-DECOMPACT |
| `C_orientation.azimuth_deg` | `faults[].strike_deg` (population only) |
| `D_superposition.relations` | `cross_cutting[]` → K-REGIME-XCUT |
| `calibration_state.problems` | `display.*` → K-REGIME-DISPLAY |
| `coverage` | `horizons[].coverage_pct` → K-REGIME-COVERAGE |

**Do NOT create a second falsifier engine.** One engine, one authority.

## 7. Doctrine that MUST be preserved through the wire (these are the bugs to avoid)

1. **`EI <= 1 → FALSIFIED` is WRONG when EI was never measured.**
   A fault moving slower than the sedimentation rate leaves **no** growth signature at all.
   Correct: EI missing → `UNMEASURED`. EI measured and ≤ 1 → `KILL` **scoped to the
   interval/syn-tectonic timing claim**, not to extension itself.

2. **`Kinematic_Reliability: 0.95` is a fabricated probability.** A CV algorithm cannot
   emit P(truth). Emit coverage + n_samples + uncertainty. F7 caps at 0.90.

3. **"listric" is not a CV output.** Dip and curvature are measurable; the *classification*
   needs a declared, named rule. No rule fired → `UNMEASURED`, value None.

4. **Non-balance during restoration is a DIAGNOSTIC, not an error flag.**
   Failure to restore without gaps/overlaps means a structure is missing from the section
   (blind fault, layer-parallel shear, out-of-plane flow), or the section is oblique to
   transport. It does **not** mean the input picks were wrong. Never instruct an
   interpreter otherwise: picks bent until they balance destroy a correct interpretation.

5. **Decompact before any thickness argument.** "Constant thickness" means constant in
   *time*, not in *depth*. Compaction thins parallel beds with zero tectonics, and an
   un-decompacted differential gets priced as growth.

6. **DTW gives warp, not thickness.** Thickness needs horizon picks on both traces.

7. **Azimuths are circular.** Circular mean only. State `r_vector_length` — near zero
   means no preferred orientation.

8. **One horizon records only the last event.** History lives in per-interval isopach
   differential + cross-cutting relations. Do not let a single-horizon call become a
   tectonic story.

9. **Geometry yields KINEMATICS, not stress.** A stress tensor from geometry alone is a
   category error → `K-REGIME-CEILING` KILLs it. Restoration yields strain. Only
   fault-slip inversion yields (4 of 6) paleostress parameters.

10. **The null hypothesis is mandatory.** Every bundle must falsify `null_depositional`
    (depositional/eustatic/compaction control) alongside the tectonic candidates.

## 8. Anti-collision protocol (mandatory for every agent)

Parallel agents and CLI sessions overwrite shared dirs mid-task. Therefore:
- **Create only the files listed in your brief.** No other file may be created or modified.
- Never edit `CONTRACT.md`, `tectonic_regime.py`, `_register.py`, `servers/vision.py`, or
  any file outside your brief.
- Before finishing, run your own tests and paste **real** command output.
- A claim without pasted tool output is not a deliverable.

DITEMPA BUKAN DIBERI ⚒️
