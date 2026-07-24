<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-07-24T00:00Z
valid_until: 2026-08-24
federation_release: v2026.07.23-PHASE-C-SEALED
live_commit: 8b45a88e
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
| Structural geology battery | ✅ 6/6 Malay Basin battery green — K-DIP arccos (SVD normal vector), full-trace K-THROW (tip→centre→tip), zero-false-negative regime aliasing | OBS |
| MCP Apps (SEP-1865) | ✅ 6 apps LIVE (Well Witness, Prospect Forge, Seismic Viewer, Basin Explorer, Risk Console, Operator Console) | OBS |
| Cross-organ capital routing | ⚠️ WEALTH bridge — implemented, integration-sealed tests pending | INT |

> **Label key:** OBS = directly validated against test data · DER = computed from validated inputs · INT = interpreted / integration claim pending sealed evidence · SPEC = assumed, not yet tested.

---

## Live Surface

| Metric | Value | Source of truth |
|--------|-------|-----------------|
| MCP tools (public canonical) | 31 — live-witnessed 2026-07-23 (`tools_loaded: 31`) | `curl :8081/health` + `tools/list` |
| MCP Apps | 6 (LIVE — SEP-1865) | `ui://` resources below |
| ui:// resources | 8 | server manifest |
| Health | **not asserted statically** — verify live | `curl :8081/health` |
| Port | 8081 | deployment config |
| Version | `v2026.07.23-PHASE-C-SEALED` | SOT-MANIFEST |
| License | BSL-1.1 → Apache 2.0 on 2029-06-29 (see note below) | [LICENSE](./LICENSE) + `pyproject.toml` |

> **F4 Clarity rule:** Runtime health and tool counts are witnessed live, not asserted as static prose — per the SOT truth rule, `/health` and `tools/list` are the only valid witnesses. The value 31 above is an OBS-recorded snapshot of the 2026-07-23 witness, not a standing claim. (Earlier prose citing 52 tools reflected an unconsolidated legacy list and has been retired.)

---

## Recent Milestones

| Date | Milestone | Detail |
|------|-----------|--------|
| 2026-07-23 | **Phase C hardening** | K-DIP/K-DL/K-THROW regime aliases wired (commit `8ce723b0`); 6/6 Malay Basin test battery PASS |
| 2026-07-23 | **Audit drift fix** | README reconciled with live `health` + `tools/list` (this update) |
| 2026-07-19 | **P1 — MCP Apps Restore** | `prefab-ui` installed, 6 apps LIVE, GUI-ready |
| 2026-07-19 | **P0 — MCP Restore** | FastMCP 3.4.2 kwargs fix, tools registered |
| 2026-07-19 | **SOT Audit** | License corrected (AGPL→BSL-1.1), version aligned, tool count synced |
| 2026-07-19 | **Gitwrap** | 4 feature branches removed, 2600+ lint errors fixed, CI advisory |
| 2026-07-23 | **Phase C Sealed State** | K-DIP arccos (SVD normal vector math), full-trace K-THROW (tip→centre→tip), zero-false-negative regime aliasing (extensional/compressional), SEP-1865 3-channel UI bindings — **75/75 unit tests + 6/6 Malay Basin battery green** |
| 2026-07-23 | **License Falsification Audit** | AGPL marking identified as drift; BSL-1.1 confirmed against LICENSE + `pyproject.toml` (commit `8b45a88e`) |
| 2026-07-24 | **README Constitutional Audit** | Three-way divergence reconciled: Phase C facts merged, epistemic labels applied, static health claims removed |

---

## Validated Datasets

| Dataset | Type | Status |
|---------|------|--------|
| **Marmousi2** | Synthetic 2D seismic + 3 wells | ✅ Full pipeline |
| **Volve field** | Real North Sea wells + production | ✅ Well logs ingested (12+ curves) |
| | | ⚠️ SEG-Y pending (Equinor license required) |

---

## MCP Apps (SEP-1865)

Live surface (verified via `resources/list` on `geox-8ce723b0`):

| App | ui:// Resource | Status |
|-----|---------------|--------|
| GEOX Well Witness | `ui://geox/well-desk` | **LIVE** |
| GEOX Prospect Forge (Basin Explorer) | `ui://geox/prospect-ui` | **LIVE** |
| GEOX Seismic Viewer | `ui://geox/seismic-vision-review` | LIVE (deprecated 2026-07-16; consider replacement) |
| GEOX Dashboard | `ui://geox/geox-mcp-visual` | **LIVE** |
| — | `ui://geox/earth-volume` | **NOT REGISTERED** — source exists at `apps/earth-volume/` |
| — | `ui://geox/judge-console` | **NOT REGISTERED** — source exists at `apps/judge-console/` |
| — | `ui://geox/operator` | **MISSING** — only in `999_vault/archive/apps-legacy-2026-07-15/` |

Sovereign decision pending: register earth-volume + judge-console, or archive them. Restoration requires a `forge_apps` registration call.

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
    tools/                  ← Canonical public tool surface (31, live-witnessed)
    resources/              ← 8 ui:// resources
    prompts/                ← MCP prompt templates

apps/                   ← MCP Apps registry (4 LIVE, 4 on disk, 1 in legacy archive)
docs/                   ← Documentation
tests/                  ← Test suite (60+ files; 75/75 unit + 6/6 structure battery)
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

**BSL-1.1 (Business Source License 1.1)** — converts to **Apache 2.0 on 2029-06-29** per the Change Date in [LICENSE](./LICENSE) (confirmed against `pyproject.toml`).

> **License history:** GEOX was briefly marked AGPL prior to the 2026-07-19 SOT Audit, which corrected it to BSL-1.1; a falsification audit on 2026-07-23 re-confirmed BSL-1.1 as canonical. All copies from 2026-07-19 onward are BSL-1.1.

---

*Maintained under F13 SOVEREIGN. Built on Marmousi, validated on Volve.*
*DITEMPA BUKAN DIBERI — truth must cool before it rules.*
