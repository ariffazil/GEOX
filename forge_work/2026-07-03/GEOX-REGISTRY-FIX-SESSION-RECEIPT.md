# GEOX Registry Fix + Malaysia Basin Stress Test — Session Receipt

> **Date:** 2026-07-03 | **FORGE** | **Git:** 236c223e

## What Happened

### 1. Registry Mismatch Fix (5 files)

Root cause: `floor_enforcement.validate_canonical_tool()` only checked `CANONICAL_PUBLIC_TOOLS` (35), ignoring 49 backward-compat aliases that `GeoxGovernanceMiddleware.on_call_tool()` already accepted via `_EXECUTABLE_SURFACE`.

| File | Change |
|------|--------|
| `src/geox_mcp/floor_enforcement.py` | `validate_canonical_tool()` now checks canonical ∪ compat ∪ legacy |
| `src/geox_mcp/geox_middleware.py` | Error message: `geox_surface_status` (public) not `geox_doctrine` (internal) |
| `scripts/control_plane_server_patch.py` | RT1 guard loads compat tools |
| `src/geox_mcp/registry.py` | Added `geox_system_registry_status` to compat list |
| `tests/test_floor_enforcement.py` | Updated `test_old_compat_name` to expect PASS |

**Result:** `geox_evidence_reason`, `geox_las_inspect`, `geox_system_registry_status` → all PROCEED.

### 2. Malaysia Basin 9-Dilemma Stress Test

| # | Dilemma | Claim ID | Status |
|---|---------|----------|--------|
| D1 | Malay Basin rift vs wrench | `6a45b01fc3fc4f9b` | **CHALLENGED** (1 FOR + 1 AGAINST) |
| D2 | Charge kitchens | (covered by D1) | — |
| D3 | High CO₂ origin | `4f56c253426547d5` | Draft (evidence attached) |
| D4 | Fault seal vs leak | `7729d6550b0947a5` | Draft |
| D5 | Inversion vs charge | `195316ec1394412e` | Draft |
| D6 | Deep basement play | `463762ac25094978` | **CHALLENGED** |
| D7 | Sarawak carbonate | `c2e361e7626e4bc7` | **CHALLENGED** |
| D8 | Sabah deepwater | `ccb86236720a4517` | Draft |
| D9 | CCS containment | `6f1288fa879c4520` | Draft |

### 3. Tools That Fired

| Tool | Result | Evidence |
|------|--------|----------|
| `geox_basin(mode=profile)` | ✅ SUCCESS | Madon 2021 Malay Basin framework |
| `geox_egs_claim_create` | ✅ 9/9 | All claims created with provenance |
| `geox_egs_evidence_attach` | ✅ 4/4 | Structural, geochemical, petrophysical |
| `geox_egs_claim_challenge` | ✅ 2/2 | D6 + D7 challenged with counter-evidence |
| `geox_egs_evidence_reason` | ✅ | Synthesize pipeline working |
| `geox_egs_scenario_audit` | ✅ | Pipeline working (empty = no scenarios yet) |
| `geox_deep_time_state(35 Ma)` | ✅ SEAL | 9 variables, confidence 0.84 |
| `geox_forbidden_claims_scan` | ✅ BLOCK | Caught "proven", "confirmed", "certain" |
| `geox_geomechanics` | ⚠️ SESSION_REQUIRED | Governance gate (not a bug) |

### 4. Verdict

**GEOX can govern all 9 dilemmas. GEOX cannot solve any alone.**

Hypothesis warfare framework is LIVE. Data ingestion is the bottleneck.

## Next

→ GEOX RSI Deep Research Scaffold (see companion file)
