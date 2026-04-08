# GEOX_HOST_ADAPTER_BLUEPRINT.md — Cross-Platform Connectivity

> **DITEMPA BUKAN DIBERI** — *Forged, Not Given*
> **Status:** PROPOSED | **Authority:** ΔΩΨ

This blueprint defines how the GEOX core connects to various AI hosts (OpenAI, Claude, Copilot, Custom) through a unified adapter layer.

---

## 🏛️ Adapter Architecture

The `arifos/geox/platforms` folder will contain the host-specific translation logic.

### 1. The Canonical Interface (`IHostAdapter`)
Each adapter must implement:
- `get_tool_schemas()`: Translate GEOX tool definitions into the host's format.
- `map_ui_resource()`: Expose the `ui_entry` via the host's resource model.
- `handle_context_sync()`: Translate host-provided session/context into GEOX state.
- `dispatch_event()`: Send a message to the host's app bridge (e.g., `postMessage`).

### 2. Specific Adapter Strategies

#### OpenAI Apps Adapter (`openai_adapter.py`)
- **Mapping:** Maps FastMCP tools to OpenAI's tool definition schema.
- **UI:** Exposes the UI as a `widget` inside the ChatGPT sidebar.
- **Session:** Tracks `widgetSessionId` provided by OpenAI to maintain interpretation state.

#### MCP Apps Adapter (`mcp_apps_adapter.py`)
- **Mapping:** Standard MCP tool registration.
- **UI:** Uses `_meta.ui.resourceUri` to point to the `geox-gui/index.html`.
- **Security:** Respects the host's sandboxed iframe and Content Security Policy (CSP).

#### Copilot / Generic Adapter (`generic_adapter.py`)
- **Mapping:** Standard Tool Schema (JSON).
- **Fallback:** Since some Copilot hosts lack rich app rendering, this adapter focuses on returning formatted markdown and deep-links to the external GEOX web host.

#### Custom GEOX Web Host (`geox_web_adapter.py`)
- **Mapping:** Direct tool execution via FastMCP.
- **UI:** Full-screen browser runtime without iframe sandboxing (for internal high-performance rendering).

---

## 🚦 Host Mapping Matrix

| Feature | OpenAI Apps | MCP Apps (Claude) | Custom Host |
|---|---|---|---|
| **Auth** | Managed Identity | OAuth / Local | Full SSO |
| **Iframe** | Yes (Widget) | Yes (Sandboxed) | No (Native) |
| **Tool Calling** | Toolset SDK | MCP standard | Direct FastMCP |
| **Context** | Chat Session | Resource Sync | Redis Cache |

---

*Sealed by: 888_JUDGE | 2026.04.09*
*DITEMPA BUKAN DIBERI*
