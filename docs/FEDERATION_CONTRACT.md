<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-12
valid_from: 2026-07-12
valid_until: 2026-08-12
confidence: high
scope: organ-local pointer
-->

# Federation Contract — Pointer (Consolidation Phase 888)

**Canonical source:** `/root/arifOS/FEDERATION_CONTRACT.md`  
**GitHub:** `ariffazil/arifos` · ratified 2026-07-12 (§5.5 + §13)

This organ-local file is a **thin bootstrap** after doctrine deduplication (Batch medium, agentic 2026-07-12).

- Do **not** maintain a parallel full contract here.
- Link upward. Import / reference / generate from arifOS.
- Organ-specific authority still lives in this repo's `AGENTS.md` + domain canon.

**Rollback:** git history of this path prior to commit `docs(doctrine): pointer to arifOS FEDERATION_CONTRACT`.

---

## Two-Entry-Point Doctrine (GEOX-Specific, Forged 2026-07-16)

GEOX has two MCP entry points. Both are valid. They serve different authority models.

### Entry Points

| Endpoint | Server Identity | Authority Model | Use Case |
|----------|----------------|-----------------|----------|
| `mcp.arif-fazil.com/mcp` | arifOS kernel | Governance-first (envelope-wrapped) | Judgment tools, session binding, seal |
| `geox.arif-fazil.com/mcp` | GEOX organ | Lane-gated (direct) | Discovery, evidence, reasoning |

### Routing Rules

| Lane | Kernel Path | Direct Path |
|------|------------|-------------|
| **discovery** | MAY | MAY (preferred) |
| **evidence** | MAY | MAY (preferred) |
| **reasoning** | SHOULD | MAY with `session_id` |
| **judgment** | **MUST** | **BLOCKED** (lane enforcement) |

### Why Two Paths

The kernel is the governance door. Direct organ access exists for read-only operations that don't need governance envelopes. Judgment-lane tools (seal, publish) MUST route through the kernel — this is enforced by `organ_governance.py` lane enforcement, not by routing.

### MCP Spec Alignment (2026-07-16)

Per MCP spec: "Servers should be highly composable — each server provides focused functionality in isolation." Both endpoints are MCP-conformant servers. The kernel is a compositional server (server that is also a client of other servers). This is explicitly permitted by the spec.

### Spec Migration Note (Draft Spec)

SEP-2575 (stateless) + SEP-2567 (sessionless) are Final. When the draft spec ships:
- `session_id` → `authority_handle` as tool argument (not HTTP header)
- `initialize`/`initialized` removed — lifecycle gate becomes obsolete
- `888_HOLD` → `InputRequiredResult` (MRTR pattern)
- This doctrine remains valid — the entry points don't change, only the wire format.

*DITEMPA BUKAN DIBERI — one contract, many organs.*

