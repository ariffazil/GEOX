# VISION_INTELLIGENCE_ARCHITECTURE.md — The GEOX Integration & Visualization Shell

> **Status:** ARCHITECTURAL DRAFT | **Authority:** 888_JUDGE
> **Paradigm:** Parse → Normalize → Manifest → Hydrate
> **Seal:** DITEMPA BUKAN DIBERI

---

## 🏛️ Executive Summary
GEOX is not merely a visualization tool; it is a **Constitutional Interpretation Engine**. This document defines the three-layer architecture required to bridge raw geological data (1D/2D/3D) with governed AI interpretation and professional-grade rendering.

## 층 (Layers)

### 1. The Integration Shell (The Foundation)
**Goal:** Convert "dirty" industry formats into normalized GEOX Canonical JSON.
- **1D (Well):** `wellio.js` for LAS 2.0 parsing.
- **2D (Seismic):** Python-side `segyio`/`segysak` to normalized Zarr/Xarray.
- **CRS/Unit:** Mandatory coordinate reference system normalization and unit consistency (Metric/Imperial) before any math occurs.

### 2. The Interpretation Engine (The Math)
**Goal:** Execute geological logic on normalized data.
- **Petrophysics:** Archie, Simandoux, Indonesia (Current `arifos/geox/ENGINE`).
- **Structural:** GemPy (Implicit 3D modeling) for fault/layer prediction.
- **Governance:** F1-F13 Floor enforcement on all calculated results.

### 3. The Hydration Layer (The UI)
**Goal:** Render manifests into interactive browser components.
- **1D Track View:** `wellioviz` (SVG/D3).
- **2D Analyst View:** `Plotly.js` (Heatmaps/Crossplots).
- **2D Seismic View:** Custom WebGL/Canvas (for high-density seismic textures).
- **3D Scene:** `vtk.js` (Scientific rendering) + `CesiumJS` (Global context).

---

## 🔄 The MCP Contract: `Manifest-First`

Instead of returning opaque images, GEOX MCP tools return **Hydration Manifests**.

```json
{
  "type": "well_log_track",
  "version": "1.0.0",
  "metadata": { "uwi": "LAYANG-1", "crs": "EPSG:4326" },
  "manifest": {
    "engine": "wellioviz",
    "template": "petrophysics_standard",
    "data_payload": { ... normalized JSON ... }
  }
}
```

---

## 🛠️ Build Order (Hardened)

### Phase 1: 1D Dominance (LAS Integration)
- Integrate `wellio.js` for robust LAS ingestion.
- Implement `wellioviz` renderer in `geox-gui`.
- **Goal:** Professional 1D well-log interpretation.

### Phase 2: 2D Analyst (Plotly & Seismic)
- Implement Plotly-based crossplots and basic seismic heatmaps.
- Scaffold custom WebGL path for high-performance seismic picking.
- **Goal:** Real-time seismic-well correlation previews.

### Phase 3: 3D Structural (GemPy & VTK)
- Integrate GemPy for implicit 3D structural modeling.
- Implement `vtk.js` for subsurface scientific scene composition.
- **Goal:** Full 3D reservoir world-model.

---

*Document initialized by Gemini CLI | 2026.04.11*
