"""
GEOX Earth Layer Registry — canonical layer catalogue + governance gate.

A "layer" is a thematic data surface that GEOX can compose into map scenes
(e.g. basin boundaries, faults, isopachs, facies). This registry declares:

- The layer's identity, truth class, and provenance requirements
- The constitutional gates a layer must pass before it enters a scene
- The licensing + community-territory check (F6 MARUAH)
- The companion MCP resource URI for live lookup

This is L4 in the GEOX open-source register audit (forge_work/...).
It is NOT a tool — it's the schema that geox_map_layers_list queries
and that geox://layers/* MCP resources expose.

Constitutional: F1 AMANAH (every layer carries provenance) +
F2 TRUTH (truth_class declares epistemic weight) +
F6 MARUAH (community-territory check for indigenous lands) +
F11 AUDIT (every layer catalogued = auditable).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

# ─────────────────────────────────────────────────────────────────────────────
# Truth classes — declares what a layer is allowed to support
# ─────────────────────────────────────────────────────────────────────────────


class TruthClass(StrEnum):
    """Epistemic weight a layer carries in a composed scene.

    Mirrors GEOX scene_plan truth_class gating. Layers are NOT all equal —
    a structural fault from peer-reviewed literature has different weight
    than a draft prospect outline.
    """

    OBSERVATION = "OBSERVATION"  # Direct measurement (well tops, samples)
    INTERPRETATION = "INTERPRETATION"  # Geologist's reading (facies, environment)
    HYPOTHESIS = "HYPOTHESIS"  # Working model not yet drill-tested
    CONTEXT = "CONTEXT"  # Background only — never decision support
    DECISION_SUPPORT = "DECISION_SUPPORT"  # Approved for prospect decisions


# Map purposes that may use each truth class
MAP_PURPOSE_ALLOW = {
    "context": {TruthClass.OBSERVATION, TruthClass.INTERPRETATION, TruthClass.CONTEXT},
    "interpretation": {TruthClass.OBSERVATION, TruthClass.INTERPRETATION, TruthClass.CONTEXT},
    "qc": {TruthClass.OBSERVATION, TruthClass.INTERPRETATION, TruthClass.CONTEXT, TruthClass.HYPOTHESIS},
    "prospect_review": {TruthClass.OBSERVATION, TruthClass.INTERPRETATION, TruthClass.HYPOTHESIS, TruthClass.DECISION_SUPPORT},
    "publication": {TruthClass.OBSERVATION, TruthClass.INTERPRETATION, TruthClass.DECISION_SUPPORT},
}


# ─────────────────────────────────────────────────────────────────────────────
# License model — every layer declares its license
# ─────────────────────────────────────────────────────────────────────────────


class License(StrEnum):
    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_NC = "CC-BY-NC"
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    GOV_OPEN_DATA = "GOV_OPEN_DATA"
    PROPRIETARY = "PROPRIETARY"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"


# License permitted in each map purpose
LICENSE_ALLOW = {
    "context": {
        License.CC0,
        License.CC_BY,
        License.CC_BY_SA,
        License.CC_BY_NC,
        License.PUBLIC_DOMAIN,
        License.GOV_OPEN_DATA,
        License.UNKNOWN,
    },
    "interpretation": {License.CC0, License.CC_BY, License.CC_BY_SA, License.PUBLIC_DOMAIN, License.GOV_OPEN_DATA},
    "qc": {License.CC0, License.CC_BY, License.CC_BY_SA, License.PUBLIC_DOMAIN, License.GOV_OPEN_DATA},
    "prospect_review": {License.CC0, License.CC_BY, License.PUBLIC_DOMAIN, License.GOV_OPEN_DATA},
    "publication": {License.CC0, License.CC_BY, License.PUBLIC_DOMAIN, License.GOV_OPEN_DATA},
}


# ─────────────────────────────────────────────────────────────────────────────
# Layer record
# ─────────────────────────────────────────────────────────────────────────────


class EarthLayer(BaseModel):
    """A single thematic layer in the GEOX catalogue.

    Carries: identity, theme, truth class, provenance, license, bbox,
    MCP resource URI, and governance gate results.
    """

    # Identity
    layer_id: str = Field(..., description="Stable slug, e.g. 'sabah.basin_outline.v3'")
    name: str = Field(..., description="Human-readable name")
    description: str | None = None
    theme: Literal[
        "regional_geology",
        "basin",
        "structure",
        "stratigraphy",
        "petroleum",
        "tectonics",
        "sabah_regional",
        "se_asia",
    ]
    layer_type: Literal[
        "raster",
        "vector_polygon",
        "vector_line",
        "vector_point",
        "grid_3d",
        "tabular",
    ] = "vector_polygon"

    # Truth + license
    truth_class: TruthClass = TruthClass.CONTEXT
    license: License = License.UNKNOWN

    # Geographic extent (optional — some layers are global)
    bbox_west: float | None = Field(None, ge=-180, le=180)
    bbox_east: float | None = Field(None, ge=-180, le=180)
    bbox_south: float | None = Field(None, ge=-90, le=90)
    bbox_north: float | None = Field(None, ge=-90, le=90)

    # CRS
    crs_epsg: int = 4326

    # Provenance (lightweight — full sidecar lives in sidecar module)
    source_id: str | None = Field(None, description="e.g. USGS map ID, Malaysian NOC dataset ref")
    source_uri: str | None = Field(None, description="Public URL or local path")
    source_year: int | None = None
    source_author: str | None = None
    provenance_sidecar_ref: str | None = Field(None, description="Path to ProvenanceSidecar artifact")

    # Companion MCP resource URI
    resource_uri: str | None = Field(None, description="e.g. 'geox://layers/sabah.basin_outline.v3'")
    resource_size_bytes: int | None = None

    # Governance
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    registered_by: str = "geox"
    version: str = "1.0.0"
    deprecated: bool = False
    superseded_by: str | None = None

    # MARUAH check — community territory flag
    community_territory_flag: bool = False
    community_territory_note: str | None = None

    @field_validator("layer_id")
    @classmethod
    def _layer_id_slug(cls, v: str) -> str:
        if not v or not v.replace(".", "").replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"layer_id must be alphanumeric slug: got '{v}'")
        return v

    def in_bbox(self, west: float, east: float, south: float, north: float) -> bool:
        """True if this layer's bbox intersects the query bbox."""
        w = self.bbox_west
        e = self.bbox_east
        s = self.bbox_south
        n = self.bbox_north
        if w is None or e is None or s is None or n is None:
            return True  # global layer — always intersects
        return not (east < w or west > e or north < s or south > n)

    def allowed_for(self, map_purpose: str) -> bool:
        """Truth-class gate for the requested map purpose."""
        allowed_classes = MAP_PURPOSE_ALLOW.get(map_purpose, set())
        return self.truth_class in allowed_classes

    def license_allowed_for(self, map_purpose: str) -> bool:
        """License gate — some licenses can't go to publication or prospect_review."""
        allowed_licenses = LICENSE_ALLOW.get(map_purpose, set())
        return self.license in allowed_licenses

    def governance_gate(self, map_purpose: str, bbox: list[float] | None = None) -> tuple[bool, list[str]]:
        """Run all governance checks. Returns (passes, list_of_block_reasons)."""
        blockers: list[str] = []
        if self.deprecated:
            blockers.append(f"Layer deprecated; superseded_by={self.superseded_by}")
        if not self.allowed_for(map_purpose):
            blockers.append(f"Truth class '{self.truth_class.value}' not allowed for map_purpose='{map_purpose}'")
        if not self.license_allowed_for(map_purpose):
            blockers.append(f"License '{self.license.value}' not allowed for map_purpose='{map_purpose}'")
        if bbox and len(bbox) == 4:
            if not self.in_bbox(*bbox):
                blockers.append("Layer bbox does not intersect query bbox")
        if self.community_territory_flag and map_purpose in ("publication", "prospect_review"):
            blockers.append(
                f"F6 MARUAH: layer flagged for community territory — review required before publication/prospect_review. Note: {self.community_territory_note}"
            )
        if self.truth_class == TruthClass.DECISION_SUPPORT and not self.provenance_sidecar_ref:
            blockers.append("DECISION_SUPPORT layers require a ProvenanceSidecar reference")
        return (len(blockers) == 0, blockers)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


# ─────────────────────────────────────────────────────────────────────────────
# Registry — the catalogue
# ─────────────────────────────────────────────────────────────────────────────


class EarthLayerRegistry(BaseModel):
    """In-memory catalogue of GEOX layers.

    Backs `geox_map_layers_list` and `geox://layers/*` MCP resources.
    Seeded with a few canonical Sabah/SE-Asia layers for testing.
    """

    layers: dict[str, EarthLayer] = Field(default_factory=dict)
    registry_version: str = "1.0.0"
    registry_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def register(self, layer: EarthLayer) -> tuple[bool, str]:
        """Register a layer. Returns (success, message)."""
        if layer.layer_id in self.layers:
            return False, f"Layer '{layer.layer_id}' already registered"
        self.layers[layer.layer_id] = layer
        return True, f"Registered layer '{layer.layer_id}'"

    def deprecate(self, layer_id: str, superseded_by: str | None = None) -> tuple[bool, str]:
        if layer_id not in self.layers:
            return False, f"Layer '{layer_id}' not found"
        self.layers[layer_id].deprecated = True
        if superseded_by:
            self.layers[layer_id].superseded_by = superseded_by
        return True, f"Deprecated layer '{layer_id}'"

    def get(self, layer_id: str) -> EarthLayer | None:
        return self.layers.get(layer_id)

    def list(self) -> dict[str, EarthLayer]:
        """Return all registered layers keyed by layer_id.

        Public read-only snapshot — used by the MCP resource router
        `geox://layers/index` to surface discoverability without
        mutating the registry.
        """
        return dict(self.layers)

    def list_for_bbox(
        self,
        bbox: list[float],
        theme: str | None = None,
        map_purpose: str = "context",
        include_unavailable: bool = False,
    ) -> tuple[list[EarthLayer], list[dict[str, Any]]]:
        """Return layers in bbox, optionally filtered by theme.

        Returns (available_layers, unavailable_with_reasons).
        Mirrors geox_map_layers_list signature.
        """
        available: list[EarthLayer] = []
        unavailable: list[dict[str, Any]] = []
        for layer in self.layers.values():
            if layer.deprecated and not include_unavailable:
                continue
            if theme and layer.theme != theme:
                continue
            passes, blockers = layer.governance_gate(map_purpose=map_purpose, bbox=bbox)
            if passes:
                if layer.in_bbox(*bbox):
                    available.append(layer)
            else:
                if include_unavailable:
                    unavailable.append({"layer_id": layer.layer_id, "blockers": blockers})
        return available, unavailable

    def export_package(self, layer_id: str) -> dict[str, Any] | None:
        """Build an exportable package descriptor for a layer.

        This is the data shape returned by `geox://layers/{layer_id}/package`
        MCP resource. NOT a new tool — surfaces through the resource router.

        Top-level shape exposes canonical consumer keys (`layer_id`, `title`,
        `license`, `truth_class`, `bbox`, `governance`, `f_loors`) alongside
        the nested `layer` and `constitutional` envelopes for full fidelity.
        """
        layer = self.get(layer_id)
        if not layer:
            return None
        constitutional = {
            "F1_amanah": bool(layer.provenance_sidecar_ref or layer.source_uri),
            "F2_truth": layer.truth_class.value,
            "F6_maruah": "FLAGGED" if layer.community_territory_flag else "CLEAR",
            "F11_audit": True,
        }
        governance = {
            "truth_class": layer.truth_class.value,
            "license": layer.license.value,
            "community_territory_flag": layer.community_territory_flag,
            "f2_truth": constitutional["F2_truth"],
            "f6_maruah": constitutional["F6_maruah"],
        }
        bbox: list[float] | None = None
        if (
            layer.bbox_west is not None
            and layer.bbox_east is not None
            and layer.bbox_south is not None
            and layer.bbox_north is not None
        ):
            bbox = [layer.bbox_west, layer.bbox_south, layer.bbox_east, layer.bbox_north]
        return {
            "package_format": "GEOX-LAYER-PKG-v1",
            "layer": layer.to_dict(),
            # Flat consumer keys (canonical contract per conformance spine v1)
            "layer_id": layer.layer_id,
            "title": layer.name,
            "license": layer.license.value,
            "truth_class": layer.truth_class.value,
            "bbox": bbox,
            "governance": governance,
            "f_loors": constitutional,
            "checksum_algorithm": "sha256",
            "exported_at": datetime.now(UTC).isoformat(),
            "audit_id": f"geox.layer.audit.{uuid4()}",
            "constitutional": constitutional,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Seed factory — Sabah + SE Asia reference layers for tests
# ─────────────────────────────────────────────────────────────────────────────


def seed_sabah_layers() -> EarthLayerRegistry:
    """Seed a registry with canonical Sabah/SE-Asia reference layers.

    These layers back the geox_map_layers_list tool and the
    geox://layers/* MCP resources. Real layer data comes from upstream
    sources (USGS, NOC-A, NPD, BP, etc.) — this seed is for tests
    and demo scenes.
    """
    reg = EarthLayerRegistry()
    reg.register(
        EarthLayer(
            layer_id="sabah.basin_outline.v3",
            name="Sabah Basin Outlines",
            description="Major sedimentary basins of Sabah (NOC-A open data v3)",
            theme="sabah_regional",
            layer_type="vector_polygon",
            truth_class=TruthClass.INTERPRETATION,
            license=License.GOV_OPEN_DATA,
            bbox_west=115.5,
            bbox_east=119.5,
            bbox_south=4.0,
            bbox_north=7.5,
            source_id="NOC-A-Sabah-Basin-v3",
            source_uri="https://data.example.gov.my/sabah-basin-v3.geojson",
            source_year=2024,
            source_author="NOC-A Upstream",
            resource_uri="geox://layers/sabah.basin_outline.v3",
            provenance_sidecar_ref=None,
        )
    )
    reg.register(
        EarthLayer(
            layer_id="sabah.faults.v2",
            name="Sabah Structural Faults",
            description="Major fault traces from seismic + outcrop integration",
            theme="structure",
            layer_type="vector_line",
            truth_class=TruthClass.INTERPRETATION,
            license=License.CC_BY,
            bbox_west=115.5,
            bbox_east=119.5,
            bbox_south=4.0,
            bbox_north=7.5,
            source_id="Tongkul-2017-faults",
            source_uri="https://doi.org/10.xxxx/tongkul2017",
            source_year=2017,
            source_author="Tongkul F.",
            provenance_sidecar_ref="forge://sidecars/sabah.faults.v2.json",
            resource_uri="geox://layers/sabah.faults.v2",
        )
    )
    reg.register(
        EarthLayer(
            layer_id="se_asia.plates.v1",
            name="SE Asia Tectonic Plates",
            description="Major tectonic plates and microplates (Bird 2003, public domain)",
            theme="tectonics",
            layer_type="vector_polygon",
            truth_class=TruthClass.OBSERVATION,
            license=License.PUBLIC_DOMAIN,
            bbox_west=90.0,
            bbox_east=160.0,
            bbox_south=-15.0,
            bbox_north=30.0,
            source_id="Bird-2003",
            source_uri="https://pubs.usgs.gov/of/2003/ofr03039/",
            source_year=2003,
            source_author="Bird R.T. (USGS)",
            provenance_sidecar_ref="forge://sidecars/se_asia.plates.v1.json",
            resource_uri="geox://layers/se_asia.plates.v1",
        )
    )
    reg.register(
        EarthLayer(
            layer_id="sabah.kinabalu_velocity.v1",
            name="Kinabalu Velocity Anomaly",
            description="Velocity pull-up anomaly around Mt Kinabalu — FALSIFIED 2026-06-29",
            theme="sabah_regional",
            layer_type="raster",
            truth_class=TruthClass.HYPOTHESIS,  # demoted from INTERPRETATION after falsification
            license=License.PROPRIETARY,
            bbox_west=116.0,
            bbox_east=116.7,
            bbox_south=5.7,
            bbox_north=6.5,
            source_id="kinabalu-falsification-lc001",
            source_uri="forge_work/KINABALU-LAYANG-BASEMENT-FALSIFICATION-LC001-2026-06-29.md",
            source_year=2026,
            provenance_sidecar_ref="forge://sidecars/sabah.kinabalu_velocity.v1.json",
            community_territory_flag=True,
            community_territory_note="Kinabalu Park UNESCO World Heritage + indigenous Dusun/Kadazan territories — review required before publication.",
            resource_uri="geox://layers/sabah.kinabalu_velocity.v1",
        )
    )
    return reg


# ─────────────────────────────────────────────────────────────────────────────
# Module-level self-test
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import json

    reg = seed_sabah_layers()
    print(f"Seeded {len(reg.layers)} layers")

    sabah_bbox = [115.5, 119.5, 4.0, 7.5]
    print("\n--- context scene, Sabah bbox ---")
    avail, unavail = reg.list_for_bbox(sabah_bbox, map_purpose="context")
    print(f"available={len(avail)} unavailable={len(unavail)}")
    for layer in avail:
        print(f"  - {layer.layer_id} ({layer.truth_class.value}, {layer.license.value})")

    print("\n--- publication scene, Sabah bbox ---")
    avail, unavail = reg.list_for_bbox(sabah_bbox, map_purpose="publication")
    print(f"available={len(avail)} unavailable={len(unavail)}")
    for u in unavail:
        print(f"  BLOCKED {u['layer_id']}: {u['blockers']}")

    print("\n--- Kinabalu export package ---")
    pkg = reg.export_package("sabah.kinabalu_velocity.v1")
    print(json.dumps(pkg, indent=2, default=str) if pkg else "NOT FOUND")
