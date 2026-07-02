"""
GEOX Provenance Sidecar — W3C PROV + ISO 19115 lineage record.

Every GEOX artifact must carry a machine-readable provenance sidecar.
This is the load-bearing receipt for: "where did this output come from,
under what conditions, and who certified it?"

Refs:
- W3C PROV-DM: https://www.w3.org/TR/prov-dm/
- ISO 19115-1:2014 (Geographic information — Metadata)
- GeMS (Geologic Map Schema, USGS)

Constitutional link: F2 TRUTH + F11 AUDIT + F13 SOVEREIGN.
A claim without provenance is hearsay. An interpretation without
provenance is fraud.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# W3C PROV Core Types — Agent, Activity, Entity, Attribution
# ─────────────────────────────────────────────────────────────────────────────


class ProvAgent(BaseModel):
    """W3C PROV 'Agent' — a person, organization, or software that bears
    responsibility for an activity."""

    agent_id: str = Field(..., description="Stable identifier (e.g., 'arifOS', 'geox_v1.0', 'arif')")
    agent_type: Literal["Person", "Organization", "SoftwareAgent"] = "SoftwareAgent"
    name: Optional[str] = None
    role: Optional[str] = Field(None, description="e.g., 'operator', 'operator_sovereign', 'system'")


class ProvActivity(BaseModel):
    """W3C PROV 'Activity' — how the artifact came to be."""

    activity_id: str = Field(..., description="Stable activity identifier")
    activity_type: str = Field(..., description="e.g., 'geox_seismic_compute', 'geox_petrophysics'")
    started_at: datetime
    ended_at: Optional[datetime] = None
    used_inputs: list[str] = Field(default_factory=list, description="Input artifact URIs")
    parameters: dict[str, Any] = Field(default_factory=dict)
    geox_version: Optional[str] = None
    git_commit: Optional[str] = None
    model_versions: dict[str, str] = Field(default_factory=dict)


class ProvEntity(BaseModel):
    """W3C PROV 'Entity' — the artifact itself."""

    entity_id: str = Field(..., description="Stable artifact URI")
    entity_type: str = Field(..., description="e.g., 'map_preview', 'claim', 'volumetrics'")
    checksum: str = Field(..., description="SHA-256 of artifact content")
    checksum_algorithm: Literal["sha256"] = "sha256"
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    media_uri: Optional[str] = Field(None, description="Where the artifact lives")


# ─────────────────────────────────────────────────────────────────────────────
# ISO 19115 Metadata Bridge — Geographic metadata
# ─────────────────────────────────────────────────────────────────────────────


class ISO19115Metadata(BaseModel):
    """ISO 19115-1 core metadata fields that GEOX must populate.

    Only the fields that matter for Earth evidence discipline.
    Full ISO 19115 has 300+ fields; we only carry the load-bearing ones.
    """

    title: str
    abstract: Optional[str] = None
    purpose: Optional[str] = None
    status: Literal["draft", "validated", "sealed_candidate", "rejected", "superseded"] = "draft"
    topic_category: Literal[
        "geoscientificInformation",
        "elevation",
        "imageryBaseMapsEarthCover",
        "oceans",
        "environment",
        "structure",
    ] = "geoscientificInformation"

    # Reference system
    crs_epsg: int = Field(4326, description="EPSG code (default WGS84)")
    crs_name: Optional[str] = "WGS84"

    # Geographic extent
    bbox_west: Optional[float] = Field(None, ge=-180, le=180)
    bbox_east: Optional[float] = Field(None, ge=-180, le=180)
    bbox_south: Optional[float] = Field(None, ge=-90, le=90)
    bbox_north: Optional[float] = Field(None, ge=-90, le=90)

    # Temporal extent
    temporal_start: Optional[datetime] = None
    temporal_end: Optional[datetime] = None

    # Lineage (ISO 19115 'LI_Lineage' condensed)
    lineage_statement: Optional[str] = None

    # Distribution
    distribution_format: Optional[str] = None
    access_constraints: Optional[str] = None
    use_constraints: Optional[str] = None

    @field_validator("bbox_west", "bbox_east")
    @classmethod
    def _bbox_lon_valid(cls, v: Optional[float]) -> Optional[float]:
        return v


# ─────────────────────────────────────────────────────────────────────────────
# GeMS Geologic Map Schema Bridge (USGS)
# ─────────────────────────────────────────────────────────────────────────────


class GeMSMapMetadata(BaseModel):
    """Geologic Map Schema (GeMS) condensed metadata.

    Only the fields GEOX exposes to the public map surface.
    Full GeMS is in `geox_map_layers_list` resources.
    """

    map_id: str
    map_name: Optional[str] = None
    map_type: Literal[
        "geologic",
        "lithologic",
        "structural",
        "isopach",
        "facies",
        "source_rock",
        "prospect",
        "uncertainty",
    ] = "geologic"
    scale: Optional[int] = Field(None, ge=1, description="Map scale denominator")
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    series: Optional[str] = None
    source_license: Literal[
        "CC0",
        "CC-BY",
        "CC-BY-SA",
        "CC-BY-NC",
        "PUBLIC_DOMAIN",
        "PROPRIETARY",
        "GOV_OPEN_DATA",
        "RESTRICTED",
        "UNKNOWN",
    ] = "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# Review & Authority Trail
# ─────────────────────────────────────────────────────────────────────────────


class HumanReview(BaseModel):
    """A human (or sovereign) review event on the artifact."""

    reviewer_id: str
    reviewer_role: Literal[
        "operator",
        "operator_sovereign",
        "domain_expert",
        "auditor",
        "guest",
    ]
    reviewed_at: datetime
    verdict: Literal["approved", "rejected", "needs_revision", "abstain"]
    notes: Optional[str] = None
    signature: Optional[str] = Field(None, description="Cryptographic signature, if any")


class ArifOSReview(BaseModel):
    """arifOS kernel review — required for SEAL-eligible artifacts."""

    arifos_review_id: Optional[str] = None
    session_id: Optional[str] = None
    verdict: Literal["SEAL", "HOLD", "SABAR", "VOID", "PENDING"] = "PENDING"
    floor_checks_passed: list[str] = Field(
        default_factory=list,
        description="F1-F13 IDs that passed, e.g. ['F2_TRUTH', 'F11_AUDIT']",
    )
    floor_checks_failed: list[str] = Field(default_factory=list)
    reviewed_at: Optional[datetime] = None


class VaultReceiptRef(BaseModel):
    """Pointer to the VAULT999 immutable record (if sealed)."""

    vault_entry_id: Optional[str] = None
    sealed_at: Optional[datetime] = None
    chain_hash: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Full Provenance Sidecar — the artifact's birth certificate
# ─────────────────────────────────────────────────────────────────────────────


class ProvenanceSidecar(BaseModel):
    """Complete provenance sidecar for a GEOX artifact.

    Combines W3C PROV + ISO 19115 + GeMS + governance trail. One sidecar
    per artifact. Sidecar is sealed alongside the artifact to VAULT999.

    Constitutional: F2 TRUTH (every artifact claims its origins).
    """

    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    artifact_type: str = Field(..., description="e.g., 'map_preview', 'claim', 'volumetrics'")

    # W3C PROV core
    entity: ProvEntity
    was_generated_by: ProvActivity
    was_attributed_to: list[ProvAgent] = Field(default_factory=list)

    # ISO 19115 / GeMS
    iso_19115: ISO19115Metadata
    gems: Optional[GeMSMapMetadata] = None

    # Governance trail
    human_reviews: list[HumanReview] = Field(default_factory=list)
    arifos_review: Optional[ArifOSReview] = None
    vault_receipt: Optional[VaultReceiptRef] = None

    # Processing steps (ordered)
    processing_steps: list[str] = Field(default_factory=list)

    # Checksums of input layers
    input_checksums: dict[str, str] = Field(default_factory=dict)

    # Sidecar metadata
    sidecar_created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sidecar_version: str = "1.0.0"

    def export_gate(self) -> tuple[bool, list[str]]:
        """Validate the sidecar is export-ready.

        Returns (is_valid, list_of_blocking_reasons).
        Mirrors ArgumentSidecar's export gate — both must pass.
        """
        blockers: list[str] = []

        if not self.entity.checksum:
            blockers.append("Entity has no checksum")
        if not self.was_generated_by.activity_id:
            blockers.append("Activity has no ID")
        if not self.was_attributed_to:
            blockers.append("No attribution — at least one agent required")
        if not self.iso_19115.title:
            blockers.append("ISO 19115 title required")
        if self.iso_19115.status not in ("validated", "sealed_candidate"):
            blockers.append(f"Status '{self.iso_19115.status}' is not export-eligible")
        # If Arif review is present and VOID/REJECTED, block
        if self.arifos_review and self.arifos_review.verdict in ("VOID", "HOLD"):
            blockers.append(f"arifOS verdict '{self.arifos_review.verdict}' blocks export")

        return (len(blockers) == 0, blockers)

    def to_dict(self) -> dict[str, Any]:
        """Canonical JSON-serializable export."""
        return self.model_dump(mode="json", exclude_none=True)

    @staticmethod
    def compute_checksum(content: bytes | str) -> str:
        """SHA-256 helper for entity checksum."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def for_artifact(
        artifact_id: str,
        artifact_type: str,
        artifact_content: bytes | str,
        activity_type: str,
        agent_id: str,
        iso_19115: ISO19115Metadata,
        gems: Optional[GeMSMapMetadata] = None,
        geox_version: Optional[str] = None,
        git_commit: Optional[str] = None,
    ) -> "ProvenanceSidecar":
        """Convenience builder for the common case.

        Makes the sidecar easy to attach without forgetting required fields.
        """
        now = datetime.now(timezone.utc)
        checksum = ProvenanceSidecar.compute_checksum(artifact_content)
        size = len(artifact_content) if isinstance(artifact_content, (bytes, str)) else None

        entity = ProvEntity(
            entity_id=f"artifact:{artifact_id}",
            entity_type=artifact_type,
            checksum=checksum,
            size_bytes=size,
        )
        activity = ProvActivity(
            activity_id=f"activity:{uuid4()}",
            activity_type=activity_type,
            started_at=now,
            geox_version=geox_version,
            git_commit=git_commit,
        )
        agents = [
            ProvAgent(agent_id="geox", agent_type="SoftwareAgent", role="system"),
            ProvAgent(agent_id=agent_id, agent_type="SoftwareAgent", role="executor"),
        ]
        return ProvenanceSidecar(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            entity=entity,
            was_generated_by=activity,
            was_attributed_to=agents,
            iso_19115=iso_19115,
            gems=gems,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level self-test
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    # Sanity check
    iso = ISO19115Metadata(
        title="Sabah Basin Closure Preview",
        bbox_west=118.0,
        bbox_east=119.5,
        bbox_south=5.0,
        bbox_north=7.5,
    )
    sidecar = ProvenanceSidecar.for_artifact(
        artifact_id="sabah_closure_preview_001",
        artifact_type="map_preview",
        artifact_content=b"fake-png-content",
        activity_type="geox_map_render_preview",
        agent_id="arifOS_session_001",
        iso_19115=iso,
        gems=GeMSMapMetadata(map_id="SABAH_001", map_type="structural"),
        geox_version="1.0.0",
        git_commit="ca4c1a73",
    )
    print(json.dumps(sidecar.to_dict(), indent=2, default=str))
    is_valid, blockers = sidecar.export_gate()
    print(f"\nExport gate: {'PASS' if is_valid else 'BLOCKED'}")
    if blockers:
        for b in blockers:
            print(f"  - {b}")
