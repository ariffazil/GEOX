# RFC: geox_deep_time_cycle

> **Status:** DRAFT — RFC, not fact  
> **Date:** 2026-07-03  
> **Author:** FORGE (000Ω)  
> **Verdict:** OVERCLAIM — HOLD until receipts exist  

---

## 1. Purpose

Given an age (Ma), determine where Earth sits in its major geological cycles (supercontinent, sea-level, climate, orbital), predict expected lithology and environment, and score deviation from observed data.

## 2. Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `age_ma` | float | Yes | Age in millions of years before present |
| `lat` | float | No | Latitude for paleogeographic context |
| `lng` | float | No | Longitude for paleogeographic context |
| `observed_lithology` | string | No | Observed lithology to compare against prediction |
| `observed_environment` | string | No | Observed environment to compare against prediction |

## 3. Outputs

| Field | Type | Description |
|-------|------|-------------|
| `cycle_phase` | object | Phase of each major cycle at this age |
| `expected_lithology` | string[] | Predicted lithologies from cycle position |
| `expected_environment` | string[] | Predicted environments from cycle position |
| `deviation_score` | float | How far observed deviates from expected (0–1) |
| `ruling` | enum | PASS / WEAK_PASS / HOLD / CONTRADICTION |
| `provenance` | object | Source curves and models used |

## 4. Cycle Engines

### 4.1 Supercontinent Cycle
- **Source:** Bradley (2011), Nance & Murphy (2013)
- **Phases:** assembly → supercontinent → breakup → dispersal → assembly
- **At 15 Ma:** Dispersal phase (modern config)
- **Expected:** Passive margins, high biodiversity, moderate volcanism

### 4.2 Sea-Level Cycle
- **Source:** Haq (2017), Miller et al. (2005)
- **Status:** ❌ PENDING — curve not ingested
- **At 15 Ma:** Mid-Miocene climatic optimum → high sea level (~+40m)

### 4.3 Climate Cycle
- **Source:** Zachos et al. (2008), Westerhold et al. (2020)
- **Status:** ❌ PENDING — curve not ingested
- **At 15 Ma:** Warm-house → transitioning to ice-house

### 4.4 Orbital Cycles (Milankovitch)
- **Source:** Laskar et al. (2011) La2011
- **Status:** ✅ Partially operational (eccentricity, obliquity computed)
- **At 15 Ma:** Normal orbital parameters

## 5. Deviation Scoring

| Deviation | Meaning | Ruling |
|-----------|---------|--------|
| 0.0 – 0.2 | Observed matches expected | PASS |
| 0.2 – 0.5 | Minor deviation, explainable | WEAK_PASS |
| 0.5 – 0.8 | Significant deviation | HOLD |
| 0.8 – 1.0 | Major contradiction | CONTRADICTION |

## 6. Governance

- **F2 TRUTH:** Predictions must cite source curves, not intuition
- **F7 HUMILITY:** If source curve is missing → confidence capped at 0.3
- **B1 (reversibility):** Read-only, fully reversible
- **B3 (uncertainty):** Deviation score must include uncertainty bounds
- **B7 (contradiction):** Deviation > threshold → HOLD

## 7. Current State

| Component | Status |
|-----------|--------|
| Supercontinent cycle engine | ⚠️ Qualitative only (Bradley 2011 reference) |
| Sea-level curve ingestion | ❌ Not built |
| Climate curve ingestion | ❌ Not built |
| Orbital computation | ✅ Partial (La2011 for eccentricity/obliquity) |
| Deviation scoring algorithm | ❌ Not built |
| Observed vs expected comparison | ❌ Not built |

**Verdict: RFC only. Tool does not exist yet.**

---

*RFC by FORGE (000Ω). No implementation until receipts prove need.*  
*DITEMPA BUKAN DIBERI.*
