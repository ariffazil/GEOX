# GEOX Health and Deployment Notes
> **DITEMPA BUKAN DIBERI** — Earth Intelligence. Last verified: 2026-05-25.

## Live Port: 18081 (NOT 8081)

**IMPORTANT:** GEOX daemon runs on port **18081**, not 8081.
Port 8081 is dead. Any config, Caddyfile, or MCP manifest pointing to 8081 for GEOX is stale.

Verify with:
```bash
ss -ltnp | grep 18081
# should show: python3 /root/geox/geoxd.py
```

## Starting GEOX Daemon

```bash
cd /root/geox
python3 geoxd.py
# or with explicit port:
python3 geoxd.py --port 18081
```

## Health Check

```bash
# Local
curl http://127.0.0.1:18081/health

# Public
curl https://geox.arif-fazil.com/health
```

Expected response:
```json
{"status": "ok", "daemon_up": true, "storage_writable": true, "vault_accessible": true, ...}
```

## Caddy Route (Current — VERIFIED 2026-05-25)

All GEOX routes in `/root/arifOS/Caddyfile` point to `127.0.0.1:18081`:
```
geox.arif-fazil.com -> 127.0.0.1:18081
```

If you find a route pointing to `:8081`, it is **stale and must be updated**.

## MCP Endpoint

- **Public:** `https://geox.arif-fazil.com/mcp`
- **Local:** `http://127.0.0.1:18081/mcp`

## Port History

| Date | Port | Notes |
|------|------|-------|
| Pre-2026-05-25 | 8081 | Wrong — daemon actually on 18081 |
| 2026-05-25 | 18081 | Correct — organ-standard alignment |
