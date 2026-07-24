# GEOX Petrophysics Runbook — F2-Compliant (Corrected)

> **Status:** ACCEPTED WITH CORRECTIONS · Ready for publication  
> **SOT:** Live tool signatures + `geox_surface_status` beat this doc  
> **Date:** 2026-07-24 · **Audit commit:** `d1d0edb0`  
> **Labels:** `[DEMO]` · `[SYNTHETIC]` · `[UNVERIFIED]` · `[LIVE]`  
> **Doctrine:** DITEMPA BUKAN DIBERI

---

## 0. Verdict summary

| Category | Status | Note |
|----------|--------|------|
| Architecture (hybrid GEOX + vanilla) | **PASS** | Doctrine sound |
| API runbook | **CORRECTED** | Modes, evidence_refs, multi-well path |
| Fabricated data claims | **WITHDRAWN** | Tapis tables, fake open URLs, Volve geography |
| WellDesk GUI | **SHIPPED** | Correlation, SYNTHETIC badge, petro defaults |
| Governance | **LIVE** | Session + actor_id gates working |
| Operability | **F2-READY** | This document is the executable path |

---

## 1. Corrections ledger (accepted)

### 1.1 API schema

| Prior false claim | Corrected truth |
|-------------------|-----------------|
| `generate` with only `well_id` | Requires `target_class` + vaulted `evidence_refs` |
| `verify` with `well_id=[list]` | `well_id` is a **string**; verify needs `candidate_ref` + `domain` |
| `mode="qc"` on petrophysics | **False** — use `geox_well_qc` |
| Curve Archie path omitted | Primary: `mode="lem_inference"` + **curves dict** + `depth_m` |
| `geox_workspace` rejects actor | **Fixed** — accepts `actor_id` + `trace_id` |

### 1.2 Residual corrections on the 2026-07-24 restatement

| Restatement claim | F2 correction |
|-------------------|---------------|
| `curves=["GR","RT",…]` list of names | **`curves` is `dict[str, list[float]]`** of samples, same length as `depth_m` |
| `arif_init(... lease_id=...)` | `lease_id` is **not** an arif_init param; session id is typically `SEAL-*` (not always `sct_v1.*`) |
| `archie_a` etc. on `lem_inference` | Generate-path params; LEM uses `rw_ohm_m`, `rho_matrix_g_cc`, `rho_fluid_g_cc` (Archie a/m/n fixed at 1/2/2 in physics_prior) |
| `DEMO_SANDAKAN_A` as on-disk LAS 2.0 | WellDesk **scaffold id** `[SYNTHETIC]`. On-disk LAS: `fixtures/_DEMO_SYNTHETIC/DEMO_WELL_A_SANDAKAN.las` |
| Vanilla latency 50–100ms | Keep **`[UNVERIFIED]`** estimate only |

### 1.3 Data claims (withdrawn)

- USGS waterdata Tapis LAS — **VOID**
- PETRONAS public Tapis LAS URL — **VOID / UNVERIFIED**
- Volve as SE Asia analogue — **VOID geography** (North Sea OSS LAS still useful)
- Fabricated Tapis net-pay tables — **VOID**

---

## 2. Corrected minimal runbook

### Phase 0 — Session

```python
# [LIVE] Kernel ignition
arif_init(mode="init", actor_id="Arif", intent="geox petro demo")
# → session_id e.g. SEAL-…  (pass as session_id to GEOX tools)
# → actor_id must be non-anonymous on evidence lane
```

### Phase 1 — Workspace + ingest

```python
geox_workspace(
    mode="set",
    basin="Malay Basin",          # context label — not a claim of real Tapis LAS
    field="Demo Field",
    play="Tertiary Sandstone",
    well_id="DEMO_WELL_A",
    session_id="<SEAL-…>",
    actor_id="Arif",
)

geox_well_ingest(
    source_uri="/root/GEOX/fixtures/_DEMO_SYNTHETIC/DEMO_WELL_A_SANDAKAN.las",  # [DEMO]
    # or: data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las  # [LIVE] North Sea
    well_id="DEMO_WELL_A",
    standardize_curves=True,
    normalize_units=True,
    qc_strict=True,
    session_id="<SEAL-…>",
    actor_id="Arif",
)
```

### Phase 2 — QC (separate tool)

```python
geox_well_qc(
    artifact_ref="<ingest artifact_ref or path>",
    artifact_type="well_log",
    qc_mode="full",               # or "quick"
    session_id="<SEAL-…>",
    actor_id="Arif",
)
```

### Phase 3 — Petrophysics primary path (`lem_inference`)

```python
# curves MUST be dict of float arrays, same length as depth_m
depth = [2500.0 + 0.5 * i for i in range(301)]  # example grid
curves = {
    "GR":   [...],   # API units, len == len(depth)
    "RT":   [...],   # ohm·m
    "RHOB": [...],   # g/cc
    "NPHI": [...],   # v/v
}

geox_petrophysics(
    mode="lem_inference",
    well_id="DEMO_WELL_A",
    curves=curves,                 # dict[str, list[float]] — NOT name list
    depth_m=depth,
    depth_top_m=2500.0,            # optional zone window
    depth_bot_m=2650.0,
    rw_ohm_m=0.05,
    rho_matrix_g_cc=2.65,
    rho_fluid_g_cc=1.0,
    target_properties=["porosity", "sw", "lithology"],
    # session/actor on MCP wrapper when called via MCP
)
# Output class: physics_prior COMPUTED — confidence capped; NOT a seal
```

### Phase 3b — Generate path (vaulted evidence only)

```python
geox_petrophysics(
    mode="generate",
    target_class="sandstone",              # REQUIRED
    evidence_refs=["vaulted-ref-here"],    # REQUIRED — demo strings → EVIDENCE_REF_NOT_FOUND
    realizations=3,
    gr_clean=15,
    gr_shale=150,
    rw=0.05,
    archie_a=1.0,
    archie_m=2.0,
    archie_n=2.0,
    zone_top_m=2500,
    zone_base_m=2650,
    canon9_profile="malay_basin",
)
# Do not claim production generate until evidence store is populated
```

### Phase 4 — Integrity verify (not multi-well list)

```python
geox_petrophysics(
    mode="verify",
    candidate_ref="<artifact from generate or store>",  # REQUIRED
    domain="malay_basin",                                # REQUIRED
)
# well_id list / target_properties multi-well correlation is NOT this mode
# Multi-well visual correlation: WellDesk Correlation tab [SYNTHETIC] or vanilla plots
```

### Phase 5 — Well desk render

```python
geox_well_desk(
    mode="render",   # also: open | publish
    well_id="DEMO_WELL_A",
    depth_top=2500,
    depth_base=2650,
    curves=["GR", "RT", "RHOB", "NPHI"],  # name list OK here (desk view selection)
    interpret=True,
    rw=0.05,
    session_id="<SEAL-…>",
    actor_id="Arif",
)
# Standalone WellDesk app shows SYNTHETIC badge until MCP hydrates real curves
```

---

## 3. Demo inventory (use these)

| ID | Path / surface | Geography | Epistemic |
|----|----------------|-----------|-----------|
| DEMO_WELL_A / B SANDAKAN | `fixtures/_DEMO_SYNTHETIC/*.las` | Sandakan-style demo | `[DEMO]` |
| DEMO_SANDAKAN_A/B | WellDesk scaffold ids | Sandakan-style | `[SYNTHETIC]` |
| MALAY_DEMO_01 | WellDesk scaffold | Malay-style labels | `[SYNTHETIC]` |
| VOLVE 15/9-19 | `data/geox_las/CHATGPT_VALIDATION_VOLVE_15_9_19.las` | **North Sea** | `[LIVE]` LAS, not SE Asia |

**Do not publish:** fabricated Tapis-01/02/03 net-pay tables; unverified USGS/PETRONAS LAS URLs; Volve as Malay Basin analogue.

---

## 4. Hybrid strategy (reconfirmed)

```
Vanilla explore (lasio/pandas/matplotlib) [UNVERIFIED timing]
        │ lock parameters
        ▼
GEOX validate
  · geox_well_qc
  · geox_petrophysics(mode=lem_inference)   ← primary curve path
  · geox_petrophysics(mode=generate|verify) ← only with vaulted refs
  · epistemic tags + session binding
        │
        ▼
Publish honestly
  · COMPUTED · SYNTH / DEMO / MEASURED
  · NOT SEALED until arifOS seal path
```

---

## 5. Residual (non-blocking)

| Issue | Status |
|-------|--------|
| Real Volve LAS full hydrate into WellDesk tracks | Pending MCP tool-result curve push |
| `generate` evidence store population for demos | Pending — expect EVIDENCE_REF_NOT_FOUND until vaulted |
| ChatGPT MCP App host visual QA | Deferred |
| Registry truth | PASS at audit (32 public tools, includes `geox_well_qc`) |

---

## 6. Publication checklist

- [x] Withdraw fabricated Tapis numbers and false open-data URLs  
- [x] Document `lem_inference` as primary curve path  
- [x] Document `curves` as **dict of samples**, not name list  
- [x] Label demo / synthetic / North Sea Volve correctly  
- [x] Flag latency numbers `[UNVERIFIED]`  
- [x] Point GUI users to WellDesk Correlation + SYNTHETIC badge  
- [ ] Populate vaulted `evidence_refs` before production `generate` claims  
- [ ] Retest `verify` with a real `candidate_ref` from a successful generate  

---

*F2 governance restatement · 2026-07-24 · GEOX organ · Arif F13*
*Primary audit receipt: `forge_work/2026-07-24/GEOX-MCP-EVAL-AUDIT-GUI-IMPROVE.md`*
)
