# 🌍 GEOX — Protocol Conformance

> **Layer:** L3 DOMAIN · **Role:** Earth Intelligence Organ
> **Protocols:** MCP Server, FastMCP 3.4.2, JSON-RPC 2.0, SSE, Streamable HTTP, SEP-2127, Well-Known, XMCP Apps

## Supported Protocols

| Protocol | Status | Detail |
|----------|--------|--------|
| MCP Server | ✅ CONFORMANT | 24 public tools, 100% envelope compliance |
| FastMCP 3.4.2 | ✅ CONFORMANT | 139 compat wrappers removed, 0 **kwargs on surface |
| JSON-RPC 2.0 | ✅ CONFORMANT | All endpoints respond to JSON-RPC |
| SSE | ✅ CONFORMANT | Legacy SSE at /sse, backwards compat |
| Streamable HTTP | ✅ CONFORMANT | POST /mcp with sessions |
| SEP-2127 | ✅ CONFORMANT | Rich server card at /.well-known/mcp/server.json |
| Well-Known | ✅ CONFORMANT | 2.4KB server.json with tools, apps, governance |
| XMCP Apps | ✅ CONFORMANT | 9 ui:// MCP Apps registered |
| DID:WEB | ❌ GAP | No did:web document published |

## MCP Tool Surface
- **Public:** 24 canonical tools (0 phantoms, 0 manifest-only)
- **Internal:** 34 internal tools
- **MCP Apps:** 9 (Well Witness, Prospect Forge, Seismic Viewer, etc.)
- **Registry:** PASS (0 drift since 2026-07-19 fix)

## Gaps
1. **DID:WEB:** No decentralized identity document for organ verification

*DITEMPA BUKAN DIBERI*
