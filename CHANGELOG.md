## [2026-06-21] — W2-W13+ Multi-Physics Earth Witness FORGE

**Scope:** GEOX 40 → 54 canonical tools. Doctrine layer, foundation model backing engine, nonseismic geophysics + open data, multi-physics joint inversion, federation integration. Live commit `657b9eb0` pushed to `origin/main`.

### Added — Doctrine (W2-W4, Gap X / 3 / 5)
- `geox_doctrine_assumption_register` — Gap X (WAJIB). Track every assumption with `parent_assumption_id`, `rung_origin` (1-7), cascading falsification.
- `geox_doctrine_anti_beautiful_one` — Gap 3 (WAJIB). `beauty_overreach_score = certainty_gradient / grounding_gradient`. Forces decomposition when rhetoric outruns evidence.
- `geox_doctrine_godel_review` — Gap 5 (WAJIB). Runtime hard-stop. Iron Law: lower rungs always beat higher rungs. States: KNOWN / UNKNOWN / UNDECIDABLE_YET / VOID.

### Added — Phase A Foundation Model (W5-W8)
- `geox_prithvi_eo_inference` — Prithvi-EO-2.0 (NASA-IMPACT + IBM, arXiv 2412.02732). 300M/600M param, pretrained on 4.2M HLS time series. Tasks: flood mapping, burn scars, land cover, multi-temporal crop, scene reasoning. Mock backend default; live requires `terratorch` + GPU + 888_HOLD.

### Added — Phase B Nonseismic + Open Data (W9-W12)
- `geox_gravity_magnetic_forward` — HarmonIC (Fatiando) gravity + magnetic forward modeling. Adapters with mock fallback.
- `geox_emag2_ingest` — EMAG2v3 V3 global magnetic anomaly grid fetcher. 228 MB TIFF cached at `/root/.cache/geox/emag2/`. Offline-safe stub default.
- `geox_icgem_models` — ICGEM (GFZ Potsdam) global gravity field model registry (EIGEN-6C4, EGM2008, XGM2019).

### Added — Phase C Multi-Physics Earth Witness (W13+)
- `geox_joint_inversion` — **Strategic centerpiece.** Fuse N modalities (seismic impedance, Vp/Vs, gravity, magnetic, MT resistivity) → one Physics9State per cell. IRLS solver with Earth-bounds clipping.
- `geox_mt_forward` — 1D CSEM/MT forward via Wait's recursion. **Fills the missing ρₑ discipline.**
- `geox_biostrat_constraint` — Biostrat time-facies admissibility. 6 built-in zones.
- `geox_seismic_inversion` — 1D post-stack PINN-style inversion. Recursive impedance + Faust + Gardner.

### Added — Federation Integration (W13+)
- `geox_geomechanics` — K, G, E, ν, AI, Vp/Vs from Physics9State. Sanity-flagged.
- `geox_well_decision_class` — **WELL → GEOX gate.** Reads operator fatigue; returns C1-C5 gating joint inversion. C5 = VOID (HOLD).
- `geox_wealth_feed` — **GEOX → WEALTH feed.** STOIIP + lithology-aware ranking + ADVANCE/DEFER/REJECT verdict.

### Changed
- `src/geox_mcp/registry.py`: CANONICAL_PUBLIC_TOOLS 40 → 54. GEOX_TOOL_MANIFEST 40 → 54.
- `src/geox_mcp/server.py`: `_EXPECTED_CANONICAL = 54` (was 40). 11 new `@mcp.tool(name=...)` decorators.
- `contracts/canonical_registry.py`: synced to 54 tools. Header updated.
- `geox-mcp.service`: restarted (888_HOLD #1). Live canonical_tools = 54.

### Fixed
- EMAG2v3 fetcher URL: updated to current NCEI TIFF endpoint (NC variant 404).
- Module `__init__.py` imports added for new subpackages.

### Added (Docs)
- `docs/MCP_TOOL_REFERENCE.md` — full 54-tool reference.
- `docs/AGENTICS_INTEGRATION.md` — WELL/WEALTH/arifOS federation wiring.
- `docs/PHYSICS9_EARTH_WITNESS.md` — multi-physics joint inversion explanation.

### Tests
- **89 tests passing**, 3 skipped (live-server drift, expected).
- New test files: `tests/test_doctrine_w2_w4.py` (28), `tests/test_adapters_w5_w12.py` (15), `tests/test_phase_c_w13.py` (19), `tests/test_pinn_w13.py` (9), `tests/test_integration_w13.py` (13).

### Constitutional Compliance
- F0: 5/5 registry-truth tests pass.
- F1: All edits reversible; service restart was the only production act, both gated by 888_HOLD.
- F2: Every output carries epistemic_provenance + godel_wall + ml_provenance.
- F4: Registry comment blocks document each forge phase.
- F8: Mock backends for FM + EMAG2v3 — no silent network calls.
- F9: FM adapters raise if terratorch/harmonica missing.
- F13: F13 SOVEREIGN authorized; both 888_HOLDs invoked with full transparency.

### Audit Verdict
- **Architecture clarity:** ✅ strong
- **Constitutional fidelity:** ✅ corrected + extended (Gap X/3/5 closed)
- **Multi-physics depth:** ✅ W13+ FORGE delivers strategic vision centerpiece
- **Publishability:** ✅ ready (push to main done)
- **SOT sync:** ✅ all 3 registries in sync at 54

### Deferred to Next Tranche
- Prithvi-EO-2.0 live weights (requires GPU + ~5GB + 888)
- Bayesian joint inversion (replace IRLS with proper covariance propagation)
- True WELL federation call (currently uses lazy-import stub fallback)
- GENESIS/003 floor realignment to F1-F13

---

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
