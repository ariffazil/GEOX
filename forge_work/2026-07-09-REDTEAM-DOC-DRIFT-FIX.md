# GEOX Red Team — Documentation Drift Fix

**Date:** 2026-07-09
**Actor:** FORGE (000Ω) under 555_CRITIQUE + GEOX_RED_TEAM review
**Session:** SEAL-1f13826a533246af

---

## Problem

Dynamic runtime facts (tool counts, contract epochs, version strings) were baked into static documentation across 20+ files. Every tool addition created a 10-file update cycle. The result: perpetual documentation drift.

**Evidence:** grep found stale references in:
- `.well-known/agent-card.json` (34)
- `.well-known/agent.json` (34)
- `.well-known/mcp/server.json` (31)
- `AGENTS.md` (35)
- `BOUNDARY.md` (35)
- `CONTEXT.md` (35)
- `RUNBOOK.md` (56)
- `QUICKSTART.md` (40)
- `README.md` (35, 46, 35, 35, 35)
- `src/geox_core/__init__.py` (34)
- `src/geox_mcp/floor_enforcement.py` (35)
- `docs/` (5+ files with 13, 21, 34, 35, 56)

**Actual state from code:**
- `registry.py`: CANONICAL_PUBLIC_TOOLS = 73 (69 surface + 4 internal)
- `server.py`: _EXPECTED_CANONICAL = 73

---

## Principle Applied

**Runtime facts live at runtime. Docs describe architecture, not counts.**

| Layer | Keeps Numbers | Why |
|-------|--------------|-----|
| `registry.py` (CANONICAL_PUBLIC_TOOLS) | ✅ Source of truth | The actual list |
| `server.py` (_EXPECTED_CANONICAL) | ✅ Invariant check | Fails startup if mismatch |
| `server.py` (GEOX_CONTRACT_EPOCH) | ✅ Changelog marker | Code, not docs |
| Agent cards (.well-known/) | ❌ Stripped | Discoverable via tools/list |
| README.md summary | ❌ Stripped | Capability map section keeps domain table |
| AGENTS.md, BOUNDARY.md, etc. | ❌ Stripped | Points to registry.py as source |
| docs/ historical files | ⚠️ Untouched | Historical snapshots — add disclaimer if needed |

---

## Files Changed

### Source code (3 files)
1. `src/geox_core/__init__.py` — version string updated, tool count removed
2. `src/geox_mcp/server.py` — contract epoch updated to 73TOOLS
3. `src/geox_mcp/floor_enforcement.py` — comment updated

### Agent discovery (3 files)
4. `.well-known/agent-card.json` — stripped tool count from description
5. `.well-known/agent.json` — stripped tool count from credentials
6. `.well-known/mcp/server.json` — stripped tool count, replaced with "discoverable via tools/list"

### Root docs (6 files)
7. `README.md` — stripped counts from summary/messaging, kept domain table in capability map
8. `AGENTS.md` — stripped stale counts, replaced with "runtime fact — verify with tools/list"
9. `BOUNDARY.md` — stripped contract epoch, replaced with "runtime fact"
10. `CONTEXT.md` — stripped tool count, replaced with source-of-truth pointers
11. `RUNBOOK.md` — stripped tool count, replaced with "runtime fact"
12. `QUICKSTART.md` — stripped tool count from comment

### Kernel invariants (UNCHANGED)
- `registry.py` CANONICAL_PUBLIC_TOOLS list — **source of truth, untouched**
- `server.py` _EXPECTED_CANONICAL = 73 — **invariant check, untouched**

---

## Red Team Findings (from 555_CRITIQUE)

### C1: "Evidence-Only" vs. Actionable Intelligence
GEOX prospect evaluation outputs POS, EVOI, AC_Risk — these are decision-shaping metrics, not neutral evidence. The constitutional boundary is linguistically clean but functionally porous.

### C2: "Physics-Constrained" vs. Approximate Physics
Petrophysics uses empirical transforms (Archie). Seismic assumes 1D convolution. "Physics-constrained" sounds rigorous but the constraints are themselves models.

### C3: Governance is Self-Enforced
`floor_enforcement.py` runs inside GEOX's own process. The governed entity enforces its own governance. Architecture fix: move floor enforcement to arifOS gateway.

### C4: Tool Count Exceeds Validation Capacity
73 tools × multiple modes = hundreds of execution paths. Code tests ≠ domain validation. A petrophysics tool can pass all unit tests and still give wrong porosity.

### C5: RASA is Circular
RASA validates evidence quality using GEOX's own validation logic. Measures internal consistency, not external truth.

### C6: "Never Authorizes" vs. Prospect Pipeline
When GEOX says "POS=0.65, EVOI=$12M, QUALIFY" — it's functionally recommending drilling.

---

## What to Fix Next (Priority Order)

1. **External ground-truth validation** — validate 5 core tools against known producing fields
2. **Move governance to gateway** — arifOS should enforce floors on GEOX calls, not GEOX
3. **Reduce tool surface for validation** — ship 5 validated tools, expand after confirmation
4. **Track predictions vs. outcomes** — follow up on every prospect evaluation
5. **Drop "Nobel-grade" framing** — credibility liability, let the work speak

---

## Rule Established

> **Documentation Drift Prevention Rule:** Static docs describe capabilities and architecture. Dynamic facts (tool counts, versions, epochs) are runtime-discoverable via `tools/list`, `/health`, or `registry.py`. Never bake a number that changes into a file that doesn't.

---

*DITEMPA BUKAN DIBERI — The mirror reflects. The forge fixes.*
