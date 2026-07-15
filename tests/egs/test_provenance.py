"""
test_provenance.py — EGS Provenance Tests

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from geox.egs.models.provenance import (
    EvidenceRef,
    ProvenanceAction,
    ProvenanceAgentKind,
    ProvenanceChain,
    ProvenanceRecord,
)


class TestProvenanceRecord:
    def test_create_provenance(self):
        pr = ProvenanceRecord(
            action=ProvenanceAction.CREATED,
            agent="Arif",
            agent_kind=ProvenanceAgentKind.HUMAN,
            description="Created entity",
        )
        assert pr.action == ProvenanceAction.CREATED
        assert len(pr.id) == 16

    def test_with_versions(self):
        pr = ProvenanceRecord(
            action=ProvenanceAction.UPDATED,
            agent="system",
            description="Updated geometry",
            entity_id="horizon_001",
            previous_version=1,
            new_version=2,
        )
        assert pr.previous_version == 1
        assert pr.new_version == 2


class TestProvenanceChain:
    def test_chain(self):
        chain = ProvenanceChain(entity_id="entity_001", entity_type="horizon")
        r1 = ProvenanceRecord(
            action=ProvenanceAction.CREATED,
            agent="Arif",
            description="Created",
            new_version=1,
        )
        chain.add_record(r1)
        assert chain.current_version == 1
        assert len(chain.records) == 1

        r2 = ProvenanceRecord(
            action=ProvenanceAction.UPDATED,
            agent="system",
            description="Updated",
            new_version=2,
        )
        chain.add_record(r2)
        assert chain.current_version == 2
        assert len(chain.records) == 2

    def test_history_ordering(self):
        chain = ProvenanceChain(entity_id="e1", entity_type="test")
        for i in range(5):
            chain.add_record(
                ProvenanceRecord(
                    action=ProvenanceAction.UPDATED,
                    agent="system",
                    description=f"Step {i}",
                    new_version=i + 1,
                )
            )
        history = chain.get_history(limit=3)
        assert len(history) == 3
        assert history[0].description == "Step 4"

    def test_get_record(self):
        chain = ProvenanceChain(entity_id="e1", entity_type="test")
        r = ProvenanceRecord(
            action=ProvenanceAction.CREATED,
            agent="test",
            description="First",
        )
        chain.add_record(r)
        found = chain.get_record(r.id)
        assert found is not None
        assert found.description == "First"
        assert chain.get_record("nonexistent") is None
