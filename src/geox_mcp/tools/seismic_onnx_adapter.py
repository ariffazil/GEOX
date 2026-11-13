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


from geox_core.schemas.candidate_geometry import CandidateGeometry


@dataclass
class LegacyOnnxCandidateGeometry:
    """Legacy unstructured candidate geometry container — adapter internal only.

    Canonical governed CandidateGeometry schema lives in geox_core.schemas.candidate_geometry.
    Use .to_canonical() to convert this legacy bundle into strictly typed CandidateGeometry instances.
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

    def to_canonical(
        self,
        crs: str = "LOCAL",
        domain: Literal["time_ms", "depth_m"] = "time_ms",
    ) -> list[CandidateGeometry]:
        """Convert legacy unstructured adapter payload into canonical CandidateGeometry instances."""
        import hashlib
        import uuid

        canonical_items: list[CandidateGeometry] = []
        src_id = str(self.provenance.get("source") or "legacy_onnx_adapter")
        src_hash = hashlib.sha256(str(self.provenance).encode()).hexdigest()
        param_hash = hashlib.sha256(b"legacy_onnx_adapter_migration").hexdigest()

        # Convert faults
        for idx, f in enumerate(self.faults):
            pts = f.get("points") or f.get("pts") or []
            tuple_pts = tuple(tuple(float(v) for v in p) for p in pts if isinstance(p, (list, tuple)))
            if tuple_pts:
                canonical_items.append(
                    CandidateGeometry(
                        candidate_id=str(f.get("id") or f"cand_flt_legacy_{uuid.uuid4().hex[:8]}"),
                        source_data_ids=(src_id,),
                        source_sha256s=(src_hash,),
                        generator_name="seismic_onnx_adapter.legacy",
                        generator_version="legacy-v1",
                        parameters_hash=param_hash,
                        geometry_type="fault_segment",
                        coordinate_reference_system=crs,
                        domain=domain,
                        coordinates=tuple_pts,
                        epistemic_status="HYPOTHESIS",
                        promotion_state="GENERATED",
                    )
                )

        # Convert horizons
        for idx, h in enumerate(self.horizons):
            pts = h.get("points") or h.get("pts") or []
            tuple_pts = tuple(tuple(float(v) for v in p) for p in pts if isinstance(p, (list, tuple)))
            if tuple_pts:
                canonical_items.append(
                    CandidateGeometry(
                        candidate_id=str(h.get("id") or f"cand_hrz_legacy_{uuid.uuid4().hex[:8]}"),
                        source_data_ids=(src_id,),
                        source_sha256s=(src_hash,),
                        generator_name="seismic_onnx_adapter.legacy",
                        generator_version="legacy-v1",
                        parameters_hash=param_hash,
                        geometry_type="horizon_fragment",
                        coordinate_reference_system=crs,
                        domain=domain,
                        coordinates=tuple_pts,
                        epistemic_status="HYPOTHESIS",
                        promotion_state="GENERATED",
                    )
                )

        return canonical_items


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

    def propose(self, image: Any, calibration: dict[str, Any] | None = None) -> LegacyOnnxCandidateGeometry:
        raise NotImplementedError("subclass must implement propose()")

    def propose_canonical(self, image: Any, calibration: dict[str, Any] | None = None) -> list[CandidateGeometry]:
        legacy = self.propose(image, calibration)
        return legacy.to_canonical()

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

    def propose(self, image: Any, calibration: dict[str, Any] | None = None) -> LegacyOnnxCandidateGeometry:
        from geox_mcp.tools.seismic_classical import classical_baseline

        out = classical_baseline(image)
        return LegacyOnnxCandidateGeometry(
            horizons=out["candidate_horizons"],
            faults=out["candidate_faults"],
            image_quality_flags=[],
            confidence_by_segment={},
            provenance={"source": "classical_baseline"},
        )


__all__ = [
    "CandidateGeometry",
    "LegacyOnnxCandidateGeometry",
    "ClassicalBaselineAdapter",
    "License",
    "ModelManifest",
    "OnnxModelAdapter",
]
