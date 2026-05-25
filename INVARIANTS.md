# INVARIANTS.md — GEOX Earth Intelligence
> **DITEMPA BUKAN DIBERI** — Federated Source of Truth.
> **Owner:** GEOX
> **Last verified:** 2026-05-25

## Owns
- Earth science, geoscience, petrophysics
- Seismic data processing
- Well log analysis (LAS, DLIS)
- Stratigraphic correlation
- DST analysis

## Does NOT Own
- Constitutional law (→ arifOS)
- Capital intelligence (→ WEALTH)
- Execution (→ A-FORGE)

## Live State

| Item | Value | Verified |
|------|-------|----------|
| Port | **18081** (NOT 8081) | ✅ |
| Health | `https://geox.arif-fazil.com/health` → `{"status":"ok"}` | ✅ |
| Daemon | `python3 geoxd.py` | ✅ |

## Port History

| Date | Port | Note |
|------|------|------|
| Pre-2026-05-25 | 8081 | Wrong — daemon was never on 8081 |
| 2026-05-25 | **18081** | Correct — organ-standard alignment |

## Required Health Check
```bash
curl http://127.0.0.1:18081/health
# or
curl https://geox.arif-fazil.com/health
# Expected: {"status": "ok", "daemon_up": true, ...}
```

## Forbidden Stale Assumptions
- ❌ GEOX on port `8081` — it is `18081`
- ❌ Any Caddyfile route to `:8081` for GEOX — it is `:18081`
- ❌ Any doc saying GEOX daemon on `8081`
- ❌ Any MCP config pointing to `localhost:8081` for GEOX

## Related Files
- `geoxd.py` — canonical daemon
- `HEALTHCHECK.md` — deployment notes
- `AGENT_KERNEL_START.md` — estate entry ritual
