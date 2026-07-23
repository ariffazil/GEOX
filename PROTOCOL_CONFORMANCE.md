# PROTOCOL_CONFORMANCE.md — GEOX Earth Intelligence

> Layer: L3 · Role: Earth/geoscience intelligence — evidence, not decisions · Repo: ariffazil/GEOX

## MCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| llms.txt | ✅ | `/root/GEOX/llms.txt` — generated from `tools_manifest.yaml` via `scripts/generate_all_surfaces.py` |
| tools/list | ✅ | `:8081` — live count from `geox_surface_status(mode="registry")` or `curl :8081/health` |
| health endpoint | ✅ | `:8081/health` — returns status, service (geox-unified), tools_loaded, canonical_tools, federation_schema_version, git_version |
| Surface audit | ✅ | `CANONICAL_PUBLIC_SURFACE.json` and `tools_sot.yaml` — live registry vs manifest |

## FastMCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| FastMCP server | ✅ | Python 3.12 FastMCP runtime on port 8081 |
| Resource discovery | ✅ | MCP resources available — evidence pipeline, basin profiles, deep time state |

## A2A Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| Agent card | ✅ | `/.well-known/agent-card.json` — full schema with tool_surface, resource_surface, skills |
| Task schema | ⚠️ | Supports A2A task operations via federation routing (AAA gateway) |
| Streaming | ❌ | No SSE streaming support |
| MCP server discovery | ✅ | `/.well-known/mcp/server.json` and `/.well-known/agent.json` |
| OpenAPI | ✅ | `/.well-known/openapi.json` — generated from `tools_manifest.yaml` |
| Tool manifest | ✅ | `/.well-known/tools.json` — generated from `tools_manifest.yaml` |

## XMCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| App schema | ❌ | No webmcp.json — GEOX is a domain intelligence organ, not an app host |
| Resource schema | ✅ | MCP resources via FastMCP — basin profiles, seismic volumes, well data |
| Federation manifest | ✅ | Federation contract and organ.yaml at root |

## Gaps
| Gap | Priority | Detail |
|-----|----------|--------|
| A2A Streaming | P2 | No SSE; acceptable for L3 domain organ. Most GEOX computations are synchronous |
| XMCP App schema | P3 | Not applicable — GEOX serves evidence, not apps |

## Required Compliance
- L3 Protocol: MCP (mandatory) + FastMCP (mandatory for Python organs) + A2A (agent card mandatory)
- GEOX is evidence-only — computes, never adjudicates
- All derived surfaces generated via `python scripts/generate_all_surfaces.py`
- Tool counts are a runtime fact — see `geox_surface_status(mode="registry")` or `curl :8081/health`
- Physics9 doctrine: physics before narrative

---
Generated: 2026-07-23 · Authority: AAA Control Plane
DITEMPA BUKAN DIBERI
