"""Tuas 2 — GEOX writes BOTH its organ-local ledger and the shared federation
telemetry from one call site.

Contract under test (2026-09-19 KITARAN audit, Tuas 2):
  * /var/lib/geox/metrics/tool_invocations.jsonl  — organ-local, AUTHORITATIVE,
    format frozen since KUTIP SAMPAH 2026-08-05.
  * /var/lib/arifos/metrics/tool_invocations.jsonl — shared federation ledger
    (/root/AAA/lib/invocation_log.py), an ADDITIVE mirror.

Read-only w.r.t. production: the invocation test routes both writers to tmp
paths via GEOX_TOOL_METRICS_PATH / GEOX_FEDERATION_METRICS_PATH. The live
organ-local ledger is only ever READ (format-freeze assertion).

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

LIVE_LOCAL = Path("/var/lib/geox/metrics/tool_invocations.jsonl")

# Frozen organ-local key set — must not drift.
LOCAL_KEYS = {
    "ts",
    "organ",
    "tool",
    "session_id",
    "actor_id",
    "ok",
    "duration_ms",
    "epoch",
}
# Shared contract keeps the same core names and adds exactly these.
FED_EXTRA_KEYS = {"host"}


def _counter():
    return importlib.import_module("geox_mcp.tool_invocation_counter")


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


# ── 1. both sinks receive the line ──────────────────────────────────────────


def test_one_call_writes_both_ledgers(tmp_path, monkeypatch):
    local = tmp_path / "organ_local.jsonl"
    fed = tmp_path / "federation.jsonl"
    monkeypatch.setenv("GEOX_TOOL_METRICS_PATH", str(local))
    monkeypatch.setenv("GEOX_FEDERATION_METRICS_PATH", str(fed))

    _counter().record_invocation(
        "geox_deep_time",
        session_id="SES-test-0001",
        actor_id="test-actor",
        ok=True,
        duration_ms=4.435,
    )

    lrows, frows = _rows(local), _rows(fed)
    assert len(lrows) == 1, f"organ-local ledger got {len(lrows)} lines"
    assert len(frows) == 1, f"federation ledger got {len(frows)} lines"

    lr, fr = lrows[0], frows[0]
    # same identity in both sinks
    for key in ("organ", "tool", "session_id", "actor_id", "ok", "duration_ms"):
        assert lr[key] == fr[key], f"{key} diverged: {lr[key]!r} != {fr[key]!r}"
    assert lr["organ"] == "GEOX"
    assert lr["tool"] == "geox_deep_time"
    assert abs(lr["epoch"] - fr["epoch"]) < 5.0


def test_failure_path_mirrors_ok_false(tmp_path, monkeypatch):
    local = tmp_path / "organ_local.jsonl"
    fed = tmp_path / "federation.jsonl"
    monkeypatch.setenv("GEOX_TOOL_METRICS_PATH", str(local))
    monkeypatch.setenv("GEOX_FEDERATION_METRICS_PATH", str(fed))

    _counter().record_invocation("geox_seismic_interpret", actor_id="test-actor", ok=False, duration_ms=1.0)

    assert _rows(local)[0]["ok"] is False
    assert _rows(fed)[0]["ok"] is False


# ── 2. format discipline on both sinks ──────────────────────────────────────


def test_organ_local_format_is_frozen(tmp_path, monkeypatch):
    """The organ-local line must keep EXACTLY the pre-Tuas-2 key set.

    No `host`, no `extra`, no rename — existing consumers read this path.
    """
    local = tmp_path / "organ_local.jsonl"
    fed = tmp_path / "federation.jsonl"
    monkeypatch.setenv("GEOX_TOOL_METRICS_PATH", str(local))
    monkeypatch.setenv("GEOX_FEDERATION_METRICS_PATH", str(fed))

    _counter().record_invocation("geox_basin", actor_id="test-actor", ok=True, duration_ms=31.667)

    lr = _rows(local)[0]
    assert set(lr) == LOCAL_KEYS, f"organ-local key drift: {sorted(set(lr) ^ LOCAL_KEYS)}"
    # microseconds + explicit UTC offset (datetime.now(UTC).isoformat())
    assert lr["ts"].endswith("+00:00") and "." in lr["ts"]
    assert lr["organ"] == "GEOX"
    assert isinstance(lr["epoch"], float)


def test_federation_line_matches_shared_contract(tmp_path, monkeypatch):
    local = tmp_path / "organ_local.jsonl"
    fed = tmp_path / "federation.jsonl"
    monkeypatch.setenv("GEOX_TOOL_METRICS_PATH", str(local))
    monkeypatch.setenv("GEOX_FEDERATION_METRICS_PATH", str(fed))

    _counter().record_invocation("geox_basin", actor_id="test-actor", ok=True, duration_ms=31.667)

    fr = _rows(fed)[0]
    assert set(fr) == LOCAL_KEYS | FED_EXTRA_KEYS, f"federation key drift: {sorted(set(fr))}"
    assert fr["ts"].endswith("Z")  # shared contract: second precision, Z suffix
    assert fr["host"]


def test_live_organ_local_ledger_still_wellformed():
    """The 580+ line production ledger must keep the frozen shape."""
    rows = _rows(LIVE_LOCAL)
    assert rows, f"live organ-local ledger missing: {LIVE_LOCAL}"
    assert len(rows) >= 580, f"live ledger shrank: {len(rows)} < 580"
    bad = [i for i, r in enumerate(rows) if set(r) != LOCAL_KEYS]
    assert not bad, f"{len(bad)} live rows have a drifted key set, first at line {bad[0] + 1}"


# ── 3. fail-soft: the local line must survive a broken mirror ───────────────


def test_mirror_failure_never_costs_the_local_line(tmp_path, monkeypatch):
    """If the federation sink cannot be written, the local line still lands.

    The sink is an existing DIRECTORY, so the contract's O_WRONLY open fails
    with EISDIR and log_invocation returns False — a genuine mirror failure,
    not a simulated one.
    """
    local = tmp_path / "organ_local.jsonl"
    fed_dir = tmp_path / "federation_sink.jsonl"
    fed_dir.mkdir()
    monkeypatch.setenv("GEOX_TOOL_METRICS_PATH", str(local))
    monkeypatch.setenv("GEOX_FEDERATION_METRICS_PATH", str(fed_dir))

    counter = _counter()
    counter.record_invocation("geox_map", actor_id="test-actor", ok=True, duration_ms=2.0)

    rows = _rows(local)
    assert len(rows) == 1 and rows[0]["tool"] == "geox_map"
    assert fed_dir.is_dir() and list(fed_dir.iterdir()) == []


def test_no_arguments_or_payloads_are_recorded(tmp_path, monkeypatch):
    """Identity only. No payload field may appear in either sink."""
    local = tmp_path / "organ_local.jsonl"
    fed = tmp_path / "federation.jsonl"
    monkeypatch.setenv("GEOX_TOOL_METRICS_PATH", str(local))
    monkeypatch.setenv("GEOX_FEDERATION_METRICS_PATH", str(fed))

    _counter().record_invocation("geox_well", session_id="SES-x", actor_id="test-actor", ok=True, duration_ms=3.0)

    for path in (local, fed):
        rec = _rows(path)[0]
        assert not ({"arguments", "args", "payload", "input", "content", "extra"} & set(rec)), sorted(rec)
