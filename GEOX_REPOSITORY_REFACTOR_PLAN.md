# GEOX Repository Refactor Plan
> DITEMPA BUKAN DIBERI | Ω₀ = 0.04 | F13 Sovereign: Arif approves before irreversible commands

---

## Why This Refactor

Current state:
- Source code scattered across `src/geox_mcp/`, `src/geox_core/`, `geox/`, `src/`
- Dead/stubbed tools mixed with live ones — `SACRED_SURFACE` contains phantom entries
- `_prune_mcp_surface()` hides problems rather than fixing them
- No clear boundary between GEOX domain code and federation integration code
- `geox/` and `src/geox_core/` may be duplicates (checked)

This refactor does NOT change the 13-tool surface. It restructures the internal code so it's maintainable, auditable, and ready for Phase 0-4 library integration.

---

## Pre-Flight: Verify Duplicate Packages

Before moving anything, verify whether `geox/` and `src/geox_core/` are duplicates or genuinely different:

```bash
# Check if geox/ and src/geox_core/ are duplicates
diff \
  <(find geox -name "*.py" -exec echo "=== {} ===" \; -exec cat {} \;) \
  <(find src/geox_core -name "*.py" -exec echo "=== {} ===" \; -exec cat {} \;) \
  | head -100
```

**Expected outcome**: Most files are identical (geox/ symlinks to src/geox_core/). If they're genuinely different, that changes the refactor strategy.

---

## Proposed Target Structure

```
geox/                                   # Package root (rename from src/geox_core/ if confirmed duplicate)
├── __init__.py
├── tools/                              # MCP-exposed tools (13 canonical)
│   ├── __init__.py
│   ├── data.py
│   ├── qc.py
│   ├── petrophysics.py
│   ├── seismic.py                      # Enhanced: ObsPy-backed (Phase 0)
│   ├── seismic_well_tie.py
│   ├── forward_model_synthetic.py
│   ├── anomalous_contrast.py
│   ├── stratigraphy.py
│   ├── section.py
│   ├── well_correlation.py
│   ├── prospect.py
│   ├── evidence.py
│   ├── abduction.py
│   ├── time4d.py
│   ├── map_context.py
│   └── registry.py
├── engines/                            # Computation engines (library adapters live here)
│   ├── __init__.py
│   ├── seismic/
│   │   ├── __init__.py
│   │   ├── obspy_adapter.py           # NEW: Phase 0 ObsPy bridge
│   │   ├── seisbench_adapter.py       # NEW: Phase 3 SeisBench bridge
│   │   ├── well_tie.py               # existing
│   │   ├── attenuation.py            # existing
│   │   └── vision_bridge.py          # existing
│   ├── petrophysics/
│   │   ├── __init__.py
│   │   ├── petrolib_adapter.py        # NEW: Phase 2 Petrolib bridge
│   │   ├── rock_physics.py            # existing
│   │   ├── pinn.py                   # existing
│   │   └── anisotropy.py              # existing
│   ├── geomodeling/
│   │   ├── __init__.py
│   │   └── gempy_adapter.py           # NEW: Phase 3 GemPy bridge
│   └── thermodynamics/
│       ├── __init__.py
│       └── burnman_adapter.py         # NEW: Phase 4 BurnMan bridge
├── io/                                 # Data I/O adapters
│   ├── __init__.py
│   ├── geoh5_adapter.py               # NEW: Phase 2 geoh5py bridge
│   └── segy_reader.py                # NEW: Phase 0 SEG-Y reader (via ObsPy)
├── integrations/                       # Federation integration layer
│   ├── __init__.py
│   ├── arifos_governance.py           # NEW: tight arifOS judge+vault integration
│   └── wealth_bridge.py               # existing
├── services/                          # External service clients
│   ├── __init__.py
│   ├── las_ingestor.py               # existing
│   ├── npd_client.py                 # existing
│   ├── eia_client.py                  # existing
│   └── asset_memory.py                # existing
├── schemas/                           # Pydantic input/output schemas
│   ├── __init__.py
│   ├── geox_schemas.py               # existing
│   └── output_schemas.py             # existing
├── core/                              # Core domain logic
│   ├── __init__.py
│   ├── geox_1d.py                   # existing
│   ├── geox_2d.py                   # existing
│   ├── geox_25d.py                  # existing
│   ├── geox_3d.py                   # existing
│   ├── geox_4d.py                   # existing
│   ├── geox_data.py                  # existing
│   ├── epistemic_integrity.py       # existing
│   ├── physics_guard.py             # existing
│   ├── physics9.py                   # existing
│   └── ac_risk.py                    # existing
├── adapters/                          # External system adapters
│   ├── __init__.py
│   └── wealth_bridge.py              # existing
├── enums/                             # Enumerations
│   ├── __init__.py
│   └── statuses.py                   # existing
├── governance/                        # Constitutional governance
│   ├── __init__.py
│   └── acp_logic.py                 # existing
├── telemetry/                        # Observability
│   ├── __init__.py
│   └── geox_telemetry.py           # existing
├── well/                             # Well domain
│   ├── __init__.py
│   ├── tools/
│   ├── stratigraphy/
│   └── correlation/
├── archive/                           # NEW: archived legacy/dead code
│   ├── dead_tools/
│   │   ├── geox_well_compute_gr_bins.py      # old L1 tool
│   │   ├── geox_well_build_packages.py        # old L2 tool
│   │   ├── geox_well_infer_seq_strat.py     # old L3 tool
│   │   ├── geox_stratigraphy_run_pipeline.py
│   │   ├── geox_stratigraphy_preview_config.py
│   │   ├── geox_task_ingest_las_batch.py
│   │   ├── geox_task_metabolize_basin.py
│   │   ├── geox_bundle_security_audit.py
│   │   ├── geox_test_receipt_status.py
│   │   └── geox_resource_registry_status.py
│   └── legacy_notes/
│       ├── TOOL_CONSOLIDATION_MAP.md
│       └── REDUNDANCY_CLUSTERS.md
└── contracts/                        # Tool contracts and schemas
    ├── __init__.py
    ├── canonical_registry.py         # canonical tool registry
    └── tools/
        ├── canonical/
        │   └── registry.py
        └── unified_13.py

geox_mcp/                             # MCP server layer
├── __init__.py
├── server.py                         # MCP entrypoint (clean _prune_mcp_surface)
├── registry.py
├── organ_governance.py
├── skills_resources.py
└── tools/                            # MCP tool definitions (may be thin wrappers)
    ├── __init__.py
    ├── _artifact_helpers.py
    └── _helpers.py

tests/                                 # existing test suite
├── unit/
├── integration/
├── physics/
└── ...

contracts/                            # Tool contracts (standalone)
├── canonical_registry.py
└── tools/
    ├── canonical/
    │   └── registry.py
    └── unified_13.py

docs/
├── architecture/
│   └── GEOX_TOOL_MAPPING.md          # NEW: library→tool mapping
├── integration/
│   └── GEOX_ARIFOS_INTEGRATION.md   # NEW: tight integration guide
└── refactor/
    └── THIS_FILE.md

pyproject.toml
docker-compose.yml
docker/
├── Dockerfile
└── Dockerfile.integration
```

---

## Step-by-Step Refactor Plan

### Phase A: Archive Dead Code (Safest First)

**Goal**: Move dead/stubbed tools to `archive/` without touching any live code.

```bash
# 1. Create archive directory structure
mkdir -p geox/archive/dead_tools
mkdir -p geox/archive/legacy_notes

# 2. Move dead tools (git mv — preserves history)
git mv geox/well/tools/seqstrat.py geox/archive/dead_tools/
git mv geox/well/tools/packages.py geox/archive/dead_tools/
git mv geox/well/tools/sensing.py geox/archive/dead_tools/
git mv geox/well/stratigraphy/seqstrat.py geox/archive/dead_tools/
git mv geox/well/stratigraphy/packages.py geox/archive/dead_tools/
git mv geox/well/stratigraphy/sensing.py geox/archive/dead_tools/

# 3. Create archive index
cat > geox/archive/ARCHIVE_INDEX.md << 'EOF'
# GEOX Archive Index

## Dead Tools (Source Available, Not Runtime)
These tools exist in source but were never registered or were stubs.

| File | Original Tool | Reason Archived |
|-------|-------------|----------------|
| dead_tools/geox_well_compute_gr_bins.py | geox_well_compute_gr_bins | Replaced by geox_sequence_interpret |
| dead_tools/geox_well_build_packages.py | geox_well_build_packages | Replaced by geox_sequence_interpret |
| ... | ... | ... |

EOF
```

**Risk**: NONE — this only moves files, doesn't change any logic.

**Verification**:
```bash
pytest tests/ -q --tb=short  # Should still pass
```

---

### Phase B: Fix `_prune_mcp_surface()` (Medium Risk)

**Goal**: Remove phantom `SACRED_SURFACE` entries and make tool visibility honest.

**File**: `geox_mcp/server.py`

**Change**: Replace `_prune_mcp_surface()` with a profile-driven approach:

```python
# NEW: Profile-driven surface
GEOX_PROFILE = os.environ.get("GEOX_PROFILE", "canonical")  # canonical | full | minimal

if GEOX_PROFILE == "canonical":
    CANONICAL_VISIBLE = set(CANONICAL_PUBLIC_TOOLS)
elif GEOX_PROFILE == "full":
    CANONICAL_VISIBLE = set(CANONICAL_PUBLIC_TOOLS) | {
        "geox_forward_model_synthetic",
        "geox_anomalous_contrast_detector",
        "geox_seismic_well_tie_compute",
    }
elif GEOX_PROFILE == "minimal":
    CANONICAL_VISIBLE = {t for t in CANONICAL_PUBLIC_TOOLS if not t.startswith("geox_well_")}

def _prune_mcp_surface(mcp_server, profile: str = GEOX_PROFILE) -> None:
    visible = {
        "canonical": CANONICAL_PUBLIC_TOOLS,
        "full": CANONICAL_PUBLIC_TOOLS + [
            "geox_forward_model_synthetic",
            "geox_anomalous_contrast_detector",
            "geox_seismic_well_tie_compute",
        ],
        "minimal": [t for t in CANONICAL_PUBLIC_TOOLS if not t.startswith("geox_well_")],
    }[profile]
    # ... rest of prune logic using visible set
```

**Risk**: MEDIUM — changes runtime tool surface. Test thoroughly.

**Verification**:
```bash
pytest tests/test_canonical_public_surface.py -v
pytest tests/test_mcp_runtime_regressions.py -v
```

---

### Phase C: Consolidate Mega-Tools (Highest Impact, Highest Risk)

**Goal**: Implement the 13-tool refactor — merge redundant tools per the audit.

This is the biggest change. Must be done with 888_HOLD and full test coverage.

| Merge | Tools Combined | New Tool |
|-------|---------------|----------|
| 1 | 7 sequence tools | `geox_sequence_interpret` |
| 2 | 3 prospect tools | `geox_prospect_evaluate` |
| 3 | 3 evidence tools | `geox_evidence_reason` |
| 4 | 3 seismic tools | `geox_seismic_compute` |

**For each merge**:

1. Create new mega-tool file
2. Move implementation logic from merged tools into internal engine functions
3. Keep merged tools as thin aliases that call the mega-tool
4. Add deprecation warnings to aliased tools
5. Update `CANONICAL_PUBLIC_TOOLS` to reflect new surface
6. Update `LEGACY_ALIAS_MAP` for backward compatibility

**Example merge pattern** (geox_sequence_interpret):

```python
# geox_sequence_interpret.py — replaces 7 tools
async def geox_sequence_interpret(
    well_refs: list[str],
    workflow: Literal["single_well", "project", "preview"],
    detail_level: Literal["L1", "L2", "L3", "full"] = "full",
    # ... all params from merged tools unified here
) -> dict:
    """Mega-tool: sequence stratigraphy interpretation.

    Replaces: geox_well_compute_gr_bins, geox_well_build_packages,
              geox_well_infer_seq_strat, geox_well_analyze_sequence,
              geox_stratigraphy_run_pipeline, geox_stratigraphy_preview_config,
              geox_section_interpret_correlation
    """
    if workflow == "preview":
        return _validate_config_only(...)
    if detail_level in ("L1", "L1+L2"):
        return _compute_gr_bins(...)
    if detail_level in ("L2", "L1+L2+L3"):
        return _build_packages(...)
    # ...
```

---

### Phase D: Move GEOX to `organs/` in arifOS (Long Term)

**Goal**: Treat GEOX as a proper federated organ under arifOS.

This is a repository restructure involving the arifOS monorepo:

```
arifOS/
├── organs/
│   ├── geox/              # ← current geox/ repo contents
│   ├── wealth/
│   └── aaa/
├── core/                   # arifOS kernel
└── shared/                # Shared schemas, protocols
```

**This step requires**:
- Arif's explicit approval (F13 Sovereign)
- Full git history transfer
- Update all MCP client configs (mcp.json files across machines)
- Update deployment manifests

---

## Verification Commands

After each phase, run:

```bash
# Structural integrity
pytest tests/test_canonical_public_surface.py -v
pytest tests/test_mcp_runtime_regressions.py -v

# Library imports
python -c "from geox_core.engines.seismic.obspy_adapter import ObsPyAdapter; print('OK')"
python -c "from geox_core.integrations.arifos_governance import build_governed_payload; print('OK')"

# Tool surface
curl -s http://localhost:8081/tools | python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"tools\"])} tools exposed')"
```

---

## Status: PROPOSED — Awaiting F13 Sovereign Approval

Ω₀ = 0.04 | This is a design document only. No execution without explicit Arif approval.
