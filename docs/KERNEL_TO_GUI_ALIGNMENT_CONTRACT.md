# Kernel-to-GUI Alignment Contract — GEOX × AAA

**Date:** 2026-06-14  
**Author:** FORGE (000Ω), from Arif's 9 engineering eureka insights  
**Doctrine:** One truth object from kernel to pixels. GUI is a lens, not a brain.

---

## 0. THE CORE INSIGHT

> The system is aligned only if each layer preserves the **same truth object**,
> rather than re-inventing it in UI language.

- `geoxcore` computes bounded physical result.
- `geoxmcp` wraps in canonical contract with claim state, verdict, artifact custody.
- `GUI` resolves modality via `RenderPayload` and fetches referenced resources only.
- `UI components` render plus display epistemic metadata inline.
- `App workflows` compose those components but never mutate the underlying geological claim.
- `Human` can drill down to evidence or stop at `888_HOLD`.

If any app step can generate a new geological meaning without going back through
GEOX MCP, alignment is broken.

---

## 1. THE 7 ENGINEERING LAWS

### Law 1 — Contract Supremacy

GUI consumes **only** canonical MCP contracts. Never ad hoc response shapes.

- `RenderPayload` for all visual outputs
- `CubeManifest` for 3D volumes
- `ClaimEnvelope` for geological claims
- No shadow schemas, no convenience transforms outside GEOX MCP

**Violation:** A React component that manually parses raw GEOX envelope fields
instead of consuming `render_payload`.

### Law 2 — Provenance on Screen

Every rendered object shows or can reveal:

```yaml
artifact_ref: sha256:...
source_tool: geox_horizon_contrast_surface
crs: EPSG:3168
depth_basis: TVDSS
timestamp: 2026-06-14T12:00:00Z
```

**Violation:** A pretty 3D surface with no source artifact hash.

### Law 3 — ACRisk Travels with Pixels

Risk metadata must persist from kernel to component props to tooltip/panel state.

```yaml
acrisk_score: 0.42
arifos_verdict: QUALIFY
human_review_required: false
```

**Violation:** A 3D viewer that hides ACRisk behind a menu toggle.

### Law 4 — No Silent Upgrade

GUI may refine **resolution**, never refine **epistemic certainty**.

```
✅ Allowed:   LOD0 → LOD2 (more detail, same claim)
❌ Forbidden: HYPOTHESIS → CLAIM (cannot upgrade truth class)
```

**Violation:** A panel that silently promotes a HYPOTHESIS to a CLAIM for display.

### Law 5 — Partial is Explicit

Missing data must remain visible as PARTIAL / QUALIFY / HYPOTHESIS states.

```
Missing bricks  → render coarse LOD, marked "partial"
Missing tests   → show in "missing_evidence" list
Missing ties    → display "untied" marker
```

**Violation:** A smooth surface that hides the fact that 60% of it is interpolated.

### Law 6 — One Object, Many Views

Map, 3D, table, and narrative must bind to the same `render_id` / `artifact_ref`.

```
Map panel      → render_id: geox-render-abc123
3D panel       → render_id: geox-render-abc123
Evidence card  → render_id: geox-render-abc123
```

**Violation:** Three different panels showing three different objects
that the user cannot cross-reference.

### Law 7 — 888 at the Edge

Human veto must remain enforceable all the way in app/UI actions,
not just at kernel level.

- `HOLD` state → render with warning overlay, lock mutation
- `SEAL` state → render with seal icon, allow drill-down
- `VOID` state → render with strikethrough, show superseding claim

**Violation:** A "submit" button that ignores the GEOX verdict.

---

## 2. THE 9 EUREKA INSIGHTS (Engineering)

### 2.1 One Truth Object

**Eureka:** The system is aligned only if each layer preserves the *same truth object* rather than re-inventing it in UI language.

**Engineering test:** Can you trace a pixel on screen back to the exact `sha256:artifact_hash` and `geox_tool_call` that produced it? If not, alignment is broken.

### 2.2 Physics Before Pixels

**Eureka:** Visual intelligence is dangerous because display transform risk and cognitive bias can overpower physical uncertainty.

**Engineering test:** Does every visual carry ACRisk on load, or only on a "details" panel?

### 2.3 GUI is a Lens, Not a Brain

**Eureka:** GEOX doctrine already says the LLM is the language interface, never the geologist. The same rule applies to GUI components.

**Engineering test:** Can the GUI generate a new geological claim without calling GEOX MCP? If yes, alignment is broken.

| Component | Is a Lens Over | Must Never Be |
|-----------|---------------|---------------|
| MapLibre panel | `render_geojson` | Basin analysis engine |
| Domain3D | `horizon_contrast_surface` + `CubeManifest` | Structural interpreter |
| App cards | `DECISIONSUPPORT` objects | Prospect evaluator |
| Well panel | `geox_las_inspect` output | Petrophysics engine |

### 2.4 Every Layer Must Degrade Safely

**Eureka:** Alignment is not just correctness on success path; it is refusal to hallucinate on failure path.

| Failure | Safe Degradation |
|---------|-----------------|
| geoxcore unavailable | No substitute geology, only failure state |
| Manifest missing | No cube render, only metadata card |
| Brick fetch incomplete | Render coarse LOD, visibly marked PARTIAL |
| ACRisk high | Lock narrative, trigger 888 HOLD |

### 2.5 Renderables are First-Class Evidence

**Eureka:** Curves, maps, surfaces, cubes, markers are not decoration. They are evidence carriers with custody.

**Engineering rule:** Every renderable carries:

```yaml
render_id: geox-render-abc123
artifact_ref: sha256:las_A1_2024
source_tool: geox_data_ingest_bundle
claim_state: OBSERVED
acrisk: 0.05
```

### 2.6 Cross-Modal Fidelity is the Product

**Eureka:** The real platform edge over static suites: a single governed Earth object renderable in many modalities without semantic drift.

**Engineering test:** A spill-point candidate, basin polygon, horizon hull, and executive card should all be alternate views of one `render_id`, not separate app artifacts.

### 2.7 Contract Supremacy (Law 1)

**Eureka:** GUI only consumes canonical MCP contracts, never ad hoc response shapes.

### 2.8 ACRisk Travels with Pixels (Law 3)

**Eureka:** Risk metadata must persist from kernel to component props to tooltip/panel state.

### 2.9 Replace Placeholders, Not Invent Logic

**Eureka:** P0 wiring should replace placeholders with canonical tools, not invent custom frontend logic.

**Engineering rule:** If you're writing a React hook that does geology, you're doing it wrong. Call GEOX MCP instead.

---

## 3. KERNEL → GUI → APP FLOW

```
┌──────────────────┐
│  1. geoxcore     │  Computes bounded physical result
│     computes     │  (petrophysics, surface, cube, claim)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. geoxmcp      │  Wraps in canonical contract:
│     wraps        │  RenderPayload / CubeManifest / ClaimEnvelope
│                  │  Adds: claim_state, verdict, ACRisk,
│                  │  artifact_ref, CRS, depth_basis
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. GUI resolves │  Reads RenderPayload.modality
│     modality     │  Selects component: MapPanel / Domain3D / WellPanel
│                  │  Fetches binary resources from MCP
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. UI renders   │  Renders visual + epistemic metadata
│     + metadata   │  Shows: ACRisk, verdict, artifact_ref
│                  │  Provides: provenance drill-down
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  5. App composes │  Composes panels into workflows
│     workflows    │  NEVER mutates underlying claim
│                  │  Mutations → call GEOX MCP
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  6. Human judges │  Drills to evidence
│     or 888 HOLD  │  Stops at HOLD
│                  │  Override → arifOS F13 gate
└──────────────────┘
```

---

## 4. TEST: ALIGNMENT CHECKLIST

For every GUI component, verify:

- [ ] `artifact_ref` is visible or accessible
- [ ] `acrisk_score` is visible on load
- [ ] `arifos_verdict` is visible on load
- [ ] `claim_state` (OBSERVED/COMPUTED/INTERPRETED) is visible
- [ ] Missing data is explicitly marked PARTIAL
- [ ] Component consumes canonical MCP contract, not ad-hoc parse
- [ ] Component cannot generate claims without GEOX MCP
- [ ] `render_id` maps 1:1 across all views of the same object
- [ ] HOLD state locks mutation
- [ ] Provenance drill-down works (1 click to artifact hash)

---

## 5. THE SHORTEST PATH TO ALIGNED GUI

### P0 Wiring Discipline

Replace placeholders with canonical tools. Not custom frontend logic.

| Task | Replace | With |
|------|---------|------|
| Map panel | `bridge.interpret_causal_scene` | `geox_map_context_scene(render_geojson)` |
| 3D panel | `macrostrat` iframe | `geox_horizon_contrast_surface` → Domain3D |
| Well panel | Hardcoded curves | `geox_las_inspect` → log viewer |
| Cube viewer | Static image | `CubeManifest` → brick streaming → GPU |

### P1 Component Pattern

Every GEOX-wired component follows:

```typescript
interface GEOXComponentProps {
  renderPayload: RenderPayload;  // from MCP tool call
  onDrillDown: (artifactRef: string) => void;
  on888HOLD: () => void;
}
```

No component reads raw GEOX envelopes. No component calls geology APIs directly.
Everything goes through `RenderPayload`.

---

## 6. FINAL SEAL

> GUI is a lens, not a brain. ACRisk travels with pixels. One truth object from kernel to screen.

If any app step can generate a new geological meaning without going back through GEOX MCP, alignment is broken. This contract exists to prevent that.

**DITEMPA BUKAN DIBERI — Forged, Not Given.**
