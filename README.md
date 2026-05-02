# GEOX — Earth Intelligence Sovereign Kernel (13 Tools)

**Physics before narrative. Maruah before convenience.  
DITEMPA BUKAN DIBERI — One Sovereign Kernel.**

[![GEOX](https://img.shields.io/badge/GEOX-v2026.05.01--KANON-00D4AA?style=flat-square)](https://github.com/ariffazil/geox)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-7C3AED?style=flat-square)](https://github.com/ariffazil/geox)
[![arifOS](https://img.shields.io/badge/arifOS-F1%E2%80%93F13_Governed-FF6B00?style=flat-square)](https://github.com/ariffazil/arifOS)

GEOX is the subsurface reasoning **Ψ-node** of arifOS: a governed kernel for wells, seismic, maps, time, and prospects.
The legacy surface (37 legacy aliases across multiple files) has been **contracted into 13 canonical tools + 1 file ingress tool**, with a governed alias bridge for backward compatibility.

***

## 1. Sovereign 13 Tool Surface

**All agents and UIs must target these canonical tools.**  
Legacy names remain available via an alias bridge for a limited migration window.

| Canonical Tool                       | Purpose                                                                 |
|--------------------------------------|-------------------------------------------------------------------------|
| `geox_data_ingest_bundle`            | Lazy ingest for LAS / SEG-Y / CSV / Parquet / JSON subsurface payloads. |
| `geox_data_qc_bundle`                | Unified header / unit / CRS / anomaly and missingness verification.     |
| `geox_subsurface_generate_candidates`| Ensemble petrophysics & structures (Min/Mid/Max) + residual misfit maps.|
| `geox_subsurface_verify_integrity`   | Physics / structural integrity checks and paradox detection.            |
| `geox_seismic_analyze_volume`        | Seismic attribute computation (e.g. Bruges) and slice extraction.       |
| `geox_section_interpret_correlation` | Multi-well stratigraphic correlation and marker interpretation.         |
| `geox_map_context_scene`             | Spatial bounding box, CRS checks, and causal scene rendering.           |
| `geox_time4d_analyze_system`         | Burial history, maturity, and regime-shift / timing analysis.           |
| `geox_prospect_evaluate`             | Probabilistic volumetrics (GRV/NTG/Recov) and POS evaluation.           |
| `geox_prospect_judge_verdict`        | Gateway to arifOS 888_JUDGE (SEAL / HOLD / VOID). ⚠️ F11 AUTH required — requires proven identity and PIN before invocation. |
| `geox_evidence_summarize_cross`      | Cross-domain causal evidence synthesis (well + seismic + map + time).   |
| `geox_system_registry_status`        | Federation health, registry discovery, and contract epoch reporting.    |
| `geox_history_audit`                 | VAULT999 retrieval of prior runs, evaluations, and decisions.           |

***

## 2. Topology & Control Plane

- **Control Plane (MCP entrypoint)**  
  `control_plane/fastmcp/server.py`

- **Sovereign Registry (13 tools)**  
  `contracts/tools/unified_13.py`

- **Alias Bridge (legacy names → 13 tools)**  
  `compatibility/legacy_aliases.py`

- **Quarantine (ghost servers / deprecated files)**  
  `archive/deprecated/`

Kernel law:
- One MCP server.
- One registry.
- No direct use of deprecated entrypoints.

***

## 3. Quick Start (Local / VPS)

### Prerequisites
- Python **3.13+**
- GEOX dependencies: `pip install -r requirements-earth.txt`

### Configuration
1. Copy `.env.example` → `.env`.
2. Set required environment variables (minimum):
```bash
export GEOX_SECRET_TOKEN="your_strong_token"
export GEOX_HOST="0.0.0.0"     # optional, default: 0.0.0.0
export GEOX_PORT="8081"        # optional, default: 8081
```

### Start the kernel
```bash
python3 control_plane/fastmcp/server.py
```
Fail-closed behavior: If `GEOX_SECRET_TOKEN` is **missing**, the process logs an F1_HALT error and **exits before binding** to any port.

***

## 4. Health & Status

The kernel exposes three health surfaces:
- `GET /health`: Liveness probe.
- `GET /ready`: Readiness probe (Registry + Auth).
- `GET /status`: Contract status (epoch, tool count, alias count).

### Common deployment issues
- **Empty health / 502 from proxy**: Verify server is bound to `0.0.0.0:8081` and proxy points to the same.
- **Immediate exit on startup**: Check `GEOX_SECRET_TOKEN` presence.

***

## 5. Migration & Compatibility

### Alias bridge
- All 37 supported legacy tool names resolve to the correct canonical tool and **return deprecation metadata**.
- Example `_meta` payload:
```json
"_meta": {
  "deprecation": "Tool 'geox_well_ingest_bundle' is aliased to 'geox_data_ingest_bundle'. Update by 2026-06-01."
}
```

### Sunset policy
- Planned removal window: **after 2026-06-01**.
- New agents and UIs **must** call the 13 canonical tools directly.

***

## 6. Federation Integration

GEOX participates in the arifOS constitutional loop as an **evidence supplier** (stage 222) and as a **judge gateway**:

```
Arif (F13) → arif_session_init → arif_sense_observe → arif_evidence_fetch
                                                       ↓
              WELL → well_reflect_readiness  (human substrate readiness)
              WEALTH → wealth_reason_npv/irr/emv  (capital intelligence)
              GEOX → geox_evidence_summarize_cross  (earth evidence)
                                                       ↓
                           arif_evidence_fetch → arif_mind_reason → arif_heart_critique → arif_judge_deliberate
                                                                                              ↓
                                          geox_prospect_judge_verdict ← gateway to 888_JUDGE
```

**Two entry points:**
- **222 EVIDENCE** — `geox_evidence_summarize_cross` + `geox_prospect_evaluate` feed `earth_evidence` into `arif_evidence_fetch`
- **888 JUDGE** — `geox_prospect_judge_verdict` is the direct gateway to `arif_judge_deliberate` (F11 AUTH required)

**F3 Tri-Witness:** GEOX's earth evidence (seismic + well + map + time) constitutes the `earth` witness leg of the constitutional Tri-Witness check at 888_JUDGE.

## 7. Constitutional Notes

- **`geox_prospect_judge_verdict`**: Direct gateway to arifOS 888_JUDGE. Requires F11 AUTH (PIN/identity verification) before invocation. This is the only organ with a direct judge-bypass path.
- **Identity guard**: Unlike WELL's `is_well()` invariant, GEOX relies on the `GEOX_SECRET_TOKEN` fail-closed startup and `/ready` endpoint for identity verification. A formal `is_geox()` identity function is a planned hardening item.
- **Epistemic tags**: Numeric outputs from GEOX tools carry CLAIM/PLAUSIBLE/HYPOTHESIS/ESTIMATE epistemic tags per F02. Min/Mid/Max ensemble outputs satisfy F07 Humility requirements natively.

***

## arifOS Federation

arifOS is part of a federated AI governance system. Each organ has a narrow responsibility so no single agent becomes uncontrolled, unaccountable, or self-authorizing.

| Organ | Human Meaning | System Role | Docs |
|---|---|---|---|
| **ARIF / APEX** | Final human authority | F13 sovereign veto, approval, override, terminal judgment | [arif-fazil.com](https://arif-fazil.com) |
| **AAA** | Operator cockpit | Identity, A2A federation gateway, session control, agent supervision | [README](https://github.com/ariffazil/AAA) |
| **A-FORGE** | Execution shell | Runs tools, performs dry-runs, executes approved actions, reports outcomes | [README](https://github.com/ariffazil/A-FORGE) |
| **arifOS** | Governance kernel | Checks evidence, risk, authority, verdicts, and auditability before action | [README](https://github.com/ariffazil/arifOS) |
| **GEOX** | Earth intelligence | Seismic, petrophysics, basin, subsurface, and physics-grounded evidence | [README](https://github.com/ariffazil/geox) |
| **WEALTH** | Capital intelligence | NPV, IRR, EMV, risk scoring, crisis triage, economic judgment | [README](https://github.com/ariffazil/wealth) |
| **WELL** | Human readiness mirror | Operator pressure, biological state, cognitive load, human-system safety | [README](https://github.com/ariffazil/well) |
| **Ω-Wiki** | Knowledge base | Persistent compiled knowledge, doctrine, references, and memory surfaces | [wiki.arif-fazil.com](https://wiki.arif-fazil.com) |

### How the organs work together

A governed action should not move directly from prompt to execution.

```
Human / Agent request
→ AAA identifies the session
→ arifOS judges the request
→ GEOX / WEALTH / WELL provide domain evidence when needed
→ A-FORGE executes only approved actions
→ VAULT999 records the receipt
→ APEX / Human can veto at any time
```

> **AAA controls the session. arifOS judges. Domain organs provide evidence. A-FORGE executes. VAULT999 records. The human remains sovereign.**

⬡ **GEOX SOVEREIGN 13 SEALED** ⬡
DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
