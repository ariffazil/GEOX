# ─── kernel/_validation.py ─── shared input validation helpers ───────────────
# Extracted to centralize length/size limits across the 16 canonical tools.
# No FastMCP imports. Pure business logic.

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

# Conservative caps. Bigger values should be batched, not single-shot.
MAX_STRING_LEN: int = 8 * 1024  # 8 KiB
MAX_LIST_LEN: int = 1_000  # batch_mode: 1000 artifacts
MAX_PATH_LEN: int = 4 * 1024  # 4 KiB filesystem path
MAX_ARTIFACT_REFS: int = 256  # synthetic tool fan-in


def validate_string_field(name: str, value: Any, max_len: int = MAX_STRING_LEN) -> str:
    """Validate a required string field.

    Raises:
        TypeError: If value is not a str.
        ValueError: If value is empty or exceeds max_len.
    """
    if not isinstance(value, str):
        raise TypeError(f"{name!r} must be a string, got {type(value).__name__}")
    if not value:
        raise ValueError(f"{name!r} must not be empty")
    if len(value) > max_len:
        raise ValueError(f"{name!r} length {len(value)} exceeds limit {max_len}")
    return value


def validate_optional_string(name: str, value: Any, max_len: int = MAX_STRING_LEN) -> str | None:
    """Validate an optional string field. None passes through."""
    if value is None:
        return None
    return validate_string_field(name, value, max_len)


def validate_list_field(name: str, value: Iterable[Any], max_len: int = MAX_LIST_LEN) -> list:
    """Validate a list field. Empty allowed (caller decides)."""
    if value is None:
        return []
    materialized = list(value)
    if len(materialized) > max_len:
        raise ValueError(f"{name!r} length {len(materialized)} exceeds limit {max_len}")
    return materialized


def validate_artifact_refs(refs: Iterable[str], max_len: int = MAX_ARTIFACT_REFS) -> list[str]:
    """Validate a list of artifact_refs."""
    if refs is None:
        return []
    out: list[str] = []
    for i, ref in enumerate(refs):
        if not isinstance(ref, str):
            raise TypeError(f"artifact_refs[{i}] must be a string, got {type(ref).__name__}")
        if not ref or len(ref) > 256:
            raise ValueError(f"artifact_refs[{i}] length {len(ref)} outside (0, 256]")
        out.append(ref)
    if len(out) > max_len:
        raise ValueError(f"artifact_refs count {len(out)} exceeds limit {max_len}")
    return out


def safe_path(target: str, allowed_roots: tuple[str, ...] = ("/data", "/tmp")) -> Path:
    """Resolve a target path and confirm it lives under one of allowed_roots.

    Prevents path traversal. Returns a resolved Path. Raises on violation.
    """
    if not isinstance(target, str) or not target:
        raise ValueError("target path must be a non-empty string")
    if len(target) > MAX_PATH_LEN:
        raise ValueError(f"target path length {len(target)} exceeds limit {MAX_PATH_LEN}")
    resolved = Path(target).expanduser().resolve()
    for root in allowed_roots:
        root_resolved = Path(root).resolve()
        try:
            resolved.relative_to(root_resolved)
            return resolved
        except ValueError:
            continue
    raise ValueError(f"target path {resolved} is not under any allowed root {list(allowed_roots)}")
