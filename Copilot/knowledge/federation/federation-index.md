# arifOS Federation Index — 7-Repo Map
> Canonical reference for GEOX Copilot | Sovereign: Arif | 2026-06-10
> Authority model: Tier 0 (read) → Tier 3 (atomic) | Ceiling for agents: 777_FORGE

---

## Federation overview

The arifOS Federation is NOT a monolith. It is 7 sovereign repos, each with a hard role boundary.
A question routed to the wrong organ is a governance failure, not a capability gap.

```
arifOS ─── Law Kernel (governance, routing, judgment)
  │
  ├── AAA ──────── Identity (A2A mesh, session, AUTH)
  ├── A-FORGE ──── Execution (build, deploy, orchestration)
  ├── geox ─────── Earth (geoscience, petrophysics, physics-9)
  ├── wealth ───── Capital (NPV, IRR, EMV, risk, allocation)
  ├── well ─────── Vitality (human readiness, machine substrate)
  └── ariffazil ── Sovereign root (Arif's identity anchor, cross-repo integration)
```

---

## Repo 1 — arifOS (Law Kernel)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/arifOS` |
| Stack | Python 3.11+, FastMCP, FastAPI, Pydantic v2 |
| MCP port | 8080 |
| Authority | 999_SEAL (highest — issues verdicts) |
| Tools | 13 canonical MCP tools (`arif_noun_verb` naming) |
| Entry | `python server.py` or `docker compose up -d` |

**What it does:** Governance engine. Routes requests across federation. Issues SEAL / VOID / HOLD / SABAR verdicts. Enforces 13 constitutional floors (F1–F13).

**What it does NOT do:** Compute geoscience, evaluate capital, execute builds, hold credentials.

**Route to arifOS when:** A verdict is needed. A cross-repo decision must be adjudicated. Constitutional floor violation is detected. 888_HOLD is triggered.

**Copilot files:** `system-prompts/01-arifo-kernel.md`, `system-prompts/02-arifo-constitutional.md`, `knowledge/federation/AGENTS.md`

---

## Repo 2 — AAA (Identity Control Plane)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/AAA` |
| Stack | Python |
| Role | A2A mesh, session anchoring, identity binding |
| Floor | F11 AUTH (mandatory), F12 INJECTION DEFENSE |
| Authority | Tier 1 (identity operations) |

**What it does:** Identity verification. Agent-to-agent authentication. Session token anchoring. Nonce-bound command authorisation.

**What it does NOT do:** Compute anything. Evaluate capital. Issue governance verdicts.

**Route to AAA when:** A session must be established. An agent identity must be verified. Sensitive op needs AUTH clearance. F11 violation detected.

**Copilot file:** `knowledge/aaa/aaa-identity-spec.md`

---

## Repo 3 — A-FORGE (Execution Layer)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/A-FORGE` |
| Stack | TypeScript ES2022, ESM, Zod, MCP SDK |
| MCP mode | `npm run mcp:stdio` or `npm run mcp:http` |
| Authority ceiling | 777_FORGE |
| Protocol | AF1 pre-execution validation (every tool call) |

**What it does:** Agent orchestration. Build and deploy artifacts. Tool dispatch. Budget tracking. Run metrics.

**What it does NOT do:**
- Compute geoscience (Vsh, PHIE, Sw, Archie) → route to **geox**
- Evaluate capital (NPV, IRR, EMV) → route to **wealth**
- Issue SEAL / VOID / HOLD → escalate to **arifOS**
- Hold `SERVICE_ROLE_KEY` or privileged DB credentials

**If A-FORGE code imports numpy, pandas, scipy, or domain physics → wrong layer.**

**Copilot file:** `knowledge/a-forge/aforge-execution-spec.md`

---

## Repo 4 — geox (Earth / Geoscience)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/geox` |
| Stack | Python 3.11+, FastMCP, Pydantic v2, asyncio |
| MCP port | 8081 |
| Tools | 37 canonical MCP tools |
| Physics | Physics9 epistemic tiers, ACRisk, 13 floors |

**What it does:** Geoscience computation. Petrophysics. Seismic interpretation. Prospect evaluation. Evidence witnessing. Governed JSON envelopes for agents.

**Canonical output envelope:** `{execution_status, claim_state, observed, derived, interpreted, cross_modal_stability, dim_spot_flag, ...}`

**What it does NOT do:**
- Interpret geological meaning (human or arifOS reasoning layer)
- Issue constitutional verdicts
- Hold privileged credentials
- Compute economic evaluation (→ wealth)
- Run basin / PSM models (maturation, expulsion, pressure history)

**When ACRisk > 0.60 or contradiction detected → automatic 888_HOLD. Not negotiable.**

**Copilot files:** `knowledge/geox/geox-spec.md`, `knowledge/geox/geox-arifo-spec.md`

---

## Repo 5 — wealth (Capital Organ)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/wealth` |
| Stack | Python |
| Domain | Capital flow, risk, allocation, economic evaluation |
| Authority | Tier 2 — explicit Arif approval for capital moves |

**What it does:** NPV, IRR, EMV. Capital risk modelling. Portfolio allocation. Economic scenario evaluation.

**What it does NOT do:** Compute geoscience. Issue governance verdicts. Make capital allocation decisions autonomously.

**Hard rule: WEALTH is NOT an unchecked allocator.** All capital commitment decisions require Arif explicit authorisation. No exceptions.

**Copilot file:** `knowledge/wealth/wealth-mcp-summary.md`

---

## Repo 6 — well (Vitality Substrate)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/well` |
| Stack | Python |
| Domain | Human readiness + machine substrate coupling |
| Floors | PEACE (F5), EMPATHY (F6), MARUAH (F9) |

**What it does:** Human readiness monitoring. Machine substrate health. Coupled-state assessment. Vitality metrics.

**What it does NOT do:** Adjudicate anything. Compute geoscience or capital. Override sovereignty.

**Copilot file:** `knowledge/well/well-vitality-spec.md`

---

## Repo 7 — ariffazil (Sovereign Root)

| Field | Value |
|-------|-------|
| GitHub | `ariffazil/ariffazil` |
| Role | Arif's identity anchor + cross-repo integration surface |
| Authority | 999_SEAL (sovereign) |

**What it is:** The root identity of the entire federation. Cross-repo integration surface. Arif's sovereign anchor. Not a computation layer — a governance and identity root.

**Rule:** Arif's word is final (F13 SOVEREIGN). Human veto is absolute.

---

## Routing quick-reference

| Question type | Route to |
|---------------|----------|
| "Is this geologically valid?" | geox |
| "What is the NPV / IRR?" | wealth |
| "Who is authorised to run this?" | AAA |
| "Execute this build / deploy" | A-FORGE |
| "Is this person/agent ready?" | well |
| "Seal / void this decision" | arifOS |
| "Final call — yes or no" | Arif (F13 SOVEREIGN) |

---

## What GEOX Copilot does when routing fails

If a question cannot be routed to a clear organ → output:
```
SCOPE_BOUNDARY: This question crosses into [organ name].
GEOX computes. MCP exposes. arifOS judges. Arif decides.
I cannot answer this without [what is needed].
```

Never silently truncate. Never fill scope gaps with assumptions.
