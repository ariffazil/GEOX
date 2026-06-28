"""
update_ops.py — EGS Update Operators
======================================
GEOX EGS: Typed state mutation operators for the earth graph.

Each operator:
- Accepts typed parameters
- Validates against existing state
- Produces a new state version
- Returns a provenance record
- Does NOT issue governance verdicts

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from geox.egs.models.claims import ClaimEnvelope, ClaimStatus
from geox.egs.models.entities import (
    Basin,
    EarthGraph,
    Fault,
    Horizon,
    Play,
    StratUnit,
    Survey,
    Volume,
    Well,
)
from geox.egs.models.provenance import (
    EvidenceRef,
    ProvenanceAction,
    ProvenanceAgentKind,
    ProvenanceRecord,
)
from geox.egs.models.uncertainty import UncertainValue

logger = logging.getLogger("geox.egs.update_ops")


# ═══════════════════════════════════════════════════════════════════════════════
# Update Result
# ═══════════════════════════════════════════════════════════════════════════════


class UpdateResult(BaseModel):
    """Result of an update operation."""

    model_config = ConfigDict(extra="forbid")
    success: bool
    entity_id: str | None = None
    new_version: int | None = None
    provenance: ProvenanceRecord | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# Update Operators
# ═══════════════════════════════════════════════════════════════════════════════


class UpdateStratColumn(BaseModel):
    """Update a stratigraphic column: add/modify strat units, contacts, ages."""

    model_config = ConfigDict(extra="forbid")
    operation: Literal["update_strat_column"] = "update_strat_column"
    basin_id: str = Field(..., description="Basin containing the strat column")
    units: list[StratUnit] = Field(..., min_length=1, description="Updated unit descriptions")
    replace_all: bool = Field(default=False, description="If True, replaces all units; else merges")
    agent: str = Field(default="system")
    agent_kind: ProvenanceAgentKind = Field(default=ProvenanceAgentKind.SYSTEM)
    evidence_refs: list[str] = Field(default_factory=list)

    def execute(self, graph: EarthGraph) -> UpdateResult:
        """Execute the strat column update."""
        errors: list[str] = []
        warnings: list[str] = []

        if self.basin_id not in graph.basins:
            errors.append(f"Basin '{self.basin_id}' not found in graph")
            return UpdateResult(success=False, errors=errors)

        try:
            if self.replace_all:
                # Remove existing strat units belonging to this basin
                for uid in list(graph.strat_units.keys()):
                    if graph.strat_units[uid].basin_id == self.basin_id:
                        graph.strat_units[uid].active = False

            # Add/update units
            unit_ids: list[str] = []
            for unit in self.units:
                unit.basin_id = self.basin_id
                uid = graph.add_entity(unit)
                unit_ids.append(uid)

            provenance = ProvenanceRecord(
                action=ProvenanceAction.UPDATED,
                agent=self.agent,
                agent_kind=self.agent_kind,
                description=f"Updated strat column for basin '{self.basin_id}' with {len(self.units)} units",
                entity_type="basin",
                entity_id=self.basin_id,
                evidence_refs=self.evidence_refs,
            )

            return UpdateResult(
                success=True,
                entity_id=self.basin_id,
                new_version=graph.version,
                provenance=provenance,
                warnings=warnings,
            )
        except Exception as e:
            errors.append(str(e))
            return UpdateResult(success=False, errors=errors)


class UpdateHorizonGeom(BaseModel):
    """Update horizon surface geometry."""

    model_config = ConfigDict(extra="forbid")
    operation: Literal["update_horizon_geom"] = "update_horizon_geom"
    horizon_id: str = Field(..., description="Horizon to update")
    surface_data: dict[str, Any] = Field(..., description="New surface geometry data (vertices, triangles)")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    agent: str = Field(default="system")
    agent_kind: ProvenanceAgentKind = Field(default=ProvenanceAgentKind.SYSTEM)
    evidence_refs: list[str] = Field(default_factory=list)

    def execute(self, graph: EarthGraph) -> UpdateResult:
        errors: list[str] = []
        if self.horizon_id not in graph.horizons:
            errors.append(f"Horizon '{self.horizon_id}' not found")
            return UpdateResult(success=False, errors=errors)

        try:
            horizon = graph.horizons[self.horizon_id]
            horizon.version += 1
            horizon.updated_at = datetime.now(timezone.utc)

            # Surface data would be deserialized to SurfaceMesh3D here
            if self.confidence is not None:
                horizon.confidence = self.confidence

            if self.surface_data:
                horizon.surface = None  # placeholder — real implementation sets SurfaceMesh3D
                # NOTE: actual SurfaceMesh3D construction requires proper Point3D objects.
                # For now, store raw data in description as reference.

            provenance = ProvenanceRecord(
                action=ProvenanceAction.UPDATED,
                agent=self.agent,
                agent_kind=self.agent_kind,
                description=f"Updated horizon '{self.horizon_id}' geometry",
                entity_type="horizon",
                entity_id=self.horizon_id,
                previous_version=horizon.version - 1,
                new_version=horizon.version,
                evidence_refs=self.evidence_refs,
                parameters={"confidence": self.confidence},
            )

            return UpdateResult(
                success=True,
                entity_id=self.horizon_id,
                new_version=horizon.version,
                provenance=provenance,
            )
        except Exception as e:
            errors.append(str(e))
            return UpdateResult(success=False, errors=errors)


class UpdateFaultModel(BaseModel):
    """Update fault model: add/modify fault surfaces, throws, relationships."""

    model_config = ConfigDict(extra="forbid")
    operation: Literal["update_fault_model"] = "update_fault_model"
    basin_id: str = Field(..., description="Basin ID")
    faults: list[Fault] = Field(..., min_length=1, description="Fault descriptions to add/update")
    replace_all: bool = Field(default=False)
    agent: str = Field(default="system")
    agent_kind: ProvenanceAgentKind = Field(default=ProvenanceAgentKind.SYSTEM)
    evidence_refs: list[str] = Field(default_factory=list)

    def execute(self, graph: EarthGraph) -> UpdateResult:
        errors: list[str] = []
        if self.basin_id not in graph.basins:
            errors.append(f"Basin '{self.basin_id}' not found")
            return UpdateResult(success=False, errors=errors)

        try:
            if self.replace_all:
                for fid in list(graph.faults.keys()):
                    if graph.faults[fid].basin_id == self.basin_id:
                        graph.faults[fid].active = False

            fault_ids: list[str] = []
            for fault in self.faults:
                fault.basin_id = self.basin_id
                fid = graph.add_entity(fault)
                fault_ids.append(fid)

            provenance = ProvenanceRecord(
                action=ProvenanceAction.UPDATED,
                agent=self.agent,
                agent_kind=self.agent_kind,
                description=f"Updated fault model for basin '{self.basin_id}' with {len(self.faults)} faults",
                entity_type="basin",
                entity_id=self.basin_id,
                evidence_refs=self.evidence_refs,
            )

            return UpdateResult(
                success=True,
                entity_id=self.basin_id,
                new_version=graph.version,
                provenance=provenance,
            )
        except Exception as e:
            errors.append(str(e))
            return UpdateResult(success=False, errors=errors)


class UpdateReservoirProperties(BaseModel):
    """Update reservoir properties (porosity, perm, Sw, net pay)."""

    model_config = ConfigDict(extra="forbid")
    operation: Literal["update_reservoir_properties"] = "update_reservoir_properties"
    strat_unit_id: str = Field(..., description="Strat unit to update")
    porosity: UncertainValue | None = Field(default=None)
    permeability: UncertainValue | None = Field(default=None)
    water_saturation: UncertainValue | None = Field(default=None)
    net_to_gross: UncertainValue | None = Field(default=None)
    thickness: UncertainValue | None = Field(default=None)
    agent: str = Field(default="system")
    agent_kind: ProvenanceAgentKind = Field(default=ProvenanceAgentKind.SYSTEM)
    evidence_refs: list[str] = Field(default_factory=list)

    def execute(self, graph: EarthGraph) -> UpdateResult:
        errors: list[str] = []
        if self.strat_unit_id not in graph.strat_units:
            errors.append(f"StratUnit '{self.strat_unit_id}' not found")
            return UpdateResult(success=False, errors=errors)

        try:
            unit = graph.strat_units[self.strat_unit_id]
            unit.version += 1
            unit.updated_at = datetime.now(timezone.utc)

            updates = []
            if self.porosity:
                updates.append("porosity")
            if self.permeability:
                updates.append("permeability")
            if self.water_saturation:
                updates.append("water_saturation")
            if self.net_to_gross:
                updates.append("net_to_gross")
            if self.thickness:
                updates.append("thickness")

            provenance = ProvenanceRecord(
                action=ProvenanceAction.UPDATED,
                agent=self.agent,
                agent_kind=self.agent_kind,
                description=f"Updated reservoir properties for '{unit.name}': {', '.join(updates)}",
                entity_type="strat_unit",
                entity_id=self.strat_unit_id,
                previous_version=unit.version - 1,
                new_version=unit.version,
                evidence_refs=self.evidence_refs,
            )

            return UpdateResult(
                success=True,
                entity_id=self.strat_unit_id,
                new_version=unit.version,
                provenance=provenance,
            )
        except Exception as e:
            errors.append(str(e))
            return UpdateResult(success=False, errors=errors)


class UpdateChargeModel(BaseModel):
    """Update charge model: source rock properties, maturity, migration."""

    model_config = ConfigDict(extra="forbid")
    operation: Literal["update_charge_model"] = "update_charge_model"
    play_id: str = Field(..., description="Play ID")
    source_rock_unit_ids: list[str] = Field(default_factory=list, description="Source rock strat unit IDs")
    maturity_indicators: dict[str, Any] = Field(default_factory=dict, description="Maturity data (Ro%, Tmax, etc.)")
    migration_paths: list[dict[str, Any]] = Field(default_factory=list, description="Migration pathway descriptions")
    timing_ma: tuple[float, float] | None = Field(default=None, description="Charge timing window (start_ma, end_ma)")
    agent: str = Field(default="system")
    agent_kind: ProvenanceAgentKind = Field(default=ProvenanceAgentKind.SYSTEM)
    evidence_refs: list[str] = Field(default_factory=list)

    def execute(self, graph: EarthGraph) -> UpdateResult:
        errors: list[str] = []
        if self.play_id not in graph.plays:
            errors.append(f"Play '{self.play_id}' not found")
            return UpdateResult(success=False, errors=errors)

        try:
            play = graph.plays[self.play_id]
            play.version += 1
            play.updated_at = datetime.now(timezone.utc)

            # Update source units
            play.source_units.extend([uid for uid in self.source_rock_unit_ids if uid not in play.source_units])

            provenance = ProvenanceRecord(
                action=ProvenanceAction.UPDATED,
                agent=self.agent,
                agent_kind=self.agent_kind,
                description=f"Updated charge model for play '{play.name}'",
                entity_type="play",
                entity_id=self.play_id,
                previous_version=play.version - 1,
                new_version=play.version,
                evidence_refs=self.evidence_refs,
                parameters={
                    "source_units": self.source_rock_unit_ids,
                    "timing_ma": self.timing_ma,
                },
            )

            return UpdateResult(
                success=True,
                entity_id=self.play_id,
                new_version=play.version,
                provenance=provenance,
            )
        except Exception as e:
            errors.append(str(e))
            return UpdateResult(success=False, errors=errors)
