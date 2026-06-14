# CHANGELOG — GEOX Earth Intelligence

**Format:** [ISO 8601] — summary | details

**Tag convention:** `vYYYY.MM.DD` (forge date, not arbitrary counter)

---

## [2026-06-14] — Doctrine Alignment Release

**Scope:** README overhaul for constitutional fidelity, tool count correction, and epistemic ladder documentation.

### Fixed
- Tool count: **37 → 39** — added missing `geox_las_inspect` and `geox_seismic_segy_inspect` to capability map and table
- Epistemic tags: `FACT / INTERPRETATION / SPECULATION` → canonical `CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN` across all sections
- F1–F13 constitutional table: fully rewritten to match canonical arifOS `000_LAW_v2026.03.07.md` — added Type (HARD/SOFT/DERIVED), Symbols (τ, W₄, P², κᵣ, Ω₀, etc.), threshold values, and GEOfield mappings

### Added
- **Epistemic Ladder section (§6)** — 7-rung ladder from OBSERVED → HUMAN JUDGMENT, with hypothesis scaffolding (evidence_for, evidence_against, expected_additional_signatures, missing_tests), and non-stationary principle
- **Hypothesis scaffolding rules** — every geological claim must carry four companion fields before it is JUDGE-ready
- **Non-stationary language** — models expire, evidence updates re-rank hypotheses, single-well interpretations are candidates, seismic without well tie is hypothesis-layer only
- CHANGELOG.md — this file

### Changed
- All section numbers incremented by 1 (old §6 → §7, old §7 → §8, ..., old §14 → §15)
- Agent rules expanded from 7 to 9 — added hypothesis scaffolding (rule 5) and non-stationary principle (rule 7)
- GEOX NEVER table: F7 and F9 floor references corrected to canonical naming
- Health check example updated to show 39 tools

### Audit Verdict
- **Architecture clarity:** ✅ strong
- **Constitutional fidelity:** ✅ corrected (was ⚠️)
- **Publishability:** ✅ ready
- **SOT sync:** updated via AAA/wiki/log.md

---

## [2026-06-14] — Controlled Release (forge: bffb8d70)

**Scope:** Intelligence Engine + Binary Transport + Skills Architecture.

See `AAA/wiki/log.md` for full release receipt. 10 verification gates passed.

---

## [2026-06-14] — GUI Forge (merge: bffb8d70^1)

**Scope:** Domain3D wireframe rebuild, useMcpTool hook, dual-mode GUI (standalone + iframe).

---

## [2026-06-13] — RenderPayload + Binary Transport (commit: 4f65fcba)

**Scope:** CubeManifest schema, LOD brick streaming, GeoJSON render mode.

---

## [2026-06-12] — RSI Governance Gate (commit: eee73d16)

**Scope:** forge-policy enforcement, claim grammar scanner, llms.txt, CI fix.

---

## [2026-06-10] — LEM Blueprint + Visual Engine (commit: 29320467)

**Scope:** LAS fixture pack, session propagation fix, Large Earth Model roadmap.

---

## [2026-06-06] — SOT Alignment (commit: 58504c58)

**Scope:** Comprehensive README (716 lines), federation contract, CONTEXT, RUNBOOK, AGENTS fix.

---

## [2026-06-04] — Vision AI + Analog Atlas (commits: ed02e163, eb038ba6)

**Scope:** MiniMax VLM adapter, vision calibration, analog atlas framework, 14 test fixes.

---

## [2026-05-26] — GENESIS Doctrine (commit: eee73d16^~)

**Scope:** Constitutional founding charter (4 GENESIS documents), kill map, first principles.

---

*See `git log --oneline --all` and `/root/AAA/wiki/log.md` for full history.*
