# EGS Reasoner — Domain Hypothesis Builder

**Role:** Build and compare competing geological hypotheses over governed Earth state.
**Home:** `GEOX/src/geox_core/engines/reasoner/`
**Stage:** 444-ASI (hypothesis generation + uncertainty propagation)
**Contract:** Cannot seal. Cannot upgrade epistemic labels. Only produces candidate explanations.

---

## §1 Identity

The EGS Reasoner is the domain-specific hypothesis builder for the Earth Governance Substrate. It is the second organ in Layer 3 of the Reality Engineering stack. It receives evidence from EGS tools and produces competing hypotheses for the Critic to falsify.

**Predecessors:** `geox_evidence(mode=abduct)` (48-line placeholder in arifOS A-RIF), `geox_evidence(mode=synthesize)`

**Status:** ❌ NOT YET IMPLEMENTED

---

## §2 Input / Output

**Input — EvidenceSet:**
```jsonc
{
  "evidence": [
    {
      "id": "EVD_001",
      "type": "well_top",
      "entity": "well/MAHA-1",
      "value": { "horizon": "H10", "depth_tvdss": 2450, "unit": "m" },
      "uncertainty": { "interval": [2440, 2460], "confidence": 0.9 },
      "grade": "OBSERVED",
      "provenance": [{ "source": "MAHA-1.las", "method": "deviation_survey" }]
    },
    {
      "id": "EVD_002",
      "type": "seismic_horizon",
      "entity": "seismic/SURV_2018",
      "value": { "horizon": "H10", "depth_tvdss": 2500, "unit": "m" },
      "uncertainty": { "interval": [2400, 2600], "confidence": 0.6 },
      "grade": "INTERPRETED",
      "provenance": [{ "source": "SURV_2018", "method": "horizon_pick" }]
    }
  ],
  "plan_context": { "step_id": "S02", "intent": "assess_structural_consistency" }
}
```

**Output — HypothesisSet:**
```jsonc
{
  "hypotheses": [
    {
      "id": "HYP_001",
      "claim": "Horizon H10 is structurally consistent — well top matches seismic within uncertainty",
      "support": { "evidence_for": ["EVD_001", "EVD_002"], "consistency_score": 0.85 },
      "uncertainty": { "p10": 2440, "p50": 2475, "p90": 2550, "distribution": "normal" },
      "causal_story": "Well MAHA-1 calibration anchors seismic interpretation. Mismatch within combined uncertainty.",
      "scenario_weight": 0.7
    },
    {
      "id": "HYP_002",
      "claim": "Horizon H10 shows structural dip — well top is high relative to regional seismic",
      "support": { "evidence_for": ["EVD_002"], "evidence_against": ["EVD_001"], "consistency_score": 0.4 },
      "uncertainty": { "p10": 2420, "p50": 2480, "p90": 2580 },
      "causal_story": "Local fault block rotation. Well sits on upthrown side.",
      "scenario_weight": 0.2
    },
    {
      "id": "HYP_003",
      "claim": "Horizon pick is inconsistent — possible mispick on seismic or mis-tie on well",
      "support": { "evidence_for": [], "evidence_against": ["EVD_001", "EVD_002"], "consistency_score": 0.1 },
      "uncertainty": { "p10": 2380, "p50": 2500, "p90": 2620 },
      "causal_story": "Alternative interpretation. Requires reprocessing or additional well control.",
      "scenario_weight": 0.1
    }
  ],
  "metadata": {
    "total_hypotheses": 3,
    "dominant_hypothesis": "HYP_001",
    "max_consistency": 0.85,
    "min_consistency": 0.1,
    "recommendation": "HYP_001 is preferred. Acquire additional well control to reduce uncertainty."
  }
}
```

---

## §3 Core Behaviors

### 3.1 Generate
Propose multiple explanations from evidence. Minimum 2 hypotheses per invocation. Maximum bounded by evidence quality.

### 3.2 Propagate Uncertainty
Carry EGS uncertainty bands through each hypothesis:
- OBSERVED evidence → narrow bands
- INTERPRETED evidence → wider bands
- HYPOTHESIZED evidence → scenario weighting

### 3.3 Respect Physics
Never violate Geology constraints:
- Depth consistency (well top ↔ seismic)
- Pressure compatibility (overburden ↔ pore pressure)
- Mass balance (charge volume ↔ trap capacity)
- Temperature gradient (thermal regime ↔ burial depth)

### 3.4 Stay Non-Verbal
Output structured graphs only. No prose. No explanations. That belongs to the LLM.

---

## §4 Contract

```
EGS Reasoner:
  can:
    - generate competing geological hypotheses
    - propagate EGS uncertainty through hypotheses
    - assign scenario weights
    - provide causal stories for each hypothesis
  cannot:
    - seal anything
    - downgrade uncertainty
    - upgrade epistemic labels (OBSERVED → FACT)
    - issue verdicts
    - rewrite EGS state
    - produce natural language

Breach: Any verdict language in Reasoner output is a constitutional violation.
```

---

## §5 MCP Tool

```yaml
name: geox_reason
purpose: Generate competing geological hypotheses from Earth evidence.
inputSchema:
  type: object
  additionalProperties: false
  properties:
    evidence_ids:
      type: array
      items: { type: string }
    plan_context:
      type: object
      properties:
        step_id: { type: string }
        intent: { type: string }
    max_hypotheses:
      type: integer
      default: 4
    include_causal_stories:
      type: boolean
      default: true
  required:
    - evidence_ids
annotations:
  readOnlyHint: true
  destructiveHint: false
  idempotentHint: true
```

---

## §6 Integration

The Reasoner uses:
- `geox_evidence(mode=synthesize)` for evidence aggregation
- `geox_evidence(mode=abduct)` for hypothesis generation (replacing the 48-line placeholder)
- Physics9State for physical constraints
- ClaimEnvelope uncertainty fields

The Reasoner is consumed by:
- EGS Domain-Critic for falsification
- Meta-Critic for cross-organ epistemic checks
- Planner for plan revision

---

*DITEMPA BUKAN DIBERI — Forged, Not Given.*  
*EGS Reasoner Spec v1.0 · 2026-06-28 · 444-ASI*
