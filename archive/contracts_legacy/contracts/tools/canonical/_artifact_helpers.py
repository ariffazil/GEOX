import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# ARTIFACT REGISTRY (IN-MEMORY)
# ═══════════════════════════════════════════════════════════════════════════════

_artifact_registry: Dict[str, Dict[str, Any]] = {}
_well_curves_registry: Dict[str, Dict[str, Any]] = {}
_artifact_store: Dict[str, Dict[str, Any]] = {}

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB limit for base64 uploads


def _artifact_exists(artifact_id: str) -> bool:
    """Check if an artifact exists in the in-memory registry."""
    return artifact_id in _artifact_registry


def _register_artifact(artifact_id: str, **kwargs) -> str:
    """Register an artifact in the in-memory store."""
    _artifact_registry[artifact_id] = kwargs
    _artifact_store[artifact_id] = kwargs # Keep a copy for direct access if needed
    return artifact_id


def _get_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an artifact from the in-memory store."""
    return _artifact_store.get(artifact_id)


def _record_latest_qc(artifact_id: str, qc_result: Dict[str, Any]):
    """Record the latest QC result for an artifact."""
    if artifact_id in _artifact_registry:
        _artifact_registry[artifact_id]["latest_qc"] = qc_result
        _artifact_store[artifact_id]["latest_qc"] = qc_result


def _reset_registry():
    """Clear the in-memory artifact registry between tests."""
    _artifact_registry.clear()
    _well_curves_registry.clear()
    _artifact_store.clear()


def _safe_upload_path(filename: str, target_dir: str = "/data/geox_las") -> Path:
    """Safely construct a file path within target_dir.

    Raises ValueError if filename attempts path traversal.
    """
    if ".." in filename or os.path.isabs(filename):
        raise ValueError("Filename contains path traversal characters or is absolute.")
    
    # Ensure target_dir exists and is absolute
    base_dir = Path(target_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    final_path = base_dir / filename
    return final_path


def _decode_upload_content(content_base64: str) -> bytes:
    """Decode base64 content and enforce size limits."""
    try:
        payload = base64.b64decode(content_base64)
    except Exception as exc:
        raise ValueError(f"Invalid base64 content: {exc}") from exc

    if len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError(f"decoded upload payload exceeds {MAX_UPLOAD_BYTES} byte limit")
    return payload
