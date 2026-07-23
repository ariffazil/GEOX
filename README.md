<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-07-24T00:00Z
valid_until: 2026-08-24
federation_release: v2026.07.20-ZEN-CONVERGENCE
live_commit: c2397743
truth_rule: live :8081/health + tools/list beat any static count in prose
mcp_tools_live: dynamic_from_tools_list
epistemic_standard: OBS / DER / INT / SPEC labels apply to this document itself
-->

# 🌊 GEOX — Subsurface Intelligence Workbench

> **DITEMPA BUKAN DIBERI** — Forged, not given.
> Earth evidence layer of the arifOS federation. Physics9-governed. Evidence-only. Never decides alone.

---

## What GEOX Does

GEOX is the **earth intelligence organ** — it ingests well logs, seismic, and geological observations; computes petrophysics, synthetics, and basin models; and preserves every interpretation with evidence, alternatives, and uncertainty.

Each capability below carries an **epistemic label** — the same OBS / DER / INT / SPEC standard GEOX enforces on its own outputs:

| Task | Status | Label |
|------|--------|-------|
| LAS well log ingestion | ✅ Marmousi + Volve field wells | OBS |
| Petrophysical computation | ✅ Vsh, φ, Sw — Archie + density methods | OBS |
| SEG-Y seismic inspection | ✅ Header, trace count, sample rate, coordinates | OBS |
| Synthetic seismogram generation | ✅ Ricker / Ormsby / Klauder wavelets | OBS |
| Seismic attribute computation | ✅ RMS, sweetness, variance, spectral | OBS |
| Seismic interpretation (horizon / fault) | ✅ Contrast detection + RSI pipeline | DER |
| Basin analysis + deep-time context | ✅ Backstrip, thermal maturity, mass balance | DER |
| Sequence stratigraphy | ✅ Well correlation + biostrat parsing | DER |
| Geomechanics | ✅ Moduli, stress polygon, pore pressure | DER |
| Gravity / magnetic forward modeling | ✅ Prism-based, screening mode | DER |
| Prospect evaluation | ✅ Volumetrics, POS, EVOI | DER |
| Geological claim management | ✅ Create, challenge, falsify, seal | OBS |
| MCP Apps (SEP-1865) | ✅ 6 apps LIVE (Well Witness, Prospect Forge, Seismic Viewer, Basin Explorer, Risk Console, Operator Console) | OBS |
| Cross-organ capital routing | ⚠️ WEALTH bridge — implemented, integration-sealed tests pending | INT |

> **Label key:** OBS = directly validated against test data · DER = computed from validated inputs · INT = interpreted / integration claim pending sealed evidence · SPEC = assumed, not yet tested.

---

## Live Surface

| Metric | Value | Source of truth |
|--------|-------|-----------------|
| MCP tools | dynamic — see `tools/list` | `curl https://geox.arif-fazil.com:8081/health` |
| MCP Apps | 6 (LIVE — SEP-1865) | `ui://` resources below |
| ui:// resources | 8 | server manifest |
| Health | **not asserted statically** — verify live | `curl :8081/health` |
| Port | 8081 | deployment config |
| Version | `v2026.07.20-ZEN-CONVERGENCE` | SOT-MANIFEST |
| License | BSL-1.1 (see transition note below) | [LICENSE](./LICENSE) |

> **F4 Clarity rule:** This README does not assert runtime health or tool counts as static prose. Per the SOT truth rule, the live `/health` endpoint and `tools/list` response are the only valid witnesses. A snapshot claim would be stale the moment it is read.

---

## Recent Milestones

| Date | Milestone | Detail |
|------|-----------|--------|
| 2026-07-19 | **P1 — MCP Apps Restore** | `prefab-ui` installed, 6 apps LIVE, GUI-ready |
| 2026-07-19 | **P0 — MCP Restore** | FastMCP 3.4.2 kwargs fix, 52 tools registered |
| 2026-07-19 | **SOT Audit** | License corrected (AGPL→BSL-1.1), version aligned, tool count synced |
| 2026-07-19 | **Gitwrap** | 4 feature branches removed, 2600+ lint errors fixed, CI advisory |
| 2026-07-24 | **README Constitutional Audit** | Version drift resolved, static health claims removed, epistemic labels applied, license transition documented |

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

**Prerequisites:** Python 3.11+, pip, and (for seismic workflows) write access to a data directory for LAS / SEG-Y ingestion.

```bash
# Install
cd /root/GEOX && pip install -e ".[dev]"

# Run tests
PYTHONPATH=src pytest tests/ -q --tb=short

# Start server
python -m geox_mcp.server

# Health check — the only valid health witness
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

**Failure contract:** when governance checks fail, GEOX fails closed — `888_HOLD` for outputs awaiting human ratification, `VOID` for ungrounded claims. No silent degradation, no ungoverned output.

---

## Repository

```
src/geox_core/         ← Physics truth engine (NOT agent-facing)
    engines/petrophysics/   ← PINN, Archie, Sw, net-pay
    engines/seismic/        ← AC risk, synthetic, well-tie

src/geox_mcp/          ← MCP agent surface
    tools/                  ← All MCP tools (count: see tools/list)
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

## Next Horizons

> Items below are **SPEC** until sealed by test evidence. This section documents what is being forged — not what is claimed.

| Horizon | Blocker / dependency | Status |
|---------|---------------------|--------|
| Volve SEG-Y full seismic pipeline | Equinor license clearance | ⚠️ Gated |
| WEALTH bridge integration sealing | End-to-end sealed test (geology → capital route) | INT → target OBS |
| Expanded `ui://` resource surface | SEP-1865 spec evolution | SPEC |
| Public tool inventory publication | `tools/list` snapshot in `docs/` per release | Planned |

---

## License

**BSL-1.1 (Business Source License).** See [LICENSE](./LICENSE).

> **Transition note (2026-07-19):** GEOX was previously published under AGPL. The SOT Audit of 2026-07-19 corrected this to BSL-1.1. Forks and clones obtained **before** that date remain governed by the license text they were obtained under; all copies from 2026-07-19 onward are BSL-1.1.

---

*Maintained under F13 SOVEREIGN. Built on Marmousi, validated on Volve.*
*DITEMPA BUKAN DIBERI — truth must cool before it rules.*
