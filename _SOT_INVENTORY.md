# GEOX — SOT Inventory Report
**Epoch:** FEDERATION-SOT-20260712-ac8550fa  
**Generated:** 2026-07-13  
**Workspace:** /root/GEOX  
**Organ:** Earth Evidence (arifOS Federation)

---

## 1. Git State

| Property | Value |
|---|---|
| **HEAD commit** | `5bc66284` — "refactor: align tool manifest with registry truth" |
| **Active branch** | `refactor/apex-entropy-20260712` |
| **Dirty files** | 1: `FEDERATION_CONTRACT.md.bak.pre-pointer-2026-07-12` (deleted/staged deletion) |
| **Recent commits** | `5bc66284` (HEAD), `d6eda35d` (fix #120), `58443d54` (ci), `ee887971` (zen migration), `586353f1` (MCP-APPS-FIX) |
| **Remote branches** | main, archive/pre-consolidation-2026-07-12, fix/geox-120-surface-drift, pr-121, refactor/apex-entropy-20260712, refactor/zen-surface-reduction, zen-migration-2026-07-11 |

## 2. README.md (First 30 Lines)

- SOT-MANIFEST block (lines 1-20) declares:
  - **Owner:** Arif (F13 SOVEREIGN)
  - **Last verified:** 2026-07-12T08:30Z
  - **Live commit:** 4784103d (note: differs from git HEAD 5bc66284 — possible race or the README manifest is stale)
  - **Public tools declared:** 26 (but health endpoint says 32)
  - **Internal tools declared:** 55
  - **Owner summary:** GREEN
  - **Machine SOT:** CANONICAL_PUBLIC_SURFACE.json
  - **Truth rule:** "tools/list + /health beat any static count in prose"

## 3. src/ Directory Structure

- **Package layout:** `src/geox/` (EGS subpackage), `src/geox_mcp/` (MCP server), `src/geox_core/` (core engine)
- **Total Python files:** 498
- **Total directories in src/:** 163
- **Key subdirectories:**
  - `src/geox_mcp/tools/` — tool implementations (biostrat/, discovery/, kernel/, basin_engines/, deep_time/)
  - `src/geox_mcp/epistemic/` — epistemic metabolism engine (7 modules)
  - `src/geox_mcp/apps/` — MCP app registration (well-desk, workbench)
  - `src/geox_mcp/resources/` — MCP resource definitions
  - `src/geox_mcp/prompts/` — MCP prompt definitions
  - `src/geox_mcp/ui/` — UI components
  - `src/geox_core/core/` — canonical core engine modules (31 files)
  - `src/geox_core/lem/` — physics-first simulation (LEM schemas)
  - `src/geox_core/seismic/`, `src/geox_core/well/`, `src/geox_core/avo/` — domain engines

## 4. Triple `core/` Directories — IDENTIFIED

All three exist and are **symlink mirrors** pointing to the single source of truth:

| Path | Type | Content |
|---|---|---|
| `/root/GEOX/core/` | **Symlink farm** (30 symlinks + 2 real files) | 28 symlinks → `../src/geox_core/core/` + 2 real files: `rock_physics_engine.py` (27KB), `tool_registry.py` (10KB) |
| `/root/GEOX/geox/core/` | **Symlink farm** (30 symlinks) | All symlinks → `../../src/geox_core/core/` except `rock_physics_engine.py` → `../../core/rock_physics_engine.py` (cross-symlink!) |
| `/root/GEOX/src/geox_core/core/` | **Canonical origin** | 31 real files (no symlinks) |

**Assessment:** Functionally unified (all point to same origin), but structurally redundant.  
The `geox/core/` → `../../core/rock_physics_engine.py` chain is a double-hop symlink (geox/core/rock_physics_engine.py → ../../core/rock_physics_engine.py, which is itself a symlink). Fragile but currently resolvable.

**FINDING: DUPLICATE CORE PATHS CONFIRMED. 3 directories named `core/` with 30 overlapping files each. Not a data duplication risk (symlinks preserve source), but a maintenance hazard.**

## 5. MCP Surface — Live Health Check

| Endpoint | Response |
|---|---|
| `GET /health` | **Healthy** — `public_tools=32`, version `v2026.07.06-phase3.1-rsi-pipeline`, owner_summary GREEN |
| `GET /` | Service index with endpoints |
| `GET /tools` | **32 live tools** (count confirmed: direct JSON query) |

### 32 Live MCP Tools (from /tools endpoint)

| # | Tool Name | Domain |
|---|---|---|
| 1 | geox_well_ingest | Well |
| 2 | geox_well_qc | Well |
| 3 | geox_well_desk_open | Well |
| 4 | geox_well_desk_publish | Well |
| 5 | geox_render_well_panel | Well |
| 6 | geox_petrophysics | Petrophysics |
| 7 | geox_sequence | Sequence |
| 8 | geox_seismic_ingest | Seismic |
| 9 | geox_seismic_compute | Seismic |
| 10 | geox_seismic_interpret | Seismic |
| 11 | geox_vision | Seismic |
| 12 | geox_subsurface_model | Subsurface |
| 13 | geox_geomechanics | Geomechanics |
| 14 | geox_basin | Basin |
| 15 | geox_deep_time_state | Deep Time |
| 16 | geox_surface_status | Surface |
| 17 | geox_claim | Claim |
| 18 | geox_evidence | Evidence |
| 19 | geox_prospect | Prospect |
| 20 | geox_map_context_scene | Map |
| 21 | geox_contrast_detect | Contrast |
| 22 | geox_biostrat_parse | Biostrat |
| 23 | geox_biostrat_falsify | Biostrat |
| 24 | geox_basin_backstrip | Basin |
| 25 | geox_sediment_mass_balance | Basin |
| 26 | geox_thermal_maturity_history | Basin |
| 27 | geox_claim_graph_evaluate | Claim |
| 28 | geox_consequence_footprint | Consequence |
| 29 | geox_optionality_loss | Consequence |
| 30 | geox_feedback_integrity | Integrity |
| 31 | geox_material_truth_challenge | Truth |
| 32 | geox_cascade_pathway | Cascade |

**Count discrepancy:** README's SOT-MANIFEST declares 26 public tools; live /health says 32.  
AGENTS.md mentions "registry/manifest may declare 77 as target" but live runtime is 32.

## 6. Parallel Vault Directories

**Only one vault found:** `/root/GEOX/999_vault/`
- **8 seal artifacts:** 999_SEAL.json, seal_*.json (3x), seal_knowledge_taxonomy, geox-registry-audit, repair_anchor.json, audit.jsonl (31KB, actively appended)
- **No parallel vaults** detected elsewhere in the repo tree

**Assessment:** Single canonical vault. Clean.

## 7. Epistemic Labeling of Geological Claims

### Framework: 7-Rung Epistemic Ladder

GEOX implements a formal epistemic hierarchy (from `src/geox_core/assumption_lineage.py`):

| Rung | Name | Label Code |
|---|---|---|
| 1 | SIGNAL | OBS |
| 2 | MEASUREMENT | OBS |
| 3 | DERIVATION | DER |
| 4 | INTERPRETATION | INT |
| 5 | MODEL | INT/SPEC |
| 6 | JUDGMENT | SPEC |
| 7 | NARRATIVE | SPEC |

**Simplified 4-class surface label** (`epistemic_label`):
- **OBS** (Observation) — Raw signals, measurements (Rungs 1-2)
- **DER** (Derived) — Computed from observations (Rung 3)
- **INT** (Interpretation) — Geologist interpretation, model output (Rungs 4-5)
- **SPEC** (Speculation) — Judgment, narrative (Rungs 6-7)

### Where Labeling Is Enforced

| Layer | Mechanism |
|---|---|
| `geox_claim` tool | `truth_class` param: FACT / INTERPRETATION / SPECULATION + `epistemic_label` |
| `geox_evidence` tool | `evidence_type` + `epistemic_label` wiring |
| `assumption_lineage.py` | Per-assumption `epistemic_label: Literal["OBS","DER","INT","SPEC"]` |
| `tools_wiring.py` | `epistemic_label` injected on tool dispatch |
| `epistemic/epistemic_runtime.py` | EpistemicEventType (RUNG_ASCENT/DESCENT, CONTRADICTION, etc.) |
| `epistemic/meta_epistemic_audit.py` | Post-hoc constitutional audit of label integrity |
| `epistemic/godel_wall.py` | Gödel Wall — prevents sealing underdetermined claims |
| `epistemic/contradiction_ontology.py` | Iron law: lower-rung claims beat higher-rung claims |
| `pai_receipt.py` | `truth_class` in receipt structure |
| `floor_enforcement.py` | F2 TRUTH floor enforcement |

### Key Constitutional Rules (Epistemic)

1. **Iron Law:** A lower-rung claim (e.g., MEASUREMENT) always beats a higher-rung claim (e.g., MODEL) in contradiction
2. **Gödel Wall:** A claim cannot be sealed if its closure conditions depend on assumptions at equal or higher rung
3. **Beautiful One Detection** (`anti_beautiful_one.py`): Flags rhetorical confidence exceeding evidentiary density
4. **Meta-Audit** (`meta_epistemic_audit.py`): Post-hoc constitutional audit returns CONSTITUTIONAL/DEVIATION/VIOLATION

**Assessment:** GEOX has a mature epistemic labeling framework with enforcement at multiple levels — claim creation, runtime event tracking, contradiction resolution, Gödel wall, and meta-audit. This exceeds typical labeling in geological software.

---

## Findings Summary

| Category | Finding | Severity |
|---|---|---|
| **Git** | On branch `refactor/apex-entropy-20260712`, 1 dirty file (deleted FEDERATION_CONTRACT backup) | 🟡 Low |
| **Core paths** | 3 redundant `core/` directories (symlink farms to single source `src/geox_core/core/`) | 🟡 Medium — maintenance hazard |
| **Tool count** | Discrepancy: README says 26, live /health says 32, AGENTS.md mentions 77 canonical target | 🟡 Medium — documentation drift |
| **Vault** | Single canonical vault at `/root/GEOX/999_vault/` — no parallel vaults | 🟢 Clean |
| **Epistemic labels** | Full 7-rung ladder with 4-class surface, Gödel Wall, contradiction ontology, meta-audit | 🟢 Strong |

**Files created:** `/root/GEOX/_SOT_INVENTORY.md`
