# GEOX Substrate Spec — v0.2 (superseded)

> **⚠️ This spec has been superseded by `EGS_SPEC.md` (Earth Grounding System).**
> EGS is the canonical name ratified by F13 SOVEREIGN on 2026-06-28.
> This file is preserved for provenance. All future work references `EGS_SPEC.md`.

**Role:** Earth reality substrate for governed agentic systems (arifOS) — **now EGS**
**Scope:** Basin–field–asset scale, CCS + exploration + development + monitoring
**Authority:** F13 SOVEREIGN (Muhammad Arif bin Fazil)
**Status:** SUPERSEDED by EGS v1.0 — preserved for provenance
**Source of truth:** `src/geox_core/` (models), `contracts/` (schemas), `src/geox_mcp/` (tools)

---

## §0 Relationship to Existing GEOX

This spec describes GEOX's **intended substrate architecture**. The following already exist in the codebase:

| Component | Status | Path |
|-----------|--------|------|
| Physics9State (9 canonical Earth parameters) | ✅ LIVE | `src/geox_core/physics/state.py` |
| Earth Material Catalog (8 lithotypes) | ✅ LIVE | `src/geox_core/physics/state.py` |
| ClaimEnvelope (epistemic labels, units, CRS) | ✅ LIVE | `src/geox_core/schemas/claim_envelope.py` |
| EarthMemoryEnvelope (canonical claim container) | ✅ LIVE | `contracts/schemas/earth/earth_memory_envelope.json` |
| ClaimStateMachine (9 states, 8 transitions) | ✅ LIVE | `contracts/claim_state_machine.yaml` |
| Provenance schema (source_id, type, hash, method) | ✅ LIVE | `contracts/schemas/earth/provenance.json` |
| EpistemicIntegrity (pLDDT-style scoring) | ✅ LIVE | `core/epistemic_integrity.py` |
| 18 canonical MCP tools (query surface) | ✅ LIVE | `src/geox_mcp/registry.py` |
| Well domain (ingest, QC, desurvey, petrophysics) | ✅ LIVE | `src/geox_mcp/tools/well*.py` |
| Seismic domain (ingest, compute, interpret, vision) | ✅ LIVE | `src/geox_mcp/tools/seismic*.py` |
| Basin domain (profile, scene, deep time) | ✅ LIVE | `src/geox_mcp/tools/basin*.py` |
| Formal uncertainty algebra (interval/distribution/scenario types) | ❌ PROPOSED | — |
| Formal Update_T operators per entity | ❌ PROPOSED | — |
| InterpretationSet with scenario weights | ❌ PROPOSED | — |
| Formal Conflict_T model | ❌ PROPOSED | — |
| Intent classification + query plan protocol | ❌ PROPOSED | — |

**Legend:** ✅ = exists in codebase, ❌ PROPOSED = aspirational, needs build

---

## §1 Primitive Data Structures

GEOX is a **typed Earth graph** built on two foundational models that coexist:

- **Entity model:** geological objects (basins, wells, horizons, faults, volumes)
- **Physics model:** canonical 9-parameter Earth state vector at every point

Neither replaces the other. The entity model provides structure. The physics model provides properties.

### 1.1 Canonical Physics Substrate — Physics9State

The fundamental atomic description of any Earth material at any point. **9 orthogonal parameters** — no derived variables stored.

```python
@dataclass(frozen=True)
class Physics9State:
    rho: float    # kg/m³    — density
    vp: float     # m/s      — compressional velocity
    vs: float     # m/s      — shear velocity
    rho_e: float  # Ω·m      — electrical resistivity
    chi: float    # SI       — magnetic susceptibility
    k: float      # W/m·K    — thermal conductivity
    P: float      # Pa       — pore pressure
    T: float      # K        — temperature
    phi: float    # 0–1      — porosity
    # Extensions (not core 9):
    epsilon, delta, gamma: float  # Thomsen anisotropy
    qp, qs: float                 # Attenuation quality factors
```

**Derived variables** (bulk modulus, shear modulus, Young's modulus, Poisson ratio, acoustic impedance, Vp/Vs ratio, thermal diffusivity) are computed from Physics9State via pure functions in `parameters.py` — never stored, per orthogonality rule.

**Earth Material Catalog:** 8 canonical lithotypes (SANDSTONE, SHALE, LIMESTONE, DOLOMITE, ANHYDRITE, SALT, COAL, BASEMENT) with pre-computed Physics9State vectors. Used for default assignment when direct measurements are absent.

### 1.2 Core Entities

**1. Basin**
- `name: String`
- `region: GeoRegion` (polygon, CRS)
- `tectonic_setting: Enum`
- `strat_column: [StratUnitRef]`
- `plays: [PlayRef]`
- `assets: [AssetRef]`
- `state: BasinState` (exploration, mature, CCS, etc.)
- **Existing tool:** `geox_basin` (mode=profile, scene, intake, macrostrat)

**2. Stratigraphic unit**
- `name: String`
- `age_range: TimeInterval`
- `lithology: LithologyDescriptor`
- `depositional_env: Enum`
- `thickness_model: ScalarField3D`
- `contacts: [StratContact]`
- **Existing tools:** `geox_sequence` (correlation, systems tracts), `geox_deep_time_state`

**3. Horizon / surface**
- `geom: SurfaceMesh3D` (triangulated, CRS)
- `time: TimeMarker`
- `unit_above/below: StratUnitRef`
- `interpretation_state: InterpretationState`
- **Existing tool:** `geox_seismic_interpret` (horizon contrast, faults, frames, blend)

**4. Fault**
- `geom: SurfaceMesh3D`
- `throw_field: ScalarField3D`
- `seal_behavior: FaultSealModelRef`
- `activity_window: TimeInterval`
- **Existing tool:** `geox_seismic_interpret` (fault analysis)

**5. Volume / grid**
- `grid: StructuredGrid3D`
- `properties: { PropertyName -> PropertyField3D }` — porosity, permeability, saturation, pressure, temperature, velocity, etc.
- `mask: VolumeMask`
- **Existing tools:** `geox_subsurface_model` (joint inversion, gravity/mag, MT forward)

**6. Well**
- `surface_location: Point2D`
- `trajectory: WellPath3D` (from deviation survey)
- `logs: { LogName -> LogCurve }`
- `tops: [WellTop]`
- `tests: [WellTest]`
- `status: Enum`
- **Existing tools:** `geox_well_ingest`, `geox_well_qc`, `geox_well_desurvey`, `geox_petrophysics`

**7. Seismic survey**
- `volume: SeismicCube3D`
- `processing_history: [ProcessStep]`
- `velocity_model: VelocityModelRef`
- `quality_flags: [QualityFlag]`
- **Existing tools:** `geox_seismic_ingest`, `geox_seismic_compute`

**8. Asset / field**
- `name: String`
- `basin: BasinRef`
- `trap_model: TrapModelRef`
- `reserves_model: ReservesModelRef`
- `development_state: Enum`
- **Existing tools:** `geox_prospect` (volumetrics, POS, EVOI, risk)

### 1.3 Geometry and Topology

**Existing geometry primitives** (from GEOX tool surface):
- `Point2D`, `Point3D` — CRS-aware via `EarthMemoryEnvelope` CRS fields
- `WellPath3D` — from deviation survey (desurvey via minimum curvature)
- `SurfaceMesh3D` — horizons and faults
- `SeismicCube3D` — seismic volumes
- `ScalarField3D` — property distributions

**PROPOSED — not yet implemented:**
- `AdjacencyGraph` (unit–unit, fault–horizon, reservoir–seal)
- `ContactRelation` (ONLAP, DOWNLAP, TRUNCATION, UNCONFORMITY, CONFORMABLE)
- `ConnectivityGraph` (reservoir compartment, fault block, pressure communicating cluster)

### 1.4 Time

**Existing:** Deep time state via `geox_deep_time_state` (ICS Chart v2024/12 resolution, age intervals with uncertainty bounds).

**PROPOSED:**
- `Event` type with `type: Enum` (rift, uplift, inversion, deposition, erosion, seal formation, charge, breach), `time_window`, `affected_entities`
- Formal chronostratigraphic framework

### 1.5 Physics

**Existing:**
- Physics9State — 9 canonical parameters at every point
- Earth Material Catalog — 8 pre-defined lithotype vectors
- Physics9-derived moduli and transforms (bulk/shear/Young modulus, Poisson ratio, AI, Vp/Vs, Gardner, Faust)
- `anomaly_contrast_theory` — AVO class detection with attention residuals
- `compute_buoyancy` — buoyancy pressure from density contrast + thickness
- Joint inversion zone hooks

**Boundary:** Physics is **not fully solved inside GEOX**. GEOX holds:
- State fields (Physics9State per cell)
- Derived moduli (computed on demand, never stored)
- Links to external simulators (flow, geomechanics — via `subsurface_model` tool)
- Constraints (overpressure envelopes, fracture gradients — via PhysicsGuard)

---

## §2 Uncertainty Representation

GEOX uses a **multi-layer uncertainty system** — existing infrastructure augmented by proposed formal algebra.

### 2.1 Existing: Claim State Machine (LIVE)

9-state lifecycle governing all Earth claims, defined in `contracts/claim_state_machine.yaml`:

```
DRAFT → AI_INFERRED → REVIEW_PENDING → APPROVED_INTERPRETATION → SEALED
                         ↕                    ↕
                   NEEDS_EVIDENCE        CHALLENGED
                                              ↓
                                         REJECTED → REVOKED
```

Every claim must be in exactly one state. Transitions require:
- Evidence pack (for AI_INFERRED+)
- Human review (for REVIEW_PENDING+)
- F13 SOVEREIGN authority (for REVOKED from SEALED)

### 2.2 Existing: Epistemic Labels (LIVE)

Every claim carries an `EpistemicLabel` from `claim_envelope.py`:

| Label | Meaning | Example |
|-------|---------|---------|
| OBSERVED | Directly measured, traceable to instrument | Well log reading |
| DERIVED | Computed from observed with deterministic transform | AI from Vp + rho |
| ESTIMATE | Computed with model assumptions — range required | Porosity from inversion |
| HYPOTHESIS | Interpretive, single-hypothesis | Fault interpretation |
| PLAUSIBLE | Multi-hypothesis, physically plausible, uncalibrated | Migration pathway |
| UNKNOWN | Insufficient data | — |

### 2.3 Existing: Epistemic Integrity Scoring (LIVE)

pLDDT-style per-element confidence from `core/epistemic_integrity.py`:

```python
@dataclass
class EpistemicResult:
    integrity_score: float      # 0–1, overall
    classification: str         # CLAIM | PLAUSIBLE | AUTO_HOLD
    posterior_breadth: float    # uncertainty range
    evidence_density: float     # wells per 100km²
    model_lineage_hash: str     # provenance chain
    independence_score: float   # cross-model independence
    cross_modal_fidelity_score: float  # structural coherence
```

Scoring basis: evidence density, model lineage diversity, cross-modal consistency, parameter-specific confidence levels.

### 2.4 Existing: Risk Classification (LIVE)

Every output carries an `AcRiskLevel`:
- `QUALIFY` — low risk, proceed autonomously
- `ADVISORY` — medium risk, surface to operator
- `HOLD` — high risk, 888_HOLD gate required
- `BLOCK` — critical risk, blocked for all generic agents

### 2.5 Existing: Provenance Schema (LIVE)

Every claim traces to a source via `contracts/schemas/earth/provenance.json`:
- `source_id`, `source_type` (las/segy/well_header/tops/pressure/core etc.)
- `source_hash` (SHA256 for integrity)
- `ingested_at`, `operator`, `method`

### 2.6 PROPOSED: Formal Uncertainty Algebra

Extensions to build on top of existing infrastructure:

**Uncertainty types:**
1. **Interval uncertainty** — `x ∈ [x_min, x_max]` with optional confidence `c ∈ [0,1]`
2. **Distribution uncertainty** — `x ~ D(θ)` (Normal, Lognormal, Beta, etc.)
3. **Scenario uncertainty** — `ScenarioSet = {S₁...Sₙ}` with weights `w_i`

**Uncertainty algebra:**
- Addition (independent): `U₁ ⊕ U₂`
- Bayesian update: `p(θ|D) ∝ p(D|θ)p(θ)`
- Scenario aggregation: `E[x] = Σ w_i x_i`

**Status:** Data structures exist (Physics9State supports interval bounds, EarthMemoryEnvelope supports confidence fields). Typed algebra operators are NOT YET IMPLEMENTED.

---

## §3 Evidence Update Rules

### 3.1 Existing: Claim State Machine as Update Framework

GEOX does not have entity-specific `Update_T` operators. Instead, all updates flow through the **claim state machine**:

1. **New evidence arrives** → create/reopen a ClaimCard
2. **Evidence linked** → ClaimCard moves to AI_INFERRED or REVIEW_PENDING
3. **If contradictory** → ClaimCard moves to CHALLENGED
4. **If validated** → ClaimCard moves to APPROVED_INTERPRETATION
5. **If finalized** → ClaimCard moves to SEALED

### 3.2 Existing: Per-tool Update Patterns

Each tool defines its own update semantics:
- `geox_well_ingest` + `geox_well_qc` → adds wells to the knowledge base
- `geox_well_desurvey` → computes TVD/X/Y/TVDSS from deviation survey
- `geox_seismic_compute(mode=well_tie)` → anchors seismic to well tops via cross-correlation
- `geox_basin(mode=profile)` → synthesizes basin context from multiple sources
- `geox_seismic_interpret(mode=horizon_contrast)` → updates horizon picks

### 3.3 PROPOSED: Formal Update Operators

Future design for entity-specific update rules:

```python
Update_T(M_T, E) → (M_T', Δ_T)
```

Where:
- `M_T` is the current model state for entity type T
- `E` is new evidence
- `M_T'` is the updated state
- `Δ_T` is a change set with provenance

Preconditions, effects, and uncertainty impact defined per operator.

**Example (well update):**

| Step | Existing? | Detail |
|------|-----------|--------|
| 1. Match tops to StratUnit set | ✅ PARTIAL | `geox_sequence(mode=correlation)` |
| 2. Update horizon depths from deviation | ✅ | `geox_well_desurvey` |
| 3. Update petroleum system model | ✅ PARTIAL | `geox_prospect` |
| 4. Condition property fields | ✅ | `geox_petrophysics` |
| 5. Reduce epistemic uncertainty | ❌ | Proposed |
| 6. Attach evidence refs | ✅ PARTIAL | Via ClaimEnvelope |

---

## §4 Conflict Reconciliation

### 4.1 Existing: Challenge State

GEOX's claim state machine includes a `CHALLENGED` state for disputed interpretations. The system supports:
- Multiple interpretations on the same entity (via separate ClaimCards)
- Contradiction scanning (`geox_evidence(mode=contradict)`)
- Human review (REVIEW_PENDING state)

### 4.2 PROPOSED: Formal Interpretation Set Model

What does NOT yet exist:

**Interpretation sets:**
```python
InterpretationSet_T = {I₁, I₂, ..., Iₙ}
```
Each Iₖ has author, method, supporting_evidence, confidence, scenario_weight.

**Conflict model:**
```python
Conflict_T = (Iₐ, I_b, EvidenceSet, ImpactScope)
```

**Resolution:**
```python
Resolve(Conflict_T, GovernanceDecision) → UpdatedInterpretationSet
```

Where GovernanceDecision is issued by human committee or governance organ and recorded as a constitutional event.

**Status:** CHALLENGED state exists. Multi-interpretation storage, scenario weights, and formal resolution decisions are NOT YET IMPLEMENTED.

---

## §5 Query Interface

### 5.1 Existing: 18 Canonical MCP Tools (LIVE)

The primary query surface is the MCP tool registry. **14 surface-facing + 4 internal tools:**

| Tool | Domain | Returns |
|------|--------|---------|
| `geox_well_ingest` | Well | Ingested well data |
| `geox_well_qc` | Well | QC report |
| `geox_well_desurvey` | Well | 3D trajectory (TVD/X/Y/TVDSS) |
| `geox_petrophysics` | Well | Vsh, porosity, Sw, perm, net pay |
| `geox_sequence` | Well | Sequence stratigraphy, correlation |
| `geox_seismic_ingest` | Seismic | SEG-Y header inspect |
| `geox_seismic_compute` | Seismic | Synthetic, well-tie, AVO, attributes |
| `geox_seismic_interpret` | Seismic | Horizon contrast, faults, frames |
| `geox_vision` | Seismic | VLM inference, audit |
| `geox_subsurface_model` | Physics | Joint inversion, gravity/mag, MT |
| `geox_geomechanics` | Physics | K, G, E, ν, AI from Physics9State |
| `geox_basin` | Basin | Profile, scene, macrostrat, deep time |
| `geox_deep_time_state` | Basin | Earth State Vector at deep time |
| `geox_surface_status` | Registry | Canonical tool list, health |
| `geox_claim` (internal) | Governance | Create, validate, challenge, seal |
| `geox_evidence` (internal) | Evidence | Discover, synthesize, abduct, contradict |
| `geox_prospect` (internal) | Risk | Volumetrics, POS, EVOI |
| `geox_doctrine` (internal) | Doctrine | Floor enforcement |

### 5.2 Existing: Response Envelope (LIVE)

Every tool returns a `ClaimEnvelope`:

```jsonc
{
  "claim_state": "AI_INFERRED",
  "epistemic_label": "DERIVED",
  "value": { /* tool-specific payload */ },
  "uncertainty": { "interval": [min, max], "confidence": 0.85 },
  "grade": "INTERPRETED",
  "provenance": [{ "source_id": "...", "source_type": "las_file" }],
  "ac_risk": "QUALIFY",
  "units": "SI",
  "crs": "EPSG:4326"
}
```

### 5.3 PROPOSED: Unified Entity Query (future)

A cross-cutting query interface that spans entity types (not yet implemented):

```python
# Context queries
get_basin_profile(BasinId) → BasinProfile
get_asset_state(AssetId) → AssetState

# Geometry/physics queries
sample_property(VolumeId, location, property) → Physics9State + uncertainty
get_horizon_depth(HorizonId, location) → float + confidence
get_pressure_at(VolumeId, location) → float + interval

# Uncertainty/risk queries
get_risk_breakdown(PlayId) → RiskBreakdown
get_conflict_list(BasinId) → [Conflict_T]
get_scenario_set(BasinId) → InterpretationSet

# Evidence/provenance queries
get_evidence_for_entity(EntityId) → [EvidencePack]
get_update_history(EntityId) → [Δ_T]
get_interpretation_set(EntityId) → InterpretationSet_T
```

**Status:** Individual tools exist for most of these. The unified query router does not. This is the next engineering milestone.

---

## §6 LLM Interaction Protocol

### 6.1 Principle

The LLM is **not** allowed to "imagine" Earth. It must query GEOX via a governed protocol.

### 6.2 Existing: arifOS Routing Layer

GEOX already operates within the arifOS federation through:
- **Session system:** every tool call is session-bound
- **Floor enforcement:** F1/F4/F7/F9/F11/F13 gates via `floor_enforcement.py`
- **Authority routing:** GEOX is evidence-only — never a policy judge
- **Claim envelopes:** all outputs carry epistemic labels, provenance, risk classification

### 6.3 Existing: Intent Classification (PARTIAL)

GEOX tools are organized by **axis** (observe, verify, reason) but there is no formal intent classification step for LLM query planning.

### 6.4 PROPOSED: Full Protocol

**Step 1 — Intent classification**

LLM receives user request and classifies:
- `intent_type: {CONTEXT, CALCULATION, HYPOTHESIS, DECISION}`
- `required_organs: {GEOX, WEALTH, WELL}`

**Step 2 — Query plan**

LLM generates ordered query plan referencing specific GEOX tools:

```jsonc
{
  "target": "GEOX",
  "queries": [
    { "tool": "geox_basin", "args": { "mode": "profile", "basin_name": "B_MALAY" } },
    { "tool": "geox_petrophysics", "args": { ... } }
  ]
}
```

**Step 3 — Execution**

Query plan is executed by arifOS, not by the LLM directly.

**Step 4 — Synthesis with constraints**

LLM must:
- NOT alter GEOX values
- NOT invent geometry
- NOT upgrade epistemic labels
- NOT suppress uncertainty
- Carry uncertainty bands
- Cite GEOX entities and provenance

**Step 5 — Decision gating**

If the request implies irreversible action, capital commitment, or public disclosure:

```
LLM → arifOS 888_HOLD → human approval
```

**Step 6 — Receipt**

Every LLM answer using GEOX produces a receipt:

```jsonc
{
  "answer_id": "ANS_xxx",
  "geox_queries_executed": ["geox_basin", "geox_petrophysics"],
  "entities_touched": ["B_MALAY", "W_01"],
  "uncertainty_summary": { "max_confidence": 0.85, "min_confidence": 0.3 },
  "authority_scope": "ADVISORY_ONLY"
}
```

**Status:** Steps 1–2 (intent classification + query plan) are NOT YET IMPLEMENTED. Steps 3–6 are partially supported by existing arifOS infrastructure.

---

## §7 Implementation Status Summary

| Component | Status | Lines of code | Path |
|-----------|--------|---------------|------|
| Physics9State | ✅ LIVE | ~180 | `src/geox_core/physics/state.py` |
| Physics parameters (moduli, rock physics) | ✅ LIVE | ~250 | `src/geox_core/physics/parameters.py` |
| Earth Material Catalog (8 lithotypes) | ✅ LIVE | ~60 | `src/geox_core/physics/state.py` |
| ClaimEnvelope (epistemic labels, units, CRS) | ✅ LIVE | ~440 | `src/geox_core/schemas/claim_envelope.py` |
| EarthMemoryEnvelope | ✅ LIVE | ~280 (schema) | `contracts/schemas/earth/` |
| ClaimStateMachine (9 states) | ✅ LIVE | ~180 | `contracts/claim_state_machine.yaml` |
| Provenance schema | ✅ LIVE | ~170 (schema) | `contracts/schemas/earth/provenance.json` |
| EpistemicIntegrity (pLDDT-style) | ✅ LIVE | ~210 | `core/epistemic_integrity.py` |
| 18 canonical MCP tools | ✅ LIVE | ~2600 (server) | `src/geox_mcp/server.py` |
| Well domain (4 tools) | ✅ LIVE | — | `src/geox_mcp/tools/well*.py` |
| Seismic domain (4 tools) | ✅ LIVE | — | `src/geox_mcp/tools/seismic*.py` |
| Basin domain (2 tools) | ✅ LIVE | — | `src/geox_mcp/tools/basin*.py` |
| Geology topology (AdjacencyGraph, ContactRelation) | ❌ | 0 | — |
| Formal uncertainty algebra | ❌ | 0 | — |
| Formal Update_T operators | ❌ | 0 | — |
| InterpretationSet with weights | ❌ | 0 | — |
| Formal Conflict_T model | ❌ | 0 | — |
| Unified query router | ❌ | 0 | — |
| Intent classification + query plan protocol | ❌ | 0 | — |

**Next build priorities (by RSI gap):**

1. **Formal uncertainty algebra** — extend Physics9State with interval/distribution fields. Smallest code change, highest theoretical impact.
2. **InterpretationSet + Conflict_T** — multi-interpretation storage using existing claim infrastructure. Medium build.
3. **Unified query router** — wraps existing 18 tools into typed query interface. Medium build.
4. **Update_T operators** — formal change sets per entity type. Large build.
5. **Intent classification protocol** — LLM-side, touches arifOS routing layer. Depends on 3.

---

## §8 One-Line Closing

> **GEOX is not a geology chatbot. It is a governed Earth physics substrate with an MCP query surface and an epistemic backbone.** The entity model gives it structure. Physics9State gives it physics. The claim system gives it truth discipline. The 18 tools give it query. The gaps above give it a build roadmap.

---

*DITEMPA BUKAN DIBERI — Forged, Not Given.*  
*GEOX Substrate Spec v0.2 · 2026-06-28 · Aligned with Phase 2.1 (18 tools)*
