"""
result_truth — shared truth helpers for GEOX tool results (F2).

Fixes inverted isError contracts where empty error="" or key presence alone
marked success as failure.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from typing import Any


def truthy_error(err: Any) -> bool:
    """True only when error payload carries real failure content."""
    if err is None or err is False:
        return False
    if isinstance(err, str):
        return bool(err.strip())
    if isinstance(err, (list, dict)):
        return len(err) > 0
    return True


def result_is_error(result: dict[str, Any] | None) -> bool:
    """Canonical error detection for GEOX dict tool results.

    Never treat bare ``"error" in result`` or ``error: ""`` as failure.
    Aligns isError with ``ok`` when present:
      - ok: False -> isError: True
      - ok: True -> isError: False (unless truthy error present)
    """
    if not isinstance(result, dict):
        return False
    if result.get("ok") is False:
        return True
    if result.get("ok") is True and not truthy_error(result.get("error")):
        return False
    if result.get("isError") is True:
        return True
    if result.get("status") in ("INVALID", "ERROR", "FAILED", "NOT_FOUND"):
        return True
    if result.get("execution_status") in ("ERROR", "FAILED", "REJECTED"):
        return True
    if truthy_error(result.get("error")):
        return True
    if truthy_error(result.get("message")) and result.get("ok") is False:
        return True
    return False


def normalize_result_truth(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize a tool result dict to satisfy strict contract:
    1. ok: False -> isError: True
    2. ok: True -> isError: False
    3. Exactly one confidence field per payload [0.0, 1.0]
    4. mode is never 'unknown'
    """
    if not isinstance(result, dict):
        return result

    # Invariant 1 & 2: ok and isError alignment
    is_err = result_is_error(result)
    if is_err:
        result["isError"] = True
        result["ok"] = False
    else:
        result["isError"] = False
        result["ok"] = True
        if not truthy_error(result.get("error")):
            result.pop("error", None)

    # Invariant 3: Exactly one confidence field per payload [0.0, 1.0]
    raw_conf = None
    for k in ("confidence", "payload_confidence", "claimed_confidence", "epistemic_confidence"):
        if k in result and result[k] is not None:
            if raw_conf is None:
                raw_conf = result[k]
            result.pop(k, None)

    if raw_conf is not None:
        try:
            val = float(raw_conf)
            result["confidence"] = max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            result["confidence"] = 0.50

    # Invariant 4: mode is strictly in ("production", "simulation", "observed") and never "unknown"
    VALID_MODES = {"production", "simulation", "observed"}
    mode = result.get("mode")
    if not mode or mode == "unknown" or mode not in VALID_MODES:
        if result.get("isError"):
            result["mode"] = "simulation"
        else:
            result["mode"] = "production"

    return result
