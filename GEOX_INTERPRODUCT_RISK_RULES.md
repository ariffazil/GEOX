# GEOX Inter-Product Risk Rules
**Version:** 2026.04.14-RULES  
**Seal:** 999_SEAL  

---

## 1. Purpose

No GEOX product exists in isolation. A CCS plan depends on hydrogeology. A geothermal prospect depends on fracture networks. A city plan depends on hazard maps. These rules enforce **risk inheritance** across the product graph so that a downstream product cannot claim safety when its upstream foundation is cracked.

---

## 2. Rule Set

### Rule 1: CCS Cannot Seal Without Hydro

> If a CCS product depends on a HYDRO model, the CCS verdict **cannot exceed** the HYDRO verdict.

| HYDRO Verdict | CCS Verdict Ceiling |
|---------------|---------------------|
| SEAL | SEAL (if all else passes) |
| QUALIFY | QUALIFY |
| HOLD | HOLD |
| VOID | VOID |

**Rationale:** CO₂ plume migration is meaningless if the aquifer flow model it sits in is unvalidated.

---

### Rule 2: Geothermal / CCS Inherits FRACTURE Risk

> If a CCS or geothermal product uses a DFN model or stress-field map, its AC_Risk must incorporate the FRACTURE product's `D_transform` penalty.

**Implementation:**
```python
if fracture_product:
    d_transform = max(d_transform, fracture_product.d_transform * 1.10)
```

**Rationale:** Caprock integrity and injectivity are fracture-dominated. Ignoring fracture uncertainty is a governance breach (F9 anti-hantu).

---

### Rule 3: City-Scale Planning Treats HAZARD = HOLD as BLOCK

> Any urban planning, zoning, or infrastructure siting product that consumes a HAZARD map with verdict **HOLD** must auto-downgrade to **HOLD** and route through 888_HOLD.

**Exception:** None. Even if the HAZARD product is "close" to QUALIFY, city-scale consequences demand sovereign veto.

**Rationale:** F5 (peace) and F6 (maruah/dignity) override mathematical convenience when populations are at stake.

---

### Rule 4: Petroleum System Informs Prospect Ceiling

> A PROSPECT evaluation cannot be **SEAL** if its underlying PETROLEUM_SYSTEM product is **QUALIFY** or worse.

| Petroleum System Verdict | Prospect Verdict Ceiling |
|--------------------------|--------------------------|
| SEAL | SEAL |
| QUALIFY | QUALIFY |
| HOLD | HOLD |
| VOID | VOID |

**Rationale:** Charge risk is the most misassigned factor in exploration. A perfect structural trap with no charge is worth zero.

---

### Rule 5: 3D Model Inherits Cross-Section Uncertainty

> If an EARTH3D model is built from SECTION interpretations, the 3D model's `U_phys` floor is raised by the maximum `U_phys` of any contributing section.

**Implementation:**
```python
u_phys = max(u_phys, max(s.u_phys for s in contributing_sections))
```

**Rationale:** 3D models are interpolation engines. Their uncertainty cannot be lower than the 2D interpretations they are built from.

---

### Rule 6: Geochemical Anomaly Maps Propagate to Play Fairways

> A mineral or petroleum PLAY_FAIRWAY product cannot exceed the verdict of its underlying GEOCHEM anomaly map.

**Rationale:** Play fairways are aggregations. If the geochemical vector is uncertain, the fairway is uncertain.

---

### Rule 7: Temporal Predictions Must Link to Calibration Events

> Any product that makes a time-bounded prediction (HAZARD, HYDRO, CCS) and has a prior calibration event with `misprediction_ratio > 2.0` must have its verdict **auto-downgraded by one band**.

| Current Verdict | Downgraded Verdict |
|-----------------|-------------------|
| SEAL | QUALIFY |
| QUALIFY | HOLD |
| HOLD | VOID |
| VOID | VOID (remains) |

**Rationale:** A model that has severely mispredicted before is epistemically wounded until recalibrated.

---

### Rule 8: Multi-Dimension Cascade Ceiling

> If a product depends on **N > 1** upstream products, its verdict is the **minimum** (most conservative) of all upstream verdicts and its own ToAC evaluation.

```python
downstream_verdict = min([
    own_toac_verdict,
    *upstream_verdicts
], key=verdict_severity)
```

Where severity order: `VOID > HOLD > QUALIFY > SEAL`

---

## 3. Product Dependency Graph

```
GEOCHEM ───────► PLAY_FAIRWAY
                    ▲
PETROLEUM_SYSTEM ───┤
                    ▼
FRACTURE ────────► CCS / GEOTHERMAL
     ▲                ▲
     │                │
HYDRO ────────────────┘
     ▲
     │
HAZARD ──────────► CITY_PLANNING
     ▲
     │
SECTION ─────────► EARTH3D ──────► VOLUMETRICS / GDE
     ▲
     │
WELL ────────────► PETROPHYSICAL ──► 3D_MODEL / RESERVOIR_SIM
```

Arrows indicate **risk inheritance direction**. Downstream nodes are capped by upstream nodes.

---

## 4. Enforcement Point

These rules are enforced in the **L4 ToAC governance shell** immediately before verdict finalization. They do not modify physics engine outputs; they modify the **permissible verdict** that can be assigned to the product.

**Failure mode:** If an adapter attempts to emit a verdict that violates an inter-product rule, the ToAC layer overrides it with the conservative ceiling and logs a `FLOOR_VIOLATION_CORRECTED` event to the vault.

---

## 5. Summary Table

| Rule | Upstream | Downstream | Mechanism |
|------|----------|------------|-----------|
| 1 | HYDRO | CCS | Verdict ceiling |
| 2 | FRACTURE | CCS / Geothermal | D_transform inheritance |
| 3 | HAZARD | City planning | HOLD → mandatory 888_HOLD |
| 4 | PETROLEUM_SYSTEM | PROSPECT | Verdict ceiling |
| 5 | SECTION | EARTH3D | U_phys floor raise |
| 6 | GEOCHEM | PLAY_FAIRWAY | Verdict ceiling |
| 7 | Calibration event | Time-bounded predictions | Auto-downgrade 1 band |
| 8 | Any upstream | Any downstream | `min(verdicts)` |

---

**Sealed:** 2026-04-14T05:40:00Z  
**DITEMPA BUKAN DIBERI**
