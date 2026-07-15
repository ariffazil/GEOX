"""
test_engines.py — EGS Engine Tests

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import math

import pytest

from geox.egs.engines.geometry import (
    SpatialIndex,
    bounding_box_area,
    bounding_box_contains,
    bounding_box_intersects,
    euclidean_distance_3d,
    haversine_distance,
    mesh_bounding_box,
    mesh_center,
    vertical_distance,
)
from geox.egs.engines.physics import (
    acoustic_impedance,
    brine_density,
    castagna_mudrock_vp_to_vs,
    elastic_impedance,
    gardner_vp_to_rho,
    gas_density,
    oil_density,
    voigt_reuss_hill,
)
from geox.egs.models.entities import Point3D, SurfaceMesh3D


class TestGeometry:
    def test_haversine_distance(self):
        # Kuala Lumpur to Singapore (approx)
        kl = Point3D(x=101.6869, y=3.1390, z=0)
        sg = Point3D(x=103.8198, y=1.3521, z=0)
        dist = haversine_distance(kl, sg)
        # ~300km
        assert 250_000 < dist < 400_000

    def test_euclidean_distance_3d(self):
        p1 = Point3D(x=0, y=0, z=0)
        p2 = Point3D(x=3, y=4, z=12)
        assert euclidean_distance_3d(p1, p2) == 13.0

    def test_vertical_distance(self):
        p1 = Point3D(x=0, y=0, z=100)
        p2 = Point3D(x=10, y=10, z=250)
        assert vertical_distance(p1, p2) == 150.0

    def test_bounding_box_contains(self):
        bbox = (100.0, 2.0, 105.0, 6.0)
        inside = Point3D(x=102.5, y=4.0, z=0)
        outside = Point3D(x=106.0, y=1.0, z=0)
        assert bounding_box_contains(bbox, inside) is True
        assert bounding_box_contains(bbox, outside) is False

    def test_bounding_box_intersects(self):
        b1 = (0, 0, 10, 10)
        b2 = (5, 5, 15, 15)
        b3 = (20, 20, 30, 30)
        assert bounding_box_intersects(b1, b2) is True
        assert bounding_box_intersects(b1, b3) is False

    def test_bounding_box_area(self):
        bbox = (100, 0, 101, 1)  # ~1 deg x 1 deg
        area = bounding_box_area(bbox)
        assert 10_000 < area < 15_000  # approx 12321 sq km

    def test_mesh_bounding_box(self):
        mesh = SurfaceMesh3D(
            vertices=[
                Point3D(x=0, y=0, z=0),
                Point3D(x=10, y=5, z=-100),
                Point3D(x=5, y=10, z=-50),
            ],
            triangles=[(0, 1, 2)],
        )
        bb = mesh_bounding_box(mesh)
        assert bb == (0, 10, 0, 10, -100, 0)

    def test_mesh_center(self):
        mesh = SurfaceMesh3D(
            vertices=[
                Point3D(x=0, y=0, z=0),
                Point3D(x=10, y=0, z=0),
                Point3D(x=0, y=10, z=0),
            ],
            triangles=[(0, 1, 2)],
        )
        center = mesh_center(mesh)
        assert center is not None
        assert center.x == pytest.approx(10 / 3)
        assert center.y == pytest.approx(10 / 3)

    def test_empty_mesh_center(self):
        mesh = SurfaceMesh3D(vertices=[], triangles=[])
        assert mesh_center(mesh) is None


class TestSpatialIndex:
    def test_add_and_query_radius(self):
        idx = SpatialIndex()
        p1 = Point3D(x=101.0, y=3.0, z=0)
        p2 = Point3D(x=102.0, y=4.0, z=0)
        idx.add("loc_a", p1)
        idx.add("loc_b", p2)

        center = Point3D(x=101.0, y=3.0, z=0)
        results = idx.query_radius(center, radius_m=500_000)
        assert len(results) == 2

        # Tight radius should find only one
        tight = idx.query_radius(center, radius_m=1000)
        assert len(tight) == 1

    def test_query_bbox(self):
        idx = SpatialIndex()
        idx.add("a", Point3D(x=101, y=3, z=0))
        idx.add("b", Point3D(x=102, y=4, z=0))
        idx.add("c", Point3D(x=110, y=10, z=0))
        results = idx.query_bbox((100, 2, 105, 5))
        assert len(results) == 2


class TestPhysics:
    def test_gardner_vp_to_rho(self):
        # Sandstone at 3500 m/s
        rho = gardner_vp_to_rho(3500)
        assert 2.3 < rho < 2.5

    def test_castagna_vp_to_vs(self):
        # Mudrock line
        vs = castagna_mudrock_vp_to_vs(3000)
        assert 1400 < vs < 1420

    def test_acoustic_impedance(self):
        ai = acoustic_impedance(3500, 2.35)
        assert ai == pytest.approx(8225.0)

    def test_elastic_impedance(self):
        ei = elastic_impedance(3500, 1800, 2.35, chi=0.3)
        assert ei > 0

    def test_brine_density(self):
        rho = brine_density(80, 35000, 30)
        assert 1.0 < rho < 1.2

    def test_oil_density(self):
        rho = oil_density(35, 100, 80, 30)
        assert 0.6 < rho < 0.9

    def test_gas_density(self):
        rho = gas_density(80, 10, 0.6)  # 10 MPa (shallow gas)
        assert 0.05 < rho < 0.5

    def test_vrh(self):
        result = voigt_reuss_hill(
            vp_mineral=5500,
            vp_fluid=1500,
            phi=0.2,
            rho_mineral=2.65,
            rho_fluid=1.0,
        )
        assert result["vp_voigt_m_s"] > result["vp_hill_m_s"] > result["vp_reuss_m_s"]
        assert result["rho_bulk_g_cc"] > 1.0
