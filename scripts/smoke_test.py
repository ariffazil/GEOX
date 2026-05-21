#!/usr/bin/env python3
"""
GEOX Smoke Test — Full Pipeline Verification
═══════════════════════════════════════════════════════════════════════════════
Boots server → ingests LAS → forward model → anomalous contrast → verifies LEM.
Exit 0 = all good. Exit 1 = failure with details printed.
DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

BASE = "http://127.0.0.1:8766"
FIXTURE_LAS = Path(__file__).parent.parent / "fixtures" / "geox_smoke_test.las"
TIMEOUT_S = 30


def _req(method: str, path: str, payload: dict | None = None) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if method == "POST" and payload is not None:
        req.add_header("Accept", "application/json, text/event-stream")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode()
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body}


def _mcp_call(tool_name: str, arguments: dict) -> dict:
    """Call a tool via the legacy JSON-RPC POST handler."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    resp = _req("POST", "/mcp", payload)
    # FastMCP streamable-http with json_response=True returns JSON-RPC envelope
    result = resp.get("result", {})
    if isinstance(result, dict) and "content" in result:
        content = result["content"]
        if content and isinstance(content, list) and "text" in content[0]:
            try:
                return json.loads(content[0]["text"])
            except json.JSONDecodeError:
                return {"raw_text": content[0]["text"]}
    # Direct result (sometimes FastMCP returns the result object directly)
    if isinstance(result, dict) and "execution_status" in result:
        return result
    return result


def main() -> int:
    print("[SMOKE] Starting GEOX smoke test pipeline...")

    # ── 1. BOOT SERVER ───────────────────────────────────────────────────────
    print("[SMOKE] Booting server on port 8766...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "geox_mcp.server", "--host", "127.0.0.1", "--port", "8766"],
        cwd=str(Path(__file__).parent.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for health
    healthy = False
    for i in range(TIMEOUT_S):
        try:
            resp = _req("GET", "/health")
            if resp.get("status") == "healthy":
                healthy = True
                print(f"[SMOKE] Server healthy after {i+1}s")
                break
        except Exception:
            pass
        time.sleep(1)

    if not healthy:
        print("[SMOKE] FAIL: Server did not become healthy")
        proc.terminate()
        return 1

    # ── 2. INGEST LAS ────────────────────────────────────────────────────────
    print("[SMOKE] Ingesting fixture LAS...")
    ingest = _mcp_call(
        "geox_data_ingest_bundle",
        {
            "source_uri": str(FIXTURE_LAS.absolute()),
            "source_type": "well",
            "well_id": "smoke_well",
            "standardize_curves": True,
            "normalize_units": True,
        },
    )
    if ingest.get("claim_state") not in ("INGESTED", "FILE_IMPORTED", "RAW_OBSERVATION"):
        print("[SMOKE] FAIL: Ingest did not succeed:", ingest.get("claim_state"))
        proc.terminate()
        return 1
    print("[SMOKE] Ingest OK:", ingest.get("claim_state"))
    time.sleep(1)  # Let artifact store settle before next call

    # ── 3. FORWARD MODEL (well mode) ─────────────────────────────────────────
    print("[SMOKE] Running forward_model_synthetic from well_id...")
    # Retry once on transient failure
    fm = None
    for attempt in range(2):
        fm = _mcp_call(
        "geox_forward_model_synthetic",
        {
            "well_id": "smoke_well",
            "wavelet_type": "ricker",
            "wavelet_freq": 25,
            "output_format": "compact",
        },
    )
        if fm and fm.get("execution_status") == "SUCCESS":
            break
        if attempt == 0:
            time.sleep(1)
    if not fm or fm.get("execution_status") != "SUCCESS":
        print("[SMOKE] FAIL: Forward model failed:", fm.get("execution_status") if fm else "no_response", "| error:", fm.get("error_code") if fm else "none")
        proc.terminate()
        return 1
    pa = fm.get("primary_artifact", {})
    print(f"[SMOKE] Forward model OK | samples={pa.get('synthetic_length_samples')} | depth={pa.get('depth_range_m')}")

    # ── 4. LEM ENVELOPE CHECKS ───────────────────────────────────────────────
    print("[SMOKE] Verifying LEM envelope contract...")
    prov = fm.get("provenance", {})
    eq = prov.get("equations_used", [])
    if "AI = Vp × ρ" not in eq:
        print("[SMOKE] FAIL: LEM equation 'AI = Vp × ρ' missing from provenance")
        proc.terminate()
        return 1
    conf = fm.get("confidence", {})
    if "sensitivity_to" not in conf:
        print("[SMOKE] FAIL: LEM sensitivity_to missing from confidence")
        proc.terminate()
        return 1
    print("[SMOKE] LEM envelope OK")

    # ── 5. ANOMALOUS CONTRAST ────────────────────────────────────────────────
    print("[SMOKE] Running anomalous_contrast_detector...")
    ac = _mcp_call(
        "geox_anomalous_contrast_detector",
        {
            "ai_profile": [4_000_000.0, 4_200_000.0, 6_500_000.0],
            "depth": [1000.0, 1005.0, 1010.0],
            "formation_tops": {"Carbonate_Top": 1000.0},
            "geological_boundary_tolerance_m": 10.0,
        },
    )
    if ac.get("execution_status") != "SUCCESS":
        print("[SMOKE] FAIL: Anomalous contrast failed:", ac.get("execution_status"))
        proc.terminate()
        return 1
    pa_ac = ac.get("primary_artifact", {})
    if pa_ac.get("law_capsule") != "LC#28":
        print("[SMOKE] FAIL: LC#28 law capsule missing")
        proc.terminate()
        return 1
    print(f"[SMOKE] Anomalous contrast OK | anomalies={len(pa_ac.get('anomalies', []))} | law_capsule={pa_ac.get('law_capsule')}")

    # ── 6. SHUTDOWN ──────────────────────────────────────────────────────────
    print("[SMOKE] Shutting down server...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    print("[SMOKE] ═══════════════════════════════════════════════════════════════")
    print("[SMOKE] ALL CHECKS PASSED")
    print("[SMOKE] ═══════════════════════════════════════════════════════════════")
    return 0


if __name__ == "__main__":
    sys.exit(main())
