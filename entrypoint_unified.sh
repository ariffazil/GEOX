#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DEPRECATED — Use entrypoint.sh instead                                    ║
# ║                                                                             ║
# ║  Both entrypoints now exec the same canonical server:                       ║
# ║    python -m geox_mcp.server                                                ║
# ║                                                                             ║
# ║  This file kept for backward compat. Scheduled removal: 2026-07-30.         ║
# ║  DITEMPA BUKAN DIBERI                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

echo "⚠️  WARNING: entrypoint_unified.sh is deprecated. Use entrypoint.sh."
echo "   Both point to the same canonical server: src/geox_mcp/server.py"

export GEOX_HOST=0.0.0.0
export GEOX_PORT=8081
export PYTHONPATH=src

exec python -m geox_mcp.server --transport streamable-http --host 0.0.0.0 --port 8081
