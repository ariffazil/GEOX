"""Drive A-FORGE MCP over stdio (session-owned connection) to fire forge_canonize x3.

Works around STATELESS_WHITELIST: HTTP lane rejects non-whitelisted tools;
stdio transport carries session ownership per serve.ts:1077 guidance.
"""
import json
import os
import subprocess
import sys

CWD = "/root/A-FORGE"
FILES = [
    ("/root/GEOX/outputs/kl2_kinabalu/kl2_kinabalu_penetration_chart_v2.png",
     "kl2_kinabalu_penetration_chart_v2.png"),
    ("/root/GEOX/outputs/kl2_kinabalu/kl2_kinabalu_well_data_v2.xlsx",
     "kl2_kinabalu_well_data_v2.xlsx"),
    ("/root/GEOX/outputs/kl2_kinabalu/kl2_kinabalu_penetration_v2.py",
     "kl2_kinabalu_penetration_v2.py"),
]

env = {**os.environ, "FORGE_STDIO_ACTOR_ID": "qwen-fi003"}
errf = open("/tmp/aforge-stdio-stderr.log", "wb")
proc = subprocess.Popen(
    ["node", "dist/src/interfaces/mcp/cli.js", "serve", "--transport", "stdio"],
    cwd=CWD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errf, env=env,
)

def send(obj):
    proc.stdin.write((json.dumps(obj) + "\n").encode())
    proc.stdin.flush()

def recv():
    while True:
        line = proc.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if line.startswith(b"{"):
            return json.loads(line)

send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "fi003-canonize-stdio-driver", "version": "1.0"}}})
init = recv()
print("[init]", json.dumps(init.get("result", {}).get("serverInfo", init))[:300])
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

ok = 0
for i, (path, name) in enumerate(FILES):
    send({"jsonrpc": "2.0", "id": 100 + i, "method": "tools/call",
          "params": {"name": "forge_canonize",
                     "arguments": {"source_path": path, "category": "artifact",
                                   "sign": True, "target_name": name}}})
    resp = recv()
    if resp is None:
        print(f"[FAIL] {name}: no response (server died? see /tmp/aforge-stdio-stderr.log)")
        break
    content = resp.get("result", {}).get("content", [])
    text = content[0].get("text", "") if content else json.dumps(resp)[:400]
    is_err = bool(resp.get("result", {}).get("isError")) or resp.get("error")
    print(f"[{'ERR' if is_err else 'OK '}] {name}: {text[:600]}")
    ok += 0 if is_err else 1

proc.terminate()
errf.close()
print(f"\ncanonized={ok}/3")
sys.exit(0 if ok == 3 else 1)
