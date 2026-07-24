# GEOX MCP Apps Readiness — Index (SOT pointer)

> **Updated:** 2026-07-24 · **Seal level target:** S4 portfolio  
> **Live truth:** `:8081/health` + `pytest tests/test_mcp_apps_readiness.py` beat this page.

## Status snapshot

| Layer | Status |
|-------|--------|
| Public tools | **32** |
| WellDesk public URL | **READY** `/apps/well-desk/` |
| Host shell `ui://geox/well-desk` | **READY** `p0-viz.html` |
| Demo registry | `resources/demo_wells.json` |
| Readiness tests | `tests/test_mcp_apps_readiness.py` |
| F2 petro runbook | [GEOX_PETRO_RUNBOOK_F2.md](./GEOX_PETRO_RUNBOOK_F2.md) |
| Verification matrix | [mcp_apps_verification_matrix.md](./mcp_apps_verification_matrix.md) |
| Host matrix | [HOST_COMPATIBILITY_MATRIX.md](./HOST_COMPATIBILITY_MATRIX.md) |

## Deploy (one path)

```bash
# From /root/GEOX
make deploy-apps
# = rsync apps → /var/www/html/geox/apps + /opt/geox/app/apps
#   + seed demo evidence + restart geox-mcp
```

## Smoke (host hydrate)

```bash
PYTHONPATH=src python3 - <<'PY'
import asyncio
from geox_mcp.tools.integration_well import geox_well_desk_open
async def main():
    r = await geox_well_desk_open(well_id="DEMO-KINABALU")
    sc = r.structured_content if hasattr(r,'structured_content') else r
    print(sc.get('ok'), sc.get('data_class'), list((sc.get('curves') or {}).keys()), len(sc.get('depths') or []))
asyncio.run(main())
PY
```

## Seal levels

| Level | Meaning |
|-------|---------|
| S1 Host shell | p0-viz + demo LAS hydrate |
| S2 Flow | ingest→qc→open→petro→render |
| S3 Evidence | generate/verify with seeded refs |
| S4 Portfolio | surface hygiene + catalog + docs |

## Residual (honest)

- ChatGPT live screenshot re-run (human host) may still be DEFERRED
- `generate` requires seeded artifacts (`make seed-evidence`)
- Full multi-file WellDesk is browser-only; MCP host uses p0-viz

DITEMPA BUKAN DIBERI
