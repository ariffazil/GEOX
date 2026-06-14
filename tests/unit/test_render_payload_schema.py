"""
RenderPayload Schema Tests — Binary Transport Contracts
=========================================================
Tests the canonical render contracts for the GEOX Visual Engine.

Covers:
  - RenderPayload serialization/validation
  - CubeManifest brick grid computation
  - render_map / render_surface / render_cube_slice builders
  - BinaryResource MCP URI contract
  - LOD pyramid metadata

DITEMPA BUKAN DIBERI
"""

import json
import pytest
from pydantic import ValidationError

from geox_core.schemas.render_payload import (
    BinaryResource,
    BrickAddress,
    BrickResource,
    CRSInfo,
    CubeManifest,
    GeometryType,
    LODInfo,
    LodLevel,
    RenderModality,
    RenderPayload,
    render_cube_slice,
    render_map,
    render_surface,
)


class TestRenderPayloadBasics:
    """RenderPayload must serialize and validate correctly."""

    def test_minimal_render_payload(self):
        """A minimal RenderPayload with only modality and render_type must work."""
        rp = RenderPayload(modality=RenderModality.MAP, render_type="test_map")
        d = rp.model_dump(mode="json")
        assert d["modality"] == "map"
        assert d["render_type"] == "test_map"
        assert d["claim_tag"] == "HYPOTHESIS"  # default
        assert d["arifos_verdict"] == "QUALIFY"  # default
        assert d["render_id"].startswith("geox-render-")
        assert d["visual_artifact_id"].startswith("sha256:geox-render-")

    def test_render_payload_with_geojson(self):
        """RenderPayload with inline GeoJSON must carry it correctly."""
        geojson = {"type": "FeatureCollection", "features": []}
        rp = RenderPayload(
            modality=RenderModality.MAP,
            render_type="basin_map",
            inline_geojson=geojson,
            claim_tag="OBSERVED",
        )
        d = rp.model_dump(mode="json")
        assert d["claim_tag"] == "OBSERVED"
        assert d["inline_geojson"]["type"] == "FeatureCollection"

    def test_render_payload_with_crs(self):
        """CRSInfo must serialize correctly."""
        rp = RenderPayload(
            modality=RenderModality.SURFACE,
            render_type="horizon_mesh",
            crs=CRSInfo(horizontal="EPSG:3168", vertical="EPSG:5703", depth_basis="TVDSS", depth_datum="MSL"),
        )
        d = rp.model_dump(mode="json")
        assert d["crs"]["horizontal"] == "EPSG:3168"
        assert d["crs"]["depth_basis"] == "TVDSS"

    def test_render_payload_invalid_modality(self):
        """Invalid modality must raise ValidationError."""
        with pytest.raises(ValidationError):
            RenderPayload(modality="invalid_modality", render_type="test")

    def test_render_payload_acrisk_bounds(self):
        """ACRisk score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            RenderPayload(modality=RenderModality.MAP, render_type="test", acrisk_score=1.5)

    def test_render_payload_serializes_to_json(self):
        """RenderPayload.model_dump_json() must produce valid JSON."""
        rp = RenderPayload(modality=RenderModality.CUBE_SLICE, render_type="inline_2450")
        j = rp.model_dump_json()
        loaded = json.loads(j)
        assert loaded["modality"] == "cube_slice"
        assert loaded["render_type"] == "inline_2450"

    def test_binary_resource_contract(self):
        """BinaryResource must carry all critical fields."""
        br = BinaryResource(
            resource_uri="geox://render/surfaces/horizon_A.npz",
            geometry_type=GeometryType.NUMPY_NPZ,
            shape=[200, 150],
            dtype="float32",
        )
        d = br.model_dump(mode="json")
        assert d["resource_uri"] == "geox://render/surfaces/horizon_A.npz"
        assert d["geometry_type"] == "numpy_npz"
        assert d["shape"] == [200, 150]
        assert d["dtype"] == "float32"
        assert d["lod"] == "full"


class TestCubeManifest:
    """CubeManifest must describe the brick grid correctly."""

    def test_minimal_cube_manifest(self):
        """A minimal CubeManifest with required fields."""
        cm = CubeManifest(
            cube_id="CUBE-001",
            dims=[500, 400, 300],
            bbox_origin=[1000, 2000, 0],
            bbox_max=[1500, 2400, 1200],
        )
        d = cm.model_dump(mode="json")
        assert d["cube_id"] == "CUBE-001"
        assert d["dims"] == [500, 400, 300]
        assert d["brick_shape"] == [64, 64, 64]  # default
        assert d["lod_count"] == 1  # default
        assert d["primary_attribute"] == "amplitude"  # default
        assert d["claim_tag"] == "COMPUTED"

    def test_cube_manifest_with_lods(self):
        """CubeManifest with LOD pyramid must carry per-LOD info."""
        cm = CubeManifest(
            cube_id="CUBE-002",
            dims=[1000, 800, 600],
            lod_count=3,
            lods=[
                LODInfo(level=0, stride=8, brick_shape=[64, 64, 64], data_type="uint8", compression="wavelet"),
                LODInfo(level=1, stride=4, brick_shape=[64, 64, 64], data_type="int16", compression="zstd"),
                LODInfo(level=2, stride=1, brick_shape=[64, 64, 64], data_type="float32", compression="none"),
            ],
        )
        d = cm.model_dump(mode="json")
        assert d["lod_count"] == 3
        assert len(d["lods"]) == 3
        assert d["lods"][0]["compression"] == "wavelet"
        assert d["lods"][1]["stride"] == 4
        assert d["lods"][2]["data_type"] == "float32"

    def test_brick_uri_template(self):
        """Brick URI template must contain all substitution variables."""
        cm = CubeManifest(
            cube_id="CUBE-003",
            dims=[500, 400, 300],
        )
        template = cm.brick_uri_template
        assert "{cube_id}" in template
        assert "{lod}" in template
        assert "{ix}" in template
        assert "{iy}" in template
        assert "{iz}" in template

    def test_brick_resource_contract(self):
        """BrickResource must carry address, LOD, and resource_uri."""
        br = BrickResource(
            brick=BrickAddress(ix=2, iy=5, iz=10),
            lod=1,
            resource_uri="geox://render/cubes/CUBE-001/lod/1/brick/2/5/10",
            byte_length=262144,
            data_type="int16",
        )
        d = br.model_dump(mode="json")
        assert d["brick"]["ix"] == 2
        assert d["brick"]["iz"] == 10
        assert d["lod"] == 1
        assert d["byte_length"] == 262144


class TestRenderBuilders:
    """Convenience builders must produce valid RenderPayloads."""

    def test_render_map_builder(self):
        """render_map() produces a valid map RenderPayload."""
        geojson = {"type": "FeatureCollection", "features": []}
        rp = render_map(geojson=geojson, bbox=[102, 3, 103, 4], claim_tag="OBSERVED")
        d = rp.model_dump(mode="json")
        assert d["modality"] == "map"
        assert d["render_type"] == "geojson_map"
        assert d["inline_geojson"]["type"] == "FeatureCollection"
        assert d["claim_tag"] == "OBSERVED"
        assert d["bbox"]["min_x"] == 102

    def test_render_surface_builder(self):
        """render_surface() produces a valid surface RenderPayload."""
        rp = render_surface(
            resource_uri="geox://render/surfaces/horizon_A.npz",
            shape=[200, 150],
            claim_tag="INTERPRETED",
        )
        d = rp.model_dump(mode="json")
        assert d["modality"] == "surface"
        assert d["render_type"] == "horizon_mesh"
        assert len(d["resources"]) == 1
        assert d["resources"][0]["resource_uri"] == "geox://render/surfaces/horizon_A.npz"

    def test_render_cube_slice_builder(self):
        """render_cube_slice() produces a valid cube_slice RenderPayload."""
        rp = render_cube_slice(
            resource_uri="geox://render/cubes/CUBE-001/lod/0/brick/0/0/0",
            shape=[64, 64],
            orientation="inline",
            slice_index=2450,
        )
        d = rp.model_dump(mode="json")
        assert d["modality"] == "cube_slice"
        assert d["render_type"] == "inline_slice_amplitude"
        assert len(d["resources"]) == 1
