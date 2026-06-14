# GEOX Forge Cycle 03 — 2026-06-14

**Forged by:** FORGE-000Ω  
**Sovereign:** Muhammad Arif bin Fazil (F13)  
**Doctrine:** DITEMPA BUKAN DIBERI  
**Lane:** A-FORGE → Implementer (Forge)

---

## Session Summary

GEOX forge cycle resolving 4 categories of issues across 11 files in 2 repos (GEOX contracts + src).

---

## Issues Fixed

### 🔴 CRITICAL: pydantic-core Version Mismatch

- **Root Cause:** pydantic-core 2.46.3 with pydantic 2.13.4 (needs 2.46.4), getting downgraded during install loops
- **Fix:** Reinstalled both in lockstep: `pydantic==2.13.4` + `pydantic-core==2.46.4`
- **Result:** All schema-dependent tests pass

### 🔴 CRITICAL: `from __future__ import annotations` Position

- **Files (11):** `contracts/schemas/output_schemas.py`, `contracts/schemas/metabolic.py`, `contracts/tools/well_correlation.py`, `contracts/tools/unified_13.py`, `contracts/tools/canonical/kernel/_biostrat.py`, `contracts/governance/acp_logic.py`, `contracts/mcp/adapter_bus_contract.py`
- **Fix:** Moved `from __future__ import annotations` to top of each file (before any non-comment code)
- **Why:** Python requires `__future__` imports before any other code

### 🟡 HIGH: Stale Canonical Surface Test

- **Root Cause:** `test_canonical_public_surface.py` tested against old KiMi-era MCP fixture (21 tools from `contracts.tools.unified_13`), not the live 40-tool server
- **Fix:** Rewrote test to verify against `src/geox_mcp/registry.py` (SOT) and the live GEOX MCP at port 8081

### 🟡 HIGH: Asset Collision — `geox_query_macrostrat` as Both Canonical Tool + Alias

- **Root Cause:** Listed in `CANONICAL_PUBLIC_TOOLS` but also had a legacy alias pointing to `geox_basin_profile`
- **Fix:** Removed alias from `src/geox_mcp/registry.py` — it's now a first-class canonical tool with its own `macrostrat_client.py`
- **SOT:** `src/geox_mcp/registry.py` (40 tools) → now the single source of truth

### 🟡 HIGH: `contracts/canonical_registry.py` Drifted from SOT

- **Root Cause:** Old copy had 39 tools (missing `geox_query_macrostrat`)
- **Fix:** Added the missing tool to both `CANONICAL_PUBLIC_TOOLS` and `GEOX_TOOL_MANIFEST` to match SOT

### 🔵 MEDIUM: Missing Integration Marker in `pyproject.toml`

- **Root Cause:** `pytest.mark.integration` was used but never registered → warning on every test run
- **Fix:** Added `[tool.pytest.ini_options]` markers block with `integration`, `slow`, `e3e`

### 🔵 MEDIUM: 4 Ruff Lint Issues in `macrostrat_client.py`

- **Fix:** Removed unused imports (`datetime`, `timezone`, `Literal`) and fixed import ordering

---

## Verifications

| Test Suite | Count | Status |
|------------|-------|--------|
| GEOX unit tests (tests/unit/) | 89 passed | ✅ |
| Macrostrat integration (tests/integration/) | 32 passed | ✅ |
| Canonical surface (structural checks) | 6 passed | ✅ |
| WEALTH internal imports | 13 passed | ✅ |
| ARIF Conformance Spine | 8/8 passed | ✅ |
| Federation organ health | 7/7 alive | ✅ |

---

## Files Changed

**GEOX repo (11 files):**
- `contracts/schemas/output_schemas.py`
- `contracts/schemas/metabolic.py`
- `contracts/tools/well_correlation.py`
- `contracts/tools/unified_13.py`
- `contracts/tools/canonical/kernel/_biostrat.py`
- `contracts/governance/acp_logic.py`
- `contracts/mcp/adapter_bus_contract.py`
- `contracts/canonical_registry.py`
- `src/geox_mcp/registry.py`
- `src/geox_mcp/tools/macrostrat_client.py`
- `pyproject.toml`

**No irreversible operations.**
