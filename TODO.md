# TODO — GEOX Execution Queue

**Actionable tasks for the current sprint.**

---

## Phase B: Physics Engine (🚧 IN PROGRESS)

### P0: Now (Governance & Physics)
- [x] **Archie saturation model** (clean formations) — *Implemented in logic layer*
- [x] **Simandoux model** (dispersed shaly sand) — *Implemented in logic layer*
- [x] **Indonesia model** (mixed/laminated) — *Implemented in logic layer*
- [ ] **Dual-Water model** (CEC-based)
- [x] **Uncertainty propagation** (Monte Carlo n=1000)
- [ ] **Validate Capability Matrix**: Run end-to-end tests for L1-L4 fallbacks.
- [ ] **Extract Schemas**: Finalize conversion of all ToolResult structures to Pydantic models.
- [ ] **Sovereign Veto**: Implement automated `888_HOLD` push notifications for physical violations.

### P1: Next (Adapter Scaffolding)
- [ ] **OpenAI Adapter SDK**: Scaffold the `window.openai` bridge in `geox-gui`.
- [ ] **Copilot Adapter**: Define the JSON-LD / Adaptive Card Extensions for MS Copilot.
- [ ] **Signed Deep-Links**: Implement HMAC signing for session-handoff to external Web Shell.

### P2: Later (App Depth & 3D)
- [ ] **Seismic Component**: Implement the multi-slice 2D view in `EarthWitness3D.tsx`.
- [ ] **Basin Map**: Integrate Leaflet/OpenLayers for GeoJSON spatial rendering.
- [ ] **Observability**: Implement custom `telemetry.emit` events for user interaction tracking.
- [ ] **cigvis 3D seismic integration** (Phase C).

---

## Recently Completed (Session 2026-04-09)
- [x] **GEOX MCP Apps Architecture** forged and SEALED (G=0.92).
- [x] **Canonical Contracts** defined (Manifest, Adapter API, Event Contract).
- [x] **Petrophysics Engine** hardened with automated Claim Tagging.
- [x] **Documentation Suite** (README, LLM_WIKI, CHANGELOG, TODO, ROADMAP) synchronized.

---

**Policy:** Do NOT add aspirations here. Keep it actionable.
