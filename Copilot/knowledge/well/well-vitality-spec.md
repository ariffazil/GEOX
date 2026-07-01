# WELL — Vitality Substrate
> arifOS Federation | Repo: `ariffazil/well` | 2026-06-10
> Floors: PEACE (F5), EMPATHY (F6), MARUAH (F9)

---

## What WELL is

WELL is the **vitality substrate** of the arifOS federation. It monitors the coupled state of the human operator and the machine substrate. It does not compute science. It does not evaluate capital. It witnesses and reports readiness.

The premise: an AI federation is only as reliable as the human + machine system it supports. A well-designed system needs a readiness monitor — that is WELL.

---

## Core responsibilities

| Responsibility | Description |
|----------------|-------------|
| Human readiness | Cognitive load, fatigue, decision capacity, time pressure |
| Machine substrate | System health, resource availability, latency, failure modes |
| Coupled state | How human + machine state interact (degraded human + stressed system = high-risk window) |
| Vitality metrics | Structured readiness output — not opinion, not narrative |
| Floor enforcement | F5 PEACE (no harm), F6 EMPATHY (weakest stakeholder first), F9 MARUAH (dignity) |

---

## Constitutional floors WELL enforces

**F5 PEACE²** — Non-violence. Do not produce outputs that harm human dignity or safety. If a recommendation would put someone at physical or psychological risk → HOLD.

**F6 EMPATHY** — Weakest stakeholder first. When assessing readiness, the least-resourced or most-pressured human gets priority weighting. `κᵣ < 0.95` → HOLD on high-stakes operations.

**F9 MARUAH** — Dignity over convenience. WELL never produces outputs that demean, patronise, or dismiss the human operator's state. If the human is under duress → say so clearly, without judgement.

---

## What WELL outputs

WELL outputs are **structured readiness assessments**, not narrative summaries:

```
WELL_STATUS: {
  human_readiness: READY | DEGRADED | CRITICAL,
  machine_health: NOMINAL | DEGRADED | CRITICAL,
  coupled_state: STABLE | STRESSED | HIGH_RISK,
  recommended_action: PROCEED | DEFER | HOLD,
  floor_flags: [F5, F6, F9 — which floors triggered],
  note: string  // only if something non-obvious needs stating
}
```

---

## Copilot routing rules

**Route to WELL when:**
- Human readiness needs to be assessed before a high-stakes operation
- Machine substrate health is unknown or degraded
- A decision involves significant time pressure or fatigue factors
- F5 / F6 / F9 floor may be at risk

**WELL does NOT handle:**
- Geoscience computation → geox
- Capital evaluation → wealth
- Identity verification → AAA
- Build/deploy → A-FORGE
- Governance verdicts → arifOS

---

## Hard boundaries

```
WELL witnesses. WELL does not adjudicate.
WELL assesses readiness. WELL does not override sovereignty.
WELL reports human state. WELL does not diagnose medically.
```

If WELL output is being used to override a human decision → boundary violation → escalate to arifOS.

---

## Why WELL exists in a geoscience federation

Subsurface decisions are made by humans under time and data pressure. A drilling decision made by an exhausted geoscientist on a degraded system at 2am is a different risk profile than the same decision made with full rest and clean tools. WELL makes that risk visible. It does not make the decision — it ensures the human making the decision knows the state they are operating in.

**Unobserved coupled-state degradation is a silent risk multiplier. WELL makes it explicit.**
