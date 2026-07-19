"""
GEOX Scar Memory — Constitutional pain records.

GEOX remembers wrong interpretations. Not to punish — to prevent repetition.

Each scar records:
- What was claimed
- What evidence was missing or wrong
- How the failure was detected
- What constraint this scar now imposes on future claims

Constitutional link: F2 TRUTH (scar tissue is a record of false confidence),
F7 HUMILITY (scars cap the confidence ceiling for analogous claims).

This is the substrate GEOX becomes wiser over time — not just smarter.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ScarSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
ScarCategory = Literal[
    "failed_play_model",
    "dry_hole_lesson",
    "false_dhi",
    "depth_conversion_failure",
    "velocity_pullup",
    "invalid_fault_model",
    "overconfident_prospect",
    "bad_data_lineage",
    "human_override",
    "governance_drift",
    "surface_drift",
    "sealed_claim_revoked",
]
ScarDetectionMethod = Literal[
    "post_drill_outcome",
    "rival_interpretation_accepted",
    "human_override",
    "audit_redteam",
    "conformance_failure",
    "vault_replay",
    "kinabalu_falsification",
    "self_disclosed",
]


class ScarEvidence(BaseModel):
    """A piece of evidence attached to a scar."""

    evidence_kind: Literal[
        "drill_result",
        "well_log",
        "seismic",
        "core",
        "DST",
        "publication",
        "audit_log",
        "test_failure",
        "human_testimony",
    ]
    description: str
    source: str | None = None
    url: str | None = None
    attached_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Scar(BaseModel):
    """A single failure event metabolized into a constitutional constraint.

    Scars are append-only. Once sealed, they cannot be deleted — only
    superseded by a newer scar that explicitly invalidates them.
    """

    scar_id: str = Field(default_factory=lambda: f"scar:{uuid4()}")
    category: ScarCategory
    severity: ScarSeverity
    scar_pressure: float = Field(..., ge=0.0, le=1.0, description="How much this scar constrains future claims [0-1]")

    # What was claimed and what was wrong
    original_claim: str = Field(..., description="The claim that failed or was wrong")
    failure_mode: str = Field(..., description="Plain-language description of the failure")
    domain: str = Field("geoscience", description="Domain this scar applies to")
    basin_id: str | None = None
    prospect_id: str | None = None

    # Detection
    detected_by: ScarDetectionMethod
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Evidence
    evidence: list[ScarEvidence] = Field(default_factory=list)

    # Constitutional constraint
    constraint_imposed: str = Field(
        ...,
        description="What this scar now forbids or requires in future claims",
    )
    confidence_ceiling: float | None = Field(
        None,
        ge=0.0,
        le=0.90,
        description="Maximum confidence any analogous claim may carry (F7 HUMILITY cap)",
    )
    analog_pattern: str | None = Field(
        None,
        description="Pattern that, if matched, triggers this scar's constraint",
    )

    # Lifecycle
    sealed: bool = Field(False, description="True if scar is sealed to VAULT999")
    vault_entry_id: str | None = None
    superseded_by: str | None = Field(
        None,
        description="scar_id of newer scar that supersedes this one",
    )
    sealed_by: str = Field("geox_scar_sealer", description="Agent or actor that sealed")
    sealed_at: datetime | None = None

    def is_active(self) -> bool:
        """Whether this scar currently constrains claims.

        Inactive if explicitly superseded or revoked (future use).
        """
        return self.sealed and self.superseded_by is None

    def matches_claim(self, claim_text: str) -> bool:
        """Naive textual match — production would use semantic similarity.

        Production: replace with Qdrant vector lookup over scar corpus.
        """
        if not self.analog_pattern:
            return False
        return self.analog_pattern.lower() in claim_text.lower()

    def apply_constraint(self, claim_confidence: float) -> tuple[float, str | None]:
        """Apply this scar's confidence ceiling to a candidate claim.

        Returns (adjusted_confidence, block_reason_or_none).
        """
        if not self.is_active():
            return claim_confidence, None
        if self.confidence_ceiling is None:
            return claim_confidence, None
        if claim_confidence > self.confidence_ceiling:
            return self.confidence_ceiling, (
                f"Scar {self.scar_id} ({self.severity}) caps confidence at {self.confidence_ceiling:.2f} for analogous claims"
            )
        return claim_confidence, None

    def seal(self, vault_entry_id: str, sealed_by: str = "geox_scar_sealer") -> None:
        """Seal this scar to VAULT999. Idempotent."""
        if self.sealed:
            return
        self.sealed = True
        self.vault_entry_id = vault_entry_id
        self.sealed_by = sealed_by
        self.sealed_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


# ─────────────────────────────────────────────────────────────────────────────
# Scar store — in-memory + persistence hook
# ─────────────────────────────────────────────────────────────────────────────


class ScarStore:
    """Canonical scar store. Backed by VAULT999 in production; in-memory here.

    Usage:
        store = ScarStore()
        scar = Scar(...)
        store.add(scar)
        store.seal(scar.scar_id, vault_entry_id="...")

        # Later, when a claim comes in:
        adjusted, reason = store.apply_to_claim("...", claim_confidence=0.85)
    """

    def __init__(self) -> None:
        self._scars: dict[str, Scar] = {}

    def add(self, scar: Scar) -> Scar:
        if scar.scar_id in self._scars:
            raise ValueError(f"Scar {scar.scar_id} already exists (scars are immutable)")
        self._scars[scar.scar_id] = scar
        return scar

    def get(self, scar_id: str) -> Scar | None:
        return self._scars.get(scar_id)

    def list_active(self, domain: str | None = None, basin_id: str | None = None) -> list[Scar]:
        scars = [s for s in self._scars.values() if s.is_active()]
        if domain:
            scars = [s for s in scars if s.domain == domain]
        if basin_id:
            scars = [s for s in scars if s.basin_id == basin_id]
        return scars

    def seal(self, scar_id: str, vault_entry_id: str, sealed_by: str = "geox_scar_sealer") -> Scar:
        scar = self.get(scar_id)
        if not scar:
            raise KeyError(f"Scar {scar_id} not found")
        scar.seal(vault_entry_id, sealed_by)
        return scar

    def apply_to_claim(self, claim_text: str, claim_confidence: float, domain: str | None = None) -> tuple[float, list[str]]:
        """Apply all active matching scars to a candidate claim.

        Returns (final_confidence, list_of_block_reasons).
        Multiple scars may apply; the most restrictive ceiling wins.
        """
        block_reasons: list[str] = []
        min_ceiling = claim_confidence

        for scar in self.list_active(domain=domain):
            if scar.matches_claim(claim_text):
                adjusted, reason = scar.apply_constraint(claim_confidence)
                if reason:
                    block_reasons.append(reason)
                if scar.confidence_ceiling is not None:
                    min_ceiling = min(min_ceiling, scar.confidence_ceiling)

        return min_ceiling, block_reasons

    def supersede(self, old_scar_id: str, new_scar: Scar) -> Scar:
        """Mark old scar as superseded by new one."""
        old = self.get(old_scar_id)
        if not old:
            raise KeyError(f"Scar {old_scar_id} not found")
        if not old.is_active():
            raise ValueError(f"Scar {old_scar_id} is not active; cannot supersede")
        old.superseded_by = new_scar.scar_id
        self.add(new_scar)
        return new_scar

    def export(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._scars.values()]


# ─────────────────────────────────────────────────────────────────────────────
# Seed scars — GEOX ships with two constitutional scars from kinabalu_corpus
# ─────────────────────────────────────────────────────────────────────────────


def seed_kinabalu_scars() -> ScarStore:
    """Two pre-loaded, sealed scars from the Kinabalu Falsification work (2026-06-29).

    These are the founding scars of GEOX scar memory — already sealed to VAULT999
    so they constrain claims immediately.

    Returns:
        ScarStore with both scars added and sealed.
    """
    store = ScarStore()
    scars: list[Scar] = []

    scars.append(
        Scar(
            category="overconfident_prospect",
            severity="HIGH",
            scar_pressure=0.85,
            original_claim=(
                "Kinabalu and Layang-Layang Basements are tectonically continuous and represent a single allochthonous terrane."
            ),
            failure_mode=(
                "Claim was based on prior literature but did not reconcile with "
                "independent structural and biostratigraphic evidence. Falsified "
                "by SCS subduction-zone kinematics and basement petrology divergence."
            ),
            domain="tectonic_correlation",
            basin_id="kinabalu_layang",
            detected_by="kinabalu_falsification",
            evidence=[
                ScarEvidence(
                    evidence_kind="publication",
                    description="GEOX-KINABALU-FALSIFICATION-LC001-2026-06-29",
                    source="forge_work/KINABALU-LAYANG-BASEMENT-FALSIFICATION-LC001-2026-06-29.md",
                )
            ],
            constraint_imposed=(
                "Any claim of tectonic continuity between Kinabalu and Layang-Layang "
                "must include independent basement petrology, biostrat, AND kinematic "
                "reconciliation. Single-source correlation is insufficient."
            ),
            confidence_ceiling=0.60,
            analog_pattern="tectonic continuity",
        )
    )

    scars.append(
        Scar(
            category="velocity_pullup",
            severity="MEDIUM",
            scar_pressure=0.55,
            original_claim=(
                "Apparent structural closure identified on time-domain seismic interpretation is a real subsurface feature."
            ),
            failure_mode=(
                "Closure was a velocity pull-up artifact from overlying high-velocity "
                "carbonate or basalt. Without depth conversion sensitivity, the "
                "feature vanishes below tuning thickness."
            ),
            domain="structural_interpretation",
            detected_by="post_drill_outcome",
            evidence=[
                ScarEvidence(
                    evidence_kind="drill_result",
                    description="Pre-drill structural high turned out to be velocity artifact",
                    source="PSC Sabah post-mortem",
                )
            ],
            constraint_imposed=(
                "Any structural closure from time-domain interpretation must be "
                "validated by depth-conversion sensitivity analysis. No depth "
                "sensitivity → no claim."
            ),
            confidence_ceiling=0.70,
            analog_pattern="structural closure",
        )
    )

    # Add to store and seal immediately — founding scars are constitutional.
    for scar in scars:
        store.add(scar)
        store.seal(scar.scar_id, vault_entry_id=f"vault:{scar.scar_id}")

    return store


# ─────────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    store = seed_kinabalu_scars()

    # Test constraint application
    test_claim = "Tectonic continuity between Sabah and Kalimantan terranes"
    final_conf, reasons = store.apply_to_claim(test_claim, claim_confidence=0.85)
    print(f"Claim: {test_claim}")
    print(f"Final confidence: {final_conf:.2f}")
    print(f"Reasons: {reasons}")

    print(f"\nActive scars: {len(store.list_active())}")
    print(f"Export: {len(store.export())} scars")
