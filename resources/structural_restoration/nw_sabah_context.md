# NW Sabah Context for Structural Restoration

> **Note:** This file contains NW Sabah-specific tectonic context. The fundamental equations, invariants, and diagnostic guards belong in the generic structural-restoration resources. NW Sabah assumptions must not contaminate other basins.

## Basin Identity

- **Location:** Northern Sabah, East Malaysia
- **Tectonic setting:** NW Borneo collision zone — Dangerous Grounds continental crust underthrust NW Borneo
- **Key feature:** North Sabah–Pagasa Wedge (NSPW) — >500 km syn-collisional, mobile-shale-dominated, sediment-loaded wedge

## Event Stack (ABKSS Framework)

| Phase | ABKSS | Age | Regime | Key Transition |
|-------|-------|-----|--------|---------------|
|1 | ASAS | Paleogene–Early Miocene (40–23 Ma) | Extension | PSCS rifting |
|2 | BEBAS | Oligocene | Extension (reoriented) | Intra-rift reorganisation |
|3 | KAPUR | ~23 Ma (BMU/TCU) | Collision | Dangerous Grounds underthrusting |
|4 | SABAR | ~13–10.5 Ma (DRU) | Post-collisional rebound | Slab detachment (mechanism OPEN: break-off vs drip vs delamination), wedge-top |
|5 | SENJA |10.5–0 Ma | Gravity-driven | Mud canopy, DWFTB |

## Key Unconformities

- **BMU/TCU** (23 Ma) — Collision onset / NSPW base
- **DRU** (13.5–12.5 Ma, Morley 2023; diachronous family) — Wedge-top / slab-detachment response (mechanism OPEN; NOT collision start)
- **UIU** (10.5 Ma) — End of mini-basin development
- **SRU** (~9–8.5 Ma, AGE HOLD — candidates 9.53 top NN9-hamatus / ~8.6 base NN10A; inboard wells validate ~9.4) — Post-canopy burial

## Restoration-Specific Considerations

### Overprinting
Current geometry = rift + post-rift + strike-slip + gravity sliding + compression, all stacked. Single-step restoration risks conflating five distinct mechanisms.

### Basement Heterogeneity
"Top Basement" may include: stretched continental crust, Dangerous Grounds blocks, igneous additions, older structural fabrics. One basement surface ≠ one geological event.

### Mobile Shale
NSPW overpressured shales expelled through pipes and vents → 1900 km² mud canopy. Shale mobility creates accommodation and deformation patterns not explained by tectonic subsidence alone.

### Carbonate Platforms
Nido Limestone growing on Dangerous Grounds platform during syn-rift. Carbonate factory on/off transitions carry tectonic signal.

## Evidence Sources

- Morley et al. 2023 (Geosphere) — NSPW definition, mud canopy, mobile shale
- Morley 2024 (Earth-Science Reviews) — NSPW tectonic synthesis
- Pilia, Rawlinson et al. 2023 (Gondwana Research) — P/S-wave arrival-time tomography: PSCS slab remnant >250 km beneath NW Borneo
- Pilia et al. 2023 (Nature Geoscience, doi:10.1038/s41561-023-01201-7) — post-subduction extension driven by lithospheric drip (mechanism model; break-off vs drip vs delamination remains OPEN)
- Cottam et al. 2013 (JGS) — Kinabalu Granite cooling at 360°C/Myr
- Lunt & Madon 2017 — DRU redating to 13–12 Ma

## Hardcoded Assumptions (HOLD)

The following values from the Dr Shahram exercise are **modelling assumptions, not basin constants**:

- 10 km calibration influence distance — scenario-specific
- 300 m maximum palaeowater-depth uncertainty — scenario-specific
- Linear distance-decay function — one option among several

These must be treated as scenario parameters (SR_INV_011), never hardcoded as NW Sabah truths.
