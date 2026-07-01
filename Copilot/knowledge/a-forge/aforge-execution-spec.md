# A-FORGE — Execution Layer
> arifOS Federation | Repo: `ariffazil/A-FORGE` | 2026-06-10
> Authority ceiling: 777_FORGE | Stack: TypeScript ES2022, ESM, Zod, MCP SDK

---

## What A-FORGE is

A-FORGE is the **execution layer** of the arifOS federation. It builds, deploys, and orchestrates agents and artifacts. It does not compute domain science — it dispatches work to the right organ and manages the execution lifecycle.

Authority ceiling: **777_FORGE**. Anything requiring 888_JUDGE or 999_SEAL must escalate to arifOS. This is enforced, not a suggestion.

---

## Core responsibilities

| Responsibility | Description |
|----------------|-------------|
| Agent orchestration | Coordinator/Worker pattern — spawns, directs, collects results |
| Tool dispatch | Permission-gated `ToolRegistry` — no tool fires without AF1 validation |
| Build/deploy | `npm run build`, `make up`, Docker artifact lifecycle |
| Budget tracking | Per-run cost and token budget enforcement |
| Run metrics | `ForgeScoreboard`, `RunMetricsLogger` — every run is measured |
| Memory | Short-term session + file-backed long-term memory |
| MCP server | Exposes agent capabilities via `npm run mcp:stdio` or `npm run mcp:http` |

---

## AF1 Pre-Execution Protocol

Every tool call from A-FORGE agents requires an **AF1 validation object** before execution.

```
AF1 = {
  intent: string,          // what the tool is being asked to do
  authority_tier: 0|1|2|3, // required authority level
  reversible: bool,        // can this be undone?
  blast_radius: string,    // what could go wrong
  arif_approval: bool      // required for Tier 2+
}
```

**No AF1 → no execution. Fail closed. This is absolute.**

---

## Hard routing boundaries

A-FORGE MUST NEVER:
- Compute geoscience (Vsh, PHIE, Sw, Archie equations) → **route to geox**
- Run economic evaluation (NPV, IRR, EMV) → **route to wealth**
- Issue SEAL / VOID / HOLD → **escalate to arifOS**
- Hold `SERVICE_ROLE_KEY` or privileged DB credentials

**Signal that code is in the wrong layer:** if A-FORGE code imports `numpy`, `pandas`, `scipy`, or domain physics → boundary violation.

---

## Key source paths

| Path | Purpose |
|------|---------|
| `src/engine/AgentEngine.ts` | Core agent loop (LLM → tools → budget → repeat) |
| `src/tools/ToolRegistry.ts` | Permission-gated tool registry |
| `src/agents/` | Coordinator/Worker orchestration + profile builders |
| `src/memory/` | Session + long-term memory |
| `src/scoreboard/` | Run metrics (`ForgeScoreboard`, `RunMetricsLogger`) |
| `src/mcp/` | MCP server surface |
| `af1/SYSTEM_PROMPT_AF1.md` | AF1 protocol definition |

---

## Trust flag

`AGENT_WORKBENCH_TRUST_LOCAL_VPS=1` is a **root-key-equivalent flag**. It disables shell filtering, enables dangerous/background/experimental tools, and forces `internal_mode`.

**Treat this flag as if it is the master key to the building. Do not set it without explicit Arif approval.**

---

## Copilot routing rules

**Route to A-FORGE when:**
- An agent needs to be built, deployed, or orchestrated
- A tool needs to be registered or dispatched
- Build artifacts need to be created or published
- Run metrics or budget needs to be tracked

**GEOX Copilot output when A-FORGE context applies:**

```
FORGE_BOUNDARY: This execution request is an A-FORGE responsibility.
Authority required: [tier]
AF1 required: [yes/no]
Arif approval required: [yes/no — Tier 2+]
```

---

## What A-FORGE is NOT

- Not a domain computation engine (no physics, no geoscience, no finance)
- Not an identity layer (→ AAA)
- Not a governance kernel (→ arifOS)
- Not a vitality monitor (→ well)

A-FORGE is pure execution infrastructure. If it starts reasoning about geology or capital → wrong layer.
