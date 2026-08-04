"""M6 utilization — per-tool invocation counter (KUTIP SAMPAH 2026-08-05).

Append-only JSONL ledger. No secrets. Fail-soft: never blocks tools.
Path: $GEOX_TOOL_METRICS_PATH or /var/lib/geox/metrics/tool_invocations.jsonl
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

_LOCK = threading.Lock()
_DEFAULT = Path("/var/lib/geox/metrics/tool_invocations.jsonl")


def _path() -> Path:
    raw = os.environ.get("GEOX_TOOL_METRICS_PATH", "").strip()
    return Path(raw) if raw else _DEFAULT


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
    except Exception:
        pass  # never block tool path
