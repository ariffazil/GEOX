# SPEC — geox `strat_datum_check` verb

**Status:** DRAFT for GEOX wiring (validator-endorsed P0, 2026-09-07)
**Root cause it kills:** `geox_well_qc` returned `strat_standard: {scheme: "NN_zone", reference_chart: ""}` — no regional chronostrat datum in the registry, so a ~2 Ma / ~2-zone Neogene error passed every gate. This verb makes the datum a first-class ingest check: the hand-diff the human validator did becomes a machine gate.

## 1. Purpose

At ingest (well tops, zone picks, charts, correlation panels), validate every supplied zone-age pair against a registered regional datum before the evidence is admitted. Detection-at-the-door for chronostratigraphic mispicks.

## 2. Inputs

```json
{
  "mode": "strat_datum_check",
  "datum_id": "nn-borneo-2023",            // optional; default per basin
  "basin_name": "Kinabalu / NW Borneo",
  "boundaries": [                            // supplied table to check
    {"surface": "NN9_base", "age_ma": 8.6},
    {"surface": "NN21-NN9", "age_top_ma": 0.0, "age_base_ma": 8.6, "kind": "group"}
  ]
}
```

Registry side: load `/root/GEOX/data/kl2/nn_datum_borneo2023.yaml` (or per-basin equivalent) as `strat_standard.reference_chart` — the field exists in the evidence envelope today; it must never again return empty for a scheme the registry carries.

## 3. Check logic (ordered, all four run)

1. **Age divergence** — for each supplied boundary present in the ladder: `|age_supplied − age_ladder| > datum.flags.age_divergence_ma` (default 0.5) → `FLAG_AGE_DIVERGENCE` with both values. NN9 supplied 8.6 vs ladder 10.55 = 1.95 Ma → FLAG.
2. **Group-scheme straddle** — any supplied surface whose name spans ladder anchors (matches `forbidden_groups` or lexically covers ≥2 anchored horizons) → `FLAG_GROUP_STRADDLE`. Reason: labels like "NN10-11" invite the Martini-vs-PETRONAS homonym trap (project NN11 = FAD horizon 8.11 Ma ≠ ICS NN11 span 5.6–7.25 Ma).
3. **Ladder seam** — supplied boundaries sorted by age must be strictly monotonic with no overlaps (v1's NN21 base 0.018 vs NN16-20 top 0.012 = 0.006 Ma overlap) → `FLAG_SEAM`. Ladder-native tables (one surface = one age) cannot seam.
4. **Un-anchored interval honesty** — any pick inside a declared `gaps` interval (NN12–15) must carry `ics_fill: true`-equivalent tag + widened σ; untagged → `FLAG_UNANCHORED_UNTAGGED` (F7 line: don't present ICS-fill as regionally calibrated).

## 4. Output (extends the existing GEOX evidence envelope)

```json
{
  "strat_standard": {"scheme": "NN_zone", "reference_chart": "nn-borneo-2023 v2"},
  "datum_check": {
    "verdict": "FLAG | PASS",
    "flags": ["FLAG_AGE_DIVERGENCE:NN9_base 8.6 vs 10.55 (Δ1.95 Ma)"],
    "checked_boundaries": 14, "flagged": 1,
    "humility_score": 0.0
  },
  "next_best_tool": "geox_well_ingest (after flags cleared)"
}
```

Verdict semantics: `FLAG` → evidence admitted as `NO_VALID_EVIDENCE`/`HOLD` (matches current claim_state machinery); `PASS` → ingest proceeds. The verb never mutates supplied data (OBSERVE class).

## 5. Wiring point

Call site: `geox_well_ingest` (tops/zone sheets) and `geox_well_qc` (any `strat_standard` seen in input). One function, two callers — same pattern as PhysicsGuard (`dV/dZ ≤ 50 m/s/m` already enforced there; this is the time-axis sibling of that guard).

## 6. Acceptance tests (must run before wiring — test-then-seal)

| Test | Input | Expected |
|---|---|---|
| T1 — v1 falsified table | NN9 base 8.6, groups NN21-9/NN7-8/NN6/NN5a-b, 0.006 Ma seam | FLAG ×3 (divergence, straddle, seam) |
| T2 — v2 ladder | nn-borneo-2023 boundaries as supplied | PASS, reference_chart populated |
| T3 — untagged NN13 pick | NN13 base 4.0 without ICS-FILL tag | FLAG_UNANCHORED_UNTAGGED |
| T4 — unknown basin | no datum registered | verdict UNKNOWN + explicit "datum not registered" (Void Guard: no-data ≠ all-clear) |

## 7. Non-goals

Does not validate pick DEPTHS (that is velocity/QC territory); does not judge correlation quality; does not replace DSG-side validation of proprietary tops — verdict-only ingress stays the boundary for those.
