#!/bin/bash
# GEOX Earth Intelligence Core — Entrypoint
# DITEMPA BUKAN DIBERI

echo "🔥 GEOX Earth Intelligence Core Starting"
echo "   Version: v2026.04.10-EIC"
echo "   Seal: DITEMPA BUKAN DIBERI"
echo "   Transport: HTTP on port 8000"

exec python -c "
import sys
sys.path.insert(0, '/app')
from geox.server import mcp
mcp.run(transport='http', host='0.0.0.0', port=8000)
"
