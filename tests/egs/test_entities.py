"""
test_entities.py — EGS Typed Earth Graph Tests

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import pytest

from geox.egs.models.entities import (
    Basin,
    EarthGraph,
    Fault,
    Horizon,
    Play,
    Point3D,
    StratUnit,
    SurfaceMesh3D,
    Survey,
    Volume,
    Well,
)


class TestPoint3D:
    def test_create_point(self):
        p = Point3D(x=100.0, y=200.0, z=-1500.0)
        assert p.x == 100.0
        assert p.y == 200.0
        assert p.z == -1500.0
        assert p.crs == "EPSG:4326"
        assert p.domain == "depth_m"

    def test_different_crs(self):
        p = Point3D(x=500000, y=200000, z=0, crs="EPSG:32750", domain="tvdss_m")
        assert p.crs == "EPSG:32750"
        assert p.domain == "tvdss_m"


class TestSurfaceMesh3D:
    def test_create_mesh(self):
        vertices = [
            Point3D(x=0, y=0, z=0),
            Point3D(x=1, y=0, z=0),
            Point3D(x=0, y=1, z=0),
            Point3D(x=1, y=1, z=0),
        ]
        triangles = [(0, 1, 2), (1, 3, 2)]
        mesh = SurfaceMesh3D(vertices=vertices, triangles=triangles)
        assert mesh.num_vertices == 4
        assert mesh.num_triangles == 2

    def test_invalid_triangle(self):
        vertices = [Point3D(x=0, y=0, z=0)]
        with pytest.raises(ValueError):
            SurfaceMesh3D(vertices=vertices, triangles=[(0,)])

    def test_negative_index(self):
        vertices = [Point3D(x=0, y=0, z=0)]
        with pytest.raises(ValueError, match="Negative"):
            SurfaceMesh3D(vertices=vertices, triangles=[(-1, 0, 1)])


class TestBasin:
    def test_create_basin(self):
        basin = Basin(
            name="Malay Basin",
            description="Tertiary rift basin",
            bounding_box=(100.0, 2.0, 105.0, 6.0),
            age_range_ma=(65.0, 0.0),
            basin_type="rift",
            tectonic_setting="extensional",
        )
        assert basin.entity_type == "basin"
        assert basin.name == "Malay Basin"
        assert basin.age_range_ma == (65.0, 0.0)
        assert len(basin.id) == 16

    def test_basin_defaults(self):
        basin = Basin(name="Test Basin")
        assert basin.active is True
        assert basin.version == 1
        assert basin.tags == []


class TestStratUnit:
    def test_create_strat_unit(self):
        unit = StratUnit(
            name="Group A",
            basin_id="basin_001",
            rank="group",
            age_top_ma=50.0,
            age_base_ma=65.0,
            lithology="sandstone",
            environment="fluvial",
        )
        assert unit.entity_type == "strat_unit"
        assert unit.age_top_ma == 50.0
        assert unit.age_base_ma == 65.0

    def test_contact_defaults(self):
        unit = StratUnit(name="Unit X", basin_id="b1")
        assert unit.contact_above.value == "unknown"
        assert unit.contact_below.value == "unknown"


class TestHorizon:
    def test_create_horizon(self):
        horizon = Horizon(
            name="Top Reservoir",
            basin_id="basin_001",
            strat_unit_id="unit_001",
            interpretation_type="seismic",
            interpreter="Arif",
            confidence=0.85,
        )
        assert horizon.entity_type == "horizon"
        assert horizon.confidence == 0.85


class TestFault:
    def test_create_fault(self):
        fault = Fault(
            name="Fault A",
            basin_id="basin_001",
            fault_type="normal",
            dip_deg=60.0,
            strike_deg=045.0,
            throw_m=50.0,
        )
        assert fault.fault_type == "normal"
        assert fault.dip_deg == 60.0


class TestWell:
    def test_create_well(self):
        well = Well(
            name="Well-001",
            basin_id="basin_001",
            uwi="123456789000",
            total_depth_m=2500.0,
            status="active",
            well_type="exploration",
        )
        assert well.uwi == "123456789000"
        assert well.total_depth_m == 2500.0


class TestEarthGraph:
    def test_empty_graph(self):
        g = EarthGraph()
        assert len(g.basins) == 0
        assert g.version == 1

    def test_add_basin(self):
        g = EarthGraph()
        basin = Basin(name="Test Basin")
        bid = g.add_entity(basin)
        assert bid == basin.id
        assert len(g.basins) == 1
        assert g.version > 1

    def test_add_multiple_types(self):
        g = EarthGraph()
        b = Basin(name="Basin")
        s = StratUnit(name="Unit", basin_id=b.id)
        h = Horizon(name="Horizon", basin_id=b.id)
        f = Fault(name="Fault", basin_id=b.id)
        w = Well(name="Well", basin_id=b.id)
        v = Volume(name="Volume", basin_id=b.id)
        surv = Survey(name="Survey", basin_id=b.id)
        p = Play(name="Play", basin_id=b.id)

        g.add_entity(b)
        g.add_entity(s)
        g.add_entity(h)
        g.add_entity(f)
        g.add_entity(w)
        g.add_entity(v)
        g.add_entity(surv)
        g.add_entity(p)

        assert len(g.basins) == 1
        assert len(g.strat_units) == 1
        assert len(g.horizons) == 1
        assert len(g.faults) == 1
        assert len(g.wells) == 1
        assert len(g.volumes) == 1
        assert len(g.surveys) == 1
        assert len(g.plays) == 1

    def test_get_entity(self):
        g = EarthGraph()
        b = Basin(name="FindMe")
        g.add_entity(b)
        found = g.get_entity(b.id)
        assert found is not None
        assert found.name == "FindMe"

    def test_get_entity_not_found(self):
        g = EarthGraph()
        assert g.get_entity("nonexistent") is None

    def test_remove_entity(self):
        g = EarthGraph()
        b = Basin(name="ToRemove")
        g.add_entity(b)
        assert g.remove_entity(b.id) is True
        assert b.active is False

    def test_remove_nonexistent(self):
        g = EarthGraph()
        assert g.remove_entity("xxx") is False
