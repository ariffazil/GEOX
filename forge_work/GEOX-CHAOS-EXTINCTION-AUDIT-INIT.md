# GEOX-CHAOS-EXTINCTION-AUDIT — Session Init

> **Purpose:** Audit ALL GEOX tools, resources, and prompts against MCP protocol spec.
> **Goal:** Clarity, no duplication, clean surface. Extinction of chaos.
> **MCP Spec:** https://modelcontextprotocol.io/specification/2025-11-25/
> **Actor:** FORGE (000Ω) on behalf of Arif (F13 SOVEREIGN)
> **Date:** 2026-07-03

---

## 0. Current State (OBS)

| Surface | Count | Notes |
|---------|-------|-------|
| Canonical tools (registry) | 46 | 42 surface + 4 internal |
| `@mcp.tool` in server.py | 64 | 18 non-canonical (legacy/compat) |
| Resources | ~25+ | `geox://` URI scheme, registered via `register_resources()` |
| Prompts | ? | Registered via `register_prompts()` |
| Backward-compat aliases | 49 | Scheduled removal 2026-07-30 |

## 1. MCP Protocol Requirements (from spec)

### Tools MUST have:
- `name` — unique, 1-128 chars, `[A-Za-z0-9_.-]`, no spaces
- `description` — human-readable
- `inputSchema` — valid JSON Schema object (NOT null)
- `outputSchema` — optional but recommended
- `annotations` — optional (readOnlyHint, destructiveHint, idempotentHint, openWorldHint)
- `execution.taskSupport` — optional (forbidden/optional/required)

### Resources MUST have:
- `uri` — unique identifier
- `name` — human-readable
- `description` — optional
- `mimeType` — optional
- `annotations` — optional (audience, priority, lastModified)

### Prompts MUST have:
- `name` — unique identifier
- `description` — optional
- `arguments[]` — optional, each with name/description/required
- Messages with role + content

## 2. Audit Checklist

### 2A. Tools Audit (46 canonical + 18 legacy)

| Check | What to Verify | Fix |
|-------|---------------|-----|
| T1 | Every tool has `description` ≥ 10 chars | Add/update description |
| T2 | Every tool has valid `inputSchema` (not null) | Add JSON Schema |
| T3 | No tool name has spaces or special chars | Rename if needed |
| T4 | No duplicate tool names | Remove duplicates |
| T5 | `outputSchema` present for compute tools | Add for physics engines |
| T6 | `annotations` present (readOnlyHint etc.) | Add for each tool |
| T7 | Legacy aliases properly marked deprecated | Add deprecation notice |
| T8 | Tool descriptions are actionable (what it does, not what it is) | Rewrite vague descriptions |
| T9 | Input schemas have `description` for each parameter | Add param descriptions |
| T10 | Required fields correctly marked | Verify `required` array |

### 2B. Resources Audit (~25+ resources)

| Check | What to Verify | Fix |
|-------|---------------|-----|
| R1 | Every resource has `name` | Add name |
| R2 | Every resource has `description` | Add description |
| R3 | `mimeType` set correctly | Fix MIME types |
| R4 | `annotations.audience` set (user/assistant/both) | Add audience |
| R5 | `annotations.priority` set (0.0-1.0) | Add priority |
| R6 | No duplicate URIs | Remove duplicates |
| R7 | URI scheme consistent (`geox://`) | Standardize |
| R8 | Resource templates use proper URI templates (RFC 6570) | Fix templates |

### 2C. Prompts Audit

| Check | What to Verify | Fix |
|-------|---------------|-----|
| P1 | Every prompt has `name` | Add name |
| P2 | Every prompt has `description` | Add description |
| P3 | Arguments have descriptions | Add descriptions |
| P4 | Required arguments marked correctly | Fix required flags |
| P5 | Messages have valid role + content | Fix message format |

### 2D. Chaos Audit (duplication + entropy)

| Check | What to Verify | Fix |
|-------|---------------|-----|
| C1 | No tool does the same thing as another | Merge/remove duplicates |
| C2 | No resource duplicates tool output | Remove redundant resources |
| C3 | No prompt duplicates tool description | Remove redundant prompts |
| C4 | Legacy aliases don't shadow canonical tools | Fix routing |
| C5 | Tool descriptions don't overlap | Clarify boundaries |
| C6 | Resource names don't conflict with tool names | Namespace properly |

## 3. Execution Plan

### Phase 1: Inventory (read-only)
1. List all 64 `@mcp.tool` registrations — name, description, inputSchema
2. List all resources — URI, name, description, mimeType
3. List all prompts — name, description, arguments
4. Compare canonical registry (46) vs actual registrations (64)

### Phase 2: Gap Analysis
1. Which tools missing `description`?
2. Which tools missing `inputSchema`?
3. Which tools missing `outputSchema`?
4. Which resources missing `name`/`description`?
5. Which items are duplicates?

### Phase 3: Fix
1. Update tool descriptions to be actionable
2. Add `inputSchema` where missing
3. Add `outputSchema` for compute tools
4. Add `annotations` (readOnlyHint, etc.)
5. Clean up resource descriptions
6. Remove true duplicates
7. Mark legacy aliases as deprecated

### Phase 4: Verify
1. Run MCP Inspector against GEOX server
2. Verify `tools/list` returns clean surface
3. Verify `resources/list` returns clean surface
4. Verify `prompts/list` returns clean surface
5. Test each tool's `inputSchema` with valid/invalid inputs

## 4. Success Criteria

| Metric | Target |
|--------|--------|
| Tools with `description` ≥ 10 chars | 100% |
| Tools with valid `inputSchema` | 100% |
| Tools with `outputSchema` | ≥ 80% (compute tools) |
| Resources with `name` + `description` | 100% |
| Duplicate tools | 0 |
| Duplicate resources | 0 |
| Legacy aliases marked deprecated | 100% |

## 5. Files to Audit

| File | What's In It |
|------|-------------|
| `src/geox_mcp/server.py` | 64 `@mcp.tool` registrations |
| `src/geox_mcp/registry.py` | 46 canonical tool names |
| `src/geox_mcp/resources/__init__.py` | ~25+ resources |
| `src/geox_mcp/prompts/` | Prompt registrations |
| `src/geox_mcp/tools_manifest.py` | Tool manifest |
| `src/geox_mcp/tool_discovery.py` | Tool discovery metadata |
| `src/geox_mcp/organ_governance.py` | Risk tiers, governance |
| `contracts/schemas/output_schemas.py` | Output schemas |

---

*DITEMPA BUKAN DIBERI — Chaos extinction begins.*
