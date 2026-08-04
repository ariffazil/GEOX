# GEOX MCP — Session Distillations (Future-Binding)

> **Sealed for carry-forward:** 2026-08-04 · Agent: Grok Build FI-007 · Sovereign: F13 ARIF  
> **Epistemic:** `OBS` (live probes) · `DER` (session process) · `INT` (doctrine)  
> **Doctrine:** DITEMPA BUKAN DIBERI  
> **llms.txt context (implementation reference only):**  
> https://gofastmcp.com/llms.txt · https://modelcontextprotocol.io/llms.txt

These eight rules bind future GEOX MCP work. They are not narratives — they are operating constraints.

---

## 1. Data ingestion is the gate

~28% of GEOX tools fail without physical files on disk.

| Required pathway | Status |
|------------------|--------|
| `source_uri` (local path / URI) | Exists on well/seismic ingest |
| `content_base64` upload decode | Exists (`contracts/tools/canonical/_artifact_helpers.py`, `tools_wiring`) |
| `/root/forge_work/` agent drop-zone | Exists; tools must accept it as first-class source_uri root |

**Rule:** Prefer `content_base64` OR explicit `forge_work` path over hoping files are pre-staged.  
**When ingest fails:** dependent claims auto-downgrade (see §4). Do not invent geology.

---

## 2. Evidence tiering is non-negotiable

Every claim leaving GEOX **must** carry one of:

`OBS` · `DER` · `INT` · `SPEC` · `UNKNOWN`

No narrative without tags. F2 TRUTH. Cheap untagged claims → VOID at judge.

---

## 3. Falsification drives EUREKA

Process > paper. Rotan session: **5 gas-origin models tested → 4 died → 1 survivor**.  
The survivor was not found pre-packaged in literature — it emerged from elimination.

**Rule:** GEOX tools that propose origin/charge/model **must** expose falsify hooks (`geox_falsify`, contradiction scan). Survival ≠ proof (Popper).

---

## 4. Failed tools must propagate uncertainty

Example: backstripping failed → burial model = **PROVISIONAL** → all thermal/maturity dependents demote.

| Mechanism | Location |
|-----------|----------|
| Cascade demotion | `geox_core/governance/cascade_demotion.py` |
| Auto-downgrade overclaims | `contracts/enums/statuses.py` F2 gate |
| Kill matrix + K009 | `geox_mcp/tools/claim_unified.py` |

**Rule:** Tool failure is not silent. Emit PROVISIONAL + demote dependents. Never paper over a missing lithology_model.

---

## 5. External audit is the calibration

Copilot **without** GEOX still caught 5 overconfidence errors.  
Human + AI + Earth tri-witness works (F3). Do not let GEOX become a self-sealing echo chamber.

**Rule:** Before SEAL-grade earth claims, prefer at least one external (non-GEOX) critique pass.

---

## 6. NSPW answers OCT plumbing; OCT still needs sand + seal + trap

| Element | Role |
|---------|------|
| **NSPW** | Plumbing engine — distal charge pathway (Rotan proves distal charge *can* work) |
| **OCT** | Still requires reservoir sand + seal + trap geometry |

**Rule:** Do not treat NSPW connectivity as a completed petroleum system. Charge plumbing ≠ commercial accumulation.

---

## 7. Surface internal tools — zero new code first

Registry drift > RESOLVED path:

1. Inventory internal vs public (`tools.json`, `CANONICAL_PUBLIC_SURFACE.json`, live `:8081/tools`)
2. Re-register existing implementations (`@mcp.tool`, EGS, GHOST resurrect)
3. Reconcile manifests to **live** count
4. Restart + prove `surface_drift.ok == true`

Live T1 (2026-08-04): **GEOX tools_loaded=42 · drift_count=0**.

---

## 8. Pressure connectivity is a snapshot; migration is a history

**Hard-coded into falsification as K009** (`PRESSURE_SNAPSHOT_NE_MIGRATION_HISTORY`).

Claims that equate present-day pressure communication with multi-Ma hydrocarbon migration/charge **must** be HIGH-severity demoted unless independent charge evidence exists (isotopes, FIS, biomarkers, timed fill).

---

## Infrastructure gaps closed this arc

| Gap | Status | Evidence |
|-----|--------|----------|
| GAP1 server/discover → `arifos://instructions` | ✅ MCP wire live; REST catalog + read path fixed 2026-08-04 | MCP `resources/read` returns BOOT SEQUENCE; REST `manifest_resources` includes bootstrap URIs |
| GAP2 555-ASI model | ✅ OpenCode `555-ASI` → `qwen-token-plan/qwen3.6-flash` | FED `:4000` still DOWN — direct provider bypass intentional |
| M1–M7 GEOX surfacing | ✅ 42 public · ghost tools resurrected · EGS re-enabled | `:8081/health` surface_drift.ok |
| tools.json drift (33 vs 42) | ✅ Reconciled to live 42 | `tools.json` version 2026.08.04 |
| K009 pressure≠migration | ✅ Coded into `geox_falsify` filters | `claim_unified.py` |

---

## Residual open loops (science / infrastructure — not silent-closed)

| Loop | Class | Why open |
|------|-------|----------|
| NSPW→Rotan direct charge linkage | SCIENCE · 888_HOLD | Needs isotope/FIS; unproven |
| Thermal model EasyRo calibration | SCIENCE · PROVISIONAL | Sensitivity uncalibrated |
| Sabah–Haq correlation source separation | SCIENCE · HOLD | Source separation incomplete |
| Data ingestion completeness (~28% file-gated tools) | ENG · OPEN | Pathways exist; end-to-end staging still partial |
| FED LiteLLM gateway `:4000` | ENG · DEGRADED | Bypassed; restore when capacity allows |
| WELL W3 degraded (~0.59) | SUBSTRATE · REFLECT | Prefer short reversible work; not a GEOX blocker |
| Backstripping lithology_model gaps | ENG/SCI · PROVISIONAL | Cascade-demote dependents when missing |

---

## Agent boot checklist (MCP-native)

```
resources/read arifos://instructions
resources/read arifos://carry-forward
resources/read arifos://flow-state
tools/call arif_init
# then organ work via GEOX :8081 — never skip epistemic tags
```

*DITEMPA BUKAN DIBERI*
