# GEOX Image Metabolizer — Tool Design

> **Status:** DRAFT — awaiting ratification
> **Date:** 2026-07-12
> **Authority:** F13 SOVEREIGN (Arif) directive + audit synthesis

---

## 1. THE THREE DIRECTIONS

```
┌─────────────────────────────────────────────────────────────────┐
│                    GEOX IMAGE METABOLIZER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   GENERATE   │     │   CONSUME    │     │  METABOLIZE  │    │
│  │              │     │              │     │              │    │
│  │ Data → PNG   │     │ Image → VLM  │     │ Image ↔ Data │    │
│  │ + metadata   │     │ → Structure  │     │ + provenance │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                  │
│  geox_render_*       geox_vision_*        geox_export_*        │
│  (P0)                (BUILT)              (P1)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. GENERATE — `geox_render_*` Tools (P0)

### 2.1 `geox_render_well_panel`

**Purpose:** Render a multi-track well log composite as PNG with embedded metadata.

**Input:**
```json
{
  "well_id": "BEK-2",
  "curves": ["GR", "RT", "NPHI", "RHOB", "DT"],
  "depth_range": [1000, 3000],
  "tops": [{"name": "Top A", "depth": 1500}, {"name": "Top B", "depth": 2200}],
  "color_scheme": "dark",
  "dpi": 150,
  "width_px": 1200,
  "height_px": 800
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64 PNG>",
      "mimeType": "image/png"
    }
  ],
  "_meta": {
    "render": {
      "tool": "geox_render_well_panel",
      "well_id": "BEK-2",
      "image_sha256": "abc123...",
      "rendered_at": "2026-07-12T07:00:00Z",
      "dpi": 150,
      "dimensions": [1200, 800],
      "curves_rendered": ["GR", "RT", "NPHI", "RHOB", "DT"],
      "depth_range": [1000, 3000],
      "epistemic_tier": "EVIDENCE",
      "data_source_sha256": "def456...",
      "provenance": {
        "tool_call_id": "call_789",
        "session_id": "session_abc",
        "agent_id": "agent_xyz"
      }
    }
  }
}
```

**Implementation:**
- Use Plotly.js → static image export (via `plotly.io.to_image`)
- Or: matplotlib with well-log track templates
- Embed metadata in PNG tEXt chunks (using PIL/Pillow)
- SHA256 of both input data and output image

**Governance:**
- Action class: OBSERVE (read-only render)
- Mutation: false
- Physics guard: false (rendering doesn't require physics validation)
- Epistemic tier: EVIDENCE (the image shows data, not interpretation)

---

### 2.2 `geox_render_seismic_section`

**Purpose:** Render a 2D seismic section as PNG with optional horizon/fault overlays.

**Input:**
```json
{
  "line_id": "SL-2024-001",
  "section_type": "inline",
  "section_value": 1500,
  "time_range": [1000, 3000],
  "display_mode": "variable_density",
  "color_scale": "seismic",
  "horizons": [{"name": "H1", "time_ms": 1800}],
  "faults": [{"x_pos": 500, "style": "dashed"}],
  "gain": 1.0,
  "clip_percentile": 98,
  "dpi": 150,
  "width_px": 1200,
  "height_px": 600
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64 PNG>",
      "mimeType": "image/png"
    }
  ],
  "_meta": {
    "render": {
      "tool": "geox_render_seismic_section",
      "line_id": "SL-2024-001",
      "section_type": "inline",
      "section_value": 1500,
      "image_sha256": "abc123...",
      "rendered_at": "2026-07-12T07:00:00Z",
      "display_mode": "variable_density",
      "color_scale": "seismic",
      "horizons_rendered": ["H1"],
      "faults_rendered": 1,
      "epistemic_tier": "EVIDENCE",
      "provenance": { ... }
    }
  }
}
```

**Implementation:**
- Use matplotlib/imshow for variable density
- Use Plotly heatmap for interactive (server-side export)
- Overlay horizons as lines, faults as dashed lines
- Embed metadata in PNG tEXt chunks

---

### 2.3 `geox_render_attribute_map`

**Purpose:** Render a horizon attribute map (RMS amplitude, sweetness, etc.) as PNG.

**Input:**
```json
{
  "horizon_name": "H1",
  "attribute": "rms_amplitude",
  "color_scale": "viridis",
  "contours": true,
  "well_markers": [{"well_id": "BEK-2", "x": 100, "y": 200}],
  "scale_bar": true,
  "dpi": 150,
  "width_px": 1000,
  "height_px": 800
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64 PNG>",
      "mimeType": "image/png"
    }
  ],
  "_meta": {
    "render": {
      "tool": "geox_render_attribute_map",
      "horizon_name": "H1",
      "attribute": "rms_amplitude",
      "image_sha256": "abc123...",
      "epistemic_tier": "INTERPRETATION",
      "provenance": { ... }
    }
  }
}
```

---

### 2.4 `geox_render_comparison`

**Purpose:** Render side-by-side comparison of two datasets.

**Input:**
```json
{
  "left": {"type": "seismic", "line_id": "SL-001", "section_value": 1500},
  "right": {"type": "attribute", "horizon": "H1", "attribute": "sweetness"},
  "layout": "side_by_side",
  "linked_cursors": true,
  "dpi": 150
}
```

---

## 3. CONSUME — `geox_vision_*` Tools (BUILT ✅)

Already implemented:
- `geox_vision` — Unified tool with 5 modes
  - `infer_minimax` — MiniMax M3 VLM on seismic images
  - `infer_mimo` — MiMo Embodied-7B native multimodal
  - `audit` — AC_Risk scoring + VisionVerdict
  - `calibrate` — Synthetic forward-inverse harness
  - `perceptual` — Build PerceptualInventory

**Status:** Working. No changes needed for P0.

---

## 4. METABOLIZE — `geox_export_*` Tools (P1)

### 4.1 `geox_export_annotated_image`

**Purpose:** Take an existing render and burn in annotations, epistemic badges, provenance.

**Input:**
```json
{
  "source_image_sha256": "abc123...",
  "annotations": [
    {"type": "arrow", "x": 100, "y": 200, "label": "Possible DHI"},
    {"type": "polygon", "points": [[100,100], [200,100], [200,200], [100,200]], "label": "Zone of Interest"}
  ],
  "epistemic_badge": "INTERPRETATION",
  "uncertainty_overlay": true,
  "scale_bar": true,
  "provenance_watermark": true,
  "output_format": "png"
}
```

**Output:**
```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64 PNG with burned-in annotations>",
      "mimeType": "image/png"
    }
  ],
  "_meta": {
    "export": {
      "source_sha256": "abc123...",
      "exported_sha256": "ghi789...",
      "annotations_burned": 2,
      "epistemic_badge": "INTERPRETATION",
      "exported_at": "2026-07-12T07:00:00Z"
    }
  }
}
```

---

### 4.2 `geox_export_comparison`

**Purpose:** Create a comparison image from two renders.

---

## 5. METADATA EMBEDDING

### PNG tEXt Chunks

Every rendered image MUST include:

```
geox:tool = geox_render_well_panel
geox:version = 1.0.0
geox:image_sha256 = abc123...
geox:data_sha256 = def456...
geox:rendered_at = 2026-07-12T07:00:00Z
geox:epistemic_tier = EVIDENCE
geox:well_id = BEK-2
geox:session_id = session_abc
geox:agent_id = agent_xyz
geox:tool_call_id = call_789
```

### Sidecar JSON (Optional)

For complex metadata, emit a `.meta.json` file alongside the image:

```json
{
  "image": "geox_render_well_panel_BEK-2_20260712.png",
  "image_sha256": "abc123...",
  "tool": "geox_render_well_panel",
  "parameters": { ... },
  "data_source": { ... },
  "provenance": { ... },
  "epistemic": { ... }
}
```

---

## 6. INTEGRATION WITH MCP APPS

### Well-Desk Integration

When the well-desk HTML app renders a view, it should:

1. Call `geox_render_well_panel` via host (postMessage → tools/call)
2. Receive base64 PNG + metadata
3. Display in the app
4. Offer "Publish Image" button that calls `geox_export_annotated_image`
5. Return annotated image to host conversation

### Host Integration

MCP hosts (ChatGPT, Claude, Copilot) receive:

```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64>",
      "mimeType": "image/png"
    },
    {
      "type": "text",
      "text": "Well log panel for BEK-2. Epistemic tier: EVIDENCE. SHA256: abc123..."
    }
  ]
}
```

The host can display the image directly in the conversation.

---

## 7. IMPLEMENTATION PLAN

### P0 (This Week)
1. Implement `geox_render_well_panel` using matplotlib
2. Implement PNG metadata embedding (PIL/Pillow tEXt)
3. Wire into MCP server
4. Test with well-desk HTML app

### P1 (Next 2 Weeks)
1. Implement `geox_render_seismic_section`
2. Implement `geox_render_attribute_map`
3. Implement `geox_export_annotated_image`
4. Add "Publish Image" to well-desk HTML

### P2 (Next Month)
1. Implement `geox_render_comparison`
2. Add Plotly-based rendering option (interactive → static export)
3. Add vision model integration (image → structure → image loop)

---

## 8. EXTERNAL COMPARISON

| Capability | Petrel | GeoTeric | GEOX (Planned) |
|------------|--------|----------|----------------|
| Well log rendering | ✅ Native | ❌ Limited | ✅ `geox_render_well_panel` |
| Seismic section | ✅ Native | ✅ Native | ✅ `geox_render_seismic_section` |
| Attribute maps | ✅ Native | ✅ Native | ✅ `geox_render_attribute_map` |
| Image export | ✅ Manual | ✅ Manual | ✅ One-click + metadata |
| Embedded provenance | ❌ None | ❌ None | ✅ SHA256 + epistemic tier |
| MCP integration | ❌ None | ❌ None | ✅ Native |
| Vision model analysis | ❌ None | ❌ None | ✅ `geox_vision_*` |

---

## 9. CONFIDENCE

| Assessment | Confidence |
|------------|------------|
| Architecture is correct | HIGH (85) |
| matplotlib can render well logs | HIGH (90) |
| PNG metadata embedding works | HIGH (90) |
| MCP content block supports images | HIGH (95) |
| Hosts will display images | MEDIUM (70) — depends on host |
| One-week P0 timeline | MEDIUM (60) — depends on data availability |

---

**DITEMPA BUKAN DIBERI — Forged, Not Given**
