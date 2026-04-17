# GEOX Governed Agentic Apps — Roadmap

> **Status:** Wave 1 Trust Foundation — MCP Deployment ACTIVE
> **Motto:** *Ditempa Bukan Diberi* — Forged, Not Given
> **Constitutional Kernel:** arifOS F1–F13
> **Ledger:** VAULT999
> **MCP Server:** FastMCP v3.2.4 · HTTP transport on :8000 · SSE
> **Last Updated:** 2026-04-16

---

## 1. Executive Summary

This roadmap translates the Gemini strategic design spec into an implementable, governed trajectory for five GEOX applications. The work is phased by governance maturity, not merely feature count.

| App | Status | Target Phase | Governance Grade |
|---|---|---|---|
| **AC_Risk Console** | LIVE | Reference implementation | AAA |
| **Attribute Audit** | PREVIEW | Working prototype | AA |
| **Seismic Vision Review** | SCAFFOLD | Governed stub | A |
| **Georeference Map** | SCAFFOLD | Governed stub | A |
| **Analog Digitizer** | PLANNED | Design spike | B |

---

## 2. What Was Delivered in This Commit

### 2.1 AC_Risk Governance Hardening (Option A)
**Files:** `geox/core/ac_risk.py`, `geox/geox_mcp/fastmcp_server.py`, `geox/core/tool_registry.py`

- **ClaimTag enum** added (`CLAIM`, `PLAUSIBLE`, `HYPOTHESIS`, `UNKNOWN`).
- **TEARFRAME dataclass** added (`truth`, `echo`, `amanah`, `rasa`).
- **Anti-Hantu screen** (`AntiHantuScreen`) with regex patterns to detect empathy/feeling claims. Fail-closed → `VOID`.
- **888_HOLD enforcement**:
  - Raw AC_Risk `HOLD`/`VOID` triggers `hold_enforced=True`.
  - `irreversible_action=True` forces `HOLD` regardless of score.
  - `amanah_locked=False` forces `HOLD` for `SEAL`/`QUALIFY`.
- **VAULT999 payload** embedded in every governed result.
- **MCP tool exposure:**
  - `geox_compute_ac_risk` — backward-compatible basic tool.
  - `geox_evaluate_prospect` — Canonical governance entrypoint with 888_HOLD and VAULT999 sealing.
  - `geox_load_seismic_line` — Seismic with F4 clarity verification.
  - `geox_build_structural_candidates` — Multi-model interpretation (non-uniqueness principle).
  - `geox_verify_geospatial` — Coordinate grounding with CRS validation.
  - `geox_feasibility_check` — Constitutional firewall (F1-F13 pre-check).
  - `geox_earth_signals` — Live Earth observations.
  - `arifos_*` tools — arifOS routing layer (routed, not direct).

### 2.2 MCP App Stubs + UI Bridge (Options B, C, D)
**Files:** `geox/apps/*/manifest.json`, `geox/apps/*/index.html`

Four new app directories created, each with:
- `manifest.json` aligned to the app-manifest schema.
- `index.html` with `ui_bridge` postMessage contract.
- `ui://` resources exposed in server.

### 2.3 Tool Registry Updates
**File:** `geox/core/tool_registry.py`

New metadata entries registered:
- `geox_evaluate_ac_risk_governed` (PROD)
- `geox_attribute_audit_stub` (PREVIEW)
- `geox_seismic_vision_review_stub` (SCAFFOLD)
- `geox_georeference_map_stub` (SCAFFOLD)
- `geox_analog_digitizer_stub` (SCAFFOLD)

---

## 3. Remaining Work — Acceptance Criteria
(Rest of the file remains same...)

---

## 4. Phase: Subsurface Epistemic Layer (2026-Q2)

**Audit Reference:** Session 2026-04-18
**Purpose:** Formalize Bayesian graph, encode dependencies explicitly, enforce hard physics constraints, quantify refusal triggers, model basin-level correlation.

### 4.1 Subsurface Skill Domains (6 Registered)

| Skill ID | Title | Status |
|----------|-------|--------|
| `geox.subsurface.formation-evaluation` | Formation Evaluation | ✅ ACTIVE |
| `geox.subsurface.seismic-interpretation` | Seismic Interpretation | ✅ ACTIVE |
| `geox.subsurface.reservoir-dynamics` | Reservoir Dynamics | ✅ ACTIVE |
| `geox.subsurface.basin-charge` | Basin Charge | ✅ ACTIVE |
| `geox.subsurface.prospect-risk` | Prospect Risk | ✅ ACTIVE |
| `geox.subsurface.posterior-integrity` | Posterior Integrity | ✅ ACTIVE |

**Physics Constraints Enforced (not advisory):**
- Porosity: 0.02 ≤ POR ≤ 0.45
- Water saturation: 0.0 ≤ Sw ≤ 1.0
- Vsh: 0.0 ≤ Vsh ≤ 1.0
- Ro oil window: 0.6% – 1.3%
- Ro gas floor: > 1.3%

### 4.2 PhysicsGuard Module

**File:** `geox/core/physics_guard.py`

Implements:
- `validate()` — Check output against physical bounds
- `check_posterior_breadth()` — Enforce P90/P10 ratio ≤ 5.0
- `check_net_pay()` — ALL THREE criteria required (Sw, POR, Vsh)
- `check_charge_timing()` — charge_ma ≤ trap_ma
- `validate_prospect_input()` — Full prospect validation

**Unit Tests:** `tests/test_physics_guard.py` ✅

### 4.3 Remaining Work

- [ ] Per-element confidence scoring (pLDDT equivalent)
- [ ] Independence checker for PoS components
- [ ] WEALTH posterior distribution pipeline
- [ ] Portfolio correlation tracker

---

*Seal: DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
