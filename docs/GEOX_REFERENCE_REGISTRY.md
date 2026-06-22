# GEOX Reference Registry — External Tools, Libraries & Codebases

> **DITEMPA BUKAN DIBERI** — Earth evidence is forged, not given.
> 
> When GEOX cannot compute from first principles, it references.
> When GEOX references, it attributes. When it attributes, it does not fabricate.
>
> This registry tracks every external tool, library, API, and codebase
> that GEOX depends on, references, or monitors. It is the canonical
> source of truth for the GEOX dependency graph.

**Last updated:** 2026-06-22  
**Registry keeper:** FORGE (A-FORGE organ, arifOS federation)  
**GEOX contract epoch:** `2026-06-22-GEOX-56TOOLS-v3.0`  
**Acknowledgement:** This work sits on the shoulders of Shanan Peters' Macrostrat lab at UW-Madison and the broader open geoscience ecosystem. On, Wisconsin. 🦡

---

## Tier 1 — Canonical Runtime Dependencies (installed in GEOX venv)

These are libraries GEOX directly imports in production tool code. They must be installable via `uv sync --frozen` and pinned in `pyproject.toml`.

| Library | Version | Language | License | GEOX Role | Imported By | Status |
|---|---|---|---|---|---|---|
| **fastmcp** | 3.4.2 | Python | MIT | MCP server framework — all tool mounting | `server.py`, all tools | ✅ INSTALLED |
| **pydantic** | 2.13.4 | Python | MIT | Schema enforcement for all tool contracts | All schemas | ✅ INSTALLED |
| **numpy** | 2.4.6 | Python | BSD-3 | Core array math | petrophysics, seismic, prospect | ✅ INSTALLED |
| **scipy** | 1.17.1 | Python | BSD-3 | Signal processing, interpolation | seismic, stratigraphy | ✅ INSTALLED |
| **lasio** | 0.32 | Python | MIT | LAS well log I/O | `well_ingest.py`, `data_ingest.py` | ✅ INSTALLED |
| **welly** | 0.5.2 | Python | MIT | Well object model, tops, deviation | `well_ingest.py` | ✅ INSTALLED |
| **striplog** | 0.9.2 | Python | MIT | Strip log / lithology column rendering | `well_correlation.py`, `section.py` | ✅ INSTALLED |
| **segyio** | 1.9.14 | Python | LGPL-3 | SEG-Y seismic volume I/O | `seismic_ingest.py`, `seismic_compute.py` | ✅ INSTALLED |
| **matplotlib** | 3.10.8 | Python | PSF | Plotting — well panels, cross-sections | `well_correlation.py`, `section.py` | ✅ INSTALLED |
| **cartopy** | 0.25.0 | Python | LGPL-3 | Map projection, basin context rendering | `map_context_scene.py` | ✅ INSTALLED |
| **scikit-learn** | 1.9.0 | Python | BSD-3 | Spatial block CV, FJIS feature analysis | `evidence_reason.py`, `qc.py` | ✅ INSTALLED |
| **statsmodels** | 0.14.6 | Python | BSD-3 | Statistical power, regression | `prospect_evaluate.py` | ✅ INSTALLED |
| **pyproj** | 3.7.2 | Python | MIT | Coordinate transforms, CRS management | `coord_transform.py`, `ingest.py` | ✅ INSTALLED |
| **pillow** | 12.2.0 | Python | HPND | Image export for correlation panels | `well_correlation.py` | ✅ INSTALLED |
| **openpyxl** | 3.1.5 | Python | MIT | XLSX export for project workflows | `sequence_interpret.py` | ✅ INSTALLED |
| **httpx** | 0.28.1 | Python | BSD-3 | Async HTTP for external APIs | `macrostrat_client.py` | ✅ INSTALLED |
| **pandas** | 3.0.2 | Python | BSD-3 | DataFrames for CSV/data ingestion | `data_ingest.py`, `data_loaders.py` | ✅ INSTALLED |
| **pysoplot** | 0.0.2 | Python | GPL-3 | Geochronology math — concordia, isochron, U-Pb, disequilibrium ages | `tools/geochronology/` (planned) | ✅ INSTALLED |
| **Pyleoclim** | 1.3.0 | Python | GPL-3 | Age-uncertain time series — binning, spectral analysis, correlation | `deep_time_state.py` context enrichment | ✅ INSTALLED |
| **pyrolite** | 0.3.7 | Python | LGPL-3 | Timescale age lookups, geochemical plotting | `deep_time_state.py` age resolution | ✅ INSTALLED |

---

## Tier 2 — External API Services (GEOX calls live)

These are web APIs that GEOX queries at runtime. All are read-only (OBSERVE only, no mutations).

| API | Endpoint Base | License | GEOX Role | Used By | Status |
|---|---|---|---|---|---|
| **Macrostrat** | `https://macrostrat.org/api/v2` | CC-BY 4.0 | Regional stratigraphy, lithology, intervals, fossils, geologic maps | `macrostrat_client.py` → `basin_profile.py` | ✅ LIVE |
| **Macrostrat GPTS Chrons** | `https://macrostrat.org/api/v2/defs/intervals?timescale_id=22` | CC-BY 4.0 | 101 geomagnetic polarity chrons (C1–M44, 0–170.76 Ma) | **Frozen CSV** → `data_loaders.py` | ✅ INGESTED |
| **Macrostrat GPTS Subchrons** | `https://macrostrat.org/api/v2/defs/intervals?timescale_id=23` | CC-BY 4.0 | 372 named subchrons (Brunhes, Matuyama, Jaramillo, etc.) | **Frozen CSV** → `data_loaders.py` | ✅ INGESTED |
| **ICS Chart v2024/12** | Embedded in `ics_chart.py` | CC-BY 4.0 | Stratigraphic chart — 100+ named units with GSSP boundaries | `age_resolver.py` | ✅ EMBEDDED |
| **Macrostrat Map** | `https://macrostrat.org/api/v2/geologic_units/map` | CC-BY 4.0 | 2.5M-scale geologic map polygons | `basin_profile.py` | ✅ LIVE |
| **PBDB** | via Macrostrat proxy | CC-BY 4.0 | Fossil occurrence data | `basin_profile.py` (macrostrat_fossils) | ✅ LIVE |

---

## Tier 3 — GEOX Internal Tools (the bridge)

These are the GEOX-native tools that connect time, correlation, and deep-time context internally. No external dependencies — pure GEOX code.

| Tool | File | Lines | Role |
|---|---|---|---|
| `geox_deep_time_state` | `deep_time_state.py` | 204 | Earth State Vector — GPTS, CO₂, temperature, sea level, paleogeography, 15+ variables |
| `geox_well_correlation_panel` | `well_correlation.py` | 393 | Multi-well correlation panel with striplog rendering |
| `geox_sequence_interpret` | `sequence_unified.py` | ~600+ | L1-L3 sequence stratigraphy pipeline (GR bins → packages → sequence) |
| `geox_basin_profile` | `basin.py` | ~400 | Basin-level intelligence with Macrostrat integration |
| `geox_data_ingest_bundle` | `data_ingest.py` | ~300 | LAS/CSV/SEG-Y ingestion pipeline |
| `geox_data_qc_bundle` | `qc.py` | ~250 | Depth monotonicity, null %, physical range QC |
| `geox_seismic_compute` | `seismic_compute.py` | ~500 | Forward model, well tie, anomalous contrast, attribute |
| `geox_evidence_reason` | `evidence_reason.py` | ~350 | Cross-domain synthesis, abduction, contradiction |
| `geox_prospect_evaluate` | `prospect_evaluate.py` | ~300 | Volumetrics, POS, EVOI with preview/seal |

---

## Tier 4 — Methodological References (shape architecture, not imported)

These are papers, repos, and codebases that inform GEOX's design but are not direct dependencies.

### Stratigraphic Correlation

| Reference | Type | Why GEOX References It | GEOX Bridge |
|---|---|---|---|
| **DTW automated correlation** (EarthArXiv) | Paper | DTW warp path for log alignment across wells | Future `geox_correlation_automated(mode="dtw")` |
| **SegNet well log segmentation** (SPWLA 2023) | Paper | Semantic segmentation of log curves for zone detection | Future ML correlation module |
| **BiLSTM/CNN zonation** (SPE 2022) | Paper | ~3m MAE on zone tops, 90% zone accuracy | Training target for automated picker |
| **Attention-based well correlation** (Geophysics 2024) | Paper | ~96% boundary detection with Hungarian matching | Cross-well feature matching architecture |
| **WLFM (Well Log Foundation Model)** | GitHub | Stratigraphy-aware embeddings, cross-well generalization | Future foundation backbone |
| **StratoBayes** (R, no Python port) | R package | Bayesian stratigraphic correlation with uncertainty | Conceptual reference for GEOX Bayesian layer |
| **pyCoreRelator** | GitHub | Python pairwise stratigraphic correlation | Evaluation candidate for DTW mode |

### Geochronology & Deep Time

| Reference | Type | Why GEOX References It | GEOX Bridge |
|---|---|---|---|
| **IsoplotR** | R package | Isoplot replacement for concordia/U-Pb | Conceptual reference; pysoplot is Python alternative |
| **pychron** | Python | Ar-Ar geochronology & noble gas workflows | Future specialized module if Ar-Ar enters GEOX |
| **detritalPy** | Python | Detrital age distributions, MDA plots, MDS | Future `geox_subsurface_generate_candidates(mode="detrital")` |
| **deeptime** (R) | R package | Geological time visualization | Conceptual reference for GEOX timeline UI |
| **Chron.jl** | Julia | Age spectra in stratigraphic context | Watchlist — Julia ecosystem |
| **Thermochron.jl** | Julia | Time-temperature inversion of thermochron data | Watchlist |

### Time Scale Visualization

| Reference | Type | Why GEOX References It | GEOX Bridge |
|---|---|---|---|
| **UW-Macrostrat/geo-timescale** | D3.js/TypeScript | Shanan Peters lab — interactive time scale component | GEOX cockpit timeline widget reference |
| **interactive-geological-timescale** | TypeScript | ICS chart browser UX pattern | GEOX cockpit age explorer reference |
| **TimeScale Creator** | Java desktop | Gold standard for time-scale dataset integration | Design reference for GEOX dataset composition |

### Plate Reconstruction & Paleogeography

| Reference | Type | Why GEOX References It | GEOX Bridge |
|---|---|---|---|
| **GPlates / PyGPlates** | C++/Python | Global plate motion, paleogeography through time | Future `geox_deep_time_state` paleogeography provider |
| **Merdith 2021** | Plate model | Full Phanerozoic plate model | PENDING_DATASETS registered (Phase 2) |
| **Scotese PALEOMAP** | Plate model | Paleogeographic maps | Alternative paleogeography source |

---

## Tier 5 — Ecosystem Watchlist (not yet evaluated for GEOX)

| Library | Language | Domain | Interest | Notes |
|---|---|---|---|---|
| **GemPy** | Python | 3D structural geological modeling | Medium | Potential for structural-stratigraphic integration |
| **OpendTect** | C++/Python | Seismic interpretation platform | Low | Too heavy for GEOX runtime, but UI reference |
| **awesome-open-geoscience** | Meta | Curated index | High | Discovery tool for new references |
| **geotimecpts** | GMT | Geological time color encoding | Low | Consistent chronostrat colors, but GMT-specific |
| **xarray** | Python | N-dimensional labeled arrays | Medium | Potential backend for raster/volume data |
| **torch** | Python | Deep learning framework | Medium | Will be needed for WLFM/ML correlation deployment |

---

## GEOX Architecture — The Bridge Diagram

```
                            GOULD'S DEEP TIME
                         (Time's Arrow × Time's Cycle)
                                  │
                    ┌─────────────▼─────────────┐
                    │   geox_deep_time_state     │
                    │   GPTS · ICS · CO₂ · T ·  │
                    │   Sea Level · Paleogeog.  │
                    │   Polarity · Day Length   │
                    │   (15 variables, F2/F9)   │
                    └─────────────┬─────────────┘
                                  │ age constraint
                    ┌─────────────▼─────────────┐
     ┌──────────────┤  geox_well_correlation    ├──────────────┐
     │              └─────────────┬─────────────┘              │
     │                            │                            │
     ▼                            ▼                            ▼
┌──────────────┐          ┌──────────────┐          ┌──────────────────┐
│ geox_well_   │          │ geox_sequence│          │ geox_basin_      │
│ ingest       │          │ _interpret   │          │ profile          │
│ (LAS/CSV)    │          │ (strat packs)│          │ (basin context)  │
└──────┬───────┘          └──────┬───────┘          └────────┬─────────┘
       │                        │                           │
       └────────────────────────┼───────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Temporalized        │
                    │   Stratigraphic       │
                    │   Interval            │
                    │   (bridge object)     │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   geox_prospect_      │
                    │   evaluate            │
                    │   Volumetrics · POS   │
                    │   · EVOI · Preview    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   WEALTH feed         │
                    │   (capital valuation) │
                    └───────────────────────┘
```

---

## Gould's Deep Time in GEOX Terms

Stephen Jay Gould's framework is not philosophy here — it is **architecture**:

| Gould Dimension | GEOX Implementation | Tool |
|---|---|---|
| **Time's Arrow** (irreversible sequence) | Stratigraphic correlation — tops, zones, well-to-well stacking order | `well_correlation.py`, `sequence_interpret.py` |
| **Time's Cycle** (recurrent Earth-state patterns) | Deep-time Earth state — polarity, CO₂, temperature, sea level, paleogeography | `deep_time_state.py`, `ics_chart.py`, `data_loaders.py` |
| **The Contingency Paradox** (history matters) | Every correlated interval keeps its epistemic tag — no collapsing of uncertainty | All tools via `EarthStateEnvelope` with governance footer |
| **Deep Time as Refusal of Narrative Convenience** | F9 ANTI-HANTU — never fabricate age/polarity/temperature for intervals that cannot be known | `_is_unknown_at_age()` in `data_loaders.py` |

The bridge object is the **Temporalized Stratigraphic Interval**:

```
{
  "well_id": "A-12",
  "interval_top_md_m": 2143.5,
  "interval_base_md_m": 2189.0,
  "correlation_id": "corr_seq_17",
  "age_hypothesis_ma": {"min": 83.2, "mode": 84.1, "max": 85.0},
  "time_scale_unit": "Santonian",
  "magnetic_polarity": "C34n",
  "earth_state": {
    "co2_ppm": 900,
    "temp_anomaly_c": 6.5,
    "sea_level_m": 120
  },
  "epistemic_tag": "INTERPRETED_LOCAL",
  "confidence": 0.71
}
```

This is not a "nice to have." This is what makes correlation physically meaningful — converting pattern matching into chronostratigraphic hypothesis with known Earth constraints.

---

## Macrostrat Acknowledgements

GEOX builds directly on Macrostrat (Shanan Peters lab, UW-Madison). Specifically:

1. **Macrostrat API** (`macrostrat.org/api/v2`) — base for `basin_profile.py`, `data_ingest.py`
2. **Macrostrat GPTS tables** (timescale_id=22, 23) — frozen as `data/gp_ts_chrons.csv` and `data/gp_ts_subchrons.csv`
3. **UW-Macrostrat/geo-timescale** — interaction reference for GEOX cockpit timeline

Macrostrat data is CC-BY 4.0. All GEOX outputs using Macrostrat data carry attribution in their governance footer.

**On, Wisconsin.** 🦡

---

*Registry version: v1.0 | Last updated: 2026-06-22 | 5 tiers, 30+ entries mapped*
*DITEMPA BUKAN DIBERI — The forge compiles reality, it does not invent it.*
