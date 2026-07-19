<!-- SOT-MANIFEST
owner: Arif (F13 SOVEREIGN)
last_verified: 2026-07-15
valid_from: 2026-07-15
valid_until: 2026-08-15
confidence: high
scope: /root/GEOX core package map
domain_law: NATURAL_LAW
-->

# GEOX Core Import Map — single domain core

> **Zen:** one domain core package. MCP membrane imports **only** that core.  
> **Canonical package:** `geox_core` → `/root/GEOX/src/geox_core/`  
> **Membrane:** `geox_mcp` → `/root/GEOX/src/geox_mcp/`  
> **Live:** ~600 `geox_core` import references in tree (dominant)  
> **DITEMPA BUKAN DIBERI**

---

## 1. Canonical layout

```
GEOX/
├── src/
│   ├── geox_mcp/          # MCP MEMBRANE (public tools/resources/prompts)
│   │   ├── server.py
│   │   ├── tools_wiring.py
│   │   ├── tools/ · resources/ · prompts/
│   │   └── ...
│   └── geox_core/         # DOMAIN CORE (NATURAL_LAW) — CANONICAL
│       ├── physics/       # Physics9 · manifests · guards
│       ├── engines/       # stratigraphy · vision · geophysics · earth_obs
│       ├── core/          # 1d petrophysics · welltie · volumetrics · ac_risk
│       ├── seismic/ · seismic_pipeline/ · seismic_cognition
│       ├── schemas/ · envelopes/ · enums/
│       ├── governance/ · bridges/ · integrations/
│       ├── io/ · renderers/ · artifacts/
│       ├── wealth/        # ⚠️ feed/adapter math only — NOT WEALTH organ authority
│       └── skills/ · services/ · lem/
├── core/                  # LEGACY SHIM tree (root) — do not extend
├── geox/                  # LEGACY namespace package — do not extend
└── adapters/              # federation edges (e.g. wealth_bridge)
```

### Import rules (agents + code)

| Allowed | Forbidden (new code) |
|---------|----------------------|
| `from geox_core...` | New `from core.` (root package) without migration path |
| `from geox_mcp...` (membrane only) | Domain physics inside `apps/` without MCP call |
| `from adapters...` for peer edges | Public MCP tools that **own** capital SEAL/EMV authority |

```python
# GOOD — membrane → core
from geox_core.physics.manifest import get_domain_law, get_physics_manifest_hash
from geox_core.core.geox_1d import compute_vsh_gr, compute_sw_archie
from geox_core.engines.stratigraphy.accommodation import ...

# AVOID in new code — legacy root core
from core.physics9 import ...          # migrate → geox_core.physics / geox_core.core
from core.shared.saf_stats import ...  # migrate or vendor under geox_core
```

---

## 2. Package roles

| Path | Role | Status |
|------|------|--------|
| **`src/geox_core/`** | **Canonical NATURAL_LAW body** | **USE** |
| **`src/geox_mcp/`** | Public MCP membrane | **USE** |
| **`core/`** (repo root) | Historical flat modules (physics9, geox_1d, …) | **LEGACY** — mirror/subset of geox_core.core; no new features |
| **`geox/`** | Older namespace (seismic, well, wealth subpkgs) | **LEGACY** — prefer geox_core |
| **`adapters/`** | Peer federation (wealth_bridge) | **USE** for edges only |
| **`apps/` · `geox-gui/`** | Human shells | Host-proxied; no silent geology |

---

## 3. Membrane → core dependency map (high traffic)

| Membrane area | Imports from `geox_core` |
|---------------|--------------------------|
| `server.py` health / domain_law | `physics.manifest` |
| `tools_wiring.py` | engines.stratigraphy · seismic_pipeline · welltie_mcp · schemas |
| `tools/vision.py` | engines.vision |
| `tools/earth_surface.py` | io fetchers (usgs, etopo, gebco) |
| `tools/seismic_compute_unified.py` | schemas.tie_* |
| `render_well_panel_petro.py` | core.geox_1d · benchmarks |
| `resources/` | enums.statuses · physics.manifest · schemas.render_payload |
| `events/` | governance.event_bus |

**Residual non-canonical imports (migrate):**

| File | Legacy import | Target |
|------|---------------|--------|
| `geox_mcp/tools/qc.py` | `core.shared.saf_stats` | `geox_core...` or shared stats package |
| `geox_mcp/tools/claims.py` | `core.organ_ledger_bridge` | `geox_core.governance` / vault bridge |

---

## 4. `geox_core` internal map (domain law zones)

| Zone | Path under `geox_core/` | Responsibility |
|------|-------------------------|----------------|
| **Physics law** | `physics/`, `laws/` | Bounds, manifests, `domain_law=NATURAL_LAW` |
| **1D–4D earth** | `core/geox_1d…4d`, engines | Petrophysics, structure, time |
| **Seismic** | `seismic*`, `avo/` | Wavefield / attributes / cognition |
| **Basin / deep time** | engines + services | Burial, mass balance, thermal |
| **Epistemic** | `enums/`, `envelopes/`, `schemas/` | OBS/DER/INT, claim shapes |
| **Governance glue** | `governance/`, `integrations/` | Event bus, arifOS hooks |
| **Wealth feed** | `wealth/` | Volumetrics → **feed numbers only**; public capital authority is WEALTH organ |
| **Vision** | `engines/vision/` | Perceptual inventory (F9 humility) |

---

## 5. Wealth bleed note (structure)

`geox_core/wealth/` and `adapters/wealth_bridge.py` may **prepare feeds** (STOIP, EMV inputs).  

They **must not**:

- replace WEALTH MCP as capital SOT  
- expose public `geox_*` tools that authorize capital  
- seal money decisions  

Public wealth-bridge MCP tools were **deregistered** (2026-07-10). Keep internal adapter-only.

---

## 6. Migration checklist

- [x] Document canonical = `src/geox_core`  
- [x] Membrane primarily imports `geox_core` (~600 refs)  
- [ ] Move `core.shared.saf_stats` / `core.organ_ledger_bridge` call sites  
- [ ] Stop new files under root `core/` and top-level `geox/`  
- [ ] Optional: shim root `core/` → re-export from `geox_core` with DeprecationWarning  

---

## 7. Agent one-liner

```
GEOX body = geox_core. GEOX face = geox_mcp. Root core/ + geox/ = legacy. Adapters = edges only.
```

*Physics first. One core. NATURAL_LAW.*
