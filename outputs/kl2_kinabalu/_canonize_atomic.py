"""Atomic KL2 canonize: kernel ACT mint -> A-FORGE stdio lease -> forge_canonize x3.

Lane discovered 2026-09-07: stateless HTTP is whitelisted; stdio carries session
ownership; ACT binding requires caller actor == token actor; EXECUTE_REVERSIBLE
requires a kernel-issued lease naming the tool in scope.
"""
import json
import subprocess
import os
import urllib.request

KERNEL = "http://localhost:8088/mcp"
ACTOR = "qwen-fi003"


def kernel_rpc(method, params, session_hdr=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params}).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if session_hdr:
        headers["Mcp-Session-Id"] = session_hdr
    req = urllib.request.Request(KERNEL, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        sid = r.headers.get("Mcp-Session-Id") or session_hdr
        return json.loads(r.read().decode()), sid


init_r, sid = kernel_rpc("initialize", {
    "protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "fi003-canonize-atomic2", "version": "1.0"}})
kernel_rpc("notifications/initialized", {}, sid)
call_r, _ = kernel_rpc("tools/call", {
    "name": "arif_init",
    "arguments": {"mode": "light", "intent": "forge_canonize KL2 v2 trio (F13 GO)",
                  "actor_id": ACTOR}}, sid)
payload = json.loads(call_r["result"]["content"][0]["text"])
token = payload["session_token"]
kern_sid = payload["session_id"]
assert token.count(".") == 2 and token.startswith("act_v1."), "bad token"
print(f"[kernel] session={kern_sid} actor={payload.get('actor_id')}")

FILES = [
    ("/root/GEOX/outputs/kl2_kinabalu/kl2_kinabalu_penetration_chart_v2.png",
     "kl2_kinabalu_penetration_chart_v2.png"),
    ("/root/GEOX/outputs/kl2_kinabalu/kl2_kinabalu_well_data_v2.xlsx",
     "kl2_kinabalu_well_data_v2.xlsx"),
    ("/root/GEOX/outputs/kl2_kinabalu/kl2_kinabalu_penetration_v2.py",
     "kl2_kinabalu_penetration_v2.py"),
]
env = {**os.environ, "FORGE_STDIO_ACTOR_ID": ACTOR}
errf = open("/tmp/aforge-stdio-stderr4.log", "wb")
p = subprocess.Popen(
    ["node", "dist/src/interfaces/mcp/cli.js", "serve", "--transport", "stdio"],
    cwd="/root/A-FORGE", stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    stderr=errf, env=env)


def send(o):
    p.stdin.write((json.dumps(o) + "\n").encode())
    p.stdin.flush()


def recv():
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if line.startswith(b"{"):
            return json.loads(line)


send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                 "clientInfo": {"name": "fi003-canonize-atomic2", "version": "1.0"}}})
recv()
send({"jsonrpc": "2.0", "method": "notifications/initialized"})


def call(tool, args, i):
    send({"jsonrpc": "2.0", "id": i, "method": "tools/call",
          "params": {"name": tool, "arguments": args}})
    r = recv()
    if r is None:
        return None, True
    res = r.get("result", {})
    body = res.get("content", [{}])[0].get("text", json.dumps(r)[:500])
    is_err = bool(res.get("isError")) or bool(r.get("error")) or '"status": "ERROR"' in body or '"status":"ERROR"' in body
    return body, is_err


# lease: scope forge_canonize, reversible ceiling
lease_body, lease_err = call("forge_lease", {
    "mode": "request", "agent_id": ACTOR, "scope": ["forge_canonize"],
    "max_action_class": "EXECUTE_REVERSIBLE", "ttl_seconds": 1800,
    "reason": "KL2 v2 trio canonize — validator re-seal PASSED, F13 GO 2026-09-07",
    "session_id": kern_sid, "session_token": token, "actor_id": ACTOR}, 10)
print("--- lease ---")
print((lease_body or "NO RESPONSE")[:500])
lease_id = None
if not lease_err:
    try:
        lease_id = json.loads(lease_body).get("lease_id")
    except Exception:
        pass
if not lease_id:
    print("[ABORT] no lease_id — cannot proceed to canonize")
    p.terminate(); errf.close()
    raise SystemExit(1)
print(f"[lease] {lease_id}")

ok = 0
for i, (path, name) in enumerate(FILES):
    body, is_err = call("forge_canonize", {
        "source_path": path, "category": "artifact", "sign": True,
        "target_name": name, "session_token": token, "session_id": kern_sid,
        "actor_id": ACTOR, "lease_id": lease_id}, 100 + i)
    print(f"--- {name} [{'ERR' if is_err else 'OK'}] ---")
    print((body or "NO RESPONSE")[:900])
    ok += 0 if is_err else 1

p.terminate()
errf.close()
print(f"\ncanonized={ok}/3")
