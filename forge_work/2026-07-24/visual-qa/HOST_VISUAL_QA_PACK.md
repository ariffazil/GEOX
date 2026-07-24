# Host Visual QA Pack — protocol evidence
Date: 2026-07-24T08:31Z

## Public URLs
- https://geox.arif-fazil.com/apps/ → HTTP 200 markers: 
- https://geox.arif-fazil.com/apps/well-desk/ → HTTP 200 markers: 
- https://geox.arif-fazil.com/apps/well-desk/p0-viz.html → HTTP 200 markers: SYNTHETIC,SYNTHETIC,SYNTHETIC,
- https://geox.arif-fazil.com/apps/well-desk/index.html → HTTP 200 markers: WellDesk,WellDesk,SYNTHETIC,

## In-process hydrate
open DEMO-KINABALU: ok=True data_class=DEMO curves=['GR', 'RES', 'DT', 'RHOB', 'NPHI'] n=200
open DEMO_WELL_A: ok=True data_class=DEMO curves=['GR', 'RES', 'DT', 'RHOB', 'NPHI'] n=200
open DEMO-VOLVE: ok=True data_class=OPEN_OSS curves=['GR', 'DT', 'RHOB', 'NPHI'] n=200
petro DEMO_WELL_A: ok=True seal=NOT_SEALED claim=ADVISORY

## MCP resource size
INFO:geox.unified:F1 inspection bypass: stdio mode detected — no token required for local use
INFO:geox.egs.registry:EGS state initialized: graph v1, claims=0, provenance_chains=0
INFO:geox.seismic.attribute_registry:Registered attribute: Amplitude
INFO:geox.seismic.attribute_registry:Registered attribute: Variance
INFO:geox.seismic.attribute_registry:Registered attribute: Sweetness
INFO:geox.seismic.attribute_registry:Registered attribute: Coherence
INFO:geox.seismic.attribute_registry:Registered attribute: Envelope
INFO:geox.seismic.attribute_registry:Registered attribute: Frequency Average
WARNING:geox.server:claims sub-server skipped (use geox_claim modes): Functions with **kwargs are not supported as tools
INFO:geox.unified:GEOX surface composed: 32 public + 30 internal = 80 runtime + 61 backward-compat tools
INFO:geox.unified:MCP App tools registered: geox_mission_board, geox_health_dashboard, well_desk_dashboard
INFO:geox.resources:geox.resources zen-pass applied to 0 existing resources (v2 contract)
INFO:geox.ui.resources:Workspace resource registered: ui://geox/workspace-v1.html
INFO:geox.ui.resources:GravMag Studio resource registered: ui://geox/gravmag-studio.html
INFO:geox.unified:MCP surface pruned: 1 non-canonical tools removed (profile=full)
INFO:geox.unified:  pruned: geox_applet_crossplot
INFO:geox.unified:MCP surface clean: 59 canonical tools exposed (profile=full)
INFO:geox.unified:tools/list_changed signal — clients should call tools/list to refresh. payload={"jsonrpc": "2.0", "method": "notifications/tools/list_changed", "params": {}}
INFO:geox.unified:resources/list_changed signal — clients should call resources/list. payload={"jsonrpc": "2.0", "method": "notifications/resources/list_changed", "params": {}}
INFO:geox.unified:prompts/list_changed signal — clients should call prompts/list. payload={"jsonrpc": "2.0", "method": "notifications/prompts/list_changed", "params": {}}
INFO:geox.unified:Phase 2 unified tools wired: 80 runtime tools registered with FastMCP
INFO:geox.governance.middleware:GeoxGovernanceMiddleware armed: 32 public tools, 122 executable tools (incl. compat), 2 irreversible tools, route_query=disabled
INFO:geox.apps.workbench:MCP App View registered: ui://geox/workbench-v1.html + readable (3 tools bound)
[07/24/26 08:31:13] WARNING  Component already exists:     local_provider.py:192
                             resource:ui://geox/well-desk@                      
INFO:geox.tools.mcp_apps_bridge:MCP App resource re-bound to real HTML: ui://geox/well-desk (23612B from apps/well-desk/p0-viz.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/seismic-vision (21894B from static/gui/seismic_viewer/index.html)
                    WARNING  Component already exists:     local_provider.py:192
                             resource:ui://geox/earth-volu                      
                             me@                                                
INFO:geox.tools.mcp_apps_bridge:MCP App resource re-bound to real HTML: ui://geox/earth-volume (9341B from apps/earth-volume/index.html)
                    WARNING  Component already exists:     local_provider.py:192
                             resource:ui://geox/judge-cons                      
                             ole@                                               
INFO:geox.tools.mcp_apps_bridge:MCP App resource re-bound to real HTML: ui://geox/judge-console (34295B from apps/judge-console/index.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/geoprobe (35137B from apps/prospect-ui/index.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/basin-explorer (20695B from static/gui/basin_explorer/index.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/earth-map (17470B from apps/workbench-v1.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/prospect-studio (35137B from apps/prospect-ui/index.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/risk-console (34295B from apps/judge-console/index.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/visual-hub (142676B from apps/geox-mcp-visual/index.html)
                    WARNING  Component already exists:     local_provider.py:192
                             resource:ui://geox/gravmag-st                      
                             udio@                                              
INFO:geox.tools.mcp_apps_bridge:MCP App resource re-bound to real HTML: ui://geox/gravmag-studio (32029B from src/geox_mcp/ui/static/gravmag_studio.html)
                    WARNING  Component already exists:     local_provider.py:192
                             resource:ui://geox/workspace-                      
                             v1@                                                
INFO:geox.tools.mcp_apps_bridge:MCP App resource re-bound to real HTML: ui://geox/workspace-v1 (17470B from apps/workbench-v1.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/workbench-v1 (17470B from apps/workbench-v1.html)
                    WARNING  Component already exists:     local_provider.py:192
                             resource:ui://geox/prospect-u                      
                             i@                                                 
INFO:geox.tools.mcp_apps_bridge:MCP App resource re-bound to real HTML: ui://geox/prospect-ui (35137B from apps/prospect-ui/index.html)
INFO:geox.tools.mcp_apps_bridge:MCP App resource registered: ui://geox/catalog (3015B from apps/site/catalog.html)
INFO:geox.tools.mcp_apps_bridge:Registered GEOX MCP Apps UI resources (ok=15 skipped=0 failed=0 total=15)
INFO:geox.mcp.tools_wiring:H2: geox_workspace tool registered
INFO:geox.mcp.tools_wiring:MANIFEST_ENRICH: enriched 31/32 canonical tools, skipped 0 (already enriched)
INFO:geox.tools.mcp_apps_bridge:Enriched 36 tools with MCP Apps UI metadata
ui://geox/well-desk bytes=23612 has_ui_init=True has_synth=True

NOTE: Live ChatGPT iframe screenshot still DEFERRED (requires human host session).
Protocol + public HTML + hydrate path = PASS for Batch D protocol gate.
