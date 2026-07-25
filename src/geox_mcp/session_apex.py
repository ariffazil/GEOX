"""
session_apex — Read-only echo of kernel apex_scalars onto GEOX receipts.

GEOX never mints constitutional G. When interpret / seal-grade receipts
need apex context, attach an echo of arifOS /health apex_scalars with:

  g_authority: arifos.health | unmeasured
  g_canonical_source: arif_think.mode=apex

NOMINAL / stub vitals are rejected (same rule as GEOX /health).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger("geox_mcp.session_apex")

_APEX_KEYS: tuple[str, ...] = ("G", "C_dark", "W3", "h", "QDF")
_REJECT_STATUS: frozenset[str] = frozenset({"", "NOMINAL", "DEFAULT", "STUB"})

# Tiny process cache — health is operator-scale, not per-sample geology.
_CACHE: dict[str, Any] = {"ts": 0.0, "apex": None}
_CACHE_TTL_S = float(os.environ.get("GEOX_APEX_CACHE_TTL_S", "15"))


def _unmeasured_block() -> dict[str, dict[str, Any]]:
    return {
        k: {
            "value": None,
            "status": "UNMEASURED",
            "source": "geox.session_apex",
            "g_canonical_source": "arif_think.mode=apex",
        }
        for k in _APEX_KEYS
    }


def _sanitize_kernel_apex(raw: Any) -> dict[str, dict[str, Any]]:
    """Accept MEASURED/UNMEASURED only; drop NOMINAL fabrications."""
    out = _unmeasured_block()
    if not isinstance(raw, dict):
        return out
    for k in _APEX_KEYS:
        v = raw.get(k)
        if not isinstance(v, dict) or "value" not in v:
            continue
        st = str(v.get("status") or "").upper()
        if st in _REJECT_STATUS:
            continue
        out[k] = {
            "value": v.get("value"),
            "status": st or "MEASURED",
            "source": v.get("source") or "arifos.health",
            "g_canonical_source": "arif_think.mode=apex",
        }
    return out


def fetch_kernel_apex_scalars(*, timeout_s: float = 1.5, use_cache: bool = True) -> dict[str, dict[str, Any]]:
    """Probe arifOS /health for apex_scalars. Fail soft → UNMEASURED."""
    now = time.monotonic()
    if use_cache and _CACHE["apex"] is not None and (now - float(_CACHE["ts"])) < _CACHE_TTL_S:
        return dict(_CACHE["apex"])  # type: ignore[arg-type]

    base = (
        os.environ.get("ARIFOS_HEALTH_URL")
        or os.environ.get("ARIFOS_URL")
        or "http://127.0.0.1:8088"
    ).rstrip("/")
    if base.endswith("/health"):
        url = base
    else:
        url = f"{base}/health"

    apex = _unmeasured_block()
    try:
        import urllib.request

        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — localhost/kernel
            import json

            body = json.loads(resp.read().decode("utf-8", errors="replace"))
        if isinstance(body, dict):
            apex = _sanitize_kernel_apex(body.get("apex_scalars"))
    except Exception as exc:  # noqa: BLE001 — fail soft is the product
        logger.debug("session_apex: kernel health probe failed: %s", exc)
        for k in apex:
            apex[k]["source"] = "geox.session_apex.unmeasured"
            apex[k]["probe_error"] = type(exc).__name__

    _CACHE["ts"] = now
    _CACHE["apex"] = apex
    return dict(apex)


def attach_session_apex(
    result: Any,
    *,
    force: bool = False,
    timeout_s: float = 1.5,
) -> Any:
    """Attach session apex_scalars + g_authority onto a dict receipt.

    Skips if already present (unless force=True). Non-dict → pass through.
    """
    if not isinstance(result, dict):
        return result
    if not force and isinstance(result.get("apex_scalars"), dict) and result.get("g_authority"):
        return result

    out = dict(result)
    apex = fetch_kernel_apex_scalars(timeout_s=timeout_s)
    out["apex_scalars"] = apex

    g_block = apex.get("G") or {}
    g_status = str(g_block.get("status") or "UNMEASURED").upper()
    if g_status == "MEASURED" and g_block.get("value") is not None:
        out["g_authority"] = "arifos.health"
    else:
        out["g_authority"] = "unmeasured"

    out.setdefault(
        "g_note",
        "Constitutional G is minted only via arif_think(mode=apex); GEOX echoes only.",
    )
    # Strip fabricated constitutional G if a tool body left a NOMINAL 0.5
    if out.get("G") == 0.5:
        out.pop("G", None)
    if "genius" in out and isinstance(out["genius"], (int, float)) and float(out["genius"]) == 0.5:
        out["genius_note"] = "local domain score — not constitutional G"
    return out
