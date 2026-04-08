# GEOX_SESSION_AUTH_CONTRACT.md — Identity & Context Stability

> **DITEMPA BUKAN DIBERI** — *Forged, Not Given*
> **Status:** PROPOSED | **Authority:** ΔΩΨ

This contract defines how GEOX maintains session stability and identity across heterogeneous AI platforms (ChatGPT, Claude, etc.).

---

## 🏛️ Identity Core

### 1. Canonical Session Object (`GeoSession`)
The `GeoSession` must be uniquely identifiable and must not rely solely on host-provided metadata.
- `session_id`: Unified GEOX session ID.
- `host_session_id`: Vendor-specific ID (e.g., `widgetSessionId`).
- `user_id`: Authenticated user identity (mapped from OAuth/JWT).
- `active_well_context`: The currently active borehole or project area.
- `interpretation_depth`: Current depth or coordinate focus.
- `audit_trail[]`: Pointers to 999_VAULT entries for the current session.

### 2. Context Sync Flow
When the host initializes the app:
1. Host calls `app.initialize` via postMessage.
2. Host passes `context` (e.g., chat_id, user_preferences, active_well_id).
3. App updates internal state and returns a `session_ignited` event.
4. Any future tool call includes the `GeoSession` context to ensure consistent reasoning.

---

## 🔐 Auth & Sovereignty

### 1. Managed Identity
GEOX will support a "Managed Identity" pattern where the host provides a signed token that the GEOX adapter validates against a centralized OIDC provider.
- **Reference:** `2389-research/mcp-socialmedia` (Session/Auth patterns)

### 2. Capability Scoping
Auth is not just binary (Yes/No). It is scoped to the geological context:
- `READ`: Access to public/basin-level data.
- `WRITE`: Capability to commit interpretations to the `999_VAULT`.
- `ADMIN`: Permission to override 888_HOLD verdicts.

---

## 🚦 Security Redlines

- **No Secret Persistence:** The UI should never store API keys or high-security tokens in the host's `localStorage`.
- **Session Bounding:** All sessions are transient by default; persistence requires an explicit **SEAL to VAULT** operation.
- **Audit Requirement:** Every session ignition and context change must be recorded for constitutional telemetry.

---

*Sealed by: 888_JUDGE | 2026.04.09*
*DITEMPA BUKAN DIBERI*
