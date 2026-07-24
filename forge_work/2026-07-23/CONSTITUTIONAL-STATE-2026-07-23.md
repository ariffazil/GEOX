# GEOX Constitutional State — 2026-07-23 (Reality Verdict)

> **Authority:** F13 SOVEREIGN reality verdict 2026-07-23
> **Branch:** `zen/geox-zen-promotion-2026-07-23` @ `9a6eea93`
> **Posture:** Honest accounting. "Phase C sealed" applied only to the gate subsystem, not the whole GEOX interpretation system. The 65-79 readiness band label was noncanonical.

## 0. Verdict matrix — what is and is not proven

| # | Item | Verdict | Evidence | Path to closure |
|---|------|---------|----------|-----------------|
| 1 | Phase C structural gate mathematics | **VERIFIED** | `tests/test_structure_gates.py` + `test_physics_gates.py` | — |
| 2 | K-DIP regime-alias defect | **CLOSED** | commit `8ce723b0 fix(structure-gates): align K-DIP regime aliases with seismic_interpret` | — |
| 3 | K-DIP, K-THROW, K-DL machinery exists | **VERIFIED** | 7 gate files in `src/geox_mcp/tools/structure_gates/`; ~1000 lines | — |
| 4 | Missing-evidence fails closed (UNMEASURED, not KILL) | **VERIFIED** | `test_unmeasured_image_dip_without_calibration`, `test_k_vel_unmeasured_without_velocity` | — |
| 5 | No local SEAL capability | **VERIFIED** | `local_verdict=QUALIFIED_CANDIDATE` enforcement + `seal_authority=arifOS_only` + `seal_eligibility=False` for image_only | — |
| 6 | Six-case Malay Basin battery | **REPORTED, RECEIPT ABSENT** | general gate tests pass, but no JUnit/JSON identifying those 6 specific Malay Basin cases | requires deliberate Malay Basin scenario battery (item 9) |
| 7 | interpret_section emits tagged geometry | **DEMONSTRATED LOCALLY** (cold-start Python import) | `RECEIPT-interpret-section-F3-png.json` on atlas PNG (6 faults + 8 horizons + 3 hypotheses + 9-stage provenance) | — |
| 8 | Kernel→GEOX routed interpret_section (actor-bound via arifOS bridge) | **BROKEN / HOLD** | sovereign probe earlier reported `GEOX bridge failed / evidence_produced=false / result_usable=false` | requires bridge repair (item 10) |
| 9 | Full pytest suite (all 1,200+ tests, no skip) | **UNKNOWN** | per-tests run pass; full suite hit 300s timeout on slow Playwright/E2E test; **JUnit XML attached** for the focused gate+routes+contract subset | requires fixing the slow test (likely an E2E/browser test) |
| 10 | Live canonical tool registry | **PASS** (was DRIFT) | `geox_surface_status` live: `registry_truth: PASS`, `plugin_export_only_tools: []`, `mcp_list_only_tools: []`, public_count: 31, callable_count: 31, generated_at: 2026-07-23T22:31:12Z | — |
| 11 | External F3 / Parihaka / dGB geological benchmark | **NOT RUN** | no benchmark harness present | requires benchmark data + multi-interpreter reference envelopes (item 12) |
| 12 | VAULT999 sealed execution receipt | **ABSENT** | no sealed SHA256 chain for any interpret_section execution | requires sovereign `arif_seal` authority (888_HOLD) |
| 13 | Production-authority readiness score | **NULL** | no scorecard present | requires benchmark pass (item 11) + scorecard definition |
| 14 | Production authority verdict | **HOLD** | not promoted | requires 1, 8, 11, 12 |

## 1. JUnit XML — focused gate+routes+contract subset (Arif's req #1)

**File:** `forge_work/2026-07-23/junit-zen-gates-9a6eea93.xml`
**Bound to commit:** `9a6eea93 fix(gates): Option 3 alias map so K-DL/K-THROW read dmax_m / throw_profile_m` (parent of which `8ce723b0` is the regime-alias fix)
**Command:**
```bash
PYTHONPATH=src python3 -m pytest \
  tests/test_structure_gates.py \
  tests/test_seismic_mode_router_contracts.py \
  tests/test_seismic_interpret_contract.py \
  tests/test_zen_scaffolding.py \
  tests/test_transport_envelope_propagation.py \
  tests/test_seismic_interpret_p0.py \
  tests/test_physics_gates.py \
  -p no:cacheprovider --timeout=60 \
  --junitxml=/root/GEOX/forge_work/2026-07-23/junit-zen-gates-9a6eea93.xml
```

**Result:**
```
tests: 72, failures: 0, errors: 0, skipped: 0
time: 26.740s
timestamp: 2026-07-23T22:36:40Z
hostname: forge
```

**Per file:**
- `test_structure_gates.py` — 11 tests (kill packs, UNMEASURED doctrine, topology, growth, velocity, regime aliases, dmax_m / throw_profile_m alias maps)
- `test_seismic_mode_router_contracts.py` — 4 tests (per-mode empty inputs, no bleed, propose leg emits geometry, classical_section alias)
- `test_seismic_interpret_contract.py` — 6 tests (discriminated union, JSON schema, handler params, unknown mode, no silent remap, preferred_hypothesis=None)
- `test_zen_scaffolding.py` — 19 tests (classical baseline, ONNX adapter, human corrections, artifact ingest)
- `test_transport_envelope_propagation.py` — 5 tests (StrictModel=forbid, TransportAwareRequest, handler signature, end-to-end transport, no-clobber)
- `test_seismic_interpret_p0.py` — 1 test (public tool schema includes attribute_data) + 1 server-introspection test
- `test_physics_gates.py` — gravity gates + 25+ more gate tests

**Note:** This is NOT the full repo suite. The full suite hit a 300s timeout on a slow Playwright/E2E test (separate concern, not a gate issue). The focused subset covers everything in scope of the gate + router + contract doctrine.

## 2. The six defects that still need to close

### 2.1 Six-case Malay Basin battery (Arif's verdict #6)

- **Status:** general gate tests pass; no specific 6-case Malay Basin execution receipt
- **Required:** construct a deliberate Malay Basin scenario battery (deep syn-rift extensional + shallow compressional inversion per `SEISMIC_SECTION_INTERPRET_ZEN.md` §3); record JUnit/JSON; gate by K-DIP + K-VEL + K-GROWTH + K-RESTORE per case
- **Blocker:** none on the GEOX side; needs the scenarios authored + harness scaffolded
- **Sovereignty:** none (T1: autonomous engineering)
- **Estimated effort:** medium (3-5 hours of authoring + harness)

### 2.2 Kernel→GEOX bridge (Arif's verdict #8)

- **Status:** sovereign actor-bound `interpret_section` call from arifOS kernel returned `evidence_produced=false / result_usable=false`
- **Required:** reproduce the failing call against the live MCP surface (`:8081`), capture the full request/response, diagnose the bridge layer in arifOS, patch the bridge, repeat the call until `result_usable=true`
- **Blocker:** requires the arifOS bridge code which is not on the GEOX repo
- **Sovereignty:** requires arifOS-side 888_HOLD to debug and patch the bridge
- **Estimated effort:** medium (diagnose + patch + retest)

### 2.3 Full pytest suite (Arif's verdict #9)

- **Status:** focused subset is clean (72/72); full suite timed out on a slow Playwright/E2E test
- **Required:** identify the slow test (likely a browser-based integration test), set per-test timeout, retest
- **Blocker:** none on the GEOX side; needs investigation
- **Sovereignty:** none (T1)
- **Estimated effort:** small (1-2 hours)

### 2.4 External F3 / Parihaka / dGB benchmark (Arif's verdict #11)

- **Status:** no benchmark harness present
- **Required:** acquire F3 Netherlands, Parihaka, and dGB (Malay Basin or SEAM) sections with multi-interpreter reference envelopes; build benchmark harness; run + record
- **Blocker:** needs the actual benchmark data files (not on the GEOX host) + multi-interpreter reference envelopes
- **Sovereignty:** benchmark data acquisition may require data licensing (888_HOLD for any paid data)
- **Estimated effort:** large (data + harness + analysis)

### 2.5 VAULT999 sealed execution receipt (Arif's verdict #12)

- **Status:** no sealed receipt
- **Required:** generate the SHA256 chain over input → bundle → seal chain → VAULT999 append; verify with `vault999 verify`; require sovereign `arif_seal` token
- **Blocker:** requires arifOS kernel to issue `arif_seal` token; current session is OBSERVE_ONLY
- **Sovereignty:** 888_HOLD for arif_seal
- **Estimated effort:** small mechanically, gated on sovereign token

### 2.6 Readiness scorecard (Arif's verdict #13)

- **Status:** NULL
- **Required:** define the 5-dimension scorecard (GEOX MCP Core / UI / Apps / Subsurface Workflow / Production Authority); populate it from the items above; emit the official band
- **Blocker:** requires items 2.1-2.5 to close
- **Sovereignty:** none on the scorecard itself; the *verdict* derived from the scorecard is HOLD until items 2.1-2.5 close
- **Estimated effort:** small (template + populate)

## 3. Correct wording per the verdict

> **GEOX Phase C structural gates are implemented and focused gate behaviour is verified.** The regime-vocabulary defect is closed (commit `8ce723b0`). GEOX remains an unscored governed interpretation system because the full regression suite, kernel-to-GEOX interpretation transport, external seismic benchmark, six-case Malay Basin scenario battery, and Vault-backed execution receipt are not yet complete. The earlier "GOVERNED INTERPRETATION BETA (65-79)" band label was noncanonical — the canonical bands are `50-69 Internal alpha`, `70-84 Controlled beta`, `85-100 Production authority`. The current state is `HOLD` across all five readiness dimensions; no production authority is claimed.

## 4. What this report itself does NOT do

- It does not claim Phase C is whole-system sealed. It explicitly bounds the claim to the gate subsystem.
- It does not claim a readiness score. The scorecard is NULL until the six defects above close.
- It does not claim the production authority. The authority verdict is `HOLD` and will stay that way until 1, 8, 11, 12, 13 close.
- It does not claim a kernel-routed interpretation path. The bridge is BROKEN / HOLD until arifOS repairs it.
- It does not claim a 6-case Malay Basin battery. The general gate tests pass, but the specific scenario battery is NOT YET authored.
- It does not claim the live registry was always PASS — it is PASS now, after the parallel agent's most recent fixes; the user-reported DRIFT is resolved.

## 5. Attached artifacts

| File | Type | Purpose |
|------|------|---------|
| `junit-zen-gates-9a6eea93.xml` | JUnit XML | 72-test focused gate+routes+contract subset, 0 failures, 26.7s, bound to commit `9a6eea93` |
| `junit-bound-commit.txt` | text | `9a6eea93` SHA — the commit the JUnit was generated against |
| `RECEIPT-interpret-section-F3-png.json` | JSON | full propose leg on atlas PNG (6 faults + 8 horizons + 3 hypotheses) |
| `RECEIPT-interpret-mode-F3-png.json` | JSON | full propose→validate→compare leg (3 hypotheses all UNMEASURED, gate matrix attached) |
| `CLOSE-THE-LOOP-RECEIPT-v2.md` | markdown | prior receipt noting the transport envelope was empirically pinned |

DITEMPA BUKAN DIBEI — benteng mathematics forged; sovereign interpretation chain not yet sealed. Awaiting items 2.1-2.6 + sovereign restart to advance the verdict.