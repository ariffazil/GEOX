"""
Portfolio Audit Module — Correlation tracking for epistemic risk.
══════════════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Detects when multiple prospects in a portfolio share the same model lineage.
Prevents "model infection" where one biased AI model affects many decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ProspectNode:
    prospect_id: str
    model_lineage_hash: str
    integrity_score: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class PortfolioAuditResult:
    status: str  # PASS, WARNING, CRITICAL
    correlation_ratio: float
    dominant_model_hash: str | None
    affected_prospects: list[str]
    recommendation: str


class PortfolioTracker:
    """
    Monitors portfolio-wide epistemic correlation.
    """

    def __init__(self, critical_threshold: float = 0.4) -> None:
        self.critical_threshold = critical_threshold
        self.prospects: dict[str, ProspectNode] = {}

    def add_prospect(
        self,
        prospect_id: str,
        model_lineage_hash: str,
        integrity_score: float
    ) -> None:
        """Add or update a prospect in the tracking registry."""
        self.prospects[prospect_id] = ProspectNode(
            prospect_id=prospect_id,
            model_lineage_hash=model_lineage_hash,
            integrity_score=integrity_score
        )

    def audit_portfolio(self) -> PortfolioAuditResult:
        """
        Check for dominant model lineage across the portfolio.
        """
        if not self.prospects:
            return PortfolioAuditResult(
                status="PASS",
                correlation_ratio=0.0,
                dominant_model_hash=None,
                affected_prospects=[],
                recommendation="Empty portfolio"
            )

        # Count occurrences of each model hash
        counts: dict[str, list[str]] = {}
        for p_id, node in self.prospects.items():
            if node.model_lineage_hash not in counts:
                counts[node.model_lineage_hash] = []
            counts[node.model_lineage_hash].append(p_id)

        # Find the most frequent model hash
        dominant_hash = max(counts, key=lambda k: len(counts[k]))
        affected_prospects = counts[dominant_hash]
        total_prospects = len(self.prospects)
        correlation_ratio = len(affected_prospects) / total_prospects

        status = "PASS"
        recommendation = "Portfolio diverse"

        if correlation_ratio >= self.critical_threshold:
            status = "CRITICAL"
            recommendation = (
                f"CORRELATION_CRITICAL: {len(affected_prospects)}/{total_prospects} "
                f"prospects sharing lineage {dominant_hash}. Portfolio at risk."
            )
        elif correlation_ratio >= 0.2:
            status = "WARNING"
            recommendation = (
                f"CORRELATION_WARNING: Elevated shared lineage {dominant_hash}."
            )

        return PortfolioAuditResult(
            status=status,
            correlation_ratio=correlation_ratio,
            dominant_model_hash=dominant_hash,
            affected_prospects=affected_prospects,
            recommendation=recommendation
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_prospects": len(self.prospects),
            "prospects": {
                p_id: {
                    "hash": node.model_lineage_hash,
                    "score": node.integrity_score,
                    "ts": node.timestamp
                }
                for p_id, node in self.prospects.items()
            }
        }
