<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
last_verified: 2026-07-19
valid_until: 2026-08-19
truth_rule: live :8081/health + tools/list beat any static count in prose
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
| MCP Apps (SEP-1865) | ✅ 13 apps — Well Desk, Seismic Vision, Earth Volume, Judge Console |
| Cross-organ capital routing | ✅ WEALTH bridge |

---

## Live Surface

| Metric | Value |
|--------|-------|
| Public tools | 24 (verify: `curl :8081/health`) |
| MCP Apps (SEP-1865) | 13 |
| Health | GREEN |
| Port | 8081 |
| Version | `v2026.07.19` |

---

## Validated Datasets

| Dataset | Type | Status |
|---------|------|--------|
| **Marmousi2** | Synthetic 2D seismic + 3 wells | ✅ Full pipeline |
| **Volve field** | Real North Sea wells + production | ✅ Well logs ingested (12+ curves) |
| | | ⚠️ SEG-Y pending (Equinor license required) |

---

## Quick Start

```bash
# Install
cd /root/geox && pip install -e ".[dev]"

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

### Generate a synthetic seismogram
```
geox_seismic_compute(mode="synthetic", well_id="MY-WELL-1",
  vp=[...], rho=[...], depth=[...], wavelet_type="ricker", wavelet_freq=30)
```

### Falsify a geological claim
```
geox_falsify(claim_text="Fault seal exists at 2500m", claim_type="structural", mode="full")
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
    tools/                  ← All public tools
    resources/              ← MCP resource definitions
    prompts/                ← MCP prompt templates

apps/                   ← MCP Apps (SEP-1865)
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

BSL-1.1 (Business Source License).

---

*Maintained under F13 SOVEREIGN. Built on Marmousi, validated on Volve.*
