# FEDERATION_NOTES.md — GEOX Integration State

> Domain-specific integration notes for GEOX.
> Source: AAA/agents/hermes/MEMORY.md — canonical home is AAA.

## GEOX MCP Status (2026-05-05)
- Server: geox_eic container
- Port: 8081 (streamable-http), 8000
- Transport: streamable-http ✅ (not SSE — compatible)
- Tools: 31 (verified by grep count)
- Public domain: geox.arif-fazil.com

## Verified Integration Gap

### GEOX Bridge is SIMULATED
**File:** `/root/arifOS/arifosmcp/apps/geox_bridge.py`
**Lines:** 73, 77, 98

```
# TODO: Replace with actual MCP call to GEOX when client is fully wired
geox_result = {
    ...
    "message": "GEOX integration pending full MCP client wiring",
}
```

**Impact:** arifOS cannot currently call live GEOX MCP tools. Bridge returns hardcoded fake data.
**Fix required:** Wire actual MCP client (sse_client from @modelcontextprotocol/sdk) to geox_eic:8081

## What Works
- GEOX MCP server is healthy and serving at geox.arif-fazil.com/mcp
- 31 tools registered and returning real data when called directly
- Caddy routing to geox_eic:8081 is correct

## What Needs Wiring
- arifOS → GEOX bridge: replace SIMULATED return with live MCP client call
- arifOS needs MCP SSE client to call GEOX (GEOX uses streamable-http, not SSE-only)
- Auth: GEOX_SECRET_TOKEN deferred until external scale

## Active Hold
- GEOX-BRIDGE-001: geox bridge still simulated; live MCP wiring pending

## Routing
- Canonical home for full state: `AAA/agents/hermes/MEMORY.md`
- arifOS constitutional references: `arifOS/docs/canon/HERMES_AGENT_CANON.md`

Last updated: 2026-05-05
