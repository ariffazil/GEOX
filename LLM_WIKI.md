# LLM_WIKI — GEOX MCP Apps Knowledge Base

**Doctrine:** "Contract over Prose."
**Status:** SEALED · v1.0.0
**Epoch:** 2026-04-09

---

## 1. System Overview
GEOX is a host-agnostic application platform for interactive geoscience tools. It uses the Model Context Protocol (MCP) to bridge geological capabilities with AI orchestrators (GitHub Copilot, OpenAI ChatGPT, Claude).

### Core Principles
- **Host-Agnostic**: Domain logic survives host-swaps.
- **Contract-First**: Interfaces are determined by GEOX, not vendor SDKs.
- **Epistemic Grounding**: Every claim tagged as CLAIM, PLAUSIBLE, HYPOTHESIS, or UNKNOWN.

---

## 2. 6-Layer Architecture
The system is partitioned to ensure total isolation of domain logic from UI and host-specific code.

| Layer | Name | Responsibility |
| :--- | :--- | :--- |
| **L6** | Security/Audit | AuthN/AuthZ (JWT), Sandboxing, 999_VAULT. |
| **L5** | UI Layer | React/TypeScript microfrontends. |
| **L4** | Host Adapter | Translation between GEOX and Vendor SDKs. |
| **L3** | App Orchestration | App manifests, Capability negotiation. |
| **L2** | Domain Logic | Physics Engine, Petrophysics, F1-F13 Validation. |
| **L1** | MCP Transport | JSON-RPC 2.0, stdio/SSE. |

---

## 3. Host Capability Model
GEOX adapts its rendering level based on the host's offerings.

- **L1 (Text)**: Plain text (Universal).
- **L2 (Rich Cards)**: Structured data (Copilot, Claude).
- **L3 (Inline Iframe)**: Embedded interactive UI (Claude, Custom).
- **L4 (External Shell)**: Full web shell (Universal via signed deep links).

---

## 4. Canonical Contracts

### 4.1 App Manifest
Every GEOX app triggers via a manifest:
- `app_id`: `geox.[domain].[name]`
- `ui_entry`: URI and mode (inline vs external).
- `required_tools`: MCP tools required for operation.

### 4.2 Host Adapter API
Adapters must implement the bridge between the host environment and the GEOX UI runtime.
- `renderInline(appId, config)`
- `launchExternal(url, params)`
- `onAction(callback)`

### 4.3 tool.result Contract
All tools return `ToolResult` containing:
- `content`: Markdown text.
- `structured_content`: JSON data for cards/apps.
- `meta.appIntent`: Instructions for the host to launch a specific GEOX app.

---

## 5. Security & Governance
- **888_HOLD**: Veto gate for unphysical or sensitive actions.
- **999_VAULT**: Immutable audit trail for physical grounding claims.
- **Sovereign Identity**: Tenant isolation via signed tokens.

---

## 6. Glossary
- **MCP**: Model Context Protocol.
- **ToAC**: Theory of Anomalous Contrast.
- **Claim Tag**: Epistemic status marker.
- **Web Shell**: The external GEOX UI runtime.

---

## 7. Lock-In Risks & Mitigations
- **Risk**: Over-reliance on ChatGPT Widgets.
- **Mitigation**: All widgets are implemented as standard GEOX Web Shells behind an OpenAI Adapter.
- **Risk**: Auth tied to Microsoft Entra.
- **Mitigation**: GEOX-Sovereign JWT bridge ensures identity portability.

---

**Audit Reference:** `VOID_20260409_073736`
