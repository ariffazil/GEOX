# PHASE-0 Reality Scan — CLOSE_VENDOR_GAP_RM5.96M

**Date:** 2026-10-14 · **Author:** 333-AGI (session SEAL-1a9debdbe7ad4f10) · **Mode:** read-only, no code changes
**Mission:** M1 Restoration · M2 FSM · M3 PSM · M4 Trap Charge — governed integration
**Status:** COMPLETE. 5 deliverables below. All claims OBS unless labeled DER/INT/SPEC.

---

## 1. Repository Capability Inventory (per mission engine)

### M1 — Structural Restoration: **FORGED BUT DORMANT** (4 artifacts exist, not activated)

| Artifact | Path | Size | Status |
|---|---|---|---|
| LoopStructural adapter | `src/geox_core/engines/geospatial/loopstructural_adapter.py` | 228 L | EXPERIMENTAL, fail-closed on ImportError, sha256 param receipts |
| Native engine package | `src/geox_core/engines/structural_restoration/` | ~1166 L | state.py(388), validate_inputs.py(304), accommodation_diff.py, basement_subsidence.py, fill_ratio.py, invariants.yaml |
| Registry | `src/geox_mcp/registry/structural_restoration_registry.yaml` | 9 tools | `status: PLANNED` — "not LIVE until compute engines are wired to MCP surface" |
| MCP wiring | `src/geox_mcp/tools/structural_restoration/wiring.py` | 16 KB / 9 tools | Header: "PLANNED — wired but not yet connected to tools_wiring.py" |
| Parity checker | `scripts/check_structural_restoration_parity.py` | 121 L | **LIVE RUN 2026-10-14: VERDICT FAIL, exit=1** — all 9 expected tools absent from tools_sot.yaml |
| Git lineage | commit `4cb34c5b` "feat(structural-restoration): new engines + ontology + registry + prospect improvements" | — | single forge commit 2026-09-14 era |

**M1 metadata drift (3-way conflict, must fix before activation):**
- Adapter docstring claims license "LoopStructural (Loop3D / CC-BY)" — PyPI OBS: **MIT** (v1.8.2)
- Adapter docstring: `Requires: loopstructural>=2.0.0` — `service_registry.py` AdapterEntry: `library_version=">=1.0"`
- AdapterEntry `canonical_tools=["geox_subsurface_model"]` — that tool is NOT on the 27-tool public surface → adapter currently contributes to zero public capability

**pynoddy:** ABSENT (0 traces in src/, manifests). PyPI metadata self-conflicts (license string "GPL" vs classifier "MIT"). Mission already mandates isolated-process-only → subprocess boundary regardless.

### M2 — Forward Stratigraphic Modelling: **NATIVE PARTIAL + VENDOR ABSENT (0/4 engines)**

Native physics-first engines already forged (2026-07-03 "extinction event" lineage), cover 1D/process accommodation & routing — NOT full landscape-evolution meshes:
- `engines/stratigraphy/accommodation.py` — McKenzie(1978) tectonic + eustasy + Airy loading + Athy compaction
- `engines/stratigraphy/sediment_routing.py` — slope transport, partitioning, avulsion, turbidite/fan
- `engines/stratigraphy/sequence_emergence.py` + `surface_first.py` — sequences/surfaces emerge from physics

Vendor adapters: **pyBadlands, goSPL, Landlab, fastscape — 0 traces** in src/, tools_sot.yaml, tools_manifest.yaml.

### M3 — Petroleum System Modelling: **NATIVE BACKBONE PRESENT — CALIBRATION GAP**

Present (native, no vendor wrapper needed for backbone):
- `engines/basin/thermal_maturity.py` — EasyRo (Sweeney & Burnham 1990), TTI (Lopatin 1971), burial+gradient
- `engines/basin/backstrip.py`, `mass_balance.py`, `model_comparison.py`, `claim_graph.py`
- `geox_core/core/basin_charge.py` — BasinChargeSimulator (charge_probability, vault_receipt in output)
- `geox_core/source_rock/parameters.py`; surface: `geox_basin` umbrella (`petroleum_system` mode + `basin_engines/thermal_tool.py`)

Gap (grep-verified): **0 hits** for BHT / measured-Ro calibration loop. pybasin/warmth/OGS: 0 traces.

### M4 — Trap Charge Analysis: **SCATTERED PARTIAL — ENGINE ABSENT (gap self-witnessed)**

Present: `geox_core/geology/fault_seal.py`, BasinChargeSimulator (trap/charge timing), `tests/test_basin_charge_wave2.py`, `tests/test_prospect_trap_validity.py`.

**The surface itself witnesses the gap** — `src/geox_mcp/tools/prospect.py:572`:
```
"upgrade_requires": ["carrier_bed_refs", "structural_dip_map", "fill_spill_points"],
"shadow_scoring_available": False
```
No closure, fetch-area, fill-spill, or charge-history engine exists anywhere in the repo.

---

## 2. Tool Dependency Graph (canonical chain)

```
surface_manifest.py (public_tool_names / internal_tool_names / compat_tools)
  → registry.py: GEOX_VERSION + GHOST_TOOLS filter (24 ghosts)
      SURFACE_TOOLS = public − ghosts = CANONICAL_PUBLIC_TOOLS  [27 tools]
  → generated surfaces (generate_all_surfaces.py, regen 2026-10-13):
      tools_manifest.yaml (2390 L) · tools_sot.yaml (381 L, sot_source: registry.py truth)
      · tools.json · GEOX_MCP_APPS_SURFACE.json · CANONICAL_PUBLIC_SURFACE.json
  → tools_wiring.py (7631 L, auto-generated from server.py) imports CANONICAL_PUBLIC_TOOLS
  → server.py (_safe_forward, _geox_annotations) → tools/_register.py
      (FastMCP mount, Evidence-Contract envelope, floor_enforcement, GEOX_RISK_MAP)
  → tool impl (src/geox_mcp/tools/*.py) → engines (geox_core/engines/*) → 13 adapters
  → parity: geox_core/parity/runtime_matrix.py (fastmcp vs vps) + check_structural_restoration_parity.py
```

**Surface count discipline:** known failure class — "31-target phantom retired 2026-10-03 — kept surface_attestation permanently SURFACE_COUNT_DRIFT". Every surface mutation must regen ALL generated surfaces from registry.py truth in one pass.

---

## 3. Existing Adapter Audit (service_registry.py — 13 AdapterEntries)

bruges · devito · pylops · pygeopressure · harmonica · simpeg · pygimli · igrf(ppigrf) · gplately · gplates_ws(gwspy) · gempy · **loopstructural** · flopy

AdapterEntry fields today: `adapter_name, library_name, library_version, canonical_tools, status(EXPERIMENTAL|STABLE|DEPRECATED|CALIBRATION_REQUIRED), acrisk(QUALIFY|ADVISORY|HOLD|BLOCK), requires_888_hold, calibration_notes, replaces, replaced_by`.

**RULE-03 GAP: AdapterEntry has NO `license_type` / `execution_mode` / `isolation_required` fields.**
Mission requires every adapter to declare these. Fix = additive schema extension with backward-compatible defaults; then backfill 13 existing entries (licenses via PyPI verification, GPL ones marked subprocess-bound).

**loopstructural_adapter finding:** EXPERIMENTAL / acrisk ADVISORY / requires_888_hold=False; 3-way metadata drift (license, version constraint, canonical_tools pointing at non-public tool). Engine package + registry + wiring are structurally sound; the dormancy is a single integration hop (`tools_wiring.py` does not import the wiring module).

**License inventory (target vendor engines, PyPI JSON API, OBS 2026-10-14):**

| Engine | PyPI license | Rule-03 lane | Confidence |
|---|---|---|---|
| LoopStructural | MIT (v1.8.2) | library import allowed | OBS |
| goSPL | GPL-3.0 | **subprocess boundary required** | OBS |
| fastscape | BSD-3-Clause | library import allowed | OBS |
| pynoddy | conflicting ("GPL" string vs "MIT" classifier) | subprocess (mission mandate) | OBS-conflict |
| pybasin | GPL-3.0-or-later (v0.2.0) | subprocess — **identity UNVERIFIED (name-collision risk; confirm this is the intended PSM engine before any wiring)** | OBS+UNKNOWN |
| warmth | license field EMPTY | **fail-closed: no import, no vendor until license known** | UNKNOWN |
| pyBadlands | not on PyPI (fetch failed) | upstream repo reports LGPL-3.0 | DER 0.80 |
| landlab | PyPI license field empty | upstream repo reports MIT | DER 0.85 |
| OGS (OpenGeoSys) | not probed | mission: later phase | UNKNOWN |

555-ASI must license-audit (repo LICENSE files, not PyPI strings) before any M2/M3 vendor wiring. pyBadlands is effectively unmaintained and goSPL is its successor-family engine (INT) — factor into M2 engine choice.

---

## 4. Surface Impact Assessment

- Canonical public = **27 tools** (tier A15/B11/C1). EXTEND umbrellas already public: `geox_basin`, `geox_model`, `geox_prospect`. NEW tools `geox_structure_restore` / `geox_strat_forward` → 27→29.
- M1 activation options:
  - **(a) Activate as designed:** connect `register_structural_restoration_tools(mcp, ...)` in tools_wiring.py → 27→36 public tools. Registry yaml + parity checker EXPECTED_TOOLS already specify these 9 names. Minimal mutation, zero new files.
  - **(b) Umbrella consolidation:** new `geox_structure_restore` with 9 modes → 27→28. Matches RULE-02 umbrella-first, but requires rewriting registry yaml + parity checker + wiring (3 file mutations instead of 1) to rename tools that already exist in artifacts.
  - Tension flag: RULE-02 (umbrella) vs RULE-01 (reuse artifacts as-is). This is a **surface-shape decision → 888-APEX** per stream assignment. Recommendation (INT): option (a) for Phase-1 (smallest diff, reuses all four forged artifacts verbatim), umbrella consolidation deferred as cosmetic pass if surface pressure demands.
- M2 vendor adapters are genuinely new files (0 to reuse) — justified; put them under `geox_core/engines/stratigraphy/` or `geospatial/` following `loopstructural_adapter.py` pattern, expose via `geox_strat_forward` umbrella + EXTEND `geox_basin`/`geox_model`.
- M3: extend `engines/basin/thermal_maturity.py` + `basin_engines/thermal_tool.py` + `geox_basin` modes. ChargeResult schema → `src/geox_core/schemas/` or `geox_mcp/contracts/` (follow existing schema conventions).
- M4: extend `geox_prospect` (closure / fetch_area / fill_spill modes) + `RiskBundle` schema. The `upgrade_requires` declaration in prospect.py is the exact extension point.

---

## 5. Recommended Mutation Sequence

**PHASE-1 (M1 — highest reuse, all artifacts exist):**
1. 555-ASI: license verify LoopStructural repo LICENSE (PyPI says MIT) — closes the CC-BY/MIT drift.
2. 333-AGI: fix adapter docstring license + unify version constraint (`>=2.0.0` vs `>=1.0`) — pick one, update both docstring and AdapterEntry.
3. 333-AGI: extend AdapterEntry with RULE-03 fields (additive, defaults for backfill); backfill all 13 entries.
4. 888-APEX: authorize surface shape (option a 9-tool activation vs option b umbrella).
5. 333-AGI: connect wiring into tools_wiring.py → regen all surfaces (generate_all_surfaces.py) → run check_structural_restoration_parity.py to PASS → venv pytest suite (geox-backend-development skill runbook).
6. Hardening: CHAMBERLIN ≥3 competing restoration models enforcement check in state.py/validate_inputs.py; fail-closed paths verified.

**PHASE-2 (M3 — native backbone, calibration is the gap):**
1. Ro/BHT calibration loop into thermal_maturity.py / thermal_tool.py (measured Ro + BHT → calibration_witness reuse).
2. ChargeResult schema (claim_state / assumptions / limitations / reversal_conditions / provenance / receipt_id per RULE-04).
3. pybasin/warmth: **BLOCKED** pending 555 license+identity audit (fail-closed). OGS deferred per mission.

**PHASE-3 (M2 — new vendor adapters, justified by 0/4 existence):**
1. fastscape (BSD, import) + landlab (MIT pending verify, import) adapters; goSPL (GPL, subprocess wrapper); pyBadlands SKIP pending justification vs goSPL successor (INT).
2. HDF5 contracts + subprocess isolation per RULE-03; `geox_strat_forward` umbrella; ≥3 competing scenarios (RULE-05).

**PHASE-4 (M4 — new engine, gap self-witnessed by prospect.py):**
1. trap-charge engine (closure, fetch-area, fill-spill, charge history) reusing BasinChargeSimulator + fault_seal.py.
2. `geox_prospect` mode extensions + RiskBundle schema; ≥3 charge pathways (RULE-05); never preferred_model, never self-seal.

**PHASE-5:** end-to-end chain Restoration → FSM → PSM → Trap Charge → claim ledger; no implementation before Phase-1..4 receipts.

---

## Risks & Flags

- **AdapterEntry lacks RULE-03 fields** — fix schema before any new adapter lands, else every adapter inherits the gap.
- **Vendor license metadata is PyPI-string-grade, not legal-grade** — landlab/warmth empty, pynoddy conflicting, pybasin identity unverified. 555-ASI audit is a hard gate, not a formality.
- **Surface count drift failure class is documented in-repo** — every surface mutation must be a single-pass regen from registry.py truth.
- **`resources/basins/kinabalu/` is untracked in git** (basin_profile.yaml, claims.json, tectonic_history.md) — pre-existing uncommitted work, flagged, untouched.
- **Kernel substrate DEGRADED** (built≠deployed commit drift at arifOS :8088) — advisory; does not affect read-only PHASE-0, reconcile before deployment-gated phases.
- **Bridges file-lock:** `geox_core/adapters/` currently holds only wealth_bridge; mission's "adapters/" convention lives in `service_registry.py` — new adapters belong in `engines/<domain>/*_adapter.py` + a service_registry entry. Do not create a parallel adapter dir.

**PHASE-0 verdict: inventory COMPLETE. No implementation authorized yet. First mutation = PHASE-1 step 1 (license verify), gated by 888-APEX on surface shape (step 4).**
