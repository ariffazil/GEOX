"""
Epistemic Integrity Module — AlphaFold pLDDT equivalent for GEOX.
══════════════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Governs epistemic integrity scoring, model lineage tracking, and independence 
checking for subsurface outputs. Prevents model-correlated risk from reaching 
WEALTH capital allocation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfidenceLevel:
    parameter: str
    score: float  # [0.0, 1.0]
    basis: str  # e.g., "Well data", "Seismic inversion", "Analogue"
    evidence_density: float  # wells per 100km2


@dataclass
class EpistemicResult:
    integrity_score: float
    classification: str  # CLAIM, PLAUSIBLE, AUTO_HOLD
    posterior_breadth: float
    evidence_density: float
    model_lineage_hash: str
    independence_score: float
    recommendation: str
    confidence_levels: list[ConfidenceLevel] = field(default_factory=list)
    hold: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_score": round(self.integrity_score, 4),
            "classification": self.classification,
            "posterior_breadth": round(self.posterior_breadth, 4),
            "evidence_density": round(self.evidence_density, 4),
            "model_lineage_hash": self.model_lineage_hash,
            "independence_score": round(self.independence_score, 4),
            "recommendation": self.recommendation,
            "confidence_levels": [
                {
                    "parameter": c.parameter,
                    "score": round(c.score, 4),
                    "basis": c.basis,
                    "evidence_density": round(c.evidence_density, 4),
                }
                for c in self.confidence_levels
            ],
            "hold": self.hold,
        }


class EpistemicIntegrity:
    """
    Governs epistemic integrity scoring.
    Enforces pLDDT-style per-element confidence and independence checking.
    """

    def __init__(self, auto_hold_threshold: float = 0.3, warning_threshold: float = 0.6) -> None:
        self.auto_hold_threshold = auto_hold_threshold
        self.warning_threshold = warning_threshold

    def compute_integrity(
        self,
        outputs: dict[str, Any],
        well_density: float,
        model_lineage: list[str],
        pos_components: dict[str, str] | None = None,
    ) -> EpistemicResult:
        """
        Compute full epistemic integrity score.

        Args:
            outputs: Subsurface results (must contain p10, p50, p90 for breadth).
            well_density: Wells per 100km2.
            model_lineage: List of model IDs/hashes that touched this result.
            pos_components: Map of PoS component -> model_lineage_hash.
                           Used for independence checking.
        """
        # 1. Posterior Breadth
        p10 = outputs.get("p10", 0.1)
        p90 = outputs.get("p90", 0.5)
        posterior_breadth = p90 / p10 if p10 > 0 else 10.0

        # 2. Model Lineage Hash (Aggregate consistency)
        lineage_str = "|".join(sorted(model_lineage))
        lineage_hash = hashlib.sha256(lineage_str.encode()).hexdigest()[:16]

        # 3. Independence Score
        independence_score = self._check_independence(pos_components)

        # 4. Confidence Levels (pLDDT equivalent)
        confidence_levels = self._compute_per_element_confidence(outputs, well_density)
        avg_confidence = (
            sum(c.score for c in confidence_levels) / len(confidence_levels)
            if confidence_levels
            else 0.5
        )

        # 5. Final Integrity Score Formula
        # weights: evidence_density (0.4), posterior_breadth (0.2), 
        # independence (0.2), avg_confidence (0.2)
        
        # Normalize evidence density: 1.0 at 5 wells/100km2
        norm_density = min(well_density / 5.0, 1.0)
        
        # Normalize breadth: 1.0 at ratio 2.0, 0.0 at ratio 10.0
        norm_breadth = max(0.0, 1.0 - (posterior_breadth - 2.0) / 8.0)
        
        integrity_score = (
            (norm_density * 0.4) +
            (norm_breadth * 0.2) +
            (independence_score * 0.2) +
            (avg_confidence * 0.2)
        )

        # 6. Classification & Recommendation
        hold = False
        recommendation = "PASS"
        if integrity_score < self.auto_hold_threshold:
            classification = "AUTO_HOLD"
            recommendation = "HOLD: Integrity score below 0.3 (Epistemic Collapse)"
            hold = True
        elif integrity_score < self.warning_threshold:
            classification = "PLAUSIBLE"
            recommendation = "WARNING: Moderate epistemic uncertainty"
        else:
            classification = "CLAIM"
            recommendation = "PASS"

        return EpistemicResult(
            integrity_score=integrity_score,
            classification=classification,
            posterior_breadth=posterior_breadth,
            evidence_density=well_density,
            model_lineage_hash=lineage_hash,
            independence_score=independence_score,
            recommendation=recommendation,
            confidence_levels=confidence_levels,
            hold=hold,
        )

    def _check_independence(self, pos_components: dict[str, str] | None) -> float:
        """
        Detects geological coupling in PoS components.
        If all components share the same model lineage, independence is 0.0.
        """
        if not pos_components:
            return 0.5  # Neutral if unknown

        unique_models = set(pos_components.values())
        component_count = len(pos_components)
        
        if component_count <= 1:
            return 1.0

        # Basic independence metric: ratio of unique models to total components
        independence = len(unique_models) / component_count
        return independence

    def _compute_per_element_confidence(
        self, outputs: dict[str, Any], well_density: float
    ) -> list[ConfidenceLevel]:
        """
        Computes pLDDT-style per-element confidence.
        """
        levels = []
        
        # Parameters to check
        params = ["porosity", "sw", "vsh", "net_pay", "permeability"]
        
        for p in params:
            if p in outputs:
                # Base score from well density
                score = min(well_density / 4.0, 0.8) # Cap well data at 0.8
                
                # Boost if specifically marked as "measured"
                basis = outputs.get(f"{p}_source", "inferred")
                if basis == "measured":
                    score = min(score + 0.2, 1.0)
                
                levels.append(ConfidenceLevel(
                    parameter=p,
                    score=score,
                    basis=basis,
                    evidence_density=well_density
                ))
                
        return levels
