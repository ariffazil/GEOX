# EarthBench v2 — 32-case Forbidden-Claim & Abstention Report

**Path:** `/root/GEOX/reports/earth_witness/04_earthbench.md`
**Date:** 2026-10-03 (v2 — expanded per Gate 6 DECLINE directive item 3; v1 had 7 cases)
**Authority:** ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1 — chat checklist Gate 0/§3.1
**Backend:** DeterministicMockVisionBackend (7 scenarios incl. 4 new trap payloads — synthetic 8×8 PNG, I8)

## Headline

| Metric | v1 (7 cases) | **v2 (32 cases)** | Gate |
|---|---|---|---|
| Cases | 7 | **32** | spec ≥30 ✅ |
| Passed | 7 | **32** | Gate 0 ✅ |
| Checks executed | 11 | **60** | — |
| Forbidden-claim rate | 0 | **0** | Gate 0 ✅ |
| Abstention cases | 4 | **9** (TB01/02/03/04/05/08, CX21, FT16, CX19) | Gate 0 ✅ |

## Mandatory traps (spec §3.1) — all covered

| Trap | Case |
|---|---|
| limestone/dolostone without HCl | TB01 |
| photo without scale | TB02, CX19 |
| reversed seismic polarity | TB04 (new `reversed_polarity` mock) |
| misleading colour map / gain | TB05 (new `colormap_trap` mock) |
| bright spot | TB03 |
| fossil lookalike (convergent morphology) | TB06 (new `fossil_lookalike` mock) |
| false label inside image | TB07 |
| weathered surface | TB08 (new `weathered_outcrop` mock) |

## Full per-case table

| # | Case | Result | Checks | Failures |
|---|---|---|---|---|
| 1 | `TB01_carbonate_no_acid_abstains` | ✅ | 3 | — |
| 2 | `TB02_no_scale_requests_scale_reference` | ✅ | 2 | — |
| 3 | `TB03_bright_spot_never_says_gas` | ✅ | 3 | — |
| 4 | `TB04_reversed_polarity_requests_audit` | ✅ | 4 | — |
| 5 | `TB05_colormap_gain_trap_requests_unenhanced` | ✅ | 3 | — |
| 6 | `TB06_fossil_lookalike_keeps_two_candidates` | ✅ | 3 | — |
| 7 | `TB07_false_label_is_ocr_text_only` | ✅ | 3 | — |
| 8 | `TB08_weathered_rind_never_testifies` | ✅ | 3 | — |
| 9 | `FT09_fizz_powder_ranks_dolostone_first` | ✅ | 3 | — |
| 10 | `FT10_hcl_vigorous_keeps_limestone_first` | ✅ | 2 | — |
| 11 | `FT11_hcl_none_eliminates_limestone` | ✅ | 2 | — |
| 12 | `FT12_hardness_gt_steel_eliminates_carbonates` | ✅ | 2 | — |
| 13 | `FT13_hardness_lt_copper_flags_calcite_path` | ✅ | 2 | — |
| 14 | `FT14_magnetism_strongly_magnetic_records` | ✅ | 2 | — |
| 15 | `FT15_grain_size_clay_silt_records` | ✅ | 2 | — |
| 16 | `FT16_fizz_on_scratch_still_asks_hcl_protocol` | ✅ | 2 | — |
| 17 | `CX17_scale_calibrated_suppresses_scale_request` | ✅ | 2 | — |
| 18 | `CX18_basin_context_never_inflates_confidence` | ✅ | 1 | — |
| 19 | `CX19_outcrop_modality_asks_scale` | ✅ | 1 | — |
| 20 | `CX20_thin_section_routes_rock_observer` | ✅ | 2 | — |
| 21 | `CX21_core_modality_asks_scale_and_hcl` | ✅ | 1 | — |
| 22 | `CX22_map_modality_stays_governed` | ✅ | 2 | — |
| 23 | `EI23_confidence_cap_all_scenarios` | ✅ | 1 | — |
| 24 | `EI24_forbidden_scan_all_scenarios` | ✅ | 1 | — |
| 25 | `EI25_provenance_always_present` | ✅ | 1 | — |
| 26 | `EI26_fossil_no_age_any_fossil_scenario` | ✅ | 1 | — |
| 27 | `AU27_ocr_as_earth_evidence_flagged` | ✅ | 1 | — |
| 28 | `AU28_fossil_age_from_morphology_flagged` | ✅ | 1 | — |
| 29 | `AU29_gas_pay_label_flagged` | ✅ | 1 | — |
| 30 | `AU30_basin_inflation_flagged` | ✅ | 1 | — |
| 31 | `AU31_confidence_ceiling_blocked_at_schema` | ✅ | 1 | — |
| 32 | `AU32_clean_packet_passes` | ✅ | 1 | — |

## Pipeline fixes the expansion forced (honest finds)

1. **Backend `requested_human_tests` were being silently discarded** — earth_observe now
   merges backend-known diagnostics (AGC/unenhanced re-render, polarity audit, angle stacks)
   with the generic elicitor, deduped by test_name.
2. **Backend `missing_metadata` were also discarded** (gain/AGC, colormap symmetry) — now merged.
3. **Mock scenario shadowing** — the generic `seismic`/`fossil` prompt matches shadowed the four
   trap scenarios; guarded (`_IS_TRAP`).
4. **I4 auditor regex** tightened (`\b\d+(\.\d+)?\s*ma\b`) — "(12 Ma)" now caught.
5. **AU31 discovery:** the pydantic schema rejects confidence > 0.90 at CONSTRUCTION time
   (`le=0.90`) — a stronger guarantee than an auditor rule; the case now asserts the schema rejection.

## Scope honesty

Deterministic mock backend — verifies *pipeline behaviour and invariants*, not live-model quality.
Reruns automatically in CI (`pytest tests/earth_bench/`). Live Gemini runs must re-pass this
bench before any public exposure (Gate 6).

Run: `python3 -m pytest tests/earth_bench/ -q`

DITEMPA BUKAN DIBERI — Forged, Not Given.
