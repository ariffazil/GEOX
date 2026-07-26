"""geo_project_state.py — Canonical GeoProjectState schema for GEOX.

Phase 888: Immutable, audit-traceable Pydantic state container wrapping wells,
surveys, artifacts, interpretations, scenarios, claims, contradictions, and receipts.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CoordinateReferenceSystem(BaseModel):
    crs_code: str = Field(default="EPSG:4326", description="Spatial reference system code")
    projected_unit: str = Field(default="m", description="Horizontal distance unit (m, ft)")
    vertical_datum: str = Field(default="MSL", description="Vertical reference datum (MSL, KB, GL)")
    depth_unit: str = Field(default="m", description="Vertical depth unit (m, ft)")


class HumanEditRecord(BaseModel):
    edit_id: str = Field(..., description="Unique edit record ID")
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    actor_id: str = Field(default="ARIF", description="Human or agent actor ID")
    target_object: str = Field(..., description="Object modified (e.g. horizon_candidate_1)")
    previous_value: Any = Field(default=None, description="Value prior to edit")
    new_value: Any = Field(..., description="New value after edit")
    reason: str = Field(..., description="Geological justification for edit")
    before_hash: str = Field(..., description="SHA-256 hash before edit")
    after_hash: str = Field(..., description="SHA-256 hash after edit")
    affected_claims: list[str] = Field(default_factory=list)


class ScenarioBranch(BaseModel):
    scenario_id: str = Field(..., description="Scenario identifier (e.g. Scenario_A_Channel)")
    title: str = Field(..., description="Descriptive title of scenario")
    hypothesis_summary: str = Field(..., description="Primary geological hypothesis")
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    volumetric_p50_mmboe: float | None = Field(default=None)
    gcos: float | None = Field(default=None)
    status: Literal["ACTIVE", "ARCHIVED", "FALSIFIED", "SELECTED"] = Field(default="ACTIVE")


class GeoProjectState(BaseModel):
    project_id: str = Field(..., description="Canonical project ID")
    project_name: str = Field(..., description="Project display name")
    created_at_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at_utc: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    commit_sha: str = Field(default="fafb6ddc", description="Repository commit SHA")
    physics_version: str = Field(default="GEOX-SOVEREIGN-v2026.07", description="Physics engine version")
    
    coordinate_reference: CoordinateReferenceSystem = Field(default_factory=CoordinateReferenceSystem)
    wells: list[dict[str, Any]] = Field(default_factory=list, description="Ingested well records")
    seismic_surveys: list[dict[str, Any]] = Field(default_factory=list, description="Seismic survey bounds & zarr refs")
    artifacts: list[dict[str, Any]] = Field(default_factory=list, description="Artifact identity references")
    interpretations: list[dict[str, Any]] = Field(default_factory=list, description="Picked horizons, faults & surfaces")
    scenarios: list[ScenarioBranch] = Field(default_factory=list, description="Competing scenario branches")
    claims: list[dict[str, Any]] = Field(default_factory=list, description="Falsifiable claim graph nodes")
    contradictions: list[dict[str, Any]] = Field(default_factory=list, description="Identified geological contradictions")
    uncertainty: dict[str, Any] = Field(default_factory=dict, description="Uncertainty taxonomy metrics")
    human_edits: list[HumanEditRecord] = Field(default_factory=list, description="Audit-trailed human edit receipts")
    receipts: list[dict[str, Any]] = Field(default_factory=list, description="Execution and witness receipts")

    def compute_state_hash(self) -> str:
        """Compute tamper-evident SHA-256 hash of canonical project state."""
        payload = {
            "project_id": self.project_id,
            "commit_sha": self.commit_sha,
            "wells_count": len(self.wells),
            "surveys_count": len(self.seismic_surveys),
            "claims_count": len(self.claims),
            "human_edits_count": len(self.human_edits),
            "updated_at_utc": self.updated_at_utc,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
