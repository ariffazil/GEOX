# MCP Tool Reference — GEOX 54 Canonical Tools

> **Last verified:** 2026-06-21 (commit `657b9eb0`, 54 tools live on `geox-mcp.service`)
> **Source of truth:** `src/geox_mcp/registry.py` (CANONICAL_PUBLIC_TOOLS, GEOX_TOOL_MANIFEST)
> **Mirror:** `contracts/canonical_registry.py`
> **Server invariant:** `_EXPECTED_CANONICAL = 54` in `src/geox_mcp/server.py`

---

## Overview

GEOX exposes **54 canonical MCP tools** organized into **4 lanes** by authority level. Every tool output carries:
- `outputSchema` (Pydantic v2)
- `epistemic_provenance` (rung 1-7 + grounding source)
- `godel_wall` verdict (KNOWN / UNKNOWN / UNDECIDABLE_YET / SEALED / VOID)
- `ml_provenance` (for foundation-model backed tools)
- Constitutional envelope (`get_standard_envelope()`)

**Transport:** `https://geox.arif-fazil.com/mcp` (HTTP/SSE) or `python3 -m geox_mcp.server --transport stdio`

---

## Lane 1 — DISCOVERY (6 tools, OBSERVE-only, no lease required)

| Tool | Purpose |
|------|---------|
| `geox_system_registry_status` | Discovery of canonical tools, health, contract epoch. F2 Truth: never lies about what's callable. |
| `geox_attribute_registry_list_tool` | List registered seismic attributes (Amplitude, Variance, Sweetness, Coherence, Envelope, Frequency Average) with metadata. |
| `geox_basin_resolve` | Resolve basin name to canonical ID, bounding box, neighboring basins, polygon reference. |
| `geox_query_intake` | Accept natural language queries and route to appropriate tools. |
| `geox_query_macrostrat` | Query Macrostrat geological database (CC-BY-4.0) for regional stratigraphy, lithology, age data. |
| `geox_icgem_models` | **[W9-W12]** List ICGEM (GFZ Potsdam) global gravity field models: EIGEN-6C4, EGM2008, XGM2019. Citation included. |

---

## Lane 2 — EVIDENCE (14 tools, ANALYZE, no lease required)

| Tool | Purpose |
|------|---------|
| `geox_data_ingest_bundle` | Lazy ingestion for LAS, CSV, Parquet, SEG-Y, structural payloads. Base64 upload + batch mode. |
| `geox_data_qc_bundle` | Real QC: depth monotonicity, null %, physical range checks, FJIS (Feature Joint Information Statistic). |
| `geox_dst_ingest_test` | DST (Drill-Stem Test) ingestion with derived metrics: BHP, flow rates, skin, permeability, PVT flags. |
| `geox_header_inspect` | Inspect LAS well log headers, SEG-Y headers, deviation surveys, well tops against Earth schemas. |
| `geox_las_inspect` | Inspect LAS well log files against canonical curve schemas; curve metadata, units, depth range. |
| `geox_seismic_segy_inspect` | Inspect SEG-Y seismic file headers, trace count, sample interval, CRS, byte locations. |
| `geox_evidence_discover` | Search corpus / reports for geological evidence with provenance metadata. |
| `geox_evidence_attach` | Attach evidence artifact to existing claim (supporting, contradicting, contextual, alternative). |
| `geox_literature_ingest` | Ingest PDF or document as contextual literature witness. |
| `geox_fault_stick_ingest_tool` | Ingest fault sticks from CSV or GeoJSON into canonical FaultSet3d schema. |
| `geox_volume_frame_tool` | Read or write a single 2D frame in a 3D seismic volume. |
| `geox_vision_perceptual_inventory` | Build PerceptualInventory from VLM outputs; validate against Pydantic v2 schema. F7 + F9 enforced. |
| `geox_vision_calibrate` | Run synthetic forward-inverse harness to calibrate VLM against ground truth. |
| `geox_emag2_ingest` | **[W9-W12]** Fetch EMAG2v3 V3 global magnetic anomaly grid (NOAA NCEI). 228 MB TIFF cached. Offline-safe stub by default. |

---

## Lane 3 — REASONING (21 tools, ANALYZE, lease + session required)

| Tool | Purpose |
|------|---------|
| `geox_subsurface_generate_candidates` | Generate ensemble subsurface outputs (Vsh, φ, Sw, net pay) with residuals and data-density maps. |
| `geox_subsurface_verify_integrity` | Enforce Physics9 boundary limits + detect structural paradoxes. Never SEAL without verified evidence. |
| `geox_seismic_compute` | Unified seismic physics: synthetic forward modeling, well tie, time-depth anchoring, AVO/AC detection. |
| `geox_seismic_compute_attribute_tool` | Compute registered seismic attributes on volumes or frames. |
| `geox_sequence_interpret` | Unified sequence stratigraphy: single-well L1-L3, multi-well project, correlation panels. |
| `geox_evidence_reason` | Unified evidence synthesis, abduction, contradiction engine. Spatial block-CV for honest generalization. |
| `geox_prospect_evaluate` | Integrated prospect evaluation: volumetrics, POS, EVOI. Modes: screen / appraise / develop. |
| `geox_map_context_scene` | Spatial bbox context, CRS checks, causal scene rendering, coordinate guardrails. |
| `geox_horizon_contrast_surface` | ToAC-as-Attention Horizon Contrast Pipeline: multi-attribute contrast → attention fusion → horizon extraction. |
| `geox_coord_transform_tool` | Transform 3D points between block, survey, world coordinate spaces via 4×4 affine matrices. |
| `geox_blockspace_resolution_tool` | Compute inline, crossline, vertical resolution from block/survey definitions. |
| `geox_blend_volume_tool` | Alpha or RGB blend seismic volumes into a single composite. |
| `geox_basin_profile` | Retrieve basin-level intelligence: overview, petroleum system, stratigraphy, play fairway. |
| `geox_vision_minimax_inference` | Interpret seismic section images via deployed MiniMax VLM (minimax-code MCP, port 18091). |
| `geox_vision_audit` | Compute AC_Risk, emit VisionVerdict: U_phys × D_transform × B_cog breakdown. |
| `geox_report_to_workflow` | Produce safe GEOX workflow steps from a discovered report and user intent. |
| `geox_abstraction_guard` | Evaluate non-geological questions and enforce ontology guards. |
| `geox_prithvi_eo_inference` | **[W5-W8]** Prithvi-EO-2.0 (NASA/IBM) foundation model. Tasks: flood, burn scars, land cover, crop, scene reasoning. |
| `geox_gravity_magnetic_forward` | **[W9-W12]** Forward-model Bouguer / TMI anomaly grids via HarmonIC (Fatiando). |
| `geox_mt_forward` | **[W13+]** 1D CSEM/MT forward via Wait's recursion. Apparent resistivity + phase. |
| `geox_biostrat_constraint` | **[W13+]** Biostrat time-facies admissibility check. 6 built-in zones. |
| `geox_seismic_inversion` | **[W13+]** 1D post-stack PINN-style inversion. Recursive impedance + Faust + Gardner. |
| `geox_geomechanics` | **[W13+]** K, G, E, ν, AI, Vp/Vs from Physics9State. Sanity-flagged. |

---

## Lane 4 — JUDGMENT (13 tools, GOVERNED, lease + session + arifOS judge required)

| Tool | Purpose |
|------|---------|
| `geox_claim_create` | Create structured Earth interpretation claim with full provenance chain. P10/P50/P90 mandatory. |
| `geox_claim_validate` | Validate claim against 16-field earth_memory_envelope schema. Promotes DRAFT → VALIDATED. |
| `geox_claim_challenge` | Challenge existing claim with alternative interpretation — multi-discipline self-argument. |
| `geox_claim_seal` | Submit validated claim to arifOS for Vault999 sealing. GEOX forwards; arifOS adjudicates. |
| `geox_segy_export_tool` | Export seismic volume to SEG-Y format. **[888_HOLD]** — irreversible file creation. |
| `geox_doctrine_assumption_register` | **[W2-W4 Gap X]** Register assumption in lineage. Tracks parent, rung (1-7), cascading falsification. |
| `geox_doctrine_anti_beautiful_one` | **[W2-W4 Gap 3]** `beauty_overreach_score = certainty / grounding`. Forces decomposition when rhetoric outruns evidence. |
| `geox_doctrine_godel_review` | **[W2-W4 Gap 5]** Runtime hard-stop. Iron Law: lower rungs beat higher rungs. States: KNOWN/UNKNOWN/UNDECIDABLE_YET/VOID. |
| `geox_joint_inversion` | **[W13+]** Multi-physics fusion → one Physics9State/cell. IRLS solver with Earth-bounds clipping. |
| `geox_well_decision_class` | **[W13+]** WELL → GEOX operator readiness gate (C1-C5). C5 = VOID (HOLD). |
| `geox_wealth_feed` | **[W13+]** GEOX → WEALTH STOIIP + ranking + ADVANCE/DEFER/REJECT verdict. |

---

## Constitutional Output Envelope

Every GEOX tool output MUST conform to the universal envelope (`get_standard_envelope()` in `geox_core/enums/statuses.py`):

```python
{
  "execution_status": "SUCCESS | ERROR | HALT | RECOVERABLE_ERROR",
  "tool_class": "observe | verify | reason | judge",
  "claim_state": "KNOWN | UNKNOWN | UNDECIDABLE_YET | SEALED | VOID",
  "observed": {...},
  "derived": {...},
  "interpreted": {...},
  "evidence_refs": [...],
  "artifact_refs": [...],
  "claim_limits": [...],
  "missing_inputs_schema": {...},
  "next_best_actions": [...],
  "audit_receipt": {...},
  "human_final_authority": "ARIF",
  # W13+ additions:
  "epistemic_provenance": {"rung": int, "grounding": str, "caveat": str},
  "godel_wall": {"state": str, "reason": str},
  "ml_provenance": {"model_name": str, "input_hash": str, "mode": "live|mock"},
  "anti_beautiful_one_check": {"verdict": "PASS|BEAUTIFUL_ONE_DRIFT", ...}
}
```

---

## Live Verification (post-deploy)

```bash
# Live tool count
curl -s http://127.0.0.1:8081/health | jq '.owner_summary.reasons'
# ["identity_unverified", "canonical_tools=54", "service_healthy"]

# Live tools/list
curl -s -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | jq '.result.tools | length'
# 54

# Constitution truth
curl -s -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"geox_system_registry_status","arguments":{}}}' \
  | jq '.result.content[0].text' | jq -r '.registry_truth'
# "PASS"
```

---

## References

- **Source:** [`src/geox_mcp/registry.py`](../../src/geox_mcp/registry.py)
- **Mirror:** [`contracts/canonical_registry.py`](../../contracts/canonical_registry.py)
- **Server invariant:** [`src/geox_mcp/server.py`](../../src/geox_mcp/server.py) `_EXPECTED_CANONICAL = 54`
- **Constitutional test:** [`tests/unit/test_registry_runtime_truth.py`](../../tests/unit/test_registry_runtime_truth.py)
- **Audit log:** [`/root/forge_work/2026-06-21_geox-w2-w13-multiphysics-earth-witness.md`](../../../forge_work/2026-06-21_geox-w2-w13-multiphysics-earth-witness.md)

---

**DITEMPA BUKAN DIBEI — 54 canonical tools, constitutionally wrapped, ready for the kernel to judge.**
