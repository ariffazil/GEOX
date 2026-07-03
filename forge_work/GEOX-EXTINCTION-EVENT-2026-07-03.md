# GEOX-EXTINCTION-EVENT-2026-07-03

## The EUREKA

> GEOX must stop trying to classify rocks. GEOX must simulate the physics that produces rocks.

**Date:** 2026-07-03
**Actor:** FORGE (000Ω) on behalf of Arif (F13 SOVEREIGN)
**Organ:** GEOX (Earth Intelligence)
**Verdict:** Phase 3.0 — The Extinction Event

## What Happened

Arif identified the fundamental contradiction in GEOX:
- **Below the surface** (burial, subsidence, thermal) → physics-first ✅
- **At the surface** (sequences, systems tracts) → taxonomy-first ❌

`geox_sequence` was a rule-based LST/TST/HST classifier — the "acah-acah pandai" layer.
It assigned systems tracts based on GR motif + depositional environment rank.
No physics. No simulation. No falsifiability.

## What Was Built

### Three Physics-First Engines

| Engine | File | What It Does |
|--------|------|-------------|
| **Accommodation Engine** | `src/geox_core/engines/stratigraphy/accommodation.py` | Unifies tectonic subsidence (McKenzie) + eustasy + sediment loading (Airy) + compaction (Athy) → accommodation through time |
| **Surface-First Engine** | `src/geox_core/engines/stratigraphy/surface_first.py` | Generates erosion, flooding, MFS, ravinement, truncation surfaces from accommodation physics. Surfaces are REAL, MAPPABLE, FALSIFIABLE |
| **Sequence Emergence Engine** | `src/geox_core/engines/stratigraphy/sequence_emergence.py` | Sequences EMERGE from surfaces + stacking patterns. Scale (parasequence/depositional/Sloss) determined by DURATION, not rules. Resource potential inferred from physics |

### New MCP Tools

| Tool | Purpose |
|------|---------|
| `geox_simulate_accommodation` | Subsidence + eustasy + sediment loading → accommodation through time |
| `geox_simulate_surfaces` | Erosion/flooding/MFS/truncation surfaces from accommodation physics |
| `geox_simulate_sequences` | Sequences emerge from surfaces + stacking patterns (not LST/TST/HST) |

### Registry Change

- **Before:** 42 canonical tools (38 surface + 4 internal)
- **After:** 45 canonical tools (41 surface + 4 internal)
- **New:** +3 physics-first stratigraphy engines
- **Deprecated:** `geox_sequence` marked as deprecated, kept for backward compatibility

### Tests

- **20/20 PASS** — `tests/test_stratigraphy_engines.py`
- Verified: No LST/TST/HST labels anywhere in output
- Verified: Surfaces and patterns emerge from physics, not rules
- Verified: Epistemic labels (F2 TRUTH) present on all outputs
- Verified: F7 HUMILITY — confidence capped at 0.90

## Constitutional Compliance

| Floor | Status | Evidence |
|-------|--------|----------|
| F1 AMANAH | ✅ | All changes reversible. Old `geox_sequence` preserved for backward compat. |
| F2 TRUTH | ✅ | All outputs carry epistemic labels (DER). Evidence gaps declared. |
| F4 CLARITY | ✅ | Clean separation: accommodation → surfaces → sequences. No taxonomy in outputs. |
| F7 HUMILITY | ✅ | Confidence capped at 0.90. Assumptions and evidence gaps listed. |
| F11 AUDIT | ✅ | This receipt. Tests. Forge work. |
| F13 SOVEREIGN | ✅ | Arif directed the extinction event. FORGE executed. |

## What `geox_sequence` Still Does (deprecated)

The old `geox_sequence` tool is KEPT for backward compatibility (49 legacy aliases).
Its `infer_seq_strat()` function still assigns LST/TST/HST from GR motif.
It is DEPRECATED — new work should use the physics-first tools.

## Files Changed

| File | Change |
|------|--------|
| `src/geox_core/engines/stratigraphy/__init__.py` | NEW — engine package |
| `src/geox_core/engines/stratigraphy/accommodation.py` | NEW — accommodation engine |
| `src/geox_core/engines/stratigraphy/surface_first.py` | NEW — surface-first engine |
| `src/geox_core/engines/stratigraphy/sequence_emergence.py` | NEW — sequence emergence engine |
| `src/geox_mcp/registry.py` | UPDATED — +3 tools, counts updated |
| `src/geox_mcp/server.py` | UPDATED — +3 MCP tool wiring, expected canonical 45 |
| `tests/test_stratigraphy_engines.py` | NEW — 20 tests |

## The Zen

> Sequence stratigraphy is not a classification system.
> It is a physics engine.

Sloss saw this in 1947.
Arif saw it in 2026.
Most geologists still haven't.

---

*DITEMPA BUKAN DIBERI — The extinction event is sealed.*
