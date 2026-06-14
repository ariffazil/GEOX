# INVARIANTS.md — GEOX Earth Intelligence
> **DITEMPA BUKAN DIBERI** — Federated Source of Truth.
> **Owner:** GEOX
> **Last verified:** 2026-06-03

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
| Port | **8081** (NOT 18081) | ✅ `ss -tlnp` shows `geox_mcp.server` PID 1888572 on `0.0.0.0:8081` |
| Health | `https://geox.arif-fazil.com/health` → 200, `registry_truth=VERIFIED` | ✅ |
| Daemon | `python3 -m geox_mcp.server` via `geox-mcp.service` (systemd) | ✅ |
| Tool count | 39 canonical (`CANONICAL_PUBLIC_TOOLS` in `src/geox_mcp/registry.py`) | ✅ |
| Version | v2026.05.27 · contract epoch 2026-05-12-GEOX-13TOOLS-v0.7 | ✅ |

> **Important — what lives on each port:**
> - **`8081`** = `geox_mcp.server` (this organ) — the Earth evidence FastMCP service
> - **`18081`** = `arifosd.py` (the constitutional daemon) — different process, NOT geox
> - A historical doc claimed 18081 was geox; it is not. The Caddy route for `geox.arif-fazil.com` correctly proxies to `:8081`.

## Port History

| Date | Port | Note |
|------|------|------|
| Pre-2026-05-25 | 8081 | Correct — geox has been on 8081 since the early Docker era |
| 2026-05-25 (claim) | 18081 | Was proposed as "organ-standard alignment" but never actually deployed — geox stayed on 8081 |
| 2026-06-03 (current) | **8081** | The live systemd `geox-mcp.service` binds `--port 8081`; do not change without sovereign ack |

## Required Health Check
```bash
curl http://127.0.0.1:8081/health
# or
curl https://geox.arif-fazil.com/health
# Expected: {"status": "healthy", "registry_truth": "VERIFIED", ...}
```

## Forbidden Stale Assumptions
- ❌ GEOX on port `18081` — it is `8081` (18081 is arifosd)
- ❌ Any Caddyfile route to `:18081` for GEOX — it must be `:8081`
- ❌ Any doc saying GEOX daemon on `18081`
- ❌ Any MCP config pointing to `localhost:18081` for GEOX
- ❌ Tool count `28` — the live surface is **39 canonical** (`CANONICAL_PUBLIC_TOOLS`)
- ❌ Tool count `21` — same: 39 is the truth

## ⚠️ Caddy misroute flagged (2026-06-03)

The Caddyfile route `geox.arif-fazil.com` correctly proxies to `:8081` ✓.
The Caddyfile route `/api/organs/geox/health` is currently misrouted to `:18081`
(which is `arifosd.py`, not geox). The `/api/organs/geox/health` path returns
arifosd's `/health` response shape, not geox's. **This is a 888_HOLD Caddyfile
edit** — flagged for sovereign approval, not auto-fixed by the agent.

## Related Files
- `src/geox_mcp/registry.py` — canonical daemon (39 canonical tools)
- `HEALTHCHECK.md` — deployment notes
- `AGENT_KERNEL_START.md` — estate entry ritual
- `/etc/systemd/system/geox-mcp.service` — systemd unit binding 8081
