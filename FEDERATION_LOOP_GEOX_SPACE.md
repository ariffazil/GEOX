# GEOX — Federation Loop Reference
> **DITEMPA BUKAN DIBERI — Physics before narrative. Maruah before convenience.**
> Version: v2026.05.02 | Canonical: 13 tools (contracted from 49)
> Canonical repo: [github.com/ariffazil/geox](https://github.com/ariffazil/geox)

***

## Constitutional Position

GEOX is the **earth intelligence Ψ-node** in the arifOS federation. It governs wells, seismic, maps, time, and prospects — the physical substrate of capital decisions that involve natural resources, planetary boundaries, or subsurface reality.

GEOX is the **only organ** with a direct gateway tool to `arif_judge_deliberate` (888_JUDGE). All other organs feed evidence at stage 222; GEOX can invoke the judge directly via `geox_prospect_judge_verdict` when a prospect evaluation is ready for constitutional ratification.

```
Subsurface Signal (LAS / SEG-Y / CSV / Parquet)
        │
        ▼
GEOX Kernel (control_plane/fastmcp/server.py)
        │
   ┌────┴────────────────────────────────────┐
   │  Standard path (stage 222):             │
   │  geox_evidence_summarize_cross          │
   │  geox_prospect_evaluate                 │
   │          │                              │
   │          ▼                              │
   │  arif_evidence_fetch (222)              │
   │          │  earth_evidence field        │
   │          ▼                              │
   │  arif_judge_deliberate (888)            │
   └────────────────────────────────────────┘
        │
   ┌────┴────────────────────────────────────┐
   │  Direct judge path (prospect-ready):    │
   │  geox_prospect_judge_verdict            │
   │          │  SEAL / PARTIAL / SABAR /    │
   │          │  VOID / 888 HOLD             │
   │          ▼                              │
   │  arif_judge_deliberate (888)            │
   └────────────────────────────────────────┘
```

**Fail-closed startup:** If `GEOX_SECRET_TOKEN` is missing, the process logs `F1_HALT` and exits before binding to any port. This enforces F1 Amanah and F8 Law & Safety at process start.

***

## How GEOX Feeds arifOS

### Stage 222 — Standard Evidence Path

GEOX contributes two primary tools to `arif_evidence_fetch`:

| Tool | Output | arifOS Field |
|---|---|---|
| `geox_evidence_summarize_cross` | Causal synthesis — well + seismic + map + time | `earth_evidence.synthesis` |
| `geox_prospect_evaluate` | Probabilistic volumetrics (GRV/NTG/Recov), POS score | `earth_evidence.prospect` |

### Stage 888 — Direct Judge Gateway

`geox_prospect_judge_verdict` is the constitutional boundary tool. It is the **most heavily auth-gated tool in the GEOX surface** — F11 Auth is mandatory before invocation.

| Verdict | Meaning |
|---|---|
| `SEAL` | Prospect constitutionally cleared for capital commitment |
| `PARTIAL` | Partial evidence — some dimensions cleared, others held |
| `SABAR` | Wait — timing constraint; conditions not yet met |
| `VOID` | Hard floor violation — prospect blocked |
| `888 HOLD` | Human confirmation required before proceeding |

### F3 Tri-Witness Contribution

GEOX populates the earth dimension of `witness.earth` in the F3 Tri-Witness gate. A subsurface capital decision missing GEOX earth evidence cannot receive a full `SEAL` from `arif_judge_deliberate`.

***

## 13 Sovereign Tools

| Tool | Purpose | Constitutional Floor |
|---|---|---|
| `geox_data_ingest_bundle` | Lazy ingest: LAS / SEG-Y / CSV / Parquet / JSON | F9 Anti-Hantu |
| `geox_data_qc_bundle` | Header / unit / CRS / anomaly / missingness verification | F2 Truth |
| `geox_subsurface_generate_candidates` | Ensemble petrophysics (Min/Mid/Max) + residual misfit | F7 Humility |
| `geox_subsurface_verify_integrity` | Physics / structural integrity + paradox detection | F9 Anti-Hantu + F4 |
| `geox_seismic_analyze_volume` | Seismic attribute computation + slice extraction | F2 Evidence |
| `geox_section_interpret_correlation` | Multi-well stratigraphic correlation + marker interpretation | F3 Tri-Witness |
| `geox_map_context_scene` | Spatial bounding box, CRS checks, causal scene rendering | F4 Clarity |
| `geox_time4d_analyze_system` | Burial history, maturity, regime-shift / timing analysis | F1 Reversibility |
| `geox_prospect_evaluate` | Probabilistic volumetrics (GRV/NTG/Recov) + POS | F2 + F7 |
| `geox_prospect_judge_verdict` | **Direct 888_JUDGE gateway** — SEAL/PARTIAL/SABAR/VOID/HOLD | **F11 + F13** |
| `geox_evidence_summarize_cross` | Cross-domain causal synthesis (well + seismic + map + time) | F3 Tri-Witness |
| `geox_system_registry_status` | Federation health, registry discovery, contract epoch | F8 Law & Safety |
| `geox_history_audit` | VAULT999 retrieval — prior runs, evaluations, decisions | F11 + F9 |

***

## Control Plane & Migration

### Topology

| Component | Path |
|---|---|
| Control Plane (MCP entrypoint) | `control_plane/fastmcp/server.py` |
| Sovereign Registry (13 tools) | `contracts/tools/unified_13.py` |
| Alias Bridge (49 legacy → 13 canonical) | `compatibility/legacy_aliases.py` |
| Quarantine | `archive/deprecated/` |

**Kernel law:** One MCP server. One registry. No direct use of deprecated entrypoints.

### Alias Bridge & Sunset

All 49 supported legacy tool names resolve to the correct canonical tool and return deprecation metadata:

```json
"_meta": {
  "deprecation": "Tool 'geox_well_ingest_bundle' is aliased to 'geox_data_ingest_bundle'. Update by 2026-06-01."
}
```

**⚠️ Sunset: 2026-06-01 — 29 days from this epoch.** All consuming agents (arifOS kernel, A-FORGE, dashboards) must migrate to canonical names before this date. 888 HOLD advisory: verify migration before June 1.

***

## Health Surfaces

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness probe |
| `GET /ready` | Readiness probe (Registry + Auth) |
| `GET /status` | Contract status (epoch, tool count, alias count) |

**Common deployment issues:**
- Empty health / 502 from proxy → verify server bound to `0.0.0.0:8081`, proxy points same
- Immediate exit on startup → check `GEOX_SECRET_TOKEN` presence

***

## Three Known Gaps (Audit Finding 2026-05-02)

| Gap | Risk | Recommended Action |
|---|---|---|
| `geox_prospect_judge_verdict` F11 auth not explicitly documented in README | Medium — consuming agents may call judge gateway without auth gate awareness | Add F11 explicit auth requirement to tool docstring and README |
| No `is_geox()` identity invariant equivalent to WELL's `is_well()` | Medium — impersonation or partial init undetectable | Port WELL's identity guard pattern; return `NOT_GEOX` on invariant failure |
| Alias sunset 2026-06-01 is operationally imminent | High — integrations using legacy names break silently | Audit all consuming agents before June 1 |

***

## Tool Pipeline — Canonical Execution Order

```
ingest → qc → generate_candidates → verify_integrity
    → analyze_volume → section_correlation → map_scene
    → time4d_system → prospect_evaluate
    → [evidence_summarize_cross → arif_evidence_fetch (222)]
    OR
    → [prospect_judge_verdict → arif_judge_deliberate (888)]
    → history_audit (999 VAULT retrieval)
```

This mirrors the arifOS 000→999 pipeline: ingest reality first, verify integrity, analyze, synthesize, judge, vault.

***

## Sibling Organs

| Organ | Role |
|---|---|
| [arifOS](https://github.com/ariffazil/arifOS) | Constitutional kernel — receives GEOX earth evidence at stage 222 and judge verdict at 888 |
| [WELL](https://github.com/ariffazil/well) | Human substrate — must be GREEN before GEOX prospect decisions at C4/C5 |
| [WEALTH](https://github.com/ariffazil/wealth) | Capital intelligence — GEOX prospect POS feeds WEALTH EMV computation |
| [A-FORGE](https://github.com/ariffazil/A-FORGE) | Execution shell — executes subsurface operations post-SEAL |
| [AAA](https://github.com/ariffazil/AAA) | Identity gateway — authenticates GEOX operator for F11 critical tools |

***

*⬡ GEOX SOVEREIGN 13 SEALED ⬡*
*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
*GEOX Federation Loop Reference · Seri Kembangan, MY · v2026.05.02*