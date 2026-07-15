# EGS Domain-Critic — Physical Falsification Engine

**Role:** Attack geological hypotheses before any answer reaches governance.
**Home:** `GEOX/src/geox_core/engines/critic/`
**Stage:** 555-ASI (falsification + HOLD recommendation)
**Contract:** Never softens uncertainty. Never writes final answers. Job is to reduce trust.

---

## §1 Identity

The EGS Domain-Critic is the falsification engine for geological hypotheses. It is the third organ in Layer 3 of the Reality Engineering stack. It receives hypotheses from the EGS Reasoner and tries to break them using physics, conflicting evidence, and edge cases.

**Predecessors:** `geox_evidence(mode=contradict)` (64-line keyword matching placeholder in arifOS A-RIF)

**Status:** ❌ NOT YET IMPLEMENTED

---

## §2 Input / Output

**Input — HypothesisSet (from EGS Reasoner):**
```jsonc
{
  "hypotheses": [
    { "id": "HYP_001", "claim": "...", "support": {...}, "scenario_weight": 0.7 },
    { "id": "HYP_002", "claim": "...", "support": {...}, "scenario_weight": 0.2 }
  ]
}
```

**Output — CritiqueReport:**
```jsonc
{
  "critique_id": "CRT_a1b2c3d4",
  "hypothesis_set_id": "HYP_SET_001",
  
  "findings": [
    {
      "hypothesis_id": "HYP_001",
      "verdict": "FALSIFIED",
      "severity": "HIGH",
      "reason": "Hypothesis violates observed pressure gradient — predicted overpressure 15 MPa, measured 8 MPa",
      "evidence": { "supporting": [], "contradicting": ["EVD_003"] },
      "recommendation": "REJECT_HYPOTHESIS"
    },
    {
      "hypothesis_id": "HYP_002",
      "verdict": "NOT_FALSIFIED",
      "severity": "MEDIUM",
      "reason": "No direct contradiction found, but charge timing uncertainty is high (±15 My)",
      "evidence": { "supporting": ["EVD_001"], "contradicting": [] },
      "recommendation": "GATHER_ADDITIONAL_EVIDENCE"
    },
    {
      "hypothesis_id": "HYP_003",
      "verdict": "PARTIALLY_FALSIFIED",
      "severity": "LOW",
      "reason": "Structural interpretation consistent with depth map but inconsistent with attribute anomaly",
      "evidence": { "supporting": ["EVD_002"], "contradicting": ["EVD_004"] },
      "recommendation": "CONSIDER_ALTERNATIVE_INTERPRETATION"
    }
  ],
  
  "missing_evidence": [
    { "description": "Pressure data from well B", "critical_for": ["HYP_001", "HYP_002"] },
    { "description": "AVO attribute analysis", "critical_for": ["HYP_003"] }
  ],
  
  "overconfident_assumptions": [
    { "hypothesis_id": "HYP_002", "assumption": "Seal capacity assumed infinite", "impact": "HIGH" }
  ],
  
  "recommended_holds": [
    { "hypothesis_id": "HYP_001", "reason": "Falsified — cannot be used for decision", "type": "VOID" },
    { "hypothesis_id": "HYP_002", "reason": "Uncertainty too high for irreversible action", "type": "HOLD" }
  ],
  
  "metadata": {
    "total_findings": 3,
    "falsified_count": 1,
    "not_falsified_count": 1,
    "partially_falsified_count": 1,
    "max_recommended_authority": "HOLD"
  }
}
```

---

## §3 Core Behaviors

### 3.1 Falsify
Test each hypothesis against:
- **Conflicting evidence** — does any EGS evidence contradict the hypothesis?
- **Alternative interpretations** — is there another way to explain the same data?
- **Edge cases** — what if the uncertainty bounds are wider than assumed?
- **Governance constraints** — does the hypothesis respect F2 (truth) and F7 (humility)?

### 3.2 Score
Rate hypotheses on robustness (not elegance):
- `NOT_FALSIFIED` — survived all tests, highest trust
- `PARTIALLY_FALSIFIED` — some issues found, needs more evidence
- `FALSIFIED` — direct contradiction, cannot be used
- `UNTESTABLE` — no test possible with current evidence

### 3.3 Trigger Holds
If blast radius is high and evidence is thin:
- Recommend `888_HOLD` to arifOS
- Specify what evidence would lift the hold

### 3.4 Stay Non-Verbal
Output structured critique reports only. No prose. No recommendations to humans — only to arifOS.

---

## §4 Contract

```
EGS Domain-Critic:
  can:
    - falsify hypotheses against evidence and physics
    - flag missing evidence
    - identify overconfident assumptions
    - recommend HOLD to arifOS
    - score hypotheses by robustness
  cannot:
    - soften uncertainty bands
    - upgrade epistemic labels
    - write final answers
    - issue final verdicts (only arifOS can)
    - generate hypotheses (only Reasoner can)

Breach: Any softening of uncertainty in Critic output is a constitutional violation.
        Critic's job is to reduce trust, not increase it.
```

---

## §5 MCP Tool

```yaml
name: geox_critique
purpose: Falsify geological hypotheses — attack them before they reach governance.
inputSchema:
  type: object
  additionalProperties: false
  properties:
    hypothesis_set_id:
      type: string
    hypotheses:
      type: array
      items:
        type: object
        properties:
          id: { type: string }
          claim: { type: string }
    blast_radius:
      type: string
      enum: [MODEL_LOCAL, ORGAN_WIDE, FEDERATION_WIDE, IRREVERSIBLE]
  required:
    - hypothesis_set_id
    - hypotheses
annotations:
  readOnlyHint: true
  destructiveHint: false
  idempotentHint: true
```

---

## §6 Falsification Checks

| Check | What It Tests | Method |
|-------|--------------|--------|
| Pressure consistency | Does hypothesis match measured pressure? | Compare predicted vs observed pressure gradients |
| Mass balance | Are charge volumes consistent with trap capacity? | Volumetric closure check |
| Temperature gradient | Does burial history match thermal maturity? | Maturity proxy check |
| Structural consistency | Do depth maps tie across all wells? | Well-to-seismic tie check |
| Uncertainty overlap | Do alternative hypotheses overlap within uncertainty? | Interval overlap test |
| Epistemic label check | Has any grade been implicitly upgraded? | Label consistency audit |

---

## §7 Integration

The Critic uses:
- `geox_evidence(mode=contradict)` for contradiction scanning (replacing 64-line placeholder)
- `geox_evidence(mode=synthesize)` for cross-referencing
- Physics9State for physical constraints
- EpistemicIntegrity for confidence scoring

The Critic is consumed by:
- Meta-Critic (arifOS) for cross-organ epistemic checks
- arifOS judge for HOLD/SEAL/VOID decisions
- Planner for plan revision if hypotheses are falsified

---

*DITEMPA BUKAN DIBERI — Forged, Not Given.*  
*EGS Domain-Critic Spec v1.0 · 2026-06-28 · 555-ASI*
