"""
test_intelligence_flow.py — Tests for the dynamic flow schema
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBEI

Verifies:
  - 7 layers + foundation + audit
  - 5 tool families
  - FlowPacket creation with F4 CLARITY
  - F1 content hash integrity
  - F8 transition rules
  - F7 confidence cap
"""
from __future__ import annotations

import pytest

from geox_core.schemas.intelligence_flow import (
    FlowLayer,
    FlowPacket,
    FlowSession,
    FlowStage,
    LAYER_DESCRIPTORS,
    TOOL_FAMILIES,
    VALID_TRANSITIONS,
    ToolFamily,
    is_valid_transition,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 7 Layers + Foundation + Audit
# ═══════════════════════════════════════════════════════════════════════════════


class TestLayers:
    def test_seven_layers_present(self) -> None:
        """Canonical 7 layers (0-5) + FOUNDATION + AUDIT."""
        assert FlowLayer.INGEST == 0
        assert FlowLayer.WITNESS == 1
        assert FlowLayer.PHYSICS == 2
        assert FlowLayer.ARCHITECTURE == 3
        assert FlowLayer.INTERPRET == 4
        assert FlowLayer.DECISION == 5
        assert FlowLayer.FOUNDATION == 98
        assert FlowLayer.AUDIT == 99

    def test_each_layer_has_descriptor(self) -> None:
        for layer in FlowLayer:
            assert layer in LAYER_DESCRIPTORS, f"Missing descriptor for {layer.name}"
            desc = LAYER_DESCRIPTORS[layer]
            for key in ("name", "purpose", "input", "output", "doctrine_gate"):
                assert key in desc, f"Layer {layer.name} missing key {key}"


# ═══════════════════════════════════════════════════════════════════════════════
# 5 Tool Families (RSI-merged from Copilot's 13)
# ═══════════════════════════════════════════════════════════════════════════════


class TestToolFamilies:
    def test_five_families(self) -> None:
        assert len(ToolFamily) == 5

    def test_each_family_has_required_keys(self) -> None:
        for fam in ToolFamily:
            desc = TOOL_FAMILIES[fam]
            for key in (
                "description",
                "primary_layer",
                "tools_complete",
                "tools_pending",
                "vp_grammar_source",
                "kinabalu_phase1_deliverable",
                "effort_estimate_days",
            ):
                assert key in desc, f"Family {fam.value} missing key {key}"

    def test_family_a_has_crustal_domain_complete(self) -> None:
        """Family A — geox_anomalous_contrast_detect (ToAC loop) was forged this session."""
        desc = TOOL_FAMILIES[ToolFamily.A_CRUSTAL_ARCHITECTURE]
        assert "geox_anomalous_contrast_detect" in desc["tools_complete"]

    def test_family_d_has_doctrine_complete(self) -> None:
        """Family D — doctrine layer is pre-existing."""
        desc = TOOL_FAMILIES[ToolFamily.D_GOVERNANCE]
        for tool in [
            "geox_doctrine_assumption_register",
            "geox_doctrine_anti_beautiful_one",
            "geox_doctrine_godel_review",
        ]:
            assert tool in desc["tools_complete"]

    def test_family_e_has_lem_predict_complete(self) -> None:
        """Family E — geox_lem_predict was pre-existing substrate."""
        desc = TOOL_FAMILIES[ToolFamily.E_LEM_FOUNDATION]
        assert "geox_lem_predict" in desc["tools_complete"]

    def test_total_pending_count(self) -> None:
        """Total pending tools across all families (sanity check)."""
        total = sum(
            len(desc["tools_pending"]) for desc in TOOL_FAMILIES.values()
        )
        assert total >= 8, f"Expected ≥8 pending tools, got {total}"

    def test_total_complete_count(self) -> None:
        total = sum(
            len(desc["tools_complete"]) for desc in TOOL_FAMILIES.values()
        )
        assert total >= 5, f"Expected ≥5 complete tools, got {total}"


# ═══════════════════════════════════════════════════════════════════════════════
# F4 CLARITY — Pydantic envelope strict
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlowPacketEnvelope:
    def test_packet_no_extra_fields(self) -> None:
        with pytest.raises(Exception):
            FlowPacket(
                packet_id="abc12345",
                source_layer=FlowLayer.PHYSICS,
                target_layer=FlowLayer.ARCHITECTURE,
                epistemic_rank=FlowStage.DER,
                confidence=0.5,
                payload={"x": 1},
                source_tool="geox_joint_inversion",
                rogue_field="not_allowed",  # type: ignore[call-arg]
            )

    def test_packet_validates_confidence_cap(self) -> None:
        """F7 HUMILITY — confidence hard-capped at 0.90."""
        with pytest.raises(Exception):
            FlowPacket(
                packet_id="abc12345",
                source_layer=FlowLayer.PHYSICS,
                target_layer=FlowLayer.ARCHITECTURE,
                epistemic_rank=FlowStage.DER,
                confidence=0.95,  # VIOLATION
                payload={"x": 1},
                source_tool="geox_joint_inversion",
            )

    def test_packet_validates_packet_id_length(self) -> None:
        with pytest.raises(Exception):
            FlowPacket(
                packet_id="short",  # < 8 chars
                source_layer=FlowLayer.PHYSICS,
                target_layer=FlowLayer.ARCHITECTURE,
                epistemic_rank=FlowStage.DER,
                confidence=0.5,
                payload={"x": 1},
                source_tool="geox_joint_inversion",
            )

    def test_packet_valid_minimum(self) -> None:
        p = FlowPacket(
            packet_id="abc12345",
            source_layer=FlowLayer.PHYSICS,
            target_layer=FlowLayer.ARCHITECTURE,
            epistemic_rank=FlowStage.DER,
            confidence=0.85,
            payload={"vp_km_s": 6.0, "crust_zone": "normal_continental"},
            source_tool="geox_joint_inversion",
        )
        assert p.confidence == 0.85


# ═══════════════════════════════════════════════════════════════════════════════
# F1 AMANAH — content-addressed hash
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentHash:
    def test_packet_added_with_hash(self) -> None:
        session = FlowSession(session_id="sess12345")
        p = FlowPacket(
            packet_id="pkt12345",
            source_layer=FlowLayer.INGEST,
            target_layer=FlowLayer.WITNESS,
            epistemic_rank=FlowStage.OBS,
            confidence=0.5,
            payload={"value": 1},
            source_tool="geox_data_ingest_bundle",
        )
        assert p.content_hash is None
        session.add_packet(p)
        assert p.content_hash is not None
        assert p.content_hash.startswith("sha256:")

    def test_different_payloads_produce_different_hashes(self) -> None:
        session = FlowSession(session_id="sess12345")
        p1 = FlowPacket(
            packet_id="pkt12345",
            source_layer=FlowLayer.INGEST,
            target_layer=FlowLayer.WITNESS,
            epistemic_rank=FlowStage.OBS,
            confidence=0.5,
            payload={"value": 1},
            source_tool="geox_data_ingest_bundle",
        )
        p2 = FlowPacket(
            packet_id="pkt67890",
            source_layer=FlowLayer.INGEST,
            target_layer=FlowLayer.WITNESS,
            epistemic_rank=FlowStage.OBS,
            confidence=0.5,
            payload={"value": 2},
            source_tool="geox_data_ingest_bundle",
        )
        session.add_packet(p1)
        session.add_packet(p2)
        assert p1.content_hash != p2.content_hash


# ═══════════════════════════════════════════════════════════════════════════════
# F8 LAW — transition rules
# ═══════════════════════════════════════════════════════════════════════════════


class TestTransitionRules:
    def test_forward_chain_valid(self) -> None:
        """Forward chain: INGEST → WITNESS → PHYSICS → ARCH → INTERPRET → DECISION."""
        for src, tgt in [
            (FlowLayer.INGEST, FlowLayer.WITNESS),
            (FlowLayer.WITNESS, FlowLayer.PHYSICS),
            (FlowLayer.PHYSICS, FlowLayer.ARCHITECTURE),
            (FlowLayer.ARCHITECTURE, FlowLayer.INTERPRET),
            (FlowLayer.INTERPRET, FlowLayer.DECISION),
        ]:
            assert is_valid_transition(src, tgt), f"{src.name} → {tgt.name} should be valid"

    def test_skipping_layers_invalid(self) -> None:
        """Cannot skip layers (e.g., INGEST → PHYSICS)."""
        assert not is_valid_transition(FlowLayer.INGEST, FlowLayer.PHYSICS)
        assert not is_valid_transition(FlowLayer.WITNESS, FlowLayer.ARCHITECTURE)

    def test_foundation_lateral(self) -> None:
        """FOUNDATION can touch any non-audit layer."""
        for tgt in [
            FlowLayer.INGEST,
            FlowLayer.WITNESS,
            FlowLayer.PHYSICS,
            FlowLayer.ARCHITECTURE,
            FlowLayer.INTERPRET,
            FlowLayer.DECISION,
        ]:
            assert is_valid_transition(FlowLayer.FOUNDATION, tgt)

    def test_audit_transverse(self) -> None:
        """AUDIT can transition to any layer."""
        for tgt in [
            FlowLayer.INGEST,
            FlowLayer.WITNESS,
            FlowLayer.PHYSICS,
            FlowLayer.ARCHITECTURE,
            FlowLayer.INTERPRET,
            FlowLayer.DECISION,
        ]:
            assert is_valid_transition(FlowLayer.AUDIT, tgt)

    def test_reverse_anomaly_feedback(self) -> None:
        """Architecture → Physics is allowed (anomaly feedback loop)."""
        assert is_valid_transition(FlowLayer.ARCHITECTURE, FlowLayer.PHYSICS)


# ═══════════════════════════════════════════════════════════════════════════════
# FlowSession — end-to-end
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlowSession:
    def test_complete_flow_chain(self) -> None:
        """Simulate a complete intelligence flow from INGEST to DECISION."""
        session = FlowSession(
            session_id="flow12345",
            basin_name="Kinabalu",
        )

        # INGEST → WITNESS
        session.add_packet(
            FlowPacket(
                packet_id="obs12345",
                source_layer=FlowLayer.INGEST,
                target_layer=FlowLayer.WITNESS,
                epistemic_rank=FlowStage.OBS,
                confidence=0.5,
                payload={"file": "Tembungo-1.LAS"},
                source_tool="geox_data_ingest_bundle",
            )
        )
        # WITNESS → PHYSICS
        session.add_packet(
            FlowPacket(
                packet_id="obs67890",
                source_layer=FlowLayer.WITNESS,
                target_layer=FlowLayer.PHYSICS,
                epistemic_rank=FlowStage.OBS,
                confidence=0.7,
                payload={"qc_passed": True},
                source_tool="geox_data_qc_bundle",
            )
        )
        # PHYSICS → ARCHITECTURE
        session.add_packet(
            FlowPacket(
                packet_id="der12345",
                source_layer=FlowLayer.PHYSICS,
                target_layer=FlowLayer.ARCHITECTURE,
                epistemic_rank=FlowStage.DER,
                confidence=0.85,
                payload={"vp_km_s": 6.0, "zone": "normal_continental"},
                source_tool="geox_joint_inversion",
            )
        )
        # ARCHITECTURE → INTERPRET
        session.add_packet(
            FlowPacket(
                packet_id="int12345",
                source_layer=FlowLayer.ARCHITECTURE,
                target_layer=FlowLayer.INTERPRET,
                epistemic_rank=FlowStage.INT,
                confidence=0.75,
                payload={"claim": "Kinabalu inboard = normal_continental"},
                source_tool="geox_crustal_domain_classify",
            )
        )
        # INTERPRET → DECISION
        session.add_packet(
            FlowPacket(
                packet_id="dec12345",
                source_layer=FlowLayer.INTERPRET,
                target_layer=FlowLayer.DECISION,
                epistemic_rank=FlowStage.SPEC,
                confidence=0.65,
                payload={"prospect_id": "KB-A1"},
                source_tool="geox_prospect_evaluate",
            )
        )

        assert len(session.packets) == 5
        # Every packet has a content hash (F1 AMANAH)
        for p in session.packets:
            assert p.content_hash is not None
            assert p.content_hash.startswith("sha256:")

        # Final layer is DECISION
        assert session.packets[-1].target_layer == FlowLayer.DECISION
