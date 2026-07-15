<!-- AAA ACTION CARDS — GEOX Adapter Integration Phase 2
     Drafted: 2026-06-27 by FORGE (Architect lane)
     Status: 888_HOLD — awaiting Arif review in AAA cockpit
     Constitutional basis: AGENTS.md §10, F1-F13, 888_HOLD gate
-->

# AAA Action Cards — GEOX Adapter Integration (Phase 2)

> **Status:** DRAFT — 888_HOLD required before any execution.
> **Sequence:** 001 → 002 → 003, then pause for AAA review before remaining four.
> **Author:** FORGE (Architect lane, not executor)
> **Date:** 2026-06-27

---

## AAA-GEOX-ADAPT-001: Biharmonic Inpainting for Sparse Borehole Data

| Field | Value |
|-------|-------|
| **Card ID** | `AAA-GEOX-ADAPT-001` |
| **Title** | Biharmonic categorical inpainting for 2D geological cross-sections from sparse boreholes |
| **Purpose** | GEOX has no capability to reconstruct continuous 2D geological cross-sections from irregularly-spaced categorical borehole data (lithology classes). This fills the spatial interpolation gap between `geox_sequence` (stratigraphic correlation) and `geox_subsurface_model` (3D geophysics). |
| **Library** | `scikit-image` (already in GEOX deps via `pillow` chain). Algorithm: `skimage.restoration.inpaint_biharmonic`. Cherry-pick from [mariosgeo/Geology](https://github.com/mariosgeo/Geology) `gridder.py` (~150 lines core logic). No new dependency required. |
| **Inputs** | Borehole XY positions, depth-coded lithology integer classes, grid resolution (dx, dy), anisotropy weights (x_weight, y_weight for directional geological fabric). |
| **Outputs** | 2D grid of interpolated lithology classes + confidence map (distance-from-nearest-borehole decay). Epistemic label: `DERIVED` → `INTERPRETED_LOCAL`. |
| **Floors touched** | **F1** (reversibility — pure computation, no side effects), **F2** (truth — output is interpolated, not observed; must label uncertainty), **F4** (clarity — grid output must be self-documenting), **F7** (humility — confidence decays with distance from control points), **F9** (anti-hantu — algorithm does not "know" geology, it interpolates), **F11** (audit — params hash + input hash for reproducibility). |
| **Epistemic level** | `DERIVED` for grid cells near boreholes. `INTERPRETED_LOCAL` for cells far from control. Never `OBSERVED`. |
| **ACRisk** | **12/100** (LOW). Pure computation. No external calls. No data mutation. No new dependency. Reversible by construction. |
| **Reversibility** | **Full** — output is a new artifact, does not modify input data. |
| **Registry impact** | New file: `src/geox_core/engines/modeling/biharmonic_adapter.py`. New mode on existing MCP tool: `geox_sequence(workflow='biharmonic_inpaint')` OR new tool: `geox_model_inpaint`. No new dependency in `pyproject.toml`. |
| **888 HOLD reason** | New MCP tool/mode = tool registry change. Even though no new dependency, the MCP surface expansion requires sovereign approval. |
| **Decision ask** | **Approve** (add adapter + wire to MCP) / **Defer** (backlog) / **Split** (adapter only, MCP wiring later) / **Reject** |

### Implementation sketch (for AAA visibility)

```python
# geox_core/engines/modeling/biharmonic_adapter.py
# ~150 lines. Uses only numpy + scipy + skimage (already in deps).

from skimage.restoration import inpaint_biharmonic
import numpy as np

def biharmonic_lithology_inpaint(
    borehole_xy: np.ndarray,      # (N, 2) — XY positions
    lithology_codes: np.ndarray,   # (N,) — integer lithology classes
    grid_shape: tuple = (100, 100),
    x_weight: float = 1.0,
    y_weight: float = 1.0,
) -> dict:
    """
    Inpaint categorical lithology onto a 2D grid using biharmonic PDE.
    
    Returns:
        - grid: 2D array of interpolated lithology codes
        - confidence: 2D array (0-1) — distance-decay from nearest borehole
        - epistemic_label: "DERIVED" | "INTERPRETED_LOCAL"
        - params_hash: sha256 of inputs for reproducibility
    """
    # 1. Create sparse grid with borehole values at grid positions
    # 2. Create binary mask (1 = unknown, 0 = known)
    # 3. Apply anisotropic weighting (stretch Y axis for geological fabric)
    # 4. Run inpaint_biharmonic per lithology class (one-vs-all)
    # 5. Assign class with highest inpainted value
    # 6. Compute confidence = exp(-distance_to_nearest_borehole / decay_length)
    ...
```

### Risk analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Interpolation artifacts far from boreholes | HIGH | MEDIUM | Confidence map flags low-control zones |
| Categorical classes not continuous → biharmonic assumption violated | MEDIUM | LOW | One-vs-all approach handles categorical data; documented caveat |
| User misinterprets interpolated grid as observed data | MEDIUM | HIGH | Epistemic label enforced: DERIVED/INTERPRETED_LOCAL, never OBSERVED |

---

## AAA-GEOX-ADAPT-002: Drillhole Desurvey and 3D Positioning

| Field | Value |
|-------|-------|
| **Card ID** | `AAA-GEOX-ADAPT-002` |
| **Title** | Drillhole desurvey — convert collar+survey+assay into 3D positioned data |
| **Purpose** | `geox_well_ingest` reads LAS files (pre-processed, depth-indexed). It cannot process raw collar+survey+assay data (the standard exploration industry format). Wrong 3D positioning contaminates the OBSERVED layer and everything downstream: petrophysics, sequence correlation, volumetrics. |
| **Library** | Pure numpy implementation (no new dependency). Desurvey algorithms are well-documented: minimum curvature method is industry standard. Reference: [drillholes](https://pypi.org/project/drillholes/) PyPI package for algorithm reference, but implementation is ~200 lines of numpy. |
| **Inputs** | Collar table (hole_id, X, Y, Z, max_depth), survey table (hole_id, depth, azimuth, dip), assay/lithology table (hole_id, from, to, value). |
| **Outputs** | 3D-positioned intervals (hole_id, X, Y, Z, from, to, value) + QC flags (depth gaps, survey interpolation warnings). Epistemic label: `DERIVED` (computed positions from survey data). |
| **Floors touched** | **F1** (reversibility — produces new artifact), **F2** (truth — 3D positions are computed, not observed; survey measurement error propagates), **F4** (clarity — output must include position uncertainty), **F7** (humility — desurvey accuracy depends on survey station density), **F9** (anti-hantu — algorithm doesn't "know" the drill path, it interpolates between survey stations), **F11** (audit — full provenance chain from collar→survey→desurveyed positions). |
| **Epistemic level** | `DERIVED` — 3D positions computed from survey measurements. Survey error (±0.5° dip, ±2° azimuth typical) propagates to position uncertainty that grows with depth. |
| **ACRisk** | **15/100** (LOW). Pure computation. No external calls. No new dependency. But: wrong desurvey = wrong positions = wrong geology everywhere downstream. Blast radius is high if misused. |
| **Reversibility** | **Full** — output is new artifact. Does not modify input collar/survey/assay tables. |
| **Registry impact** | New file: `src/geox_core/engines/well/desurvey_adapter.py`. New mode: `geox_well_ingest(load_format='collar_survey_assay')` or new tool: `geox_desurvey`. No new dependency. |
| **888 HOLD reason** | Tool registry change. Also: desurveyed positions become the OBSERVED foundation for all downstream GEOX computation — errors here cascade. |
| **Decision ask** | **Approve** / **Defer** / **Split** / **Reject** |

### Implementation sketch

```python
# geox_core/engines/well/desurvey_adapter.py
# ~200 lines. Uses only numpy.

def minimum_curvature_desurvey(
    collar: dict,      # {hole_id: (X, Y, Z, max_depth)}
    survey: dict,      # {hole_id: [(depth, azimuth, dip), ...]}
    intervals: dict,   # {hole_id: [(from, to, value), ...]}
) -> dict:
    """
    Industry-standard minimum curvature desurvey.
    
    Returns:
        - positioned_intervals: list of {hole_id, X, Y, Z, from, to, value}
        - position_uncertainty_m: estimated from survey station spacing
        - qc_flags: depth gaps, extrapolation warnings
        - epistemic_label: "DERIVED"
    """
    # 1. Interpolate survey stations to interval midpoints
    # 2. Apply minimum curvature method (dog-leg severity)
    # 3. Compute 3D positions
    # 4. Estimate position uncertainty from survey spacing
    # 5. Flag depth gaps and extrapolation zones
    ...
```

### Risk analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Wrong desurvey → wrong 3D positions for all downstream | MEDIUM | CRITICAL | QC flags on survey spacing; position uncertainty propagated |
| No survey data → straight vertical assumption | HIGH | MEDIUM | Explicit warning when survey is missing; default to vertical |
| Survey interpolation error at deep intervals | MEDIUM | MEDIUM | Uncertainty grows with depth; flag intervals beyond last survey station |

---

## AAA-GEOX-ADAPT-003: HuggingFace Governed Artifact Layer

| Field | Value |
|-------|-------|
| **Card ID** | `AAA-GEOX-ADAPT-003` |
| **Title** | Governed HuggingFace Hub integration — model/dataset supply chain under MCP |
| **Purpose** | GEOX has a point-to-point Prithvi adapter but no generic HF layer. Every new geo/EO model becomes a one-off adapter (repo entropy). A governed HF client provides: single entry point for pulling models/datasets, supply chain control (allowed orgs, revision pinning), and constitutional hooks (F2, F9, F11). |
| **Library** | `huggingface_hub` (thin client, ~2MB). No `transformers`/`torch` in core — those are loaded lazily by downstream adapters (Prithvi, future models). |
| **Inputs** | `repo_id` (e.g. `ibm-nasa-geospatial/Prithvi-EO-2.0`), `revision` (commit hash or tag), `task` (classification), `trust_level` (allowed orgs list), `cache_dir`. |
| **Outputs** | Local model/dataset path + metadata (card text, license, tags, revision hash) + governance verdict (ALLOWED/BLOCKED/UNKNOWN org). Epistemic label: `OBSERVED` (the artifact exists) + governance tag. |
| **Floors touched** | **F1** (reversibility — downloads to local cache, deletable), **F2** (truth — model card/license must be surfaced; no silent model swaps), **F4** (clarity — single registry, no duplicate roots), **F7** (humility — HF models are external artifacts, not GEOX truth), **F9** (anti-hantu — never assume model capability from name alone; read card), **F11** (audit — every pull logged with revision hash, org, license), **F13** (sovereign — allowed-orgs list is sovereign-configured). |
| **Epistemic level** | `OBSERVED` (artifact downloaded) + `GOVERNANCE_TAG` (allowed/blocked org). Model *outputs* are governed by downstream adapter (Prithvi, etc.), not this layer. |
| **ACRisk** | **35/100** (MEDIUM). External artifact ingestion. Can pull arbitrary weights/data from HF Hub. Blast radius: model behavior change if upstream revises. Mitigated by: revision pinning, allowed-orgs allowlist, license surfacing. |
| **Reversibility** | **Full** — downloads to local cache. Can delete cache. No production mutation. |
| **Registry impact** | New file: `src/geox_core/engines/ml/hf_adapter.py`. New dependency: `huggingface_hub>=0.20.0` in `pyproject.toml` [ml] optional group. New MCP tool: `geox_hf_pull` or mode on existing tool. Config: `geox_core/config/hf_allowed_orgs.json` (sovereign-configured allowlist). |
| **888 HOLD reason** | 1) New dependency in `pyproject.toml`. 2) New MCP tool surface. 3) External artifact ingestion = supply chain risk. 4) Allowed-orgs config is sovereign authority (F13). |
| **Decision ask** | **Approve** / **Defer** / **Split** (adapter only, MCP later) / **Reject** |

### Architecture

```
┌─────────────────────────────────────────────────┐
│  MCP Tool: geox_hf_pull                         │
│  (governed entry point)                         │
├─────────────────────────────────────────────────┤
│  hf_adapter.py                                  │
│  ┌───────────────┐  ┌──────────────────────┐   │
│  │ org_allowlist  │  │ revision_pin_check   │   │
│  │ (F13 config)   │  │ (F2 — no silent swap)│   │
│  └───────┬───────┘  └──────────┬───────────┘   │
│          │                     │                │
│  ┌───────▼─────────────────────▼───────────┐   │
│  │  huggingface_hub.snapshot_download()     │   │
│  │  + model card parsing                    │   │
│  │  + license extraction                    │   │
│  └───────────────────┬─────────────────────┘   │
│                      │                          │
│  ┌───────────────────▼─────────────────────┐   │
│  │  Return: local_path + metadata + verdict │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │
         ▼ (consumed by downstream adapters)
┌─────────────────┐  ┌──────────────────┐
│ prithvi_adapter  │  │ future_adapters  │
│ (EO inference)   │  │ (new geo models) │
└─────────────────┘  └──────────────────┘
```

### Allowed-orgs config (sovereign)

```json
// geox_core/config/hf_allowed_orgs.json
// F13: Only Arif can modify this file.
{
  "allowed_orgs": [
    "ibm-nasa-geospatial",
    "NASA-IMPACT",
    "microsoft",
    "facebook",
    "openai"
  ],
  "blocked_orgs": [],
  "require_license": true,
  "require_model_card": true,
  "pin_revision": true
}
```

### Risk analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Upstream model revision changes behavior silently | MEDIUM | HIGH | Revision pinning enforced; card diff on re-pull |
| Pull from untrusted org | LOW | CRITICAL | Allowed-orgs allowlist; blocked at adapter level |
| License violation | LOW | HIGH | License surfaced in output; `require_license` flag |
| Cache bloat | MEDIUM | LOW | TTL + manual cache clear |
| `huggingface_hub` dependency conflict | LOW | MEDIUM | Thin client, minimal deps; tested against GEOX env |

---

## Summary — Decision Matrix

| Card | Blast Radius | New Deps | Registry Change | ACRisk | Recommendation |
|------|-------------|----------|-----------------|--------|---------------|
| **001** Biharmonic | Low | None | New file + MCP mode | 12 | **Approve** — cleanest, lowest risk |
| **002** Desurvey | Medium | None | New file + MCP mode | 15 | **Approve** — critical data quality fix |
| **003** HF Layer | High | `huggingface_hub` | New file + dep + MCP tool | 35 | **Split** — adapter first, MCP wiring after AAA review |

**Sequence:** 001 → 002 → 003 (split) → **PAUSE** → AAA cockpit review → remaining four cards (GemGIS, StratAge, hylite, GLiM).

---

*Drafted by FORGE in Architect lane. Not executed. Awaiting 888 in AAA cockpit.*
*DITEMPA BUKAN DIBERI*
