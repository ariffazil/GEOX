# FUTURE.md — Where GEOX is going, and what it is not

> Companion to `README.md`. Written 2026-11-24 after the Volve maturation audit and the
> external audit of that audit (R1–R11). Numbers here are probes, not projections.

---

## 0. What GEOX is, in one paragraph

Petrel, DSG and Geoteric are **workbenches for human geologists**: a screen, terabytes of
seismic, a person clicking. GEOX is a **physics-and-honesty fence for AI agents**. An agent
asks; GEOX answers with a number *and its label* — measured, derived, interpreted, assumed,
impossible, or unknown. GEOX does not compete with Petrel. It sits beside the agent as a
physics auditor.

**It is not a product yet.** Zero external users, zero paying customers, zero public
case studies written by someone other than its builder. Its present value is the design
discipline and the fact that when challenged from outside, it gets corrected within hours.

---

## 1. Honest scorecard (1–5, builder's own judgement)

| Dimension | GEOX | Petrel / DSG | Geoteric |
|---|---|---|---|
| Physics accuracy on valid input | 4 | 5 | 4 |
| Rejects impossible input (fail-closed) | 3 (was 1 before this week) | 3 | ? |
| Provenance honesty | 3 (DEFAULT tagging now complete; `defaults_applied[]` added) | 2 | 2 |
| Real data held inside the system | **1** (0 seismic cubes; 1 benchmark dataset) | 5 | 4 |
| Seismic / visualisation | 1 | 5 | 5 |
| Agent-ready (MCP) | **4** | 2 | 2–3 |
| Users / revenue | **0 / none** | thousands | 500+ projects |
| Ops resilience | 2 (single host, VAULT timeouts) | 5 | 4 |

Market context: E&P software ≈ USD 11.56 bn in 2026, seismic/subsurface software ≈ 29.3 %
share (~USD 3.4 bn). The space exists and is owned by incumbents. The unfilled slot is a
**neutral verification layer** — nobody sells "force the agent to be honest about the rock".

Valuation is deliberately not stated. There is no market price for a thing nobody has paid
for. What exists is (a) replacement cost — the domain knowledge embedded in 29 tools and
their physics gates — and (b) option value if "physics-grounded agent" becomes a
procurement requirement.

---

## 2. The three horizons

### H1 — 0–3 months: make the fence load-bearing

Goal: an outside engineer can clone, run, and trust the gate without meeting the author.

| Item | Done when |
|---|---|
| Golden Volve suite in CI | `tests/test_golden_volve.py` runs on every push; a regression fails the build, not a review comment |
| One end-to-end pipeline on real data | ingest → QC → petrophysics → geomechanics → volumetrics → decline → report, all through GEOX tools, on a public dataset |
| Output trimmed | <2k tokens of governance metadata per call (currently 3–8k); one verdict per response |
| Source == deploy | `surface_status.deployed_git_sha` equals HEAD, verified by a CI check not a self-report |
| Remaining P0 closed | geox_well `las_path`, lease forwarding, prospect lane documented both ways |

**Kill criterion:** if H1 finishes and still nobody outside has run it, stop adding tools.

### H2 — 3–12 months: one external pilot

Goal: one user who is not the author, on their own data.

- Pilot with a university group or a small operator. Deliverable is *their* dataset run
  through GEOX, with a written verdict they are willing to sign.
- Record every forecast in CHRON and score it. The asset is not the tool — it is the
  **record of how often the tool was wrong**.
- Publish one benchmark: Volve (public, answer-key-backed) and FORCE 2020 (118 wells).
- First revenue question: does anyone pay for calibration, or only for software?

**Honest risk:** the pilot never happens because GEOX has no data and no distribution.
That is the most likely failure mode, and it is a business problem, not a physics problem.

### H3 — 1–3 years: the calibration layer

The defensible position, if H2 succeeds: GEOX knows **how often agent forecasts are wrong
per play type**, because it has the receipts. "Physics gate" is copyable by SLB.
"Calibrated error record per play" is not, because it requires years of honest bookkeeping
and a willingness to publish losses.

**Not promised.** H3 depends on H2, which depends on one person deciding to try it.

---

## 3. Domain transfer (why the physics is reusable)

The same gates apply to CO₂ storage (capacity, seal integrity, pressure limits),
geothermal (heat flow, fracture permeability), and minerals (grade continuity, geomet
uncertainty). The core is: *reject impossible numbers, label the rest*. That does not
depend on hydrocarbons.

---

## 4. What to stop doing

- Stop adding governance metadata no agent consumes (`maruah_flag`, `delta_S`, full `apex`
  blocks inside error payloads).
- Stop letting defaults masquerade as measurements.
- Stop counting tools as a health metric. 29 tools is not maturity.
- Stop calling a smoke test a pass when it only counts successful imports.
- Stop verifying your own work. Author ≠ judge is a floor, not a preference.
- Stop deriving "lessons" from a single case (the v1 report's calibration claim was
  invented from N=1 and was deleted in v2).

## 5. What to keep doing

- Reject, label, and publish the gaps.
- Recompute every headline number from source before shipping it.
- Keep the golden suite adversarial: it should fail on a bad day.

---

## 6. IP and conflict note (not a legal opinion)

GEOX is public and the author is employed by an operator whose vendor is one of the
incumbents named above. Licence terms for the public Volve dataset have changed several
times and must be re-checked before any redistribution. Employment-IP and conflict-of-
interest review is the author's decision, not the agent's.

---

*REALITY > EVERYTHING. Rock does not read documentation; it answers when drilled.*
