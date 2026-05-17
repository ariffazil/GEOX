"""Governed artifact path and file validation for GEOX renderers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ArtifactValidationError(ValueError):
    """Raised when an artifact path or generated file is invalid."""


@dataclass
class ArtifactValidationResult:
    path: str
    status: str
    size_bytes: int
    format: str
    readable: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "size_bytes": self.size_bytes,
            "format": self.format,
            "readable": self.readable,
            "message": self.message,
        }


def allowed_artifact_roots() -> list[Path]:
    raw = os.environ.get(
        "GEOX_ALLOWED_ARTIFACT_DIRS",
        "/data/geox_panels:/tmp/geox_panels:/tmp:/root/geox/data/geox_panels",
    )
    return [Path(item).expanduser().resolve() for item in raw.split(":") if item.strip()]


def validate_output_path(path: str, *, must_have_suffix: str | None = None) -> str:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        raise ArtifactValidationError("output path must be absolute")
    if must_have_suffix and candidate.suffix.lower() != must_have_suffix.lower():
        raise ArtifactValidationError(f"output path must end with {must_have_suffix}")

    resolved_parent = candidate.parent.resolve()
    allowed = allowed_artifact_roots()
    if not any(resolved_parent == root or resolved_parent.is_relative_to(root) for root in allowed):
        roots = ", ".join(str(root) for root in allowed)
        raise ArtifactValidationError(f"output path outside allowed artifact directories: {roots}")
    resolved_parent.mkdir(parents=True, exist_ok=True)
    return str(candidate)


def write_json_audit(path: str, payload: dict[str, Any]) -> str:
    audit_path = validate_output_path(path, must_have_suffix=".json")
    Path(audit_path).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return audit_path


def verify_artifact(path: str, expected_format: str | None = None) -> ArtifactValidationResult:
    p = Path(path)
    fmt = (expected_format or p.suffix.lstrip(".") or "unknown").lower()
    if not p.exists():
        return ArtifactValidationResult(str(p), "INVALID", 0, fmt, False, "file does not exist")
    size = p.stat().st_size
    if size <= 0:
        return ArtifactValidationResult(str(p), "INVALID", size, fmt, False, "file is empty")

    if fmt in {"png", "jpg", "jpeg", "webp"}:
        try:
            from PIL import Image

            with Image.open(p) as image:
                image.verify()
        except Exception as exc:
            return ArtifactValidationResult(
                str(p),
                "INVALID",
                size,
                fmt,
                False,
                f"image unreadable: {exc}",
            )

    return ArtifactValidationResult(str(p), "VALID", size, fmt, True)


def verify_artifact_pack(artifacts: dict[str, str | None]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name, path in artifacts.items():
        if not path:
            continue
        expected = "csv" if name.endswith("csv_summary_path") else Path(path).suffix.lstrip(".")
        results[name] = verify_artifact(path, expected).to_dict()
    return results
