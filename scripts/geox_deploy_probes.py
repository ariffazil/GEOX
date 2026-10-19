#!/usr/bin/env python3
"""GEOX deploy probes — P0 patch (df23f352). Written BEFORE the deploy command runs.

Usage: python3 geox_deploy_probes.py [pre|post]
  pre  — measure PAST against live 2d6fde9b (expects vuln present: traversal writes)
  post — measure RESULT against patched tree (expects SCHEMA_REJECTION everywhere)

Probes (stateless MCP wire, strict httpx):
  P1  /health identity git_version + surface_drift (deploy identity metric)
  P2  F1b execution proof: relative traversal / absolute outside / symlink-in-root
      each → error_class=SCHEMA_REJECTION + ZERO filesystem writes (post)
  P3  FastMCP ValidationError (wrong-typed arg) → SCHEMA_REJECTION / -32602 (F3)
  P4  envelope on failed call → transport_status=OK, execution_status=FAILED (F2)
  P5  normal physics_section call (human path) → renders, artifacts returned
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8081"
MCP = f"{BASE}/mcp"
ROOT = "/tmp/geox"  # live default: GEOX_OUTPUT_DIR unset in /etc/geox/geox.env
results: list[tuple[str, str, str]] = []


def rec(name: str, ok: bool, detail: str) -> None:
    results.append((name, "PASS" if ok else "FAIL", detail))
    print(f"[{name}] {'PASS' if ok else 'FAIL'} — {detail}")


class Mcp:
    """Minimal streamable-HTTP MCP client (initialize → notifications/initialized → tools/call)."""

    def __init__(self) -> None:
        self.c = httpx.Client(timeout=180)
        self.sid = None
        self._init()

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        return h

    def _post(self, payload: dict) -> dict:
        r = self.c.post(MCP, headers=self._headers(), json=payload)
        if "mcp-session-id" in r.headers:
            self.sid = r.headers["mcp-session-id"]
        body = r.text
        if body.startswith("event:") or "\ndata:" in body or body.startswith("data:"):
            for line in body.splitlines():
                if line.startswith("data:"):
                    body = line[5:].strip()
                    break
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return {"_raw": body[:300], "_http": r.status_code}

    def _init(self) -> None:
        self._post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "deploy-probe", "version": "1"},
                },
            }
        )
        self.c.post(MCP, headers=self._headers(), json={"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, tool: str, args: dict) -> dict:
        return self._post(
            {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/call", "params": {"name": tool, "arguments": args}}
        )


def result_dict(resp: dict) -> dict:
    res = resp.get("result", {})
    sc = res.get("structuredContent") or res.get("structured_content") or {}
    return sc if isinstance(sc, dict) else {}


def envelope(resp: dict) -> dict:
    sc = result_dict(resp)
    return (sc.get("_evidence_envelope") or {}).get("_envelope", {}) or {}


def main() -> int:
    phase = sys.argv[1] if len(sys.argv) > 1 else "post"
    m = Mcp()

    # P1 — deploy identity
    h = httpx.get(f"{BASE}/health", timeout=30).json()
    gv = h.get("git_version") or h.get("identity", {}).get("value")
    sd = h.get("surface_drift", {})
    import subprocess

    head = subprocess.run(
        ["git", "-C", "/opt/geox", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    exp = f"geox-{head}" if head else None
    rec("P1_identity", exp is not None and gv == exp, f"git_version={gv} expected={exp}")
    rec("P1_surface", sd.get("ok") and sd.get("live_count") == 27, f"surface_drift ok={sd.get('ok')} live={sd.get('live_count')}")

    # P2 — F1b execution proof (mkdir ordering is the whole claim)
    # A relative out_dir resolves against THREE different bases on the unpatched tree
    # (service CWD, renderer CWD, absolute) — check every candidate write location.
    # NOTE: geox-mcp.service runs under systemd PrivateTmp — the service sees
    # /tmp/systemd-private-*/tmp as its /tmp. Probe BOTH views.
    import glob as _glob

    _priv = _glob.glob("/tmp/systemd-private-*-geox-mcp.service-*/tmp")
    _stmp = _priv[0] if _priv else "/tmp"
    _sroot = f"{_stmp}/geox"
    probes = [
        (
            "P2a_traversal",
            "../pwn_probe_geox",
            [f"{_stmp}/pwn_probe_geox", "/opt/pwn_probe_geox", "/opt/geox/geox/skills/subsurface/pwn_probe_geox"],
        ),
        ("P2b_absolute", "/tmp/pwn_probe_geox_abs", [f"{_stmp}/pwn_probe_geox_abs", "/tmp/pwn_probe_geox_abs"]),
        (
            "P2c_symlink",
            "link_probe",
            [
                f"{_stmp}/pwn_probe_geox_sym",
                "/tmp/pwn_probe_geox_sym",
                "/opt/geox/link_probe",
                "/opt/geox/geox/skills/subsurface/link_probe",
            ],
        ),
    ]
    # symlink INSIDE the service's output root pointing outside it
    import os

    link = f"{_sroot}/link_probe"
    if os.path.islink(link) or os.path.exists(link):
        try:
            os.unlink(link)
        except OSError:
            shutil.rmtree(link)
    try:
        os.symlink("/tmp/pwn_probe_geox_sym", link, target_is_directory=True)
    except Exception as e:  # noqa: BLE001
        rec("P2c_symlink_setup", False, str(e))

    for name, od, outsides in probes:
        for outside in outsides:
            clean(outside)
        resp = m.call("geox_model", {"mode": "physics_section", "theme": "dark", "out_dir": od})
        sc = result_dict(resp)
        wrote = [p for p in outsides if os_path_exists(p)]
        leaked = [p for p in (sc.get("artifacts") or []) if not p.startswith(ROOT)]
        if phase == "post":
            ok = (
                sc.get("status") == "ERROR"
                and sc.get("error_class") == "SCHEMA_REJECTION"
                and not wrote
                and not (sc.get("artifacts") or [])
            )
            rec(name, ok, f"status={sc.get('status')} class={sc.get('error_class')} wrote_outside={wrote}")
        else:
            rec(name, not (wrote or leaked), f"(PAST) status={sc.get('status')} wrote={wrote} leaked_artifacts={leaked}")

    # P3 — F3: wrong-typed argument → FastMCP ValidationError must map to SCHEMA_REJECTION/-32602
    resp = m.call("geox_model", {"mode": "physics_section", "theme": ["not", "a", "string"]})
    sc = result_dict(resp)
    txt = json.dumps(resp)
    is_schema = "SCHEMA_REJECTION" in txt or "-32602" in txt
    is_internal = "-32001" in txt or "INTERNAL_ERROR" in txt
    rec(
        "P3_schema_rejection",
        is_schema and not is_internal,
        f"schema={is_schema} internal={is_internal} http_or_code={resp.get('error', {}).get('code') if isinstance(resp.get('error'), dict) else None}",
    )

    # P4 — F2 envelope: tool failure is execution FAILED, transport OK
    resp = m.call("geox_model", {"mode": "physics_section", "theme": "neon"})
    env = envelope(resp)
    if env:
        ok = env.get("transport_status") == "OK" and env.get("execution_status") == "FAILED"
        rec(
            "P4_envelope",
            ok,
            f"transport={env.get('transport_status')} execution={env.get('execution_status')} artifact={env.get('artifact_status')}",
        )
    else:
        rec("P4_envelope", False, f"no envelope; keys={list(result_dict(resp).keys())[:8]}")

    # P5 — human path: normal render, artifacts present, no raw traceback
    clean(f"{ROOT}/asas_malam_xs.svg")
    resp = m.call("geox_model", {"mode": "physics_section", "theme": "dark"})
    sc = result_dict(resp)
    arts = sc.get("artifacts") or []
    err = sc.get("error") or ""
    ok = (sc.get("status") in ("OK", "BLOCKED_CONFIDENTIALITY_GATE")) and bool(arts) and "Traceback" not in err
    rec("P5_human_path", ok, f"status={sc.get('status')} artifacts={len(arts)} traceback_leak={'Traceback' in err}")

    fails = [r for r in results if r[1] == "FAIL"]
    print(f"\n== {phase.upper()} SUMMARY: {len(results) - len(fails)}/{len(results)} PASS ==")
    return 1 if fails else 0


def clean(p: str) -> None:
    import os

    if os.path.islink(p) or os.path.isfile(p):
        os.unlink(p)
    elif os.path.isdir(p):
        shutil.rmtree(p)


def os_path_exists(p: str) -> bool:
    import os

    return os.path.lexists(p)


def os_path_islink(p: str) -> bool:
    import os

    return os.path.islink(p)


if __name__ == "__main__":
    sys.exit(main())
