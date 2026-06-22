# GEOX MCP Transport Surface — Manifest

> **Last verified:** 2026-06-22 (W2-W13+ FORGE complete, commit `ead04d1c` on `origin/main`)
> **Source of truth:** `src/geox_mcp/registry.py` (CANONICAL_PUBLIC_TOOLS), `src/geox_mcp/resources/__init__.py` (resource registrations), `src/geox_mcp/prompts/__init__.py` (prompt registrations)
> **Server invariant:** `_EXPECTED_CANONICAL = 54` in `src/geox_mcp/server.py`
> **Transport:** HTTP/SSE (`https://geox.arif-fazil.com/mcp`) or stdio (`python3 -m geox_mcp.server --transport stdio`)
> **SDK:** FastMCP 3.x (Python) — `gofastmcp.com`
> **Spec compliance:** MCP 2025-11-25 (`modelcontextprotocol.io`)

---

## Executive Summary

| Primitive | Count | Lane / Category | Location |
|-----------|-------|-----------------|----------|
| **Tools** | **54** | 4 lanes (Discovery 6 / Evidence 14 / Reasoning 21 / Judgment 13) | `src/geox_mcp/tools/` (45+ files) + decorators in `src/geox_mcp/server.py` |
| **Resources** | **17+** templates | Identity, registry, knowledge pack, literature, basins, claims, artifacts, render | `src/geox_mcp/resources/` (splitting to per-module files) |
| **Prompts** | **11** templates | Earth intelligence (3), discipline (3), red-team (1), reports (3), abstraction guard (1) | `src/geox_mcp/prompts/` (splitting to per-module files) |
| **Sub-servers (mounted)** | 4 | witness, paleoscan, claims, vision | `src/geox_mcp/servers/` |
| **UI App applets** | registered | 3 applet templates (mission_board, health_dashboard, well_desk_dashboard) | `src/geox_mcp/tools/ui_applets.py` |
| **WebMCP HTTP endpoints** | 5 | `/.well-known/webmcp`, `/webmcp`, `/webmcp/tools`, `/webmcp/status`, `/webmcp/call/{tool}` | `src/geox_mcp/webmcp.py` |

**Total MCP primitives: 86+** (54 tools + 17+ resources + 11 prompts + 4 mounted sub-servers + WebMCP endpoints).

---

## 1. TOOLS — 54 Canonical (4 Lanes)

### Lane 1 — DISCOVERY (6 tools, OBSERVE-only, no lease)

| # | Tool | Purpose |
|---|------|---------|
| 1 | `geox_system_registry_status` | Discovery of canonical tools, health, contract epoch. F2 Truth: never lies. |
| 2 | `geox_attribute_registry_list_tool` | List registered seismic attributes with metadata. |
| 3 | `geox_basin_resolve` | Resolve basin name to canonical ID, bounding box, neighboring basins. |
| 4 | `geox_query_intake` | Accept natural language queries and route to tools. |
| 5 | `geox_query_macrostrat` | Query Macrostrat database (CC-BY-4.0) for stratigraphy. |
| 6 | `geox_icgem_models` | **[W9-W12]** List ICGEM (GFZ Potsdam) gravity field models. |

### Lane 2 — EVIDENCE (14 tools, ANALYZE, no lease)

| # | Tool | Purpose |
|---|------|---------|
| 7 | `geox_data_ingest_bundle` | Lazy LAS/CSV/Parquet/SEG-Y ingestion. |
| 8 | `geox_data_qc_bundle` | Real QC: depth monotonicity, null %, physical ranges, FJIS. |
| 9 | `geox_dst_ingest_test` | DST ingestion with derived metrics. |
| 10 | `geox_header_inspect` | Inspect LAS/SEG-Y/deviation/tops headers. |
| 11 | `geox_las_inspect` | LAS curve metadata + units + depth range. |
| 12 | `geox_seismic_segy_inspect` | SEG-Y header inspection. |
| 13 | `geox_evidence_discover` | Search corpus for geological evidence. |
| 14 | `geox_evidence_attach` | Attach evidence to claim (supporting/contradicting/etc.). |
| 15 | `geox_literature_ingest` | PDF ingest as literature witness. |
| 16 | `geox_fault_stick_ingest_tool` | Fault sticks CSV/GeoJSON → FaultSet3d. |
| 17 | `geox_volume_frame_tool` | Read/write 2D frame in 3D seismic volume. |
| 18 | `geox_vision_perceptual_inventory` | PerceptualInventory from VLM, schema-validated. |
| 19 | `geox_vision_calibrate` | VLM forward-inverse calibration harness. |
| 20 | `geox_emag2_ingest` | **[W9-W12]** EMAG2v3 global magnetic anomaly grid (NOAA NCEI). |

### Lane 3 — REASONING (21 tools, ANALYZE, lease + session)

| # | Tool | Purpose |
|---|------|---------|
| 21 | `geox_subsurface_generate_candidates` | Ensemble subsurface outputs (Vsh, φ, Sw, net pay). |
| 22 | `geox_subsurface_verify_integrity` | Physics9 boundary check + structural paradox detection. |
| 23 | `geox_seismic_compute` | Unified seismic physics: synthetic, well tie, AVO/AC. |
| 24 | `geox_seismic_compute_attribute_tool` | Registered seismic attributes. |
| 25 | `geox_sequence_interpret` | Sequence stratigraphy L1-L3 pipeline. |
| 26 | `geox_evidence_reason` | Evidence synthesis + abduction + contradiction. |
| 27 | `geox_prospect_evaluate` | Volumetrics, POS, EVOI. |
| 28 | `geox_map_context_scene` | Spatial bbox context + CRS + scene rendering. |
| 29 | `geox_horizon_contrast_surface` | ToAC-as-Attention horizon pipeline. |
| 30 | `geox_coord_transform_tool` | 3D point transforms. |
| 31 | `geox_blockspace_resolution_tool` | Inline/crossline/vertical resolution. |
| 32 | `geox_blend_volume_tool` | Alpha/RGB seismic volume blend. |
| 33 | `geox_basin_profile` | Basin intelligence: petroleum system, stratigraphy, fairway. |
| 34 | `geox_vision_minimax_inference` | Seismic image interpretation via MiniMax VLM. |
| 35 | `geox_vision_audit` | AC_Risk + VisionVerdict. |
| 36 | `geox_report_to_workflow` | Safe GEOX workflow from report + intent. |
| 37 | `geox_abstraction_guard` | Non-geological question guard. |
| 38 | `geox_prithvi_eo_inference` | **[W5-W8]** Prithvi-EO-2.0 (NASA/IBM) foundation model. |
| 39 | `geox_gravity_magnetic_forward` | **[W9-W12]** HarmonIC gravity/mag forward. |
| 40 | `geox_mt_forward` | **[W13+]** 1D CSEM/MT Wait's recursion. |
| 41 | `geox_biostrat_constraint` | **[W13+]** Biostrat time-facies admissibility. |
| 42 | `geox_seismic_inversion` | **[W13+]** 1D post-stack PINN-style inversion. |
| 43 | `geox_geomechanics` | **[W13+]** K, G, E, ν from Physics9State. |

### Lane 4 — JUDGMENT (13 tools, GOVERNED, lease + session + arifOS judge)

| # | Tool | Purpose |
|---|------|---------|
| 44 | `geox_claim_create` | Create structured claim with provenance + uncertainty bands. |
| 45 | `geox_claim_validate` | Schema validation (DRAFT → VALIDATED). |
| 46 | `geox_claim_challenge` | Alternative interpretation (multi-discipline argument). |
| 47 | `geox_claim_seal` | Submit to arifOS for Vault999 sealing. |
| 48 | `geox_segy_export_tool` | **[888_HOLD]** SEG-Y export (irreversible). |
| 49 | `geox_doctrine_assumption_register` | **[W2-W4 Gap X]** Assumption lineage + falsification cascade. |
| 50 | `geox_doctrine_anti_beautiful_one` | **[W2-W4 Gap 3]** Beauty-vs-grounding audit. |
| 51 | `geox_doctrine_godel_review` | **[W2-W4 Gap 5]** Runtime hard-stop (Iron Law). |
| 52 | `geox_joint_inversion` | **[W13+]** Multi-physics fusion → Physics9State. |
| 53 | `geox_well_decision_class` | **[W13+]** WELL → GEOX operator readiness gate. |
| 54 | `geox_wealth_feed` | **[W13+]** GEOX → WEALTH STOIIP + verdict. |

---

## 2. RESOURCES — 17+ Templates (URI scheme: `geox://...` and `tree777://...`)

### 2.1 Identity + Reality Context (5)

| URI | Purpose |
|-----|---------|
| `geox://reality/context` | Reality context for grounding agent reasoning. |
| `geox://identity` | GEOX organ identity (constitution, contract, git version). |
| `geox://registry/apps` | List registered GEOX apps/applets. |
| `geox://profile/status` | Profile status (operator profile readiness). |
| `geox://surface/truth` | Surface Truth Lock — current surface-truth status. |

### 2.2 Capabilities + Knowledge Pack (4)

| URI | Purpose |
|-----|---------|
| `geox://capabilities` | Full capability map (tools + domains + claim limits + next actions). |
| `geox://resources/{category}/{name}` | Knowledge pack (ontology, playbooks, schemas, examples). |
| `geox://resources/index` | Index of all knowledge pack resources. |
| `geox://surface/truth` | (also under identity) |

### 2.3 TREE777 Wiki (4) — federation skills/concepts/scars

| URI | Purpose |
|-----|---------|
| `tree777://index` | TREE777 wiki index (skills, concepts, scars). |
| `tree777://skills/geox/{name}` | Individual GEOX skill page. |
| `tree777://geo/concepts/{name}` | Geoscience concept page. |
| `tree777://geo/scars/{name}` | GEOX scar/incident record (failure lessons). |

### 2.4 Literature + Basins (3)

| URI | Purpose |
|-----|---------|
| `geox://literature/GSM-MADON-2021-MALAY-BASIN` | Mazlan Madon's 2021 GSM Malay Basin paper. |
| `geox://literature/index` | Index of all literature resources. |
| `geox://basins/malay-basin/profile` | Malay Basin geological profile. |
| `geox://basins/index` | Index of all basins. |

### 2.5 Claims + Artifacts (4)

| URI | Purpose |
|-----|---------|
| `geox://claims/index` | Index of claims (draft/validated/sealed). |
| `geox://claims/graph` | Visual claim graph (nodes + edges). |
| `geox://artifacts/index` | Index of visualizable artifacts. |
| `geox://resources/prompts/index` | Index of prompt templates. |
| `geox://resources/playbooks/index` | Index of playbook files. |
| `geox://resources/ontology/index` | Index of ontology files. |
| `geox://resources/schemas/index` | Index of schema files. |

### 2.6 Binary Render Transport (Module J, 5)

| URI | Purpose |
|-----|---------|
| `geox://render/surfaces/{surface_id}` | Binary surface (horizon mesh, fault plane) — base64. |
| `geox://render/cubes/{volume_id}/{orientation}/{slice_index}` | Binary cube slice — base64 Float32. |
| `geox://render/payload-schema/{version}` | Canonical RenderPayload JSON Schema. |
| `geox://render/cubes/{cube_id}/manifest` | CubeManifest (brick grid + LOD pyramid + URI template). |
| `geox://render/cubes/{cube_id}/lod/{lod}/brick/{ix}/{iy}/{iz}` | Single brick (binary, progressive LOD). |

---

## 3. PROMPTS — 11 Templates

### 3.1 Earth Intelligence (3 — the core trio)

| Name | Purpose |
|------|---------|
| `geox_sense` | **Earth observation**: ingest, inspect, handle raw data. |
| `geox_qc` | **Earth verification**: physics bounds, QC pipeline, uncertainty bands. |
| `geox_interpret` | **Earth synthesis**: claims, cross-discipline argument, prospect evaluation. |

> Assessment language: `CONSISTENT | NEEDS_CORRECTION | INSUFFICIENT_DATA`
> (NEVER use `SEAL/SABAR/HOLD` — those are arifOS 888_JUDGE verdicts)

### 3.2 Discipline (3)

| Name | Purpose |
|------|---------|
| `geox.ui_explain_panel` | Explain data or metadata shown on a UI panel. |
| `geox.claim_discipline` | Formulate claim-disciplined observations/derived inputs. |
| `geox.abstraction_guard` | Enforce category boundaries for non-geological concepts. |

### 3.3 Red Team (1)

| Name | Purpose |
|------|---------|
| `geox.red_team_reviewer` | Red-team review claims; search for contradictions. |

### 3.4 Reports (3)

| Name | Purpose |
|------|---------|
| `geox.report_writer` | Draft structured geological reports referencing claims. |
| `geox.literature_to_claims` | Extract claims from a literature text block. |
| `geox.basin_screen` | Assist in screening a basin profile for play fairways. |

### 3.5 Plus discovery-query and intake (in server.py decorator; see `geox_query_intake` tool lane 1)

---

## 4. SUB-SERVERS (mounted via `mcp.mount()`)

| Sub-server | Path | Role |
|------------|------|------|
| witness | `src/geox_mcp/servers/witness.py` | Witness packet emission (claim attestation). |
| paleoscan | `src/geox_mcp/servers/paleoscan.py` | paleoscan_python v2.0.0 coordinate/image substrate. |
| claims | `src/geox_mcp/servers/claims.py` | H5 Claim Engine (claim_seal/etc.). |
| vision | `src/geox_mcp/servers/vision.py` | Vision V1 layer (perceptual_inventory, audit). |

Composition happens in `src/geox_mcp/server.py:compose_geox_servers()`.

---

## 5. UI APPS (Prefabs)

| Applet | Path | Purpose |
|--------|------|---------|
| `geox_mission_board` | `src/geox_mcp/tools/ui_applets.py` | Mission control board (operator dashboard). |
| `geox_health_dashboard` | same | Service health monitoring. |
| `well_desk_dashboard` | same | Well desk UI for human operator. |

Conditional registration — only when `HAS_FASTMCP_APPS = True` (Prefabs feature flag).

---

## 6. WebMCP (HTTP Endpoints for Browser-Based MCP Hosts)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/webmcp` | GET | Manifest (capability advertisement). |
| `/webmcp` | GET | Browser entry page. |
| `/webmcp/tools` | GET | Tool list for browser clients. |
| `/webmcp/status` | GET | Server status (health + version). |
| `/webmcp/call/{tool_name}` | POST | Browser-side tool invocation. |

Mounted in `src/geox_mcp/server.py` Starlette app.

---

## 7. Transport Layer Details

### 7.1 FastMCP Transport Options

| Transport | Use Case | Status |
|-----------|----------|--------|
| `stdio` | Local agents (Claude Code, OpenCode, Continue CLI) | ✅ Supported (default for `python3 -m geox_mcp.server --transport stdio`) |
| HTTP/SSE (Streamable HTTP) | Remote agents (Cloudflare Tunnel → `https://geox.arif-fazil.com/mcp`) | ✅ Supported (default for systemd `geox-mcp.service`) |

### 7.2 FastMCP Extensions Wired

| Extension | Status | Notes |
|-----------|--------|-------|
| Resources (URI templates) | ✅ | `geox://...`, `tree777://...` schemes |
| Prompts (parameterized templates) | ✅ | 11 templates |
| UI Apps (Prefabs) | ✅ | 3 applets conditional on `HAS_FASTMCP_APPS` |
| WebMCP HTTP | ✅ | Browser-based MCP hosts |
| OAuth 2.1 / CIMD auth | ⏸ Not wired | FastMCP supports; GEOX currently localhost-bridged via Cloudflare |
| OpenTelemetry | ⏸ Not wired | FastMCP supports; deferred (see W14+ backlog) |
| Background Tasks (long-running ops) | ⏸ Not wired | `joint_inversion` is a candidate for async tasks |
| Tools/Resources/Prompts Search transform | ⏸ Not wired | Would help large tool catalogs |
| Skill Provider | ⏸ Not wired | FastMCP has skill-style provider |

### 7.3 Authority Lane Mapping (Server-side Enforcement)

```
Discovery  → OBSERVE      → No lease, no session required
Evidence   → ANALYZE      → No lease, no session required
Reasoning  → ANALYZE      → Lease + session required (via arifOS kernel)
Judgment   → GOVERNED     → Lease + session + arifOS 888_JUDGE required
```

Enforced in `src/geox_mcp/registry.py` per-tool lane assignment and in the `is_geox_func` / `enforce_geox_func` guards in `src/geox_mcp/resources/__init__.py:register_resources()`.

---

## 8. MCP Spec Alignment (per `modelcontextprotocol.io/specification/2025-11-25`)

| Spec Section | GEOX Coverage |
|--------------|---------------|
| **Tools** (`server/tools.md`) | ✅ 54 tools with `inputSchema`/`outputSchema` (Pydantic v2 → JSON Schema 2020-12) |
| **Resources** (`server/resources.md`) | ✅ 17+ templates with URIs, MIME types, descriptions |
| **Prompts** (`server/prompts.md`) | ✅ 11 parameterized templates |
| **Logging** (`server/utilities/logging.md`) | ✅ Server-sent logging via Python `logging` |
| **Progress** (`basic/utilities/progress.md`) | ✅ Supported via `ctx.report_progress` (where used) |
| **Cancellation** (`basic/utilities/cancellation.md`) | ✅ Inherited from FastMCP |
| **Tasks** (`extensions/tasks/overview.md`) | ⏸ Not wired (deferred) |
| **Elicitation** (`client/elicitation.md`) | ⏸ Not wired (deferred) |
| **Sampling** (`client/sampling.md`) | ⏸ Not wired (deferred — server can request LLM completion from client) |
| **Roots** (`client/roots.md`) | ⏸ Not wired (deferred — client provides file system boundaries) |
| **Authorization** (`basic/authorization.md`) | ⏸ Localhost-bridged; OAuth 2.1 deferred |

---

## 9. Language Support

**FastMCP itself: Python-only** (`gofastmcp.com` tagline: *"The fast, Pythonic way to build MCP servers"*).

**MCP spec: language-agnostic** (JSON-RPC based). Official SDKs exist for:

| Language | SDK | Tier |
|----------|-----|------|
| **Python** | `mcp` (official), `fastmcp` (Prefect Horizon) | Tier 1 |
| **TypeScript** | `@modelcontextprotocol/sdk` | Tier 1 |
| **Go** | `github.com/modelcontextprotocol/go-sdk` | Tier 1 |
| **Java** | `io.modelcontextprotocol:java-sdk` | Tier 1 |
| **Kotlin** | `io.modelcontextprotocol:kotlin-sdk` | Tier 1 |
| **C#** | `com.modelcontextprotocol:csharp-sdk` | Tier 2 |
| **Rust** | `rmcp` (community) | Tier 2 |
| **Ruby** | `model_context_protocol` (community) | Tier 2 |
| **Swift** | (in development) | Tier 3 |

**GEOX uses Python/FastMCP.** Other arifOS organs:
- **A-FORGE**: TypeScript (Express + Zod)
- **arifOS kernel**: TypeScript
- **AAA cockpit**: TypeScript + React

If you need a TS or Go client to consume GEOX: use the official MCP SDK in that language to connect to `https://geox.arif-fazil.com/mcp` (HTTP/SSE) or run GEOX via stdio (Python) from your TS/Go host. The MCP protocol is identical across languages.

---

## 10. Verification (live)

```bash
# Tools count
curl -s http://127.0.0.1:8081/health | jq '.owner_summary.reasons'
# → ["identity_unverified", "canonical_tools=54", "service_healthy"]

# Tools list
curl -s -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | jq '.result.tools | length'
# → 54

# Resources list
curl -s -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}' \
  | jq '.result.resources | length'
# → 17+

# Prompts list
curl -s -X POST http://127.0.0.1:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"prompts/list","params":{}}' \
  | jq '.result.prompts | length'
# → 11
```

---

## 11. File Organization

```
src/geox_mcp/
├── server.py                      ← FastMCP server (canonical, ~1,200 lines)
├── registry.py                    ← CANONICAL_PUBLIC_TOOLS, GEOX_TOOL_MANIFEST
├── webmcp.py                      ← WebMCP HTTP endpoints (5 routes)
├── pai_receipt.py                 ← PAI receipt format
├── organ_governance.py            ← Organ governance rules
├── federation_memory.py           ← Federation memory helper
├── routing/                       ← Tool routing, policy, audit, guard, models
├── resources/                     ← MCP resources
│   ├── __init__.py               ← register_resources() orchestrator (824 lines, refactoring target)
│   ├── identity.py               ← [planned] geox://identity, geox://reality/context, profile
│   ├── registry.py               ← [planned] geox://registry/apps, capabilities, surface-truth
│   ├── tree777.py                ← [planned] tree777://... TREE777 wiki integration
│   ├── basins.py                 ← [planned] geox://basins/...
│   ├── literature.py             ← [planned] geox://literature/...
│   ├── claims.py                 ← [planned] geox://claims/...
│   ├── artifacts.py              ← [planned] geox://artifacts/...
│   ├── knowledge_pack.py         ← [planned] geox://resources/{category}/{name}
│   └── render.py                 ← [planned] geox://render/... (binary transport)
├── prompts/                       ← MCP prompts
│   ├── __init__.py               ← register_prompts() orchestrator (361 lines, refactoring target)
│   ├── earth_intelligence.py     ← [planned] geox_sense, geox_qc, geox_interpret
│   ├── discipline.py             ← [planned] geox.ui_explain_panel, claim_discipline, abstraction_guard
│   ├── red_team.py               ← [planned] geox.red_team_reviewer
│   └── reports.py                ← [planned] geox.report_writer, literature_to_claims, basin_screen
├── tools/                         ← MCP tools (45+ files, subpackages, decorators in server.py)
│   ├── doctrine.py, earth_obs.py, geomechanics.py, multi_physics.py, ... ← W13+ forge
│   ├── biostrat/, discovery/, kernel/ ← subpackages
│   └── ui_applets.py              ← Prefab UI applets
├── servers/                       ← Mounted sub-servers (witness, paleoscan, claims, vision)
└── tests/                         ← Regression suite (89+ tests passing)
```

---

## 12. Migration Path (Future)

| Action | When | Authority | Notes |
|--------|------|-----------|-------|
| **Resources split** into per-template modules | W14+ | Autonomous | Code organization; zero behavior change |
| **Prompts split** into per-template modules | W14+ | Autonomous | Code organization; zero behavior change |
| **OAuth 2.1 auth** | W14+ (post-F13 deploy gate) | 888_HOLD | Federate auth via arifOS kernel |
| **OpenTelemetry** | W15+ | Autonomous | Distributed tracing |
| **Background Tasks** for joint_inversion | W15+ | 888_HOLD | Long-running multi-physics inversion |
| **Tools/Resources/Prompts Search transform** | W15+ | Autonomous | Reduce tool catalog noise |
| **Skills Provider** | W16+ | Autonomous | FastMCP skill-style provider for GEOX knowledge pack |
| **MCP Registry publication** | W16+ | 888_HOLD | Publish to `https://registry.modelcontextprotocol.io` |

---

## References

- **MCP spec:** https://modelcontextprotocol.io
- **FastMCP docs:** https://gofastmcp.com
- **GEOX server source:** `src/geox_mcp/server.py`
- **GEOX registry:** `src/geox_mcp/registry.py` (CANONICAL_PUBLIC_TOOLS)
- **GEOX contracts mirror:** `contracts/canonical_registry.py`
- **Forge receipt:** `/root/forge_work/2026-06-21_geox-w2-w13-multiphysics-earth-witness.md`
- **AGENTS.md:** `/root/geox/AGENTS.md`
- **RUNBOOK.md:** `/root/geox/RUNBOOK.md`
- **Steel Security Layer:** non-blocking, no pre-commit hooks, no pnpm migration

---

**DITEMPA BUKAN DIBEI — 86+ MCP primitives, constitutionally wrapped, ready for the federation.**