# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] — 2026-04-08  Phase B Petrophysics MCP Tools

### Added
- **`geox_select_sw_model`** — Sw model admissibility evaluation (Archie / Simandoux / Indonesia) with log QC flag analysis; raises explicit `PetrophysicsHold` on poor QC.
- **`geox_compute_petrophysics`** — Full property pipeline (Sw, PHIe, BVW) with optional Monte Carlo uncertainty bands; enforces F7 Humility; HOLD on physically impossible results (Sw > 1.0, PHI ≤ 0).
- **`geox_validate_cutoffs`** — CutoffPolicy application: classifies interval as pay / non-pay / marginal; returns `POLICY` provenance tag and list of failed cutoffs.
- **`geox_petrophysical_hold_check`** — 888_HOLD floor scanner for F2/F4/F7/F9 compliance; returns `PetrophysicsHold` with hold_id, severity, and remediation steps.
- **`arifos/geox/schemas/petrophysics_schemas.py`** — 7 new Pydantic v2 schemas: `LogQCFlags`, `SwModelAdmissibility`, `PetrophysicsInput`, `PetrophysicsOutput`, `CutoffPolicy`, `CutoffValidationResult`, `PetrophysicsHold`.
- **`tests/test_petrophysics_tools.py`** — 36 pytest tests (14 schema unit + 22 async MCP integration), all passing.
- Provenance tag system: RAW → CORRECTED → DERIVED → POLICY pipeline applied across all new tools.
- `smithery.yaml` updated to v0.6.0 with all 11 tool entries registered for Smithery registry.

### Changed
- `GEOX_VERSION` bumped `0.5.0` → `0.6.0`.
- `pyproject.toml` version bumped to `0.6.0`.

### Fixed
- FastMCP 3.x `ToolResult` return type: tests use `_sc()` helper to extract `structured_content` safely across 2.x/3.x.

### Security
- F13 Sovereign: `PetrophysicsHold` with `severity == "block"` always sets `requires_human_signoff=True` (Pydantic model_validator enforced).
- F9 Anti-Hantu: shaly-sand models (Simandoux / Indonesia) reject inputs with `rsh_ohm_m=None` at schema validation time.

---

## [Unreleased] — 2026-04-09

### Added

- **GEOX MCP Apps Architecture**: Complete 6-layer host-agnostic framework.
- **Canonical Contracts**: Defined App Manifest, Host Adapter API, and Event Contract.
- **Petrophysics Engine**: Archie, Simandoux, and Indonesia models with MC uncertainty.
- **Claim Tagging**: Epistemic status tracking (CLAIM/PLAUSIBLE/HYPOTHESIS/UNKNOWN).
- **Agnostic Prompt Pack**: Agnostic Orchestration Prompts for cross-agent coordination.
- **Karpathy-Style Wiki**: Established the `wiki/` directory foundation for deep theory/physics memory.

### Changed

- Refactored `geox_mcp_server.py` to include governed petrophysical tools.
- Updated `prefab_views.py` with physical grounding surfaces (Petrophysics View).
- Unified documentation suite (README, LLM_WIKI, CHANGELOG, TODO, ROADMAP).

### Fixed

- Pydantic schema validation for `PetrophysicsOutput`.
- Tool return type compatibility for FastMCP 3.x.

### Security
- Implemented **888_HOLD** triggers for unphysical petrophysical results ($Sw > 1.0$).
- Defined explicit security boundaries for host-app JSON-RPC communication.

---

*DITEMPA BUKAN DIBERI — Forged, Not Given*
