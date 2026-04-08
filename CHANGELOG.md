# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — 2026-04-09

### Added
- **GEOX MCP Apps Architecture**: Complete 6-layer host-agnostic framework.
- **Canonical Contracts**: Defined App Manifest, Host Adapter API, and Event Contract.
- **Petrophysics Engine**: Archie, Simandoux, and Indonesia models with MC uncertainty.
- **Claim Tagging**: Epistemic status tracking (CLAIM/PLAUSIBLE/HYPOTHESIS/UNKNOWN).
- **Agnostic Prompt Pack**: `GEOX_PLATFORM_AGNOSTIC_PROMPTS.md` for cross-agent orchestration.
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
