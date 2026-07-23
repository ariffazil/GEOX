"""
🌊 GEOX Artifact Ingest (PR-A1)

Artifact-first ingestion. Caller passes `artifact_ref` (path or url);
GEOX hashes the bytes, captures provenance, applies calibration
metadata, and never embeds large base64 blobs in MCP requests.

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


ArtifactType = Literal[
    "section_image",
    "segy_2d",
    "segy_3d",
    "interpreted_section",
    "framework_json",
]


@dataclass
class IngestedArtifact:
    artifact_ref: str
    artifact_type: ArtifactType
    sha256: str
    size_bytes: int
    ingested_at_iso: str
    artifact_hash_chain: str = ""  # sha256 over the canonical metadata
    calibration_sha: str = ""     # sha256 of the calibration blob (if any)
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: str, *, chunk_bytes: int = 1 << 20) -> str:
    """Stream-hash a file. Returns 'sha256:<hex>'."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_bytes), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def ingest_artifact(
    artifact_ref: str,
    *,
    artifact_type: ArtifactType = "section_image",
    calibration: dict[str, Any] | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Ingest an artifact from a local path.

    Returns:
        IngestedArtifact dict with sha256 + provenance.
    """
    if not artifact_ref:
        raise ValueError("artifact_ref required")

    if not os.path.exists(artifact_ref):
        # Allow remote URI / opaque ref without local hash; mark note
        size_bytes = 0
        sha = "sha256:unresolved"
    else:
        size_bytes = os.path.getsize(artifact_ref)
        sha = sha256_file(artifact_ref)

    cal_sha = ""
    if calibration:
        cal_bytes = repr(sorted(calibration.items())).encode("utf-8")
        cal_sha = sha256_bytes(cal_bytes)

    art = IngestedArtifact(
        artifact_ref=artifact_ref,
        artifact_type=artifact_type,
        sha256=sha,
        size_bytes=size_bytes,
        ingested_at_iso=datetime.now(timezone.utc).isoformat(),
        calibration_sha=cal_sha,
        note=note,
    )

    # Hash-chain over the canonical metadata
    canon = repr(sorted(art.to_dict().items())).encode("utf-8")
    art_hash = hashlib.sha256(canon).hexdigest()
    art.artifact_hash_chain = "sha256:" + art_hash

    return art.to_dict()


def validate_calibration_state(calibration: dict[str, Any] | None) -> dict[str, Any]:
    """Return a state map of which calibration fields are present.

    Used by gates to decide UNMEASURED vs WARN vs PASS.
    """
    if not calibration:
        return {"calibrated": False, "missing": ["all"]}
    required = [
        "x_axis",
        "vertical_axis",
        "vertical_exaggeration",
        "polarity",
        "phase_degrees",
    ]
    present = [k for k in required if calibration.get(k) is not None]
    missing = [k for k in required if calibration.get(k) is None]
    return {
        "calibrated": (len(missing) == 0),
        "present": present,
        "missing": missing,
        "sha256": sha256_bytes(repr(sorted(calibration.items())).encode("utf-8")),
    }


__all__ = [
    "ArtifactType",
    "IngestedArtifact",
    "ingest_artifact",
    "sha256_bytes",
    "sha256_file",
    "validate_calibration_state",
]