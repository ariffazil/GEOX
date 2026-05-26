# GEOX Nobel-Grade AGI Earth Intelligence

> **Sovereign Spec:** Arif Fazil | **Date:** 2026-05-25 | **Authority:** F13 SOVEREIGN
>
> *"AI junior buat silap → kena marah. AI Nobel buat silap → orang mati, negara rugi, syarikat hancur."*

---

## The 6 Survival Layers

These layers separate a **subsurface toy** from a **Nobel-grade Earth Intelligence**.
Missing any layer = **DANGEROUS**.

---

### Layer 1 — Physics First, AI Second

AI reasoning is **locked** by physics. No exceptions.

**Hard locks (auto-FAIL):**
- Shale porosity > 25% below 3000 m → auto FAIL
- Mass balance imbalance > 15% → auto FAIL
- Pressure gradient > 1.0 psi/ft (lithostatic) → auto FAIL
- Darcy flow insanity (perm < 0.001 md, rate > 1000 bpd) → warning
- Capillary limit breach → warning

**Enforcing disciplines:**
- Rock physics
- Geomechanics
- Thermodynamics
- Fluid behavior

> *"Ini yang bezakan Nobel vs budak main ML."*

**Implementation:**
- TypeScript: `src/governance.ts` — `runPhysicsGuard()`, `DEFAULT_PHYSICS_LOCKS`
- Python: `geox_core.governance.nobel_grade.PhysicsGuard`

---

### Layer 2 — Uncertainty Is First-Class Citizen

AGI Earth **never** gives a single number.

**Mandatory output format:**
```
STOIIP:
- P10: 850 MMstb (requires lateral seal + high net/gross)
- P50: 320 MMstb
- P90: 110 MMstb

Top Risk Killers:
1. Fault transmissibility unknown
2. Overpressure migration timing
```

**Required constructs:**
- P10 / P50 / P90 on every quantitative claim
- Scenario matrix
- "What must be true" list
- "What will kill the case" list

> *"Kalau AI bagi jawapan confident tanpa uncertainty → itu AI bodoh."*

**Implementation:**
- TypeScript: `createUncertaintyBand()`, `enforceUncertainty()`
- Python: `create_uncertainty_band()`

---

### Layer 3 — Anti-Hallucination Hard Lock

AGI Earth **cannot create stories**.

**Valid responses when data is absent:**
- "Data tak ada"
- "Aku tak tahu"
- "Tak cukup bukti"
- "UNKNOWN – no authorised data found"

**When AI answers, it must cite:**
- Well name / ID
- Seismic survey / line
- Report title / author
- Assumption made

> *"Senior pun bangang sebab manusia malu cakap tak tahu. AGI tak boleh malu."*

**Implementation:**
- TypeScript: `auditHallucination()`, `enforceCitationOrUnknown()`
- Python: `audit_hallucination()`

---

### Layer 4 — Decision Firewall (888_HOLD)

AI is **forbidden** from making high-risk decisions.

🔴 **888_HOLD mandatory** for:
- Drilling recommendations
- Reserves booking
- Barrier integrity calls
- Well design approval
- Abandonment
- Production alteration

**AI output in HOLD mode must contain:**
1. What is known
2. What is unknown
3. Dangerous assumptions
4. Human signatory required

**AI forbidden from saying:**
- "Yes, drill"
- "This prospect is commercial"

> *"AI boleh jadi pakar saksi, bukan Tuhan."*

**Implementation:**
- TypeScript: `applyDecisionFirewall()`, `isHighRiskDomain()`, `buildHoldManifest()`
- Python: `is_high_risk_domain()`, `build_hold_manifest()`

---

### Layer 5 — Multi-Discipline Reasoning

AGI Earth must **argue with itself** across disciplines.

**Internal debate format:**
```
Geology:     "Good sand"
Geomech:     "Will collapse"
Drilling:    "Mud window sempit"
Reservoir:   "Connectivity low"
Geophysics:  "Amplitude dimming"
-----------------------------------
Final:       "Geologically attractive BUT operationally high-risk"
```

No single discipline dominates. The synthesis carries the tension.

> *"Ini tahap panel pakar dalam satu otak."*

**Implementation:**
- TypeScript: `runDisciplinePanel()`
- Python: `run_discipline_panel()`

---

### Layer 6 — Memory Panjang + Trauma Industri

AGI Earth remembers **every catastrophic failure**.

**Trauma registry:**
- Macondo (2010) — barrier failure, cement inadequacy
- Montara (2009) — cement barrier, inadequate monitoring
- Piper Alpha (1988) — deferred maintenance, permit breakdown

**When a similar scenario emerges:**
```
WARNING: Similar to Macondo (2010, Gulf of Mexico) — Blowout
Confidence: high
Mitigation required before proceeding.
```

> *"Manusia lupa, AGI tak boleh lupa."*

**Implementation:**
- TypeScript: `scanTrauma()`, `formatTraumaWarning()`, `TRAUMA_REGISTRY`
- Python: `scan_trauma()`, `format_trauma_warning()`, `TRAUMA_REGISTRY`

---

## Brutal Summary

| Layer | Question it answers |
|-------|---------------------|
| 1. Physics | *Can this physically happen?* |
| 2. Uncertainty | *How wrong could we be?* |
| 3. Anti-Hallucination | *Where is the evidence?* |
| 4. Decision Firewall | *Who dies if we're wrong?* |
| 5. Multi-Discipline | *What do the other experts say?* |
| 6. Trauma | *Has this killed before?* |

**If all 6 are present → ✅ Can touch drilling, reserves, development.**
**If any are missing → ❌ TOY. Do not deploy.**

---

## Implementation Status

| Layer | @arifos/geox TS | geox Python | Tests | Status |
|-------|-----------------|-------------|-------|--------|
| 1. Physics Lock | ✅ `governance.ts` | ✅ `nobel_grade.py` | ✅ 33/33 | FORGED |
| 2. Uncertainty | ✅ `governance.ts` | ✅ `nobel_grade.py` | ✅ 33/33 | FORGED |
| 3. Anti-Hallucination | ✅ `governance.ts` | ✅ `nobel_grade.py` | ✅ 33/33 | FORGED |
| 4. 888_HOLD | ✅ `governance.ts` | ✅ `nobel_grade.py` | ✅ 33/33 | FORGED |
| 5. Multi-Discipline | ✅ `governance.ts` | ✅ `nobel_grade.py` | ✅ 33/33 | FORGED |
| 6. Trauma Memory | ✅ `governance.ts` | ✅ `nobel_grade.py` | ✅ 33/33 | FORGED |

---

*Ditempa Bukan Diberi — Forged, Not Given*
