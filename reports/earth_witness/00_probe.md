# GEOX Earth Witness Probe Report
**Path:** `/root/GEOX/reports/earth_witness/00_probe.md`  
**Date:** 2026-10-03  
**Auditor / Clerk:** Antigravity (FI-004) under Sovereign Directive `ARIFOS::GEOX::EARTH_WITNESS_SLICE::v1`  
**Classification:** EVIDENCE ONLY (No runtime fixes in Phase 0)  

---

## 0.1 Git Reality & Branch Posture

```
Branch: main (up to date with origin/main)
HEAD Commit: 17802197 feat(basins): SRU age + stage settlement + cross-province invariance rules (F13 2026-10-01)
Tag: v2026.10.01

Recent 5 Commits:
17802197 feat(basins): SRU age + stage settlement + cross-province invariance rules (F13 2026-10-01)
79e372e5 merge: feat/mcp-dual-era-2026-07-28 → main — canonical surface reconcile (BL surface ruling 2026-09-30)
6dacdc4f fix(tests): use snake_case annotation lookups + skip App widgets
e52c4e9e fix(docs): expand README to 343 lines + add CONTEXT.md + RUNBOOK.md
e3e2dfa9 fix(tests): adjust GEOX MCP readiness test to current surface

Working Tree State:
- Staged renames: docs/GEOX_FORGE_FLOW_AGENT_PROMPT.md -> _archive/2026-10-01/, docs/README-FULL.md -> _archive/2026-10-01/
- Unstaged edits: .github/workflows/09-boundary-ratchet.yml, README.md, contracts/tools.yaml, scripts/generate_all_surfaces.py, src/geox_mcp/generated/CANONICAL_PUBLIC_SURFACE.json, src/geox_mcp/geox_middleware.py, src/geox_mcp/registry.py, src/geox_mcp/tools_manifest.yaml, tools.json, tools_sot.yaml
```

---

## 0.2 Live Surface vs Declared Surface & Drift Analysis

### Gate Verdict: LIVE MCP = UNKNOWN (Sandboxed Network Boundary)
Direct TCP probe to `127.0.0.1:8081` from the sandbox returned `Direct IP access is not allowed`. Per Phase 0 Gate rules:
> **GATE:** if live MCP unreachable -> report UNKNOWN + continue on code only.

### Surface Drift Table

| Tool Name | In `registry.py` (Public) | In Live MCP | In `tools_sot.yaml` | In `contracts/tools.yaml` | In UI Bridge (`geox-mcp-bridge.js`) | Drift Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `geox_basin` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_basin_backstrip` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Bridge calls internal/mode via legacy name |
| `geox_calibration_register_witness` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical compute tool; UI bridge does not call directly |
| `geox_claim` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_claim_graph_evaluate` | ❌ (GHOST) | UNKNOWN | ❌ | ❌ | ✅ | **DRIFT:** In `GHOST_TOOLS` (deregistered 2026-07-29); UI bridge still calls it |
| `geox_contrast_metabolize` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical seismic contrast tool |
| `geox_contradiction_scan` | ❌ (Audit-only) | UNKNOWN | ❌ | ❌ | ✅ | Audit-only; RT1 guard blocks external calls |
| `geox_deep_time` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_deep_time_state` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Bridge calls sub-mode |
| `geox_evidence` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Bridge calls internal mode |
| `geox_extract_display_proxy` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public compute tool |
| `geox_extract_native_trace` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public compute tool |
| `geox_falsify` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Mode on `geox_claim` |
| `geox_geomechanics` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_glof` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical hazard tool |
| `geox_gravmag_studio` | ❌ (GHOST) | UNKNOWN | ❌ | ❌ | ✅ | **DRIFT:** In `GHOST_TOOLS`; UI bridge still calls it |
| `geox_lem_predict` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Bridge calls internal engine |
| `geox_list_registered_sources` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public compute tool |
| `geox_map` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_model` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_paleobiodb_query` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_petrophysics` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_prospect` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_register_native_source` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_sediment_mass_balance` | ❌ (GHOST) | UNKNOWN | ❌ | ❌ | ✅ | **DRIFT:** In `GHOST_TOOLS`; UI bridge still calls it |
| `geox_seismic_cognition` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Bridge calls internal engine |
| `geox_seismic_compute` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_seismic_ingest` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_seismic_interpret` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_sequence` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Mode on basin/stratigraphy |
| `geox_simulate_accommodation` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Mode on basin/sediment |
| `geox_simulate_sequences` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Mode on basin/sediment |
| `geox_source` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_spatial` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_subsurface_model` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Sub-mode of `geox_model` |
| `geox_surface_status` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_temporal` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_thermal_maturity_history` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Mode on `geox_source` / `geox_basin` |
| `geox_tie_preflight` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Sub-mode of `geox_seismic_compute` |
| `geox_tie_receipt` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Sub-mode of `geox_seismic_compute` |
| `geox_to_wealth_bridge` | ❌ (GHOST) | UNKNOWN | ❌ | ❌ | ✅ | **DRIFT:** In `GHOST_TOOLS`; UI bridge still calls it |
| `geox_visual_generate_hypotheses` | ❌ (GHOST) | UNKNOWN | ❌ | ❌ | ✅ | **DRIFT:** In `GHOST_TOOLS` (deregistered 2026-07-29); UI bridge still calls it |
| `geox_visual_understand` | ❌ (NOT IN SOT) | UNKNOWN | ❌ | ❌ | ✅ | **DRIFT:** UI bridge calls it; not in public 26 tools |
| `geox_wavelet_extract_least_squares`| ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Sub-mode of `geox_seismic_compute` |
| `geox_well` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |
| `geox_well_desk` | ❌ (Internal) | UNKNOWN | ❌ | ❌ | ✅ | Sub-mode of `geox_well` |
| `geox_well_ingest` | ✅ | UNKNOWN | ✅ | ✅ | ✅ | Synchronized |
| `geox_well_qc` | ✅ | UNKNOWN | ✅ | ✅ | ❌ | Canonical public tool |

---

## 0.3 Inventory of Vision Path & Hardcoded Backends

1. **`src/geox_mcp/tools/vision.py`**:
   - `DEFAULT_VLM_MCP_URL = os.getenv("GEOX_VLM_MCP_URL", "http://127.0.0.1:18091/mcp")` (Hardcoded port 18091 - MiniMax MCP)
   - `DEFAULT_MIMO_BACKEND_URL = os.getenv("GEOX_MIMO_BACKEND_URL", "http://127.0.0.1:8000/v1")` (Hardcoded port 8000 - MiMo vLLM/SGLang)
   - Tools defined: `geox_vision_perceptual_inventory`, `geox_vision_minimax_inference`, `geox_vision_calibrate`, `geox_vision_audit`.
   - **Finding:** None of these four tools are in `CANONICAL_PUBLIC_TOOLS` (26). They are wired as internal/experimental.

2. **`src/geox_core/engines/vision/`**:
   - `minimax_vlm_adapter.py`: Calls port 18091 or remote endpoint with MiniMax VLM.
   - `mimo_vlm_adapter.py`: Calls localhost:8000 OpenAI-compatible endpoint.
   - `perceptual_inventory.py`: Pydantic schemas (`PerceptualInventory`, `ReflectorObservation`, `FaultObservation`, `AmplitudeZoneObservation`).
   - `vision_test_harness.py`: Synthetic test fixtures.

3. **Design Contracts & Vision Doctrine**:
   - `contracts/IMAGE_METABOLIZER_DESIGN.md`: Status is `DRAFT — awaiting ratification` (2026-07-12). Defines Generate (`geox_render_*`), Consume (`geox_vision_*`), Metabolize (`geox_export_*`).
   - `docs/PHYSICS9_EARTH_WITNESS.md`: Status is `geox_joint_inversion live (IRLS baseline)`. Defines 9 orthogonal Earth state parameters ($\rho, V_p, V_s, \rho_e, \chi, k, P, T, \phi$).
   - `vision/earth_substrate_v1.md`: Status is `OVERCLAIM — HOLD THE SEAL` (2026-07-03). Highlights lack of generic rock/outcrop observation pipeline.

---

## 0.4 UI Bridge Audit (`geox_visual_understand` / `geox_visual_generate_hypotheses`)

- **`geox_visual_generate_hypotheses`**:
  - Found in `src/geox_mcp/registry.py::GHOST_TOOLS` (line 45: `GHOSTED 2026-07-29 — experimental DL, overlaps seismic_interpret`).
  - Active in `geox-mcp-bridge.js`.
  - **Verdict:** Ghosted from public registry; calls from UI will fail or require resurrection/mapping.
- **`geox_visual_understand`**:
  - Found in `geox-mcp-bridge.js` line 440 (`async visualUnderstand(imageBlob, metadata)`).
  - Tested in `tests/test_visual_understand_p0_truth.py`.
  - **Verdict:** Implemented as internal dispatch in `geox_mcp/tools/seismic_vision_ai.py`, but NOT exposed in the 26 canonical public tools.

---

## 0.5 Existing Test Suite Baseline

- `tests/test_vision_v1.py`: **25 PASSED** in 4.47s
- `tests/test_mimo_vision.py`: **16 PASSED** in 0.18s
- `tests/test_visual_understand_p0_truth.py`: **3 PASSED** in 3.97s
- Test run note: `cache_dir=/tmp/.pytest_cache` required to avoid sandbox mount write lock.

---

**Phase 0 Status: COMPLETE.**  
No files mutated outside deliverable report. Proceeding to Phase 1.
