# GEOX — Earth Intelligence Sovereign Kernel (13 Tools)

**Physics before narrative. Maruah before convenience.  
DITEMPA BUKAN DIBERI — One Sovereign Kernel.**

[![GEOX](https://img.shields.io/badge/GEOX-v2026.05.01--KANON-00D4AA?style=flat-square)](https://github.com/ariffazil/geox)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-7C3AED?style=flat-square)](https://github.com/ariffazil/geox)
[![arifOS](https://img.shields.io/badge/arifOS-F1%E2%80%93F13_Governed-FF6B00?style=flat-square)](https://github.com/ariffazil/arifOS)

GEOX is the subsurface reasoning **Ψ-node** of arifOS: a governed kernel for wells, seismic, maps, time, and prospects.
The legacy surface (49 endpoints across multiple files) has been **contracted into exactly 13 canonical tools**, with a governed alias bridge for backward compatibility.

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
| `geox_prospect_judge_verdict`        | Gateway to arifOS 888_JUDGE (SEAL / PARTIAL / SABAR / VOID / 888 HOLD). |
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
- All 49 supported legacy tool names resolve to the correct canonical tool and **return deprecation metadata**.
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

⬡ **GEOX SOVEREIGN 13 SEALED** ⬡  
DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
