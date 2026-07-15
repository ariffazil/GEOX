"""
GEOX Artifact Chain Envelope — Forensic Traceability Contract
=============================================================

Every GEOX tool return MUST carry these fields to be certifiable:

  artifact_id    — unique ID for this output (uuid7 or content-addressed)
  artifact_hash  — SHA-256 of the output content
  source_refs    — list of {layer_id, checksum, source_kind} for every input
  scene_plan_id  — if derived from a map scene, the scene plan ID
  geox_version   — GEOX version that produced this output
  git_commit     — exact git commit of the producing code

This is the "three fields" Arif identified as the certification backbone:
  1. artifact_id + checksum
  2. source_layer_ids + their checksums
  3. geox_version + git_commit

Usage in tools:
    from contracts.artifact_envelope import stamp_envelope

    result = {"status": "OK", "data": ...}
    return stamp_envelope(result, source_refs=[...])

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from typing import Any


def _get_git_commit() -> str:
    """Get current git commit hash (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _get_geox_version() -> str:
    """Get GEOX version from env or git."""
    return os.getenv("GIT_SHA", os.getenv("GEOX_VERSION", "2026.07.02"))


def compute_artifact_hash(content: Any) -> str:
    """Compute SHA-256 of arbitrary content (JSON-serialized)."""
    if isinstance(content, (dict, list)):
        serialized = json.dumps(content, sort_keys=True, default=str).encode()
    elif isinstance(content, str):
        serialized = content.encode()
    elif isinstance(content, bytes):
        serialized = content
    else:
        serialized = str(content).encode()
    return f"sha256:{hashlib.sha256(serialized).hexdigest()}"


def make_source_ref(
    layer_id: str,
    checksum: str = "unavailable",
    source_kind: str = "observed",
    artifact_uri: str | None = None,
) -> dict:
    """Create a source reference entry."""
    ref = {
        "layer_id": layer_id,
        "checksum": checksum,
        "source_kind": source_kind,
    }
    if artifact_uri:
        ref["artifact_uri"] = artifact_uri
    return ref


def stamp_envelope(
    result: dict,
    source_refs: list[dict] | None = None,
    scene_plan_id: str | None = None,
    scene_plan_version: str | None = None,
    tool_name: str | None = None,
    review_mode: str = "draft",
) -> dict:
    """Stamp a GEOX tool result with artifact chain envelope fields.

    Adds forensic traceability to any tool output. The result dict is
    modified in-place and returned.

    Args:
        result: The tool result dict (must have "status" key).
        source_refs: List of source_ref dicts (from make_source_ref).
        scene_plan_id: If derived from a map scene, the scene plan ID.
        scene_plan_version: Version of the scene plan.
        tool_name: Name of the tool that produced this output.
        review_mode: draft | validated | sealed_candidate.

    Returns:
        The result dict with envelope fields added.
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())

    # Compute artifact hash from the result content (before envelope)
    content_for_hash = {k: v for k, v in result.items() if k != "_envelope"}
    artifact_hash = compute_artifact_hash(content_for_hash)

    # Generate artifact ID
    artifact_id = f"geox-art-{uuid.uuid4().hex[:16]}"

    envelope: dict[str, Any] = {
        "artifact_id": artifact_id,
        "artifact_hash": artifact_hash,
        "produced_at": now,
        "geox_version": _get_geox_version(),
        "git_commit": _get_git_commit(),
        "tool_name": tool_name or "unknown",
        "review_mode": review_mode,
    }

    if source_refs:
        envelope["source_refs"] = source_refs
        # Compute a combined source hash for quick integrity checks
        source_str = json.dumps([s.get("checksum", "") for s in source_refs], sort_keys=True)
        envelope["source_hash"] = compute_artifact_hash(source_str)

    if scene_plan_id:
        envelope["scene_plan_id"] = scene_plan_id
        envelope["scene_plan_version"] = scene_plan_version or "unversioned"

    result["_envelope"] = envelope  # type: ignore[assignment]
    return result


def verify_envelope(result: dict) -> dict:
    """Verify an artifact chain envelope's integrity.

    Returns:
        {"valid": bool, "checks": list[str], "errors": list[str]}
    """
    checks = []
    errors = []

    envelope = result.get("_envelope")
    if not envelope:
        return {"valid": False, "checks": [], "errors": ["No _envelope found"]}

    # Check required fields
    required = ["artifact_id", "artifact_hash", "produced_at", "geox_version", "git_commit"]
    for field in required:
        if field in envelope:
            checks.append(f"✅ {field} present")
        else:
            errors.append(f"❌ {field} missing")

    # Verify hash
    content_for_hash = {k: v for k, v in result.items() if k != "_envelope"}
    expected_hash = compute_artifact_hash(content_for_hash)
    if envelope.get("artifact_hash") == expected_hash:
        checks.append("✅ artifact_hash matches content")
    else:
        errors.append(f"❌ artifact_hash mismatch: expected {expected_hash[:32]}...")

    # Verify source refs
    source_refs = envelope.get("source_refs", [])
    if source_refs:
        checks.append(f"✅ {len(source_refs)} source refs recorded")
        for i, ref in enumerate(source_refs):
            if "layer_id" not in ref:
                errors.append(f"❌ source_refs[{i}] missing layer_id")
            if "checksum" not in ref:
                errors.append(f"❌ source_refs[{i}] missing checksum")
    else:
        checks.append("⚠️  no source refs (may be acceptable for top-level tools)")

    return {
        "valid": len(errors) == 0,
        "checks": checks,
        "errors": errors,
    }
