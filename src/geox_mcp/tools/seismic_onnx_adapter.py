"""
🌊 GEOX ONNX Model Adapter (PR-A3)

Interface contract for any neural proposer model. The adapter
deliberately forbids producing a final geological verdict:

  - Output is always CANDIDATE_GEOMETRY, never OBS_GEOLOGY.
  - Every model carries a model_manifest (license, intended use,
    prohibited_use, training_dataset_refs).
  - Promotion to live surface requires ≥5 benchmark gates (F3,
    CRACKS, Parihaka, SEAM, CRACKS-like).

Doctrine:
  - Models PROPOSE. Gates CHALLENGE.
  - arifOS SEALS.

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ──────────────────────────────────────────────────────────────────────
# Model manifest (license-aware, AAPG/AGPL/CC-aware)
# ──────────────────────────────────────────────────────────────────────


License = Literal[
    "Apache-2.0",
    "MIT",
    "BSD-3-Clause",
    "BSL-1.1",
    "EUPL-1.2",
    "LGPL-3.0",  # dynamic-link only
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC-BY-NC-4.0",  # RESEARCH ONLY — flagged
    "GPL-3.0",  # AVOID in commercial core
    "Research-only",
]


@dataclass(frozen=True)
class ModelManifest:
    """Every ONNX proposer must carry this manifest."""

    model_id: str
    revision: str  # sha256 of weights file
    license: License
    training_dataset_refs: list[str] = field(default_factory=list)
    intended_use: Literal["candidate_generation", "feature_extraction"] = "candidate_generation"
    prohibited_use: list[str] = field(default_factory=lambda: [
        "final_verdict",
        "autonomous_structure_acceptance",
        "capital_forecast",
    ])

    def is_commercial_safe(self) -> bool:
        """Reject CC-BY-NC and GPL from the commercial core."""
        if self.license in ("CC-BY-NC-4.0", "Research-only"):
            return False
        if self.license.startswith("GPL"):
            return False
        return True


# ──────────────────────────────────────────────────────────────────────
# Adapter interface
# ──────────────────────────────────────────────────────────────────────


@dataclass
class CandidateGeometry:
    """Generic candidate geometry output.

    The proposer must produce ONLY this shape — no Earth-verdict fields.
    """

    horizons: list[dict[str, Any]] = field(default_factory=list)
    faults: list[dict[str, Any]] = field(default_factory=list)
    image_quality_flags: list[dict[str, Any]] = field(default_factory=list)
    confidence_by_segment: dict[str, list[float]] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_horizons": self.horizons,
            "candidate_faults": self.faults,
            "image_quality_flags": self.image_quality_flags,
            "confidence_by_segment": self.confidence_by_segment,
            "provenance": {
                **self.provenance,
                "epistemic_label": "INT_SEISMIC",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "seal_authority": "arifOS_only",
            },
        }


class OnnxModelAdapter:
    """Abstract base for any ONNX proposer.

    Concrete adapters subclass this, validate the model_manifest on load,
    and never produce a final verdict. The interface is deliberately tiny
    so the proposer cannot smuggle out-of-scope claims.
    """

    def __init__(self, manifest: ModelManifest, weights_path: str = ""):
        if not manifest.is_commercial_safe():
            raise ValueError(
                f"model {manifest.model_id} license {manifest.license} is not "
                "commercial-safe (CC-BY-NC / GPL / Research-only blocked)"
            )
        self.manifest = manifest
        self.weights_path = weights_path
        self._loaded = False

    def load(self) -> None:
        """Load weights into an ONNX Runtime session.

        Concrete subclass MUST set self._loaded = True. Stub here for
        interfaces that defer to a remote engine (which would require
        888_HOLD).
        """
        self._loaded = True

    def propose(self, image: Any, calibration: dict[str, Any] | None = None) -> CandidateGeometry:
        """Run inference. Returns CANDIDATE_GEOMETRY only.

        Subclass MUST NOT return any field that hints at geological truth.
        """
        raise NotImplementedError("subclass must implement propose()")

    def refuse_to_seal(self) -> dict[str, Any]:
        """Mandatory: every proposer must declare its refusal to seal."""
        return {
            "model_id": self.manifest.model_id,
            "refuses": [
                "final_verdict",
                "autonomous_structure_acceptance",
                "capital_forecast",
            ],
            "promotion_required_benchmarks": [
                "synthetic_cases",
                "F3 Netherlands",
                "Parihaka",
                "SEAM Phase I",
                "CRACKS",
                "unseen Malaysian-basin section approved for testing",
            ],
            "epistemic_label": "INT_SEISMIC",
        }


# ──────────────────────────────────────────────────────────────────────
# Stub adapter — for tests + RGT/classical baseline as a model
# ──────────────────────────────────────────────────────────────────────


class ClassicalBaselineAdapter(OnnxModelAdapter):
    """Wraps the classical baseline as a 'proposer' so it can flow through
    the same propose → validate → falsify pipeline as a neural model.

    Manifest is locked Apache-2.0; no license risk.
    """

    def __init__(self, weights_path: str = ""):
        super().__init__(
            manifest=ModelManifest(
                model_id="geox-classical-baseline-v1",
                revision="classical-v1",
                license="Apache-2.0",
                training_dataset_refs=[],  # synthetic / classical, no training data
                intended_use="candidate_generation",
            ),
            weights_path=weights_path,
        )

    def propose(self, image: Any, calibration: dict[str, Any] | None = None) -> CandidateGeometry:
        # Lazy import to avoid circular dep
        from geox_mcp.tools.seismic_classical import classical_baseline

        out = classical_baseline(image)
        return CandidateGeometry(
            horizons=out["candidate_horizons"],
            faults=out["candidate_faults"],
            image_quality_flags=[],
            confidence_by_segment={},
            provenance={"source": "classical_baseline"},
        )


__all__ = [
    "CandidateGeometry",
    "ClassicalBaselineAdapter",
    "License",
    "ModelManifest",
    "OnnxModelAdapter",
]