#!/usr/bin/env bash
# ONE-COMMAND ROLLBACK of the GEOX dual-era MCP change (2026-09-15).
# Restores /opt/geox/src/geox_mcp/server.py from the pre-change backup, removes
# the added module, restarts the unit and re-verifies health + legacy surface.
set -euo pipefail
BK=/root/GEOX/.backup-geox-mcp-20260915
echo "[rollback] restoring server.py from $BK/server.py.bak.before-dual-era"
cp -a "$BK/server.py.bak.before-dual-era" /opt/geox/src/geox_mcp/server.py
if [ -f "$BK/stateless_era.py.added" ]; then
  mv -f /opt/geox/src/geox_mcp/stateless_era.py "$BK/stateless_era.py.rolledback" 2>/dev/null || true
fi
find /opt/geox/src/geox_mcp -name '__pycache__' -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
systemctl restart geox-mcp.service
sleep 12
echo "[rollback] unit state: $(systemctl is-active geox-mcp.service)"
curl -s -m 10 http://127.0.0.1:8081/health | python3 -c "import json,sys;d=json.load(sys.stdin);sd=d.get('surface_drift') or {};print('[rollback] health status=',d.get('status'),'surface_drift canonical/live=',sd.get('canonical_count'),sd.get('live_count'))"
echo "[rollback] modern probe (expected: 400 again on the pre-change code):"
curl -s -m 10 -o /dev/null -w '[rollback] server/discover HTTP %{http_code}\n' -X POST http://127.0.0.1:8081/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' -H 'Mcp-Method: server/discover' \
  -d '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{}}'
echo "[rollback] done"
