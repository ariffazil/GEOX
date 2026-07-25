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
    Aligns isError with ``ok`` when present.
    """
    if not isinstance(result, dict):
        return False
    if result.get("ok") is False:
        return True
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
