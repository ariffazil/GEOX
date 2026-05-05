# GEOX — Roadmap H1–H4

**Version:** v2026.05.06  
**Organ:** GEOX (Earth · Ψ Node)  
**Maturity:** PRODUCTION (387 commits)  
**Role:** Earth-domain coprocessor — geoscience, petrophysics, physics-9 verification  
**Status:** SEALED — pending APEX ratification

---

## Executive Summary

GEOX is the Earth-domain coprocessor of the arifOS federation — the Ψ node for subsurface intelligence. It is PRODUCTION-mature with solid domain organ architecture. H1–H4 focuses on: real-time sensor ingestion, uncertainty quantification standards, and physics solver integration.

**GEOX responsibilities by horizon:**

| Horizon | Theme | GEOX Milestones |
|---------|-------|-----------------|
| **H1** (Q2–Q3 2026) | Substrate Hardening | Real-time sensor bridge, uncertainty quantification |
| **H2** (Q4 2026–Q1 2027) | Recursive Governance | Physics solver integration, proof-carrying evidence |
| **H3** (Q2–Q3 2027) | AGI-Scale Runtime | Real-time planetary boundary monitoring with WEALTH |
| **H4** (Q4 2027+) | Foundational Substrate | Cross-federation earth data standard |

---

## H1: Substrate Hardening (Q2–Q3 2026)

### H1.1 Real-Time Sensor Bridge

Move from file-batch ingestion to streaming sensor ingestion for live seismic and environmental monitoring.

**Current state:** File-based batch ingestion (LAS files, SEG-Y, CSV)  
**Target state:** MQTT/IoT streaming + REST polling for live sensors

**Architecture:**

```
Sensors ( seismometers, GPS, pressure gauges )
         │
         ▼ (MQTT / OSC / HTTP)
┌─────────────────────────┐
│  GEOX Sensor Bridge     │
│  - Protocol adapters    │
│  - Normalization layer   │
│  - Quality control       │
│  - Drift correction      │
└────────────┬────────────┘
             │ (normalized readings)
             ▼
┌─────────────────────────┐
│  GEOX Evidence Store     │
│  - Time-series DB        │
│  - Uncertainty metadata  │
│  - arifOS verdict ready  │
└────────────┬────────────┘
             │ (MCP call)
             ▼
       arifOS 888 JUDGE
```

**Sensor protocols to support:**
- MQTT (primary for IoT sensors)
- OSC (OpenSound Control — seismic instruments)
- HTTP/REST polling (weather stations, satellite feeds)
- WebSocket (near-real-time satellite data)

**Quality flags:**
```python
@dataclass
class SensorReading:
    sensor_id: str
    timestamp: datetime
    value: float
    unit: str
    quality_flags: list[QualityFlag]
    uncertainty_m: float  # Measurement uncertainty (±)
    drift_corrected: bool

class QualityFlag(Enum):
    VALID = "valid"
    SUSPECT = "suspect"       # Calibration drift detected
    GAP = "gap"               # Missing data in window
    SPIKE = "spike"           # Anomalous spike detected
    CALIBRATED = "calibrated" # Post-calibration correction applied
```

**Owner:** GEOX infrastructure team  
**Target:** August 2026  
**Dependency:** arifOS MCP tool `arif_evidence_fetch` must accept streaming inputs

### H1.2 Uncertainty Quantification Standard

Every GEOX output must carry explicit confidence intervals and epistemic/aleatory uncertainty decomposition.

**arifOS ignores point estimates without variance.**

**Required output schema for all GEOX tools:**

```python
@dataclass
class UncertaintyQuantifiedOutput:
    # Point estimate
    value: float
    unit: str

    # Aleatory uncertainty (irreducible — natural variability)
    aleatory_std: float
    aleatory_ci_95: tuple[float, float]  # Lower, upper bound

    # Epistemic uncertainty (reducible with more data)
    epistemic_std: float | None = None
    epistemic_ci_95: tuple[float, float] | None = None

    # Combined uncertainty
    total_std: float
    total_ci_95: tuple[float, float]

    # Dominant uncertainty type
    dominant_uncertainty: Literal["aleatory", "epistemic", "mixed"]

    # Evidence quality
    data_points: int
    coverage_ratio: float  # % of domain covered by data
    model_confidence: float  # 0–1 internal model confidence

    # arifOS will reject outputs where:
    # - total_ci_95 width > 20% of value magnitude
    # - epistemic_std > aleatory_std (means more data would significantly change result)
    # - coverage_ratio < 0.6 (insufficient spatial coverage)
```

**Existing tools to update:**
- `geox_porosity_calculate`
- `geox_saturation_calculate`
- `geox_lithos_interpret`
- `geox_fluid_mapping`
- `geox_pressure_gradient`

**Owner:** GEOX science team  
**Target:** July 2026

### H1.3 Physics Solver Integration

Hard-link GEOX to deterministic physics engines (OpenFOAM, SeisSol) so AI-generated interpretations can be grounded against first-principles simulation.

**Integration levels:**

```yaml
# Level 1 — Validation (H2, Q4 2026)
GEOX outputs a result →
Physics solver runs independently →
Results compared →
GEOX flags large discrepancies (Δ > 2σ)

# Level 2 — Guidance (H3, Q2 2027)
arifOS routes uncertain cases to physics solver first →
Physics result becomes primary evidence →
GEOX AI interpretation secondary

# Level 3 — Fusion (H4, Q4 2027+)
Joint AI + physics inversion ( Ensemble Kalman Filter )
Real-time updating as sensor data streams
```

**Physics engines:**
- **OpenFOAM** — Computational fluid dynamics (reservoir simulation)
- **SeisSol** — Dynamic earthquake rupture simulation
- **Specfem** — Seismic wave propagation
- **MRst** — MATLAB Reservoir simulation toolbox

**Owner:** GEOX science team  
**Target:** December 2026 (Level 1)

---

## H2: Recursive Governance (Q4 2026 – Q1 2027)

### H2.1 Proof-Carrying Evidence

Every GEOX evidence output must include a verifiable justification trace for arifOS 888_JUDGE.

**Required proof components for GEOX:**
1. **Data lineage:** Raw sensor/file → processed → interpreted with full trace
2. **Model identification:** Which petrophysical model used (Archie, Simandoux, etc.)
3. **Assumption inventory:** Every assumption with explicit confidence
4. **Alternative considered:** At least one alternative interpretation that was rejected
5. **Physical consistency:** Cross-check against physics solver results
6. **Uncertainty budget:** Full epistemic/aleatory decomposition

### H2.2 WEALTH ↔ GEOX Coupling

Price ecological damage in real time: GEOX outputs feed directly into WEALTH `wealth_future_steward` for planetary boundary valuation.

**Coupling specification:**

```
GEOX (real-time):
  - Seismic activity index
  - Groundwater depletion rate
  - Soil erosion flux
  - Carbon storage change
         │
         ▼ (每小时 MCP call)
WEALTH (wealth_future_steward):
  - Price ecological externalities
  - Update planetary boundary indicators
  - Trigger alerts if thresholds exceeded
```

---

## H3: AGI-Scale Runtime (Q2–Q3 2027)

### H3.1 Real-Time Planetary Boundary Monitoring

GEOX + WEALTH loop running continuously, monitoring:
- Planetary boundaries (Rockström et al. 2009)
- Subsurface stability indices
- Resource extraction rates vs. renewal rates

### H3.2 Interpretability Organ (LENS) Integration

GEOX outputs fed to LENS (new organ) for causal attribution in earth-domain judgments.

---

## H4: Foundational Substrate (Q4 2027+)

### H4.1 Cross-Federation Earth Data Standard

GEOX data schemas adopted as the federation standard for earth/subsurface evidence exchange.

---

## Immediate Actions (This Week)

- [ ] **Sensor inventory** — List all sensor types, protocols, data rates currently in use
- [ ] **Uncertainty schema** — Draft `UncertaintyQuantifiedOutput` schema for review
- [ ] **Physics solver candidates** — Identify Level 1 integration targets (OpenFOAM or SeisSol)

---

## Dependency Chain

```
[H1.1 Sensor Bridge] ──► [H1.2 Uncertainty Quant]
         │
         └──────► [H2.2 WEALTH-GEOX Coupling]
                              │
                              ▼
               [H3.1 Real-time Planetary Monitoring]
```

---

## Tool Count Note

GEOX claims 15 MCP tools. This must be reconciled in the unified `MCP_ENDPOINT_REGISTRY` v2.0 (AAA ownership, June 2026).

---

**DITEMPA BUKAN DIBERI — Earth intelligence is forged, not given.**

*SEALED: 2026-05-06 | GEOX Earth Domain*
