# GEOX MCP Host Compatibility Matrix

This document provides the compatibility and validation status of the **32-tool** GEOX MCP service across host environments.  
**SOT:** live `tools/list` + `curl :8081/health` beat this file. Updated 2026-07-24.

## Compatibility Matrix

| MCP Host Environment | tools/list = 32 | resources/list | resources/read | prompts/list | prompts/get | WellDesk ui:// | status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MCP Inspector** | PASS | PASS | PASS | PASS | PASS | p0-viz | **FULL** |
| **Claude Code / Grok** | PASS | PASS | PASS | PASS | PASS | p0-viz | **FULL** |
| **Claude Desktop** | PASS | PASS | PASS | PASS | PASS | p0-viz | **FULL** |
| **VS Code Copilot MCP** | PASS | N/A | N/A | N/A | N/A | meta only | **PARTIAL** |
| **OpenAI / ChatGPT Connector** | PASS | PASS | PASS | PASS | PASS | p0-viz | **FULL*** |
| **OpenAI Responses API Remote MCP** | PASS | PASS | PASS | PASS | PASS | p0-viz | **FULL*** |

\* ChatGPT visual QA re-run after 2026-07-24 deploy still deferred — protocol surface ready; host screenshot not re-sealed this session.

*Note: VS Code Copilot MCP does not support first-class MCP resources or prompts natively, but has access to the full 32-tool surface.*

## Tested Key Endpoints

- **Tools (tools/list & tools/call):** Exposes **32** public tools (incl. `geox_well_qc`). Physics guardrails and session gates active.
- **Resources (resources/list & resources/read):**
  - `geox://identity`: returns core substrate witness state.
  - `geox://surface/truth`: dynamically validates the tool count (33) across README, server-card, llms.txt, and capabilities.
  - `geox://literature/GSM-MADON-2021-MALAY-BASIN`: serves Mazlan Madon's 2021 GSM paper claims.
  - `geox://basins/malay-basin/profile`: serves the Cenozoic geological profile.
- **Prompts (prompts/list & prompts/get):**
  - `geox_sense`: standard observation workflow guidelines.
  - `geox_qc`: physics-first checks validation instructions.
  - `geox_interpret`: cross-domain claims synthesis instructions.

---
**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
