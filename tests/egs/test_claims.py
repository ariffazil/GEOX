"""
test_claims.py — EGS Claim & Evidence Tests

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import pytest

from geox.egs.models.claims import (
    ClaimDomain,
    ClaimEnvelope,
    ClaimStatus,
    CompetingInterpretation,
    InterpretationSet,
)
from geox.egs.models.provenance import EvidenceKind, EvidenceRef, EvidenceStrength, ProvenanceAction, ProvenanceRecord


class TestClaimEnvelope:
    def test_create_claim(self):
        claim = ClaimEnvelope(
            title="Top reservoir is at 2500m TVDSS",
            statement="The top of the Group A reservoir is interpreted at 2500m TVDSS based on well markers.",
            domain=ClaimDomain.STRATIGRAPHY,
            author="Arif",
            confidence_score=0.85,
        )
        assert claim.status == ClaimStatus.DRAFT
        assert claim.domain == ClaimDomain.STRATIGRAPHY
        assert len(claim.id) == 16

    def test_claim_with_evidence(self):
        claim = ClaimEnvelope(
            title="Test claim",
            statement="Test statement",
        )
        ev = EvidenceRef(
            evidence_kind=EvidenceKind.WELL_LOG,
            strength=EvidenceStrength.DIRECT_MEASUREMENT,
            description="Gamma ray log shows the marker at 2500m",
            source="Well-001",
        )
        claim.add_evidence(ev, supporting=True)
        assert len(claim.evidence_for) == 1
        assert claim.evidence_balance == 1.0

    def test_claim_with_contradicting_evidence(self):
        claim = ClaimEnvelope(
            title="Test claim",
            statement="Test statement",
            status=ClaimStatus.ACCEPTED,
        )
        ev = EvidenceRef(
            evidence_kind=EvidenceKind.SEISMIC,
            strength=EvidenceStrength.SINGLE_LINE,
            description="Seismic shows different geometry",
            supporting=False,
        )
        claim.add_evidence(ev, supporting=False)
        assert claim.status == ClaimStatus.CHALLENGED
        assert claim.evidence_balance < 0

    def test_evidence_balance(self):
        claim = ClaimEnvelope(title="Balance test", statement="Test")
        e1 = EvidenceRef(
            evidence_kind=EvidenceKind.LITERATURE,
            strength=EvidenceStrength.SINGLE_LINE,
            description="Supports",
            supporting=True,
        )
        e2 = EvidenceRef(
            evidence_kind=EvidenceKind.LITERATURE,
            strength=EvidenceStrength.SINGLE_LINE,
            description="Challenges",
            supporting=False,
        )
        claim.add_evidence(e1, supporting=True)
        claim.add_evidence(e2, supporting=False)
        assert claim.evidence_balance == 0.0

    def test_add_provenance(self):
        claim = ClaimEnvelope(title="Prov test", statement="Test")
        pr = ProvenanceRecord(
            action=ProvenanceAction.CREATED,
            agent="system",
            description="Created",
        )
        claim.add_provenance(pr)
        assert len(claim.provenance) == 1


class TestInterpretationSet:
    def test_interpretation_set(self):
        primary = ClaimEnvelope(
            title="Primary interpretation",
            statement="Horizon is at 2000m",
        )
        alt_claim = ClaimEnvelope(
            title="Alternative interpretation",
            statement="Horizon is at 2100m",
        )
        alt = CompetingInterpretation(
            claim=alt_claim,
            proponent="Another interpreter",
            key_differences=["Depth difference of 100m"],
        )
        interp_set = InterpretationSet(
            entity_id="horizon_001",
            entity_type="horizon",
            primary_interpretation=primary,
        )
        interp_set.add_alternative(alt)
        assert len(interp_set.alternatives) == 1
        assert interp_set.consensus_status == "contested"
