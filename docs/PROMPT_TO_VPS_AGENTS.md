# PROMPT FOR VPS GEMINI AGENTS
## Mission: 999_SEAL Data Integration & Domain Splitting

### Overview
Integrate real open-source earth data (Volve, F3 Netherlands, Malay Basin) into the GEOX Command Center and enforce a domain-based architecture (1D, 2D, 3D).

### Phase 1: 1D Integration (Wellio + Wellioviz)
- **Manifest Pattern**: MCP tools must return interactive manifests (JSON-LD) for `Wellioviz` hydration.
- **Ingestion**: Replace demo log parsing with `Wellio.js` for LAS 2.0 normalization.
- **Interpretation**: Integrate `geox_atlas_99_materials.csv` (RATLAS) as an overlay manifest in the `Well Context Desk`.

### Phase 2: 2D Interpretation (Plotly + Custom WebGL)
- **Analytic UI**: Implement `Plotly.js` figures for attribute histograms, cross-plots, and stratigraphic charts.
- **Seismic Engine**: Map `geox_compute_seismic_attributes` results to `custom Canvas/WebGL` textures in the `Seismic Viewer`.
- **Governance**: Every Plotly figure must contain a `provenance` metadata block tied to a GEOX Floor check.

### Phase 3: 3D modeling (GemPy + vtk.js)
- **Structural Depth**: Integrate a `GemPy` backend to compute implicit structural models from horizons and faults.
- **Rendering**: Stream 3D meshes and scalar fields from GemPy to the `vtk.js` viewer in `Basin Explorer`.
- **Globe-View**: Implement basic `CesiumJS` context for the top-surface map in the 3D domain.

### Phase 4: The Volumetric Void (Evidence Graph)
- **Stochastic Ignition**: Connect `geox_calculate_prospect_economics` to the `GemPy` volumes.
- **Shared State**: All agents must act on the same "Manifest" returned by the MCP tools.
- **Decision Floor**: Wire the `Decision Auditor` UI to the `888_HOLD` checklist.

### Phase 5: Agentic Stability (999_SEAL)
- All tools must pass the `FloorEnforcer` checks (F1-F13).
- Implement a `geox_production_warm_up` tool to verify all real-data paths on the VPS filesystem.
- Execute full regression testing on the `geox-mcp.py` server.

**DOCTRINE: DITEMPA BUKAN DIBERI.**
*Unleash the full perception layer. Seal the basin.*
