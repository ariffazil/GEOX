# WEALTH — Capital Organ
> arifOS Federation | Repo: `ariffazil/wealth` | 2026-06-10
> Authority: Tier 2 — explicit Arif approval for all capital moves

---

## What WEALTH is

WEALTH is the **capital domain organ** of the arifOS federation. It computes economic evaluation — NPV, IRR, EMV, risk-adjusted returns, capital allocation. It does not compute geoscience. It does not issue governance verdicts. It is not an unchecked allocator.

**Every capital commitment decision requires Arif explicit authorisation. Non-negotiable.**

---

## Core responsibilities

| Responsibility | Description |
|----------------|-------------|
| Economic evaluation | NPV, IRR, EMV — standard upstream economic metrics |
| Capital risk modelling | Probabilistic range on economic outcomes given input uncertainty |
| Portfolio allocation | Multi-asset capital allocation under constraints |
| Scenario evaluation | What-if analysis on price, cost, production assumptions |
| Economic output envelope | Governed JSON — same envelope philosophy as geox |

---

## What WEALTH requires as input

WEALTH computes economics on top of **geoscience evidence**. It is downstream of geox.

Input chain:
```
geox (volumes, POS, uncertainty) → wealth (NPV, IRR, EMV, risk) → Arif (decision)
```

If wealth receives inputs without geox provenance → flag `UNANCHORED_ECONOMICS`. Do not compute as if inputs are validated.

---

## Hard rule: not an unchecked allocator

WEALTH computes what the economics **look like**. It does not decide what to **do**.

```
WEALTH: "The P50 NPV is X, the EMV is Y, downside is Z."
Arif: "We invest / we don't / we defer."
```

Any WEALTH output that claims to make a capital allocation decision without Arif authorisation → governance violation → escalate to arifOS.

---

## Copilot routing rules

**Route to WEALTH when:**
- NPV / IRR / EMV calculation is needed
- Capital risk range needs to be quantified
- Portfolio allocation across multiple assets is being evaluated
- Economic scenario sensitivity is needed

**WEALTH does NOT handle:**
- Geoscience computation → geox
- Identity verification → AAA
- Build/deploy → A-FORGE
- Governance verdicts → arifOS
- Human readiness → well

---

## GEOX Copilot output when WEALTH context applies

```
WEALTH_BOUNDARY: Economic evaluation is a WEALTH organ responsibility.
Required inputs: geox provenance (volumes, POS, uncertainty bands)
Authority required: Tier 2 — Arif explicit approval for capital commitment
GEOX cannot compute NPV/IRR/EMV — route to WEALTH with geox outputs attached.
```

---

## Relationship with geox

WEALTH is the **consumer** of geox outputs. The flow:

1. geox computes: STOIIP, recovery factor, POS, uncertainty bands
2. geox issues: `claim_state` (SEAL / PLAUSIBLE / HYPOTHESIS) + `ACRisk`
3. WEALTH receives geox envelope
4. WEALTH applies economic parameters (price, cost, fiscal regime)
5. WEALTH outputs: EMV = POS × NPV_success − (1−POS) × cost_dry

If geox claim_state is `HYPOTHESIS` or `HOLD` → WEALTH must carry that uncertainty forward. Economic outputs from unvalidated geoscience are explicitly labelled `UNANCHORED_ECONOMICS`.

---

## What WEALTH is NOT

- Not a trading system
- Not a banking or treasury system
- Not a replacement for enterprise economic modelling tools
- Not an autonomous investment allocator

WEALTH is a computation surface within a governed federation. Capital decisions remain with Arif.
