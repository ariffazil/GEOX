# GEOX-AUDIT-FIX-002 — Tool Domain Manifest Remediation

**Action ID:** GEOX-AUDIT-FIX-002
**Type:** Registry metadata correction
**Severity:** LOW (metadata only, no functional change)
**Status:** COMMITTED + LIVE ✅
**Date:** 2026-06-28
**Author:** FORGE (000Ω)
**SOT:** `geox-2065d17d`

---

## What Was Wrong

`geox_surface_status(mode="registry")` was returning `domain="earth.general"` for all 12 EGS tools + `geox_surface_status` itself because the hardcoded `tool_domains` dict in `server.py` only covered 17 old tools (well, seismic, basin, governance plumbing).

The EGS tools added in Phase 2.1 (2026-06-28) were never added to that dict, so they fell through to the default `"earth.general"`.

## Root Cause

The domain metadata was stored as an inline Python dict in `server.py:2049–2067`, not in the structured `GEOX_TOOL_MANIFEST`. This meant:
1. EGS tools (12 tools) had no domain entry
2. `geox_surface_status` itself had no domain entry
3. Domain metadata was not co-located with lane/axis/affordance in the manifest
4. Adding new tools required updating two separate places (manifest + hardcoded dict)

## What Changed

### `registry.py`
- Added `domain` field to every entry in `GEOX_TOOL_MANIFEST`
- Added `get_tool_domain(tool_name: str) -> str` helper function
- Single source of truth for domain — structured manifest, version-controlled

**Domain assignments:**
| Tool(s) | Domain |
|---------|--------|
| `geox_well_ingest`, `geox_well_qc`, `geox_well_desurvey` | `earth.well` |
| `geox_petrophysics` | `earth.petrophysics` |
| `geox_sequence` | `earth.stratigraphy` |
| `geox_seismic_ingest`, `geox_seismic_compute`, `geox_seismic_interpret` | `earth.seismic` |
| `geox_vision` | `earth.perception` |
| `geox_subsurface_model` | `earth.model` |
| `geox_geomechanics` | `earth.mechanics` |
| `geox_basin` | `earth.basin` |
| `geox_deep_time_state` | `earth.deep_time` |
| `geox_surface_status` | `earth.general` |
| `geox_egs_query_*` (4 tools) | `earth.governance` |
| `geox_egs_claim_create`, `geox_egs_claim_challenge`, `geox_egs_evidence_attach`, `geox_egs_evidence_reason`, `geox_egs_scenario_audit` | `earth.governance` |
| `geox_egs_seismic_compute` | `earth.seismic` |
| `geox_egs_rock_physics` | `earth.petrophysics` |
| `geox_egs_data_qc_bundle` | `earth.general` |
| `geox_claim` | `governance.claims` |
| `geox_evidence` | `governance.evidence` |
| `geox_prospect` | `governance.prospect` |
| `geox_doctrine` | `governance.doctrine` |

### `server.py`
- Removed 19-line hardcoded `tool_domains` dict
- `geox_surface_status` now calls `get_tool_domain(tool_name)` from registry
- Import updated to include `get_tool_domain`

## Verification

```
geox_surface_status(mode="registry") — 30/30 tools ✅
```

Before (sample):
```json
{"name": "geox_egs_query_entity", "domain": "earth.general"}  // WRONG
```

After (sample):
```json
{"name": "geox_egs_query_entity", "domain": "earth.governance"}  // CORRECT
```

All 30 tools now return semantically correct domains:
- EGS query tools → `earth.governance` ✅
- EGS claim/evidence tools → `earth.governance` ✅
- EGS seismic_compute → `earth.seismic` ✅
- EGS rock_physics → `earth.petrophysics` ✅
- EGS data_qc_bundle → `earth.general` ✅
- EGS scenario_audit → `earth.governance` ✅
- `geox_surface_status` itself → `earth.general` ✅

## Files Changed

| File | Change |
|------|--------|
| `src/geox_mcp/registry.py` | Add domain to manifest + get_tool_domain() helper |
| `src/geox_mcp/server.py` | Remove hardcoded dict, use get_tool_domain() |

## Commit

```
2065d17d fix(registry): GEOX-AUDIT-FIX-002 — add domain to tool manifest, replace hardcoded dict
```

## Pre-Existing Conditions (NOT changed)

- 72 mypy type errors in server.py (pre-existing, full codebase)
- LSP errors in organ_governance.py (pre-existing, full codebase)
- 17 pre-existing test failures (alignment×4, deep_time×6, lem×1, physics×2, transport_manifest×2, registry×2)

---

**DITEMPA BUKAN DIBERI — Evidence is forged, not given.**