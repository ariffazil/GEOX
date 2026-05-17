#!/bin/bash
# GEOX Dimension-Native MCP Server — HTTP Transport
# DITEMPA BUKAN DIBERI

echo "🔥 GEOX Dimension-Native Server Starting"
echo "   Version: v2026.05.17-UNIFIED"
echo "   Seal: DITEMPA BUKAN DIBERI"
echo "   Profile: ${GEOX_PROFILE:-vps}"
echo "   Transport: streamable-http on port 8081"
echo ""

export GEOX_HOST=0.0.0.0
export GEOX_PORT=8081
export PYTHONPATH=src

# Run canonical unified server
exec python -m geox_mcp.server --transport streamable-http --host 0.0.0.0 --port 8081
