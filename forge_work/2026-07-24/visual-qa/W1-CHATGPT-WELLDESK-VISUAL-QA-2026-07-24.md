# W1 — ChatGPT WellDesk Visual QA
**Date:** 2026-07-24T09:54Z  
**Agent:** Grok FI-007  
**Runtime pin:** `geox-51396db0` → surface regen after W2

## Acceptance matrix

| ID | Task | Result |
|----|------|--------|
| **W1.1** | MCP `geox_well_desk` mode=open well_id=DEMO_WELL_A | **PASS** — curves+depths+data_class=DEMO · UI `ui://geox/well-desk` |
| **W1.2** | Host shell `ui://geox/well-desk` (p0-viz) | **PASS (protocol)** — public HTTP 200, ui/initialize present, tracks after host-sim tool-result |
| **W1.3** | Screenshots under `visual-qa/` | **PASS (agent host-sim)** — PNGs below |
| **W1.4** | mode=petro | **PASS** — ok, seal_status path ADVISORY / NOT_SEALED, UI bound |

## Screenshots (this session)

| File | What |
|------|------|
| `chatgpt-well-desk-p0-viz-public.png` | Public p0-viz standalone scaffold |
| `chatgpt-well-desk-index-public.png` | Public full modular WellDesk |
| `chatgpt-well-desk-p0-viz-local-standalone.png` | Local file standalone |
| `chatgpt-well-desk-host-sim-open-DEMO_WELL_A.png` | Host-sim tool-result hydrate DEMO_WELL_A (tracks + DEMO badge) |
| `chatgpt-well-desk-host-sim-petro-DEMO_WELL_A.png` | Host-sim petro path |
| `chatgpt-well-desk-public-host-sim-DEMO_WELL_A.png` | Public URL + host-sim postMessage |

## Honest residual (F2 / F7)

**Live ChatGPT (or Claude Desktop) iframe session still needs human host login.**  
This pack proves:
1. tool open/petro channels  
2. p0-viz host bridge (`ui/initialize` + `tool-result` hydrate)  
3. public HTML twin + pixel evidence  

It does **not** claim a sealed ChatGPT connector screenshot until Arif (or operator) captures one inside the ChatGPT MCP Apps host. Filename prefix `chatgpt-` marks the intended host surface, not a ChatGPT session capture.

## Prove

```bash
cd /root/GEOX && make readiness-test
PYTHONPATH=src .venv/bin/python3 -c "..."  # geox_well_desk open DEMO_WELL_A
ls forge_work/2026-07-24/visual-qa/*.png
```

DITEMPA BUKAN DIBERI
