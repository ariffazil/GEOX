# REPO_ROUTING_CONSTITUTION.md
> **DITEMPA BUKAN DIBERI** — Routing intelligence is earned, not assumed.
> **Version:** 2026.05.02-KANON | **Authority:** Human Architect (Arif)

---

## MISSION

Put every piece of work into the **correct repository** — on VPS and on GitHub.
Prefer refusal over misrouting.

---

## AUTHORITATIVE REPO MAP

| Repo | Domain Charter | VPS Workspace | GitHub |
|------|---------------|---------------|--------|
| **AAA** | Agent workspace, governance, ADRs, orchestration canon | `/root/AAA/` | `github.com/ariffazil/AAA` |
| **WEALTH** | Capital intelligence, portfolio, finance | `/root/WEALTH/` | `github.com/ariffazil/wealth` |
| **GEOX** | Earth domain, geo/terrain/maps, well logs, subsurface | `/root/GEOX/` | `github.com/ariffazil/geox` |
| **arifOS** | Constitutional kernel, F1–F13 floors, MCP runtime | `/root/arifOS/` | `github.com/ariffazil/arifOS` |
| **A-FORGE** | Planning twin, design, architecture | `/root/A-FORGE/` | `github.com/ariffazil/A-FORGE` |
| **arif-sites** | Website/static/web-facing assets | `/root/arif-sites/` | `github.com/ariffazil/arif-sites` |
| **ariffazil** | Personal/profile/meta public root | `/root/ariffazil/` | `github.com/ariffazil/ariffazil` |

---

## CLASSIFICATION RULES

1. Finance code → WEALTH. MCP/floors → arifOS. Earth/subsurface → GEOX. Agent governance → AAA. Planning/design → A-FORGE. Web assets → arif-sites.
2. If confidence < 0.8, stop and ask.
3. Cross-repo moves require 888_HOLD.

---

## PUSH GATE RULES

Never: ❌ `git push origin main`. Always: ✅ branch → PR.

---

**Ditempa Bukan Diberi — Routing intelligence is forged, not given.**

---

## APPENDIX: GEOX Earth-Domain Tool Behaviour (2026.05.02)

### M5 — Structured error schema for NPD/EIA tools

All five NPD/EIA open-energy tools (`geox_field_observe_npd`, `geox_well_load_npd`, `geox_production_observe_npd`, `geox_price_observe_eia`, `geox_production_observe_eia`) return a canonical error envelope on failure:

```json
{
  "error": "upstream_unavailable",
  "source": "npd.no",
  "details": "Connection refused",
  "retry_hint": "later",
  "status": "error",
  "claim_tag": "UNKNOWN",
  "data_origin": null
}
```

Error codes: `upstream_unavailable` | `config_missing` | `bad_request` | `unsupported_query`

Downstream tools can distinguish "no data" (`error=upstream_unavailable`, `source=upstream`) from "service broken" by branching on `source`.

### L3 — data_origin tagging

| data_origin | Meaning |
|---|---|
| `OBSERVED` | Real data from upstream API (NPD/EIA) |
| `SYNTHETIC_FIXTURE` | Generated fixture / test data |
| `null` | Error path (no data) |

All five NPD/EIA tools and `geox_well_compute_petrophysics` carry `data_origin` on success. Error paths carry `data_origin: null` explicitly.

### M6 — RHOB nullable explicit

`geox_well_compute_petrophysics` now emits `rhob: null` in every curve sample and declares `RHOB` as `"nullable": true` in the `curve_manifest`.

### L1 — geox_map_get_context_summary bounds

| Input | Result |
|---|---|
| `bounds=None` | `error=bounds_required`, `area=0.0`, `claim_tag=UNKNOWN` |
| `bounds={xmin:2,ymin:59,xmax:5,ymax:62}` (Norwegian shelf) | `area>0`, `area_unit=degrees_squared`, `width_deg`/`height_deg` present |

```python
# Downstream can branch on data_origin
if result.get("data_origin") == "SYNTHETIC_FIXTURE":
    # treat as hypothesis, not evidence
```
