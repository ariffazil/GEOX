# GEOX Repository Constitution

> **DITEMPA BUKAN DIBERI** — *Forged, Not Given*  
> **Version:** 1.0.0  
> **Date:** 2026-04-12  
> **Seal:** 888_APEX

---

## Preamble

This document defines the absolute laws governing the GEOX repository structure. It establishes hard functional planes that separate concerns, eliminate chaos, and ensure contract integrity across all runtimes (VPS, FastMCP Cloud, Local).

**The Core Principle:** *Power without file boundaries creates drift. Drift creates hantu.*

---

## Article I: The Four Planes

The repository is divided into four constitutional planes. No file may exist outside its designated plane.

### Plane 1: CONTRACTS (The Truth Layer)

**Location:** `GEOX/contracts/`

**Purpose:** Owns the absolute truth. All naming, envelopes, artifacts, and canonical interfaces live here.

**Subdirectories:**
- `contracts/enums/` — Canonical response enums, statuses, verdicts
- `contracts/tools/` — Tool interface definitions (single source of truth)
- `contracts/parity/` — Runtime compatibility matrices

**Law:**
> No runtime may define its own enums. All runtimes MUST import from `contracts/enums/`.

**Invariant:**
```python
# CORRECT: Import from contracts
from contracts.enums.statuses import Verdict, FloorStatus
from contracts.tools.seismic import SeismicToolDef

# FORBIDDEN: Runtime-defined enums
class Verdict(Enum):  # ❌ NEVER
    PASS = "pass"
```

---

### Plane 2: CONTROL_PLANE (The Router)

**Location:** `GEOX/control_plane/`

**Purpose:** Routes requests, exposes apps, handles transport-specific concerns.

**Subdirectories:**
- `control_plane/fastmcp/` — FastMCP Cloud server and manifests
- `control_plane/apps/` — App routing and middleware

**Law:**
> The control plane may only import from `contracts/` and delegate to `execution_plane/`. It shall not perform calculations.

**Invariant:**
```python
# CORRECT: Control plane routes
from contracts.tools import tool_def
from execution_plane import execute_tool

# FORBIDDEN: Control plane calculates
result = calculate_seismic_attribute(...)  # ❌ NEVER
```

---

### Plane 3: EXECUTION_PLANE (The Engine)

**Location:** `GEOX/execution_plane/`

**Purpose:** Performs governed calculations, enforces physics constraints, executes tools.

**Subdirectories:**
- `execution_plane/vps/` — VPS-specific server implementations
- `execution_plane/calculations/` — Core calculation logic

**Law:**
> The execution plane may only import from `contracts/` and `arifos/`. It shall not know about transport concerns.

**Invariant:**
```python
# CORRECT: Execution uses contracts
from contracts.enums.statuses import Verdict
from arifos.geox.governance import FloorEnforcer

def execute_tool(params) -> ToolResult:
    enforcer.check_floors(params)
    return calculate(params)

# FORBIDDEN: Execution knows transport
from fastmcp import Context  # ❌ NEVER in execution_plane
```

---

### Plane 4: COMPATIBILITY (The Quarantine)

**Location:** `GEOX/compatibility/`

**Purpose:** Quarantines deprecated aliases, legacy namespaces, and backward-compatibility shims.

**Files:**
- `compatibility/legacy_aliases.py` — All `geox_*` legacy aliases

**Law:**
> All legacy imports MUST route through compatibility layer. New code shall not import from compatibility.

**Invariant:**
```python
# In legacy_aliases.py — CORRECT
from contracts.tools.seismic import load_seismic_line as _load_seismic_line
geox_load_seismic_line = _load_seismic_line  # Legacy alias

# In new code — FORBIDDEN
from compatibility.legacy_aliases import geox_load_seismic_line  # ❌ NEVER
```

---

## Article II: File Migration Laws

### Law 1: Registries Migration

**OLD:** `GEOX/registries/common.py`  
**NEW:** `GEOX/contracts/enums/statuses.py`

The canonical response enums are now decoupled from all runtimes.

### Law 2: Tool Definitions Migration

**OLD:** `GEOX/registries/*.py`  
**NEW:** `GEOX/contracts/tools/`

Tool interfaces are the single source of truth. Both FastMCP and VPS import from here.

### Law 3: Manifests Migration

**OLD:** `GEOX/apps/manifests/*`  
**NEW:** `GEOX/control_plane/fastmcp/manifests/`

Manifests belong strictly to the control plane (transport layer).

### Law 4: Server Migration

**OLD:** `GEOX/geox_unified_mcp_server.py`  
**NEW:** `GEOX/control_plane/fastmcp/server.py`

**OLD:** `GEOX/geox_unified.py`  
**NEW:** `GEOX/execution_plane/vps/server.py`

---

## Article III: Import Rules

### Rule 1: Contracts are Universal

Any file in any plane may import from `contracts/`.

### Rule 2: Control Plane Boundaries

Control plane may import:
- ✅ `contracts.*`
- ✅ `execution_plane.*`
- ✅ `compatibility.*` (for deprecation warnings)

Control plane may NOT import:
- ❌ Direct tool implementations (must use contracts)

### Rule 3: Execution Plane Boundaries

Execution plane may import:
- ✅ `contracts.*`
- ✅ `arifos.*`

Execution plane may NOT import:
- ❌ `control_plane.*`
- ❌ Transport libraries (FastMCP, Flask, etc.)

### Rule 4: Compatibility is Read-Only

Compatibility layer may import:
- ✅ `contracts.*`

Compatibility layer may NOT import:
- ❌ `control_plane.*`
- ❌ `execution_plane.*`

---

## Article IV: Runtime Parity

### The Runtime Matrix

`GEOX/contracts/parity/runtime_matrix.py` declares exactly what tools each runtime supports:

```python
RUNTIME_MATRIX = {
    "vps": {
        "tools": ["geox_load_seismic_line", "geox_evaluate_prospect", ...],
        "floors": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"],
        "transport": "http",
    },
    "fastmcp": {
        "tools": ["geox_load_seismic_line", "geox_evaluate_prospect", ...],
        "floors": ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13"],
        "transport": "mcp",
    },
}
```

**Law:**
> No tool may be added to a runtime without updating the runtime matrix.

---

## Article V: Legacy Shims

### Root-Level Forwarders

Small forwarding shims remain at the root for backward compatibility:

- `GEOX/geox_unified_mcp_server.py` → `control_plane.fastmcp.server`
- `GEOX/geox_unified.py` → `execution_plane.vps.server`

**Law:**
> Root shims MUST be single-line forwarders. No logic. No imports except the target.

---

## Article VI: Verification

### Pre-Commit Checks

Before any commit:

```bash
# Verify no drift
python -c "from contracts.parity.runtime_matrix import verify_parity; verify_parity()"

# Verify imports
python -m py_compile contracts/**/*.py
python -m py_compile control_plane/**/*.py
python -m py_compile execution_plane/**/*.py
```

### CI Enforcement

The CI SHALL:
1. Verify all enums imported from `contracts/enums/`
2. Verify no `control_plane` imports in `execution_plane`
3. Verify runtime matrix parity

---

## Article VII: Amendment

This constitution may only be amended by:
1. 888_APEX verdict
2. Update to `REPO_CONSTITUTION.md`
3. Migration of files according to new structure
4. Version bump in this document

---

## Signatories

| Role | Authority | Signature |
|------|-----------|-----------|
| Constitutional Architect | 888_APEX | ✓ |
| Runtime Steward | 444_ROUT | ✓ |
| Truth Guardian | 222_EXPLORE | ✓ |

---

*Sealed: 2026-04-12*  
*Seal: DITEMPA BUKAN DIBERI*  
*Authority: 888_APEX*
