# Seismic Section Viewer — App Specification

**App ID:** `geox.seismic.viewer`
**Domain:** Seismic
**Status:** 🚧 FORGING · Phase B
**Epoch:** 2026-04-09

---

## 1. Overview

The Seismic Viewer is the primary visual interface for interpreting seismic cross-sections. It enforces the **Theory of Anomalous Contrast (ToAC)** by preventing auto-interpretation on unverified data stretches.

---

## 2. Capabilities

- **ToAC Realtime Contrast**: Interactive adjustment of display gain and contrast to match physical rock mechanics.
- **888_HOLD Integration**: Hard-stop for physically suspicious data (e.g. impossible dip angles).
- **Claim Embedding**: Every visual anomaly is tagged with its epistemic status (CLAIM/PLAUSIBLE).
- **Host Sync**: Automatically pushes the current viewer state (Z-depth, scale) back to the LLM.

---

## 3. Tool Requirements

- `geox_load_seismic_line`: Fetches raw data and QC badges.
- `geox_build_structural_candidates`: Fetches multiple interpretation hypotheses.

---

## 4. UI Events Surface

- **Outbound**:
  - `ui.action`: `contrast_change`, `horizon_pick`, `hold_resolve`.
  - `ui.state.sync`: Coordinates and display settings.
- **Inbound**:
  - `app.context.patch`: Highlighting horizons suggested by the LLM.

---

## 5. Deployment

- **Local**: `arifos/geox/apps/seismic_viewer/index.html`
- **Prod**: `https://geox.apps/seismic-viewer/latest/`

---

**Audit Reference:** `VOID_20260409_081416`
