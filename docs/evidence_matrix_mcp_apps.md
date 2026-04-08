# EVIDENCE MATRIX — GEOX MCP Apps

**Status:** SEALED
**Doctrine:** "Contract over Prose."

---

## 1. Core Architectural Claims

| Claim ID | Claim | Epistemic Status | Source |
| :--- | :--- | :--- | :--- |
| **C1** | MCP Apps can be platform-agnostic if separated into neutral core + thin adapters. | **CLAIM** | [stevekinney.com](https://stevekinney.com/writing/mcp-apps) |
| **C2** | Build host-neutral core first; add adapters for ChatGPT, Copilot, Claude later. | **CLAIM** | [alpic.ai](https://alpic.ai/blog/mcp-apps-how-it-works-and-how-it-compares-to-chatgpt-apps) |
| **C3** | Trio of (Domain Core, MCP Layer, UI Microfrontend) is the portable unit. | **PLAUSIBLE** | [alpic.ai](https://alpic.ai/blog/mcp-apps-how-it-works-and-how-it-compares-to-chatgpt-apps) |
| **C4** | Agreement on "Server-defined capabilities + Host-rendered interactive UI". | **CLAIM** | [stevekinney.com](https://stevekinney.com/writing/mcp-apps) |

---

## 2. Interface Alignment

| Feature | MCP Apps Spec | OpenAI Apps SDK | Alignment |
| :--- | :--- | :--- | :--- |
| **UI Delivery** | `_meta.ui.resourceUri` | Widget Runtime | **MATCH** (via iframe) |
| **Comms** | JSON-RPC / postMessage | JSON-RPC / custom bridge | **MATCH** (Bridge pattern) |
| **Sandboxing** | Host-provided Iframe | Hosted / Sandboxed Iframe | **MATCH** |
| **Registry** | Tools/Resources | Tools/Templates/Widgets | **MATCH** |

---

## 3. Fallback Logic

- **Direct Support**: Render inline iframe app.
- **Tool-Only Support**: Use tool results + **Signed Deep Link** to external GEOX web UI.
- **Custom Host**: Direct implementation of the MCP bridge.

---

**Audit Reference:** `VOID_20260409_073326`
