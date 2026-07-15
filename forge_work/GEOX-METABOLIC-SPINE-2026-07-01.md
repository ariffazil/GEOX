# GEOX Metabolic Spine + Certification Drift Fix — FORGE Receipt

> **Date:** 2026-07-01
> **Agent:** FORGE (000Ω)
> **Session:** SEAL-01e890e8b9014b6f
> **Verdict:** PROCEED — executed

---

## What Happened

Arif directed focus on GEOX within the Federation Metabolism Spine concept. Two streams of work executed:

### Stream 1: Federation Metabolism Spine (GEOX)

Built the canonical **FederationEnvelope** — the blood packet every organ must use to talk to every other organ.

| Artifact | Path | Purpose |
|----------|------|---------|
| `federation_envelope.py` | `contracts/schemas/federation_envelope.py` | Canonical schema + builder + GEOX adapter |
| `test_federation_envelope.py` | `tests/test_federation_envelope.py` | 12 tests covering construction, Sabah Basin loop, floor checks |

**Key design decisions:**
- `FederationEnvelope` carries: trace_id, actor_id, organ_origin, organ_target, intent, evidence_layer, autonomy_band, reversibility_class, risk_class, required_floor_checks, proposed_action, execution_status, measurement_result, vault_receipt_reference, f13_required
- `geox_to_federation_envelope()` adapter wraps any GEOX tool output in the envelope
- `build_federation_envelope()` builder for cross-organ construction
- F7 HUMILITY cap at 0.90 enforced in confidence field
- Sabah Basin test scenario exercises full GEOX→WEALTH→arifOS→A-FORGE loop

**Test results:** 12/12 passed

### Stream 2: Certification Drift Fix

The audit correctly identified tool count drift across 6 files. Fixed all stale references to align with live truth (34 canonical tools, epoch `2026-07-01-GEOX-34TOOLS-PHASE23`):

| File | Before | After |
|------|--------|-------|
| `BOUNDARY.md` | 56 tools, epoch `2026-06-22-GEOX-56TOOLS-v3.0` | 34 tools, epoch `2026-07-01-GEOX-34TOOLS-PHASE23` |
| `CONTEXT.md` | 56 tools, `_EXPECTED_CANONICAL = 56` | 34 tools, `_EXPECTED_CANONICAL = 34` |
| `pyproject.toml` | "40 canonical MCP tools" | "34 canonical MCP tools" |
| `AGENTS.md` | 31 tools (Phase 2.2) | 34 tools (Phase 2.3) |
| `docs/MCP_TRANSPORT_SURFACE.md` | `_EXPECTED_CANONICAL = 56` | `_EXPECTED_CANONICAL = 34` |
| `docs/MCP_TOOL_REFERENCE.md` | `_EXPECTED_CANONICAL = 56` | `_EXPECTED_CANONICAL = 34` |

**Source of truth verified:** `python3 -c "from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS; print(len(CANONICAL_PUBLIC_TOOLS))"` → 34

---

## What the Audit Got Right

1. **Certification drift is real** — 6 files disagreed on tool count. Fixed.
2. **Map tool surface is correct** — `geox_map_layers_list`, `geox_map_scene_plan`, `geox_map_render_preview` already exist as Phase 2.3.
3. **4th map tool missing** — `geox_map_export_package` not yet built. Deferred.
4. **Provenance sidecars needed** — The W3C PROV + ISO 19115 sidecar template is sound direction.
5. **Narrow surface is right** — 4 map verbs (list, plan, render, export) is the correct target.

## What the Audit Got Wrong (or Overstated)

1. **"56 canonical tools" was stale docs, not competing truths** — The live server has been 34 since Phase 2.3. The 56/40/31 numbers were documentation lag, not architectural confusion.
2. **GEOX already has metabolic schemas** — `MetabolicOutput` (metabolic.py) has been Phase 1 adopted since June. The FederationEnvelope builds on it.
3. **The "two server surfaces" issue is known** — `BOUNDARY.md` already documents this as a known boundary violation.

## Remaining Work

| Item | Priority | Status |
|------|----------|--------|
| `geox_map_export_package` tool | HIGH | Not started |
| Wire FederationEnvelope into GEOX MCP server output | MEDIUM | Pending |
| Provenance sidecar schema (W3C PROV) | MEDIUM | Pending |
| PMTiles/COG storage layer | LOW | Deferred |
| MCP App review UI | LOW | Deferred |

---

## Constitutional Check

| Floor | Status | Note |
|-------|--------|------|
| F1 AMANAH | ✅ | All changes backed by git. Reversible. |
| F2 TRUTH | ✅ | Tool count verified by live import, not assumed. |
| F4 CLARITY | ✅ | Reduced entropy — 6 files now agree. |
| F7 HUMILITY | ✅ | Confidence cap 0.90 enforced. |
| F11 AUDIT | ✅ | This receipt. |

---

*DITEMPA BUKAN DIBERI*
