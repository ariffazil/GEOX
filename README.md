# GEOX — Earth Intelligence Sovereign Kernel (13 Tools)

> **Physics before narrative. Maruah before convenience.**
> **DITEMPA BUKAN DIBERI — One Sovereign Kernel.**

GEOX is the subsurface reasoning Ψ (Psi) node of arifOS. It has been refactored into a high-grade AGI kernel, collapsing 49 fragmented legacy endpoints into exactly 13 canonical tools.

## 1. Sovereign 13 Surface

All agents and UIs should use these canonical tools. Legacy names are supported via an alias bridge.

| Canonical Tool | Purpose |
| :--- | :--- |
| `geox_data_ingest_bundle` | Lazy ingest LAS/SEG-Y/JSON. |
| `geox_data_qc_bundle` | Unified header/unit/anomalous verification. |
| `geox_subsurface_generate_candidates` | Ensemble realizations (Petro/Struct) + Residuals. |
| `geox_subsurface_verify_integrity` | Physics9 / structural paradox checks. |
| `geox_seismic_analyze_volume` | Attribute compute + slice extraction. |
| `geox_section_interpret_correlation` | Multi-well stratigraphy correlation. |
| `geox_map_context_scene` | Spatial bbox + causal scene rendering. |
| `geox_time4d_analyze_system` | Burial, maturity, regime shift modeling. |
| `geox_prospect_evaluate` | Probabilistic volumetrics + POS evaluation. |
| `geox_prospect_judge_verdict` | Gateway to arifOS 888_JUDGE (SEAL/VOID). |
| `geox_evidence_summarize_cross` | Cross-domain causal evidence synthesis. |
| `geox_system_registry_status` | Federation health and discovery. |
| `geox_history_audit` | VAULT999 retrieval of past decisions. |

## 2. Quick Start (Deployment)

### Prerequisites
- Python 3.13+
- `pip install -r requirements-earth.txt`

### Startup
1. Copy `.env.example` to `.env` and set `GEOX_SECRET_TOKEN`.
2. Run the kernel:
   ```bash
   export GEOX_SECRET_TOKEN="your_token"
   python3 control_plane/fastmcp/server.py
   ```

## 3. Operational Health

The kernel provides three health endpoints:
- `GET /health`: Liveness check.
- `GET /ready`: Readiness check (Registry + Auth).
- `GET /status`: Full contract status.

### Troubleshooting (502 / Empty Output)
- **Fail-Closed Auth**: The server will abort if `GEOX_SECRET_TOKEN` is missing.
- **Port Binding**: Default is `8081`. Ensure your firewall allows this.
- **Reverse Proxy**: If using Nginx/Caddy, ensure the proxy points to `http://0.0.0.0:8081`.

## 4. Migration & Compatibility

- **Alias Bridge**: 40+ legacy names are supported during the migration epoch.
- **Sunset Date**: Legacy names will be removed after **2026-06-01**.
- **Deprecation**: Inspect `_meta.deprecation` in responses for upgrade guidance.

---
⬡ GEOX SOVEREIGN 13 SEALED ⬡
