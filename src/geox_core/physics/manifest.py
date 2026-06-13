"""
GEOX Physics Manifest — Identity anchor for natural-law Earth intelligence.

Computes physics_manifest_hash from the canonical PHYSICS_MANIFEST.md file.
This is GEOX's domain identity anchor — the equivalent of arifOS's constitution_hash
but for natural law (kuasa alam) rather than constitutional law.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger("geox.physics_manifest")

# Canonical paths to the physics manifest
_MANIFEST_PATHS = [
    Path("/root/geox/GENESIS/004_PHYSICS_MANIFEST.md"),
    Path("/opt/geox/app/GENESIS/004_PHYSICS_MANIFEST.md"),
    Path(__file__).parent.parent.parent.parent / "GENESIS" / "004_PHYSICS_MANIFEST.md",
]

# Fallback in case file is missing
_FALLBACK_HASH = "sha256:missing"
_DOMAIN_LAW = "NATURAL_LAW"


def _sha256_of_file(path: Path) -> str:
    """Compute sha256: hex digest of a file's contents."""
    try:
        with open(path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        return f"sha256:{digest}"
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.warning(f"Cannot read physics manifest at {path}: {e}")
        return _FALLBACK_HASH


def compute_physics_manifest_hash() -> str:
    """Compute the physics manifest hash from the canonical manifest file.

    Returns:
        str: "sha256:<64-char-hex>" or "sha256:missing" if no manifest file found.
    """
    for path in _MANIFEST_PATHS:
        if path.exists():
            h = _sha256_of_file(path)
            if h != _FALLBACK_HASH:
                return h
    logger.warning(
        "Physics manifest not found at any canonical path. "
        "GEOX identity anchor will be 'sha256:missing'. "
        "Run GEOX with GENESIS/004_PHYSICS_MANIFEST.md present."
    )
    return _FALLBACK_HASH


def get_physics_manifest_hash() -> str:
    """Return cached physics manifest hash, computing it on first call."""
    return compute_physics_manifest_hash()


def get_domain_law() -> str:
    """Return GEOX's domain law type."""
    return _DOMAIN_LAW


def _compute_physics_guard_version() -> str:
    """Compute physics guard version from git SHA, falling back to shipped constant."""
    try:
        import subprocess as _sp

        _sha = (
            _sp.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(Path(__file__).parent.parent.parent.parent),
                timeout=5,
            )
            .decode()
            .strip()
        )
        return f"geox-{_sha}"
    except Exception:
        return "geox-014d3e33"  # shipped fallback


_PHYSICS_GUARD_VERSION = _compute_physics_guard_version()


def get_geo_identity() -> dict:
    """Return GEOX identity anchor block for use in health, registry, and envelopes.

    Returns a dict suitable for merging into health responses, registry status,
    and output provenance — replacing the old constitution_hash pattern.
    """
    return {
        "domain_law": _DOMAIN_LAW,
        "physics_manifest_hash": get_physics_manifest_hash(),
        "physics_guard_version": _PHYSICS_GUARD_VERSION,
    }
