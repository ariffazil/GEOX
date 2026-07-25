# GENESIS/018 — Δ·Ω·Ψ GEOX Hardening

**Document ID:** `GEOX/GENESIS/018`
**Voice:** KERNEL / ENFORCE
**Grammar:** Earth-mechanical claim, modality mapping, enforcement rule
**Status:** DRAFT · design target (P1 stamps live in code; 11-field envelope optional enrich)
**Date:** 2026-07-25
**Authority:** Muhammad Arif bin Fazil, F13 SOVEREIGN
**Parent doctrine:** `arifOS/GENESIS/054_DELTA_OMEGA_PSI_MULTIMODAL_COGNITION.md` · `docs/GEOX_DELTA_OMEGA_PSI_MAP.md`
**Parent surface:** `GEOX/GENESIS/013_GEOX_METABOLIC_SURFACE.md`
**Live code:** `ext_witness_stamp.py` · `session_apex.py` · middleware gate · tip `ea2ae0a4+`

---

## 1. GEOX as a Δ Substrate

GEOX is the primary Δ (Python) metabolic engine for earth-evidence. Its role in the Δ·Ω·Ψ architecture:

> **GEOX metabolises multimodal earth inputs into the P (Physics) primitive of G.**

Every tool in GEOX that processes raw earth data is a Δ-substrate pipeline. The LLM never touches raw seismic bytes or LAS curves directly — GEOX decomposes, inspects, and falsifies before any claim enters the federation.

### 1.1 Modality-to-G-primitive mapping (GEOX-specific)

| Modality | Tool(s) | Δ pipeline | G-primitive | Counterpart witness |
|----------|---------|------------|-------------|---------------------|
| Seismic section (image) | `geox_visual_understand`, `geox_seismic_interpret` | numpy → feature extraction → horizon contrast → testable hypotheses | P (Physics) | Ext_witness |
| Seismic volumes (SEG-Y) | `geox_seismic_ingest`, `geox_seismic_compute` | SEG-Y parse → QC → attribute → synthetic | P (Physics) | Ext_witness |
| Well logs (LAS) | `geox_well_ingest`, `geox_petrophysics` | LAS parse → Vsh/phi/Sw → Archie QC → statistical bounds | P (Physics) | Ext_witness |
| Check shots / VSP | `geox_well_tie`, `geox_tie_receipt` | travel-time → drift correction → calibration | P (Physics) | Ext_witness |
| Basin data (Macrostrat) | `geox_basin` | strat columns → backstrip → tectonic reconstruction | P (Physics) | Ext_witness |
| Geomechanics | `geox_geomechanics` | stress polygon → pore pressure → fracture gradient | P (Physics) | Ext_witness |
| Gravity / magnetic | `geox_gravmag_studio` | forward model → prism → anomaly | P (Physics) | Ext_witness |
| Biostratigraphy | `geox_sequence`, `geox_deep_time_state` | marker parse → falsification → age calibration | P (Physics) + E (deep time) | Ext_witness |
| Prospect evaluation | `geox_prospect` | volumetrics → POS → EVOI → risk matrix | P (Physics) + X (Exploration) | Ext_witness |
| Claims / evidence | `geox_claim`, `geox_evidence`, `geox_falsify` | claim graph → contradiction scan → K001-K007 KILL | None (governance surface; evidence gate) | AI_witness (via arifOS) |

### 1.2 Δ-substrate enforcement rule

> **GH-1:** No GEOX tool shall emit a claim rated `SUCCESS` without passing through its Δ-substrate decomposition pipeline. Raw model output is not earth evidence.

> **GH-2:** Every GEOX tool output must carry an Ω-envelope with at minimum: `modality`, `claim_state`, `g_primitive`, `delta_substrate_hash`.

> **GH-3:** The `geox_falsify` tool is the final Δ gate. Any claim that fails Kill-Matrix K001–K007 shall be rejected BEFORE it reaches the kernel.

---

## 2. Ω-Envelope Hardening for GEOX

### 2.1 Required envelope fields

Every GEOX tool output envelope must now carry:

```python
REQUIRED_GEOX_ENVELOPE_FIELDS = (
    "transport_status",       # OK | DEGRADED | FAILED
    "execution_status",       # COMPLETED | REJECTED | ERROR
    "artifact_status",        # OK | ENVELOPE_INCOMPLETE | REJECTED
    "verification_status",    # VERIFIED | UNVERIFIED | FALSIFIED
    "governance_verdict",     # HOLD | PASS | NOMINAL
    "claim_state",            # OBSERVED | DERIVED | INTERPRETED | HYPOTHESIS
    "modality",               # seismic | well_log | basin | gravmag | biostrat | prospect | claim
    "g_primitive",            # P | E | X | null
    "delta_substrate_hash",   # SHA256 of the Δ pipeline code that processed this evidence
    "provenance_chain",       # ordered list of tool names that processed this input
    "contradiction_scan",     # PASS | KILL_<K00N> | UNMEASURED
)
```

### 2.2 Modality tag contract

The `modality` field is a binding contract with the kernel. When GEOX emits a claim with `modality: "seismic"`, the kernel knows:
- This evidence contributes to P (Physics) → G composition
- It must pass through GEOX's Δ substrate (numpy → feature extraction → QC)
- The tri-witness Ext_witness channel is authoritative for this modality
- Cross-modal contradiction scanning applies (seismic vs well log vs gravmag)

### 2.3 G-primitive field

The `g_primitive` field declares which term in G = A·P·E·X·Φ this evidence modifies:

| g_primitive | Meaning | GEOX tools |
|-------------|---------|------------|
| `P` | Physics — earth ground truth | seismic, petrophysics, basin, geomechanics |
| `E` | Energy / deep time | deep_time_state, biostratigraphy |
| `X` | Exploration / prospect | geox_prospect, volumetric assessment |
| `null` | Governance surface (not a G-primitive contributor) | geox_claim, geox_falsify, geox_evidence |

The kernel rejects any tool output claiming to be a G-primitive contributor but lacking `delta_substrate_hash`.

---

## 3. GEOX /health Endpoint Hardening

### 3.1 New `/health` response fields

The GEOX health endpoint must now expose:

```json
{
  "g_primitive_state": {
    "P": {
      "status": "UNMEASURED",
      "confidence": 0.87,
      "degraded_modalities": [],
      "active_pipelines": ["seismic", "well_log", "basin"],
      "stale_since": null
    },
    "E": {
      "status": "UNMEASURED",
      "confidence": 0.72,
      "degraded_modalities": [],
      "active_pipelines": ["deep_time", "biostrat"],
      "stale_since": null
    },
    "X": {
      "status": "UNMEASURED",
      "confidence": 0.65,
      "degraded_modalities": [],
      "active_pipelines": ["prospect_eval"],
      "stale_since": null
    }
  },
  "delta_substrate_health": {
    "pipelines": {
      "seismic": {"status": "healthy", "last_run": "2026-07-25T10:00:00Z"},
      "well_log": {"status": "healthy", "last_run": "2026-07-25T09:45:00Z"},
      "basin": {"status": "healthy", "last_run": "2026-07-24T23:00:00Z"},
      "gravmag": {"status": "degraded", "last_run": null, "warning": "no data ingested"},
      "biostrat": {"status": "healthy", "last_run": "2026-07-25T08:00:00Z"},
      "deep_time": {"status": "healthy", "last_run": "2026-07-25T10:00:00Z"},
      "prospect_eval": {"status": "healthy", "last_run": "2026-07-24T15:00:00Z"}
    },
    "overall": "UNMEASURED"
  },
  "contradiction_scan_state": {
    "active_scans": 0,
    "kills_today": 0,
    "k_total": 7
  }
}
```

### 3.2 Why this matters

When the kernel computes G = A·P·E·X·Φ, it must know:
- **Is the P term reliable?** → query GEOX /health → check `g_primitive_state.P.status`
- **Which modalities are contributing?** → `g_primitive_state.P.active_pipelines`
- **Is any modality stale?** → `delta_substrate_health.pipelines.<modality>.last_run`
- **Has GEOX been falsifying claims?** → `contradiction_scan_state`

A degraded P term lowers G. A stale seismic pipeline raises C_dark. This is the thermodynamic link between multimodal perception and constitutional governance.

> **F2 rule:** `/health` apex and vitals are MEASURED | UNMEASURED only. **NOMINAL is void** (fabricated 0.5 banned). Constitutional G is never minted in GEOX — see `session_apex.py` + P0 health handler.

---

## 4. The GEOX-001 Spine as Δ Proof

The GEOX-001 spine (defined in GENESIS/013) is the concrete proof that Δ-substrate metabolism works:

```
geox_well_ingest → geox_well_qc → geox_seismic_ingest → geox_tie_preflight
  → geox_well_tie_compute → geox_tie_receipt → ONLY THEN: geox_claim
```

Each step is a reversible, inspectable Python operation. No step is a black-box LLM call. The tie receipt is the Δ proof that seismic and well evidence are metabolic — not decorative.

> **GH-4:** Any GEOX claim that bypasses the GEOX-001 spine shall be tagged `ENVELOPE_INCOMPLETE` with `verification_status: UNVERIFIED`. The kernel shall treat UNVERIFIED evidence as `HOLD` grade — admissible for reasoning, inadmissible for SEAL.

---

## 5. Multimodal Contradiction Scanning (Kill Matrix K001–K007)

The `geox_falsify` tool implements the KILL matrix. Each K-filter maps to a cross-modal contradiction:

| K-filter | Modalities checked | Example |
|----------|-------------------|---------|
| K001 | seismic ↔ well | Seismic says anticline; well log says flat-lying → KILL |
| K002 | seismic ↔ gravity | Bright spot on seismic; no density contrast on gravity → KILL |
| K003 | seismic ↔ biostrat | Fault interpreted at 2800m; biostrat says unconformity at 2800m → KILL |
| K004 | petrophysics ↔ lithology | Archie Sw says pay; core says tight → KILL |
| K005 | basin model ↔ thermal | Basin model predicts oil window; Ro data says overmature → KILL |
| K006 | prospect ↔ economic | POS says 60%; breakeven says negative EMV → KILL |
| K007 | any ↔ physics bounds | Vp/Vs outside Castagna mudrock ± 3σ → KILL |

> **GH-5:** Any GEOX tool that detects a contradiction between modalities must emit `contradiction_scan: KILL_<K00N>` in the envelope. The arifOS kernel reading this must trigger C_dark recalculation.

---

## 6. Operational Rules for GEOX

1. **Every tool output must carry the 11-field Ω-envelope.** Middleware (`envelope_normalizer.py`) synthesizes for legacy tools; new tools must produce envelopes natively.

2. **The `delta_substrate_hash` must be a SHA256 of the Python file that performed the Δ decomposition.** This enables the kernel to verify: "Did this claim pass through the correct pipeline?"

3. **Modality tags are non-optional for evidence-grade tools.** `geox_visual_understand`, `geox_seismic_interpret`, `geox_petrophysics`, `geox_well_*`, `geox_basin`, `geox_gravmag_studio`, `geox_deep_time_state`, `geox_prospect` — all must declare `modality`.

4. **G-primitive must be declared before evidence leaves GEOX.** If `geox_prospect` completes a volumetric assessment, the envelope must carry `g_primitive: "X"` and `delta_substrate_hash` pointing to the volumetric code.

5. **UNVERIFIED evidence is admissible for `arif_think` but not for `arif_seal`.** The kernel enforces this. GEOX must never claim SEAL on unverified evidence.

---

## 7. Relationship to Parent Doctrine

| Parent (arifOS/GENESIS/054) | Implementation (GEOX/GENESIS/018) |
|-----------------------------|-----------------------------------|
| MM-CD1: Δ-substrate required | GH-1 through GH-5 enforce Δ-substrate gating |
| MM-CD2: LLM is witness, not judge | GEOX falsifies claims; arifOS judges them |
| MM-CD3: Every modality maps to G primitive | Section 1.1 map + `g_primitive` envelope field |
| MM-CD4: No SEAL without all three witnesses | GEOX provides Ext_witness; W_4 gate in kernel |

---

*DITEMPA BUKAN DIBERI — GEOX does not perceive. GEOX metabolises. The LLM is the witness. The vault is the memory. The Δ substrate is the proof.*
