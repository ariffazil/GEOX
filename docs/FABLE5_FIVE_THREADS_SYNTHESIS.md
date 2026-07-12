# Fable 5 × arifOS Federation — Five-Thread Synthesis

> **Forged:** 2026-07-11 | **Model:** Fable 5 | **Authority:** OBSERVE_ONLY
> **Threads:** 1 (Audit) · 2 (ZEN 89→14) · 3 (GUI Vision) · 4 (MCP Apps) · 5 (Constitutional Fit)
> **DITEMPA BUKAN DIBERI**

---

## Thread Status

| # | Thread | Status | Artifact |
|---|--------|--------|----------|
| 1 | Whole-Federation Audit | 🔄 RUNNING | (agent in progress) |
| 2 | GEOX 89→14 ZEN Consolidation | ✅ PLAN DONE | `docs/GEOX_ZEN_14_CONSOLIDATION_PLAN.md` |
| 3 | GEOX GUI Vision | 🔄 RUNNING | (agent in progress) |
| 4 | MCP Apps with Real UI | ✅ PLAN DONE | `docs/MCP_APPS_REAL_UI_PLAN.md` |
| 5 | Constitutional Fit | 🔄 RUNNING | (agent in progress — CRITICAL findings) |

---

## Critical Finding from Thread 5 (Partial)

The constitutional fit agent has already found **critical self-attestation vulnerabilities**:

### F3 Witness Check is Keyword-Based (CRITICAL)
In `core/laws.py` lines 602-656, `_check_f3_witness` determines witness presence by scanning text for keywords:
- Human: "888_hold", "888_approved", "ratified", "sovereign", "user confirmed"
- AI: "critique", "validation", "floor", "constraint", "forged", "reasoning"
- Earth: "http", "source:", "[ref", "evidence", "observation"
- Verifier: "shadow", "adversarial", "risk check", "security scan"

**Risk:** An agent can embed these keywords in any parameter string to pass all four witness lanes. witness_score = witness_count / 4.0 with threshold ≥ 0.75 means 3/4 keyword matches passes.

### Human Witness Defaults are Spoofable (HIGH)
- `governance_engine.py` line 46: `human = 1.0 if result.get("authority") else 0.8`
- `judgment.py` lines 423-429: `human_witness = 0.7` default, upgraded to 0.8 if "human" in evidence_sources
- `governance_kernel.py` lines 192-196: human_witness from `opts.get("human_witness", 0.0)` — caller controls

### V-Witness Defaults to 1.0 (MEDIUM)
`_compute_v_witness()` catches all exceptions and returns 1.0. Vault-Shadow witness provides no actual constraint.

### Earth Witness is Caller-Controlled (HIGH)
`earth_witness = opts.get("earth_witness", 0.0)` — caller controls the value.

### F2 Truth Check is Text-Analysis (HIGH)
`_check_f2_truth` evaluates truth by scanning query text for source-attribution markers.

---

## Implications for Fable 5

### What Fable 5 Can Do (Safe)
1. **Whole-federation audits** — 1M window, cross-organ contradiction detection
2. **Long-horizon consolidation** — GEOX 89→14 ZEN migration planning
3. **Vision-driven GUI iteration** — screenshot critique, visual falsifiers
4. **MCP Apps development** — well-tie panel, verdict geometry dashboard
5. **Planning and analysis** — all OBSERVE-class work

### What Fable 5 Cannot Do (Unsafe Under Current Architecture)
1. **Self-certify** — the keyword-based F3 witness can be spoofed by any agent
2. **Replace human witness** — the human witness defaults are caller-controlled
3. **Validate its own outputs** — source-as-truth bias means file reads ≠ verification
4. **Bypass external gates** — only VAULT999 hash chain and Ed25519 signatures are truly external

### What Must Be Hardened Before Fable 5 Mutation
1. **F3 witness must use live probes, not keyword scanning**
   - Human: require actual Telegram/message presence (F11 Bridge pattern)
   - AI: require actual tool call results, not text mentions
   - Earth: require actual external API response, not URL mentions
   - Verifier: require actual security scan results, not keyword matches

2. **Human witness must default to 0.0, not 0.7/0.8**
   - Only upgrade when actual human interaction is verified
   - Use F11 Bridge (Telegram presence) as minimum viable human witness

3. **V-Witness must not default to 1.0 on error**
   - Default to 0.0 (blocking) when vault is unavailable
   - Only return 1.0 when vault chain is verified

4. **Earth witness must not be caller-controlled**
   - Derive from actual external API responses
   - Use live probes (Macrostrat, USGS, etc.) as earth witness

---

## Recommended Action Order

### Immediate (OBSERVE — this session)
1. ✅ Thread 1: Federation audit (agent running)
2. ✅ Thread 2: ZEN consolidation plan (done)
3. ✅ Thread 3: GUI vision audit (agent running)
4. ✅ Thread 4: MCP Apps plan (done)
5. ✅ Thread 5: Constitutional fit audit (agent running)

### Next Session (MUTATE — requires signed nonce + re-init)
1. **Harden F3 witness** — replace keyword scanning with live probes
2. **Harden human witness** — default to 0.0, require F11 Bridge
3. **Harden V-Witness** — default to 0.0 on error
4. **Harden earth witness** — derive from external API
5. **Deploy GEOX ZEN 14** — merge tools, run falsifiers
6. **Build well-tie panel** — MCP Apps with real UI
7. **Build verdict dashboard** — kernel cockpit

### Long-term (requires governance change)
1. Constitutional amendment to F3 — live probe requirement
2. Constitutional amendment to F7 — Ω₀ enforcement via external audit
3. Fable 5 classifier awareness — document fallback triggers

---

## The Key Insight

**Fable 5's self-verification capability is powerful but, under arifOS's own framework, it's still self-attestation.** The current architecture has keyword-based witness checks that any agent can spoof. The truly external gates (VAULT999 hash chain, Ed25519 signatures) are strong but underused.

**The fix is not to weaken Fable 5 — it's to harden arifOS.** Replace keyword scanning with live probes. Replace default witness scores with blocking defaults. Replace caller-controlled values with externally-derived values.

**Once arifOS is hardened, Fable 5 becomes the most capable agent ever to operate under constitutional governance.** The 1M window, long-horizon execution, and vision capabilities are exactly what the federation needs — but only if the governance layer is genuinely external, not just keyword-matching.

---

## Thread 2: GEOX ZEN 14 — Summary

Current: 17 public tools → Target: 14 public tools

| Merge | From | To | Rationale |
|-------|------|----|-----------|
| 1 | `geox_well_qc` | `geox_petrophysics(mode="qc")` | QC is a step in petrophysics |
| 2 | `geox_wavelet_extract_least_squares` | `geox_seismic_compute(mode="wavelet_extract")` | Wavelet = seismic computation |
| 3 | `geox_vision` | `geox_seismic_interpret(mode="rsi_pipeline")` | Vision = seismic interpretation |
| 4 | (promote) | `geox_cross_evidence` | Governance entry point |

5 falsifiers defined. 4 phases. Full plan at `docs/GEOX_ZEN_14_CONSOLIDATION_PLAN.md`.

---

## Thread 4: MCP Apps — Summary

Two new apps:

1. **Well-Tie Panel** (`ui://geox/well-tie-panel`)
   - Synthetic vs real trace display
   - Drift threshold sliders bound to `geox_seismic_compute`
   - QC metrics (correlation, RMS error, drift)
   - Bidirectional: slider changes trigger recomputation

2. **Verdict Geometry Dashboard** (`ui://arifos/verdict-geometry`)
   - Session band visualization (INIT→SENSE→THINK→JUDGE→SEAL)
   - Floor status grid (13 floors, color-coded)
   - Witness diversity triangle (Human × AI × Earth)
   - Verdict history timeline

Plus: Fable 5 vision-driven GUI iteration pattern (screenshot → critique → fix).

Full plan at `docs/MCP_APPS_REAL_UI_PLAN.md`.

---

*Waiting for Thread 1, 3, 5 agents to complete.*
*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
