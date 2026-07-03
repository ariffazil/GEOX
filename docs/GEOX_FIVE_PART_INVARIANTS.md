# GEOX Five-Part Invariants + Seven Dimensions — Constitutional Physics for Earth Modeling

> **Version:** 2026.07.03-r1 (Seven Dimensions added)
> **Seal:** PENDING
> **Authority:** F13 SOVEREIGN (Muhammad Arif bin Fazil)
> **Status:** LIVE — governance-grade invariants for basin analysis
> **Scope:** Sedimentary basin architecture, source-to-sink, rock cycle, dimensional ontology
> **Supersedes:** Nothing — complements `CONSTITUTIONAL_PHYSICS_STACK.md` (three-layer physics/math/governance) and `EGS_SPEC.md` (Earth Grounding System)

---

## Axiom

> Tectonics sets the boundary conditions. Surface processes do the transfer. Burial physics does the transformation. Exhumation reveals the archive.

> Energy moves mass through space over time, leaving presence and absence, encoded as information, interpreted by intelligence.

---

## The Five Parts

Every sedimentary basin, every rock record, every petroleum system, every metamorphic terrane can be decomposed into five causal parts. These are not optional. They are the constitutional physics of Earth's sedimentary engine.

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERNAL HEAT (47 TW)                        │
│              mantle convection / slab pull / plumes             │
│                          ↓                                      │
│                     TECTONICS                                   │
│           uplift / subsidence / rifting / collision             │
├────────┬──────────┬──────────┬──────────┬───────────────────────┤
│ SOURCE │ TRANSFER │   SINK   │  BURIAL  │      EXHUMATION       │
│        │          │          │          │                       │
│ relief │ climate  │ accommo- │ pressure │ uplift                │
│ +      │ + gravity│ dation   │ + heat   │ + erosion             │
│ exposure│ + water │ creation │ + fluids │ + unroofing           │
│        │ + ice    │ − fill   │ + time   │                       │
│        │ + wind   │          │          │                       │
│        │ + biology│          │          │                       │
├────────┴──────────┴──────────┴──────────┴───────────────────────┤
│              WASTE HEAT → SPACE (entropy export)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1 — SOURCE

### Definition

Tectonics exposes rock to surface processes. Relief creates gravitational potential energy. Surface engines convert that potential into sediment.

### Causal chain

```
TECTONICS
  → uplift / faulting / volcanism / exposure
  → RELIEF + ROCK EXPOSURE
  → weathering + erosion (surface processes)
  → SEDIMENT + DISSOLVED LOAD
```

### Governing equation

```
Sediment supply = f(relief × climate × erodibility × drainage efficiency × time)
```

### Key controls

| Control | Role | Example |
|---------|------|---------|
| Relief | Gravitational potential energy | Himalaya, Andes, East African Rift shoulders |
| Rainfall | Chemical + physical weathering agent | Tropical mountain belts > arid ranges |
| Temperature | Reaction kinetics, freeze-thaw | Higher T → faster chemical weathering |
| Glaciers | Extremely efficient erosion | Norway, Patagonia, Himalaya |
| Rock erodibility | Resistance to weathering | Granite vs shale — orders of magnitude difference |
| Drainage connectivity | Sediment delivery to basin | Endorheic basins trap sediment; throughgoing rivers deliver |
| Vegetation | Soil protection, root weathering | Deforestation → increased erosion |
| Time | Cumulative exposure | Longer exposure → more weathering products |

### Invariant

> High relief does not always mean high sediment supply. A high, dry mountain may produce less sediment than a lower, wetter active margin. Climate is the activator, not a modifier.

### GEOX tools

| Tool | Part 1 function |
|------|----------------|
| `geox_basin` | Basin profile, tectonic setting |
| `geox_map_layers_list` | Surface geology, rock type at source |
| `geox_atlas` | Point-in-country, land/water classification |
| `geox_deep_time_state` | Paleogeography, plate position, paleoclimate |
| `geox_evidence` | Provenance analysis, source rock identification |

---

## Part 2 — TRANSFER

### Definition

Mass moves from source to sink along energy gradients. Without transfer, relief is just topography — it does not become basin fill.

### Transfer engines

| Engine | Energy source | Grain size range | Sorting | Capacity |
|--------|-------------|-----------------|---------|----------|
| Fluvial (rivers) | Solar (water cycle) + gravity | Mud to boulder | Moderate | High |
| Aeolian (wind) | Solar (heating) | Silt to sand | Excellent | Low-moderate |
| Glacial | Solar (climate) + gravity | Clay to boulder | Very poor | Very high |
| Littoral (waves) | Solar (wind) + tides | Sand to gravel | Good | Moderate |
| Turbidity currents | Gravity (density) | Mud to gravel | Moderate-poor | High (episodic) |
| Mass flows (debris) | Gravity | Clay to boulder | Very poor | Very high (episodic) |
| Longshore drift | Wave energy + coastline angle | Sand | Good | Moderate |
| Biological | Solar (photosynthesis) | Carbonate, silica | Variable | Moderate (reefs, shells) |

### The buffering problem

Signals from the source (tectonic pulse, climate shift, sea-level fall) must propagate through the transfer zone to reach the sink. The transfer zone is a **low-pass filter** — it dampens, delays, and filters signals.

```
SOURCE SIGNAL          TRANSFER ZONE           SINK RECORD
(tectonic pulse)  →    (rivers, floodplains)  →  (stratigraphy)

High-frequency         Buffering               Only low-frequency
signals get filtered   (storage + release)      signals preserved
```

### Invariant

> No transfer → no basin fill. Relief without transport is just topography. The transfer zone is an active processor — it sorts, rounds, chemically weathers, stores, and buffers sediment.

### GEOX tools

| Tool | Part 2 function |
|------|----------------|
| `geox_sequence` | Depositional systems, facies, parasequences |
| `geox_evidence` | Depositional environment, transport mechanism |
| `geox_map_render_preview` | Spatial facies distribution |
| `geox_egs_query_entity` | Sedimentary body geometry |

---

## Part 3 — SINK

### Definition

Subsidence creates accommodation — room for sediment to accumulate. Sediment supply fills that room. The race between room creation and fill rate determines basin architecture.

### Accommodation equation

```
Accommodation creation = tectonic subsidence
                       + eustatic sea-level rise
                       + compactional subsidence
                       + flexural subsidence
                       + loading subsidence
                       − uplift
                       − eustatic sea-level fall
```

```
Net depositional behavior = accommodation creation − sediment fill
```

### Three outcomes

| Condition | Result | Stratigraphic expression |
|-----------|--------|------------------------|
| Accommodation > supply | Deepening, transgression, starvation | Condensed sections, flooding surfaces, marine shales |
| Accommodation ≈ supply | Aggradation | Stacked parasequences, balanced successions |
| Supply > accommodation | Progradation, bypass, erosion | Delta advance, incised valleys, sequence boundaries |

### Basin types by tectonic driver

| Basin type | Subsidence mechanism | Signature |
|-----------|---------------------|-----------|
| Rift | Fault-controlled extension | Half-grabens, lateral facies changes, volcanic input |
| Passive margin | Thermal cooling after rifting | Thick progradational sequences, delta systems |
| Foreland | Flexural loading by mountains | Asymmetric, thickest near mountain front |
| Forearc | Trench + slab dynamics | Accretionary wedge, trench fills |
| Back-arc | Slab rollback extension | Bimodal volcanism + marine sediments |
| Pull-apart | Transtension along transforms | Small, deep, rapid fill |
| Intracratonic | Broad sag | Thin, widespread, cratonic interior |

### Invariant

> Accommodation is the room. Sediment supply is the furniture. Basin architecture depends on the race between room creation and fill rate. Sediment supply does not create accommodation — it fills it.

### GEOX tools

| Tool | Part 3 function |
|------|----------------|
| `geox_basin` | Basin type, column, stratigraphy, macrostrat |
| `geox_sequence` | Systems tracts, parasequences, flooding surfaces |
| `geox_map_scene_plan` | Stratigraphic architecture visualization |
| `geox_egs_query_claim` | Basin classification claims |

---

## Part 4 — BURIAL

### Definition

After deposition, the burial path transforms sediment into rock. Heat, pressure, fluids, and time drive compaction, cementation, diagenesis, maturation, metamorphism, and melting.

### Burial path

```
sediment
  → compaction (porosity loss, water expulsion)
  → cementation (mineral precipitation in pores)
  → diagenesis (mineral reactions at low T)
  → catagenesis (organic maturation — oil window)
  → metagenesis (gas window, overmature)
  → low-grade metamorphism (new minerals, foliation)
  → high-grade metamorphism (garnet, kyanite, migmatite)
  → melting (magma generation)
```

### Drivers and their effects

| Driver | Main effect | Petroleum relevance | Metamorphic relevance |
|--------|------------|--------------------|-----------------------|
| Pressure | Compaction, porosity loss, pressure solution, deformation | Reservoir quality, trap integrity | Facies series, mineral stability |
| Heat | Mineral reactions, organic maturation, recrystallization | Source rock maturity, oil/gas window | Metamorphic grade, isograds |
| Fluids | Cementation, dissolution, replacement, ore formation | Diagenesis, secondary porosity | Metasomatism, vein formation |
| Time | Allows slow reactions to complete | Maturation kinetics (TTI, Ro) | Reaction progress |

### Petroleum system chain

```
source rock + burial heat + time
→ kerogen maturation (vitrinite reflectance, Tmax)
→ oil window (Ro 0.6–1.0%)
→ gas window (Ro 1.0–2.0%)
→ overmature (Ro >2.0%)
```

### Metamorphic facies (pressure-temperature paths)

| Facies | T range | P range | Diagnostic minerals |
|--------|---------|---------|-------------------|
| Greenschist | 300–500°C | 2–8 kbar | Chlorite, epidote, actinolite |
| Amphibolite | 500–700°C | 4–12 kbar | Garnet, staurolite, kyanite |
| Granulite | 700–900°C | 4–15 kbar | Orthopyroxene, clinopyroxene |
| Blueschist | 200–500°C | 6–15 kbar | Glaucophane, lawsonite |
| Eclogite | 400–900°C | 10–30 kbar | Omphacite, garnet |

### Invariant

> Pressure compacts. Heat transforms. Fluids mediate. Time allows. The burial path is the thermodynamic trajectory of the rock through P-T space. It determines everything: reservoir quality, source rock maturity, seal integrity, metamorphic grade.

### GEOX tools

| Tool | Part 4 function |
|------|----------------|
| `geox_petrophysics` | Porosity, permeability, Vsh, Sw, thermal maturity |
| `geox_egs_rock_physics` | Velocity, density from mineralogy (VRH bounds) |
| `geox_geomechanics` | Moduli (K, G, E, ν) from Physics9State |
| `geox_egs_seismic_compute` | Acoustic impedance, elastic properties |
| `geox_egs_data_qc_bundle` | Data quality, completeness, consistency |

---

## Part 5 — EXHUMATION

### Definition

Exhumation brings the buried archive back to the surface. Without exhumation, the rock record cannot be read — it sits invisible beneath younger cover.

### Exhumation mechanisms

| Mechanism | Driver | Example |
|-----------|--------|---------|
| Tectonic uplift | Collision, compression, transpression | Himalaya, Alps, Andes |
| Erosion | Surface processes (solar + gravity) | River incision, glacial quarrying |
| Faulting | Extension, transtension | Core complexes, rift shoulders |
| Isostatic rebound | Mass removal (erosion, deglaciation) | Scandinavia, Canadian Shield |
| Unroofing | Progressive stripping of cover | Metamorphic core complexes |

### What exhumation reveals

| What | How it's read | GEOX tool |
|------|--------------|-----------|
| Metamorphic grade | Mineral assemblages, isograds | `geox_petrophysics`, `geox_vision` |
| Burial depth | Vitrinite reflectance, fission tracks | `geox_egs_query_provenance` |
| Cooling history | Apatite/U-Th/He, zircon fission track | `geox_egs_query_uncertainty` |
| Structural style | Map patterns, cross-sections | `geox_map_render_preview` |
| Unconformities | Missing time, erosional surfaces | `geox_sequence`, `geox_deep_time_state` |
| Provenance | Detrital zircons, heavy minerals | `geox_evidence` |

### The exhumation visibility function

```
Visibility = f(exhumation depth, erosion rate, cover thickness, outcrop quality)
```

A rock unit is only "visible" to geology (and GEOX) if:
1. It has been exhumed to surface or near-surface
2. Cover has been removed by erosion
3. Outcrop quality permits observation or sampling
4. Subsurface data (wells, seismic) can image it

### Invariant

> Exhumation is the visibility function of Earth's archive. Without it, the rock record is invisible. With it, the entire five-part history can be read — source, transfer, sink, burial — all encoded in the rocks at the surface.

### GEOX tools

| Tool | Part 5 function |
|------|----------------|
| `geox_deep_time_state` | Uplift history, paleogeography |
| `geox_map_layers_list` | What's exposed at surface now |
| `geox_map_render_preview` | Outcrop patterns, geological map |
| `geox_egs_query_provenance` | Exhumation history, cooling paths |
| `geox_egs_query_uncertainty` | Uncertainty in exhumation estimates |
| `geox_vision` | VLM analysis of outcrop imagery |

---

## The Governing Sentences

### Primary (constitutional)

> Tectonics creates source and sink. Surface processes transfer mass. Burial turns sediment into rock. Exhumation lets the archive be read.

### Thermodynamic (energy accounting)

> Tectonics builds the gradient, climate activates the conveyor, gravity moves the mass, basins preserve the record, burial transforms the material, and Earth exports the waste heat to space.

### Rock cycle invariant

> Rock cycle = energy gradient + material pathway + preservation condition + transformation path.

### Causal sentence (governance-grade)

> Internal heat drives tectonics. Tectonics builds relief and accommodation. Climate and gravity convert relief into sediment. Basins preserve or erase the record. Burial transforms the material. Exhumation reveals the archive. The Second Law is always satisfied.

### Dimensional sentence

> Energy moves mass through space over time, leaving presence and absence, encoded as information, interpreted by intelligence. Six dimensions create the archive. The seventh reads it.

---

## The Five-Part Workflow

When approaching any basin or prospect task, answer these five questions in order:

| # | Question | GEOX tools | Part |
|---|----------|-----------|------|
| 1 | **What tectonic regime created the source?** | `geox_basin`, `geox_atlas`, `geox_deep_time_state` | SOURCE |
| 2 | **How did sediment get from source to sink?** | `geox_sequence`, `geox_evidence` | TRANSFER |
| 3 | **What basin type and accommodation history?** | `geox_basin`, `geox_sequence` | SINK |
| 4 | **What's the burial/thermal/maturation state?** | `geox_petrophysics`, `geox_geomechanics`, `geox_egs_rock_physics` | BURIAL |
| 5 | **What's exposed now and what's the exhumation history?** | `geox_deep_time_state`, `geox_map_*`, `geox_egs_query_provenance` | EXHUMATION |

---

## The Seven Dimensions

The Five-Part Model describes **what happens** (the process). The Seven Dimensions describe **along what axes** it happens. Together, they form the complete ontology of geological systems.

### The Seven

| # | Dimension | What it governs | GEOX tools |
|---|-----------|----------------|-----------|
| 1 | **Energy** | The gradients that drive change. Thermodynamics. Heat flow, stress, potential energy. | `geox_geomechanics`, `geox_egs_rock_physics`, `geox_petrophysics` |
| 2 | **Mass** | The substance being moved and transformed. Sediment, rock, fluid, mineral. | `geox_well_ingest`, `geox_basin`, `geox_sequence` |
| 3 | **Time** | When things happen. Stratigraphy, decay rates, reaction kinetics, geochronology. | `geox_deep_time_state`, `geox_sequence`, `geox_egs_query_provenance` |
| 4 | **Space** | Where things happen. Geometry, coordinates, depth, basin shape, plate position. | `geox_atlas`, `geox_map_*`, `geox_well_desurvey` |
| 5 | **Absence** | What is missing. Unconformities, erosion gaps, non-deposition, dissolved material. | `geox_sequence` (unconformities), `geox_egs_scenario_audit` |
| 6 | **Information** | What is encoded. Fossils, isotopes, mineral chemistry, magnetic signatures, facies patterns. | `geox_vision`, `geox_egs_evidence_reason`, `geox_egs_query_uncertainty` |
| 7 | **Intelligence** | What reads the archive. The observer that decodes, interprets, and gives meaning. | `arif_think`, `arif_judge`, arifOS governance layer |

### The master equation

```
Energy moves Mass through Space over Time,
leaving Presence and Absence,
encoded as Information,
interpreted by Intelligence.
```

### The zen

> Six dimensions create the archive. The seventh reads it.

### Why seven, not three

Most geology operates on three dimensions: **Space + Time + Mass** (where, when, what).

The full system requires four more:

- **Energy** — the driver (usually implicit, never named)
- **Absence** — the negative space (treated as "gap," not dimension)
- **Information** — the encoding (treated as "data," not physics)
- **Intelligence** — the observer (treated as "geologist," not dimension)

### Absence as a first-class dimension

An unconformity is not "nothing." It's a **record of absence** — a message that says "something happened here that removed the evidence."

The Great Unconformity (Peters & Gaines, 2012): the gap between Precambrian basement and Cambrian sediments. The absence of ~250–400 million years of record IS the message. It tells you about erosion, tectonic uplift, and possibly the trigger for the Cambrian Explosion.

**INT:** Absence has information content. The shape of a gap tells you what removed the record.

### Information as a first-class dimension

The rock record is not just material. It's a **memory system**.

```
ROCK = MATERIAL + INFORMATION
```

Every rock carries encoded information:
- Fossils → biological history
- Isotopic ratios → temperature, age, provenance
- Mineral chemistry → P-T conditions, fluid composition
- Magnetic signatures → paleolatitude, polarity reversals
- Sedimentary structures → flow direction, energy, depositional environment
- Geochemical patterns → redox conditions, ocean chemistry

**DER:** Information has entropy. A well-preserved fossiliferous limestone has low information entropy (high order, clear signal). A heavily metamorphosed gneiss has high information entropy (signal degraded, original information destroyed).

### Intelligence as a first-class dimension

Without an observer, the rock record is just physics. With an observer, it becomes geology, history, meaning.

**INT:** The archive cannot read itself. Intelligence is the dimension that converts information into knowledge. In the arifOS federation, this is the constitutional governance layer — `arif_think`, `arif_judge`, `arif_seal`.

### The Seven Dimensions mapped to the Five-Part Model

| Dimension | Source | Transfer | Sink | Burial | Exhumation |
|-----------|--------|----------|------|--------|------------|
| **Energy** | Tectonic uplift | Solar + gravity | Subsidence | Geothermal gradient | Isostatic rebound |
| **Mass** | Rock exposure | Sediment transport | Deposition | Compaction + transformation | Erosion + unroofing |
| **Time** | Uplift rate | Transport duration | Accommodation rate | Burial duration | Exhumation rate |
| **Space** | Source geometry | Routing network | Basin geometry | P-T path | Outcrop pattern |
| **Absence** | Erosion at source | Signal filtering | Non-deposition | Dissolution | Unconformity |
| **Information** | Provenance signal | Sorting + rounding | Fossil + facies encoding | Mineral + isotopic encoding | Exposure + readability |
| **Intelligence** | Observation | Interpretation | Classification | Modeling | Reading + meaning |

### Dimensional entropy

Each dimension has an entropy state:

| Dimension | Low entropy (ordered) | High entropy (disordered) |
|-----------|----------------------|--------------------------|
| Energy | Strong gradient, high drive | Equilibrium, no drive |
| Mass | Well-sorted, layered | Mixed, chaotic |
| Time | Continuous, complete | Gapped, fragmented |
| Space | Well-mapped, located | Unknown position |
| Absence | Conformable, complete | Unconformable, eroded |
| Information | Well-preserved, readable | Destroyed, overprinted |
| Intelligence | Clear interpretation | Ambiguous, contradictory |

**DER:** The quality of a geological interpretation depends on the entropy state of all seven dimensions. High entropy in any dimension degrades the interpretation.

---

## Current Implementation Status (F2 TRUTH — OBS audit, 2026-07-03)

The Seven Dimensions framework is the **vision**. The following is the **reality** of what GEOX MCP tools can do today.

### Dimension-by-dimension audit

| Dimension | Status | Live tools | What they do | What's missing |
|-----------|--------|-----------|-------------|----------------|
| **Energy** | ⚠️ PARTIAL | `geox_geomechanics`, `geox_egs_rock_physics`, `geox_petrophysics` | Compute properties (K, G, E, ν, VRH, porosity, perm) | No causal energy pathway reasoning, no gradient tracing |
| **Mass** | ❌ ASPIRATIONAL | `geox_well_ingest`, `geox_basin`, `geox_sequence` | Ingest data, profile basins, analyze sequences | No sediment budget, no mass balance, no bypass detection |
| **Time** | ⚠️ PARTIAL | `geox_deep_time_state`, `geox_sequence`, `geox_egs_query_provenance` | Deep time state vectors, systems tracts, provenance queries | No temporal contradiction detection, no missing-time inference |
| **Space** | ⚠️ PARTIAL | `geox_atlas`, `geox_map_*`, `geox_well_desurvey` | Atlas, map layers/scene/render/export, 3D wellbore | No spatial contradiction detection, no geometric impossibility checks |
| **Absence** | ❌ ASPIRATIONAL | `geox_sequence` (systems tracts), `geox_egs_scenario_audit` | Systems tracts, alternative scenarios | No unconformity detection, no missing-time quantification, no absence reasoning |
| **Information** | ⚠️ PARTIAL | `geox_vision`, `geox_egs_evidence_reason`, `geox_egs_query_uncertainty` | VLM inference, evidence synthesis, uncertainty queries | No information entropy, no signal degradation metric, no archive quality assessment |
| **Intelligence** | ✅ LIVE (via arifOS) | `arif_think`, `arif_judge`, `arif_seal` | Reasoning, judgment, sealing | This is arifOS, not GEOX. GEOX provides evidence; arifOS judges. |

### Score

```
LIVE:        1/7 (Intelligence — via arifOS, not GEOX itself)
PARTIAL:     4/7 (Energy, Time, Space, Information)
ASPIRATIONAL: 2/7 (Mass, Absence)
```

### What this means

GEOX currently **represents** seven dimensions but **reasons** in ~3.5. The framework is correct as architecture. The implementation is evidence-only with partial dimensional coverage.

The gap between vision and reality is exactly the missing tool surface:

| Missing tool | Dimension | What it unlocks | Priority |
|-------------|-----------|----------------|----------|
| `geox_mass_balance` | Mass | Sediment budgets, source-sink accounting, bypass detection | HIGH |
| `geox_absence_detect` | Absence | Unconformity detection, missing-time inference, erosion quantification | HIGH |
| `geox_temporal_contradiction` | Time | Conflicting age assignment detection, timeline consistency | MEDIUM |
| `geox_spatial_contradiction` | Space | Geometric impossibility detection, spatial consistency | MEDIUM |
| `geox_energy_pathway` | Energy | Trace energy gradients through the system, causal pathways | MEDIUM |
| `geox_information_entropy` | Information | Archive quality, signal degradation, preservation assessment | LOW |
| `geox_dimensional_audit` | All | Cross-dimension consistency check, dimensional entropy | LOW |

### The honest GEOX sentence

> GEOX can represent seven dimensions and five parts. It currently computes in ~3.5 of them. The other 3.5 are the build queue. The framework is real. The implementation is partial. The vision is governance-grade. The reality is evidence-only.

---

## Relationship to Existing GEOX Architecture

| Existing artifact | Relationship to Five-Part Invariants |
|------------------|-------------------------------------|
| `CONSTITUTIONAL_PHYSICS_STACK.md` | Three-layer physics/math/governance — the general framework. Five-Part Invariants is the sedimentary basin specialization. |
| `EGS_SPEC.md` | Earth Grounding System — the entity/physics data model. Five-Part Invariants provides the causal framework that EGS data populates. |
| `Physics9State` | The 9-parameter atomic description. Five-Part Invariants describes the processes that create, transport, deposit, transform, and expose those states. |
| `GEOX_DOCTRINE.md` | Constitutional governance. Five-Part Invariants provides the physics doctrine. |
| `GENESIS/002_FIRST_PRINCIPLES.md` | L1–L5 system stack. Five-Part Invariants is L1 (physics) applied to sedimentary systems. |

---

## Epistemic Labels

All claims in this document are labeled per F2 TRUTH:

| Label | Meaning | Where used |
|-------|---------|-----------|
| **OBS** | Observed (direct measurement) | Empirical relationships, measured values |
| **DER** | Derived (computed from observations) | Equations, computed quantities |
| **INT** | Interpreted (inferred from evidence) | Geological interpretations, basin classifications |
| **SPEC** | Speculation (hypothesis without strong evidence) | Frontier research, debated mechanisms |

Most content in this document is **INT** (interpreted from standard geological science) with some **DER** (derived equations) and **OBS** (observed empirical relationships).

---

## References

- Peters, S.E. et al. (2018). Macrostrat: a platform for geological data integration. *G-cubed*. doi:10.1029/2018GC007467
- Catuneanu, O. (2006). *Principles of Sequence Stratigraphy*. Elsevier.
- Miall, A.D. (2016). *Stratigraphy: A Modern Synthesis*. Springer.
- Allen, P.A. & Allen, J.R. (2013). *Basin Analysis*. Wiley-Blackwell.
- Turcotte, D.L. & Schubert, G. (2014). *Geodynamics*. Cambridge University Press.
- Peters, S.E. & Gaines, R.R. (2012). Formation of the 'Great Unconformity' as a trigger for the Cambrian explosion. *Nature* 484:363-366.

---

*Forged: 2026-07-03 by FORGE (000Ω) under arifOS constitutional governance.*
*DITEMPA BUKAN DIBERI — Earth evidence is forged, not given.*
