#!/bin/bash
# GEOX Unified MCP Server — Sovereign 13 Kernel + Dimension Native
# DITEMPA BUKAN DIBERI

echo "🔥 GEOX Unified Server Starting"
echo "   Version: v2026.05.01-KANON"
echo "   Seal: DITEMPA BUKAN DIBERI"
echo "   Transport: streamable-http on port 8081"
echo "   Governance: arifOS F1-F13"
echo "   Canonical entrypoint: server.py"

export GEOX_HOST=0.0.0.0
export GEOX_PORT=8081
export GEOX_PROFILE=full

exec python server.py --host 0.0.0.0 --port 8081
