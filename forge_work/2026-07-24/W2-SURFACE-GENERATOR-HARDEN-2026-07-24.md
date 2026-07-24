# W2 — generate_mcp_apps_surface.py anti-regression
**Date:** 2026-07-24T09:54Z  

## Bug (proved)

Re-running the old generator against live tools produced **5 active zero-bound** UIs:

- `ui://geox/geox-mcp-visual`
- `ui://geox/gravmag-studio.html`
- `ui://geox/prospect-studio`
- `ui://geox/workbench-v1.html`
- `ui://geox/workspace-v1.html`

Root cause: bound_tools only from exact `meta.ui.resourceUri` match. Alias family (`.html` twins, legacy `geox-mcp-visual` ↔ `visual-hub`, `prospect-studio` ↔ `prospect-ui`) and reverse maps from `_app_to_tool` / `_tool_app_fallback` were ignored.

## Fix

`scripts/generate_mcp_apps_surface.py`:
1. Import `GEOX_APPS`, `_app_to_tool`, `_tool_app_fallback`
2. URI canonicalization + `_URI_ALIASES`
3. Reverse maps + apps.json `visual_tools` seeds
4. **Fail closed** if any active resource has empty `bound_tools` (exit 1)
5. Emit `active_zero_bound` field

## Gates

- `make generate-mcp-apps-surface` → exit 0, active_zero_bound=0  
- `tests/test_mcp_apps_readiness.py::test_10c_surface_manifest_active_zero_bound`  
- `make readiness-test` → **23 passed**

DITEMPA BUKAN DIBERI
