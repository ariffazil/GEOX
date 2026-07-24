"""
🌊 GEOX ONNX Model Adapter (PR-A3)

Interface contract for any neural proposer model. The adapter
deliberately forbids producing a final geological verdict:

  - Output is always CANDIDATE_GEOMETRY, never OBS_GEOLOGY.
  - Every model carries a model_manifest (license, intended use,
    prohibited_use, training_dataset_refs).
  - Promotion to live surface requires ≥5 benchmark gates.

Doctrine:
  - Models PROPOSE. Gates CHALLENGE.
  - arifOS SEALS.

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

License = Literal[
    "Apache-2.0",
    "MIT",
    "BSD-3-Clause",
    "BSL-1.1",
    "EUPL-1.2",
    "LGPL-3.0",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC-BY-NC-4.0",
    "GPL-3.0",
    "Research-only",
]


@dataclass(frozen=True)
class ModelManifest:
    """Every ONNX proposer must carry this manifest."""

    model_id: str
    revision: str
    license: License
    training_dataset_refs: list[str] = field(default_factory=list)
    intended_use: Literal["candidate_generation", "feature_extraction"] = "candidate_generation"
    prohibited_use: list[str] = field(
        default_factory=lambda: [
            "final_verdict",
            "autonomous_structure_acceptance",
            "capital_forecast",
        ]
    )

    def is_commercial_safe(self) -> bool:
        if self.license in ("CC-BY-NC-4.0", "Research-only"):
            return False
        if self.license.startswith("GPL"):
            return False
        return True


@dataclass
class CandidateGeometry:
    """Generic candidate geometry output — never an Earth-verdict field."""

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
    """Abstract base for any ONNX proposer."""

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
        self._loaded = True

    def propose(self, image: Any, calibration: dict[str, Any] | None = None) -> CandidateGeometry:
        raise NotImplementedError("subclass must implement propose()")

    def refuse_to_seal(self) -> dict[str, Any]:
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


class ClassicalBaselineAdapter(OnnxModelAdapter):
    """Wraps the classical baseline as a 'proposer'."""

    def __init__(self, weights_path: str = ""):
        super().__init__(
            manifest=ModelManifest(
                model_id="geox-classical-baseline-v1",
                revision="classical-v1",
                license="Apache-2.0",
                training_dataset_refs=[],
                intended_use="candidate_generation",
            ),
            weights_path=weights_path,
        )

    def propose(self, image: Any, calibration: dict[str, Any] | None = None) -> CandidateGeometry:
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
