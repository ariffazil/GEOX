"""GEOX stabilisation — Phase 0.2 contract freeze + invariant tests.

AUTHORED BY: 555-ASI (verifier), 2026-10-28. Delivered as text; materialised here by 333-AGI with
ONE mechanical correction: ``tools/list`` must send ``params`` (the authored text sent ``arguments``,
which is not a valid request-object key). No assertion was altered.

Read-only: probes live MCP + /health, reads baseline JSON. stdlib only.
Skips cleanly if GEOX (:8081) is unreachable or the baseline file is absent.

EXPECTED RED TODAY (xfail strict=True, marker removed in the SAME commit as its fix):
  count-invariant x2      -> fix: S2 (duplicate removal OR honest counter with duplicate names)
  health-parity x2        -> fix: S1 (one probe, named fields, derived status)
  annotations destructive -> fix: S4
  annotations openworld   -> fix: S4
  geox_workspace ghost    -> fix: HOLD-3 (drop llms.txt claim) or restore tool
  contrast_metabolize flat-> fix: S3
Plain-red today (no marker, must go green by the fix):
  test_health_reasons_never_contain_the_literal_kernel_not_SEAL
"""

from __future__ import annotations

import json
import socket
import urllib.request

import pytest

GEOX_MCP = "http://127.0.0.1:8081/mcp"
GEOX_HEALTH = "http://127.0.0.1:8081/health"
BASELINE = "/root/forge_work/geox-stabilise/baseline/tools_list.json"
HDRS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "User-Agent": "asi-555-contract-test/1.0",
}


def _geox_port_open() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8081), timeout=1.5):
            return True
    except OSError:
        return False


GEOX_UP = _geox_port_open()

pytestmark = pytest.mark.skipif(not GEOX_UP, reason="GEOX organ :8081 unreachable — not this machine's failure")


# ---------- helpers ----------


def _post(payload: dict, session_id: str | None = None) -> tuple[dict | None, str | None]:
    req = urllib.request.Request(GEOX_MCP, data=json.dumps(payload).encode(), headers=HDRS, method="POST")
    if session_id:
        req.add_header("Mcp-Session-Id", session_id)
    with urllib.request.urlopen(req, timeout=15) as resp:
        sid = resp.headers.get("Mcp-Session-Id") or session_id
        raw = resp.read().decode()
        ctype = resp.headers.get("Content-Type", "")
    if "event-stream" in ctype:
        for line in reversed(raw.splitlines()):
            if line.startswith("data:"):
                try:
                    msg = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    continue
                if isinstance(msg, dict) and "id" in msg:
                    return msg, sid
        return None, sid
    try:
        return json.loads(raw), sid
    except json.JSONDecodeError:
        return None, sid


def _mcp_session() -> tuple[str, dict]:
    msg, sid = _post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "asi-555-contract-test", "version": "1.0"},
            },
        }
    )
    if sid is None:
        pytest.skip("GEOX MCP handshake failed (no session id)")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return sid, (msg or {}).get("result", {})


def _tool_call(sid: str, name: str, args: dict | None = None) -> dict:
    msg, _ = _post({"jsonrpc": "2.0", "id": 99, "method": "tools/call", "params": {"name": name, "arguments": args or {}}}, sid)
    assert msg is not None, f"tools/call {name}: no parseable response"
    result = msg.get("result") or {}
    sc = result.get("structuredContent")
    if sc is None:
        content = (result.get("content") or [{}])[0].get("text", "")
        sc = json.loads(content) if content else {}
    return sc


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=10) as r:
        return json.loads(r.read().decode())


def _prop_sig(p: dict) -> tuple:
    """NAME+TYPE freeze signature. anyOf/oneOf frozen as a type-set (null ignored)."""
    if "type" in p:
        return ("type", p["type"])
    for key in ("anyOf", "oneOf"):
        if key in p:
            return (key, frozenset(s.get("type") for s in p[key] if isinstance(s, dict) and s.get("type") != "null"))
    return ("other", None)


# ---------- fixtures ----------


@pytest.fixture(scope="module")
def sid() -> str:
    s, _ = _mcp_session()
    return s


@pytest.fixture(scope="module")
def live_tools(sid) -> dict[str, dict]:
    msg, _ = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
    tools = ((msg or {}).get("result") or {}).get("tools")
    assert tools is not None, "tools/list returned no tools array"
    return {t["name"]: t for t in tools}


@pytest.fixture(scope="module")
def surface(sid) -> dict:
    return _tool_call(sid, "geox_surface_status")


@pytest.fixture(scope="module")
def geox_health() -> dict:
    return _get_json(GEOX_HEALTH)


@pytest.fixture(scope="module")
def baseline() -> dict:
    try:
        with open(BASELINE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.skip(f"baseline contract file absent: {BASELINE}")


# ---------- T_CONTRACT (Phase 0.2 freeze) ----------


def test_contract_baseline_required_and_property_names_types_still_present_live(live_tools, baseline):
    """INVARIANT: nothing frozen at baseline (required[] or property name+type) may be removed or retyped."""
    drift = []
    for bt in baseline["tools"]:
        name = bt["name"]
        lt = live_tools.get(name)
        if lt is None:
            drift.append(f"{name}: REMOVED from live surface")
            continue
        base, live = bt.get("inputSchema", {}), (lt.get("inputSchema") or {})
        missing_req = set(base.get("required", [])) - set(live.get("required", []))
        if missing_req:
            drift.append(f"{name}: required[] shrank: {sorted(missing_req)}")
        for pname, pdef in (base.get("properties") or {}).items():
            if pname not in (live.get("properties") or {}):
                drift.append(f"{name}.{pname}: property REMOVED")
            elif _prop_sig(pdef) != _prop_sig(live["properties"][pname]):
                drift.append(f"{name}.{pname}: retyped {_prop_sig(pdef)} -> {_prop_sig(live['properties'][pname])}")
    assert not drift, "CONTRACT FREEZE VIOLATED: " + "; ".join(drift)


# ---------- T_COUNT_INVARIANT ----------


@pytest.mark.xfail(
    strict=True, reason="S2 fix: honest counter (duplicate names reported) or duplicate removal after 888 decision"
)
def test_count_invariant_tools_total_equals_public_plus_nonpublic(surface):
    """INVARIANT: live_counts.tools_total == len(public) + len(nonpublic)."""
    lc = surface["live_counts"]
    total, pub, nonpub = lc["tools_total"], len(lc["tools_public_names"]), len(lc["tools_nonpublic_names"])
    assert total == pub + nonpub, (
        f"COUNT INVARIANT VIOLATED: tools_total={total} != public={pub} + nonpublic={nonpub} "
        f"(unaccounted {total - pub - nonpub} registry entry — duplicate canonical registration)"
    )


@pytest.mark.xfail(strict=True, reason="S2 fix: same — duplicates must be named, not absorbed")
def test_count_invariant_public_and_nonpublic_names_fully_account_for_tools_total(surface):
    """INVARIANT: set(public)|set(nonpublic) must equal the registry count — no name counted twice."""
    lc = surface["live_counts"]
    union = set(lc["tools_public_names"]) | set(lc["tools_nonpublic_names"])
    assert lc["tools_total"] == len(union), (
        f"COUNT INVARIANT VIOLATED: tools_total={lc['tools_total']} but distinct names={len(union)} "
        f"— {lc['tools_total'] - len(union)} entry/entries appear in neither list (duplicate)"
    )


# ---------- T_HEALTH_PARITY ----------


@pytest.mark.xfail(strict=True, reason="S1 fix: one probe emits kernel_verdict + registry_state on BOTH surfaces")
def test_health_parity_kernel_verdict_and_registry_state_identical_on_both_surfaces(geox_health, surface):
    """INVARIANT: one organ, one truth — both surfaces report the same kernel_verdict and registry_state."""
    missing = [
        n
        for n, d in (("/health", geox_health), ("surface_status", surface))
        if "kernel_verdict" not in d or "registry_state" not in d
    ]
    assert not missing, f"HEALTH PARITY VIOLATED: {missing} omit kernel_verdict/registry_state"
    assert geox_health["kernel_verdict"] == surface["kernel_verdict"], (
        "HEALTH PARITY VIOLATED: kernel_verdict disagrees between surfaces"
    )
    assert geox_health["registry_state"] == surface["registry_state"], (
        "HEALTH PARITY VIOLATED: registry_state disagrees between surfaces"
    )


@pytest.mark.xfail(
    strict=True, reason="S1 fix: top-level status derived from named fields, not the literal at tools_wiring.py:7552"
)
def test_health_no_bare_healthy_status_while_any_named_field_not_green(geox_health, surface):
    """INVARIANT: 'healthy' only when every named field is green."""
    lc = surface["live_counts"]
    named_green = (
        lc["tools_total"] == len(lc["tools_public_names"]) + len(lc["tools_nonpublic_names"])
        and surface["public_count"] == surface["public_count_target"] == len(surface["canonical_tools"])
        and geox_health.get("kernel_verdict") not in ("HOLD", "VOID")
    )
    assert surface["status"] != "healthy" or named_green, (
        f"HEALTH PARITY VIOLATED: status='healthy' while named fields not green "
        f"(total={lc['tools_total']}, kernel_verdict={geox_health.get('kernel_verdict')})"
    )


def test_health_reasons_never_contain_the_literal_kernel_not_SEAL(geox_health, surface):
    """INVARIANT: no reason list may assert 'kernel_not_SEAL' — name the measured cause instead."""
    blobs = json.dumps(geox_health) + json.dumps(surface)
    assert "kernel_not_SEAL" not in blobs, (
        "TRUTH DEFECT: 'kernel_not_SEAL' emitted while kernel is reachable and degraded for F1/F8"
    )


# ---------- T_ANNOTATIONS ----------


def test_annotations_readonly_hint_present_and_boolean_on_every_public_tool(live_tools):
    """INVARIANT: every public tool declares readOnlyHint as a boolean."""
    bad = [n for n, t in live_tools.items() if not isinstance((t.get("annotations") or {}).get("readOnlyHint"), bool)]
    assert not bad, f"ANNOTATION INVARIANT VIOLATED: readOnlyHint missing/non-boolean on {sorted(bad)}"


@pytest.mark.xfail(strict=True, reason="S4 fix: destructiveHint=true on geox_claim + geox_prospect")
def test_annotations_destructive_hint_true_on_geox_claim_and_geox_prospect(live_tools):
    """INVARIANT: irreversible modes must be visible as destructiveHint=true."""
    liars = [
        n
        for n in ("geox_claim", "geox_prospect")
        if (live_tools.get(n, {}).get("annotations") or {}).get("destructiveHint") is not True
    ]
    assert not liars, f"ANNOTATION UNDER-DECLARATION: destructiveHint not true on {liars}"


@pytest.mark.xfail(strict=True, reason="S4 fix: openWorldHint=true on paleobiodb_query/spatial/deep_time/map")
def test_annotations_openworld_hint_true_on_external_source_tools(live_tools):
    """INVARIANT: tools reading external/public data declare openWorldHint=true."""
    external = ("geox_paleobiodb_query", "geox_spatial", "geox_deep_time", "geox_map")
    liars = [n for n in external if (live_tools.get(n, {}).get("annotations") or {}).get("openWorldHint") is not True]
    assert not liars, f"ANNOTATION UNDER-DECLARATION: openWorldHint not true on {liars}"


@pytest.mark.xfail(strict=True, reason="HOLD-3 fix: drop geox_workspace claim from llms.txt, or restore the tool")
def test_annotations_tool_advertised_in_served_llms_txt_exists_on_surface(live_tools):
    """INVARIANT: no documented ghosts — every advertised tool exists on tools/list."""
    assert "geox_workspace" in live_tools, "GHOST TOOL: 'geox_workspace' advertised in llms.txt but absent from tools/list"


# ---------- T_SCHEMA_INTROSPECTABLE ----------


def test_schema_every_public_tool_exposes_nonempty_input_properties(live_tools):
    """INVARIANT: every public tool's inputSchema exposes at least one property."""
    empty = [n for n, t in live_tools.items() if not ((t.get("inputSchema") or {}).get("properties") or {})]
    assert not empty, f"SCHEMA INTROSPECTION VIOLATION: empty properties on {sorted(empty)}"


# Federation envelope params — carried by every GEOX tool, never domain signal.
# (Federation contract: all tools accept session_id/actor_id/trace_id.)
ENVELOPE_PARAMS = {"session_id", "actor_id", "trace_id"}


@pytest.mark.xfail(strict=True, reason="S3 fix: flatten geox_contrast_metabolize; keep `arguments` as deprecated alias")
def test_schema_contrast_metabolize_exposes_flat_params_with_arguments_deprecated_alias(live_tools):
    """INVARIANT: mode-dispatched tools expose flat DOMAIN params; `arguments` only as deprecated alias.

    Envelope params (session_id/actor_id/trace_id) are transport plumbing, not domain signal —
    counting them as 'flat' let this test pass against a tool that exposes zero domain params."""
    props = (live_tools["geox_contrast_metabolize"].get("inputSchema") or {}).get("properties") or {}
    flat = [k for k in props if k != "arguments" and k not in ENVELOPE_PARAMS]
    assert flat, (
        f"SCHEMA INTROSPECTION VIOLATION: geox_contrast_metabolize exposes zero flat DOMAIN params "
        f"(props={sorted(props)} after excluding arguments alias + envelope {sorted(ENVELOPE_PARAMS)})"
    )
    assert "arguments" in props, "ALIAS REGRESSION: deprecated `arguments` alias removed"
