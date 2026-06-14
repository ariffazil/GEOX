# CONTEXT.md — GEOX (Earth Intelligence)

> **Organ:** GEOX | **Port:** 8081 | **Repo:** `ariffazil/geox`
> **Kernel SoT:** `ariffazil/arifos` (FEDERATION_CONTRACT.md + GENESIS/000)
> **Last Updated:** 2026-06-12

## Live State
- **Service:** `geox-mcp.service` (systemd, enabled)
- **Health:** `http://127.0.0.1:8081/health`
- **Tools:** 40 canonical MCP tools
- **License:** Apache-2.0 (scientific tooling; federation governed by kernel AGPL-3.0)

## Dependencies
- arifOS MCP kernel (port 8088) — constitutional judgment
- No database dependencies (stateless earth coprocessor)
- Caddy reverse proxy for public endpoint

## Current Focus
- Operational. 40 tools live. GENESIS/000-003 canon chain established.
- GENESIS/003 floor numbering needs realignment to F1-F13 (see FEDERATION_STATUS.md)

## Known Issues
- GENESIS/003 uses old F01-F09 floor numbering — needs F13 realignment
- No CONTEXT.md or RUNBOOK.md until now (2026-06-12)
