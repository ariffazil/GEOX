# GEOX State of the Tree (SOT) — 2026-05-11

> **Canonical runtime reference for GEOX**
> **Seal:** DITEMPA BUKAN DIBERI
> **Version:** `v2026.05.10-KANON`
> **Authority posture:** `fail_closed`

---

## Quick Reference

| Attribute | Value |
|-----------|-------|
| Canonical repository | `https://github.com/ariffazil/geox` |
| Canonical branch | `main` |
| Repo head audited | `a7807bcb` |
| Public health | `https://geox.arif-fazil.com/health` |
| Public ready | `https://geox.arif-fazil.com/ready` |
| Public MCP | `https://geox.arif-fazil.com/mcp` |
| Ready status | `ok` |
| Canonical tools | `39` |
| Legacy aliases | `85` |
| Contract epoch | `2026-05-01-GEOX-13TOOLS-v0.4` |

---

## Live Runtime Truth

| Field | Value |
|---|---|
| Service | `geox-mcp-kernel` |
| Identity | `GEOX` |
| Role | `Earth Substrate Witness` |
| Authority | `TERRAIN_WITNESS` |
| Profile | `full` |
| Enabled dimensions | `prospect`, `well`, `earth3d`, `map`, `cross`, `physics`, `section`, `canonical` |
| Auth mode | `fail_closed` |
| Caddy upstream | `127.0.0.1:8081` |

---

## Canonical Guidance

- GEOX public truth is the readiness contract exposed at `/ready`; the README and contract tree must stay aligned with that count.
- Legacy aliases remain callable for compatibility, but the canonical surface is 40 tools.
- Public ingress is now host-safe through localhost proxying rather than Docker-only service names.
