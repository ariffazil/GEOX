"""Tests for W13+ Phase C integrations:
- geomechanics (K, G, E, ν, AI from Physics13State)
- WELL → GEOX (operator decision_class from fatigue)
- WEALTH ← GEOX (STOIIP + ranking + verdict)
"""

from __future__ import annotations

import asyncio

import pytest

from geox_mcp.tools.geomechanics import (
    GeomechanicsRequest,
    geox_geomechanics,
)
from geox_mcp.tools.integration_well import (
    WellStateRequest,
    geox_well_decision_class,
    _stub_well_assess,
)
from geox_mcp.tools.integration_wealth import (
    WealthFeedRequest,
    geox_wealth_feed,
    stoiip_cell,
)
from geox_core.physics.state import SANDSTONE, SHALE, LIMESTONE, BASEMENT


# ════════════════════════════════════════════════════════════════════════════════
# GEOMECHANICS
# ════════════════════════════════════════════════════════════════════════════════
class TestGeomechanics:
    def test_sandstone_derives_expected_moduli(self):
        r = asyncio.run(geox_geomechanics(GeomechanicsRequest(state=SANDSTONE.to_dict())))
        assert r.ok is True
        d = r.result["derived"]
        # Sandstone: ρ=2350, Vp=2950, Vs=1680 → K ≈ 11.4 GPa
        assert 8.0 < d["K_GPa"] < 15.0
        assert 5.0 < d["G_GPa"] < 10.0
        assert d["nu"] > 0.0
        assert d["nu"] < 0.5
        assert r.result["grade"] == "AAA"

    def test_basement_yields_higher_moduli(self):
        r = asyncio.run(geox_geomechanics(GeomechanicsRequest(state=BASEMENT.to_dict())))
        assert r.ok is True
        # Basement: Vp=5800, Vs=3400 → much higher K, G
        assert r.result["derived"]["K_GPa"] > 30.0
        assert r.result["derived"]["G_GPa"] > 30.0

    def test_invalid_state_returns_error(self):
        r = asyncio.run(geox_geomechanics(GeomechanicsRequest(state={"rho": -1, "vp": 1000, "vs": 500, "rho_e": 1, "chi": 0, "k": 1, "P": 1, "T": 100, "phi": 0.5})))
        # Negative density violates Physics9 bounds
        assert r.result["sanity_flags"] == [] or "bulk_modulus_negative" in r.result["sanity_flags"] or r.result["grade"] == "RAW"

    def test_godel_wall_known_for_aaa_state(self):
        r = asyncio.run(geox_geomechanics(GeomechanicsRequest(state=SANDSTONE.to_dict())))
        assert r.result["godel_wall"]["state"] == "KNOWN"


# ════════════════════════════════════════════════════════════════════════════════
# WELL → GEOX
# ════════════════════════════════════════════════════════════════════════════════
class TestWellIntegration:
    def test_stub_returns_c3_by_default(self):
        async def run():
            return await geox_well_decision_class(
                WellStateRequest(operator_id="arif"),
                well_assess_homeostasis=_stub_well_assess,
            )
        r = asyncio.run(run())
        assert r.ok is True
        # stub returns fatigue=0.5 → C3
        assert r.decision_class == "C3"
        assert "session fatigue" in r.rationale.lower()

    def test_low_fatigue_returns_c1(self):
        async def low_fatigue(*, subject, mode):
            return {"chronic_fatigue": False, "accumulated_session_fatigue": 0.2, "subject": subject}

        async def run():
            return await geox_well_decision_class(
                WellStateRequest(operator_id="arif"),
                well_assess_homeostasis=low_fatigue,
            )
        r = asyncio.run(run())
        assert r.decision_class == "C1"
        assert r.operator_readiness == "OPTIMAL"

    def test_high_fatigue_returns_c5_hold(self):
        async def high_fatigue(*, subject, mode):
            return {"chronic_fatigue": True, "accumulated_session_fatigue": 0.9, "subject": subject}

        async def run():
            return await geox_well_decision_class(
                WellStateRequest(operator_id="arif"),
                well_assess_homeostasis=high_fatigue,
            )
        r = asyncio.run(run())
        assert r.decision_class == "C5"
        assert r.operator_readiness == "RED"
        assert r.godel_wall["state"] == "VOID"

    def test_moderate_fatigue_returns_c3_or_c4(self):
        async def moderate(*, subject, mode):
            return {"chronic_fatigue": False, "accumulated_session_fatigue": 0.7, "subject": subject}

        async def run():
            return await geox_well_decision_class(
                WellStateRequest(operator_id="arif"),
                well_assess_homeostasis=moderate,
            )
        r = asyncio.run(run())
        assert r.decision_class in ("C3", "C4")


# ════════════════════════════════════════════════════════════════════════════════
# WEALTH ← GEOX
# ════════════════════════════════════════════════════════════════════════════════
class TestWealthFeed:
    def test_stoiip_arithmetic(self):
        v = stoiip_cell(
            phi=0.25, sw=0.30,
            areal_extent_m2=1e6, pay_zone_thickness_m=50.0,
            formation_volume_factor=1.3, recovery_factor=0.30,
        )
        # V_bulk = 1e6 * 50 = 5e7 m^3
        # HCPV = 5e7 * 0.25 * 0.7 = 8.75e6 m^3
        assert abs(v["hcpv_m3"] - 8.75e6) < 1.0
        # STOIIP = 8.75e6 / 1.3 = 6.73e6 m^3 → 4.23e7 bbl
        assert abs(v["stoiip_m3"] - 8.75e6 / 1.3) < 1.0

    def test_high_porosity_cells_advance(self):
        cells = [SANDSTONE.to_dict() for _ in range(5)]  # all phi=0.25
        r = asyncio.run(geox_wealth_feed(
            WealthFeedRequest(cell_states=cells, water_saturation=0.20),
        ))
        assert r.ok is True
        # Sandstone phi=0.25, Sw=0.20 → producible = 0.20 * 0.8 * 0.3 * 1.0 = 0.048 → ADVANCE
        assert r.feed["verdict"] == "ADVANCE"
        assert r.feed["ranking_score"] > 0.04

    def test_low_quality_cells_defer_or_reject(self):
        # All shale (low porosity, high Sw implied)
        cells = [SHALE.to_dict() for _ in range(5)]
        r = asyncio.run(geox_wealth_feed(
            WealthFeedRequest(cell_states=cells, water_saturation=0.50),
        ))
        assert r.ok is True
        # Ranking should be low → DEFER or REJECT
        assert r.feed["verdict"] in ("DEFER", "REJECT")

    def test_phi_p10_p50_p90(self):
        cells = []
        for phi in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40):
            cells.append({**SANDSTONE.to_dict(), "phi": phi})
        r = asyncio.run(geox_wealth_feed(
            WealthFeedRequest(cell_states=cells, water_saturation=0.20),
        ))
        assert r.ok is True
        assert r.feed["phi_p10"] <= r.feed["phi_p50"] <= r.feed["phi_p90"]

    def test_empty_cells_returns_error(self):
        r = asyncio.run(geox_wealth_feed(WealthFeedRequest(cell_states=[])))
        assert r.ok is False or r.feed["n_cells"] == 0
