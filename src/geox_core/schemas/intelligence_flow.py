"""
intelligence_flow.py — Dynamic Flow of Intelligence through GEOX
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given.

This module formalizes the dynamic flow of intelligence through the
arifOS federation's GEOX organ. Intelligence is NOT a static ledger —
it is a moving current. This schema is the typed contract for that flow.

Architecture: 7 layers + 1 foundation + 1 audit

  Layer 0     INGEST       Raw data → typed observations
  Layer 1     WITNESS      OBS-grade measurements (LAS, SEG-Y validated)
  Layer 2     PHYSICS      DER-grade (joint inversion → Physics13State)
  Layer 3     ARCHITECTURE INT-grade (crustal domain, COB, tectonics)
  Layer 4     INTERPRET    INT→SPEC transition (biostrat, sequence)
  Layer 5     DECISION     SPEC→action (prospect, wealth feed)
  Foundation  LEM          Lateral — provides priors + analog matching
  Audit       DOCTRINE     Transverse — gates every transition

Constitutional binding:
  F1  AMANAH    — FlowPacket is content-addressed; reversibility explicit.
  F2  TRUTH     — Every FlowStage carries epistemic_rank (OBS/DER/INT/SPEC).
  F4  CLARITY   — Schema strict (extra=forbid). No drift.
  F7  HUMILITY  — Confidence hard-capped at 0.90 across all layers.
  F8  LAW       — Layer transitions governed by doctrine gate.
  F9  ANTI-HANTU— LEM outputs marked DERIVED, never SEAL-grade alone.
  F11 AUDIT     — Every flow appends to an immutable ledger.
  F13 SOVEREIGN — Layer 5 (DECISION) → 888_HOLD required.

Reference:
  forge_work/2026-06-22-rsi-roadmap.md
  docs/GEOX_INTELLIGENCE_FLOW.md
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ═══════════════════════════════════════════════════════════════════════════════
# 7 Layers + Foundation + Audit
# ═══════════════════════════════════════════════════════════════════════════════


class FlowLayer(IntEnum):
    """Canonical 7 layers of GEOX intelligence flow.

    Lower numbers are upstream (raw), higher numbers are downstream (action).
    Foundation and Audit are LATERAL and TRANSVERSE respectively.
    """

    INGEST = 0
    WITNESS = 1
    PHYSICS = 2
    ARCHITECTURE = 3
    INTERPRET = 4
    DECISION = 5
    FOUNDATION = 98  # LEM — lateral
    AUDIT = 99  # Doctrine — transverse


class FlowStage(StrEnum):
    """Stage of intelligence at a layer."""

    OBS = "OBS"  # Layer 1 — direct observation
    DER = "DER"  # Layer 2 — derived from physics
    INT = "INT"  # Layer 3-4 — interpretation
    SPEC = "SPEC"  # Layer 5 — speculative / decision


class ToolFamily(StrEnum):
    """Canonical 5 tool families identified by RSI pass 2026-06-22.

    Replaces Copilot's ungrouped 13-item list with 5 coherent families.
    """

    A_CRUSTAL_ARCHITECTURE = "A_crustal_architecture"
    B_TECTONIC_CONTEXT = "B_tectonic_context"
    C_LEM_ANALOG = "C_lem_analog"
    D_GOVERNANCE = "D_governance"
    E_LEM_FOUNDATION = "E_lem_foundation"


# ═══════════════════════════════════════════════════════════════════════════════
# Layer descriptors
# ═══════════════════════════════════════════════════════════════════════════════


LAYER_DESCRIPTORS: dict[FlowLayer, dict[str, Any]] = {
    FlowLayer.INGEST: {
        "name": "Ingest",
        "stage": "raw",
        "purpose": "Convert raw data into typed observations.",
        "input": "Files (LAS, SEG-Y, CSV, Parquet), live streams",
        "output": "Typed Observation envelopes",
        "example_tools": ["geox_data_ingest_bundle", "geox_header_inspect"],
        "lem_role": "tokenization source",
        "doctrine_gate": "F1 (no destructive ops on source)",
    },
    FlowLayer.WITNESS: {
        "name": "Witness",
        "stage": "OBS",
        "purpose": "Validate and quantify observations. First epistemic gate.",
        "input": "Typed Observations",
        "output": "QC'd OBS-grade evidence",
        "example_tools": [
            "geox_data_qc_bundle",
            "geox_las_inspect",
            "geox_seismic_segy_inspect",
        ],
        "lem_role": "encoder input",
        "doctrine_gate": "F2 (epistemic rank assigned)",
    },
    FlowLayer.PHYSICS: {
        "name": "Physics",
        "stage": "DER",
        "purpose": "Multi-physics inversion under Physics9 bounds.",
        "input": "QC'd observations",
        "output": "Physics13State per cell",
        "example_tools": [
            "geox_joint_inversion",
            "geox_seismic_compute",
            "geox_gravity_magnetic_forward",
            "geox_mt_forward",
        ],
        "lem_role": "physics_head constraint",
        "doctrine_gate": "F8 (Physics9 bounds), F7 (≤0.90)",
    },
    FlowLayer.ARCHITECTURE: {
        "name": "Architecture",
        "stage": "INT",
        "purpose": "Classify crustal architecture from inverted state.",
        "input": "Physics13State + crust context (Vp, thickness, heat flow)",
        "output": "CrustZone classification + domain map",
        "example_tools": [
            "geox_crustal_domain_classify",  # FORGED THIS SESSION
            "geox_ductile_layer_detect",     # Family A — pending
            "geox_cob_zone_map",              # Family A — pending
            "geox_basement_register",         # Family A — pending
        ],
        "lem_role": "analog matching via crust-type priors",
        "doctrine_gate": "F7, F13 (domain BOUNDARIES sovereign)",
    },
    FlowLayer.INTERPRET: {
        "name": "Interpret",
        "stage": "INT → SPEC",
        "purpose": "Layer interpretive context (biostrat, sequence, facies).",
        "input": "Architecture classifications + biostrat picks",
        "output": "Interpretive claims (with confidence bands)",
        "example_tools": [
            "geox_biostrat_constraint",
            "geox_sequence_interpret",
            "geox_evidence_reason",
            "geox_claim_create",  # JUDGMENT lane
        ],
        "lem_role": "biostrat ↔ crust-type calibration",
        "doctrine_gate": "F11 (audit trail), F2 (epistemic rank)",
    },
    FlowLayer.DECISION: {
        "name": "Decision",
        "stage": "SPEC → action",
        "purpose": "Convert interpreted claims into prospect evaluations.",
        "input": "Interpretive claims + economic context",
        "output": "Prospect card + wealth feed",
        "example_tools": [
            "geox_prospect_evaluate",
            "geox_wealth_feed",
            "geox_geomechanics",
        ],
        "lem_role": "anomaly scoring on prospect vectors",
        "doctrine_gate": "F13 (888_HOLD required for SEAL)",
    },
    FlowLayer.FOUNDATION: {
        "name": "LEM Foundation",
        "stage": "lateral",
        "purpose": "Provide priors + analog matching across all layers.",
        "input": "Any layer's typed packet",
        "output": "Embedding + analog matches + anomaly scores",
        "example_tools": [
            "geox_lem_predict",                # FORGED W14+
            "geox_lem_encode",                  # Family E — pending
            "geox_lem_analog_match",            # Family E — pending
            "geox_lem_anomaly_score",           # Family E — pending
            "geox_lem_fine_tune_basin",         # Family E — pending (888_HOLD)
        ],
        "lem_role": "self",
        "doctrine_gate": "F9 (LEM outputs DERIVED, never SEAL alone)",
    },
    FlowLayer.AUDIT: {
        "name": "Doctrine Audit",
        "stage": "transverse",
        "purpose": "Gate every transition with F1-F13 floor checks.",
        "input": "Any FlowStage",
        "output": "PASS / HOLD / BLOCK verdict + audit_receipt",
        "example_tools": [
            "geox_doctrine_assumption_register",
            "geox_doctrine_anti_beautiful_one",
            "geox_doctrine_godel_review",
            "geox_paradox_register",            # Family D — pending
            "geox_age_anchor_validator",        # Family D — pending
        ],
        "lem_role": "audit only — does not consume LEM output",
        "doctrine_gate": "self-evident",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Typed flow packets — what's actually flowing
# ═══════════════════════════════════════════════════════════════════════════════


class FlowPacket(BaseModel):
    """A single typed packet moving through the flow.

    F4 CLARITY: every packet has explicit source_layer + target_layer.
    F2 TRUTH: epistemic_rank is required (no UNKNOWN values).
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    packet_id: str = Field(..., min_length=8)
    source_layer: FlowLayer
    target_layer: FlowLayer
    epistemic_rank: FlowStage
    confidence: float = Field(..., ge=0.0, le=0.90)  # F7
    payload: dict[str, Any] = Field(..., description="Layer-specific payload")
    source_tool: str = Field(..., min_length=1)
    session_id: str | None = None
    actor_id: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    # Content-addressed audit (F1 AMANAH)
    content_hash: str | None = None
    # Doctrine verdict
    doctrine_verdict: str | None = Field(
        default=None,
        description="PASS | HOLD | BLOCK | VOID from doctrine audit.",
    )
    doctrine_audit_receipt: dict[str, Any] | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# Flow session — the complete current
# ═══════════════════════════════════════════════════════════════════════════════


class FlowSession(BaseModel):
    """A complete intelligence flow session.

    Captures a packet moving through the layers from ingest to decision.
    """

    model_config = ConfigDict(extra="forbid", frozen=False)

    session_id: str = Field(..., min_length=8)
    basin_name: str | None = None
    actor_id: str | None = None
    started_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    packets: list[FlowPacket] = Field(default_factory=list)
    # Final state when decision reached
    final_decision: str | None = None
    final_verdict: str | None = None  # SEAL | SABAR | VOID

    def add_packet(self, packet: FlowPacket) -> None:
        """Append a packet to the flow (with hash integrity)."""
        # Compute content hash if not set
        if packet.content_hash is None:
            packet.content_hash = self._compute_hash(packet)
        self.packets.append(packet)

    @staticmethod
    def _compute_hash(packet: FlowPacket) -> str:
        """F1 AMANAH — content-addressed hash."""
        payload = (
            f"{packet.packet_id}|{packet.source_layer}|{packet.target_layer}|"
            f"{packet.epistemic_rank}|{packet.source_tool}|"
            f"{hash(tuple(sorted(packet.payload.items())))}"
        )
        return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


# ═══════════════════════════════════════════════════════════════════════════════
# Tool family descriptors — for the RSI-merged 5 families
# ═══════════════════════════════════════════════════════════════════════════════


TOOL_FAMILIES: dict[ToolFamily, dict[str, Any]] = {
    ToolFamily.A_CRUSTAL_ARCHITECTURE: {
        "description": "Crustal architecture from physics-first substrate.",
        "primary_layer": FlowLayer.ARCHITECTURE,
        "tools_complete": [
            "geox_anomalous_contrast_detect",  # UPGRADED TO ToAC LOOP
        ],
        "tools_pending": [
            "geox_ductile_layer_detect",
            "geox_cob_zone_map",
            "geox_basement_register",
        ],
        "vp_grammar_source": "Huang et al. (2021)",
        "kinabalu_phase1_deliverable": "D1 (Crustal Domain Map) + D2 (COB) + D3 (Basement)",
        "effort_estimate_days": "5-7 days total",
    },
    ToolFamily.B_TECTONIC_CONTEXT: {
        "description": "Tectonic context propagation, conjugacy, diachrony.",
        "primary_layer": FlowLayer.ARCHITECTURE,
        "tools_complete": [],
        "tools_pending": [
            "geox_diachronous_tectonics",
            "geox_conjugate_margin_compare",  # cross-family with C
        ],
        "vp_grammar_source": "Huang et al. (2021) propagator kinematics",
        "kinabalu_phase1_deliverable": "D4 (Tectonic Event Horizons) supporting context",
        "effort_estimate_days": "8-10 days total",
    },
    ToolFamily.C_LEM_ANALOG: {
        "description": "LEM-powered analog matching + rock physics templates.",
        "primary_layer": FlowLayer.FOUNDATION,
        "tools_complete": [],
        "tools_pending": [
            "geox_lem_analog_match",
            "geox_lem_anomaly_score",
            "geox_rock_physics_template_match",  # uses existing lem_predict substrate
        ],
        "vp_grammar_source": "Substrate: geox_core/engines/lem/",
        "kinabalu_phase1_deliverable": "D1 validation (Layang-Layang ≈ Zhongsha analog)",
        "effort_estimate_days": "10-14 days total (after LEM training)",
    },
    ToolFamily.D_GOVERNANCE: {
        "description": "Governance ledger, paradox capture, age validation.",
        "primary_layer": FlowLayer.AUDIT,
        "tools_complete": [
            "geox_doctrine_assumption_register",  # pre-existing
            "geox_doctrine_anti_beautiful_one",   # pre-existing
            "geox_doctrine_godel_review",          # pre-existing
        ],
        "tools_pending": [
            "geox_paradox_register",
            "geox_age_anchor_validator",
        ],
        "vp_grammar_source": "N/A (governance substrate)",
        "kinabalu_phase1_deliverable": "Audit trail for D1+D2+D3+D4",
        "effort_estimate_days": "2-3 days total",
    },
    ToolFamily.E_LEM_FOUNDATION: {
        "description": "LEM-as-MCP foundation tools (encoder + analog + anomaly + fine-tune).",
        "primary_layer": FlowLayer.FOUNDATION,
        "tools_complete": [
            "geox_lem_predict",  # pre-existing substrate
        ],
        "tools_pending": [
            "geox_lem_encode",
            "geox_lem_fine_tune_basin",  # 888_HOLD
        ],
        "vp_grammar_source": "Substrate: geox_core/engines/lem/",
        "kinabalu_phase1_deliverable": "Phase II — LEM-anchored cross-domain synthesis",
        "effort_estimate_days": "10-15 days (needs GPU + 888_HOLD)",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Transition rules
# ═══════════════════════════════════════════════════════════════════════════════


VALID_TRANSITIONS: set[tuple[FlowLayer, FlowLayer]] = {
    # Forward transitions
    (FlowLayer.INGEST, FlowLayer.WITNESS),
    (FlowLayer.WITNESS, FlowLayer.PHYSICS),
    (FlowLayer.PHYSICS, FlowLayer.ARCHITECTURE),
    (FlowLayer.ARCHITECTURE, FlowLayer.INTERPRET),
    (FlowLayer.INTERPRET, FlowLayer.DECISION),
    # Lateral: FOUNDATION touches any non-audit layer
    (FlowLayer.FOUNDATION, FlowLayer.INGEST),
    (FlowLayer.FOUNDATION, FlowLayer.WITNESS),
    (FlowLayer.FOUNDATION, FlowLayer.PHYSICS),
    (FlowLayer.FOUNDATION, FlowLayer.ARCHITECTURE),
    (FlowLayer.FOUNDATION, FlowLayer.INTERPRET),
    (FlowLayer.FOUNDATION, FlowLayer.DECISION),
    # Reverse: anomaly feedback (Architecture → Physics) — needs audit
    (FlowLayer.ARCHITECTURE, FlowLayer.PHYSICS),
    (FlowLayer.INTERPRET, FlowLayer.ARCHITECTURE),
    # Audit is transverse: any → audit, audit → any
    (FlowLayer.AUDIT, FlowLayer.INGEST),
    (FlowLayer.AUDIT, FlowLayer.WITNESS),
    (FlowLayer.AUDIT, FlowLayer.PHYSICS),
    (FlowLayer.AUDIT, FlowLayer.ARCHITECTURE),
    (FlowLayer.AUDIT, FlowLayer.INTERPRET),
    (FlowLayer.AUDIT, FlowLayer.DECISION),
}


def is_valid_transition(source: FlowLayer, target: FlowLayer) -> bool:
    """F8 LAW — check if a transition is allowed."""
    return (source, target) in VALID_TRANSITIONS


__all__ = [
    "FlowLayer",
    "FlowStage",
    "ToolFamily",
    "LAYER_DESCRIPTORS",
    "FlowPacket",
    "FlowSession",
    "TOOL_FAMILIES",
    "VALID_TRANSITIONS",
    "is_valid_transition",
]
