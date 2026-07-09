# GENESIS/012 — GEOX-001: Model Deserves To Live

> **Benchmark:** Well-Seismic Truth Test  
> **Sealed wedge priority:** FIRST — before basin narrative, prospect volumetrics, or 3D fans  
> **Thesis:** If the well does not tie, the model does not get to speak as truth.

---

## 1. Why this wedge

SLB / Halliburton win on platform breadth: workbench, visualization, data rooms, multi-user interpretation, enterprise contracts.

Their structural weakness:

```text
they let interpretation become reality too easily
```

GEOX-001 attacks that directly. It does not try to out-workbench DS365. It answers one question serious buyers care about:

> **Can GEOX catch when a subsurface interpretation is not supported by the actual well-seismic evidence?**

Attack line (from competitive layer map):

> DS365 tells you where your model lives. GEOX tells you whether your model deserves to live.

---

## 2. Minimum data

| Artifact | Role | Epistemic rung |
|----------|------|----------------|
| 1 LAS file | Sonic + density + GR/RT/NPHI | OBS |
| 1 tops table | Top reservoir pick | INT |
| 1 checkshot / VSP | Time-depth control | OBS |
| 1 seismic line / extract | Observed event | OBS |
| 1 horizon pick | Mapped H1 | INT |
| 1 velocity assumption | T-D model + uncertainty | SPEC |

---

## 3. Workflow

```text
ingest_data
  → QC evidence
  → build evidence graph
  → generate synthetic tie
  → compare well tie vs seismic event
  → classify OBS / DER / INT / SPEC
  → create claim
  → challenge claim
  → falsification scan
  → uncertainty-calibrated verdict
```

**Implementation**

| Layer | Path |
|-------|------|
| Core engine | `src/geox_core/benchmarks/geox_001_well_seismic_truth.py` |
| MCP tool | `geox_benchmark_001` |
| Fixtures | `tests/fixtures/geox_001/` |
| Tests | `tests/benchmarks/test_geox_001_well_seismic_truth.py` |
| CLI | `PYTHONPATH=src python -m geox_core.benchmarks.geox_001_well_seismic_truth --scenario mistie_hold` |

---

## 4. Success condition (all six)

1. QC-verified ingested files  
2. Explicit evidence graph  
3. Synthetic tie / drift result  
4. Claim with OBS / DER / INT / SPEC separation  
5. Active challenge / alternative interpretation  
6. Verdict that can say **PROCEED**, **HOLD**, or **KILL** without pretending certainty  

Missing any one → benchmark incomplete.

---

## 5. Killer receipt (demo shape)

```yaml
claim: "Horizon H1 represents the top reservoir at Well A."
verdict: HOLD
reason:
  - synthetic tie peak is shifted +38 ms from mapped event
  - checkshot drift exceeds threshold
  - GR/resistivity motif supports sand, but density-neutron separation is weak
  - top pick confidence is INTERPRETATION, not OBSERVATION
  - velocity model uncertainty can erase closure
falsification:
  - if revised checkshot still gives >25 ms mistie, kill horizon tie
  - if nearby well top contradicts depth trend, downgrade prospect
next_test:
  - re-pick seismic event around tie window
  - run alternate velocity model
  - attach second well or sidetrack if available
```

That is the thing DS365 does not naturally volunteer.

---

## 6. Verdict gates

| Condition | Verdict | Model lives? |
|-----------|---------|--------------|
| mistie ≤ 8 ms, residual `good_tie`, corr ≥ 0.70 | **PROCEED** | yes (with uncertainty) |
| mistie ≥ 25 ms or checkshot drift high | **HOLD** | no |
| mistie ≥ 40 ms or mistie+offset contradiction | **KILL** | no |
| QC FAIL on required artifacts | **KILL** | no |

Thresholds are explicit, not vibes. Confidence always capped (F7).

---

## 7. Scenarios

| Scenario | Purpose |
|----------|---------|
| `mistie_hold` | Default demo — +38 ms mistie → HOLD |
| `good_tie` | Clean path — model may live |
| `kill_contradiction` | Hard fail — large mistie + nearby top contradiction |

---

## 8. What not to start with

| Candidate | Why later |
|-----------|-----------|
| Malay Basin prospect screening | Narrative too fast |
| Deepwater Sabah amplitude-risk audit | Needs seismic discipline first |
| Carbonate platform uncertainty audit | Facies-specific |
| Mature field bypassed-pay screen | Needs production + petro |
| Full basin-to-prospect loop | Too many moving parts |

---

## 9. Shortest path from prototype to weapon

**One well · one horizon · one seismic tie · one claim · one contradiction.**

Wire Well-Seismic Truth Test first. Everything else builds on the right to believe.

---

*GENESIS 012 · GEOX-001 · 2026-07-09*  
*Depends on: 010 AEI Governance (tie as spine), 011 Competitive Layer Map*  
*DITEMPA BUKAN DIBERI*
