<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-07-20T16:25Z
valid_until: 2026-08-20
federation_release: v2026.07.20-ZEN-CONVERGENCE
live_commit: c2397743
truth_rule: live :8081/health + tools/list beat any static count in prose
mcp_tools_live: dynamic_from_tools_list
-->

# 🌊 GEOX — Subsurface Intelligence Workbench

> **DITEMPA BUKAN DIBERI** — Forged, not given.
> Earth evidence layer of the arifOS federation. Physics9-governed. Evidence-only. Never decides alone.

---

## What GEOX Does

GEOX is the **earth intelligence organ** — it ingests well logs, seismic, and geological observations; computes petrophysics, synthetics, and basin models; and preserves every interpretation with evidence, alternatives, and uncertainty.

| Task | Status |
|------|--------|
| LAS well log ingestion | ✅ Marmousi + Volve field wells |
| Petrophysical computation | ✅ Vsh, φ, Sw — Archie + density methods |
| SEG-Y seismic inspection | ✅ Header, trace count, sample rate, coordinates |
| Synthetic seismogram generation | ✅ Ricker / Ormsby / Klauder wavelets |
| Seismic attribute computation | ✅ RMS, sweetness, variance, spectral |
| Seismic interpretation (horizon / fault) | ✅ Contrast detection + RSI pipeline |
| Basin analysis + deep-time context | ✅ Backstrip, thermal maturity, mass balance |
| Sequence stratigraphy | ✅ Well correlation + biostrat parsing |
| Geomechanics | ✅ Moduli, stress polygon, pore pressure |
| Gravity / magnetic forward modeling | ✅ Prism-based, screening mode |
| Prospect evaluation | ✅ Volumetrics, POS, EVOI |
| Geological claim management | ✅ Create, challenge, falsify, seal |
| MCP Apps (SEP-1865) | ✅ 6 apps LIVE (Well Witness, Prospect Forge, Seismic Viewer, Basin Explorer, Risk Console, Operator Console) |
| Cross-organ capital routing | ✅ WEALTH bridge |

---

## Live Surface

| Metric | Value |
|--------|-------|
| Total MCP tools | 52 |
| Public tools | 24 (verify: `curl :8081/health`) |
| MCP Apps | 6 (LIVE — SEP-1865) |
| ui:// resources | 8 |
| Health | 🟢 GREEN |
| Port | 8081 |
| Version | `v2026.07.19` |
| License | BSL-1.1 (Business Source License) |

---

## Recent Milestones

| Date | Milestone | Detail |
|------|-----------|--------|
| 2026-07-19 | **P1 — MCP Apps Restore** | `prefab-ui` installed, 6 apps LIVE, GUI-ready |
| 2026-07-19 | **P0 — MCP Restore** | FastMCP 3.4.2 kwargs fix, 52 tools registered |
| 2026-07-19 | **SOT Audit** | License corrected (AGPL→BSL-1.1), version aligned, tool count synced |
| 2026-07-19 | **Gitwrap** | 4 feature branches removed, 2600+ lint errors fixed, CI advisory |

---

## Validated Datasets

| Dataset | Type | Status |
|---------|------|--------|
| **Marmousi2** | Synthetic 2D seismic + 3 wells | ✅ Full pipeline |
| **Volve field** | Real North Sea wells + production | ✅ Well logs ingested (12+ curves) |
| | | ⚠️ SEG-Y pending (Equinor license required) |

---

## MCP Apps (SEP-1865)

| App | ui:// Resource | Status |
|-----|---------------|--------|
| GEOX Well Witness | `ui://geox/well-desk` | LIVE |
| GEOX Prospect Forge | `ui://geox/prospect-ui` | LIVE |
| GEOX Seismic Viewer | `ui://geox/seismic-vision-review` | LIVE |
| GEOX Basin Explorer | `ui://geox/earth-volume` | LIVE |
| GEOX Risk Console | `ui://geox/judge-console` | LIVE |
| GEOX Operator Console | `ui://geox/operator` | LIVE |

Connect via: `https://geox.arif-fazil.com/mcp`

---

## Quick Start

```bash
# Install
cd /root/GEOX && pip install -e ".[dev]"

# Run tests
PYTHONPATH=src pytest tests/ -q --tb=short

# Start server
python -m geox_mcp.server

# Health check
curl http://localhost:8081/health
```

### Ingest a well log
```
geox_well_ingest(mode="auto", source_uri="/data/wells/my-well.las", well_id="MY-WELL-1")
```

### Compute petrophysics
```
geox_petrophysics(mode="generate", well_id="MY-WELL-1",
  curves={...}, matrix_density=2.65, rw=0.05)
```

---

## Architecture

GEOX separates four things that most subsurface software conflates:

1. **Observation** — what was measured (log value, seismic amplitude)
2. **Derivation** — what was computed (porosity, impedance)
3. **Interpretation** — what was concluded (reservoir, seal, charge)
4. **Speculation** — what was assumed (fluid phase, migration pathway)

Every output carries an epistemic label (OBS / DER / INT / SPEC) and an uncertainty band.

---

## Repository

```
src/geox_core/         ← Physics truth engine (NOT agent-facing)
    engines/petrophysics/   ← PINN, Archie, Sw, net-pay
    engines/seismic/        ← AC risk, synthetic, well-tie

src/geox_mcp/          ← MCP agent surface
    tools/                  ← All 52 MCP tools
    resources/              ← 8 ui:// resources
    prompts/                ← MCP prompt templates

apps/                   ← 6 MCP Apps (SEP-1865)
docs/                   ← Documentation
tests/                  ← Test suite (60+ files)
GENESIS/                ← Constitutional charter
```

---

## What GEOX Is Not

GEOX is **not** a replacement for Petrel, DecisionSpace, PaleoScan, or OpendTect. It cannot edit horizons interactively, build geocellular grids, or run reservoir simulation.

It IS a vendor-neutral layer that can:
- Challenge interpretations from incumbent software
- Preserve the evidence behind every geological claim
- Compute selected subsurface workflows with full provenance
- Route capital consequences from geology to decision frameworks

---

## License

BSL-1.1 (Business Source License). See [LICENSE](./LICENSE).

---

*Maintained under F13 SOVEREIGN. Built on Marmousi, validated on Volve.*
