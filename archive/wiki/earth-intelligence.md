# What is Earth Intelligence

Earth Intelligence is the discipline of deriving actionable understanding from geospatial data. Unlike traditional GIS, which focuses on storage and visualization, Earth Intelligence emphasizes *inference*—the transformation of raw observation into structured knowledge that can drive decisions.

## Intelligence vs. Data

Data is raw. Intelligence is contextual.

A satellite image is data. The classification of that image into land cover types, the detection of change over time, and the prediction of future states based on historical patterns—that is intelligence.

GEOX operationalizes this through a substrate-aware architecture. We recognize that intelligence flows through multiple mediums: human analysts, machine agents, physical infrastructure, orbital platforms, environmental sensors, and the void spaces where communication breaks down. Each substrate has distinct capabilities, constraints, and failure modes.

> "The map is not the territory, but the territory is not the data either. Intelligence sits in the transformation between them."

## The Substrate Model

GEOX recognizes eight substrates through which intelligence operates:

### Human
Analysts, decision-makers, field operators.
- **Strength**: Contextual judgment, ethical reasoning, creative problem-solving
- **Weakness**: Bandwidth limitations, cognitive bias, fatigue

### Machine-Fixed
Algorithms, models, automated processors on fixed infrastructure.
- **Strength**: Scale, consistency, persistence
- **Weakness**: Edge cases, overconfidence, updates required

### Machine-Mobile
Autonomous systems in motion: drones, vehicles, vessels.
- **Strength**: Dynamic positioning, in-situ sensing
- **Weakness**: Power constraints, communication limits

### Infrastructure
Networks, storage, compute, telemetry backbone.
- **Strength**: Persistence, throughput, reliability
- **Weakness**: Fragility, maintenance requirements, single points of failure

### Orbital
Satellites, constellations, space-based sensors.
- **Strength**: Coverage, revisit frequency, global perspective
- **Weakness**: Latency, cost, vulnerability to interference

### Environment-Field
Physical terrain, atmosphere, hydrology—the operational environment.
- **Strength**: Ground truth, physical reality
- **Weakness**: Unpredictability, hazard, uncontrollable variables

### Celestial
Solar, lunar, astronomical influences on Earth systems.
- **Strength**: Predictable cycles, gravitational reference
- **Weakness**: Long-period cycles, tidal complexity

### Void
Communication gaps, sensor shadows, unknown states.
- **Not absence but presence**: Requires special handling and fallback protocols
- **Critical for resilience**: Systems must function when parts of the substrate are unavailable

Every GEOX skill declares which substrates it operates across. A flood model may ingest orbital imagery (orbital), process on cloud infrastructure (infrastructure), be validated by human experts (human), navigate across unmapped terrain (void)—while explicitly handling void regions where terrain data is missing.

## The 44 Skills / 11 Domains

GEOX organizes its 44 atomic skills into 11 domains:

| Domain | Skills | Focus |
|--------|--------|-------|
| **Sensing** | signal_acquisition, telemetry_link, sensor_calibration, noise_filtering | Data acquisition and quality |
| **Geodesy** | coordinate_transform, datum_alignment, gps_rtk, gravity_model | Position and reference frames |
| **Terrain** | dem_processing, surface_classify, roughness_analysis, slope_aspect | Elevation and land cover |
| **Water** | flood_model, watershed_delineate, drainage_analysis, tidal_model | Hydrology and coastal |
| **Atmosphere** | weather_ingest, atmospheric_correction, climate_trend, storm_track | Meteorology and climate |
| **Mobility** | route_optimize, accessibility_map, traffic_pattern, terrain_navigate | Movement and routing |
| **Infrastructure** | asset_inventory, network_trace, urban_growth, facility_siting | Built environment |
| **Hazards** | seismic_hazard, landslide_susceptibility, volcanic_threat, multi_risk | Risk assessment |
| **Governance** | boundary_verify, rights_mapping, compliance_check, constitutional_gate | Policy and rights |
| **Time** | change_detect, time_series, forecast_model, anomaly_detect | Temporal analysis |
| **Orchestration** | agent_coordination, void_detect, edge_handle, fallback_orchestrate | Multi-agent coordination |

## Observation to Action

The GEOX pipeline follows a canonical flow:

1. **Sense** — Data acquisition from any substrate
2. **Process** — Transformation into analysable form
3. **Understand** — Extraction of patterns and meaning
4. **Decide** — Evaluation of options with constraints
5. **Act** — Execution with monitoring and feedback

Each stage has associated skills. Sensing uses `signal_acquisition` and `telemetry_link`. Processing chains `atmospheric_correction` and `coordinate_transform`. Understanding applies `surface_classify` and `change_detect`. Decision incorporates `multi_risk` and `constitutional_gate`. Action deploys `route_optimize` or `agent_coordination`.

## Intelligence as Composition

Individual skills are atomic. Intelligence emerges from composition.

A flood response mission might compose:
- Sensing: `weather_ingest` for rainfall forecasts
- Processing: `dem_processing` for terrain
- Understanding: `flood_model` for inundation prediction
- Decision: `route_optimize` for evacuation routing
- Action: `agent_coordination` for multi-team response

Each composition is governed. The `constitutional_gate` skill evaluates the full chain against arifOS F1-F13 constraints before execution.

## Quality of Intelligence

GEOX evaluates intelligence quality through multiple lenses:

- **Feasibility** (Physics9): Does this violate physical laws?
- **Uncertainty** (F7): Are confidence bounds explicit?
- **Risk** (κ): What is the risk density of this operation?
- **Coherence** (peace²): Are all parts of the analysis internally consistent?
- **Grounding** (F2): Is every claim supported by evidence?

Intelligence that passes all gates receives an **888 SEAL** verdict and proceeds. Intelligence that fails gates receives **888 HOLD** (for review) or **888 VOID** (for rejection).

This is Earth Intelligence: not just data processing, but *governed transformation* from raw signal to actionable understanding.
