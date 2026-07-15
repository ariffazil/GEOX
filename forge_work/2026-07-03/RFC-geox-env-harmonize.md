# RFC: geox_env_harmonize

> **Status:** DRAFT — RFC, not fact  
> **Date:** 2026-07-03  
> **Author:** FORGE (000Ω)  
> **Verdict:** OVERCLAIM — HOLD until receipts exist  

---

## 1. Purpose

Harmonize local environment interpretations (from well logs, biostrat, lithology) with Macrostrat's global environment classifications. Detect conflicts, score them, and produce a governed verdict.

## 2. Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `local_env` | string | Yes | Local environment interpretation (e.g., "deltaic", "reef", "bathyal") |
| `macro_env` | string | Yes | Macrostrat environment classification at the same location/age |
| `local_lithology` | string | No | Local lithology for cross-check |
| `macro_lithology` | string | No | Macrostrat lithology for cross-check |
| `age_ma` | float | No | Age for temporal context |

## 3. Outputs

| Field | Type | Description |
|-------|------|-------------|
| `conflict_score` | float | 0.0 (no conflict) to 1.0 (total contradiction) |
| `contradictory_properties` | array | List of specific contradictions (e.g., "local=reef, macro=deep_marine") |
| `harmonized_env` | string | Best-guess unified environment |
| `confidence` | float | Confidence in harmonized result (0–1) |
| `ruling` | enum | PASS / WEAK_PASS / HOLD / CONTRADICTION |
| `provenance` | object | Source of each input |

## 4. Conflict Scoring

| Score Range | Meaning | Ruling |
|-------------|---------|--------|
| 0.0 – 0.3 | Compatible environments | PASS |
| 0.3 – 0.7 | Partial overlap, some tension | WEAK_PASS |
| 0.7 – 1.0 | Direct contradiction | HOLD (blocks SEAL) |

## 5. Environment Taxonomy

Must map between:
- **Local taxonomy:** Operator-specific codes (e.g., "FLUVIAL", "DELTAIC", "REEF")
- **Macrostrat taxonomy:** `macrostrat_client.get_environments(unit_id)` → standardized codes
- **GEOX internal:** `depo_env_code` from geox_sequence

Mapping table required. If mapping is ambiguous → HOLD.

## 6. Governance

- **F2 TRUTH:** Conflict score must be computed, not guessed
- **F4 CLARITY:** Contradictory properties must be explicit
- **F7 HUMILITY:** If local and macro environments are in different taxonomy families, confidence capped at 0.7
- **B4 (facies veto):** Lithology-environment cross-check required
- **B7 (contradiction):** Conflict > 0.7 → HOLD, blocks SEAL

## 7. Current State

| Component | Status |
|-----------|--------|
| Local environment parsing | ❌ Not built |
| Macrostrat environment API | ❌ Not built |
| Taxonomy mapping table | ❌ Not built |
| Conflict scoring algorithm | ❌ Not built |
| Cross-check with lithology | ❌ Not built |

**Verdict: RFC only. Tool does not exist yet.**

---

*RFC by FORGE (000Ω). No implementation until receipts prove need.*  
*DITEMPA BUKAN DIBERI.*
