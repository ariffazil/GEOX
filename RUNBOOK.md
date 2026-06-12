# RUNBOOK.md — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Port:** 8081
> **Last Updated:** 2026-06-12

## Start / Stop
```bash
systemctl start geox-mcp
systemctl stop geox-mcp
systemctl restart geox-mcp
systemctl status geox-mcp
```

## Health Check
```bash
curl -s http://127.0.0.1:8081/health | python3 -m json.tool
```

## Logs
```bash
journalctl -u geox-mcp -n 50 --no-pager
journalctl -u geox-mcp -f   # follow
```

## Test
```bash
cd /root/geox
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -q --tb=short
```

## Common Failure Modes
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| /health unreachable | Service crashed | `systemctl restart geox-mcp` |
| /mcp returns 404 | Caddy misroute | Check `/etc/caddy/Caddyfile` GEOX block |
| Tools returning errors | Python env broken | `pip install -e ".[dev]"` then restart |
| Port conflict | Another process on 8081 | `ss -tlnp | grep 8081` |

## What NOT to Do
- Do NOT bind to 0.0.0.0 (must be 127.0.0.1 — Caddy/Tunnel handles public)
- Do NOT modify GENESIS/ without F13 approval
- Do NOT change canonical tool surface without updating FEDERATION_STATUS.md
