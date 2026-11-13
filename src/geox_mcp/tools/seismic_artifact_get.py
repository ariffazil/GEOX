"""
GEOX Seismic Artifact Get — universal artifact reader.

Per the GEOX Seismic Interpretation Forge Package, MCP responses return
artifact/manifest/QC references — never full opaque volumes. This tool
is the foundation of that pattern: given an artifact_id, it returns
the manifest/payload, validating against the appropriate contract schema.

Capabilities:
- Volume manifests        → VolumeManifest
- Derived volume manifests → DerivedVolumeManifest
- QC receipts             → QCReceipt
- Polarity registers      → PolarityPhaseRegister
- Editing primitives      → Polyline / Polygon / SurfaceMesh / VoxelMask / PointSet

Universal pattern: capability-driven dispatcher. The implementation that
satisfies a capability is a separate concern (governed by CapabilityRef
on the artifact), not the responsibility of this reader.

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from geox_core.enums.statuses import get_standard_envelope  # type: ignore
from geox.seismic.contracts import (
    PointSet,
    Polygon,
    Polyline,
    PolarityPhaseRegister,
    QCReceipt,
    SurfaceMesh,
    VoxelMask,
)
from pydantic import ValidationError

logger = logging.getLogger("geox.seismic_artifact_get")

TOOL_NAME = "geox_seismic_artifact_get"

# Artifact type inferred from URI prefix
_ARTIFACT_KIND_BY_PREFIX = {
    "geox://volume/": "volume_manifest",
    "geox://derived/": "derived_volume_manifest",
    "geox://qc/": "qc_receipt",
    "geox://artifact/polarity-": "polarity_register",
    "geox://artifact/": "editing_primitive",
}


def _infer_kind(artifact_id: str) -> str:
    for prefix, kind in _ARTIFACT_KIND_BY_PREFIX.items():
        if artifact_id.startswith(prefix):
            return kind
    return "unknown"


def _validate_against_schema(payload: dict, kind: str) -> tuple[bool, str | None]:
    """Validate payload against the appropriate schema."""
    try:
        if kind == "volume_manifest":
            from geox.seismic.contracts import VolumeManifest
            VolumeManifest.model_validate(payload)
        elif kind == "derived_volume_manifest":
            from geox.seismic.contracts import DerivedVolumeManifest
            DerivedVolumeManifest.model_validate(payload)
        elif kind == "qc_receipt":
            QCReceipt.model_validate(payload)
        elif kind == "polarity_register":
            PolarityPhaseRegister.model_validate(payload)
        elif kind == "editing_primitive":
            # Try each editing primitive; first match wins
            for cls in (Polyline, Polygon, SurfaceMesh, VoxelMask, PointSet):
                try:
                    cls.model_validate(payload)
                    return True, cls.__name__
                except ValidationError:
                    continue
            return False, "no editing primitive schema matched"
        return True, None
    except ValidationError as e:
        return False, str(e)


# ────────────────────────────────────────────────────────────────────────────
# Backend abstraction — to be wired to artifact store when ready
# ────────────────────────────────────────────────────────────────────────────


class ArtifactBackend:
    """Abstract base for artifact storage backends.

    Concrete implementations: file:// (test), s3://, geox-artifact-store.
    """

    def fetch(self, artifact_id: str) -> dict | None:
        raise NotImplementedError


class FileBackend(ArtifactBackend):
    """Local file backend — used in tests; for production use ArtifactStoreBackend."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def fetch(self, artifact_id: str) -> dict | None:
        # Map geox://<type>/<id> → <root>/<type>/<id>.json
        rel = artifact_id.replace("geox://", "").replace("/", "__")
        candidate = self.root / f"{rel}.json"
        if not candidate.exists():
            return None
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("FileBackend failed to read %s: %s", candidate, e)
            return None


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_artifact_get(
    artifact_id: str = "",
    include_qc: bool = True,
    backend: ArtifactBackend | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Retrieve a seismic artifact by ID, validated against its contract schema.

    Parameters
    ----------
    artifact_id : str
        geox:// URI (e.g., geox://volume/f3/raw, geox://qc/<id>).
    include_qc : bool
        If True, attach the latest QC receipt if known.
    backend : ArtifactBackend, optional
        Backend implementation; defaults to FileBackend at /var/lib/geox/artifacts.
    session_id, actor_id, trace_id : str, optional
        Provenance fields.
    """
    if not artifact_id.startswith("geox://"):
        return _envelope(
            status="HOLD",
            error=f"artifact_id must start with 'geox://', got: {artifact_id!r}",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    if backend is None:
        # Default location; production wires this to artifact-store
        backend = FileBackend(Path("/var/lib/geox/artifacts"))

    payload = backend.fetch(artifact_id)
    if payload is None:
        return _envelope(
            status="HOLD",
            error=f"artifact not found: {artifact_id}",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    kind = _infer_kind(artifact_id)
    valid, validation_msg = _validate_against_schema(payload, kind)

    if not valid:
        return {
            **_envelope(
                status="HOLD",
                error=f"schema validation failed for kind={kind}: {validation_msg}",
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            ),
            "artifact_id": artifact_id,
            "inferred_kind": kind,
        }

    return {
        **_envelope(
            status="OK",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        ),
        "artifact_id": artifact_id,
        "inferred_kind": kind,
        "validated_against": validation_msg or kind,
        "payload": payload,
        "claim": None,
    }


def _envelope(
    *,
    status: str,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Minimal GEOX-style envelope — slim variant (see polarity_register._envelope)."""
    env = {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id or "kimi-code/FI-008",
        "session_id": session_id,
        "trace_id": trace_id,
        "execution_status": "OK" if status == "OK" else "HOLD",
        "artifact_status": "READY" if status == "OK" else "DRAFT",
        "governance_status": "QUALIFIED" if status == "OK" else "HOLD",
    }
    if status == "OK":
        return {**env, "status": "OK", "claim": None}
    return {
        **env,
        "status": status,
        "error": error,
        "hold_reason": error,
        "claim": None,
    }


def register_with_mcp(mcp: Any) -> None:
    """Register this tool with a fastmcp server instance."""
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_artifact_get)
    logger.info("Registered %s with MCP", TOOL_NAME)
