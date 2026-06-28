"""
test_update_ops.py — EGS Update Operator Tests

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from geox.egs.engines.update_ops import (
    UpdateFaultModel,
    UpdateHorizonGeom,
    UpdateReservoirProperties,
    UpdateStratColumn,
)
from geox.egs.models.entities import (
    Basin,
    EarthGraph,
    Fault,
    Horizon,
    StratUnit,
)
from geox.egs.models.provenance import ProvenanceAgentKind


def _make_graph_with_basin() -> EarthGraph:
    g = EarthGraph()
    g.add_entity(Basin(name="Test Basin", id="basin_001"))
    return g


class TestUpdateStratColumn:
    def test_add_units(self):
        g = _make_graph_with_basin()
        units = [
            StratUnit(name="Unit A", basin_id="basin_001", age_top_ma=50, age_base_ma=65),
            StratUnit(name="Unit B", basin_id="basin_001", age_top_ma=30, age_base_ma=50),
        ]
        op = UpdateStratColumn(basin_id="basin_001", units=units)
        result = op.execute(g)
        assert result.success is True
        assert result.entity_id == "basin_001"
        assert len(g.strat_units) == 2

    def test_basin_not_found(self):
        g = EarthGraph()
        op = UpdateStratColumn(
            basin_id="nonexistent",
            units=[StratUnit(name="A", basin_id="nonexistent")],
        )
        result = op.execute(g)
        assert result.success is False
        assert len(result.errors) > 0

    def test_replace_all(self):
        g = _make_graph_with_basin()
        units = [StratUnit(name="Old A", basin_id="basin_001")]
        op = UpdateStratColumn(basin_id="basin_001", units=units)
        op.execute(g)
        assert len(g.strat_units) == 1

        # Replace with new units
        new_units = [StratUnit(name="New A", basin_id="basin_001")]
        op2 = UpdateStratColumn(basin_id="basin_001", units=new_units, replace_all=True)
        op2.execute(g)
        # Old units should be inactive
        inactive = [u for u in g.strat_units.values() if not u.active]
        assert len(inactive) == 1


class TestUpdateHorizonGeom:
    def test_horizon_not_found(self):
        g = EarthGraph()
        op = UpdateHorizonGeom(horizon_id="nonexistent", surface_data={})
        result = op.execute(g)
        assert result.success is False

    def test_update_confidence(self):
        g = EarthGraph()
        h = Horizon(name="Top", basin_id="b1")
        g.add_entity(h)
        op = UpdateHorizonGeom(
            horizon_id=h.id,
            surface_data={},
            confidence=0.95,
        )
        result = op.execute(g)
        assert result.success is True
        assert result.new_version is not None


class TestUpdateFaultModel:
    def test_add_faults(self):
        g = _make_graph_with_basin()
        faults = [
            Fault(name="Fault 1", basin_id="basin_001", fault_type="normal"),
        ]
        op = UpdateFaultModel(basin_id="basin_001", faults=faults)
        result = op.execute(g)
        assert result.success is True
        assert len(g.faults) == 1

    def test_basin_not_found(self):
        g = EarthGraph()
        op = UpdateFaultModel(
            basin_id="nonexistent",
            faults=[Fault(name="F1", basin_id="nonexistent")],
        )
        result = op.execute(g)
        assert result.success is False


class TestUpdateReservoirProperties:
    def test_update(self):
        g = EarthGraph()
        unit = StratUnit(name="Reservoir", basin_id="b1")
        g.add_entity(unit)
        op = UpdateReservoirProperties(
            strat_unit_id=unit.id,
            agent="test",
            agent_kind=ProvenanceAgentKind.HUMAN,
        )
        result = op.execute(g)
        assert result.success is True
        assert result.provenance is not None
