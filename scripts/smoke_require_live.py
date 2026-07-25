#!/usr/bin/env python3
"""GEOX_REQUIRE_LIVE fail-closed smoke (P1 · 2026-07-25).

Exercises offline-stub fetchers under GEOX_REQUIRE_LIVE=1 and asserts
RequireLiveError (fail closed). Without the flag, stubs still stamp
ext_witness_ready=False.

Exit 0 = green. Exit 1 = regression.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import os
import sys

# Ensure src on path when run as script
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def main() -> int:
    from geox_mcp.ext_witness_stamp import RequireLiveError, stamp_and_gate, stamp_ext_witness

    failures: list[str] = []

    # 1) Stamp always present
    stamped = stamp_ext_witness(
        {"ok": True, "mode": "offline_stub", "note": "smoke"},
        tool_name="geox_earthquake_catalog",
    )
    if stamped.get("ext_witness_ready") is not False:
        failures.append("offline_stub must set ext_witness_ready=False")
    if stamped.get("data_mode") != "offline_stub":
        failures.append(f"expected data_mode=offline_stub got {stamped.get('data_mode')}")

    # 2) Fail closed under REQUIRE_LIVE
    os.environ["GEOX_REQUIRE_LIVE"] = "1"
    try:
        stamp_and_gate(
            {"ok": True, "mode": "offline_stub"},
            tool_name="geox_earthquake_catalog",
        )
        failures.append("GEOX_REQUIRE_LIVE=1 must raise RequireLiveError on offline_stub")
    except RequireLiveError as e:
        if e.mode != "offline_stub":
            failures.append(f"RequireLiveError.mode={e.mode!r} expected offline_stub")

    # 3) Live allowed under REQUIRE_LIVE
    try:
        live = stamp_and_gate(
            {"ok": True, "mode": "live", "count": 1},
            tool_name="geox_earthquake_catalog",
        )
        if not live.get("ext_witness_ready"):
            failures.append("live must be ext_witness_ready=True")
    except RequireLiveError as e:
        failures.append(f"live must not raise: {e}")

    # 4) Real offline fetcher → REQUIRE_LIVE must fail closed
    try:
        import dataclasses

        from geox_core.io.usgs_earthquake_fetcher import EarthquakeQuery, USGSEarthquakeFetcher

        os.environ.setdefault("GEOX_USGS_EQ_OFFLINE", "1")
        os.environ["GEOX_REQUIRE_LIVE"] = "1"
        fetcher = USGSEarthquakeFetcher()
        res = fetcher.query(EarthquakeQuery(limit=5))
        if hasattr(res, "model_dump"):
            payload = res.model_dump()
        elif dataclasses.is_dataclass(res):
            payload = dataclasses.asdict(res)
        else:
            payload = dict(getattr(res, "__dict__", {}))
        try:
            stamp_and_gate(payload, tool_name="geox_earthquake_catalog")
            failures.append("USGS offline_stub must raise RequireLiveError under GEOX_REQUIRE_LIVE=1")
        except RequireLiveError:
            pass  # expected
    except Exception as exc:  # noqa: BLE001
        failures.append(f"fetcher path error: {type(exc).__name__}: {exc}")

    os.environ.pop("GEOX_REQUIRE_LIVE", None)

    if failures:
        print("FAIL smoke_require_live:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("PASS smoke_require_live: stamp + GEOX_REQUIRE_LIVE fail-closed")
    return 0


def normalize_stub_mode(payload: dict) -> str:
    from geox_mcp.ext_witness_stamp import normalize_mode

    return normalize_mode(payload.get("mode"))


if __name__ == "__main__":
    raise SystemExit(main())
