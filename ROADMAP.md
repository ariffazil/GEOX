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
*Seal: DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
