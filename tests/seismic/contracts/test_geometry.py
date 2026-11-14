"""Tests for geometry primitives (VOI, VoxelMask, Polyline, Polygon, SurfaceMesh)."""
from __future__ import annotations

import pytest

from geox.seismic.contracts import (
    PointSet,
    Polygon,
    Polyline,
    SurfaceMesh,
    VOI,
    VoxelMask,
)


class TestVOI:
    def test_valid_voi(self):
        v = VOI(
            volume_ref="geox://volume/f3/raw",
            inline_range=(300, 400),
            xline_range=(500, 650),
            sample_range=(0, 1000),
        )
        assert v.inline_range == (300, 400)

    def test_invalid_range_rejected(self):
        with pytest.raises(ValueError):
            VOI(
                volume_ref="geox://volume/f3/raw",
                inline_range=(400, 300),  # start > end
                xline_range=(500, 650),
            )


class TestVoxelMask:
    def test_valid_mask(self):
        m = VoxelMask(
            mask_id="geox://artifact/chimney-mask-1",
            volume_ref="geox://volume/f3/raw",
            voi=VOI(volume_ref="geox://volume/f3/raw"),
            dtype="float32",
            threshold_applied=0.7,
            created_by="kimi-code/FI-008",
        )
        assert m.dtype == "float32"
        assert m.threshold_applied == 0.7

    def test_bool_mask_no_threshold_required(self):
        m = VoxelMask(
            mask_id="geox://artifact/mask-2",
            volume_ref="geox://volume/f3/raw",
            voi=VOI(volume_ref="geox://volume/f3/raw"),
            dtype="bool",
            created_by="kimi-code/FI-008",
        )
        assert m.threshold_applied is None


class TestPolyline:
    def test_valid_polyline(self):
        p = Polyline(
            polyline_id="geox://artifact/fault-stick-1",
            coordinate_frame="INLINE_XLINE_SAMPLE",
            points=[(100, 200, 300), (101, 201, 301), (102, 202, 302)],
            created_by="kimi-code/FI-008",
        )
        assert len(p.points) == 3

    def test_confidence_in_range(self):
        with pytest.raises(ValueError):
            Polyline(
                polyline_id="geox://artifact/fault-stick-1",
                coordinate_frame="INLINE_XLINE_SAMPLE",
                points=[(100, 200, 300), (101, 201, 301)],
                confidence=[0.95, 1.5],  # out of range
                created_by="kimi-code/FI-008",
            )

    def test_minimum_points(self):
        with pytest.raises(ValueError):
            Polyline(
                polyline_id="geox://artifact/single-point",
                coordinate_frame="INLINE_XLINE_SAMPLE",
                points=[(100, 200, 300)],  # need >= 2
                created_by="kimi-code/FI-008",
            )


class TestPolygon:
    def test_valid_polygon(self):
        p = Polygon(
            polygon_id="geox://artifact/geobody-footprint-1",
            coordinate_frame="INLINE_XLINE",
            vertices=[(100, 200), (300, 200), (300, 400), (100, 400)],
            created_by="kimi-code/FI-008",
        )
        assert len(p.vertices) == 4
        assert p.closed is True

    def test_minimum_vertices(self):
        with pytest.raises(ValueError):
            Polygon(
                polygon_id="geox://artifact/triangle-bad",
                coordinate_frame="INLINE_XLINE",
                vertices=[(100, 200), (300, 200)],  # need >= 3
                created_by="kimi-code/FI-008",
            )


class TestSurfaceMesh:
    def test_valid_mesh(self):
        s = SurfaceMesh(
            mesh_id="geox://artifact/horizon-1",
            coordinate_frame="INLINE_XLINE_TIME",
            vertices=[(100, 200, 1500.0), (300, 200, 1520.0), (100, 400, 1510.0), (300, 400, 1530.0)],
            faces=[(0, 1, 2), (1, 3, 2)],
            created_by="kimi-code/FI-008",
        )
        assert len(s.faces) == 2

    def test_face_indices_in_range(self):
        with pytest.raises(ValueError):
            SurfaceMesh(
                mesh_id="geox://artifact/horizon-bad",
                coordinate_frame="INLINE_XLINE_TIME",
                vertices=[(100, 200, 1500.0), (300, 200, 1520.0), (100, 400, 1510.0)],
                faces=[(0, 1, 5)],  # 5 out of range
                created_by="kimi-code/FI-008",
            )

    def test_alternative_paths_recorded(self):
        s = SurfaceMesh(
            mesh_id="geox://artifact/horizon-2",
            coordinate_frame="INLINE_XLINE_TIME",
            vertices=[(100, 200, 1500.0), (300, 200, 1520.0), (100, 400, 1510.0)],
            faces=[(0, 1, 2)],
            alternative_paths=["geox://artifact/horizon-2-alt-1"],
            stopped_regions=[{"region": "fault_block_3", "reason": "throw_exceeded_threshold"}],
            created_by="kimi-code/FI-008",
        )
        assert len(s.alternative_paths) == 1
        assert s.stopped_regions[0]["region"] == "fault_block_3"


class TestPointSet:
    def test_valid_pointset(self):
        p = PointSet(
            pointset_id="geox://artifact/seed-points-1",
            coordinate_frame="INLINE_XLINE_TIME",
            points=[(100, 200, 1500.0), (300, 400, 1520.0)],
            created_by="kimi-code/FI-008",
        )
        assert len(p.points) == 2
