"""
CandidateGeometry Schema — Immutable, strictly typed hypothesis container.
Phase B2 Contract (ARIF Sovereign Seal 2026-11-03).
════════════════════════════════════════════════════════════════════════════════
Invariants:
1. epistemic_status is strictly HYPOTHESIS.
2. promotion_state starts at GENERATED, advances to SCREENED, SURVIVES_TEST or REJECTED.
3. HUMAN_ACCEPTED is impossible via automated generation or gate evaluation.
4. Outer class is frozen; all internal sequence collections are immutable tuples.
5. Volumetrics and accepted interpretations MUST reject candidates that are not HUMAN_ACCEPTED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

GateVerdict = Literal[
    "PASS",
    "FAIL",
    "NOT_RUN",
    "INSUFFICIENT_INPUT",
    "ERROR",
]

PromotionState = Literal[
    "GENERATED",
    "SCREENED",
    "SURVIVES_TEST",
    "REJECTED",
    "HUMAN_ACCEPTED",
]

GeometryType = Literal[
    "fault_segment",
    "horizon_fragment",
    "closure_outline",
]

DomainType = Literal["time_ms", "depth_m"]


@dataclass(frozen=True)
class CandidateGeometry:
    candidate_id: str

    source_data_ids: tuple[str, ...]
    source_sha256s: tuple[str, ...]

    generator_name: str
    generator_version: str
    parameters_hash: str

    geometry_type: GeometryType
    coordinate_reference_system: str
    domain: DomainType
    coordinates: tuple[tuple[float, ...], ...]

    epistemic_status: Literal["HYPOTHESIS"] = "HYPOTHESIS"
    promotion_state: PromotionState = "GENERATED"

    falsifier_results: dict[str, GateVerdict] = field(default_factory=dict)
    rejection_reasons: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_data_ids": list(self.source_data_ids),
            "source_sha256s": list(self.source_sha256s),
            "generator_name": self.generator_name,
            "generator_version": self.generator_version,
            "parameters_hash": self.parameters_hash,
            "geometry_type": self.geometry_type,
            "coordinate_reference_system": self.coordinate_reference_system,
            "domain": self.domain,
            "coordinates": [list(c) for c in self.coordinates],
            "epistemic_status": self.epistemic_status,
            "promotion_state": self.promotion_state,
            "falsifier_results": dict(self.falsifier_results),
            "rejection_reasons": list(self.rejection_reasons),
            "missing_evidence": list(self.missing_evidence),
            "contradictions": list(self.contradictions),
        }

    def with_falsifier_results(
        self,
        results: dict[str, GateVerdict],
        reasons: tuple[str, ...] = (),
        missing: tuple[str, ...] = (),
        contradictions: tuple[str, ...] = (),
    ) -> CandidateGeometry:
        """Return a new instance with updated falsifier results.

        Invariants:
        - If any falsifier fails, state becomes REJECTED.
        - If all evaluated gates pass (and at least one evaluated), state becomes SURVIVES_TEST.
        - Under no circumstances can this promote to HUMAN_ACCEPTED.
        """
        has_fail = any(v == "FAIL" for v in results.values())
        has_error = any(v == "ERROR" for v in results.values())
        has_pass = any(v == "PASS" for v in results.values())

        if has_fail:
            new_state: PromotionState = "REJECTED"
        elif has_pass and not has_error:
            new_state = "SURVIVES_TEST"
        else:
            new_state = "SCREENED"

        merged_results = {**self.falsifier_results, **results}
        # Deduplicate while preserving order
        merged_reasons = tuple(dict.fromkeys(self.rejection_reasons + reasons))
        merged_missing = tuple(dict.fromkeys(self.missing_evidence + missing))
        merged_contradictions = tuple(dict.fromkeys(self.contradictions + contradictions))

        return CandidateGeometry(
            candidate_id=self.candidate_id,
            source_data_ids=self.source_data_ids,
            source_sha256s=self.source_sha256s,
            generator_name=self.generator_name,
            generator_version=self.generator_version,
            parameters_hash=self.parameters_hash,
            geometry_type=self.geometry_type,
            coordinate_reference_system=self.coordinate_reference_system,
            domain=self.domain,
            coordinates=self.coordinates,
            epistemic_status="HYPOTHESIS",
            promotion_state=new_state,
            falsifier_results=merged_results,
            rejection_reasons=merged_reasons,
            missing_evidence=merged_missing,
            contradictions=merged_contradictions,
        )
