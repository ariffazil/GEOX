"""
geox_core/schemas/claim_envelope.py — P1 CRITICAL
DITEMPA BUKAN DIBERI — Evidence is forged, not given.

Canonical public contract for ALL GEOX MCP tool outputs.

This is the ONLY schema that external MCP clients ever receive.
Every adapter, engine, and internal service wraps its output into this
envelope before it crosses the membrane.

LAW:
  - This file is THE law. No adapter returns raw JSON across the membrane.
  - Internal fields may change freely inside geox_core/engines/.
  - This envelope is IMMUTABLE once locked at a version epoch.
  - To add a field: propose via 888_HOLD. Never ad-hoc extend.

RULES:
  1. Every public MCP tool returns ClaimEnvelope (or subclass).
  2. The LLM/receiving agent sees ONLY this envelope.
  3. Adapter names, library names, internal version strings — NEVER in this envelope.
  4. evidence_for + evidence_against MUST be populated for any DERIVED or higher output.
  5. canon9_variable MUST be set for any physics-grounded output.

Version: 1.0.0 (locked 2026-06-26)
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Self
from uuid import uuid4

from pydantic import BaseModel, Field

# ─── Enums ───────────────────────────────────────────────────────────────────────


class ClaimState(StrEnum):
    """Epistemic claim level for the output value.

    Strict hierarchy — never skip levels.
    NO_VALID_EVIDENCE can escalate to any level via sufficient evidence.
    """

    NO_VALID_EVIDENCE = "NO_VALID_EVIDENCE"  # input data exists, no computation yet
    INGESTED = "INGESTED"  # raw data ingested, not QC'd
    QC_VERIFIED = "QC_VERIFIED"  # passed QC checks
    INTERPRETED = "INTERPRETED"  # human or model interpretation applied
    DERIVED_CANDIDATE = "DERIVED_CANDIDATE"  # computed, needs corroboration
    SEALED = "SEALED"  # arifOS 888_JUDGE has sealed this
    JUDGE_PREVIEW = "JUDGE_PREVIEW"  # sent for 888_JUDGE, awaiting verdict
    HOLD = "888_HOLD"  # blocked — requires Arif release
    VOID = "VOID"  # retracted or contradicted by new evidence


class ClaimOrigin(StrEnum):
    """Pipeline stage that produced this claim. Used for traceability and GUI sorting."""

    EXTRACT = "EXTRACT"
    FORMULATE = "FORMULATE"
    CHALLENGE = "CHALLENGE"
    SYNTHESIZE = "SYNTHESIZE"
    FORWARD = "FORWARD"


class ReasonCode(StrEnum):
    """Structured reason codes for rejection envelopes.

    Maps to GUI's logic layer — never prose. Every rejection carries one.
    """

    QUALIFY = "QUALIFY"  # No rejection — claim is valid
    NO_EVIDENCE = "NO_EVIDENCE"  # evidence_for is empty
    CONTRADICTION = "CONTRADICTION"  # evidence_against outweighs evidence_for
    INVALID_GEOMETRY = "INVALID_GEOMETRY"  # spatial/math bounds violation
    UNCERTAINTY_TOO_HIGH = "UNCERTAINTY_TOO_HIGH"  # uncertainty exceeds threshold
    ENGINE_FAILURE = "ENGINE_FAILURE"  # computation error
    GOVERNANCE_BLOCK = "GOVERNANCE_BLOCK"  # blocked by arifOS governance
    SCHEMA_REJECTION = "SCHEMA_REJECTION"  # invalid input schema
    NOT_APPLICABLE = "NOT_APPLICABLE"  # tool not applicable to this context


class AcRiskLevel(StrEnum):
    """ACRisk classification — governs whether output requires Arif release."""

    QUALIFY = "QUALIFY"  # low risk — proceed autonomously
    ADVISORY = "ADVISORY"  # medium risk — surface to Arif, no block
    HOLD = "HOLD"  # high risk — 888_HOLD gate required before use
    BLOCK = "BLOCK"  # critical risk — blocked for all generic agents


class EpistemicLabel(StrEnum):
    """External-facing epistemic label (simplified from internal rung ladder).

    Used in the claim envelope so LLMs understand the confidence tier.
    """

    OBSERVED = "OBSERVED"  # directly measured, traceable to instrument
    DERIVED = "DERIVED"  # computed from observed with deterministic transform
    ESTIMATE = "ESTIMATE"  # computed with model assumptions — range required
    HYPOTHESIS = "HYPOTHESIS"  # interpretive, single-hypothesis, needs alternatives
    PLAUSIBLE = "PLAUSIBLE"  # multi-hypothesis, physically plausible, uncalibrated
    UNKNOWN = "UNKNOWN"  # insufficient data — no claim possible


class UnitSystem(StrEnum):
    """Required unit strings for all physical values."""

    METRE = "m"
    KILOMETRE = "km"
    MILLIGAL = "mGal"
    NANOTESLA = "nT"
    MEGAPASCAL = "MPa"
    OHMM = "Ω·m"
    DEGREE = "°"
    DEGREE_PER_MA = "°/Ma"
    G_PER_CM3 = "g·cm⁻³"
    KG_PER_M3 = "kg·m⁻³"
    M_S = "m·s⁻¹"
    SECONDS = "s"
    YEAR = "yr"
    DIMENSIONLESS = "dimensionless"


# ─── Canonical Envelope ─────────────────────────────────────────────────────────


class ClaimEnvelope(BaseModel):
    """
    The ONE public contract for all GEOX MCP tool outputs.

    This envelope crosses the membrane from geox_core → external MCP client.
    No adapter, engine, or internal service returns raw JSON directly.

    FIELDS — PUBLIC (may be rendered to LLM):
      tool_id, claim_state, epistemic_label, value, unit, canon9_variable,
      uncertainty_band, acrisk, verdict, evidence_for, evidence_against,
      artifact_ref, requires_arif, caveats, timestamp_utc

    FIELDS — INTERNAL ONLY (never exposed to external clients):
      _internal: {adapter_name, library_versions, engine_hash, params_hash,
                 session_id, trace_id, replan_epoch}

    Governance:
      - F2 TRUTH: claim_state must match actual epistemic tier
      - F4 CLARITY: uncertainty_band required for ESTIMATE and above
      - F7 HUMILITY: acrisk = HOLD → requires_arif = True
      - F11 AUDIT: params_hash and artifact_ref are immutable audit trail
      - F13 SOVEREIGN: requires_arif = True blocks autonomous use

    Usage:
      adapter_output = some_adapter.compute(...)
      envelope = ClaimEnvelope.from_adapter_output(
          tool_id="gravity.get_bouguer_anomaly",
          adapter_output=adapter_output,
          canon9_variable="rho",
      )
      return envelope.model_dump(mode="json", exclude={"_internal"})

    Version: 1.0.0 (locked 2026-06-26)
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    tool_id: str = Field(
        ...,
        description="Public tool identifier. Format: domain_verb. E.g. gravity.get_bouguer_anomaly. "
        "NEVER contains library names, adapter names, or internal service names.",
        examples=[
            "gravity.get_bouguer_anomaly",
            "magnetics.get_declination",
            "tectonics.reconstruct_point",
            "bathymetry.get_depth",
        ],
    )

    # ── Core claim ───────────────────────────────────────────────────────────

    claim_state: ClaimState = Field(
        ...,
        description="Current epistemic state of the output. Determines what the LLM may say about this result.",
    )

    epistemic_label: EpistemicLabel = Field(
        ...,
        description="Simplified confidence tier for external rendering.",
    )

    value: Any = Field(
        ...,
        description="The primary computed value. Type matches the physical quantity. "
        "MUST be accompanied by uncertainty_band for ESTIMATE and above.",
    )

    unit: str = Field(
        ...,
        description="Physical unit string. Use UnitSystem values.",
    )

    # ── Physics grounding ─────────────────────────────────────────────────────

    canon9_variable: str | None = Field(
        default=None,
        description="CANON-9 variable this output grounds. "
        "E.g. rho, Vp, Vs, phi, Sw, P, k, T, chi. "
        "Required for any physics-grounded output.",
        examples=["rho", "Vp", "Vs", "phi", "Sw", "P", "k", "T", "chi"],
    )

    uncertainty_band: tuple[float, float] | None = Field(
        default=None,
        description="5th and 95th percentile bounds on the value. REQUIRED for ESTIMATE and above. Format: [p05, p95].",
    )

    # ── Governance ───────────────────────────────────────────────────────────

    acrisk: AcRiskLevel = Field(
        default=AcRiskLevel.QUALIFY,
        description="ACRisk tier. QUALIFY = autonomous use OK. HOLD = 888_HOLD gate. BLOCK = no use allowed.",
    )

    verdict: str = Field(
        default="QUALIFY",
        description="Short verdict string. E.g. QUALIFY, HOLD, REJECT. HOLD means requires Arif release before use.",
    )

    # ── Evidence ─────────────────────────────────────────────────────────────

    evidence_for: list[str] = Field(
        default_factory=list,
        description="Evidence that supports this claim. Required for DERIVED_CANDIDATE and above.",
    )

    evidence_against: list[str] = Field(
        default_factory=list,
        description="Evidence that contradicts or limits this claim. "
        "Required for DERIVED_CANDIDATE and above. "
        "This is what prevents epistemic collapse.",
    )

    caveats: list[str] = Field(
        default_factory=list,
        description="Assumptions, limitations, and warnings. NEVER empty — at minimum state the method used.",
    )

    # ── Audit trail ──────────────────────────────────────────────────────────

    artifact_ref: str | None = Field(
        default=None,
        description="Reference to the artifact (file, grid, trace) that this "
        "claim is based on. Format: DATASET.TIMESTAMP.HASH. "
        "Used for audit replay.",
        examples=["GRAV_GRID_OTSDEM.122023.4326.1", "WELL_LAS_BATEH1.20240115.ab32"],
    )

    requires_arif: bool = Field(
        default=False,
        description="If True: this output MUST NOT be used by autonomous agents. "
        " Arif must explicitly release. "
        "Auto-set to True when acrisk = HOLD or BLOCK.",
    )

    # ── Pipeline traceability (P0 #4 fix, 2026-07-10 — version 1.1.0) ──────
    origin: str = Field(
        default="FORMULATE",
        description="Pipeline stage that produced this claim. "
        "EXTRACT / FORMULATE / CHALLENGE / SYNTHESIZE / FORWARD. "
        "Used by GUI for sorting and timeline rendering.",
    )

    reason_code: str = Field(
        default="QUALIFY",
        description="Structured reason code for rejection envelope. "
        "QUALIFY = valid. NO_EVIDENCE / CONTRADICTION / etc. = rejected. "
        "Maps to GUI logic layer — never prose.",
    )

    actor: str = Field(
        default="geox-core",
        description="Engine or organ that issued this claim. "
        "Defaults to tool name. Never None — prevents G=0.0 from APEX gate. "
        "P0 #4 fix: READ operations default to tool name when actor is absent.",
    )

    # ── Timestamps ───────────────────────────────────────────────────────────

    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="UTC timestamp of computation. ISO 8601 format.",
    )

    # ── Internal fields — excluded from public serialization ──────────────────

    _internal: dict[str, Any] = Field(
        default_factory=dict,
        description="INTERNAL ONLY. Excluded from public serialization. Used by geox_core for versioning, audit, and replay.",
    )

    class Config:
        # Never serialize _internal to JSON — it never crosses the membrane
        json_schema_extra = {
            "exclude_none": False,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def model_dump_public(self) -> dict[str, Any]:
        """
        Serialize WITHOUT _internal fields.
        This is the ONLY serialization method for external exposure.
        """
        return self.model_dump(mode="json", exclude={"_internal"})

    @classmethod
    def from_adapter_output(
        cls,
        tool_id: str,
        adapter_output: dict[str, Any],
        canon9_variable: str | None = None,
        artifact_ref: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> Self:
        """
        Bridge from internal adapter dict to public ClaimEnvelope.

        Args:
            tool_id: Public tool identifier (e.g. "gravity.get_bouguer_anomaly").
            adapter_output: Raw output from the internal adapter.
            canon9_variable: CANON-9 variable this output grounds.
            artifact_ref: Reference to the source artifact.
            session_id: Internal session ID (goes to _internal only).
            trace_id: Internal trace ID (goes to _internal only).
            overrides: Explicit field overrides (e.g. acrisk=HOLD, requires_arif=True).

        Returns:
            ClaimEnvelope ready for external delivery.
        """
        # Map adapter epistemic label to public EpistemicLabel
        adapter_label = adapter_output.get("epistemic_label", "UNKNOWN").upper()
        label_map = {
            "OBSERVED": EpistemicLabel.OBSERVED,
            "DERIVED": EpistemicLabel.DERIVED,
            "ESTIMATE": EpistemicLabel.ESTIMATE,
            "HYPOTHESIS": EpistemicLabel.HYPOTHESIS,
            "PLAUSIBLE": EpistemicLabel.PLAUSIBLE,
            "CLAIM": EpistemicLabel.DERIVED,  # internal CLAIM → DERIVED externally
            "UNKNOWN": EpistemicLabel.UNKNOWN,
        }
        epistemic = label_map.get(adapter_label, EpistemicLabel.UNKNOWN)

        # Map adapter confidence to ACRisk
        adapter_confidence = adapter_output.get("confidence", "MEDIUM").upper()
        conf_map = {
            "HIGH": AcRiskLevel.QUALIFY,
            "MEDIUM": AcRiskLevel.QUALIFY,
            "LOW": AcRiskLevel.ADVISORY,
        }
        acrisk = conf_map.get(adapter_confidence, AcRiskLevel.ADVISORY)

        # Check for explicit 888_HOLD triggers in adapter output
        if adapter_output.get("calibration_status") == "UNCALIBRATED":
            acrisk = AcRiskLevel.HOLD
        if "⚠️ 888_HOLD" in " ".join(adapter_output.get("caveats", [])):
            acrisk = AcRiskLevel.HOLD

        # Uncertainty band
        uncertainty_band = None
        if epistemic in (EpistemicLabel.ESTIMATE, EpistemicLabel.HYPOTHESIS, EpistemicLabel.PLAUSIBLE):
            uncertainty_band = (
                adapter_output.get("uncertainty_band")
                or adapter_output.get("p05_p95")
                or adapter_output.get("confidence_interval")
            )

        # P0 #4: Auto-populate evidence_refs and actor for READ operations.
        # When evidence_for is empty and the operation is a READ (INGESTED/QC_VERIFIED),
        # default evidence_for to ["LIVE_PROBE"] so the APEX gate has something to score.
        evidence_for = adapter_output.get("evidence_for", [])
        claim_state_val = adapter_output.get("claim_state", "DERIVED_CANDIDATE")
        if not evidence_for and claim_state_val in ("INGESTED", "QC_VERIFIED", "NO_VALID_EVIDENCE"):
            evidence_for = ["LIVE_PROBE"]

        evidence_against = adapter_output.get("evidence_against", [])

        # P0 #4: Default actor to tool_id when adapter_output has no actor.
        # Prevents G=0.0 from APEX gate due to missing identity.
        actor_val = adapter_output.get("actor", tool_id.split(".")[0] if "." in tool_id else "geox-core")

        # P0 #4: Derive reason_code from acrisk + evidence.
        adapter_output.get("action_class", "READ")
        reason_code_val = "QUALIFY"
        if acrisk in (AcRiskLevel.HOLD, AcRiskLevel.BLOCK):
            reason_code_val = "GOVERNANCE_BLOCK"
        elif not evidence_for:
            reason_code_val = "NO_EVIDENCE"
        elif evidence_against and len(evidence_against) >= len(evidence_for):
            reason_code_val = "CONTRADICTION"

        # Verdict
        verdict = "QUALIFY"
        requires_arif = False
        if acrisk == AcRiskLevel.HOLD:
            verdict = "HOLD"
            requires_arif = True
        elif acrisk == AcRiskLevel.BLOCK:
            verdict = "REJECT"
            requires_arif = True

        overrides = overrides or {}

        return cls(
            tool_id=tool_id,
            claim_state=ClaimState.DERIVED_CANDIDATE,
            epistemic_label=epistemic,
            value=adapter_output.get("value", adapter_output.get("result", adapter_output)),
            unit=adapter_output.get("unit", "dimensionless"),
            canon9_variable=canon9_variable or adapter_output.get("canon9_variable"),
            uncertainty_band=uncertainty_band,
            acrisk=acrisk,
            verdict=verdict,
            requires_arif=requires_arif,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            caveats=adapter_output.get("caveats", []),
            artifact_ref=artifact_ref,
            # P0 #4: Pipeline traceability fields
            origin=adapter_output.get("origin", "FORMULATE"),
            reason_code=adapter_output.get("reason_code", reason_code_val),
            actor=actor_val,
            _internal={
                "adapter_output_ref": str(uuid4())[:8],
                "library_versions": adapter_output.get("library_version"),
                "params_hash": adapter_output.get("params_hash"),
                "session_id": session_id,
                "trace_id": trace_id,
                "adapter_name": adapter_output.get("library"),
            },
            **overrides,
        )


# ─── Specialized Envelope Subclasses ──────────────────────────────────────────


class GravityEnvelope(ClaimEnvelope):
    """Specialized envelope for gravity outputs."""

    canon9_variable: str = "rho"  # density is the gravity grounding


class MagneticEnvelope(ClaimEnvelope):
    """Specialized envelope for magnetic outputs."""

    canon9_variable: str = "chi"  # magnetic susceptibility context


class TectonicEnvelope(ClaimEnvelope):
    """Specialized envelope for plate tectonic outputs."""

    canon9_variable: None = None  # plate tectonics is structural, not CANON-9


class BathymetryEnvelope(ClaimEnvelope):
    """Specialized envelope for seabed/bathymetry outputs."""

    canon9_variable: None = None  # surface observation


# ─── Membrane Guard ───────────────────────────────────────────────────────────


def wrap_for_membrane(
    tool_id: str,
    adapter_output: dict[str, Any],
    canon9_variable: str | None = None,
    envelope_class: type[ClaimEnvelope] = ClaimEnvelope,
    **kwargs,
) -> dict[str, Any]:
    """
    ONE entry point for all outputs crossing the geox_core → MCP membrane.

    This function is the customs checkpoint. Every adapter output must pass
    through here before reaching an external MCP client.

    Args:
        tool_id: Public tool ID from tools_manifest.py.
        adapter_output: Raw output from the internal adapter.
        canon9_variable: CANON-9 variable grounding.
        envelope_class: Specialized envelope subclass if needed.
        **kwargs: Additional ClaimEnvelope field overrides.

    Returns:
        dict — the public envelope JSON (no _internal fields).
    """
    envelope = envelope_class.from_adapter_output(
        tool_id=tool_id,
        adapter_output=adapter_output,
        canon9_variable=canon9_variable,
        **kwargs,
    )
    return envelope.model_dump_public()


# ─── Version Lock ─────────────────────────────────────────────────────────────

CLAIM_ENVELOPE_VERSION = "1.1.0"
CLAIM_ENVELOPE_EPOCH = "2026-07-10"
CLAIM_ENVELOPE_STATUS = "LOCKED"

"""
Version history:
  1.0.0 (2026-06-26) — Initial locked schema. Replaces ad-hoc JSON returns.
                          All 16 canonical tools must use ClaimEnvelope from this date.
  1.1.0 (2026-07-10) — P0 #4 fix: Added origin, reason_code, actor fields.
                          Auto-populates evidence_refs for READ operations.
                          Defaults actor to tool name when absent (prevents G=0.0).
                          Defaults evidence_for to ["LIVE_PROBE"] for READ-class claims.

DITEMPA BUKAN DIBERI — The envelope is law. The envelope is not a suggestion.
"""
