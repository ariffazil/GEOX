# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2026.05.01] - 2026-05-01
### Added
- **Temporal Earth Dating**: Rebranded versioning to reflect aging earth date (2026.05.01).
- **Sovereign 13 Surface**: Consolidated 49 fragmented endpoints into 13 canonical tools.
- **Epistemic Anchorage**: Versioning now reflects planetary time, grounding the kernel in geological reality.
- **Alias Bridge**: Support for 40+ legacy names with `_meta.deprecation` metadata.
- **Fail-Closed Auth**: Server now aborts if `GEOX_SECRET_TOKEN` is missing.
- **LoopStructural Integration**: Implicit 3D modeling for `geox_subsurface_generate_candidates`.
- **Ensemble Petrophysics**: Min/Mid/Max Sw/Phi realization logic for Wells.
- **Hardened Health**: Non-empty `/health`, `/ready`, and `/status` endpoints.

### Changed
- **Entrypoint**: Unified at `control_plane/fastmcp/server.py`.
- **Registry**: Consolidated at `contracts/tools/unified_13.py`.
- **Manifests**: All 11 MCP App manifests updated to canonical tool names.
- **Naming Grammar**: Shifted to `geox_<domain>_<action>_<object>` underscores.

### Deprecated
- Legacy dotted names (e.g. `geox_well.compute_petrophysics`).
- Pre-refactor underscore names (e.g. `geox_well_qc_logs`).
- Removal scheduled for 2026-06-01.

### Security
- F1_AMANAH Compliance: Process fails closed on missing secrets.

### Migration Notes
- UI components must be updated to reference the new `primary_artifact` envelope.
- Check `llms.txt` for the updated agent reasoning map.
## [v2026.05.12] - 2026-05-12
### Added
- **ToAC v1 Perception Bridge**: `perception_class`, `evidence_tag`, `canon_9_touched`, `vertical_trend`, `litho_class`, `strat_standard` fields across all 16 tool output schemas.
- **EARTH.CANON_9 State Vector**: Nine invariant subsurface quantities (ρ, Vp, Vs, ρₑ, χ, k, P, T, φ) with `CANON9_TOOL_MAP` declaring tool-level dependencies.
- **Biostratigraphy Parsing**: `kernel/_biostrat.py` — NN zone parsing (regex + GPTS2020 lookup), GDE mapping (12-rule vocabulary), lithology classification. Exported via `_helpers.py` shim.
- **GDE Trend Mode**: `geox_section_interpret_correlation` gains `mode="gde_trend"` — 3-bin sliding window vertical paleoenvironment trend from GDE index stacks. Same algorithm as Kinabalu Basin 10 m biostrat workbook.
- **Strat Standard Parameter**: `geox_section_interpret_correlation` accepts `strat_standard` dict (scheme + reference_chart URI) for NN-anchored correlation.
- **MCP Completions Capability**: Declared `"completions": {}` for argument autocompletion support.
- **GDE Vocabulary and CANON_9 Discovery**: `geox://identity` resource now exposes `canon_9.tool_map`, `gde_vocabulary`, `strat_standards`, and `toac_version: "v1"`.
- **Schema Version Bump**: Universal output contract now `geox-output-v0.7`.

### Security
- All new fields flow through existing F2 Truth (enforce_claim_state) and F7 Humility (evidence_tag) gates.

---

⬡ DITEMPA BUKAN DIBERI — 999 SEAL ALIVE ⬡
