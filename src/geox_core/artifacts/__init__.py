"""Artifact writing and verification helpers for GEOX."""

from .writer import (
    ArtifactValidationError,
    ArtifactValidationResult,
    validate_output_path,
    verify_artifact_pack,
    write_json_audit,
)

__all__ = [
    "ArtifactValidationError",
    "ArtifactValidationResult",
    "validate_output_path",
    "verify_artifact_pack",
    "write_json_audit",
    "validate_artifact",
    "build_artifact_envelope",
]


def validate_artifact(artifact_path, expected_format=None):
    """Stub: validate artifact path and format."""
    if not artifact_path:
        return {"ok": False, "error": "No artifact path provided"}
    return {"ok": True, "path": str(artifact_path), "format": expected_format}


def build_artifact_envelope(artifact_path, claim_state, depth_basis, depth_unit, renderer, plot_spec_digest):
    """Stub: build governed artifact envelope."""
    return {
        "artifact_path": artifact_path,
        "claim_state": claim_state,
        "depth_basis": depth_basis,
        "depth_unit": depth_unit,
        "renderer": renderer,
        "plot_spec_digest": plot_spec_digest,
    }
