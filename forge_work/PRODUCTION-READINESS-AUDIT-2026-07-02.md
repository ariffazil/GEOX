# GEOX Production Readiness Audit — 11-Gate Scorecard

> **Date:** 2026-07-02 | **Session:** SEAL-318331bb5a70466d
> **Sovereign:** Arif (F13) | **Auditor:** OpenCode (FORGE)
> **Evidence band:** L2 (MCP source inspection), L4 (architecture verdict)
> **Verdict:** YELLOW — concept strong, production gaps real

## Scorecard

| # | Gate | Status | Evidence | Gap |
|---|------|--------|----------|-----|
| 1 | Protocol Health | 🟡 85% | MCP initialize ✅, tools/list ✅ (33/35), tools/call ✅, schemas ✅, conformance 9/9 | 2 tools not exposed (atlas, doctrine); session lifecycle needs proper MCP client |
| 2 | Domain Correctness | 🟡 70% | 196 claim/uncertainty refs, fixtures exist, map tools live, EGS system operational | 1 test failure (alignment); no golden output corpus for LAS/SEG-Y validation |
| 3 | Governance Correctness | 🟡 75% | 888_HOLD on claim/prospect, truth class gates on map, EGS challenge engine | No dry-run mode; auth not tested; evidence floor classifier not explicit |
| 4 | Reproducibility | 🟡 60% | Artifact envelope contract written, export PROV sidecar live, checksums on exports | Envelope not stamped on 35 tool returns; no parameter_set recording per tool |
| 5 | Civilizational Safety | 🟡 70% | Truth classes enforced (CONTEXT/INTERPRETATION/DECISION_SUPPORT), limitations in export warnings | No explicit forbidden-claims list in code; no BLACK risk classification |

## What Exists (Strong Foundation)

| Component | Status | Quality |
|-----------|--------|---------|
| MCP server | ✅ Live on :8081 | FastMCP 3.4.2, Streamable HTTP, 33 tools exposed |
| Tool schemas | ✅ 100% coverage | inputSchema + outputSchema on all 33 tools |
| EGS (Earth Graph System) | ✅ Operational | claim_create, challenge, evidence_attach, evidence_reason, uncertainty, provenance |
| Map verb chain | ✅ Complete | layers_list → scene_plan → render_preview → export_package |
| PROV sidecar | ✅ Built | W3C PROV-O + STAC catalog on every export |
| Artifact envelope | ✅ Contract written | `contracts/artifact_envelope.py` — stamp_envelope() + verify_envelope() |
| Truth classes | ✅ Enforced | CONTEXT, INTERPRETATION, DECISION_SUPPORT gates on map tools |
| Uncertainty model | ✅ 561 references | p10/p50/p90, confidence scoring, uncertainty layers |
| arifOS conformance | ✅ 9/9 PASS | Full constitutional kernel verified |
| Test suite | ⚠️ Partial | 837+ tests, 1 alignment failure |

## What's Missing (Production Gaps)

### Critical (blocks v1)

| Gap | Impact | Effort | Fix |
|-----|--------|--------|-----|
| `stamp_envelope()` not integrated | No forensic traceability on tool returns | 1 day | Add 1-line stamp to each of 35 tool returns |
| No golden test corpus | Cannot prove domain correctness | 2 days | Create LAS/SEG-Y/attribute fixtures with expected outputs |
| No dry-run mode | Cannot preview mutations safely | 1 day | Add `dry_run: bool` param to mutating tools |
| 1 test failure | Alignment discipline broken | 1 hour | Fix `test_f3_receipt_exists_for_substrate_hardening` |
| 2 tools missing from MCP | atlas + doctrine not exposed | 1 hour | Register in MCP server or mark as internal-only |

### Important (blocks production)

| Gap | Impact | Effort | Fix |
|-----|--------|--------|-----|
| No forbidden-claims enforcement | GEOX could output "proven reserves" | 2 days | Add claim classifier with BLOCKED_TERMS list |
| No BLACK risk classification | No safety gate for illegal/fraudulent actions | 1 day | Add risk_band to tool registry |
| No parameter_set recording | Reproducibility incomplete | 1 day | Record all tool params in _envelope |
| No evidence floor classifier | L4 inference could be treated as L1 truth | 2 days | Add epistemic_label to every tool output |
| No explicit auth testing | Unknown if unauthorized actors are blocked | 1 day | Add auth test cases |

### Nice-to-have (post-v1)

| Gap | Impact | Effort |
|-----|--------|--------|
| A2A Agent Cards | Interoperability | 3 days |
| MCP Inspector pass | Standards compliance | 1 day |
| OpenTelemetry traces | Observability | 2 days |
| MCP Apps (map review UI) | UX | 1 week |
| Full data ingest layer (DLIS, LIS, RESQML, WITSML) | Format coverage | weeks |

## Production Readiness Score

```
Protocol Health:        ████████░░ 85%
Domain Correctness:     ███████░░░ 70%
Governance:             ████████░░ 75%
Reproducibility:        ██████░░░░ 60%
Civilizational Safety:  ███████░░░ 70%
                        ─────────────────
Overall:                ███████░░░ 72% → YELLOW
```

## Architecture Verdict

Arif's specification is **correct**. The architecture is:

```
Human/Agent → arifOS (constitutional) → AAA (display) → Domain organs → MCP tools
```

GEOX is the **Earth evidence organ**, not a standalone system. It produces claims, challenges, uncertainty, and provenance. arifOS governs, routes, judges, and seals. VAULT999 remembers.

The gap is not architecture — it's **integration discipline**. The pieces exist. They need to be connected with the artifact chain envelope on every return, the forbidden-claims classifier, and the evidence floor labels.

## One-Line Verdict

**GEOX is a governed Earth evidence refinery at 72% readiness. The forge is hot. The mould is right. The casting needs 2 more weeks of disciplined integration.**

---

*DITEMPA BUKAN DIBERI — Earth evidence is forged, not given.*
