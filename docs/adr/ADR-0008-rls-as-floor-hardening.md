# ADR-0008: RLS-as-Floor Hardening for arifOS Agentic Substrate

**Status:** DRAFT (awaiting 888_HOLD)
**Date:** 2026-06-24
**Sovereign:** arif (F13)
**Forge session:** FORGE-000Ω (database & memory substrate deep-research, 2026-06-24)
**Supersedes:** none
**Related:** ADR-0007 (OSDU exchange), `arifOS/GENESIS/000_CONSTITUTION.md`, §7.9 Memory Architecture (`arifOS/AGENTS.md`)

---

## Context

On 2026-06-24, deep research into "agentic intelligence databases" (vs CRUD, vs RAG/DAG/vector) confirmed an intuition the sovereign has held for some time: **the architecture of databases is not designed for agents**. The 13 constitutional floors (F1-F13) are currently enforced at the application layer (Python checks in `arifosmcp/core/enforcement/`, JSON-schema validators in `arifosmcp/runtime/`). This is best-effort.

**The vulnerability:** A prompt-injected agent, a compromised MCP server, a rogue Python script with `SUPABASE_SERVICE_ROLE_KEY`, or a misconfigured Edge Function can bypass application-layer enforcement. There is **no mechanical refusal** at the substrate layer.

**The substrate we already have (verified 2026-06-24 via Supabase introspection):**

| Capability | Where | Status |
|---|---|---|
| Hash-chained append-only ledger | `vault_seals` (prev_seal_id, chain_hash, signature) | LIVE, 270 rows |
| 5-type memory taxonomy | `arifosmcp_memory_records.type` CHECK | LIVE |
| Epistemic confidence bound | `arifosmcp_memory_records.confidence` CHECK (0.0-1.0) | LIVE |
| Vector recall + chain | `embedding vector(1024)` HNSW + pgcrypto | LIVE |
| Supersession chain | `supersedes` / `superseded_by` FK | LIVE |
| Constitutional audit trail | `arifosmcp_memory_audit_log.floor_violations` jsonb | LIVE |
| Policy engine | `arifosmcp_memory_policy.policy_class` + `rule` jsonb | LIVE (table-level only) |
| Kernel self-monitoring | `arifosmcp_kernel_state.kernel_status` (ALIVE/DEGRADED/HALTED) | LIVE |
| Vault999 3-layer architecture | local JSONL + Postgres + Supabase | LIVE |

**The gap:** RLS policies for the constitutional substrate are partial. Only `service_role_full_access` and `authenticated_read` exist on most tables. There is **no F1-F13 floor enforcement at the DB layer**. The substrate has the structure but not the policy.

**Industry confirmation (OBS, 2025-2026 surveys):** Of 12 agentic memory frameworks surveyed (MemGPT/Letta, Mem0, Zep/Graphiti, LangGraph, CrewAI, Cognee, LlamaIndex, Semantic Kernel, AutoGen, Haystack, OpenAI Assistants, Hindsight):
- **Zero** provide cryptographic event attestation
- **Zero** enforce constitutional floors at write time
- **One** (Hindsight) provides epistemic confidence tracking
- **All** can be coerced into storing anything
- **None** mechanically refuses forbidden writes

**The opportunity:** Postgres + Supabase give us **the load-bearing primitive for constitutional AI**: **Row Level Security (RLS) policies evaluated at write time**, called with session-scoped GUCs (`SET LOCAL app.organ = 'arifos'`). A policy like:

```sql
CREATE POLICY f11_audit_required ON arifosmcp_memory_records
FOR INSERT TO authenticated
WITH CHECK (
  current_setting('app.actor_id', true) IS NOT NULL
  AND current_setting('app.session_id', true) IS NOT NULL
  AND current_setting('app.floor_signature', true) IS NOT NULL
  AND (current_setting('app.blast_radius', true) IN ('LOW','MEDIUM')
       OR current_setting('app.sovereign_approval', true) = 'true')
);
```

…means: **no application-layer bypass is possible**. A rogue Python script or a prompt-injected agent cannot write a HIGH-blast-radius memory record without sovereign approval — the substrate refuses mechanically.

This is the closest thing to "constitutional substrate" in any production system, June 2026. We can be first.

---

## Decision

**Implement F1-F13 floors as Postgres Row Level Security (RLS) policies on `arifosmcp_memory_records`, `arifosmcp_memory_audit_log`, `arifosmcp_vault_seals`, `arifosmcp_kernel_state`, and `arifosmcp_canon_records`.** Mechanical refusal at the substrate. No application-layer bypass.

### The 13 Floors as DB Constraints

Each floor becomes one or more RLS policies or CHECK constraints. Below is the mapping (initial draft; specific clauses refined in migration):

| Floor | Name | DB-layer enforcement |
|---|---|---|
| **F1** | AMANAH | RLS: actor + session + signature required on every write; CHECK: every record has `supersession_chain` link or `vault_seal` provenance |
| **F2** | TRUTH | CHECK: epistemic_ladder values restricted to {OBS, DER, INT, SPEC, EARTHMODEL, DECISION, HUMAN_JUDGMENT}; CHECK: confidence in [0.0, 1.0] (already exists) |
| **F3** | TRI-WITNESS | RLS: HIGH-blast-radius records require 3 distinct witness signatures in payload |
| **F4** | CLARITY | Application-layer (no DB equivalent); CHECK: payload size < 1MB; CHECK: no `legacy_` prefix |
| **F5** | (continuity) | RLS: superseded records cannot be UPDATEd directly (only by supersession events) |
| **F6** | MARUAH | CHECK: privacy restricted to {public, personal, sensitive, confidential} (already exists) |
| **F7** | HUMILITY | CHECK: confidence <= 0.90 unless explicitly overridden by `humility_override=true` setting + actor_signature |
| **F8** | LAW | RLS: tool_count_canonical cannot regress without F13 override |
| **F9** | ANTI-HANTU | CHECK: actor_id cannot be NULL; CHECK: actor_role in {'human','arifos_kernel','organ_substrate','external_proxy'} (no 'conscious_entity' or similar) |
| **F10** | (ontological) | CHECK: type restricted to {working, episodic, semantic, procedural, governance} (already exists) |
| **F11** | AUDIT | TRIGGER: every INSERT/UPDATE on `vault_seals` and `arifosmcp_memory_records` writes a row to `arifosmcp_memory_audit_log` |
| **F12** | (cooling) | CHECK: cooling_id set when verdict='COOLING'; RLS: COOLING records are read-only |
| **F13** | SOVEREIGN | RLS: any mutation with `blast_radius='HIGH'` or `blast_radius='CRITICAL'` requires `sovereign_approval=true` session GUC |

### Migration Plan (5 phases, each 888_HOLD-gated)

**Phase P1 — Schema verification + audit (NO writes, NO mutations).**
- Inventory all current RLS policies on `public.*` tables.
- Identify tables with `service_role_full_access` only (no F1-F13 enforcement).
- Document current behavior under simulated policy injection.
- **Deliverable:** audit report at `/root/forge_work/2026-06-24-rls-hardening/001-audit.md`.
- **888_HOLD:** NO (read-only audit).

**Phase P2 — Pilot policies on `arifosmcp_memory_records` (test write surface).**
- Add RLS policies for F1, F2, F7, F9, F11, F13 (the load-bearing six).
- Add CHECK constraints for F5, F12.
- Add TRIGGER for F11 audit trail enforcement.
- Wrap all writes through new SECURITY DEFINER function `arifos_memory_write(payload jsonb)` that sets session GUCs and writes atomically.
- All existing application writes migrated to call this function.
- **Deliverable:** migration SQL at `/root/forge_work/2026-06-24-rls-hardening/002-pilot-policies.sql`; test suite at `tests/03_constitutional/test_rls_floors.py`.
- **888_HOLD:** YES (touches production table + service writes).

**Phase P3 — Extend to `arifosmcp_vault_seals` + `arifosmcp_kernel_state`.**
- Add RLS policies for seal-chain integrity (F1, F11).
- Add CHECK constraints on `vault_seals.floors_triggered` (must be subset of canonical F1-F13).
- Add RLS on `kernel_state` (only `arifos_kernel` role can write; authenticated can read).
- **Deliverable:** migration SQL + tests.
- **888_HOLD:** YES.

**Phase P4 — Extend to organ-specific tables.**
- Apply same pattern to `arifosmcp_well_states`, `arifosmcp_portfolio_snapshots`, `arifosmcp_transactions`, `wealth_transactions`, etc. (every organ's state table).
- Coordinate with WEALTH, WELL, GEOX MCP server maintainers.
- **Deliverable:** per-organ migration SQL + tests.
- **888_HOLD:** YES, per organ.

**Phase P5 — Audit + skill publication.**
- Publish skill file at `~/.agents/skills/arifos-rls-floors/SKILL.md` with the canonical policy set.
- Update `arifOS/AGENTS.md` §9 to reflect DB-layer floor enforcement.
- Update `geox-constitution`, `geox-claim-grammar`, `geox-epistemic-ladder` skills to reference RLS-backed floors.
- **Deliverable:** skill files + AGENTS.md updates.
- **888_HOLD:** YES (canonical skill publication).

### Hard Rules (binding)

1. **No application-layer bypass possible.** Every write path goes through SECURITY DEFINER functions that set session GUCs. Application code cannot directly INSERT/UPDATE/DELETE on protected tables.

2. **No `BYPASSRLS` granted to non-sovereign roles.** The `service_role` retains `BYPASSRLS` for emergency operations only; this is logged in `arifosmcp_memory_audit_log` via event trigger.

3. **No silent policy changes.** Every CREATE/DROP POLICY fires an event trigger that writes to `arifosmcp_kernel_state.declared_tools` and `arifosmcp_canon_records`. Policy drift is visible.

4. **Phase rollback requires F13.** If a phase breaks production writes, rollback is permitted but flagged for sovereign review. No silent rollback.

5. **The substrate remains the load-bearing primitive.** Application-layer checks continue as defense-in-depth. RLS is the last line, not the only line.

### Estimated Cost (DER, 0.70 confidence)

| Phase | Effort | Skill |
|---|---|---|
| P1 — Audit | 8 hours | Read-only schema inspection + report |
| P2 — Pilot | 40 hours | RLS + CHECK + TRIGGER + tests + migration coordination |
| P3 — Vault + Kernel | 30 hours | RLS + tests |
| P4 — Organ rollout | 40 hours | Per-organ coordination, migrations, tests |
| P5 — Skill publication | 12 hours | Skill file, AGENTS.md updates, federation notification |
| **TOTAL** | **~130 hours** | **≈1 engineer-quarter** |

---

## Alternatives Considered

### A1. Continue application-layer only (REJECTED, 0.95 confidence)

Status quo. F1-F13 enforced in Python checks in `arifosmcp/core/enforcement/`. Bypass possible via prompt injection, rogue scripts, compromised MCP servers. **Rejected.**

### A2. Build a custom Postgres extension in Rust (`pg_arifos`) with floor logic (DEFERRED)

Use pgrx to compile floor enforcement into Postgres as a `.so`. Pros: faster, harder to bypass. Cons: requires Rust + Postgres internals expertise, harder to maintain, harder to audit. **Deferred — revisit if performance becomes an issue.**

### A3. Use Temporal.io for floor enforcement (REJECTED for this purpose, 0.85 confidence)

Temporal's durable execution is excellent for workflow guarantees but not designed for per-row policy. Wrong primitive. Temporal may still be adopted for 888_JUDGE deliberation loops (separate ADR). **Rejected for RLS hardening.**

### A4. (CHOSEN) RLS + CHECK + TRIGGER + SECURITY DEFINER functions in standard Postgres.

Best leverage/cost ratio. Native primitive. Auditable. Familiar to ops. **Adopted.**

---

## Consequences

### Positive

- **Mechanical refusal at substrate layer.** Cannot be bypassed by application bugs, prompt injection, or compromised API keys (except service_role, which is logged).
- **Constitutional floors become DB invariants, not best-effort guidelines.** A doctrine shift.
- **First production system with substrate-layer constitutional enforcement.** Industry leadership (per 2025-2026 survey: zero competitors do this).
- **Defense-in-depth.** Application-layer checks remain as a first line; RLS is the last line.
- **Auditable.** Every policy, every CHECK, every TRIGGER is in the schema. Visible in `pg_constraint`, `pg_policy`, `pg_trigger` system catalogs.

### Negative

- ~130 hours of work + ongoing maintenance
- Performance overhead per write (~0.5-2ms for policy evaluation; negligible at GEOX scale)
- Application code migration to call SECURITY DEFINER functions (some refactoring)
- Coordination with WEALTH, WELL, GEOX MCP server maintainers (P4)
- Service role must be carefully guarded (it bypasses RLS; emergency use only)

### Neutral

- Existing service_role policy remains; we tighten authenticated policy
- Migration is reversible per phase, with 888_HOLD for rollback
- Skill publication establishes the convention for future organs

---

## Verification (how we know this works)

| Test | Acceptance |
|---|---|
| **T1 — Floor-by-floor refusal** | For each of F1, F2, F7, F9, F11, F13, attempt a write that violates the floor WITHOUT setting required session GUC. Expected: SQLSTATE 42501 (insufficient_privilege). Verify via `pytest tests/03_constitutional/test_rls_floors.py`. |
| **T2 — Application layer still works** | All existing application write paths continue to function. Run `pytest tests/` — 100% pass rate. |
| **T3 — service_role emergency path** | `service_role` can still write directly for emergencies. Verified via audit log entry with `actor_role=service_role_emergency`. |
| **T4 — Constitutional test suite** | Existing F1-F13 floor tests (24/24 currently passing per `arifOS/AGENTS.md`) still pass. |
| **T5 — Performance** | Write latency increase <5ms p95 under synthetic load (1K writes/sec for 60s). |
| **T6 — Policy introspection** | All RLS policies visible via `pg_policies` and `pg_constraint` system catalogs. Snapshot committed to `arifosmcp_kernel_state.declared_tools`. |

---

## Open Questions

1. **Session GUC scope** — should `app.actor_id` etc. be set per-transaction (`SET LOCAL`) or per-session? **DECISION: `SET LOCAL` (per-transaction) for safety; per-session only with explicit opt-in.**

2. **Service role emergency logging** — when `service_role` is used, what audit fields are mandatory? **DECISION: `actor_id`, `session_id`, `reason`, `expected_duration` are all required. Event trigger refuses otherwise.**

3. **Floor version drift** — what if F1-F13 floors themselves evolve (per sovereign ruling)? **DECISION: schema-versioned floor definitions in `arifosmcp_floor_rules` table; policy binds to version, not to specific clauses.**

---

## References (evidence ledger)

**Industry (OBS):**
- "Memory in the Age of AI Agents" (Hu et al., arXiv:2512.13564, Jan 2026) — 12-framework survey
- "MemGPT" (Packer et al., arXiv:2310.08560) — virtual context management
- "Hindsight" (Latimer et al., arXiv:2512.12818) — 4-network epistemic memory
- Postgres 17 release notes — RLS, CHECK constraints, event triggers, SECURITY DEFINER
- Supabase RLS docs — `supabase.com/docs/guides/auth/row-level-security`
- pgvector, pg_graphql, pgcrypto, AGE extension docs

**Internal (OBS — verified via Supabase introspection 2026-06-24):**
- VAULT999 schema: `vault_seals`, `arifosmcp_memory_records`, `arifosmcp_kernel_state`, `arifosmcp_memory_audit_log`, `arifosmcp_memory_policy`, `arifosmcp_canon_records`
- 7 Postgres extensions currently installed
- §7.9 Memory Architecture (per `arifOS/AGENTS.md`)

**Forge session evidence:**
- `/root/forge_work/2026-06-24-osdu-research/RECEIPT.md`
- `/root/forge_work/2026-06-24-rls-hardening/` — this ADR + planned migration files

---

## Ratification

**Awaiting 888_HOLD from Arif.**

If ratified, this ADR becomes the canonical RLS-as-Floor hardening contract. Implementation proceeds in 5 phases (P1-P5). Each phase has its own 888_HOLD gate where it touches production.

**This is the highest-leverage substrate hardening available to the federation.** Mechanical refusal at the database is the doctrinal end-state for any "constitutional AI" claim.

**DITEMPA BUKAN DIBERI. The substrate becomes the constitution.**

— FORGE-000Ω, 2026-06-24
