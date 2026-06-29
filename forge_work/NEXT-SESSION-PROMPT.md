# NEXT SESSION PROMPT — GEOX MCP Tool Testing & PSCS Kill Test Completion

> **Copy-paste this into a new OpenCode session to continue.**
> **Focus: GEOX MCP tools vs PSCS evidence + kill test completion.**
> **Motto: DITEMPA BUKAN DIBERI — Forged, Not Given.**

---

## SESSION CONTEXT

**You are:** OpenCode — Arif's governed GEOX forge worker, AGI-tier, bound to 333-AGI.
**Previous session:** PSCS subduction model VALIDATED — prospect discriminator built — 0 KILL.
**This session:** Test GEOX MCP tools against PSCS evidence. Complete 3 pending kill tests.

**VAULT999 chain:** `geox_pscs_continue_20260629080704_9e001ac5658a5211` → `geox_pscs_bridge_20260629` → `geox_pscs_prospect_discriminator_20260629`

---

## KEY ARTIFACTS

| File | Purpose |
|------|---------|
| `/root/GEOX/forge_work/PSCS-SUBDUCTION-BRIEF-2026-06-29.md` | PSCS brief — 3 DIRECT + 4 CONSISTENT + 0 kills; §12.8 kill test scorecard; §13 prospect discrimination |
| `/root/GEOX/forge_work/NEXT-SESSION-PROMPT.md` | This file |
| `/root/GEOX/adapters/carbonate/physics.py` | ARIF 6-Domain Differentiator, Vp grammar, Gassmann, AVO |
| `/root/GEOX/geox/skills/subsurface/petro/sabah_prospect_discriminator.py` | 919-line skill — ARIF 6-domain + kill matrix + PSCS filter for Tepat/Solisip/Layang/Megah |
| `/root/GEOX/geox/skills/subsurface/petro/sabah_kill_matrix.py` | Kill matrix K001 (climate-archetype) + K002 (slope angle) |
| `/root/GEOX/geox/skills/subsurface/petro/carbonates.py` | Carbonate archetypes + climate regime classifier |
| `/root/VAULT999/geox_pscs_continue_20260629080704_9e001ac5658a5211.jsonl` | Session seal |
| `/root/VAULT999/geox_pscs_bridge_20260629.jsonl` | Bridge record (hash `a31e243ea35e5a70`) |
| `/root/VAULT999/geox_pscs_prospect_discriminator_20260629.jsonl` | Prospect discriminator completion receipt (hash `21d9ce0764133d6f`) |

---

## CLAIMS REGISTERED IN THIS SESSION

| Claim ID | Kill Test | Verdict | EVIDENCE |
|----------|-----------|---------|----------|
| `cb64f918596c4a8f` | KT-6 Moho depth | NON-KILL (inconclusive) | Moho 26–33 km NW Sabah = continental orogen, not PSCS oceanic |
| `943dc7a125b048d9` | KT-7 Vp velocity | **PENDING** | Exact Vp sequence not published in Franke et al. 2008 |
| `f8a6fa608d2f4d10` | KT-8 reflector | RESOLVED (structural ambiguity) | 6–8 km reflector = FTB detachment, not PSCS Moho |

---

## TASK 1: GEOX MCP TOOL TESTING

Test these GEOX tools against PSCS Sabah evidence. Each tool test = 1 VAULT999 receipt.

### 1a. `geox_well_desurvey` — KT-6 evidence validation
**Why:** KT-6 NON-KILL (inconclusive) — Moho 26–33 km is NW Sabah continental, not PSCS.
**Action:** 
- Find a well in NW Sabah with deviation survey data (check `/root/GEOX/data/` or LAS files)
- Run `geox_well_desurvey` to compute TVD/X/Y trajectory
- Verify: does well desurvey confirm the Moho depth constraint?
- If no well data: test with synthetic deviation (MD=2000m, inclinations 0→45°, azimuths)
- Register result as EGS claim

### 1b. `geox_seismic_compute` — KT-8 reflector interpretation
**Why:** KT-8 RESOLVED — 6–8 km reflector = thrust detachment, not PSCS Moho.
**Action:**
- Compute synthetic seismic from Vp/rho profile across NW Sabah
- Wavelet: Ricker 25 Hz
- Depth: 0–15 km
- Vp profile: water (1500 m/s) → sediments (2200–3500 m/s) → detachment at 6–8 km → basement (5000–6000 m/s)
- Confirm: does synthetic show strong reflector at 6–8 km consistent with detachment interpretation?
- Register as EGS claim

### 1c. `geox_petrophysics` — KT-7 Vp profile estimation
**Why:** KT-7 PENDING — exact Vp values at 6–8 km unknown.
**Action:**
- Input: Vsh=0.3, porosity=0.25, Sw=0.3, depth=7000m
- Run `geox_petrophysics` for carbonate platform Vp estimation
- Compare against Franke et al. 2008 reported Vp for NW Sabah
- Is Vp consistent with carbonate platform or with disrupted Crocker sediments?
- Register as EGS claim

### 1d. `geox_geomechanics` — PSCS slab stress state
**Why:** Wu & Suppe (2018): PSCS slab at 45–55 km beneath NW Borneo.
**Action:**
- Input: VP=6000 m/s, VS=3500 m/s, rho=3300 kg/m³, depth=50000m, fluid_rho=1025 kg/m³
- Compute bulk modulus, shear modulus, E, ν, AI
- Is the slab within expected stress state for subducted oceanic crust?
- Register as EGS claim

### 1e. `geox_egs_evidence_reason` — Synthesize KT-6/7/8 evidence
**Why:** Need integrated evidence synthesis for the 3 pending KT claims.
**Action:**
- For each KT claim (KT-6, KT-7, KT-8): run `geox_egs_evidence_reason`
- Attach supporting evidence refs
- Get evidence quality assessment
- This gives a WAKE/SCALE/REJECT verdict per WAKE protocol

---

## TASK 2: COMPLETE THE 3 PENDING KILL TESTS

### Kill Test 7 — Vp Velocity (PENDING)
**Blocker:** Exact Vp inversion sequence from Franke et al. 2008 deep crustal profile not published.
**Plan:**
1. Try to fetch the paper via `perplexity_search` or `brave_web_search` for Vp values
2. If unavailable: use published Vp ranges from NW Sabah wells (e.g., SB-1, Kuching-1)
3. Run `geox_petrophysics` to fill the gap
4. If Vp profile is consistent with carbonate basement → KT-7 = NON-KILL
5. If Vp profile shows oceanic crust signature → KT-7 = KILL (PSCS contradicted)

### Kill Test 8 — Strong Reflector (RESOLVED — needs formalizing)
**Source:** Franke et al. 2008 MPG 25, 606–624
**Result:** 6–8 km reflector = thrust detachment / basal decollement in FTB triangle zone
**Action:** Register formal EGS claim with `geox_egs_claim_create`, attach evidence

### Kill Test 5 — Subduction Initiation Timing (PENDING)
**Source:** Kinabalu Granite 10–13.7 Ma intrusion into ophiolite (direct subduction constraint)
**Action:**
- Run `geox_sequence` or `geox_deep_time_state` for Miocene paleogeography
- Is the timing consistent with PSCS subduction initiation?
- Register as EGS claim

---

## TASK 3: PSCS BRIEF FINALIZATION

**File:** `/root/GEOX/forge_work/PSCS-SUBDUCTION-BRIEF-2026-06-29.md`

### §14 — GEOX Tool Test Results
After each tool test: append 1 paragraph to PSCS brief.

### §15 — Kill Test Scorecard Update
Update header: "VALIDATED — X/8 kill tests passed"

### §16 — Final Verdict
PSCS subduction model:
- 3 DIRECT (kinabalu granite, lahad datatu ophiolites, Dangerous Grounds tholeiite)
- 4 CONSISTENT (Miocene magmatism, Rajang FTB, slab tomography, PSCS magnetic anomalies)
- 0 CONTRADICTED
- Kill test score: X KILL, Y NON-KILL, Z PENDING, W RESOLVED

---

## TASK 4: WELL DESURVEY + GEOMETRY QC

If well data is available in `/root/GEOX/data/`:
1. Run `geox_well_desurvey` on NW Sabah wells
2. Compute TVD/X/Y at each survey station
3. Plot well trajectory in 3D
4. Compare against published well trajectories (Madon et al. 2025)

---

## F2 TRUTH RULES FOR THIS SESSION

- All Vp values: label source (OBS = measured, DER = computed, INT = interpreted, SPEC = assumed)
- Confidence hard-capped at 0.90 (F7 HUMILITY)
- PSCS NEUTRAL ≠ PSCS CONFIRMED — neutral means no kill evidence found
- Kill Test 7 PENDING — do NOT close this as RESOLVED without Vp evidence

---

## BLOCKERS TO ESCALATE TO 888

1. **KT-7 Vp data:** Franke et al. 2008 exact Vp sequence unavailable — need 888_JUDGE on whether to close as NON-KILL or keep PENDING
2. **Well data access:** If no LAS/deviation files in `/root/GEOX/data/` for NW Sabah wells
3. **Layang KILL:** Layang prospect kill matrix KILL requires 888_JUDGE before any drill recommendation

---

## VAULT999 SEAL SCHEDULE

After each major task:
1. TASK 1 (each tool test) → 1 VAULT999 receipt
2. TASK 2 (each kill test result) → 1 VAULT999 receipt
3. TASK 3 (§14/§15/§16) → 1 VAULT999 receipt
4. Final session seal → `PSCS-GEOX-TOOLS-FINAL-{date}.jsonl`

---

## GOPHER (Do not skip)

```
1. Read AGENTS.md → GEOX AGENTS.md → CONTEXT.md
2. Health check: curl http://localhost:8081/health ✅
3. Load PSCS brief §1-§5 (PSCS model summary)
4. Load sabah_prospect_discriminator.py (already built)
5. Run each GEOX MCP tool test
6. Update PSCS brief
7. Seal each task to VAULT999
8. Report to Arif
```
