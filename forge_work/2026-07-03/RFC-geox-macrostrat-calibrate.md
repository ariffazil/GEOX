# RFC: geox_macrostrat_calibrate

> **Status:** DRAFT — RFC, not fact  
> **Date:** 2026-07-03  
> **Author:** FORGE (000Ω)  
> **Verdict:** OVERCLAIM — HOLD until receipts exist  

---

## 1. Purpose

Resolve a biozone to an absolute age bracket by cross-referencing:
1. GEOX internal NN-age table (Martini 1971 + GPTS2020)
2. Macrostrat time intervals (global age brackets)
3. Macrostrat units at lat/lng (local rock packages)

Merge all three into a calibrated age bracket with uncertainty, provenance, contradiction flags, and a constitutional ruling.

## 2. Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `biozone` | string | Yes | Biozone identifier (e.g., "NN5", "P21") |
| `lat` | float | Yes | Latitude (EPSG:4326) |
| `lng` | float | Yes | Longitude (EPSG:4326) |
| `radius_km` | float | No | Search radius for Macrostrat columns (default: 50) |
| `discipline_hint` | string | No | Biostrat discipline (calcareous_nannofossil, planktonic_foram, etc.) |

## 3. Outputs

| Field | Type | Description |
|-------|------|-------------|
| `age_min_ma` | float | Youngest possible age |
| `age_max_ma` | float | Oldest possible age |
| `uncertainty_myr` | float | Age uncertainty in Myr |
| `calibration_source` | string | Which source provided the age (NN_table / macrostrat_interval / macrostrat_unit) |
| `contradiction_list` | array | List of contradictions found between sources |
| `ruling` | enum | PASS / WEAK_PASS / HOLD / CONTRADICTION |
| `provenance` | object | Full audit trail of each source consulted |

## 4. Contradiction Rules

| Condition | Ruling |
|-----------|--------|
| NN age fully within Macrostrat interval | PASS |
| NN age partially overlaps Macrostrat interval | WEAK_PASS |
| NN age outside Macrostrat interval | CONTRADICTION |
| No Macrostrat data at location | HOLD |
| NN zone not recognized | HOLD |

## 5. Governance

- **ΔΩΨ (clarity × humility × vitality):** All three must pass for PASS ruling
- **B1 (reversibility):** Tool is read-only, fully reversible
- **B2 (evidence):** Every output field must carry source_citation
- **B3 (uncertainty):** Age uncertainty must be explicit, never hidden
- **B4 (facies veto):** Biozone-implied environment must not conflict with lithology without explanation
- **B5 (diachroneity):** Must flag if biozone is known to be diachronous
- **B6 (reworking):** Must check if fossils could be reworked
- **B7 (contradiction):** Contradictions must be surfaced, never suppressed
- **B8 (seal):** CONTRADICTION ruling blocks SEAL

## 6. Implementation Notes

- Wraps existing `geox_biostrat_nn_age` (NN table lookup)
- Wraps Macrostrat API client (to be built: `macrostrat_client.get_intervals()`, `get_columns()`, `get_units()`)
- Does NOT replace Macrostrat — queries it as external evidence
- Returns governed envelope with claim_tag, evidence_refs, audit_receipt

## 7. Current State

| Component | Status |
|-----------|--------|
| NN-age table | ✅ Exists (`geox_biostrat_nn_age`) |
| Macrostrat API client | ❌ Not built |
| Cross-reference engine | ❌ Not built |
| Contradiction detection | ❌ Not built |
| Facies veto | ❌ Not built |

**Verdict: RFC only. Tool does not exist yet.**

---

*RFC by FORGE (000Ω). No implementation until receipts prove need.*  
*DITEMPA BUKAN DIBERI.*
