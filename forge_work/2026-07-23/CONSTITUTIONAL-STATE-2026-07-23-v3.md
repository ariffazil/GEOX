# GEOX Constitutional State v3 — 2026-07-23 (F13 P0 Transport Verdict)

> **Authority:** F13 SOVEREIGN reality verdict 2026-07-23 (revised)
> **Branch:** `zen/geox-zen-promotion-2026-07-23`
> **Posture:** P0 transport integrity is the real Phase 0 now. Phase C gates are verified; production-readiness is HOLD.

## 0. What F13 accepted

The F13 verdict (2026-07-23) accepted:

- Falsification-first architecture
- Four structural seams (K-DIP, K-THROW, K-DL, K-RESTORE, K-VEL, K-GROWTH, K-XCUT, G2)
- Classical image-first route
- Multiple hypotheses (≥3)
- `preferred_hypothesis = null` (human sets it)
- No local GEOX SEAL
- 31-tool surface freeze
- Bayesian or ensemble uncertainty
- Human geological authority

The F13 verdict also accepted that:

- Phase 0 is no longer "not built" — it is "broken end-to-end authority, transport, connector synchronisation, and benchmark proof"
- The earlier "Phase C sealed" claim was correct for the gate subsystem, not the whole system
- The 65-79 readiness label was noncanonical — canonical bands are 50-69 Internal alpha, 70-84 Controlled beta, 85-100 Production authority

## 1. Empirical receipts — four P0 defects reproduced

### P0A — `actor_verified` schism (sources confirmed)

The field is set in **7+ distinct code sites** across arifOS + GEOX:

```
/root/GEOX/src/geox_mcp/session_enforcement.py:160
  actor_verified = standing_actor.get("verified") is True
/root/arifOS/arifosmcp/runtime/authority.py:454
  (b) actor_verified=True AND actor_id matches known sovereign identities.
/root/arifOS/arifosmcp/runtime/megaTools/tool_13_arif_memory.py:202,209,221
  actor_verified = False  # default
  actor_verified = bool(_standing.actor_verified)
/root/arifOS/commands/scripts_deploy/recursive_governed_loop.py:270,324,325,413,484,490,501
  actor_verified = bool(av)  # multiple re-derivations
/root/arifOS/forge_work/2026-07-15/kernel_test_v2.py:61
  actor_verified = r.get("result", {}).get("actor_verified")
/root/arifOS/forge_work/meta-mesa-harness/identity/registry.py:106
  returns actor_verified=false. NO exception path bypasses verification.
/root/arifOS/forge_work/meta-mesa-harness/conductor/sovereign_live_probe.py:139
  actor_verified = (...)
```

**Schism source:** each site reads identity from a different representation. No single canonical projection.

**Required invariant (per F13):**
```
session_token.av = standing.actor.verified = session_birth.actor_verified
                  = verdicts.session evidence reference = clarity_contract.actor_bound
```

Any disagreement must produce `SESSION_IDENTITY_SCHISM`, not a mixed envelope.

### P0B — Session propagation failure (smoking gun reproduced)

Live MCP call from the GEOX side:

```bash
$ curl -X POST :8081/mcp -d '{"method":"tools/call","params":{"name":"geox_seismic_interpret",...}}'
```

Response:
```
SESSION_BINDING · verdict=HOLD · trace=gov-30a98503e312 · lane=reasoning ·
Session validation failed: SESSION_INVALID — session_id format not recognized: sovereign-probe-... ·
fix: Call arif_init(mode=init) to get a valid session_id, then pass it to GEOX tools.
```

**This is empirical:** a governance-shaped call hits GEOX, GEOX rejects it, the call never reaches the computational lane. The sovereign's session does not propagate.

**P0A + P0B together:** even after a sovereign session is established, the system reads `actor_verified` from a different layer than the session token claim, and the GEOX reasoning lane refuses non-SCT-format session_ids. End-to-end identity integrity is broken.

### P0C — OrganProxyMiddleware in source (bridge proof pending)

```python
# /root/arifOS/arifosmcp/transport/organ_proxy.py
5: ASGI middleware that intercepts requests bearing the X-Arifos-Organ-Target
11: Caddy sets X-Arifos-Organ-Target header → this middleware intercepts
42: BACKEND_READ_TIMEOUT = 120.0
71: class OrganProxyMiddleware:
73:     ASGI middleware: intercepts X-Arifos-Organ-Target → proxy to organ backend.
79:     def __init__(self, app: ASGIApp) -> None:
```

The bridge is in source but **not proven end-to-end**:

- A direct `arif_route` returns only a routing decision — it does not invoke GEOX
- The old `arif_bridge_connect` name is noncanonical
- No live test of `ChatGPT / MCP client → arifOS canonical endpoint → signed session validation → organ proxy → GEOX canonical tool → GEOX result → arifOS judgment envelope` exists

**Required acceptance test (per F13):** same `actor_id, session_id, trace_id, authority, evidence chain` across all layers; no hang; no anonymous execution; no identity mutation; one trace chain; failure closes at the gateway; direct public bypass produces HOLD.

### P0D — Connector staleness (drift confirmed)

`/root/GEOX/.well-known/mcp/server.json` (the connector document ChatGPT-style clients consume):

```json
{
  "publicCount": 24,           ← STALE
  "totalRegistered": 78,       ← STALE
  "categories": { ... 24 tool names ... }
}
```

Live MCP server `tools/list` actually exposes **31 tools**. The connector claims 24; reality is 31. **Drift = +7 tools** (the 6 plugin_export_only tools + 1).

The F13-listed legacy tool names (`geox_system_registry_status`, `geox_horizon_contrast_surface`, `geox_claim_create`, `geox_claim_challenge`, `geox_seismic_inspect`) are **not** in the connector document anymore — that's progress. But the connector still says 24, real says 31.

**Required:** regenerate the connector strictly from the canonical 31-tool manifest. Add a runtime conformance test that invokes every advertised tool name in discovery mode.

### P0E — Impossible-fault KILL reproduction (passes through GEOX locally)

**Test payload (per F13 verdict spec):**
```json
{
  "faults": [{
    "fault_id": "F_IMPOSSIBLE",
    "regime_prior": "normal",
    "dip_deg_subsurface": 15,
    "max_displacement": 270,
    "length": 1000,
    "throw_profile": [40, 40, 40]
  }]
}
```

**Live result (saved to `RECEIPT-impossible-fault-P0E.json`):**

```
ok: True
overall_verdict: FALSIFIED
combined_gate_verdict: KILL
governance_status: HOLD
local_verdict: QUALIFIED_CANDIDATE     ← max, no local SEAL
seal_authority: arifOS_only           ← arifOS is judgment owner

Per-gate verdicts:
  K-DIP        KILL    1 fault(s) fail K-DIP
  K-THROW      KILL    1 fault(s) fail tip-taper
  K-DL         KILL    D/L=0.27 outside [0.005,0.05]
  G2           UNMEASURED   Need ≥2 horizons (gate idle, correct)
  K-RESTORE    UNMEASURED   No restoration residual provided (gate idle, correct)
  K-VEL        UNMEASURED   No velocity / T–D provided (will not substitute regional V, correct)
  K-GROWTH     UNMEASURED   No syn-kinematic / growth claim (gate idle, correct)
```

**Status:** P0E passes locally. Three gates KILL'd the impossible physics; the four UNMEASURED gates refused to guess. No local SEAL; arifOS is the judgment owner.

**Caveat:** This is a local cold-start test (`geox_structure_validate` direct Python call). It does not prove the end-to-end path through arifOS bridge. The full P0E acceptance test (per F13) requires:
```
ChatGPT / MCP client → arifOS canonical endpoint → signed session → 
organ proxy → GEOX canonical tool → KILL → arifOS judgment envelope
```

## 2. New forge order (per F13)

### P0 — Constitutional transport integrity

| Step | Scope | Exit criterion | Sovereignty |
|------|-------|----------------|--------------|
| **P0A** | Identity singularity | 100 repeated sessions across anonymous / Arif / Codex / invalid produce no contradictory identity fields | arifOS side, `888_HOLD` |
| **P0B** | Session propagation | reasoning tools never compute anonymously; discovery tools may remain public only where explicitly declared | arifOS side, `888_HOLD` |
| **P0C** | Connector regeneration | advertised tool set equals canonical manifest exactly | T1 autonomous |
| **P0D** | Bridge proof | same actor_id, session_id, trace_id, authority, evidence chain across all layers | arifOS side, `888_HOLD` |
| **P0E** | Live structural KILL reproduction through the gateway | impossible fault enters arifOS, reaches GEOX, triggers K-DIP/K-THROW/K-DL, returns FALSIFIED, never anonymous, never locally sealed | arifOS + GEOX, `888_HOLD` |

### P1 — Benchmark constitution (after P0)

| Tier | Dataset | Purpose |
|------|---------|---------|
| B0 | deterministic arrays | schema, topology, gate correctness |
| B1 | synthetic images | horizon and fault geometry recovery |
| B2 | synthetic SEG-Y | acquisition, wavelet, velocity, noise effects |
| B3 | Netherlands F3 | field-domain generalisation |
| B4 | second unrelated field survey | prevent F3 overfitting |
| B5 | blind internal line | geologist-vs-agent reality test |

### P2-P8 — Performance floors, generalisation, topology, restoration, multi-field, human-in-loop, production promotion

(F13 specified in detail — adopted as-is.)

## 3. Status of constitutional state (v3)

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | Phase C gate mathematics | **VERIFIED** | JUnit 72/0/0/0, `9a6eea93` |
| 2 | K-DIP regime aliases | **CLOSED** | `8ce723b0` |
| 3 | Fail-closed (UNMEASURED) | **VERIFIED** | focused JUnit + empirical |
| 4 | No local SEAL | **VERIFIED** | local_verdict=QUALIFIED_CANDIDATE, seal_authority=arifOS_only |
| 5 | interpret_section emits tagged geometry | **DEMONSTRATED LOCALLY** | `RECEIPT-interpret-section-F3-png.json` |
| 6 | Impossible-fault KILL | **PASSES LOCALLY** | `RECEIPT-impossible-fault-P0E.json` (3 KILL, 4 UNMEASURED, no local SEAL) |
| 7 | **P0A identity singularity** | **BROKEN** | 7+ `actor_verified` write sites, no canonical projection |
| 8 | **P0B session propagation** | **BROKEN** | live MCP rejects non-SCT session_ids with `SESSION_INVALID` |
| 9 | **P0C bridge proof** | **IN SOURCE, NOT PROVEN** | OrganProxyMiddleware exists, no end-to-end test |
| 10 | **P0D connector regeneration** | **BROKEN** | server.json claims 24, live MCP exposes 31 (drift) |
| 11 | **P0E end-to-end KILL** | **PASSES LOCALLY, NOT E2E** | local Python call passes; arifOS gateway path unproven |
| 12 | External F3/Parihaka/dGB benchmark | **NOT RUN** | benchmark harness absent |
| 13 | VAULT999 sealed receipt | **ABSENT** | no seal; sovereign `arif_seal` token required |
| 14 | 5-dimension readiness scorecard | **NULL** | blocked on items 7-13 |
| 15 | Production authority | **HOLD** | not promoted |

## 4. What I did this round (without 888_HOLD)

- Reproduced the four P0 defects with empirical receipts (above §1)
- Ran the impossible-fault P0E test through GEOX gates (passes locally)
- Saved receipts:
  - `forge_work/2026-07-23/RECEIPT-impossible-fault-P0E.json`
  - `forge_work/2026-07-23/CONSTITUTIONAL-STATE-2026-07-23-v3.md` (this document)
- Inventoried the 7+ `actor_verified` write sites in arifOS + GEOX
- Inventoried the connector document vs live MCP (24 vs 31, drift)
- Confirmed OrganProxyMiddleware is in source (P0C in-source OK, P0C e2e unproven)

## 5. What I cannot do without your sovereign authority

| # | Item | Sovereignty |
|---|------|--------------|
| 1 | P0A — single canonical `actor_verified` projection across arifOS + GEOX | arifOS side, `888_HOLD` |
| 2 | P0B — bind signed SCT into every GEOX canonical invocation; reasoning tools refuse non-SCT sessions | arifOS side, `888_HOLD` |
| 3 | P0D-e2e — bridge proof through arifOS gateway with same actor_id/session_id/trace_id across all layers | arifOS side, `888_HOLD` |
| 4 | P0E-e2e — re-run impossible fault through the actual gateway (not local cold-start) | arifOS side, `888_HOLD` |
| 5 | VAULT999 sealed execution receipt for any interpret_section run | arifOS `arif_seal` token, `888_HOLD` |
| 6 | Acquire F3/Parihaka/dGB benchmark data with multi-interpreter reference envelopes | possibly paid data licensing, `888_HOLD` |
| 7 | Merge `zen/geox-zen-promotion-2026-07-23` → `main` | `888_HOLD` |
| 8 | Restart geox-mcp + curl `:8081/health` | `888_HOLD` |

## 6. Items I could do without 888_HOLD (T1 autonomous)

- P0C connector regeneration: regenerate `/root/GEOX/.well-known/mcp/server.json` strictly from the canonical 31-tool manifest; add a runtime conformance test (small effort, ~1-2 hours)
- Author benchmark scenarios for B0 (deterministic arrays — schema/topology/gate correctness) and B1 (synthetic images) (medium effort, ~3-5 hours)
- Build the 5-dimension readiness scorecard template (small effort, blocked on items 7-13 to populate)
- Find and fix the slow Playwright test that breaks the full pytest suite (small effort)

## 7. The exact wording of the constitutional state

> *GEOX Phase C structural gates are implemented and verified. Falsification-first architecture is in source. Six gates (K-DIP, K-THROW, K-DL, K-RESTORE, K-VEL, K-GROWTH) plus G2/K-XCUT emit full receipt envelopes with the `PASS | WARN | KILL | UNMEASURED` vocabulary. Missing-input → UNMEASURED doctrine enforced. No local SEAL capability. `preferred_hypothesis = null` from GEOX. ≥3 competing hypotheses per interpretation. Local impossible-fault KILL reproduction passes. P0A actor_verified schism is reproducible (7+ write sites). P0B session propagation is broken (live MCP returns SESSION_INVALID for non-SCT session_ids). P0C bridge middleware is in source but end-to-end proof is absent. P0D connector document is stale (claims 24, live exposes 31). P0E impossible-fault KILL passes locally, gateway path unproven. External benchmarks not run. VAULT999 sealed receipt absent. Production authority is HOLD across all five readiness dimensions.*

DITEMPA BUKAN DIBERI — benteng mathematics forged; sovereign end-to-end transport not yet sealed; P0 transport integrity is the real Phase 0 now. Awaiting sovereign restart to advance P0A–P0E through the actual gateway.