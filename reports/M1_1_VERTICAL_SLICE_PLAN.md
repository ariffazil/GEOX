# M1_1_VERTICAL_SLICE_PLAN.md

**Status:** PLAN (not executed). Gate on: GATE B + C sufficiently resolved, and
verified actor OR explicit Arif authorization for the mutation.

---

## 1. Objective

Smallest vertical smoke test proving LoopStructural 1.8.x can drive a 2D restoration
path from synthetic input to a `RestorationBundle` candidate — no more, no less.

## 2. Preconditions (gates)

- GATE B: schema reconciliation accepted (or at least not blocking) — schemas are
  DRAFT_CANDIDATE with 5 dimensions.
- GATE C: synthetic fixture set exists (NOT yet generated — blocked on provenance matrix acceptance).
- `LoopStructural.modelling.features` enumerated (closes the UNKNOWN compatibility rows).

## 3. Vertical slice steps

```
1. synthetic observations (SYNTHETIC_2d_line.json + SYNTHETIC_strat_column.yaml)
   → load via adapter (fail-closed on missing/corrupt input — reject before modelling)
2. GeologicalModel construction (modelling.GeologicalModel)
3. one stratigraphic feature (StratigraphicColumn → surface)
4. one fault relationship (fault feature from modelling.features — TBD after enumeration)
5. output extraction (surface geometry → numpy arrays)
6. provenance hash (sha256 over params — adapter already has _sha256_params)
7. RestorationBundle candidate:
     epistemic_class=HYPOTHESIS
     lifecycle_state=DERIVED_CANDIDATE
     explanation_class=UNCLASSIFIED (NARRATIVE-class — not action-eligible)
     authority_ceiling=QUALIFIED_CANDIDATE
     constitutional_verdict=null
     hypotheses>=3 (one primary + two perturbations)
     preferred_model=null
     provenance=[params hash, fixture hashes]
```

## 4. Invariants exercised in the slice (prepare, do NOT claim passed until run)

- >=3 competing restoration hypotheses (one + 2 perturbations)
- preferred_model stays null
- area-balance check (2D) — compute, report, do not assert pass
- strain threshold — report, do not assert
- datum consistency
- stratigraphic-order preservation (ages monotonic)
- missing velocity/depth → HOLD at authority layer (not fabricated)
- malformed input → reject before modelling
- assumptions + reversal_conditions mandatory (non-empty)
- confidence ceiling <= 0.75 (F7)
- NO hydrocarbon conclusion from restoration alone

## 5. Separation of concerns (do NOT conflate)

- geological validity (expert QC) ≠ software correctness (smoke test) ≠ schema
  conformance (verify_bundle_schemas) ≠ authority decision (arifOS/888).

## 6. Explicitly NOT in this slice

- four-line orchestration
- 3D restoration bundle
- public MCP tool
- UI resource
- pynoddy integration
- deployment

## 7. Stop conditions

- required LoopStructural API absent → HOLD + report
- fixture provenance uncertain → HOLD
- restricted data involved → HOLD
- <3 hypotheses → HOLD
- preferred_model non-null → VOID
- any "SEALED" without arifOS → VOID

## 8. Exit

This is a PLAN. Executing it is a mutation that requires verified actor OR explicit
Arif authorization. Current run exits before execution.
