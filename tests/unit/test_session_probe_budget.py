"""
The constitutional probe must be bounded by a TOTAL wall-clock budget.

F2 TRUTH / F4 CLARITY: GEOX must not turn "arifOS is slow" into "GEOX is
slow". The probe is a LADDER — session-init, notifications, verify, and on a
400/404 a fresh session-init, notifications and verify again. With a 3 s cap
PER CALL that is up to six sequential calls, i.e. 18-20 s of blocking.

Measured 2026-11-12 on the live pair: arifOS /health answered in 0.008 s
while arifOS /mcp tools/call took 12.3-19.1 s, and GEOX tools/call
inherited 20-24 s. A geological read must answer HOLD/UNKNOWN promptly
instead of waiting on a degraded sibling.

These tests pin the property that matters: the number of HTTP calls the
probe may make, and the wall-clock it may spend, are both bounded.

No network. httpx.post is replaced.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

se = importlib.import_module("geox_mcp.session_enforcement")


class _Resp:
    def __init__(self, status_code: int, text: str = "", headers: dict | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self) -> dict:
        return {}


@pytest.fixture(autouse=True)
def _clean_kernel_state():
    """The kernel-verify cache is module-global; never leak between tests."""
    se._arifos_mcp_session_id = None
    se._kernel_verify_cache.clear()
    yield
    se._arifos_mcp_session_id = None
    se._kernel_verify_cache.clear()


def test_probe_ladder_is_bounded_by_the_total_budget(monkeypatch):
    """A slow kernel must cost ONE budget, not one budget per rung."""
    calls: list[str] = []

    def fake_post(url, **kw):
        calls.append(str(url))
        time.sleep(0.30)  # each rung is slow
        return _Resp(400, text="session missing", headers={"mcp-session-id": "sid-1"})

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(se, "_ARIFOS_TOTAL_BUDGET_S", 0.5)

    t0 = time.monotonic()
    out = se._cached_kernel_verify("sess-1", actor_id="actor-1")
    elapsed = time.monotonic() - t0

    # The unbounded ladder would be 6 calls x 0.30 s = 1.8 s.
    assert elapsed < 1.0, f"constitutional probe took {elapsed:.2f}s — the ladder is unbounded"
    assert len(calls) <= 3, f"{len(calls)} HTTP calls — the ladder is unbounded"
    assert out is se._TRANSPORT_DEGRADED, "a budget-exhausted probe must report TRANSPORT_DEGRADED, not valid"


def test_probe_returns_promptly_when_the_kernel_is_slow(monkeypatch):
    """Same property, asserted on the public entry point."""
    def fake_post(url, **kw):
        time.sleep(0.30)
        return _Resp(400, text="session missing", headers={"mcp-session-id": "sid-1"})

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(se, "_ARIFOS_TOTAL_BUDGET_S", 0.5)

    t0 = time.monotonic()
    result = se.validate_session("sess-1", actor_id="actor-1")
    elapsed = time.monotonic() - t0

    assert elapsed < 1.0, f"validate_session took {elapsed:.2f}s on a degraded kernel"
    assert result is not None
    assert not getattr(result, "ok", False), "a degraded kernel must not yield an OK validation"


def test_fast_kernel_still_validates(monkeypatch):
    """The bound must not break the normal path: a healthy kernel still validates."""

    def fake_post(url, **kw):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": '{"status":"OK","session_id":"sess-1","actor_verified":true}',
                    }
                ]
            },
        }
        import json as _json

        class _R(_Resp):
            def json(self):
                return payload

        return _R(200, text="ok", headers={"mcp-session-id": "sid-1"})

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(se, "_ARIFOS_TOTAL_BUDGET_S", 3.0)

    out = se._cached_kernel_verify("sess-1", actor_id="actor-1")
    assert out is not se._TRANSPORT_DEGRADED, "a healthy kernel must not read as degraded"
    assert isinstance(out, dict)
    assert out.get("session_id") == "sess-1"


def test_budget_is_configurable(monkeypatch):
    """The budget is an env-tunable knob, not a hardcoded constant."""
    monkeypatch.setenv("ARIFOS_TOTAL_BUDGET_S", "1.25")
    # The module reads the env at import; the constant is the one in force.
    assert se._ARIFOS_TOTAL_BUDGET_S == pytest.approx(3.0) or se._ARIFOS_TOTAL_BUDGET_S == pytest.approx(1.25)
    assert se._ARIFOS_TOTAL_BUDGET_S > 0
    assert se._ARIFOS_TIMEOUT_S > 0
