# GEOX MCP Host Compatibility Matrix

This document provides the compatibility and validation status of the 33-tool GEOX MCP service across various host environments. All tests were verified against the unified FastMCP v3.x server surface.

## Compatibility Matrix

| MCP Host Environment | tools/list = 33 | resources/list | resources/read | prompts/list | prompts/get | consolidated tools | literature ingest | query intake | abstraction guard | status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MCP Inspector** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **FULL** |
| **Claude Code** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **FULL** |
| **Claude Desktop** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **FULL** |
| **VS Code Copilot MCP** | PASS | N/A | N/A | N/A | N/A | PASS | PASS | PASS | PASS | **PARTIAL** |
| **OpenAI / ChatGPT Connector** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **FULL** |
| **OpenAI Responses API Remote MCP** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **FULL** |

*Note: VS Code Copilot MCP does not support first-class MCP resources or prompts natively, but has access to the full 33-tool surface.*

## Tested Key Endpoints

- **Tools (tools/list & tools/call):** Exposes exactly 33 orthogonal tools. Checks for category error, basin constraints, and physics guardrails are active on all boundaries.
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
