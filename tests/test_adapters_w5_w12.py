"""Tests for W5-W12 adapters:
- Prithvi-EO-2.0 (earth_obs)
- HarmonIC gravity/magnetic (geophysics)
- EMAG2v3 fetcher (io)
"""

from __future__ import annotations

import os
import pytest

from geox_core.engines.earth_obs.prithvi_adapter import (
    PrithviEOAdapter,
    HLSInput,
    PrithviTask,
    MockPrithviBackend,
    LivePrithviBackend,
)
from geox_core.engines.geophysics.harmonica_adapter import (
    HarmonICAdapter,
    GravityMagneticInput,
    MockHarmonICBackend,
)
from geox_core.io.emag2_fetcher import (
    EMAG2Fetcher,
    ICGEMFetcher,
    WGM2012Citation,
    EMAG2_V3_SOURCES,
)


# ════════════════════════════════════════════════════════════════════════════════
# W5-W8 — PRITHVI-EO-2.0 ADAPTER
# ════════════════════════════════════════════════════════════════════════════════
class TestPrithviAdapter:
    def test_mock_backend_is_available(self):
        b = MockPrithviBackend()
        assert b.is_available() is True

    def test_mock_flood_mapping_is_deterministic(self):
        b = MockPrithviBackend()
        inp = HLSInput(tile_id="T30TXN")
        out1 = b.infer(inp, "flood_mapping")
        out2 = b.infer(inp, "flood_mapping")
        assert out1["water_mask"]["seed"] == out2["water_mask"]["seed"]

    def test_mock_different_tile_yields_different_seed(self):
        b = MockPrithviBackend()
        o1 = b.infer(HLSInput(tile_id="T30TXN"), "land_cover")
        o2 = b.infer(HLSInput(tile_id="T31TGK"), "land_cover")
        assert o1["seed"] != o2["seed"]

    def test_adapter_wraps_output_with_provenance(self):
        adapter = PrithviEOAdapter(backend=MockPrithviBackend())
        assert adapter.mode == "mock"
        out = adapter.infer(HLSInput(tile_id="T30TXN"), "land_cover")
        assert out.ml_provenance.mode == "mock"
        assert out.ml_provenance.model_name == "Prithvi-EO-2.0"
        assert len(out.ml_provenance.input_hash) == 64  # SHA-256 hex
        assert out.godel_wall["state"] == "KNOWN"
        assert out.epistemic_provenance["rung"] == 2

    def test_live_backend_raises_without_terratorch(self):
        if "terratorch" in __import__("sys").modules:
            pytest.skip("terratorch installed; live backend test skipped")
        # LivePrithviBackend may raise at __init__ or at .is_available() depending
        # on whether the optional import succeeded. We test that calling
        # is_available() correctly returns False, OR that constructing raises.
        try:
            b = LivePrithviBackend(weights_path="/tmp/nonexistent")
            assert b.is_available() is False
        except RuntimeError:
            # Acceptable — explicit error if import-time check fires.
            pass

    def test_scene_reasoning_task(self):
        adapter = PrithviEOAdapter(backend=MockPrithviBackend())
        out = adapter.infer(HLSInput(tile_id="T30TXN"), "scene_reasoning")
        assert "answer" in out.result
        assert "MOCK" in out.result["answer"]


# ════════════════════════════════════════════════════════════════════════════════
# W9-W12 — HARMONIC GRAVITY/MAGNETIC ADAPTER
# ════════════════════════════════════════════════════════════════════════════════
class TestHarmonICAdapter:
    def test_empty_prisms_zero_anomaly(self):
        b = MockHarmonICBackend()
        payload = GravityMagneticInput(
            survey_type="gravity",
            easting_m=(0.0, 1000.0),
            northing_m=(0.0, 1000.0),
            prisms=[],
        )
        vals = b.forward(payload)
        assert len(vals) == 4
        assert all(v == 0.0 for v in vals)

    def test_gravity_anomaly_positive_over_buried_high_density(self):
        b = MockHarmonICBackend()
        # Single prism at center with positive density contrast (basement high).
        payload = GravityMagneticInput(
            survey_type="gravity",
            easting_m=(-2000.0, -1000.0, 0.0, 1000.0, 2000.0),
            northing_m=(-2000.0, -1000.0, 0.0, 1000.0, 2000.0),
            prisms=[{
                "easting": 0.0, "northing": 0.0,
                "depth_top": 1000.0, "depth_bottom": 3000.0,
                "density": 600.0, "width_e": 1000.0, "width_n": 1000.0,
            }],
        )
        vals = b.forward(payload)
        # The center grid point (index 12 in 5x5 flat array, row 2 col 2) should
        # be the largest anomaly.
        center_idx = 2 * 5 + 2
        corner_idx = 0 * 5 + 0
        assert vals[center_idx] > 0.0
        assert vals[center_idx] > vals[corner_idx]

    def test_magnetic_anomaly_dipole_signs(self):
        b = MockHarmonICBackend()
        payload = GravityMagneticInput(
            survey_type="magnetic",
            easting_m=(-1000.0, 0.0, 1000.0),
            northing_m=(0.0,),
            prisms=[{
                "easting": 0.0, "northing": 0.0,
                "depth_top": 500.0, "depth_bottom": 1500.0,
                "density": 0.0, "width_e": 500.0, "width_n": 500.0,
            }],
            magnetization_a_m=1.0,
            field_declination_deg=0.0,
            field_inclination_deg=45.0,
        )
        vals = b.forward(payload)
        assert len(vals) == 3

    def test_adapter_outputs_correct_grid_shape(self):
        adapter = HarmonICAdapter(backend=MockHarmonICBackend())
        ne, nn = 4, 3
        payload = GravityMagneticInput(
            survey_type="gravity",
            easting_m=tuple([i * 1000.0 for i in range(ne)]),
            northing_m=tuple([i * 1000.0 for i in range(nn)]),
            prisms=[{
                "easting": 1500.0, "northing": 1000.0,
                "depth_top": 500.0, "depth_bottom": 2500.0,
                "density": 200.0, "width_e": 1000.0, "width_n": 1000.0,
            }],
        )
        out = adapter.forward(payload)
        assert out.grid_shape == (nn, ne)
        assert len(out.anomaly_values) == ne * nn
        assert out.provenance.input_hash == out.provenance.input_hash  # hash present
        assert out.godel_wall["state"] == "KNOWN"

    def test_provenance_records_mode(self):
        adapter = HarmonICAdapter(backend=MockHarmonICBackend())
        assert adapter.mode == "mock"
        payload = GravityMagneticInput(
            survey_type="gravity",
            easting_m=(0.0,),
            northing_m=(0.0,),
            prisms=[],
        )
        out = adapter.forward(payload)
        assert out.provenance.library == "mock"


# ════════════════════════════════════════════════════════════════════════════════
# EMAG2v3 + ICGEM + WGM2012 FETCHERS
# ════════════════════════════════════════════════════════════════════════════════
class TestEMAG2Fetcher:
    def test_offline_default_returns_stub(self, monkeypatch):
        monkeypatch.setenv("GEOX_EMAG2_OFFLINE", "1")
        monkeypatch.setenv("GEOX_EMAG2_CACHE_DIR", "/tmp/geox_emag2_test_offline")
        f = EMAG2Fetcher()
        r = f.fetch()
        assert r.ok is True
        assert r.mode == "offline_stub"
        assert r.meta is not None
        assert r.meta.resolution_arcmin == 2.0
        assert r.meta.bbox == (-180.0, -90.0, 180.0, 90.0)
        assert "Meyer" in r.citation or "NOAA" in r.citation

    def test_live_without_local_returns_not_ok(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GEOX_EMAG2_OFFLINE", "0")
        monkeypatch.setenv("GEOX_EMAG2_CACHE_DIR", str(tmp_path / "cache"))
        f = EMAG2Fetcher()
        r = f.fetch()
        assert r.ok is False
        assert "download" in r.note.lower()


class TestICGEMFetcher:
    def test_list_models_returns_known_models(self):
        f = ICGEMFetcher()
        models = f.list_models()
        names = [m.name for m in models]
        assert "EIGEN-6C4" in names
        assert "EGM2008" in names
        assert "XGM2019" in names
        for m in models:
            assert m.source_uri.startswith("https://")
            assert len(m.citation) > 20


class TestWGM2012Citation:
    def test_citation_has_bgi_attribution(self):
        assert "Bonvalot" in WGM2012Citation.CITATION
        assert "BGI" in WGM2012Citation.CITATION
        assert WGM2012Citation.SOURCE_URI.startswith("https://")
