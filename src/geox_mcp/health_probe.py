"""Single health probe for GEOX — the one function both /health and geox_surface_status read.

FORGED 2026-10-28 (S1) because two surfaces of one organ disagreed: /health said
`degraded` (with the false reason `kernel_not_SEAL`) while `geox_surface_status`
returned the hardcoded literal `"healthy"`.

DESIGN LAWS (each one exists because the previous code broke it):
  1. No field may compare a constant to itself.  `registry_state` is derived from a live
     provider enumeration, never from `len(CANONICAL_PUBLIC_TOOLS) == len(CANONICAL_PUBLIC_TOOLS)`.
  2. Exceptions fail CLOSED.  An unreachable dependency is `unreachable`, never `healthy`,
     and never silently dropped from `reasons`.
  3. The top-level status word is DERIVED (`status_source` says so).  It may be `healthy`
     only when every named field is green.
  4. A dependency's verdict is passed upward WITH its real reason (floors, not a summary word).
  5. Duplicates are named, not absorbed.  A count that is a set difference can never detect
     a duplicate, so `registry_counts` carries `entries`, `unique` and `duplicates`.

Authority: 555_COMPUTE_ONLY. This function reports; it never fixes, judges or seals.
"""

from __future__ import annotations

import asyncio
import datetime as _dt
from collections import Counter
from typing import Any

import httpx

from geox_mcp.registry import CANONICAL_PUBLIC_TOOLS

ARIFOS_HEALTH_URL = "http://127.0.0.1:8088/health"


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _reason(field: str, value: Any, severity: str, explanation: str) -> dict[str, Any]:
    return {"field": field, "value": value, "severity": severity, "explanation": explanation}


async def _probe_registry(mcp_server: Any) -> dict[str, Any]:
    """Enumerate the live registry and derive registry_state. Never tautological."""
    if mcp_server is None:
        return {
            "registry_state": "UNKNOWN",
            "registry_source": "no mcp server handle",
            "registry_counts": None,
            "reasons": [
                _reason("registry_state", "UNKNOWN", "warning", "registry probe had no server handle; cannot witness the surface")
            ],
        }
    try:
        fn = getattr(mcp_server, "list_tools", None)
        if not callable(fn):
            raise AttributeError("mcp server exposes no list_tools()")
        res = fn()
        if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
            res = await res
        names = [getattr(t, "name", str(t)) for t in (res or [])]
    except Exception as exc:  # fail closed — never green on a broken probe
        return {
            "registry_state": "UNKNOWN",
            "registry_source": f"enumeration failed: {type(exc).__name__}: {exc}",
            "registry_counts": None,
            "reasons": [
                _reason(
                    "registry_state",
                    "UNKNOWN",
                    "warning",
                    f"live registry enumeration failed ({type(exc).__name__}); surface parity is unwitnessed, not passing",
                )
            ],
        }

    counts = Counter(names)
    duplicates = sorted(n for n, c in counts.items() if c > 1)
    missing = sorted(set(CANONICAL_PUBLIC_TOOLS) - set(counts))
    reasons: list[dict[str, Any]] = []
    if duplicates:
        reasons.append(
            _reason(
                "registry.duplicates",
                duplicates,
                "error",
                "the same tool name is registered by more than one provider; clients "
                "receive one copy by name and the others are unreachable",
            )
        )
    if missing:
        reasons.append(_reason("registry.missing", missing, "error", "canonical tools are not present in the live registry"))
    return {
        "registry_state": "PASS" if not duplicates and not missing else "FAIL",
        "registry_source": "mcp.list_tools() live enumeration",
        "registry_counts": {
            "entries": len(names),
            "unique": len(counts),
            "canonical_declared": len(CANONICAL_PUBLIC_TOOLS),
            "duplicates": duplicates,
            "missing": missing,
        },
        "reasons": reasons,
    }


async def _probe_kernel(url: str, timeout: float) -> dict[str, Any]:
    """Read arifOS /health and pass its verdict up WITH the floors that produced it."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            data = resp.json()
    except Exception as exc:
        return {
            "kernel_state": "unreachable",
            "kernel_verdict": "UNKNOWN",
            "kernel_status": None,
            "kernel_floors_failing": [],
            "kernel_floors_unmeasured": [],
            "reasons": [
                _reason(
                    "dependency.arifos",
                    "unreachable",
                    "warning",
                    f"kernel health probe failed ({type(exc).__name__}); verdict unknown, not healthy",
                )
            ],
        }

    thermo = data.get("thermodynamic") if isinstance(data.get("thermodynamic"), dict) else {}
    verdict = thermo.get("verdict") or "UNKNOWN"
    status = data.get("status")
    con = (data.get("layer_health") or {}).get("constitutional") or {}
    failing = list(con.get("floors_failing") or [])
    unmeasured = list(con.get("floors_unmeasured") or [])

    if status is None:
        state = "unknown"
    elif status == "healthy" and verdict not in ("HOLD", "VOID"):
        state = "healthy"
    else:
        state = "degraded"

    reasons: list[dict[str, Any]] = []
    if state != "healthy":
        parts = []
        if failing:
            parts.append(f"floors_failing={','.join(failing)}")
        if unmeasured:
            parts.append(f"floors_unmeasured={','.join(unmeasured)}")
        if status is None:
            parts.append("kernel status field absent")
        detail = "; ".join(parts) or "no floor detail published"
        reasons.append(
            _reason(
                "dependency.arifos",
                f"status={status}, verdict={verdict}",
                "error",
                f"kernel_degraded (from arifOS, quoted not summarised): {detail}",
            )
        )
    return {
        "kernel_state": state,
        "kernel_verdict": verdict,
        "kernel_status": status,
        "kernel_floors_failing": failing,
        "kernel_floors_unmeasured": unmeasured,
        "reasons": reasons,
    }


async def probe_health_fields(
    mcp_server: Any = None,
    *,
    arifos_url: str = ARIFOS_HEALTH_URL,
    timeout: float = 2.0,
) -> dict[str, Any]:
    """Return the organ's health as named, independently falsifiable fields."""
    registry, kernel = await asyncio.gather(
        _probe_registry(mcp_server),
        _probe_kernel(arifos_url, timeout),
    )

    reasons = list(registry.pop("reasons")) + list(kernel.pop("reasons"))
    registry_state = registry["registry_state"]
    kernel_state = kernel["kernel_state"]

    if registry_state == "PASS" and kernel_state == "healthy":
        status, cause = "healthy", "NONE"
    elif registry_state == "FAIL":
        status, cause = "degraded", "REGISTRY"
    elif registry_state == "UNKNOWN":
        status, cause = "degraded", "UNWITNESSED"
    else:
        status, cause = "degraded", "DEPENDENCY"

    reason_strings = [f"{r['field']}: {r['value']} — {r['explanation']}" for r in reasons] or ["all named fields green"]

    return {
        "status": status,
        "cause": cause,
        "status_source": "derived: registry_state + kernel_state (+ dependency_state)",
        "measured_at_utc": _now(),
        "registry_state": registry_state,
        "registry_source": registry["registry_source"],
        "registry_counts": registry["registry_counts"],
        "kernel_state": kernel_state,
        "kernel_verdict": kernel["kernel_verdict"],
        "kernel_status": kernel["kernel_status"],
        "kernel_floors_failing": kernel["kernel_floors_failing"],
        "kernel_floors_unmeasured": kernel["kernel_floors_unmeasured"],
        "dependency_state": {
            "arifos": {
                "state": kernel_state,
                "status": kernel["kernel_status"],
                "verdict": kernel["kernel_verdict"],
                "floors_failing": kernel["kernel_floors_failing"],
                "floors_unmeasured": kernel["kernel_floors_unmeasured"],
                "source": arifos_url,
            }
        },
        "reasons": reasons,
        "reason_strings": reason_strings,
    }
