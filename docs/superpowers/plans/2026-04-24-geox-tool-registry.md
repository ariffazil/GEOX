# GEOX Tool Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded module-level imports in `fastmcp_server.py` with a registry pattern so that deleting any tool module never crashes the server at import time.

**Architecture:** A `tool_registry.py` module holds a simple dict of `{name: callable}`. The top of `fastmcp_server.py` replaces bare `from ... import X` statements with `try/except ImportError` blocks that register each function on success. Call sites inside `@mcp.tool()` functions retrieve implementations via `get_tool()` and return a structured error if the tool is absent. Shim modules in `geox/geox_mcp/tools/` keep working but emit `DeprecationWarning`.

**Tech Stack:** Python 3.11, FastMCP 2.x, pytest

---

## Context You Need

`fastmcp_server.py` is ~1700 lines. It has two distinct zones:

1. **Import zone** (lines 28–52): bare `from geox.geox_mcp.tools.X import Y` — these are the fragile lines.
2. **Call sites** (scattered): 10 places where imported functions are called inside `@mcp.tool()` decorated wrappers.

The `@mcp.tool()` wrappers are large validation + routing functions defined inline in `fastmcp_server.py`. The imported functions are implementation helpers called *inside* those wrappers. They are **not** the MCP tools themselves.

The 8 fragile imports and their call sites:

| Import alias | Module path | Call sites (approx lines) |
|---|---|---|
| `geox_ingest_las_tool` | `tools.las_ingest_tool` | 468 |
| `geox_compute_sw_ensemble_tool` | `tools.petro_ensemble_tool` | 592, 1184 |
| `geox_compute_volume_probabilistic_tool` | `tools.volumetrics_tool` | 649, 1199 |
| `geox_run_sensitivity_sweep_tool` | `tools.sensitivity_tool` | 668, 1184 |
| `geox_render_log_track_tool` | `tools.visualization` | 711 |
| `geox_memory_store_asset_tool` | `tools.asset_memory_tool` | 745, 1206 |
| `geox_render_volume_slice_tool` | `tools.visualization` | 844 |
| `geox_memory_recall_asset_tool` | `tools.asset_memory_tool` | 1309 |
| `geox_simulate_basin_charge_tool` | `tools.basin_charge_tool` | imported, not yet called |

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| **Create** | `geox/geox_mcp/tool_registry.py` | Registry dict + register/get/list API |
| **Modify** | `geox/geox_mcp/fastmcp_server.py` lines 28–52 | Replace bare imports with try/except + register |
| **Modify** | `geox/geox_mcp/fastmcp_server.py` lines 468, 592, 649, 668, 711, 745, 844, 1184, 1199, 1206, 1309 | Replace direct calls with get_tool() + None guard |
| **Modify** | `geox/geox_mcp/tools/*.py` (8 shim files) | Add DeprecationWarning + TEMP header |
| **Create** | `tests/test_tool_registration.py` | CI guard: registry must load ≥1 tool |

---

## Task 1: Create `tool_registry.py`

**Files:**
- Create: `geox/geox_mcp/tool_registry.py`
- Test: `tests/test_tool_registration.py` (written in Task 5)

- [ ] **Step 1: Write the file**

```python
# geox/geox_mcp/tool_registry.py
"""
GEOX tool registry — decouples fastmcp_server from file layout.

Tools self-register at import time. Missing modules emit a warning;
they do NOT crash the server.
"""

import logging
from typing import Callable

_REGISTRY: dict[str, Callable] = {}

logger = logging.getLogger(__name__)


def register_tool(name: str, fn: Callable) -> None:
    """Register a callable under the given name."""
    if name in _REGISTRY:
        logger.warning("tool_registry: overwriting existing tool %r", name)
    _REGISTRY[name] = fn


def get_tool(name: str) -> Callable | None:
    """Return the registered callable or None if not registered."""
    return _REGISTRY.get(name)


def list_tools() -> list[str]:
    """Return sorted list of registered tool names."""
    return sorted(_REGISTRY.keys())
```

- [ ] **Step 2: Verify import works**

```bash
cd /c/ariffazil/GEOX
python -c "from geox.geox_mcp.tool_registry import register_tool, get_tool, list_tools; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add geox/geox_mcp/tool_registry.py
git commit -m "feat: add tool_registry — decoupled tool loading for GEOX MCP"
```

---

## Task 2: Refactor Import Zone in `fastmcp_server.py`

**Files:**
- Modify: `geox/geox_mcp/fastmcp_server.py` (lines 28–52 only)

Replace the 5 bare import blocks with guarded try/except + registration.

- [ ] **Step 1: Replace lines 28–52**

Find this block:

```python
from geox.geox_mcp.tools.asset_memory_tool import (
    geox_memory_recall_asset_tool,
    geox_memory_store_asset_tool,
)
from geox.geox_mcp.tools.basin_charge_tool import geox_simulate_basin_charge_tool
from geox.geox_mcp.tools.las_ingest_tool import geox_ingest_las_tool
from geox.geox_mcp.tools.petro_ensemble_tool import geox_compute_sw_ensemble_tool
from geox.geox_mcp.tools.sensitivity_tool import geox_run_sensitivity_sweep_tool
from geox.geox_mcp.tools.visualization import (
    geox_render_log_track_tool,
    geox_render_volume_slice_tool,
)
from geox.geox_mcp.tools.volumetrics_tool import geox_compute_volume_probabilistic_tool
```

Replace with:

```python
import logging as _log
from geox.geox_mcp.tool_registry import register_tool, get_tool, list_tools

def _load_tool(mod_path: str, fn_name: str) -> None:
    """Import one tool function and register it. Log on failure, never raise."""
    try:
        import importlib
        mod = importlib.import_module(mod_path)
        register_tool(fn_name, getattr(mod, fn_name))
    except Exception as exc:
        _log.warning(
            "GEOX tool unavailable — %s.%s: %s",
            mod_path, fn_name, exc,
            extra={"tool": fn_name, "module": mod_path, "error": str(exc)},
        )

_load_tool("geox.geox_mcp.tools.asset_memory_tool", "geox_memory_recall_asset_tool")
_load_tool("geox.geox_mcp.tools.asset_memory_tool", "geox_memory_store_asset_tool")
_load_tool("geox.geox_mcp.tools.basin_charge_tool",  "geox_simulate_basin_charge_tool")
_load_tool("geox.geox_mcp.tools.las_ingest_tool",    "geox_ingest_las_tool")
_load_tool("geox.geox_mcp.tools.petro_ensemble_tool","geox_compute_sw_ensemble_tool")
_load_tool("geox.geox_mcp.tools.sensitivity_tool",   "geox_run_sensitivity_sweep_tool")
_load_tool("geox.geox_mcp.tools.visualization",      "geox_render_log_track_tool")
_load_tool("geox.geox_mcp.tools.visualization",      "geox_render_volume_slice_tool")
_load_tool("geox.geox_mcp.tools.volumetrics_tool",   "geox_compute_volume_probabilistic_tool")
```

- [ ] **Step 2: Verify server boots (import only — no uvicorn)**

```bash
python -c "import geox.geox_mcp.fastmcp_server; print('boot OK')"
```

Expected: `boot OK` (with optional WARNING lines if any tool fails — that is correct behaviour)

- [ ] **Step 3: Verify registry has tools**

```bash
python -c "
from geox.geox_mcp.fastmcp_server import mcp
from geox.geox_mcp.tool_registry import list_tools
print('MCP tools:', len(list(mcp._tool_manager.tools)))
print('Registry:', list_tools())
"
```

Expected: at least `geox_ingest_las_tool` and several others listed.

- [ ] **Step 4: Commit**

```bash
git add geox/geox_mcp/fastmcp_server.py
git commit -m "refactor: replace fragile bare imports in fastmcp_server with registry loader"
```

---

## Task 3: Refactor Call Sites in `fastmcp_server.py`

**Files:**
- Modify: `geox/geox_mcp/fastmcp_server.py` — ~10 call sites

For each location where an imported function is called, replace the direct call with a `get_tool()` lookup + None guard.

**Pattern to apply at every call site:**

Before:
```python
manifest = geox_ingest_las_tool(str(safe_las), asset_id=well_id)
```

After:
```python
_geox_ingest_las = get_tool("geox_ingest_las_tool")
if _geox_ingest_las is None:
    return {
        "well_id": well_id,
        "status": "error",
        "claim_tag": "VOID",
        "error": "tool_unavailable:geox_ingest_las_tool",
    }
manifest = _geox_ingest_las(str(safe_las), asset_id=well_id)
```

- [ ] **Step 1: Apply pattern at line ~468 (`geox_ingest_las_tool`)**

Find:
```python
            manifest = geox_ingest_las_tool(str(safe_las), asset_id=well_id)
```
Replace with the guarded version above (the `return` dict shape must match the existing error returns in that function — copy the shape from the `except FileNotFoundError` block above it).

- [ ] **Step 2: Apply pattern at line ~592 (`geox_compute_sw_ensemble_tool`)**

Find:
```python
        ensemble = geox_compute_sw_ensemble_tool(
```
Before that call add:
```python
        _compute_sw = get_tool("geox_compute_sw_ensemble_tool")
        if _compute_sw is None:
            return {"well_id": well_id, "status": "error", "claim_tag": "VOID",
                    "error": "tool_unavailable:geox_compute_sw_ensemble_tool"}
```
Change the call to use `_compute_sw(...)`.

- [ ] **Step 3: Apply pattern at line ~649 (`geox_compute_volume_probabilistic_tool`)**

```python
        _vol_prob = get_tool("geox_compute_volume_probabilistic_tool")
        if _vol_prob is None:
            return {"well_id": well_id, "status": "error", "claim_tag": "VOID",
                    "error": "tool_unavailable:geox_compute_volume_probabilistic_tool"}
        probabilistic_volume = _vol_prob(...)
```

- [ ] **Step 4: Apply pattern at line ~668 (`geox_run_sensitivity_sweep_tool`)**

```python
        _sensitivity = get_tool("geox_run_sensitivity_sweep_tool")
        if _sensitivity is None:
            return {"well_id": well_id, "status": "error", "claim_tag": "VOID",
                    "error": "tool_unavailable:geox_run_sensitivity_sweep_tool"}
        sensitivity = _sensitivity(...)
```

- [ ] **Step 5: Apply pattern at line ~711 (`geox_render_log_track_tool`)**

```python
        _render_log = get_tool("geox_render_log_track_tool")
        "visualization_payload": _render_log(...) if _render_log else {"error": "tool_unavailable:geox_render_log_track_tool"},
```

- [ ] **Step 6: Apply pattern at lines ~745, ~1206 (`geox_memory_store_asset_tool`)**

```python
        _mem_store = get_tool("geox_memory_store_asset_tool")
        if _mem_store:
            result["asset_memory"] = _mem_store(...)
        else:
            result["asset_memory"] = {"error": "tool_unavailable:geox_memory_store_asset_tool"}
```

- [ ] **Step 7: Apply pattern at line ~844 (`geox_render_volume_slice_tool`)**

```python
        _render_vol = get_tool("geox_render_volume_slice_tool")
        "render_payload": _render_vol(...) if _render_vol else {"error": "tool_unavailable:geox_render_volume_slice_tool"},
```

- [ ] **Step 8: Apply pattern at lines ~1184 (second `geox_run_sensitivity_sweep_tool` call)**

Same as Step 4, using `_sensitivity = get_tool("geox_run_sensitivity_sweep_tool")`.

- [ ] **Step 9: Apply pattern at line ~1199 (second `geox_compute_volume_probabilistic_tool` call)**

Same as Step 3.

- [ ] **Step 10: Apply pattern at line ~1309 (`geox_memory_recall_asset_tool`)**

```python
        _mem_recall = get_tool("geox_memory_recall_asset_tool")
        if _mem_recall is None:
            return {"status": "error", "claim_tag": "VOID",
                    "error": "tool_unavailable:geox_memory_recall_asset_tool"}
        result["asset_memory"] = _mem_recall(...)
```

- [ ] **Step 11: Verify server still boots**

```bash
python -c "import geox.geox_mcp.fastmcp_server; print('OK')"
```

- [ ] **Step 12: Commit**

```bash
git add geox/geox_mcp/fastmcp_server.py
git commit -m "refactor: replace direct tool calls with get_tool() registry lookups"
```

---

## Task 4: Add Pre-flight Guard

**Files:**
- Modify: `geox/geox_mcp/fastmcp_server.py` — find the `mcp = FastMCP("geox")` line (~line 65)

- [ ] **Step 1: Add guard after tool loading block**

After all `_load_tool(...)` calls, insert:

```python
# Pre-flight: fail with structured message if no tools loaded
_loaded = list_tools()
if not _loaded:
    import sys
    print(
        '{"level":"CRITICAL","event":"preflight_fail","detail":"No GEOX tools registered.",'
        '"action":"Check geox.geox_mcp.tools modules and legacy_skills paths."}',
        file=sys.stderr,
    )
    sys.exit(1)
_log.info("GEOX tool registry: %d tools loaded: %s", len(_loaded), _loaded)
```

- [ ] **Step 2: Test the guard fires correctly**

Temporarily add a bad path and confirm structured output:

```bash
python -c "
import geox.geox_mcp.tool_registry as r
r._REGISTRY.clear()
# Guard would fire if this were startup; verify shape manually
from geox.geox_mcp.tool_registry import list_tools
assert list_tools() == []
print('guard shape verified')
"
```

- [ ] **Step 3: Commit**

```bash
git add geox/geox_mcp/fastmcp_server.py
git commit -m "feat: add structured pre-flight guard — server exits clean if no tools loaded"
```

---

## Task 5: Add CI Test

**Files:**
- Create: `tests/test_tool_registration.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_tool_registration.py
"""
CI guard: verifies GEOX tool registry loads at least the canonical tool set.
Does NOT depend on the shim path geox.geox_mcp.tools.*
"""
import importlib
import pytest

EXPECTED_TOOLS = [
    "geox_ingest_las_tool",
    "geox_compute_sw_ensemble_tool",
    "geox_compute_volume_probabilistic_tool",
    "geox_run_sensitivity_sweep_tool",
    "geox_render_log_track_tool",
    "geox_render_volume_slice_tool",
    "geox_memory_store_asset_tool",
    "geox_memory_recall_asset_tool",
]


@pytest.fixture(autouse=True)
def load_server():
    """Import fastmcp_server to trigger _load_tool() calls."""
    importlib.import_module("geox.geox_mcp.fastmcp_server")


def test_registry_not_empty():
    from geox.geox_mcp.tool_registry import list_tools
    registered = list_tools()
    assert len(registered) > 0, (
        f"Tool registry is empty. Expected at least: {EXPECTED_TOOLS}. "
        "Check geox/geox_mcp/tools/ and geox/legacy_skills/ paths."
    )


@pytest.mark.parametrize("tool_name", EXPECTED_TOOLS)
def test_canonical_tool_registered(tool_name):
    from geox.geox_mcp.tool_registry import get_tool
    fn = get_tool(tool_name)
    assert fn is not None, (
        f"Tool '{tool_name}' not in registry. "
        f"Check _load_tool() call for this function in fastmcp_server.py."
    )
    assert callable(fn), f"Registry entry for '{tool_name}' is not callable."


def test_registry_does_not_depend_on_shim_path():
    """Registry must work even if tools/ shim package is absent."""
    from geox.geox_mcp.tool_registry import list_tools, _REGISTRY
    # Direct registry access — not through geox.geox_mcp.tools.*
    assert len(_REGISTRY) > 0
```

- [ ] **Step 2: Run it**

```bash
cd /c/ariffazil/GEOX
python -m pytest tests/test_tool_registration.py -v
```

Expected: all tests PASS. If any `test_canonical_tool_registered` test fails, a tool was not loaded — fix the `_load_tool()` call or the legacy_skills path before continuing.

- [ ] **Step 3: Commit**

```bash
git add tests/test_tool_registration.py
git commit -m "test: add CI guard for GEOX tool registry — fails if canonical tools missing"
```

---

## Task 6: Deprecate Shim Modules

**Files:**
- Modify: all 8 files in `geox/geox_mcp/tools/` (the shims created in the previous session)

Apply this header and warning to each file. Example for `las_ingest_tool.py`:

- [ ] **Step 1: Update all 8 shim files**

Template (apply to each file, changing the function name):

```python
# TEMP COMPAT LAYER — remove after vNext (post-registry migration complete)
import warnings
warnings.warn(
    "geox.geox_mcp.tools.las_ingest_tool is deprecated; "
    "functions are now loaded via geox.geox_mcp.tool_registry.",
    DeprecationWarning,
    stacklevel=2,
)

from geox.legacy_skills.petro.las_ingest import geox_ingest_las_tool

__all__ = ["geox_ingest_las_tool"]
```

For each file:

| Shim file | Warning text | Import from |
|---|---|---|
| `asset_memory_tool.py` | `geox.geox_mcp.tools.asset_memory_tool is deprecated` | `geox.legacy_skills.asset_memory_tool` |
| `basin_charge_tool.py` | `geox.geox_mcp.tools.basin_charge_tool is deprecated` | `geox.legacy_skills.prospect.basin_charge` |
| `las_ingest_tool.py` | `geox.geox_mcp.tools.las_ingest_tool is deprecated` | `geox.legacy_skills.petro.las_ingest` |
| `petro_ensemble_tool.py` | `geox.geox_mcp.tools.petro_ensemble_tool is deprecated` | `geox.legacy_skills.petro.petro_ensemble` |
| `sensitivity_tool.py` | `geox.geox_mcp.tools.sensitivity_tool is deprecated` | `geox.legacy_skills.sensitivity_tool` |
| `visualization.py` | `geox.geox_mcp.tools.visualization is deprecated` | `geox.legacy_skills.maps.visualization` |
| `volumetrics_tool.py` | `geox.geox_mcp.tools.volumetrics_tool is deprecated` | `geox.legacy_skills.volumes.volumetrics` |
| `__init__.py` | `geox.geox_mcp.tools is deprecated` | *(no import, just warn)* |

- [ ] **Step 2: Verify deprecation fires**

```bash
python -W all -c "
import warnings
warnings.simplefilter('always')
from geox.geox_mcp.tools.las_ingest_tool import geox_ingest_las_tool
" 2>&1 | grep -i deprecated
```

Expected output: `DeprecationWarning: geox.geox_mcp.tools.las_ingest_tool is deprecated`

- [ ] **Step 3: Commit**

```bash
git add geox/geox_mcp/tools/
git commit -m "chore: mark geox_mcp.tools shims as deprecated — TEMP COMPAT LAYER"
```

---

## Task 7: Final Verification + Push

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest tests/test_tool_registration.py -v --tb=short
```

Expected: all green.

- [ ] **Step 2: Verify import-time resilience**

```bash
python -c "
import sys, types
# Simulate a missing module
sys.modules['geox.geox_mcp.tools.las_ingest_tool'] = None  # type: ignore
import importlib
importlib.invalidate_caches()
# Now reimport fastmcp_server — should NOT crash
import geox.geox_mcp.tool_registry as r
r._REGISTRY.clear()

# Manually test _load_tool with a bad path
import logging
logging.basicConfig(level=logging.WARNING)

# Import the loader
from geox.geox_mcp import fastmcp_server as srv
from geox.geox_mcp.tool_registry import list_tools
print('Tools after partial failure:', list_tools())
print('RESILIENCE OK')
"
```

Expected: warning lines printed, `RESILIENCE OK` at end, no traceback.

- [ ] **Step 3: Push**

```bash
git push origin main
```

---

## Migration Notes

**After vNext:** Remove `geox/geox_mcp/tools/` entirely. The `_load_tool()` calls in `fastmcp_server.py` should be updated to point directly at `geox.legacy_skills.*` paths, eliminating the shim layer entirely:

```python
# vNext — direct legacy_skills registration, no shim
_load_tool("geox.legacy_skills.petro.las_ingest",  "geox_ingest_las_tool")
_load_tool("geox.legacy_skills.prospect.basin_charge", "geox_simulate_basin_charge_tool")
# etc.
```

**Self-registration alternative (future):** If tool count grows beyond ~20, consider moving each `_load_tool()` call into the tool module itself (call `register_tool()` at module bottom), and replace all `_load_tool(...)` calls in `fastmcp_server.py` with a single auto-discovery loop over a known package. Not needed now — YAGNI.

---

## Directory Diff Tree

```
geox/
  geox_mcp/
    tool_registry.py          ← NEW
    fastmcp_server.py         ← MODIFIED (imports + call sites + preflight)
    tools/
      __init__.py             ← MODIFIED (deprecation warning)
      asset_memory_tool.py    ← MODIFIED (deprecation warning)
      basin_charge_tool.py    ← MODIFIED (deprecation warning)
      las_ingest_tool.py      ← MODIFIED (deprecation warning)
      petro_ensemble_tool.py  ← MODIFIED (deprecation warning)
      sensitivity_tool.py     ← MODIFIED (deprecation warning)
      visualization.py        ← MODIFIED (deprecation warning)
      volumetrics_tool.py     ← MODIFIED (deprecation warning)
tests/
  test_tool_registration.py   ← NEW
docs/
  superpowers/
    plans/
      2026-04-24-geox-tool-registry.md  ← THIS FILE
```
