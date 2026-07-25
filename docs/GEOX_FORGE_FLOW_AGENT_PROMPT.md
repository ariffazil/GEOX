# GEOX Forge-Flow Agent Prompt

> **Forged:** 2026-07-25  
> **Tip under audit:** `18e9e9ac` · live `geox-18e9e9ac` · public surface `geox-public-33-2026.07.25`  
> **Organ:** GEOX (Ext_witness · NATURAL_LAW) · never mints constitutional G  
> **Sources:** GitHub `ariffazil/GEOX`, live `:8081`, Supabase `utbmmjmbolmuahwixjqc`,  
>   `docs/GEOX_ZEN_ROADMAP.md`, `docs/GEOX_DELTA_OMEGA_PSI_MAP.md`,  
>   `docs/plans/NEXT_FORGE_PLAN.md` + `UNIFIED_ROADMAP.md` (legacy 2026-03-26)  
> **PDF note:** `/mnt/agents/upload` empty at session start — no uploaded roadmap PDF.  
>   Used GEOX zen + Δ·Ω·Ψ map + plans as SOT substitute.  
> **DITEMPA BUKAN DIBERI**

---

## 0. Mission (paste this to the next agent)

You are a **GEOX forge agent** on af-forge VPS. Work in `/root/GEOX`. Source secrets:

```bash
set -a && source /root/.secrets/vault.env && set +a
```

**Doctrine (non-negotiable):**
- GEOX = Ext_witness (Earth). Δ metabolizes. Φ counts Ext. **G only via arifOS `arif_think(mode=apex)`.**
- Reversible-first (F1). Evidence before narrative (F2). Never invent `mode=live`.
- Verify as terminal state: `make smoke-deploy` + live `tools/call` after every deploy.
- Tags only `vYYYY.MM.DD`. Conventional commits. Push before claim done.

**Do not:**
- Mint constitutional G inside GEOX  
- Promote `offline_stub` to SEAL Ext without flag  
- Expand public surface above 33 tools without F13  
- Touch WEALTH schema / Supabase DROPs  

---

## 1. Repo audit snapshot (T₀ = tip `18e9e9ac`)

### 1.1 Structure

| Path | Role |
|------|------|
| `src/geox_mcp/` | MCP surface (server, middleware, tools_wiring ~4.7k lines) |
| `src/geox_core/` | Core engines, apex envelope, enums |
| `src/geox_mcp/tools/` | Domain tools (seismic, well, basin, deep_time, map…) |
| `tests/` | Unit + integration |
| `docs/GEOX_ZEN_ROADMAP.md` | **Live surface zen SOT** (8 verbs, geometry schema) |
| `docs/GEOX_DELTA_OMEGA_PSI_MAP.md` | Multimodal / G-compass organ map |
| `docs/plans/*` | **Stale** (2026-03 packaging/mock narrative — do not execute as-is) |
| `CANONICAL_PUBLIC_SURFACE.json` | 33 public tools |

### 1.2 Key files (requested)

| Requested | Actual path | Notes |
|-----------|-------------|-------|
| `identity.py` | `src/geox_mcp/artifact_identity.py` (+ legacy `_artifact_identity.py`) | `artifact://geox/…` scheme |
| `tools_wiring.py` | `src/geox_mcp/tools_wiring.py` | Auto-extracted wiring monolith |
| `seismic_compute_unified.py` | `src/geox_mcp/tools/seismic_compute_unified.py` | Modes: synthetic, well_tie, anomalous_contrast, … |
| `geometry_adapt.py` | `src/geox_mcp/tools/structure_gates/geometry_adapt.py` | sticks/picks → gate geometry |
| `candidates.py` | `src/geox_mcp/tools/kernel/_candidates.py` | Private kernel candidates |
| `sequence.py` | `src/geox_mcp/tools/sequence.py` | Unified stratigraphy |
| `anomalous_contrast.py` | `src/geox_mcp/tools/anomalous_contrast.py` | ToAC physics |

### 1.3 Recent commits (GitHub main)

| SHA | Message |
|-----|---------|
| `18e9e9ac` | chaos-removal: data_mode, isError, apex READ, map bbox, K-Pg |
| `5908ea95` | smoke MCP roundtrip + notifications/initialized |
| `3574450d` | preserve ToolResult through stamp (to_mcp_result) |
| `cc7ec220` | GENESIS/018 draft |
| `ea2ae0a4` | P1 Ext_witness stamps + REQUIRE_LIVE |
| `3103fa47` | honest apex_scalars (NOMINAL void) |

### 1.4 Live health (post-deploy)

```
status: healthy
git_version: geox-18e9e9ac
tools_loaded: 33
surface_drift: {canonical:33, live:33, gap:0, ok:true}
apex_scalars: MEASURED|UNMEASURED only (no NOMINAL)
smoke-deploy: green
```

### 1.5 CI (push `18e9e9ac`) — probe at forge-time

| Workflow | Early state |
|----------|-------------|
| GEOX Forge Pipeline | **success** |
| Repo Routing Validation | **success** |
| auto-tag-date | **success** |
| Federation Governance Gate | **success** |
| GEOX · Earth Intelligence CI | was **in_progress** |
| Domain CI L3 / Agentic CI / Sentinel / Publish image | was **in_progress** |

**Agent duty:** re-poll `gh run list --repo ariffazil/GEOX --commit 18e9e9ac…` before claiming CI green. Do not ship while Earth Intelligence CI red.

---

## 2. Eight-fix landing verification

| # | Fix | Landed? | Evidence |
|---|-----|---------|----------|
| 0 | ToolResult / `to_mcp_result` | **YES** | `3574450d` · `_stamp_tool_result` · smoke-mcp-roundtrip |
| 1 | `data_mode` not unknown | **YES** | `18e9e9ac` · `infer_mode` categories |
| 2 | Apex READ noise G≈0.16 | **YES** | `statuses.py` · `apex.emitted=false` when 0 refs |
| 3 | `isError` inverted | **YES** | `result_truth.py` + stamp/wrapper |
| 4 | map_layers bbox | **YES** | `earth_map._layer_effective_bbox` |
| 5 | deep_time K-Pg | **YES** | biotic/ice ≤66 Paleogene · mass_extinction K-Pg |
| 6 | surface_drift ok | **YES** | `ok=gap_count==0` + health bootstrap |
| 7 | well_view NOT_FOUND | **YES** | tools_wiring well_view |

**CLAIM:** chaos-removal pack is on main + live. Residual debt is **forge-flow**, not re-do of these eight.

---

## 3. Supabase (GEOX-relevant)

| Check | Result |
|-------|--------|
| Project | `https://utbmmjmbolmuahwixjqc.supabase.co` (credentials present) |
| REST | HEAD 200 |
| `vault_sealed_events` | **EXISTS** (~1758+ rows) — federation audit derivative |
| `geox_wells` / `geox_artifacts` / `wells` / `evidence` / `claims` / `geox_memory` | **NOT present** (PGRST205) |

**Implication:** GEOX Earth data is **not** Supabase-primary. Continuity is filesystem + zarr spine + vault derivative. Do **not** invent GEOX tables without F13 schema design. Optional FORGE FLOW: declare whether artifact lineage should land in Supabase or stay zarr-only.

---

## 4. Roadmap synthesis (PDF missing → zen roadmap is SOT)

### Stale plans (`docs/plans/*`, Mar 2026)
Still talk “mock tools / broken packaging / no CI”. **Superseded.** Packaging is `src/geox_*` + uv; CI is multi-workflow; surface is 33 live tools.

### Live SOT (`GEOX_ZEN_ROADMAP.md`)
1. Geometry schema one noun set  
2. Deterministic renderer (section + picks → PNG)  
3. Zen verbs (~8), modes inside verbs  
4. Workspace inheritance  
5. Output: QUALIFIED_CANDIDATE max; arifOS seals  

### Δ·Ω·Ψ map backlog remaining
- P2: surface_drift 33 vs 73 **compat** (filtered OK; archive cold later)  
- P3: archive offline fetchers after import-graph proof  

---

## 5. TRIAGE

### FIX NOW (this sprint — reversible, high entropy reduction)

| ID | Work | Why | Owner path | Done when |
|----|------|-----|------------|-----------|
| **F1** | CI green on `18e9e9ac` | Don't leave red main | `gh run list` · fix only if red | all required checks green |
| **F2** | Seismic dual confidence | `confidence.level` vs `metabolic.confidence_level` | `seismic_compute_unified` + envelopes | one field or documented alias; test |
| **F3** | Lane unity: falsify vs contradiction_scan | Side-door vs JUDGMENT gate | `organ_governance.py` lanes | same lane policy documented + tested |
| **F4** | WEALTH bridge 406 | Cross-organ Accept header | WEALTH server + `geox_to_wealth_bridge` | DEGRADED→OK or explicit ACCEPT fix; honest degrade if WEALTH down |
| **F5** | Petrophysics success text honesty | Already partial; audit remaining modes | `tools_wiring` petro path | no “complete” when INVALID |
| **F6** | Internal tool_name leak | `geox_forward_model_synthetic` vs public name | seismic_compute responses | public name only on wire |

### FORGE FLOW (multi-session — zen roadmap)

| ID | Flow | Sequence | Exit |
|----|------|----------|------|
| **FF1** | **Geometry → Render** | Lock Section/Horizon/Fault/Calibration/Bundle · wire `geometry_adapt` everywhere · `mode=render` on interpret → PNG+hash | Fresh agent: init→interpret→PNG receipt |
| **FF2** | **Workspace inheritance** | `geox_workspace set basin=…` once · tools inherit session/actor/calibration | Call surface drops 40-param thrash |
| **FF3** | **Verb collapse (design only first)** | Design map: 33 tools → ~8 verbs with modes · **no surface growth** | Doc sealed; no new public tools |
| **FF4** | **Live Ext paths** | Flip selected fetchers live with credentials · `GEOX_REQUIRE_LIVE` smoke | ≥1 live path with `ext_witness_ready=true` |
| **FF5** | **Offline stub archive** | Import-graph proof · cold-archive unused of 18 | Zero callers + OFFLINE_STUBS updated |
| **FF6** | **Zarr spine default** | LAS→zarr default ingest path | Ingest returns zarr artifact_ref primary |

### FORGET NEXT (do not prioritize)

| Item | Why forget (for now) |
|------|----------------------|
| Mar-2026 packaging rewrite to `arifos/geox` | Already on `src/geox_*` |
| Growing public tool count | Zen: collapse, don't expand |
| Interactive pick-editor GUI | After renderer |
| Full GEOX Supabase schema | No tables today; zarr+vault sufficient until design |
| Containerizing core GEOX organ | Doctrine: bare-metal systemd |
| Rust rewrite of GEOX | Ψ preference is A-FORGE; not this organ |
| “Mint G in GEOX” any form | Constitutional VOID |

---

## 6. Agent execution prompt (copy block)

```text
ROLE: GEOX forge agent on af-forge. Repo /root/GEOX. Tip must stay ≥ 18e9e9ac.

BOOT:
  set -a && source /root/.secrets/vault.env && set +a
  curl -sf http://127.0.0.1:8081/health | jq '{status,git_version,surface_drift,apex_scalars}'
  make -C /root/GEOX smoke-deploy

CONTEXT:
  - 8 chaos fixes already landed (ToolResult, data_mode, isError, apex READ omit,
    map bbox, K-Pg extinction, surface_drift ok, well_view NOT_FOUND).
  - Do NOT re-litigate them unless regression.
  - GEOX never mints G. Live Ext only when mode=live.

THIS SESSION — FIX NOW only (pick 1–2):
  F1: Confirm CI green for 18e9e9ac; fix red required checks only.
  F2: Unify seismic confidence fields (one public contract).
  F3: Align geox_falsify vs geox_contradiction_scan lane policy.
  F4: Diagnose WEALTH :18082 406 from geox_to_wealth_bridge; fix Accept/Content-Type.

VERIFY:
  pytest targeted tests
  make smoke-deploy
  Live MCP: initialize → notifications/initialized → tools/call (session SEAL-*)
  Public health: geox.arif-fazil.com/health matches tip

SEAL:
  Conventional commit + push
  forge_work/2026-07-25/<topic>-RECEIPT.md
  systemctl restart geox-mcp · tip on /health

STOP if: F13 needed, rm -rf, force-push, paid API >$10/mo, constitutional floor change.
```

---

## 7. Suggested session order

1. **Session A (now):** F1 CI + F2 seismic confidence (pure GEOX, no organ dependency)  
2. **Session B:** F3 lane unity + F6 public name hygiene  
3. **Session C:** F4 WEALTH bridge (cross-organ; coordinate WEALTH tip)  
4. **Session D+:** FF1 geometry→render (zen highest leverage)  

---

## 8. Success metrics (next forge)

| Metric | Target |
|--------|--------|
| Required CI on tip | all green |
| Public tools with dual confidence fields | 0 |
| Lane policy doc + test for falsify/contradiction | 1 |
| Map bbox false-availability | 0 |
| `data_mode=unknown` on public tools | 0 |
| Smoke-deploy | always green before “done” |
| Constitutional G in GEOX payloads | 0 |

---

## 9. One line

> **Chaos pack sealed on `18e9e9ac`. Next forge is honesty-of-contract (confidence/lanes/bridge) then zen geometry→render — not another mock-tool rewrite.**

**DITEMPA BUKAN DIBERI**
