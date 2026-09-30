#!/usr/bin/env bash
# GEOX dual-era MCP probe suite — every claim in the report comes from here.
# Usage: bash probe_dual_era.sh <base_url>   e.g. http://127.0.0.1:8081
BASE="${1:-http://127.0.0.1:8081}"
MCP="$BASE/mcp"
echo "############ PROBE SUITE against $BASE ############"
echo
echo "===== [1] MODERN stateless server/discover (MCP-Protocol-Version: 2026-07-28 + Mcp-Method) ====="
curl -s -m 15 -w "\n--HTTP %{http_code}--\n" -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2026-07-28" -H "Mcp-Method: server/discover" \
  -d '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},"io.modelcontextprotocol/clientInfo":{"name":"audit","version":"1"}}}}'
echo
echo "===== [1b] MODERN headers dump for [1] ====="
curl -s -D - -o /dev/null -m 15 -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2026-07-28" -H "Mcp-Method: server/discover" \
  -d '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}' | tr -d '\r' | grep -E "^HTTP|^mcp-protocol-version|^x-mcp-era|^content-type"
echo
echo "===== [2] LEGACY 2025-11-25 initialize ====="
INIT_HDRS=$(mktemp)
curl -s -D "$INIT_HDRS" -o /tmp/geox_probe_init.json -m 15 -w "--HTTP %{http_code}--\n" -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"legacy-audit","version":"1"}}}'
python3 -c "import json;d=json.load(open('/tmp/geox_probe_init.json'));r=d['result'];print('negotiated protocolVersion =',r['protocolVersion']);print('serverInfo =',r['serverInfo']['name'],r['serverInfo'].get('version'))"
SID=$(tr -d '\r' < "$INIT_HDRS" | grep -i "^mcp-session-id" | awk '{print $2}')
echo "mcp-session-id = $SID"
echo "--- [2b] legacy notifications/initialized ---"
curl -s -m 15 -o /dev/null -w "--HTTP %{http_code}--\n" -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SID" -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
echo "--- [2c] legacy tools/list (session) ---"
curl -s -m 25 -o /tmp/geox_probe_tools.json -w "--HTTP %{http_code}--\n" -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: $SID" -d '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}}'
python3 -c "
import json
d=json.load(open('/tmp/geox_probe_tools.json'))
tools=d['result']['tools']
print('LEGACY tools/list count =', len(tools))
print('names =', ','.join(sorted(t['name'] for t in tools)))
print('ttlMs present =', 'ttlMs' in d['result'])
"
echo
echo "===== [3] MODERN stateless tools/list (no session id, era-declared) ====="
curl -s -m 25 -o /tmp/geox_probe_stateless_tools.json -w "--HTTP %{http_code}--\n" -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2026-07-28" -H "Mcp-Method: tools/list" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
python3 -c "
import json
try:
    d=json.load(open('/tmp/geox_probe_stateless_tools.json'))
except Exception as e:
    print('non-JSON body:', open('/tmp/geox_probe_stateless_tools.json').read()[:200]); raise SystemExit(0)
if 'result' in d:
    t=d['result']['tools']
    print('STATELESS tools/list count =', len(t))
    print('first5 =', [x['name'] for x in t[:5]])
else:
    print('ERROR payload:', json.dumps(d)[:300])
"
echo
echo "===== [4] MODERN stateless tools/call (no session id) ====="
curl -s -m 30 -o /tmp/geox_probe_stateless_call.json -w "--HTTP %{http_code}--\n" -X POST "$MCP" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2026-07-28" -H "Mcp-Method: tools/call" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"geox_list_registered_sources","arguments":{},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28"}}}'
head -c 500 /tmp/geox_probe_stateless_call.json; echo
echo
echo "===== [5] HEALTH ====="
curl -s -m 15 -w "\n--HTTP %{http_code}--\n" "$BASE/health" -o /tmp/geox_probe_health.json
python3 -c "
import json
d=json.load(open('/tmp/geox_probe_health.json'))
print('status =', d.get('status'), '| kernel_verdict =', d.get('kernel_verdict'), '| version =', d.get('version'))
sd=d.get('surface_drift') or {}
print('surface_drift =', json.dumps(sd))
print('canonical==live==31 ?', sd.get('canonical_count')==sd.get('live_count')==31)
"
echo "############ END ############"
