# PROTOCOL_CONFORMANCE.md — GEOX Earth Intelligence

> Layer: L3 · Role: Earth/geoscience intelligence — evidence, not decisions · Repo: ariffazil/GEOX

## MCP Conformance
| Requirement | Status | Evidence |
|------------|--------|----------|
| llms.txt | ✅ | `/root/GEOX/llms.txt` — 15 public tools declared, canonical tool surface from `tools_manifest.yaml` |
| tools/list | ✅ | `:8081` — 24 tools loaded, 24 canonical (geox_basin, geox_petrophysics, geox_seismic_compute, geox_seismic_ingest, geox_seismic_interpret, geox_well_ingest, geox_well_desk, geox_claim, geox_deep_time_state, geox_geomechanics, geox_gravmag_studio, geox_prospect, geox_sequence, geox_subsurface_model, geox_surface_status, geox_thermal_maturity_history, geox_evidence, geox_falsify, geox_contradiction_scan, geox_claim_graph_evaluate, geox_lem_predict, geox_sediment_mass_balance, geox_to_wealth_bridge, geox_basin_backstrip) |
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
| OpenAPI | ✅ | `/.well-known/openapi.json` |
| Tool manifest | ✅ | `/.well-known/tools.json` |

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
| llms.txt tool count mismatch | P1 | llms.txt declares 15 tools but live surface has 24. llms.txt should be regenerated from live `tools/list` |

## Required Compliance
- L3 Protocol: MCP (mandatory) + FastMCP (mandatory for Python organs) + A2A (agent card mandatory)
- GEOX is evidence-only — computes, never adjudicates
- 24 operational tools, zero drift between loaded and canonical
- Physics9 doctrine: physics before narrative
- Next milestone: Regenerate llms.txt to match live 24-tool surface (P1)

---
Generated: 2026-07-19 · Authority: AAA Control Plane
DITEMPA BUKAN DIBERI
