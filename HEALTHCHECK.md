# GEOX Health and Deployment Notes
> **DITEMPA BUKAN DIBERI** — Earth Intelligence. Last verified: 2026-06-02.

## Live Port: 8081

**IMPORTANT:** GEOX daemon runs on port **8081**, not 18081.
Port 18081 is now used by **arifosd** (the constitutional control plane / GEOX bridge).
If you find any GEOX config, Caddyfile, or MCP manifest pointing to 18081, it is **stale and must be updated to 8081**.

Verify with:
```bash
ss -ltnp | grep 8081
# should show: python3 -m geox_mcp.server
systemctl status geox-mcp
```

## Starting GEOX Daemon

The service is managed by systemd — **do not start it manually**:

```bash
# Status
systemctl status geox-mcp

# Restart (after config change)
sudo systemctl restart geox-mcp

# View logs
journalctl -u geox-mcp -n 50 --no-pager
```

Manual start (only for local debugging, never in production):
```bash
cd /root/geox
python3 -m geox_mcp.server --host 127.0.0.1 --port 8081
```

## Health Check

```bash
# Local
curl http://127.0.0.1:8081/health

# Public
curl https://geox.arif-fazil.com/health
```

Expected response (healthy):
```json
{
  "status": "healthy",
  "registry_truth": "VERIFIED",
  "timestamp": "2026-06-02T..."
}
```

## Caddy Route (Current — VERIFIED 2026-06-02)

All GEOX routes in `/etc/caddy/Caddyfile` point to `127.0.0.1:8081`:
```
geox.arif-fazil.com -> 127.0.0.1:8081
```

If you find a route pointing to `:18081` for GEOX, it is **stale and must be updated**.

The `/mcp` route uses `handle /mcp /mcp/*` (preserves path) — `handle_path` would strip `/mcp` and the backend would 404.

## MCP Endpoint

- **Public:** `https://geox.arif-fazil.com/mcp`
- **Local:** `http://127.0.0.1:8081/mcp`

## Port History

| Date | Port | Notes |
|------|------|-------|
| Pre-2026-05-25 | 8081 | Was correct before the port-history doc got out of sync |
| 2026-05-25 → 2026-06-01 | 18081 | Doc claimed this; reality was always 8081 per `geox-mcp.service` |
| 2026-06-02 | 8081 | **Corrected** — systemd unit, Caddyfile, and all contracts aligned to 8081. The 18081 port is owned by arifosd. |
