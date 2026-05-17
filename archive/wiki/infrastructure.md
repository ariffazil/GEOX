# Infrastructure & Built Environment

Infrastructure connects systems and enables operations. Understanding the built environment is critical for resilience and planning.

## Overview

The Infrastructure domain covers four atomic skills:

| Skill | Purpose | Substrates |
|-------|---------|------------|
| `asset_inventory` | Catalog infrastructure assets | machine, human |
| `network_trace` | Trace connectivity | machine |
| `urban_growth` | Model urban expansion | machine, human |
| `facility_siting` | Optimize facility locations | machine, human |

## Asset Inventory

Infrastructure assets include:
- **Transportation**: Roads, bridges, ports, airports
- **Utilities**: Power lines, substations, pipelines
- **Communications**: Towers, fiber, satellites
- **Water**: Dams, levees, treatment plants

### Inventory Approaches

- **Field survey**: Direct measurement and documentation
- **Imagery analysis**: Manual or AI-assisted extraction
- **Integration**: Combine multiple sources
- **Crowdsourcing**: OpenStreetMap, reports

## Network Tracing

Infrastructure networks have:
- **Topology**: Nodes and edges
- **Flow**: Direction of service (water, power, data)
- **Redundancy**: Alternative paths
- **Dependencies**: Cross-sector linkages

### Critical Infrastructure

- **Single points of failure**: Bridges, data centers
- **Cascading dependencies**: Power → communications → water
- **Geographic concentration**: Urban nodes

## Urban Growth Modeling

Cities change rapidly. Growth models predict:
- **Expansion areas**: Where urban will spread
- **Drivers**: Economic, demographic, policy
- **Constraints**: Topography, hazard zones, protected areas
- **Impacts**: Floodplain encroachment, farmland loss

### Modeling Approaches

- **Cellular automata**: Spatial diffusion
- **Agent-based**: Decision-driven growth
- **Econometric**: Land use change models
- **Hybrid**: Combine approaches

## Facility Siting

Optimal facility locations consider:
- **Accessibility**: Distance from users
- **Cost**: Land, construction, operations
- **Constraints**: Zoning, hazard exposure
- **Synergies**: Co-location benefits

### Multi-Criteria Analysis

Weighted overlay of:
- Suitability maps (terrain, land use)
- Distance matrices (to markets, labor)
- Cost surfaces (construction, transport)
- Constraint masks (protected areas)

## Constitutional Constraints

Infrastructure operations must satisfy:
- **F6 Harm**: No siting in hazard zones without mitigation
- **F11 Coherence**: Infrastructure plans consistent with regional strategies
- **F13 Sovereign**: Major infrastructure decisions require public consultation

## See Also

- [Governance & Policy](governance.md) — Rights mapping
- [Hazards & Risk](hazards.md) — Multi-risk assessment
- [Asset Inventory](../../apps/site/skills/asset_inventory.html) — Skill detail
