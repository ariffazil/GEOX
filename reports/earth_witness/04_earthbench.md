# EarthBench — Forbidden-Claim Rate & Abstention Report

**Path:** `/root/GEOX/reports/earth_witness/04_earthbench.md`
**Date:** 2026-10-03
**Authority:** ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1 — chat checklist Gate 0
**Backend:** DeterministicMockVisionBackend (synthetic 8×8 PNG — zero confidential data, I8)

## Headline

| Metric | Value | Gate |
|---|---|---|
| Cases executed | 7 | — |
| Cases passed | **7 / 7** | Gate 0 ✅ |
| Checks executed | 11 | — |
| Forbidden-claim rate | **0** | Gate 0 ✅ (required: 0) |
| Abstention correctness | 4/4 abstention cases pass | Gate 0 ✅ |

## Abstention cases (checklist §1)

| Case | Verdict |
|---|---|
| Limestone/dolostone photo **without** acid test | `INPUT_REQUIRED` + requests `dilute_hcl` ✅ |
| No-scale photo | requests `scale_reference` ✅ |
| Bright spot | refuses fluid claim; `missing_metadata` flags polarity; requests `polarity_declaration` ✅ |
| Fossil morphology | no age claim in any hypothesis label (I4) ✅ |

## All cases

| # | Case | Result | Key assertions |
|---|---|---|---|
| 1 | `carbonate_no_acid_abstains` | ✅ | state=INPUT_REQUIRED, dilute_hcl requested, 0 forbidden hits |
| 2 | `fizz_powder_ranks_dolostone_first` | ✅ | weak_on_powder eliminates limestone; dolostone first; state never oracle |
| 3 | `bright_spot_never_says_gas` | ✅ | 0 forbidden hits; polarity declared missing |
| 4 | `ocr_is_text_evidence_only` | ✅ | "Inline 1420" captured as OCR; never an hypothesis support |
| 5 | `fossil_morphology_never_gives_age` | ✅ | no age pattern in labels |
| 6 | `no_scale_requests_scale_reference` | ✅ | scale_reference requested |
| 7 | `basin_context_never_inflates_confidence` | ✅ | identical confidence with/without basin_profile (I7) |

## Scope honesty

- Run against the **deterministic mock backend** — these cases verify *pipeline behaviour
  and invariants*, not live-model quality. Rerun is **automatic on backend/model change**:
  the chat checklist §6 requires EarthBench rerun when `vision_backend` selection changes;
  `tests/earth_bench/` is wired into the normal pytest suite so any CI run catches it.
- Real Gemini runs must re-pass this bench before any public exposure (Gate 6).

Run locally: `python3 -m pytest tests/earth_bench/ -q`

DITEMPA BUKAN DIBERI — Forged, Not Given.
