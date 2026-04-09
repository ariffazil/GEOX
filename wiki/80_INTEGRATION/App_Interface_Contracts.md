# App Interface Contracts — Manifest & Events

**Status:** ✅ SEALED
**Authority:** 888_JUDGE
**Epoch:** 2026-04-09

---

## 1. Overview

GEOX Apps are governed by two primary interface contracts: the **App Manifest** (Discovery) and the **UI Event Bus** (Interaction). These contracts ensure that any app can run in any host (ChatGPT, Copilot, Claude) as long as a suitable adapter is present.

---

## 2. The App Manifest (Discovery)

Every GEOX App must provide a manifest that declares its identity and requirements.

**Schema:** `arifos.geox.contracts.manifest.AppManifest`

```json
{
  "app_id": "geox.seismic.viewer",
  "version": "1.0.0",
  "domain": "seismic",
  "ui_entry": {
    "resource_uri": "https://geox.apps/seismic-viewer",
    "mode": "inline-or-external"
  },
  "tools_required": [
    "geox_load_seismic_line",
    "geox_build_structural_candidates"
  ]
}
```

---

## 3. The UI Event Bus (JSON-RPC 2.0)

Communication between the App and the Host Adapter uses a standardized JSON-RPC 2.0 bridge.

**Schema:** `arifos.geox.contracts.events`

### 3.1 Outbound Events (App -> Host)

- `app.initialize`: Initial handshake.
- `ui.action`: User interactions (clicks, zooms, picks).
- `ui.state.sync`: Pushing critical state (e.g., "currently viewing slice 450") back to the LLM.
- `tool.request`: Requesting the host to call an MCP tool.

### 3.2 Inbound Events (Host -> App)

- `app.context.patch`: LLM context updates (e.g., "The user now wants to see a deeper horizon").
- `tool.response`: Results from requested tool calls.

---

## 4. Implementation Rules

1. **Zero Logic in UI**: The UI must not perform saturation calculations or structural reasoning. It only renders and sends `tool.request`.
2. **State Sync Frequency**: Don't flood the host with events. Only sync state on meaningful user pausing or "Sealing" actions.
3. **Graceful Degradation**: If the Event Bus is disconnected, the UI must show a "Read-Only / Disconnected" state.

---

**Audit Reference:** `VOID_20260409_081416`
