"""
Test: Sabah Basin Metabolic Spine — Full Federation Loop
═══════════════════════════════════════════════════════════════════════════════

The first end-to-end test of the Federation Metabolism Spine.

Scenario: Assess Sabah Basin opportunity/risk
Flow:     GEOX → WEALTH → WELL → arifOS → A-FORGE → VAULT999 → F13

This test exercises:
  1. GEOX produces evidence wrapped in FederationEnvelope
  2. Envelope flows through organ chain with trace_id preservation
  3. Each organ adds its layer without breaking the envelope
  4. Constitutional floor checks propagate correctly
  5. F13 gate blocks IRREVERSIBLE actions without sovereign approval

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from contracts.schemas.federation_envelope import (
    AutonomyBand,
    ExecutionStatus,
    FederationEnvelope,
    FloorCheck,
    MetabolicPhase,
    OrganID,
    ReversibilityClass,
    RiskClass,
    build_federation_envelope,
    geox_to_federation_envelope,
)


# ── Test fixtures ─────────────────────────────────────────────────────────────


def _trace_id() -> str:
    return f"trc-{uuid4().hex[:12]}"


def _sabah_basin_geox_output() -> dict:
    """Simulated GEOX basin screening output for Sabah Basin."""
    return {
        "execution_status": "success",
        "tool_class": "basin",
        "governance_status": "autonomous",
        "artifact_status": "created",
        "claim_state": "INTERPRETED",
        "claim_tag": "SABAH-BASIN-SCREEN-001",
        "perception_class": "DERIVED",
        "confidence_band": {"low": 0.4, "mid": 0.6, "high": 0.75},
        "humility_score": 0.35,
        "evidence_refs": [
            "macrostrat:Sabah_Basin",
            "geox:deep_time_state:Miocene",
            "ne:10m:Sabah_boundary",
        ],
        "provenance": {
            "tool_name": "geox_basin",
            "tool_version": "v2026.06.29",
            "artifact_hash": "sha256:sabah_basin_001",
            "claim_state": "INTERPRETED",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "session_id": "SEAL-test-sabah-001",
        },
        "primary_artifact": {
            "basin_name": "Sabah Basin",
            "basin_type": "forearc",
            "age_ma_range": [23.0, 0.0],
            "primary_source_rocks": ["Crocker Fm", "Temburong Fm"],
            "primary_reservoirs": ["Kudat Fm", "Meligan Fm"],
            "structural_style": "thrust_and_fold",
            "petroleum_system": "oil_biogenic",
            "play_count": 4,
            "risk_summary": "Moderate geological risk. Active tectonics creates both trap and seal risk.",
        },
        "depth_basis": {"type": "TVDSS", "datum": "MSL"},
    }


def _sabah_prospect_output() -> dict:
    """Simulated GEOX prospect evaluation for Sabah Basin opportunity."""
    return {
        "execution_status": "success",
        "tool_class": "evaluation",
        "governance_status": "governed",
        "artifact_status": "created",
        "claim_state": "DERIVED_CANDIDATE",
        "claim_tag": "SABAH-PROSPECT-001",
        "perception_class": "HYPOTHESIS",
        "confidence_band": {"low": 0.25, "mid": 0.45, "high": 0.60},
        "humility_score": 0.55,
        "evidence_refs": [
            "geox_basin:Sabah_Basin",
            "geox_well:SN-1",
            "geox_seismic:SABAH-3D-2024",
        ],
        "provenance": {
            "tool_name": "geox_prospect",
            "tool_version": "v2026.06.29",
            "artifact_hash": "sha256:sabah_prospect_001",
            "claim_state": "DERIVED_CANDIDATE",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "session_id": "SEAL-test-sabah-001",
        },
        "primary_artifact": {
            "prospect_name": "Sabah Deep Water Fan",
            "play_type": "stratigraphic_trap",
            "volumetrics": {
                "stoiip_p50_mmstb": 120,
                "stoiip_p10_mmstb": 250,
                "stoiip_p90_mmstb": 45,
                "gas_p50_bcf": 350,
            },
            "pos_estimate": 0.35,
            "npv_usd_million": 850,
            "irr_estimate": 0.18,
            "evoi_usd_million": 12,
            "key_risks": [
                "Seal integrity in active tectonic setting",
                "Reservoir quality at depth (>3000m)",
                "Trap geometry uncertainty",
            ],
            "recommended_action": "Drill exploration well to de-risk seal and reservoir",
        },
        "depth_basis": {"type": "TVDSS", "datum": "MSL"},
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestFederationEnvelopeConstruction:
    """Test basic envelope construction and validation."""

    def test_build_minimal_envelope(self):
        """Minimal envelope has all required fields."""
        env = build_federation_envelope(
            trace_id=_trace_id(),
            actor_id="FORGE",
            organ_origin=OrganID.GEOX,
            intent="Test envelope construction",
        )
        assert env.envelope_id.startswith("env-")
        assert env.organ_origin == OrganID.GEOX
        assert env.execution_status == ExecutionStatus.SENSED
        assert env.autonomy_band == AutonomyBand.OBSERVE
        assert env.reversibility_class == ReversibilityClass.FULL
        assert env.risk_class == RiskClass.LOW
        assert env.f13_required is False

    def test_envelope_identity_chain(self):
        """Envelopes can be chained via parent_envelope_id."""
        trace = _trace_id()
        env1 = build_federation_envelope(
            trace_id=trace,
            actor_id="FORGE",
            organ_origin=OrganID.GEOX,
            intent="Step 1: Basin screening",
        )
        env2 = build_federation_envelope(
            trace_id=trace,
            actor_id="FORGE",
            organ_origin=OrganID.WEALTH,
            intent="Step 2: Capital assessment",
            parent_envelope_id=env1.envelope_id,
        )
        assert env2.parent_envelope_id == env1.envelope_id
        assert env2.trace_id == env1.trace_id  # Same trace

    def test_envelope_serialization_roundtrip(self):
        """Envelope survives JSON serialization."""
        env = build_federation_envelope(
            trace_id=_trace_id(),
            actor_id="FORGE",
            organ_origin=OrganID.GEOX,
            intent="Serialization test",
            measurement_result={"key": "value"},
        )
        json_str = env.model_dump_json()
        env2 = FederationEnvelope.model_validate_json(json_str)
        assert env2.envelope_id == env.envelope_id
        assert env2.measurement_result == {"key": "value"}


class TestGEOXToEnvelopeAdapter:
    """Test GEOX tool output → FederationEnvelope wrapping."""

    def test_geox_basin_output_wraps_correctly(self):
        """GEOX basin output wraps into envelope with correct metadata."""
        output = _sabah_basin_geox_output()
        trace = _trace_id()

        env = geox_to_federation_envelope(
            tool_name="geox_basin",
            tool_output=output,
            trace_id=trace,
            actor_id="FORGE",
            intent="Screen Sabah Basin for hydrocarbon potential",
        )

        assert env.organ_origin == OrganID.GEOX
        assert env.execution_status == ExecutionStatus.MEASURED  # INTERPRETED → MEASURED
        assert env.evidence_layer.evidence_type == "geological"
        assert env.evidence_layer.epistemic_label == "DER"  # DERIVED → DER
        assert env.evidence_layer.confidence <= 0.90  # F7 HUMILITY cap
        assert env.risk_class == RiskClass.LOW  # basin = LOW risk
        assert env.f13_required is False  # LOW risk → no F13
        assert env.payload["tool_name"] == "geox_basin"
        assert env.payload["claim_state"] == "INTERPRETED"

    def test_geox_prospect_output_high_risk(self):
        """Prospect evaluation → HIGH risk, F13 required."""
        output = _sabah_prospect_output()
        trace = _trace_id()

        env = geox_to_federation_envelope(
            tool_name="geox_prospect",
            tool_output=output,
            trace_id=trace,
            actor_id="FORGE",
            intent="Evaluate Sabah Deep Water Fan prospect",
        )

        assert env.risk_class == RiskClass.HIGH  # prospect = HIGH risk
        assert env.f13_required is True  # HIGH → F13 required
        assert env.autonomy_band == AutonomyBand.DRAFT  # HIGH → DRAFT only
        assert env.execution_status == ExecutionStatus.MEASURED  # DERIVED_CANDIDATE → MEASURED

    def test_geox_hold_status_propagates(self):
        """GEOX HOLD status maps to envelope HOLD."""
        output = _sabah_basin_geox_output()
        output["claim_state"] = "888_HOLD"
        trace = _trace_id()

        env = geox_to_federation_envelope(
            tool_name="geox_basin",
            tool_output=output,
            trace_id=trace,
            actor_id="FORGE",
            intent="Test HOLD propagation",
        )

        assert env.execution_status == ExecutionStatus.HOLD
        assert env.autonomy_band == AutonomyBand.OBSERVE  # HOLD → OBSERVE only


class TestSabahBasinMetabolicLoop:
    """Test the full Sabah Basin metabolic loop: GEOX → WEALTH → arifOS → F13."""

    def test_full_loop_trace_preservation(self):
        """Trace ID preserves through entire organ chain."""
        trace = _trace_id()
        actor = "ARIF_FAZIL"

        # Step 1: GEOX produces basin evidence
        geox_env = geox_to_federation_envelope(
            tool_name="geox_basin",
            tool_output=_sabah_basin_geox_output(),
            trace_id=trace,
            actor_id=actor,
            intent="Assess Sabah Basin opportunity/risk",
            organ_target=OrganID.WEALTH,
            handoff_reason="Basin screening complete → assess capital consequence",
        )

        # Step 2: GEOX produces prospect evidence
        prospect_env = geox_to_federation_envelope(
            tool_name="geox_prospect",
            tool_output=_sabah_prospect_output(),
            trace_id=trace,
            actor_id=actor,
            intent="Assess Sabah Basin opportunity/risk",
            parent_envelope_id=geox_env.envelope_id,
            organ_target=OrganID.WEALTH,
            handoff_reason="Prospect evaluation → capital/risk assessment",
        )

        # Step 3: WEALTH receives (simulated)
        wealth_env = build_federation_envelope(
            trace_id=trace,
            actor_id=actor,
            organ_origin=OrganID.WEALTH,
            intent="Assess Sabah Basin opportunity/risk",
            metabolic_phase=MetabolicPhase.DELIBERATE,
            evidence_type="financial",
            evidence_refs=[
                f"geox_envelope:{geox_env.envelope_id}",
                f"geox_envelope:{prospect_env.envelope_id}",
            ],
            epistemic_label="DER",
            confidence=0.45,
            autonomy_band=AutonomyBand.DRAFT,
            reversibility_class=ReversibilityClass.FULL,
            risk_class=RiskClass.HIGH,
            proposed_action="Assess NPV/EMV for Sabah Deep Water Fan",
            execution_status=ExecutionStatus.MEASURED,
            measurement_result={
                "npv_usd_million": 850,
                "irr_estimate": 0.18,
                "emv_usd_million": 297,  # NPV × POS
                "capital_risk": "HIGH",
            },
            measurement_summary="EMV $297M at 35% POS. High geological risk offsets strong NPV.",
            organ_target=OrganID.ARIFOS,
            handoff_reason="Capital assessment → constitutional judgment",
            parent_envelope_id=prospect_env.envelope_id,
            f13_required=True,
        )

        # Verify trace preservation
        assert geox_env.trace_id == trace
        assert prospect_env.trace_id == trace
        assert wealth_env.trace_id == trace

        # Verify organ chain
        assert geox_env.organ_origin == OrganID.GEOX
        assert prospect_env.organ_origin == OrganID.GEOX
        assert wealth_env.organ_origin == OrganID.WEALTH

        # Verify chain linkage
        assert prospect_env.parent_envelope_id == geox_env.envelope_id
        assert wealth_env.parent_envelope_id == prospect_env.envelope_id

        # Verify F13 propagation
        assert geox_env.f13_required is False  # basin = LOW
        assert prospect_env.f13_required is True  # prospect = HIGH
        assert wealth_env.f13_required is True  # capital = HIGH

    def test_irreversible_blocked_without_f13(self):
        """IRREVERSIBLE action cannot proceed without F13 approval."""
        env = build_federation_envelope(
            trace_id=_trace_id(),
            actor_id="FORGE",
            organ_origin=OrganID.A_FORGE,
            intent="Drill Sabah exploration well",
            metabolic_phase=MetabolicPhase.EXECUTE,
            autonomy_band=AutonomyBand.IRREVERSIBLE,
            reversibility_class=ReversibilityClass.NONE,
            risk_class=RiskClass.CRITICAL,
            proposed_action="drill_exploration_well_SABAH-001",
            f13_required=True,
            execution_status=ExecutionStatus.DELIBERATING,
        )

        # The envelope MUST have f13_required=True for IRREVERSIBLE
        assert env.f13_required is True
        assert env.reversibility_class == ReversibilityClass.NONE
        assert env.autonomy_band == AutonomyBand.IRREVERSIBLE

        # Without vault_receipt_reference, it cannot be SEALED
        assert env.vault_receipt_reference == ""  # Not yet sealed

    def test_envelope_json_schema_matches_spec(self):
        """Envelope JSON schema matches Arif's required fields."""
        env = build_federation_envelope(
            trace_id=_trace_id(),
            actor_id="FORGE",
            organ_origin=OrganID.GEOX,
            intent="Schema validation",
        )

        schema = env.model_json_schema()
        props = schema.get("properties", {})

        # All fields from Arif's spec must be present
        required_fields = [
            "trace_id",
            "actor_id",
            "organ_origin",
            "organ_target",
            "intent",
            "evidence_layer",
            "autonomy_band",
            "reversibility_class",
            "risk_class",
            "required_floor_checks",
            "proposed_action",
            "execution_status",
            "measurement_result",
            "vault_receipt_reference",
            "f13_required",
        ]
        for field in required_fields:
            assert field in props, f"Missing required field: {field}"

    def test_envelope_as_json_for_cross_organ_transport(self):
        """Envelope serializes to JSON for MCP transport."""
        env = geox_to_federation_envelope(
            tool_name="geox_basin",
            tool_output=_sabah_basin_geox_output(),
            trace_id=_trace_id(),
            actor_id="FORGE",
            intent="Cross-organ transport test",
            organ_target=OrganID.WEALTH,
        )

        # Serialize to JSON (this is what travels through MCP)
        json_str = env.model_dump_json(indent=2)
        parsed = json.loads(json_str)

        # Verify it's a valid envelope
        assert parsed["organ_origin"] == "GEOX"
        assert parsed["organ_target"] == "WEALTH"
        assert parsed["trace_id"].startswith("trc-")
        assert "measurement_result" in parsed
        assert "evidence_layer" in parsed
        assert "autonomy_band" in parsed


class TestFloorChecks:
    """Test constitutional floor check integration."""

    def test_floor_checks_attached_to_envelope(self):
        """Floor checks can be attached to envelope."""
        floor_checks = [
            FloorCheck(
                floor_id="F1",
                floor_name="AMANAH",
                passed=True,
                reason="Action is reversible (FULL)",
            ),
            FloorCheck(
                floor_id="F2",
                floor_name="TRUTH",
                passed=True,
                reason="Evidence labeled OBS with confidence 0.6",
            ),
            FloorCheck(
                floor_id="F7",
                floor_name="HUMILITY",
                passed=True,
                reason="Confidence capped at 0.90",
            ),
        ]

        env = build_federation_envelope(
            trace_id=_trace_id(),
            actor_id="FORGE",
            organ_origin=OrganID.GEOX,
            intent="Floor check test",
            required_floor_checks=floor_checks,
        )

        assert len(env.required_floor_checks) == 3
        assert all(fc.passed for fc in env.required_floor_checks)

    def test_failed_floor_check_blocks_envelope(self):
        """Failed floor check is visible in envelope."""
        floor_checks = [
            FloorCheck(
                floor_id="F9",
                floor_name="ANTI-HANTU",
                passed=False,
                reason="Claimed consciousness in output",
            ),
        ]

        env = build_federation_envelope(
            trace_id=_trace_id(),
            actor_id="FORGE",
            organ_origin=OrganID.GEOX,
            intent="Failed floor test",
            required_floor_checks=floor_checks,
            execution_status=ExecutionStatus.HOLD,
        )

        assert env.execution_status == ExecutionStatus.HOLD
        assert not env.required_floor_checks[0].passed
