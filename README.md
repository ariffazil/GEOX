# GEOX — Earth Intelligence Sovereign Kernel (21 Tools)

**Physics before narrative. Maruah before convenience.  
DITEMPA BUKAN DIBERI — One Sovereign Kernel.**

[![GEOX](https://img.shields.io/badge/GEOX-v2026.05.13-00D4AA?style=flat-square)](https://github.com/ariffazil/geox)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-7C3AED?style=flat-square)](https://github.com/ariffazil/geox)
[![arifOS](https://img.shields.io/badge/arifOS-F1%E2%80%93F13_Governed-FF6B00?style=flat-square)](https://github.com/ariffazil/arifOS)

GEOX is the subsurface reasoning **Ψ-node** of arifOS: a governed kernel for wells, seismic, maps, time, prospects, and sequence stratigraphy. 21 canonical tools + 85 legacy aliases for backward compatibility.

---

## 1. Sovereign 21 Tool Surface

### Data Intake & QC
| Tool | Purpose |
|------|---------|
| `geox_data_ingest_bundle` | Lazy ingest LAS/CSV/SEG-Y/JSON/b64 upload |
| `geox_data_qc_bundle` | Depth monotonicity, null %, physical range validation |
| `geox_dst_ingest_test` | Structured Drill Stem Test ingestion (CGR, WGR, CO2/H2S) |

### Subsurface & Petrophysics
| Tool | Purpose |
|------|---------|
| `geox_subsurface_generate_candidates` | Ensemble petrophysics (Vsh, porosity, Sw, netpay) + structure |
| `geox_subsurface_verify_integrity` | Physics9 boundary enforcement, paradox detection |

### Seismic & Maps
| Tool | Purpose |
|------|---------|
| `geox_seismic_analyze_volume` | Attribute computation, slice rendering, interpretation |
| `geox_map_context_scene` | CRS checks, bbox context, F6 Maruah territorial flags |

### Stratigraphy, Time & Well Logs
| Tool | Purpose |
|------|---------|
| `geox_section_interpret_correlation` | Multi-well stratigraphic correlation, GR motifs, sequence strat |
| `geox_time4d_analyze_system` | Burial history, maturity modeling, regime shift analysis |
| `geox_well_compute_gr_bins` | **L1** — 10 m GR sensing bins (P10/P50/P90) + motif classification |
| `geox_well_build_packages` | **L2** — Geological package builder from 10 m bins |
| `geox_well_infer_seq_strat` | **L3** — Systems tract inference (LST/TST/HST/FSST/CS) |
| `geox_well_analyze_sequence` | Full L1+L2+L3 pipeline for a single well |

### Prospect Evaluation & Governance
| Tool | Purpose |
|------|---------|
| `geox_prospect_evaluate` | Probabilistic volumetrics (GRV/NTG/Recov) + POS + EVOI |
| `geox_prospect_judge_preview` | Reversible advisory verdict (no ack required) |
| `geox_prospect_judge_seal` | **Irreversible** 888_JUDGE gateway. F11 PIN + F13 confirm required |
| `geox_evidence_summarize_cross` | Cross-domain evidence graph synthesis (JSON/CSV export) |

### Pipeline Orchestration
| Tool | Purpose |
|------|---------|
| `geox_stratigraphy_run_pipeline` | Full multi-well L1-L3 stratigraphy. Accepts YAML config. Returns XLSX (5 sheets) + per-well PNG + correlation panel |
| `geox_stratigraphy_preview_config` | Validate YAML project config without running pipeline |

### System & Registry
| Tool | Purpose |
|------|---------|
| `geox_system_registry_status` | Federation health, tool discovery, contract epoch |
| `geox_history_audit` | VAULT999 decision lineage retrieval |

---

## 2. Quick Start (Local stdio — no token required)

```bash
# Install
pip install -r requirements-earth.txt

# Run (stdio — VS Code / Claude Desktop)
python3 server.py

# Or HTTP (requires GEOX_SECRET_TOKEN)
export GEOX_SECRET_TOKEN="your_token"
python3 server.py --host 0.0.0.0 --port 8081
```

**Auth:** Local stdio auto-detects and bypasses token check. Remote HTTP requires `GEOX_SECRET_TOKEN` (fail-closed).

---

## 3. Well Stratigraphy Pipeline

Config-driven sequence stratigraphy for any well set:

```yaml
project: KL2
bin_size_m: 10
wells:
  - name: ROTAN-1
    path: ./data/ROTAN-1.LAS
    format: LAS
intervals:
  ROTAN-1:
    - zone: NN11
      top: 1836
      base: 1994
      depo_env: MBT
```

Outputs: XLSX (01_GEO_PACKAGES, 03_WELL_SUMMARY, 05_COLOR_LEGEND), per-well 6-track PNG, correlation panel PNG.

---

## 4. Architecture

```
server.py (FastMCP + Starlette)
├── contracts/tools/unified_13.py    # 15 original canonical tools
├── geox/well/mcp_tools.py           # 4 well stratigraphy tools (L1-L3)
├── geox/well/mcp_stratigraphy.py    # 2 pipeline orchestration tools
├── geox/well/stratigraphy/          # Generalized L1-L3 pipeline engine
│   ├── config.py                    # ProjectConfig schema
│   ├── loader.py                    # LAS/CSV loader with GR detection
│   ├── sensing.py                   # L1: configurable GR binning
│   ├── packages.py                  # L2: geological package builder
│   ├── seqstrat.py                  # L3: systems tract inference
│   ├── pipeline.py                  # Pipeline orchestrator
│   ├── plot.py                      # 6-track well panel + correlation panel
│   ├── excel.py                     # 5-sheet XLSX exporter
│   └── codec.py                     # PNG ⇄ XLSX round-trip codec
└── compatibility/legacy_aliases.py  # 85 legacy aliases → canonical bridge
```

---

## 5. Federation Integration

GEOX participates in the arifOS constitutional loop as an **evidence supplier** (stage 222) and as a **judge gateway** (stage 888):

```
Arif (F13) → arif_session_init → arif_sense_observe → arif_evidence_fetch
                                                       ↓
              GEOX → geox_evidence_summarize_cross  (earth evidence)
              GEOX → geox_stratigraphy_run_pipeline  (well stratigraphy)
                                                       ↓
                           arif_judge_deliberate
                                ↓
           geox_prospect_judge_seal ← irreversible gateway
```

---

⬡ **GEOX SOVEREIGN 21 — SEALED** ⬡
DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
