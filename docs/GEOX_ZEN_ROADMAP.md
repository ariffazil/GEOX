# GEOX Zen Roadmap

> **SOT for surface calm.** Forged from live session `SEAL-51a63024e73c45e0` + multi-model witness (Claude / ChatGPT).  
> **Law:** geometry schema → renderer → (maybe never) interactive editor.  
> **Test of zen:** fresh agent, no priming: `arif_init` → `geox_interpret` → gated, rendered, hash-stamped `QUALIFIED_CANDIDATE`.

DITEMPA BUKAN DIBERI.

---

## 0. Two loops (do not conflate)

| Loop | Needs | Does **not** need |
|------|--------|-------------------|
| **Machine** | Structured geometry I/O (Section, Horizon, Fault, Calibration, Bundle). Pick in coords → gate coords → challenge coords. | Interactive GUI (degrades agents back to pixels) |
| **Human (F13 veto)** | Deterministic **renderer**: section + picks → PNG/SVG with receipt hash burned in | Full pick-editor on day one |

ChatGPT's annotated PNG felt "more finished" than an un-rendered gate matrix. That was **presentation**, not capability. Both models' picks were `UNMEASURED` hypotheses. The **disagreement** (N-dipping normal flank segmentation vs reverse pop-up/flower) is the valuable multi-witness artifact — exactly what K-DIP/K-THROW exist to adjudicate once VE/T–D exist.

**Epistemic rule:** vision polarity conflict without measurement = multi-hypothesis input, not a scoreboard. Weightings without physics are vibes.

---

## 1. Priority order (locked)

1. **Geometry schema** — one noun set in/out of every verb *(partial: sticks/name adapters + calibration_derive, 2026-07-24)*  
2. **Renderer** — `render(section, horizons, faults, annotations) → PNG` · matplotlib · auto at end of interpret  
3. **Interactive pick-editor** — later luxury; only when hand-correction beats counter-prompt  

---

## 2. Zen surface (target ~8 capability verbs)

| Verb | Absorbs (today) | Role |
|------|-----------------|------|
| `geox_ingest` | well_ingest, seismic_ingest, image, LAS/SEG-Y | One door for data |
| `geox_interpret` | seismic_interpret, visual_* propose | Section / well / map propose |
| `geox_validate` | structure_validate, falsify, contradiction | All gates, any geometry |
| `geox_compute` | petrophysics, geomech, seismic_compute, synthetics | Numbers |
| `geox_render` | **NEW** section overlay; map_render_preview later | Human-loop image |
| `geox_basin` | basin, backstrip, thermal, sequence | Basin story |
| `geox_prospect` | prospect | Screen / evaluate |
| `geox_workspace` | workspace (exists) | Inherit basin/session once |

Modes live **inside** verbs. **Design law (A1 elevated):** unknown mode = **error**, never silent fallback.

Until full collapse: prefer **modes on existing tools** over new public tools (charter). `mode=render` on `geox_seismic_interpret` ships the render verb without growing the 32-tool count.

---

## 3. One noun set

```
Section | Horizon | Fault | Calibration | Bundle
```

Same shapes into and out of every verb. Dialects (sticks vs points vs name vs fault_id) are **adapters only** — never parallel public contracts.

---

## 4. Zen the output

| Return | Rule |
|--------|------|
| Default | `verdict` + one line per gate + receipt hashes + `detail_ref` / inline `detail` on request |
| Full gate physics | On demand (`detail=full` or `detail_ref` fetch) |
| Bundle size | Happy path ~1–3 KB summary, not 30 KB × 3 hyps of boilerplate |

`preferred_hypothesis` stays **null** from GEOX. Local max **QUALIFIED_CANDIDATE**. arifOS seals.

---

## 5. Workspace inheritance

`geox_workspace set basin=malay` (and session/actor/calibration defaults) once.  
Tools inherit — stop threading 40 params every call. (`geox_workspace` already public.)

---

## 6. Tool descriptions = triggers

Bad: "Use when you need basin evidence."  
Good: "User has a 2D seismic section image and wants candidate faults/horizons gated against physics, with a PNG overlay for human review."

---

## 7. Happy path (one call after arif_init)

```
image | SEG-Y
  → propose picks
  → run gates (with calibration if present)
  → render PNG (hash-stamped)
  → QUALIFIED_CANDIDATE bundle (compact)
```

Everything else is refinement (challenge hyp, re-calibrate, falsify claim).

---

## 8. Status

| Item | State |
|------|--------|
| Geometry adapters (sticks/name) | **SHIPPED** 2026-07-24 |
| Calibration derive (B1–B5) | **SHIPPED** 2026-07-24 |
| Mode dispatch no silent fallback | **SHIPPED** 2026-07-24 |
| Deterministic section renderer | **THIS SPRINT** (`mode=render` + auto on interpret) |
| Compact gate envelope | **THIS SPRINT** |
| 32 → ~8 verb collapse | **ROADMAP** (alias layer, no big-bang delete) |
| Interactive editor | **HOLD** |

---

*Witness disagreement without measurement is not failure — it is the input the gate architecture was built for.*
