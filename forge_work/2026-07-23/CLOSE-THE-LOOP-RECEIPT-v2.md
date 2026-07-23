# Close-the-Loop Receipt v2 — Transport Envelope Doctrine, Pinned

> **Authority:** F13 SOVEREIGN · DRAFT_ONLY
> **Branch:** `zen/geox-zen-promotion-2026-07-23` (4 commits ahead of main)
> **Caller:** Arif (sovereign probe round 2)
> **Purpose:** pin down the three points Arif raised about the contract patch — with empirical proofs, not assertions.

## 0. Honest corrections to v1

Arif caught three real issues. I owe the corrections up front:

| Arif's point | Was v1's claim | What's actually true | Action taken |
|--------------|---------------|----------------------|--------------|
| **#1: `ignore` vs `allow`** | "unknown request fields are now passed through to handler (audit intent)" | `extra="ignore"` *silently drops* unknown fields. They never reach the handler. The audit-intent claim was wrong. | My `extra="ignore"` was superseded by parallel-agent commit `07619e31 fix(contract): declared transport envelope + extra=forbid (not ignore)` — `StrictModel.extra="forbid"`, `TransportAwareRequest` declares the 4 transport fields. Now the receipt survives validation, not silent drop. |
| **#2: typo hazard** | (not addressed in v1) | `forbid` keeps the typo tripwire; declared `TransportAwareRequest` keeps transport flowing. | Already correct after `07619e31`. |
| **#3: deployed, not just patched** | "branch is ready" | Correct — the patch is on the branch, not merged to main. | Acknowledged. Below. |

## 1. Empirical proof — what actually happens to MCP transport

I wrote a test (`tests/test_transport_envelope_propagation.py`, 5 tests, all green) that pins three layers:

### 1a. Schema layer (parallel-agent commit `07619e31`)

```
StrictModel.model_config.extra = 'forbid'                 # typo tripwire alive
TransportAwareRequest declared fields =                   # transport envelope
  ['actor_id', 'session_id', 'source_sha256', 'trace_id']
```

- ✅ `session_idd` (typo with extra `d`) → `ValidationError: interpret_section.session_idd`
- ✅ `some_random_garbage` (undeclared noise) → `ValidationError: interpret_section.some_random_garbage`
- ✅ Declared transport fields reach `model_dump()` unaltered

### 1b. Handler signature layer (this commit `12b788eb`)

Before this commit, the empirical test showed:

```
geox_seismic_interpret(session_id='probe-001', ...)
→ TypeError: geox_seismic_interpret() got an unexpected keyword argument 'session_id'
```

That's the gap. The schema declared the fields, but the Python signature rejected them — so even after the parallel-agent's fix, the receipt never reached the handler. **My v1 report missed this.**

After this commit:

```
geox_seismic_interpret signature = ... session_id, actor_id, trace_id, source_sha256, ...
handler accepts transport kwargs ✓
```

### 1c. End-to-end — declared transport reaches response provenance

```
geox_seismic_interpret(mode='interpret_section', image_path=..., 
                       session_id='probe-sess-001', actor_id='arif-fazil', 
                       trace_id='trc-sov-1', source_sha256='sha256:abc123')
  → response.provenance.session_id  = 'probe-sess-001'
  → response.provenance.actor_id    = 'arif-fazil'
  → response.provenance.trace_id    = 'trc-sov-1'
  → response.provenance.source_sha256 = 'sha256:abc123'
```

Pinned by `test_transport_reaches_response_provenance`.

## 2. Doctrine: schema + signature must both declare the same fields

The lesson from this round:

- **Schema alone** (TransportAwareRequest + forbid): typos trip, but the handler signature still rejects the field.
- **Signature alone** (added kwargs): typos slip, but fields flow.
- **Schema + signature together** (this commit's state): typos trip at schema, declared fields flow to handler, response carries provenance.

The audit trail is no longer blind on this. The 5-test regression set in `tests/test_transport_envelope_propagation.py` makes the contract falsifiable — if anyone re-introduces `extra="ignore"` or strips the signature params, the test fails.

## 3. Capability leg — `interpret_section` emits tagged geometry (unchanged from v1)

Saved to `forge_work/2026-07-23/RECEIPT-interpret-section-F3-png.json` (atlas PNG, 6 faults + 8 horizons + 3 hypotheses) and `RECEIPT-interpret-mode-F3-png.json` (interpret mode, full propose→validate→compare, 3 hypotheses all UNMEASURED on missing scale).

## 4. VOID vs ERROR — still distinguishable

| Outcome | `ok` | `error` | `governance_status` | Meaning |
|---------|------|---------|---------------------|---------|
| VOID-no-data (governance) | `True` | `None` | `HOLD` | image-only → no SEAL; pick is INTERPRETED, not Earth |
| VOID-gates KILL | `True` | `None` | `HOLD` | physically impossible structure |
| VOID-no-input (UNMEASURED) | `True` | `None` | `HOLD` | missing scale → never guess |
| ERROR-router | `False` | `UNKNOWN_MODE` | `HOLD` | dispatch contract failure |
| ERROR-file-missing (ops) | `False` | `FILE_NOT_FOUND` | `HOLD` | input unavailable |
| ERROR-handler-bug | `False` | `MISSING_REQUIRED_FIELD` / `MISSING_IMAGE_PATH` | `HOLD` | engineering defect |
| ERROR-unreachable (server down) | n/a | n/a | n/a | transport — separate layer |

## 5. Status of the two open claims (corrected)

| Claim | Before v1 | After v1 | After v2 (now) |
|-------|-----------|----------|----------------|
| Router dispatch bug | INTERPRETED | OBSERVED (single-witness, Arif) | OBSERVED (router regression test in `tests/test_seismic_mode_router_contracts.py`) |
| Propose leg alive | INTERPRETED | OBSERVED (interpret_section end-to-end) | OBSERVED (RECEIPT-*.json + 4-test router regression) |
| **NEW: transport envelope flows** | (not asserted) | (audit-intent claim was wrong) | **OBSERVED** — 5 regression tests in `test_transport_envelope_propagation.py` |

## 6. Point 3 — code-changed, not deployed

Arif is right. The receipts in this report are pinned to **branch state**, not main. The path to close-the-loop for real is:

```
patch on branch  →  merge to main  →  restart geox-mcp  →  curl :8081/health  →
  →  rerun 3 originally-failing calls from Arif's surface  →  all 3 mode-correct
```

Items 1–2 are 888_HOLD per `AGENTS.md §6.2` ("`git push origin main` for sovereign commit chain" + "Production deployment without verified build + test pass"). The branch is ready; the call is Arif's to make.

Until merge + restart, this is **one surface** (Kimi-side Python imports) plus **one surface** (Arif's MCP call earlier in the conversation) corroborating each other. Independent third surface = your three-call rerun post-restart. I cannot mark B-deployed until that.

## 7. Open items (not blocking receipt pinning)

| # | Item | Severity | Notes |
|---|------|----------|-------|
| 1 | GEOX `/health` GET time-out (MCP serves fine) | low | needs an ops fix; not a contract issue |
| 2 | `geox_blend_volume_tool()` returned `MISSING_REQUIRED_FIELD` for `volume_ref` | low | parallel-agent fixed in `4bef1d8a` — returns VOID_NO_DATA instead of raising |
| 3 | GEOX availability oscillation (up → down → up) | medium | ops check; this session saw it back up; needs a watchdog |
| 4 | Phase D: SEG-Y 2.1 XML parsing + 3D volume | deferred | not on image-first path; deferred per audit |
| 5 | Audit-log dropped fields if any future layer falls back to `extra="ignore"` | low | doctrine now keeps forbid; no current need |

## 8. Branch + test status

- `zen/geox-zen-promotion-2026-07-23` at `12b788eb fix(seismic): handler signature declares + propagates MCP transport metadata` (5 commits ahead of main)
- 5 / 5 transport tests pass
- 55 / 55 focused tests pass (transport + router contracts + interpret contract + structure gates + zen scaffolding + p0)
- Full suite timed out on a slow Playwright test (not on the close-the-loop critical path)

DITEMPA BUKAN DIBEI — receipts pinned with empirical tests; ready for the sovereign restart call.

Ping me after the restart and the three-call rerun — that's the missing third surface.