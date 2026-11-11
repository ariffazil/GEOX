"""GEOX source drift: this repo's HEAD against its own origin/main.

This is not an arifOS certificate. A live ls-remote is preferred so a
stale remote-tracking ref cannot stand in for the public branch. The
result is cached so /health does not call the network on every probe.
"""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from typing import Any

_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_TTL_S = 60.0


def _git(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=2.0)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return proc.returncode, (proc.stdout or "").strip()


def probe_geox_source_drift(
    repo: str = "/opt/geox",
    runner: Callable[[list[str]], tuple[int, str]] | None = None,
    now: float | None = None,
    ttl_s: float = _TTL_S,
) -> dict[str, Any]:
    """Compare local HEAD with origin/main.

    runner is a test seam. The default runner is git, with a 2s timeout.
    A successful live read is cached for ttl_s. A fallback to the
    remote-tracking ref is labelled and is not cached as a live read.
    """
    clock = time.time() if now is None else now
    if runner is None and ttl_s > 0:
        cached = _CACHE.get("value")
        if isinstance(cached, dict) and clock - float(_CACHE.get("at") or 0) < ttl_s:
            return dict(cached)

    run = runner or _git
    rc, local = run(["git", "-C", repo, "rev-parse", "HEAD"])
    local_head = local if rc == 0 and local else "unknown"
    origin_main = "unknown"
    compared_via = "git ls-remote"
    rc_url, origin_url = run(["git", "-C", repo, "remote", "get-url", "origin"])
    if rc_url == 0 and origin_url and "://" in origin_url:
        rc_remote, remote = run(["git", "ls-remote", origin_url, "refs/heads/main"])
        if rc_remote == 0 and remote:
            origin_main = remote.split()[0]
    if origin_main == "unknown":
        compared_via = "origin/main tracking ref"
        rc_tracked, tracked = run(["git", "-C", repo, "rev-parse", "origin/main"])
        if rc_tracked == 0 and tracked:
            origin_main = tracked
    if local_head != "unknown" and origin_main != "unknown":
        drift: bool | None = local_head != origin_main
        status = "drift" if drift else "aligned"
    else:
        drift = None
        status = "unknown"
    value = {
        "local_head": local_head,
        "origin_main": origin_main,
        "drift": drift,
        "status": status,
        "compared_via": compared_via,
        "repo": repo,
        "rule": "local HEAD == origin/main. This field certifies GEOX only.",
    }
    if runner is None and compared_via == "git ls-remote" and origin_main != "unknown":
        _CACHE["at"] = clock
        _CACHE["value"] = dict(value)
    return value
