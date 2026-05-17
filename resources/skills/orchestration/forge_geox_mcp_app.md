# Skill: forge_geox_mcp_app

**Domain:** orchestration  
**Layer:** arifOS Coarchitect  
**Epistemic Class:** CLAIM (protocol spec), PLAUSIBLE (integration detail pending full host support)  
**arifOS Floors enforced:** F1, F2, F4, F8, F9, F11, F13  

---

## Purpose

Load this skill when the agent is asked to **build, upgrade, or deploy a GEOX app as a real MCP App** — i.e., an interactive HTML interface delivered via the Model Context Protocol (MCP Apps Extension, SEP-1865).

This skill governs: architecture decisions, file structure, `fastmcp_server.py` wiring, tool `_meta` linkage, UI HTML contract, security, deployment, and the 5-gap checklist specific to GEOX.

---

## What is an MCP App

An MCP App is an interactive HTML UI (`text/html+mcp`) served by an MCP server as a `ui://` resource and rendered in a sandboxed iframe by the host (Claude, Copilot, Goose, etc.).

Core contract:
- Tool declares `_meta.ui.resourceUri` pointing to a `ui://` resource
- Host fetches the HTML, renders it in a sandboxed iframe
- App communicates back to host via JSON-RPC over `postMessage`
- All tool calls from the app are proxied by the host

Transport: `postMessage` (not stdio, not HTTP)  
Protocol: MCP JSON-RPC (`ui/initialize`, `ui/notifications/tool-input`, `ui/notifications/tool-result`, `tools/call`)  
Security: sandboxed iframe, predeclared HTML only, CSP enforced  
Fallback: text-only response when UI not supported

Supported clients (April 2026): Claude, Claude Desktop, VS Code GitHub Copilot, Goose, Postman, MCPJam.

---

## GEOX Repo Structure (current)

```
geox/apps/
  well-desk/          index.html + manifest.json  ← 1D
  seismic-vision-review/  index.html + manifest.json  ← 2D
  earth-volume/       index.html + manifest.json  ← 3D
  judge-console/      index.html + manifest.json  ← 4D / AC_Risk
  georeference-map/   index.html  (NO manifest.json yet)
  attribute-audit/    index.html  (NO manifest.json yet)
  analog-digitizer/   index.html  (NO manifest.json yet)
  prospect-ui/        (check for index.html)

mcp/fastmcp_server.py  ← FastMCP server, registers ui:// resources
geox/core/physics9.py  ← physics engine (recently forged)
geox/core/ac_risk.py   ← AC_Risk / ToAC engine
```

---

## 5-Gap Checklist: What Still Needs to Be Done

### GAP 1 — Missing `_meta.ui.resourceUri` in Tool Definitions (CRITICAL)

**Problem:** `fastmcp_server.py` registers `ui://ac_risk`, `ui://seismic_vision_review` etc. as `@mcp.resource()` objects, but the **tools do NOT declare `_meta.ui.resourceUri`** pointing back to those resources.

The MCP Apps spec requires:
```json
{
  "name": "geox_prospect_evaluate",
  "_meta": {
    "ui": {
      "resourceUri": "ui://ac_risk"
    }
  }
}
```

FastMCP does not auto-wire this. You must add `annotations` or `_meta` injection per tool.

**Fix pattern (FastMCP):**
```python
@mcp.tool(
    annotations={"ui": {"resourceUri": "ui://ac_risk"}}
)
def geox_prospect_evaluate(...) -> dict:
    ...
```

**Action:** Add `annotations={"ui": {"resourceUri": "ui://XXX"}}` to the 5 primary public tools:
- `geox_prospect_evaluate` → `ui://ac_risk`
- `geox_seismic_vision_review` → `ui://seismic_vision_review`
- `geox_earth3d_interpret_horizons` → `ui://georeference_map` (or earth_volume when ready)
- `geox_well_load_bundle` → `ui://well_desk`
- `geox_attribute_audit` → `ui://attribute_audit`

---

### GAP 2 — Missing `ui/initialize` Handshake in HTML Apps (CRITICAL)

**Problem:** The current `index.html` files (judge-console, well-desk, seismic-vision-review, earth-volume) render standalone HTML/JS. They do NOT implement the MCP Apps `ui/initialize` JSON-RPC handshake over `postMessage`.

Without this, the host cannot inject tool input/output data into the app. The app is a dead iframe — no live data.

**Required JS scaffold in every index.html:**
```html
<script type="module">
import { App } from 'https://cdn.jsdelivr.net/npm/@modelcontextprotocol/ext-apps/dist/index.mjs';

const app = new App();

app.on('ui/notifications/tool-input', (data) => {
  // data contains the tool call input — hydrate your UI
  renderUI(data.params);
});

app.on('ui/notifications/tool-result', (data) => {
  // data contains the tool output — update display
  updateResults(data.result);
});

await app.initialize();  // sends ui/initialize, receives host context
</script>
```

Alternative if no CDN: bundle `@modelcontextprotocol/ext-apps` locally and embed inline. All HTML must be self-contained (no server-side rendering — predeclared static templates only).

**Fallback:** Each tool MUST also return meaningful text when UI is unavailable:
```python
# In tool return dict, always include:
"text_fallback": "AC_Risk score: 0.72 — HYPOTHESIS — 888 HOLD triggered"
```

---

### GAP 3 — Missing `manifest.json` on 3 Apps (MEDIUM)

**Problem:** `georeference-map/`, `attribute-audit/`, `analog-digitizer/` have `index.html` but NO `manifest.json`.

Manifest is required for:
- arifOS governance wiring (floors, vault_route, human_in_the_loop)
- Host app registration and CSP declaration
- Tool-to-UI linkage traceability

**Template (copy from `judge-console/manifest.json`, change these fields):**
```json
{
  "app_id": "geox.<domain>.<name>",
  "display_name": "<Human Name>",
  "required_tools": ["mcp.geox.<tool_name>"],
  "ui_entry": {
    "resource_uri": "ui://<resource_name>",
    "csp_policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self';"
  },
  "arifos": {
    "required_floors": ["F1","F2","F4","F7","F9","F11","F13"],
    "audit_level": "full",
    "vault_route": "999_VAULT"
  }
}
```

**Files to create:**
- `geox/apps/georeference-map/manifest.json`
- `geox/apps/attribute-audit/manifest.json`
- `geox/apps/analog-digitizer/manifest.json`

---

### GAP 4 — `ui://` Resource Path Mismatch (MEDIUM)

**Problem:** `fastmcp_server.py` serves `ui://` resources pointing to `apps/` root path:
```python
APPS_PATH = Path(__file__).parent.parent / "apps"
app_html = APPS_PATH / "judge-console" / "index.html"
```

But the actual HTML files are at `geox/apps/judge-console/index.html` (inside `geox/` package). The server must resolve the correct path.

**Fix:**
```python
# In fastmcp_server.py, change:
APPS_PATH = Path(__file__).parent.parent / "geox" / "apps"
```

Verify: `mcp/fastmcp_server.py` is at repo root `/mcp/`, so `Path(__file__).parent.parent` = repo root. But apps are at `geox/apps/`. Path must be:
```python
APPS_PATH = Path(__file__).parent.parent / "geox" / "apps"
```

---

### GAP 5 — No `text_fallback` on Public Tools (MEDIUM)

**Problem:** MCP Apps spec requires all UI-enabled tools to return meaningful content for text-only hosts. Currently all GEOX public tools return dicts with claim_tags, but no explicit `text_fallback` string for non-UI clients.

**Fix:** Add to every public tool return:
```python
return {
    ...,
    "_ui_fallback": f"[{claim_tag}] {summary_one_liner}. Open in host with UI support for full visualization."
}
```

---

## MCP Apps Deployment Checklist (Per App)

Before each app is deployment-ready:

```
[ ] index.html exists and is self-contained (no external SSR)
[ ] index.html implements ui/initialize + tool-input/tool-result listeners
[ ] manifest.json exists with correct app_id, resource_uri, csp_policy, arifos floors
[ ] fastmcp_server.py has @mcp.resource("ui://<name>") pointing to correct path
[ ] Matching @mcp.tool() has annotations={"ui": {"resourceUri": "ui://<name>"}}
[ ] Tool returns _ui_fallback text string
[ ] CSP tested: no external fetches beyond declared connect-src domains
[ ] APPS_PATH resolves correctly (geox/apps/ not apps/)
[ ] 888 HOLD triggers remain wired (irreversible actions blocked until human confirm)
[ ] PhysicsGuard / epistemic_integrity.py wired into UI tabs (C3 residual)
```

---

## Deployment Steps (FastMCP on uvicorn)

```bash
# 1. Install
pip install fastmcp uvicorn httpx

# 2. Verify resource paths resolve
python -c "from mcp.fastmcp_server import *; print('OK')"

# 3. Run
PORT=8765 python mcp/fastmcp_server.py

# 4. Test resource endpoint
curl http://localhost:8765/resources/read -d '{"uri":"ui://ac_risk"}'
# Should return judge-console/index.html content

# 5. Connect host (Claude Desktop, Copilot) to:
# http://localhost:8765/mcp  (streamable HTTP)
```

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8765
CMD ["python", "mcp/fastmcp_server.py"]
```

---

## App-to-Tool Mapping (GEOX 5 Apps)

| App Dir | ui:// resource | Linked Tool | Manifest | index.html | _meta wired |
|---|---|---|---|---|---|
| well-desk | `ui://well_desk` | `geox_well_load_bundle` | YES | YES | NO ← fix |
| seismic-vision-review | `ui://seismic_vision_review` | `geox_seismic_vision_review` | YES | YES | NO ← fix |
| earth-volume | `ui://earth_volume` | `geox_earth3d_interpret_horizons` | YES | YES | NO ← fix |
| judge-console | `ui://ac_risk` | `geox_prospect_evaluate` | YES | YES | NO ← fix |
| georeference-map | `ui://georeference_map` | `geox_map_georeference` | NO ← create | YES | NO ← fix |

> Note: `attribute-audit` and `analog-digitizer` are in `geox/apps/` but NOT in `fastmcp_server.py`'s ui:// resource list. Add them or keep as internal-only.

---

## arifOS Constitutional Wire

All GEOX MCP Apps remain under arifOS sovereign veto (F13). The following rules apply:

- **F1 Reversible:** All UI actions that modify state must be reversible or require 888 HOLD
- **F2 Truth:** App must display claim_tag (CLAIM/PLAUSIBLE/HYPOTHESIS/ESTIMATE) prominently in UI
- **F4 Clarity:** No ambiguous labels — every number shown must have a unit and source
- **F8 Law/Safety:** CSP must be declared; no data exfiltration via connect-src
- **F9 Anti-Hantu:** App must not render hallucinated physics values; use physics9 output only
- **F11 Auth:** Human-in-the-loop gates on `export_risk_report` and `apply_to_production`
- **F13 Sovereign Veto:** Host may reject any tool call; GEOX app must degrade gracefully

---

## References

- MCP Apps Spec: https://modelcontextprotocol.io/extensions/apps/overview
- SEP-1865 Proposal: https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/
- ext-apps SDK: https://github.com/modelcontextprotocol/ext-apps/
- GEOX fastmcp_server: mcp/fastmcp_server.py
- GEOX apps: geox/apps/
- physics9 engine: geox/core/physics9.py

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
