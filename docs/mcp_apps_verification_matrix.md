# GEOX MCP Apps Verification Matrix

| Widget URI | Backing tool(s) | resources/read OK | Renders in host | Tool round-trip from iframe | Empty-state OK | Error-state OK | CSP parity | Status |
|---|---|---|---|---|---|---|---|---|
| `ui://geox/well-desk` | `geox_well_desk` | ✅ YES (17 KB) | ✅ PASS (Canvas2D) | ✅ PASS (SEP-1865) | ✅ PASS (Clear error) | ✅ PASS (NO_LAS_DATA) | ✅ PASS (Parity) | **READY** |
| `ui://well/desk` | `geox_well_desk` | ✅ YES (11.5 KB) | ✅ PASS (Canvas2D) | ✅ PASS (SEP-1865) | ✅ PASS (Clear error) | ✅ PASS (NO_LAS_DATA) | ✅ PASS (Parity) | **READY** |
| `ui://geox/workspace-v1.html` | `geox_workspace_v1_open` | ✅ YES (11.5 KB) | ✅ PASS (Evidence DOM) | ✅ PASS (SEP-1865) | ✅ PASS (Message) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/workspace-v1` | `geox_workspace_v1_open` | ✅ YES (11.5 KB) | ✅ PASS (Evidence DOM) | ✅ PASS (SEP-1865) | ✅ PASS (Message) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/workbench-v1.html` | `geox_workspace_v1_open` | ✅ YES (17.5 KB) | ✅ PASS (Evidence DOM) | ✅ PASS (SEP-1865) | ✅ PASS (Message) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/gravmag-studio.html` | `geox_gravmag_studio` | ✅ YES (32 KB) | ✅ PASS (Canvas2D Heatmap) | ✅ PASS (SEP-1865) | ✅ PASS (Preview mode) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/gravmag-studio` | `geox_gravmag_studio` | ✅ YES (32 KB) | ✅ PASS (Canvas2D Heatmap) | ✅ PASS (SEP-1865) | ✅ PASS (Preview mode) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/seismic-vision` | `geox_seismic_mode_router` | ✅ YES (22 KB) | ✅ PASS (2D/3D Viewer) | ✅ PASS (SEP-1865) | ✅ PASS (Empty trace msg) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/earth-volume` | `geox_earth_volume` | ✅ YES (9.3 KB) | ✅ PASS (3D Volume DOM) | ✅ PASS (SEP-1865) | ✅ PASS (Placeholder) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/judge-console` | `geox_judge_console` | ✅ YES (34 KB) | ✅ PASS (Audit Panel) | ✅ PASS (SEP-1865) | ✅ PASS (Empty queue) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/geoprobe` | `geox_geoprobe` | ✅ YES (35 KB) | ✅ PASS (Probe Dashboard) | ✅ PASS (SEP-1865) | ✅ PASS (Default probe) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/basin-explorer` | `geox_basin_explorer` | ✅ YES (20.7 KB) | ✅ PASS (Basin Panel) | ✅ PASS (SEP-1865) | ✅ PASS (No selection) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/earth-map` | `geox_earth_map` | ✅ YES (17.5 KB) | ✅ PASS (Cesium/OSM Map) | ✅ PASS (SEP-1865) | ✅ PASS (Global view) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/prospect-studio` | `geox_prospect_studio` | ✅ YES (35 KB) | ✅ PASS (Prospect Dashboard) | ✅ PASS (SEP-1865) | ✅ PASS (No closure) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/risk-console` | `geox_risk_console` | ✅ YES (34 KB) | ✅ PASS (Risk Audit) | ✅ PASS (SEP-1865) | ✅ PASS (Empty risk log) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/visual-hub` | `geox_visual_hub` | ✅ YES (142 KB) | ✅ PASS (5-in-1 Dashboard) | ✅ PASS (SEP-1865) | ✅ PASS (Hub ready) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/catalog` | `geox_catalog` | ✅ YES (3 KB) | ✅ PASS (Skills Registry) | ✅ PASS (SEP-1865) | ✅ PASS (44 skills) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/prospect-ui` | `geox_prospect_ui` | ✅ YES (35 KB) | ✅ PASS (Prospect View) | ✅ PASS (SEP-1865) | ✅ PASS (No prospect) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
| `ui://geox/geox-mcp-visual` | `geox_visual_hub` | ✅ YES (142 KB) | ✅ PASS (Visual Engine) | ✅ PASS (SEP-1865) | ✅ PASS (Dashboard ready) | ✅ PASS (Handled) | ✅ PASS (Parity) | **READY** |
