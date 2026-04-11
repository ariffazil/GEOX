#!/bin/bash
# GEOX Unified MCP Server — Higher Intelligence State
# DITEMPA BUKAN DIBERI

echo "🔥 GEOX REST Bridge Starting"
echo "   Version: v2026.04.11-REST"
echo "   Seal: DITEMPA BUKAN DIBERI"
echo "   Transport: HTTP on port 8000"
echo "   Governance: arifOS F1-F13"
echo "   Tools: Bridge + Dimensional + ACP + ToAC + CANON_9"
echo "   REST API: /health, /tools, /invoke"
echo "   MCP Endpoint: /mcp"

export GEOX_HOST=0.0.0.0
export GEOX_PORT=8000

exec python geox_rest_bridge.py --host 0.0.0.0 --port 8000
