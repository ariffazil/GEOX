# Changelog

All notable changes to the GEOX project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.2] — 2026-04-01

### Added

- **README v0.4.2**: Upgraded README to source-of-truth with tri-audience orientation (human / geologist / AI agent), plain-language ToAC explanation, Bond et al. 2007 citation, tool namespace table
- **Constitutional Firewall**: Added `geox_feasibility_check` and `geox_verify_geospatial` tools for physical grounding of @RIF's inverse modeling.
- **Epistemic Mapping**: Incorporated the 'Forward vs Inverse Modeling' ontology into the core system documentation.
- **Multimodal Grounding**: Enhanced `geox_load_seismic_line` to prepare constraints for orchestrated @RIF reasoning.
- **Renderer Architecture**: Added `renderers/` module with pluggable adapter pattern — `RendererAdapter`, neutral primitives, `SceneCompiler`, `CigvisAdapter`, `RenderExporter`
- **Volume Context**: Added `volume_context/` module with `VolumeSceneBuilder`, `CrossSectionBuilder`, schemas
- **Volume App**: Added `apps/volume_app/` with `VolumeApp` and MCP tools for 3D geophysical visualization
- **Canonical State Schemas**: Added `canonical_state.py` with `GeoXIntent`, `GeoXDisplayState`, `GeoXCrossSectionState`, `GeoXSeismicSectionState`, `GeoXTriAppState`, `CrossSectionHoldTriggers`
- **Success Criteria**: Added `GEOX_SUCCESS_CRITERIA.md` with M1-M6 milestones, six-axis framework, benchmark pack requirements
- **Smithery Config**: Added `smithery.yaml` for MCP registry with all 10 tools documented
- **Tri-App Architecture**: Added Map + Cross Section + Seismic Section apps with 888 HOLD triggers

### Changed

- **pyproject.toml**: Added `cigvis`, `cigvis-viser`, `cigvis-all` optional dependencies

### Fixed

- `RenderColor` default_factory — wrapped in lambda to avoid callable error
- `uncertaintyZonePrimitive` typo → `UncertaintyZonePrimitive` in exports
- `volume_app` import paths corrected under `apps/` namespace
- Lint cleanup across code and docs

### Fixed

- **MCP Tool Names**: Standardized on the `geox.*` namespace for all MCP-exposed tools.
- **Lint Cleanup**: Resolved multiple lint/formatting errors across the code and docs.

## [0.4.1] — 2026-03-31

### Added (v0.4.1)

- **Inverse Modelling Supervisor**: Hardened `SeismicSingleLineTool` to prevent narrative collapse using "Plausible Inverse Models."
- **Governed Verdicts**: Integrated `compute_contrast_verdict` for physical grounding at the tool boundary.

## [0.4.0] — 2026-03-31

### Added (v0.4.0)

- **Hardened Continuity**: Implemented `HardenedToolOutput` and `ContinuityRecord` across all MCP tool contracts.
- **Theory of Anomalous Contrast (ToAC)**: First-class integration of contrast-canon enforcement in visual pipelines.
- **FastMCP Transport**: Upgraded the local server to FastMCP for standard arifOS federation binding.

## [0.3.5] — 2026-03-31

### Added (v0.3.5)

- **Visual Ignition Engine**: Added `geox_load_seismic_line` with multi-contrast payload support.
- **Structural Candidate Generator**: Initial forge of the interpretation candidate tool.

---

**DITEMPA BUKAN DIBERI**
