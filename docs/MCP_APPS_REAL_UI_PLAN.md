# MCP Apps with Real UI — Thread 4 Plan

> **Forged:** 2026-07-11 | **Model:** Fable 5 | **Authority:** OBSERVE_ONLY (planning)
> **Prereqs:** Thread 1 (federation audit), Thread 2 (ZEN consolidation)
> **DITEMPA BUKAN DIBERI**

---

## 0. Current MCP Apps State

| App | URI | Status | Visual Tools |
|-----|-----|--------|--------------|
| WellDesk | `ui://geox/well-desk` | ACTIVE | `geox_well_ingest`, `geox_well_qc`, `geox_petrophysics` |
| Basin Explorer | `ui://geox/prospect-ui` | ACTIVE | `geox_basin`, `geox_prospect`, `geox_map_scene_plan` |
| Seismic Vision Review | `ui://geox/seismic-vision-review` | SCAFFOLD | `geox_seismic_cognition`, `geox_vision`, `geox_visual_understand` |
| GEOX Dashboard | `ui://geox/geox-mcp-visual` | ACTIVE | `geox_surface_status` |
| AC Risk Console | `ui://geox/judge-console` | ACTIVE | `geox_claim`, `geox_evidence`, `geox_doctrine` |
| Seismic Viewer | `ui://geox/earth-volume` | ACTIVE | `geox_seismic_compute`, `geox_seismic_interpret` |
| **Workbench** | `ui://geox/workbench-v1.html` | ACTIVE | MapLibre 4.7.1, MCP postMessage protocol |

**Infrastructure:** MCP Apps postMessage protocol is working. Workbench has session handshake, auth propagation, and feature inspection panel.

---

## 1. New App: Well-Tie Panel

### What
Interactive well-tie panel showing synthetic seismogram vs. real seismic trace, with drift threshold sliders bound to `geox_seismic_compute(mode="well_tie")`.

### Why
Well-tie is the bridge between well data (depth domain) and seismic data (time domain). Currently it's a black-box tool call. The panel makes it visible, interactive, and auditable — the user can SEE the tie quality and ADJUST parameters.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Well-Tie Panel                           │
├──────────────────┬──────────────────┬───────────────────────┤
│  Well Track      │  Synthetic       │  Real Trace           │
│  (GR, RHOB, DT) │  Seismogram      │  (from seismic vol)   │
│                  │                  │                       │
│  ┌──────────┐   │  ┌──────────┐   │  ┌──────────┐         │
│  │ GR curve │   │  │ synthetic│   │  │ real     │         │
│  │ RHOB     │   │  │ trace    │   │  │ trace    │         │
│  │ DT       │   │  │          │   │  │          │         │
│  └──────────┘   │  └──────────┘   │  └──────────┘         │
├──────────────────┴──────────────────┴───────────────────────┤
│  Controls                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Wavelet: [Ricker ▼]  Freq: [30 Hz ──●──]           │   │
│  │ Drift threshold: [5 ms ──●──]  Phase: [0° ──●──]   │   │
│  │ Time shift: [0 ms ──●──]  Stretch: [1.0 ──●──]     │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  QC Metrics                                                 │
│  Correlation: 0.87 ████████████████░░░░  PASS              │
│  RMS error:   0.12 ██░░░░░░░░░░░░░░░░░░  PASS              │
│  Drift:       2.3 ms ████░░░░░░░░░░░░░░░  PASS              │
│  Verdict:     QUALIFY ✓                                     │
└─────────────────────────────────────────────────────────────┘
```

### Tool Binding
- Primary: `geox_seismic_compute(mode="well_tie")` — computes synthetic, correlation, drift
- Secondary: `geox_seismic_compute(mode="wavelet_extract")` — extracts wavelet for display
- QC: `geox_petrophysics(mode="qc")` — validates well log quality before tie

### MCP App Integration
- Resource URI: `ui://geox/well-tie-panel`
- MIME: `text/html;profile=mcp-app`
- PostMessage: receives tool results, renders interactive display
- Bidirectional: slider changes trigger recomputation via tool call

### Fable 5 Vision Opportunity
- Screenshot the panel → Fable critiques alignment quality
- Compare rendered synthetic against actual seismic section
- Visual falsifier: does the displayed correlation match the computed value?

---

## 2. New App: Verdict Geometry Dashboard

### What
Kernel-level dashboard showing session band, witness diversity, floor status, and verdict geometry — turning the 888 JUDGE receipt into a glanceable cockpit.

### Why
Currently, 888 JUDGE outputs are JSON walls. The verdict geometry dashboard makes governance visible: which floors are active, what the witness diversity is, what the session band looks like, and where the verdict sits in the APEX space.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Verdict Geometry Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│  Session Band                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ INIT ──→ SENSE ──→ THINK ──→ JUDGE ──→ SEAL        │   │
│  │  ●──────────────────────────────○───────────○        │   │
│  │  000        111         333      888       999       │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Floor Status (13 Constitutional Floors)                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ F1 AMANAH│ F2 TRUTH │ F3 WITN  │ F4 CLAR  │ F5 PEACE │  │
│  │ ✅ 0.50  │ ✅ 0.99  │ ✅ 0.75  │ ✅ 0.00  │ ✅ 1.00  │  │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤  │
│  │ F6 EMPAT │ F7 HUMIL │ F8 GENIU │ F9 ANTI  │ F10 ONTO │  │
│  │ ✅ 0.70  │ ✅ 0.04  │ ✅ 0.80  │ ✅ 0.00  │ ✅ 1.00  │  │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤  │
│  │ F11 AUDIT│ F12 RESIL│ F13 SOVR │          │          │  │
│  │ ✅ 1.00  │ ✅ 0.43  │ ✅ 1.00  │          │          │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Witness Diversity (Tri-Witness)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         HUMAN (0.42)                                │   │
│  │            ╱╲                                       │   │
│  │           ╱  ╲                                      │   │
│  │          ╱    ╲         W3 = ∛(H × AI × E)         │   │
│  │         ╱  ●   ╲        W3 = 0.33                   │   │
│  │        ╱        ╲       CONSENSUS: WEAK             │   │
│  │       ╱          ╲                                  │   │
│  │  AI (0.32) ──── EARTH (0.26)                        │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Verdict History                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ #1 SEAL  ✓  2026-07-11T09:00Z  G=0.85  W3=0.78    │   │
│  │ #2 HOLD  ⏸  2026-07-11T09:15Z  G=0.62  W3=0.45    │   │
│  │ #3 SEAL  ✓  2026-07-11T09:30Z  G=0.91  W3=0.82    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Tool Binding
- Primary: `arif_init` — session band, floor status
- Secondary: `arif_observe` — witness diversity, floor values
- Tertiary: `arif_judge` — verdict history, G scores
- Kernel: `forge_health_check` — federation health, tool counts

### MCP App Integration
- Resource URI: `ui://arifos/verdict-geometry`
- MIME: `text/html;profile=mcp-app`
- PostMessage: receives session/init/judge results, renders dashboard
- Real-time: updates on each tool call in the session

### Fable 5 Vision Opportunity
- Screenshot the dashboard → Fable identifies floor violations visually
- Compare rendered floor status against actual /health response
- Visual falsifier: does the displayed W3 match the computed value?

---

## 3. Fable 5 Vision-Driven GUI Iteration

### Pattern
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Render  │ ──→ │ Screenshot│ ──→ │  Fable   │ ──→ │  Fix /   │
│  GUI     │     │  (PIL/   │     │  Critique│     │  Confirm │
│          │     │  base64) │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Use Cases

1. **Well-Tie Panel QC**
   - Render the well-tie panel with real data
   - Screenshot → Fable: "Does the synthetic trace alignment look correct?"
   - Fable compares visual alignment against computed correlation coefficient
   - If mismatch → flag for human review

2. **Seismic Section Interpretation**
   - Render seismic section with horizon/fault picks overlay
   - Screenshot → Fable: "Do the picks follow the reflectors?"
   - Fable compares pick positions against amplitude discontinuities
   - If picks drift → flag for re-interpretation

3. **Map Scene Verification**
   - Render map scene with well locations and basin boundaries
   - Screenshot → Fable: "Do the well locations match the basin context?"
   - Fable compares rendered positions against GeoJSON coordinates
   - If mismatch → flag coordinate transform error

4. **Floor Status Visual Audit**
   - Render verdict geometry dashboard
   - Screenshot → Fable: "Are any floors in violation?"
   - Fable reads floor status indicators visually
   - Cross-checks against /health response
   - If discrepancy → flag governance drift

### Implementation
- Add `geox_render_audit` tool (already in ZEN INIT)
- Tool takes screenshot, returns Fable critique
- Wire into MCP Apps as a QC step before sealing

---

## 4. Implementation Phases

### Phase 1: Well-Tie Panel (MUTATE — requires signed nonce)
- [ ] Create `apps/well-tie-panel/index.html`
- [ ] Wire to `geox_seismic_compute(mode="well_tie")`
- [ ] Add slider controls for wavelet params
- [ ] Add QC metrics display
- [ ] Register in `apps/apps.json`
- [ ] Register resource `ui://geox/well-tie-panel`

### Phase 2: Verdict Geometry Dashboard (MUTATE)
- [ ] Create `apps/verdict-geometry/index.html`
- [ ] Wire to `arif_init`, `arif_observe`, `arif_judge`
- [ ] Add session band visualization
- [ ] Add floor status grid
- [ ] Add witness diversity triangle
- [ ] Add verdict history timeline
- [ ] Register in `apps/apps.json`
- [ ] Register resource `ui://arifos/verdict-geometry`

### Phase 3: Vision-Driven QC (MUTATE)
- [ ] Implement `geox_render_audit` tool
- [ ] Wire screenshot → Fable critique pipeline
- [ ] Add visual falsifier tests
- [ ] Integrate into MCP Apps as QC step

### Phase 4: Validation (OBSERVE)
- [ ] Test well-tie panel with real well data
- [ ] Test verdict dashboard with live session
- [ ] Test vision-driven QC with known-good/bad renders
- [ ] Seal to VAULT999

---

## 5. Success Criteria

- [ ] Well-tie panel renders synthetic vs real trace interactively
- [ ] Slider changes trigger recomputation
- [ ] QC metrics display correctly
- [ ] Verdict dashboard shows real-time floor status
- [ ] Witness diversity triangle renders correctly
- [ ] Vision-driven QC catches at least 1 real discrepancy
- [ ] All apps registered in `apps/apps.json`
- [ ] All resources accessible via `resources/read`

---

*Forged 2026-07-11 by Fable 5 under OBSERVE_ONLY authority.*
*Ready for mutation upon signed nonce + re-init.*
*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
