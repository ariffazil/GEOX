# EUREKA INSIGHTS — Kinabalu KL2 Time-Depth Survey (2026-06-03)

**Author:** OMEGA (Ω) Forge Agent
**Source:** Copilot external analysis of `TZ KL2.xlsx` (8 wells, Kinabalu Basin, offshore Sabah)
**Status:** Distilled — for forge routing into GEOX eurekas
**Real-data eureka insights, no new MCP tool surface required**

---

## 1. THE DATASET (canonical reference)

| Well | Type | Deviated? | Headers | Notes |
|---|---|---|---|---|
| BARTON-2 | measured | no (X=Y=0) | 2-row header | Vertical well |
| ROTAN-1 | measured | near-vertical | 2-row header | Vertical well |
| BUNGA LILI-1 | measured | **YES (X,Y nonzero)** | none | Deviated — Eureka 6 trigger |
| BULUH-1 | **SYNTHETIC** | no | none + "SYNTHETIC" label in row 0 | Pseudo-checkshot — Eureka 2 trigger |
| MALIGAN-1 | measured | near-vertical | none | |
| PEKAKA-1 | measured | near-vertical | none | |
| SUGUT-1ST1 | measured | near-vertical | none | |
| SOLISIP-1 | measured | near-vertical | none | |

Three distinct Excel formats observed:
- BARTON-2 / ROTAN-1 → 2 header rows, data from row 2
- BUNGA LILI-1 / BULUH-1 / MALIGAN-1 / PEKAKA-1 / SUGUT / SOLISIP-1 → no headers, data from row 0
- BULUH-1 has 10 columns; col 8 and col 9 contain "SYNTHETIC" label in row 0

**V_avg typical range:** 1800–3500 m/s (Malay Basin carbonates + clastics)
**V_int range:** 1500–5000 m/s expected, all within CANON-9 [1500, 6000]
**Depths:** ~2000–4000 m TVDSS
**TWT:** ~1500–3500 ms

---

## 2. THE 8 EUREKA INSIGHTS (distilled)

### Insight 1 — Quality flagging must auto-detect "SYNTHETIC" labels
**Observation:** BULUH-1's row 0 has the literal text "SYNTHETIC" in column 8. A human can spot it. GEOX's `legacy_ingest.quality_tagger` (Eureka 2) MUST auto-detect this.

**Forge action:** Add `legacy_ingest/quality_tagger.py::auto_detect_synthetic()` — scans row 0 of every column for the tokens `["SYNTHETIC", "PSEUDO", "TENTATIVE", "INFERRED"]`. Returns a list of (column_idx, token) hits → downgrade `confidence_score` to 0.5, set `tentative: true` in artifact metadata.

### Insight 2 — Three Excel formats require a single parser
**Observation:** 8 wells, 3 header conventions. The Copilot's `pd.read_excel(header=None)` + manual `skiprows` was the right call. GEOX needs the same.

**Forge action:** `legacy_ingest/excel_parser.py` — accepts a list of candidate `header_rows=[0, 1, 2]`, picks the one where every numeric column has ≥80% numeric values. For BARTON-2/ROTAN-1 → `header_rows=2`; for the rest → `header_rows=0`.

### Insight 3 — Deviated well (BUNGA LILI-1) needs ray-traced TWT correction
**Observation:** `h_off = sqrt(X² + Y²)` is nonzero for BUNGA LILI-1. A straight-line vertical-projection correction leaves up to 6 ms one-way error.

**Forge action:** `data/deviated_correction.py` (Eureka 6) — use Bunga Lili as canonical test case. Deviation ≥ 30° triggers raytraced TVD-time; else straight-line OK. The Copilot's plot of `h_off vs TVDSS` IS the diagnostic.

### Insight 4 — dVint/dZ derivative is the compaction indicator
**Observation:** Copilot clipped `dv_dz` to `[-50, +50]` m/s/m. **This matches the GEOX `PhysicsGuard.validate_velocity_sanity()` bound exactly** (line 280 of `guards.py`). Independent cross-validation.

**Forge action:** ZERO. The Copilot's bound choice is identical to the GEOX guard. This is the F2 audit gate being honored. Document the cross-validation here as a citation in the test suite.

### Insight 5 — V_avg vs TWT is the velocity-analysis cross-check
**Observation:** The Copilot's panel (2,1) is a classic velocity-analysis plot. A non-monotonic V_avg with TWT is the **overpressure signature** (Hottman-Johnson indicator).

**Forge action:** ZERO new tool needed. The 3D cube generator `geox_data.generate_3d_cube` already uses per-trace Vp variation. The V_avg curve check is a derivative operation: `dV_avg/dTWT > 0` is normal compaction; `dV_avg/dTWT < 0` over a 200-m window = overpressure. Add this as a `validate_compaction_trend()` to PhysicsGuard (open forge).

### Insight 6 — T-Z residual from linear trend is the polynomial-fitter output
**Observation:** The Copilot's panel (3,0) computed `tz_r = TVDSS − polyval(polyfit(TWT, TVDSS, 1), TWT)`. This IS the residual that the new `fit_polynomial` fitter (Eureka 1) will surface in its envelope.

**Forge action:** ENHANCE `TDFitResult` to include the full residual curve, not just per-checkshot RMSE. The Copilot's plot is what the envelope's `residuals_ms` array will look like.

### Insight 7 — Vint distribution IS the Bayesian prior
**Observation:** Panel (2,2) histogram of all wells' Vint values. For a new well, this distribution is the **prior** for Bayesian update (Eureka 3, open).

**Forge action:** `uncertainty/bayesian_update.py` — start with this empirical Vint distribution as the prior. New checkshot → update posterior. The histogram becomes the seeded prior automatically when the well is from the same basin.

### Insight 8 — Multi-well simultaneous calibration is the right call
**Observation:** 8 wells in one basin, mixed deviation, mixed measurement quality. This is **exactly** the multi-well calibration scenario Eureka 4 was designed for.

**Forge action:** `calibration/multi_well.py` — fit one velocity model that minimises the χ² across all 8 wells simultaneously, with per-well bulk-shift, per-layer V_int, and shared Thomsen δ. The Copilot's panel grid is the visual diagnostic.

---

## 3. CROSS-VALIDATION TABLE

| Copilot's choice | GEOX canonical | Match? | Notes |
|---|---|---|---|
| `clip(dv_dz, -50, 50)` | `PhysicsGuard.validate_velocity_sanity` bounds | ✅ EXACT | Independent cross-validation, F2 honored |
| CANON-9 Vp [1500, 6000] | `Physics9State.grade()` | ✅ | GeoX-implicit |
| `Vint` clipped to [500, 7000] for viz | tighter [1500, 6000] for audit | ⚠️ | Copilot is more permissive for display; GEOX is stricter for audit |
| `np.polyfit(twt, tvdss, 1)` for residual | `fit_polynomial` degree=1 | ✅ | Polynomial fitter already does this |
| 3-panel per-well plots | 12-panel summary | ⚠️ | Different visual; both valid |

---

## 4. WHAT THE COPILOT DIDN'T CATCH (forge targets)

- **No Bayesian prior** — panel (2,2) is a static histogram, not a posterior update
- **No anisotropy (Thomsen ε, δ, γ)** — Copilot did not compute, even though the Shale vs Sandstone distinction in the basin demands it
- **No Monte Carlo / P10/P50/P90** — point estimates only
- **No OCR / legacy ingestion** — Copilot only handled XLSX; the original report had scanned 1970s checkshots (per session log)
- **No cascade demotion** — when Copilot's "synthetic" BULUH-1 differs from a future real BULUH-1, the system should auto-demote the assumption; it didn't
- **No Kriging** — 8 wells across a basin should be interpolated geostatistically; Copilot only did per-well plots
- **No ray-trace for BUNGA LILI-1** — Copilot computed `h_off` but didn't correct the TWT for it

**Every "didn't catch" → a specific Eureka on the open list.** This dataset is the **stress test** that will validate the full 7-Eureka forge.

---

## 5. ACTION ITEMS (forge routing)

| Eureka | What this dataset demands | Open / Closed |
|---|---|---|
| **E1 — td_methods** | Polynomial fitter with residual curve, layer_cake with tops from these wells | **CLOSED 2026-06-03** (just forged) |
| **E2 — legacy_ingest** | Quality tagger for "SYNTHETIC" labels, 3-format Excel parser, OCR for legacy scans | OPEN — forge this week |
| **E3 — uncertainty ensemble** | Monte Carlo over Vint prior, Bayesian update on new well | OPEN |
| **E4 — multi_well calibration** | χ² minimisation over 8 wells, per-well bulk shift, shared Thomsen δ | OPEN |
| **E5 — anisotropy VTI/TTI** | Shale vs Sandstone δ/ε from Vsh | OPEN |
| **E6 — deviated correction** | BUNGA LILI-1 raytrace vs straight-line | OPEN |
| **E7 — cascade demotion** | When BULUH-1 synthetic is replaced by a real checkshot, auto-demote the assumption | **CLOSED 2026-06-03** (just forged) |

---

**DITEMPA BUKAN DIBERI** — the real basin just handed us the test corpus. The forge continues.

*Authored 2026-06-03 by OMEGA. arifOS Federation. F2_TRUTH honored.*
