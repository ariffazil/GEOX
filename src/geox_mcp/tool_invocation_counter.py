"""M6 utilization — per-tool invocation counter (KUTIP SAMPAH 2026-08-05).

Append-only JSONL ledger. No secrets. Fail-soft: never blocks tools.
Path: $GEOX_TOOL_METRICS_PATH or /var/lib/geox/metrics/tool_invocations.jsonl

Tuas 2 (2026-09-19): this organ-local ledger is mirrored, additively, into the
shared federation telemetry (/root/AAA/lib/invocation_log.py ->
/var/lib/arifos/metrics/tool_invocations.jsonl) so the federation aggregator
can see GEOX without reading GEOX's private path. The organ-local line below is
authoritative and its format is unchanged. The mirror is fail-soft: if the
shared contract is absent or unwritable, the local line still lands and the
tool call is unaffected.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

_LOCK = threading.Lock()
_DEFAULT = Path("/var/lib/geox/metrics/tool_invocations.jsonl")

# Tuas 2 federation mirror — additive. Override path for tests only.
_FED_LIB = "/root/AAA/lib"
_FED_ENV = "GEOX_FEDERATION_METRICS_PATH"


def _path() -> Path:
    raw = os.environ.get("GEOX_TOOL_METRICS_PATH", "").strip()
    return Path(raw) if raw else _DEFAULT


def _mirror_to_federation(
    tool: str,
    *,
    session_id: str | None,
    actor_id: str | None,
    ok: bool,
    duration_ms: float | None,
) -> None:
    """Append the SAME invocation to the shared federation telemetry (Tuas 2).

    Identity only: tool name + actor id. Never arguments, payloads or content.
    Never raises into the caller — a telemetry failure must not break the tool.
    """
    try:
        if _FED_LIB not in sys.path:
            sys.path.insert(0, _FED_LIB)
        from invocation_log import log_invocation

        sink = os.environ.get(_FED_ENV, "").strip() or None
        log_invocation(
            "GEOX",
            tool,
            actor_id=actor_id,
            ok=ok,
            duration_ms=duration_ms,
            session_id=session_id,
            path=sink,
        )
    except Exception:
        pass  # never block the tool path; local ledger already written


def record_invocation(
    tool: str,
    *,
    session_id: str | None = None,
    actor_id: str | None = None,
    ok: bool = True,
    duration_ms: float | None = None,
) -> None:
    """Append one invocation row. Fail-soft."""
    try:
        path = _path()
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": datetime.now(UTC).isoformat(),
            "organ": "GEOX",
            "tool": tool,
            "session_id": session_id or None,
            "actor_id": actor_id or None,
            "ok": bool(ok),
            "duration_ms": round(duration_ms, 3) if duration_ms is not None else None,
            "epoch": time.time(),
        }
        line = json.dumps(row, separators=(",", ":"), default=str) + "\n"
        with _LOCK:
            with path.open("a", encoding="utf-8") as f:
                f.write(line)
        # Tuas 2: mirror the same invocation to the federation ledger.
        # Runs AFTER the local line is durable, so the organ-local ledger wins
        # any conflict. Fail-soft inside; never blocks the tool path.
        _mirror_to_federation(
            tool,
            session_id=session_id or None,
            actor_id=actor_id or None,
            ok=ok,
            duration_ms=duration_ms,
        )
    except Exception:
        pass  # never block tool path
