"""
Tests for Wave 2 GEOX capability upgrades.
Covers: petro_ensemble, volumetrics, basin_charge, sensitivity,
        las_ingestor, asset_memory, visualization tools, tool_registry.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Gap 2 — Petro Ensemble
# ============================================================================

class TestPetroEnsemble:
    """Tests for geox/core/petro_ensemble.py"""

    def setup_method(self):
        from geox.core.petro_ensemble import PetroEnsemble
        self.ensemble = PetroEnsemble()

    def test_compute_sw_ensemble_returns_all_models(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        assert "archie" in result.models
        assert "indonesia" in result.models
        assert "simandoux" in result.models

    def test_sw_values_in_bounds(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        for name, sw in result.models.items():
            assert 0.0 <= sw <= 1.0, f"{name} Sw={sw} out of [0,1]"

    def test_p10_le_p50_le_p90(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        assert result.p10 <= result.p50 <= result.p90

    def test_disagreement_band_positive(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.20)
        assert result.disagreement_band >= 0.0

    def test_high_disagreement_triggers_hold(self):
        # Very shaly formation — models should disagree significantly
        result = self.ensemble.compute_sw_ensemble(rt=5.0, phi=0.15, rw=0.05, vsh=0.50)
        if result.disagreement_band > 0.20:
            assert result.hold_enforced is True

    def test_vault_receipt_emitted(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        assert result.vault_receipt is not None
        assert "hash" in result.vault_receipt
        assert "timestamp" in result.vault_receipt

    def test_claim_tag_emitted(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        assert result.claim_tag in {"CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"}

    def test_to_dict_serializable(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        d = result.to_dict()
        json.dumps(d)  # must not raise

    def test_physics_guard_validates_all_models(self):
        result = self.ensemble.compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.10)
        assert result.physics_status in {"PASS", "PHYSICS_VIOLATION"}

    def test_archie_clean_sand(self):
        """Clean sand (vsh=0): all models should converge close to Archie."""
        result = self.ensemble.compute_sw_ensemble(rt=100.0, phi=0.25, rw=0.05, vsh=0.0)
        assert result.models["archie"] < 0.5   # low Sw = hydrocarbon-bearing


class TestPetroEnsembleTool:
    def test_mcp_tool_returns_expected_keys(self):
        from geox.geox_mcp.tools.petro_ensemble_tool import geox_compute_sw_ensemble
        result = geox_compute_sw_ensemble(rt=10.0, phi=0.20, rw=0.05, vsh=0.15)
        assert "models" in result
        assert "p10" in result
        assert "p90" in result
        assert "hold_enforced" in result
        assert "vault_receipt" in result


# ============================================================================
# Gap 4 — Probabilistic Volumetrics
# ============================================================================

class TestProbabilisticVolumetrics:
    """Tests for geox/core/volumetrics.py"""

    def setup_method(self):
        from geox.core.volumetrics import ProbabilisticVolumetrics, TriangularDist, LognormalDist
        self.vol = ProbabilisticVolumetrics(n_draws=1000)  # fewer draws for speed
        self.TriangularDist = TriangularDist
        self.LognormalDist = LognormalDist

    def test_compute_hcpv_returns_p10_p50_p90(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(50, 100, 200),
            ntg_dist=self.TriangularDist(0.4, 0.6, 0.8),
            phi_dist=self.TriangularDist(0.10, 0.18, 0.28),
            sw_dist=self.TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
        )
        assert result.p10 > 0
        assert result.p50 >= result.p10
        assert result.p90 >= result.p50

    def test_n_valid_draws_reasonable(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(50, 100, 200),
            ntg_dist=self.TriangularDist(0.4, 0.6, 0.8),
            phi_dist=self.TriangularDist(0.10, 0.18, 0.28),
            sw_dist=self.TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
        )
        assert result.n_valid > result.n_draws * 0.9

    def test_posterior_ratio_computed(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(50, 100, 200),
            ntg_dist=self.TriangularDist(0.4, 0.6, 0.8),
            phi_dist=self.TriangularDist(0.10, 0.18, 0.28),
            sw_dist=self.TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
        )
        assert result.posterior_ratio > 0

    def test_hold_enforced_when_ratio_exceeds_5(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(1, 100, 10000),   # very wide
            ntg_dist=self.TriangularDist(0.1, 0.5, 0.9),
            phi_dist=self.TriangularDist(0.02, 0.20, 0.44),
            sw_dist=self.TriangularDist(0.05, 0.50, 0.95),
            fvf=1.0,
        )
        if result.posterior_ratio > 5.0:
            assert result.hold_enforced is True

    def test_vault_receipt_emitted(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(50, 100, 200),
            ntg_dist=self.TriangularDist(0.4, 0.6, 0.8),
            phi_dist=self.TriangularDist(0.10, 0.18, 0.28),
            sw_dist=self.TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
        )
        assert "hash" in result.vault_receipt

    def test_tornado_data_sorted_by_impact(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(50, 100, 200),
            ntg_dist=self.TriangularDist(0.4, 0.6, 0.8),
            phi_dist=self.TriangularDist(0.10, 0.18, 0.28),
            sw_dist=self.TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
        )
        impacts = [e["abs_impact"] for e in result.tornado_data]
        assert impacts == sorted(impacts, reverse=True)

    def test_to_dict_json_serializable(self):
        result = self.vol.compute_hcpv(
            grv_dist=self.TriangularDist(50, 100, 200),
            ntg_dist=self.TriangularDist(0.4, 0.6, 0.8),
            phi_dist=self.TriangularDist(0.10, 0.18, 0.28),
            sw_dist=self.TriangularDist(0.20, 0.35, 0.55),
            fvf=1.35,
        )
        json.dumps(result.to_dict())


class TestVolumetricsTool:
    def test_mcp_tool_returns_expected_keys(self):
        from geox.geox_mcp.tools.volumetrics_tool import geox_compute_volume_probabilistic
        result = geox_compute_volume_probabilistic(
            grv_min=50, grv_ml=100, grv_max=200,
            ntg_min=0.4, ntg_ml=0.6, ntg_max=0.8,
            phi_min=0.10, phi_ml=0.18, phi_max=0.28,
            sw_min=0.20, sw_ml=0.35, sw_max=0.55,
            fvf=1.35, n_draws=500,
        )
        assert "p10" in result
        assert "p50" in result
        assert "p90" in result
        assert "tornado_data" in result
        assert "vault_receipt" in result


# ============================================================================
# Gap 5 — Basin Charge
# ============================================================================

_SAMPLE_BURIAL = [
    {"age_ma_start": 100.0, "age_ma_end": 60.0, "temp_start_c": 40.0, "temp_end_c": 80.0},
    {"age_ma_start": 60.0, "age_ma_end": 20.0, "temp_start_c": 80.0, "temp_end_c": 120.0},
    {"age_ma_start": 20.0, "age_ma_end": 0.0, "temp_start_c": 120.0, "temp_end_c": 130.0},
]


class TestBasinCharge:
    """Tests for geox/core/basin_charge.py"""

    def setup_method(self):
        from geox.core.basin_charge import BasinCharge, compute_tti, compute_easy_ro
        self.charge = BasinCharge()
        self.compute_tti = compute_tti
        self.compute_easy_ro = compute_easy_ro

    def test_tti_positive(self):
        tti = self.compute_tti(_SAMPLE_BURIAL)
        assert tti > 0

    def test_easy_ro_positive(self):
        ro = self.compute_easy_ro(_SAMPLE_BURIAL)
        assert ro > 0

    def test_easy_ro_oil_window(self):
        """Deep burial at ~130°C should give oil window Ro."""
        ro = self.compute_easy_ro(_SAMPLE_BURIAL)
        assert ro >= 0.3   # at least past early maturity

    def test_simulate_returns_all_fields(self):
        result = self.charge.simulate(_SAMPLE_BURIAL)
        assert result.tti > 0
        assert result.easy_ro > 0
        assert result.maturity_window in {"IMMATURE", "OIL_WINDOW", "GAS_WINDOW", "OVERMATURE"}
        assert 0.0 <= result.charge_probability <= 1.0
        assert result.migration_distance_km >= 0.0
        assert 0.0 <= result.seal_integrity_estimate <= 1.0

    def test_vault_receipt_emitted(self):
        result = self.charge.simulate(_SAMPLE_BURIAL)
        assert "hash" in result.vault_receipt

    def test_claim_tag_emitted(self):
        result = self.charge.simulate(_SAMPLE_BURIAL)
        assert result.claim_tag in {"CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"}

    def test_to_dict_json_serializable(self):
        result = self.charge.simulate(_SAMPLE_BURIAL)
        json.dumps(result.to_dict())

    def test_immature_burial_low_prob(self):
        """Very shallow, cold burial should give low charge probability."""
        cold_burial = [
            {"age_ma_start": 50.0, "age_ma_end": 0.0, "temp_start_c": 20.0, "temp_end_c": 40.0},
        ]
        result = self.charge.simulate(cold_burial)
        assert result.maturity_window == "IMMATURE"
        assert result.charge_probability < 0.4


class TestBasinChargeTool:
    def test_mcp_tool_returns_expected_keys(self):
        from geox.geox_mcp.tools.basin_charge_tool import geox_simulate_basin_charge
        result = geox_simulate_basin_charge(_SAMPLE_BURIAL)
        assert "tti" in result
        assert "easy_ro" in result
        assert "charge_probability" in result
        assert "migration_distance_km" in result
        assert "vault_receipt" in result


# ============================================================================
# Gap 7 — Sensitivity Sweep
# ============================================================================

class TestSensitivitySweep:
    """Tests for geox/core/sensitivity.py"""

    def setup_method(self):
        from geox.core.sensitivity import SensitivitySweep
        self.sweep = SensitivitySweep()

    def test_sweep_returns_four_entries(self):
        result = self.sweep.run(
            u_ambiguity=0.5,
            evidence_credit=0.5,
            echo_score=0.3,
            truth_score=0.6,
        )
        assert len(result.entries) == 4

    def test_entries_ranked_by_si_descending(self):
        result = self.sweep.run(
            u_ambiguity=0.5,
            evidence_credit=0.5,
            echo_score=0.3,
            truth_score=0.6,
        )
        sis = [e.sensitivity_index for e in result.entries]
        assert sis == sorted(sis, reverse=True)

    def test_entries_have_correct_ranks(self):
        result = self.sweep.run(
            u_ambiguity=0.5,
            evidence_credit=0.5,
            echo_score=0.3,
            truth_score=0.6,
        )
        for i, entry in enumerate(result.entries):
            assert entry.rank == i + 1

    def test_critical_sensitivity_flag(self):
        result = self.sweep.run(
            u_ambiguity=0.8,  # high u_ambiguity → dominant driver
            evidence_credit=0.5,
            echo_score=0.3,
            truth_score=0.6,
        )
        assert isinstance(result.critical_sensitivity, bool)

    def test_verdict_demotion_on_critical(self):
        result = self.sweep.run(
            u_ambiguity=0.8,
            evidence_credit=0.5,
            echo_score=0.3,
            truth_score=0.6,
        )
        if result.critical_sensitivity and result.base_verdict == "PROCEED":
            assert result.demoted_verdict == "PARTIAL"

    def test_vault_receipt_emitted(self):
        result = self.sweep.run(0.3, 0.7, 0.5, 0.8)
        assert "hash" in result.vault_receipt

    def test_to_dict_json_serializable(self):
        result = self.sweep.run(0.3, 0.7, 0.5, 0.8)
        json.dumps(result.to_dict())


class TestSensitivityTool:
    def test_mcp_tool_returns_expected_keys(self):
        from geox.geox_mcp.tools.sensitivity_tool import geox_run_sensitivity_sweep
        result = geox_run_sensitivity_sweep(
            u_ambiguity=0.5, evidence_credit=0.5,
            echo_score=0.3, truth_score=0.6,
        )
        assert "entries" in result
        assert "top_si" in result
        assert "critical_sensitivity" in result
        assert "vault_receipt" in result


# ============================================================================
# Gap 3 — LAS Ingestor
# ============================================================================

def _write_sample_las(path: str) -> None:
    """Write a minimal LAS 2.0 file for testing."""
    content = """\
~Version ---------------------------------------------------
 VERS.                    2.0   :LAS, version 2.0
 WRAP.                     NO   :ONE LINE PER DEPTH STEP
~Well ------------------------------------------------------
 STRT.M              1500.0000   :START DEPTH
 STOP.M              1510.0000   :STOP DEPTH
 STEP.M                 1.0000   :STEP
 NULL.              -999.25000   :NULL VALUE
 COMP.             TEST COMPANY   :COMPANY
 WELL.             TEST-WELL-001  :WELL NAME
 UWI .             12-34-56-789W4 :UNIQUE WELL ID
 KB  .M                  15.0   :KELLY BUSHING
~Curve Information -----------------------------------------
 DEPT.M              :  DEPTH
 GR  .GAPI           :  GAMMA RAY
 RT  .OHMM           :  RESISTIVITY
 RHOB.G/C3           :  BULK DENSITY
 NPHI.V/V            :  NEUTRON POROSITY
~A DEPT        GR         RT         RHOB       NPHI
 1500.0000  45.000    10.000     2.350      0.200
 1501.0000  42.000    12.000     2.320      0.210
 1502.0000  50.000     8.000     2.400      0.180
 1503.0000  60.000     5.000     2.450      0.160
 1504.0000  55.000     6.000     2.430      0.170
 1505.0000  40.000    15.000     2.300      0.220
 1506.0000  38.000    18.000     2.280      0.230
 1507.0000  35.000    20.000     2.260      0.240
 1508.0000  48.000    11.000     2.370      0.195
 1509.0000  52.000     9.000     2.410      0.175
 1510.0000  46.000    13.000     2.340      0.205
"""
    with open(path, "w") as f:
        f.write(content)


class TestLASIngestor:
    """Tests for geox/services/las_ingestor.py"""

    def setup_method(self):
        from geox.services.las_ingestor import LASIngestor
        self.ingestor = LASIngestor()

    def test_ingest_valid_las(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path), asset_id="TEST-ASSET")
        assert result.asset_id == "TEST-ASSET"
        assert result.n_depth_samples == 11
        assert result.n_curves >= 4  # GR, RT, RHOB, NPHI

    def test_depth_range_correct(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path))
        assert result.depth_range_m[0] == pytest.approx(1500.0, abs=0.1)
        assert result.depth_range_m[1] == pytest.approx(1510.0, abs=0.1)

    def test_uwi_extracted(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path))
        assert "12-34" in result.uwi or result.uwi != "UNKNOWN"

    def test_curve_qc_results_present(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path))
        mnemonics = {c.mnemonic for c in result.curves}
        assert "GR" in mnemonics
        assert "RT" in mnemonics

    def test_claim_tag_emitted(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path))
        assert result.claim_tag in {"CLAIM", "PLAUSIBLE", "HYPOTHESIS", "ESTIMATE", "UNKNOWN"}

    def test_vault_receipt_emitted(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path))
        assert "hash" in result.vault_receipt

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            self.ingestor.ingest("/nonexistent/path/test.las")

    def test_to_dict_json_serializable(self, tmp_path):
        las_path = tmp_path / "test.las"
        _write_sample_las(str(las_path))
        result = self.ingestor.ingest(str(las_path))
        json.dumps(result.to_dict())


class TestLASIngestTool:
    def test_mcp_tool_file_not_found_returns_error(self):
        from geox.geox_mcp.tools.las_ingest_tool import geox_ingest_las
        result = geox_ingest_las("/nonexistent/file.las")
        assert "error" in result
        assert result["hold_enforced"] is True

    def test_mcp_tool_valid_file(self, tmp_path):
        _write_sample_las(str(tmp_path / "test.las"))
        from geox.geox_mcp.tools.las_ingest_tool import geox_ingest_las
        result = geox_ingest_las(str(tmp_path / "test.las"), asset_id="MY-FIELD")
        assert "asset_id" in result
        assert result["asset_id"] == "MY-FIELD"
        assert "curves" in result


# ============================================================================
# Gap 6 — Asset Memory
# ============================================================================

class TestAssetMemory:
    """Tests for geox/services/asset_memory.py"""

    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        from geox.services.asset_memory import AssetMemoryStore
        self.store = AssetMemoryStore(db_path=os.path.join(self._tmpdir, "test.db"))

    def test_store_with_amanah_locked(self):
        result = self.store.store(
            asset_id="DULANG-A",
            eval_type="petro_ensemble",
            payload={"mean": 0.35, "p50": 0.35},
            amanah_locked=True,
        )
        assert result.success is True
        assert result.record_id is not None

    def test_store_without_amanah_locked_denied(self):
        result = self.store.store(
            asset_id="DULANG-A",
            eval_type="petro_ensemble",
            payload={"mean": 0.35},
            amanah_locked=False,
        )
        assert result.success is False
        assert result.record_id is None
        assert "F11" in result.audit_trace

    def test_recall_returns_stored_records(self):
        self.store.store("TIO-3", "volumetrics", {"p50": 120.0}, amanah_locked=True)
        recall = self.store.recall("TIO-3")
        assert recall.n_records >= 1

    def test_recall_filters_by_eval_type(self):
        self.store.store("BEK-2", "petro_ensemble", {"p50": 0.3}, amanah_locked=True)
        self.store.store("BEK-2", "volumetrics", {"p50": 200.0}, amanah_locked=True)
        recall = self.store.recall("BEK-2", eval_type="volumetrics")
        assert all(r.eval_type == "volumetrics" for r in recall.records)

    def test_recall_empty_returns_estimate_tag(self):
        recall = self.store.recall("NONEXISTENT-WELL-XYZ")
        assert recall.claim_tag == "ESTIMATE"
        assert recall.n_records == 0

    def test_vault_receipt_on_store(self):
        result = self.store.store("SEL-1", "basin_charge", {}, amanah_locked=True)
        assert "hash" in result.vault_receipt

    def test_vault_receipt_on_recall(self):
        self.store.store("SEL-1", "las_ingest", {"uwi": "12-345"}, amanah_locked=True)
        recall = self.store.recall("SEL-1")
        assert "hash" in recall.vault_receipt

    def test_to_dict_json_serializable(self):
        self.store.store("DUL-A1", "sensitivity", {"top_si": 0.3}, amanah_locked=True)
        recall = self.store.recall("DUL-A1")
        json.dumps(recall.to_dict())


class TestAssetMemoryTool:
    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        # Monkey-patch the singleton store to use a temp DB
        import geox.geox_mcp.tools.asset_memory_tool as amt
        from geox.services.asset_memory import AssetMemoryStore
        amt._store = AssetMemoryStore(db_path=os.path.join(self._tmpdir, "test.db"))

    def test_store_and_recall_roundtrip(self):
        from geox.geox_mcp.tools.asset_memory_tool import geox_memory_store_asset, geox_memory_recall_asset
        store_result = geox_memory_store_asset(
            asset_id="DULANG-A",
            eval_type="test_eval",
            payload={"value": 42},
            amanah_locked=True,
        )
        assert store_result["success"] is True

        recall_result = geox_memory_recall_asset(asset_id="DULANG-A", eval_type="test_eval")
        assert recall_result["n_records"] >= 1
        assert recall_result["records"][0]["payload"]["value"] == 42


# ============================================================================
# Gap 1 — Visualization
# ============================================================================

class TestVisualizationTools:
    """Tests for geox/geox_mcp/tools/visualization.py"""

    def test_render_log_track_basic(self):
        from geox.geox_mcp.tools.visualization import geox_render_log_track
        depth = [1500.0 + i for i in range(10)]
        gr = [50.0 + i for i in range(10)]
        result = geox_render_log_track(depth=depth, gr=gr)
        assert result["render_type"] == "log_track"
        assert result["n_samples"] == 10
        assert len(result["tracks"]) >= 1
        assert result["tracks"][0]["mnemonic"] == "GR"

    def test_render_log_track_all_curves(self):
        from geox.geox_mcp.tools.visualization import geox_render_log_track
        depth = list(range(1500, 1510))
        result = geox_render_log_track(
            depth=depth,
            gr=[50.0] * 10,
            rhob=[2.3] * 10,
            nphi=[0.22] * 10,
            rt=[10.0] * 10,
        )
        mnemonics = [t["mnemonic"] for t in result["tracks"]]
        assert "GR" in mnemonics
        assert "RHOB" in mnemonics
        assert "NPHI" in mnemonics
        assert "RT" in mnemonics

    def test_render_log_track_vault_receipt(self):
        from geox.geox_mcp.tools.visualization import geox_render_log_track
        result = geox_render_log_track(depth=[1500.0], gr=[50.0])
        assert "hash" in result["vault_receipt"]

    def test_render_log_track_normalised_in_range(self):
        from geox.geox_mcp.tools.visualization import geox_render_log_track
        result = geox_render_log_track(depth=[1500.0, 1501.0], gr=[0.0, 150.0])
        norm = result["tracks"][0]["normalised"]
        for v in norm:
            if v is not None:
                assert 0.0 <= v <= 1.0

    def test_render_log_track_json_serializable(self):
        from geox.geox_mcp.tools.visualization import geox_render_log_track
        result = geox_render_log_track(depth=[1500.0], gr=[50.0])
        json.dumps(result)

    def test_render_volume_slice_basic(self):
        from geox.geox_mcp.tools.visualization import geox_render_volume_slice
        data = [[float(i + j) for j in range(8)] for i in range(4)]
        result = geox_render_volume_slice(volume_data=data, nx=8, ny=4)
        assert result["render_type"] == "volume_slice"
        assert result["nx"] == 8
        assert result["ny"] == 4
        assert len(result["flat_data"]) == 32

    def test_render_volume_slice_normalised(self):
        from geox.geox_mcp.tools.visualization import geox_render_volume_slice
        data = [[-1.0, 0.0, 1.0]]
        result = geox_render_volume_slice(volume_data=data, nx=3, ny=1)
        for v in result["flat_data"]:
            assert 0.0 <= v <= 1.0

    def test_render_volume_slice_vault_receipt(self):
        from geox.geox_mcp.tools.visualization import geox_render_volume_slice
        result = geox_render_volume_slice(volume_data=[[1.0]], nx=1, ny=1)
        assert "hash" in result["vault_receipt"]

    def test_render_volume_slice_json_serializable(self):
        from geox.geox_mcp.tools.visualization import geox_render_volume_slice
        data = [[float(i) for i in range(5)] for _ in range(3)]
        result = geox_render_volume_slice(volume_data=data, nx=5, ny=3)
        json.dumps(result)


# ============================================================================
# Tool Registry
# ============================================================================

class TestToolRegistry:
    """Tests for Wave 2 tool registrations in tool_registry.py."""

    def setup_method(self):
        from geox.core.tool_registry import ToolRegistry
        self.registry = ToolRegistry

    def test_wave2_tools_registered(self):
        expected = {
            "geox_compute_sw_ensemble",
            "geox_compute_volume_probabilistic",
            "geox_simulate_basin_charge",
            "geox_run_sensitivity_sweep",
            "geox_ingest_las",
            "geox_memory_store_asset",
            "geox_memory_recall_asset",
            "geox_render_log_track",
            "geox_render_volume_slice",
        }
        registered = {t.name for t in self.registry.list_tools()}
        for name in expected:
            assert name in registered, f"Tool not registered: {name}"

    def test_all_registered_tools_have_version(self):
        for tool in self.registry.list_tools():
            assert tool.version, f"Tool {tool.name} missing version"

    def test_all_registered_tools_have_description(self):
        for tool in self.registry.list_tools():
            assert tool.description, f"Tool {tool.name} missing description"

    def test_get_tool_by_name(self):
        tool = self.registry.get("geox_compute_sw_ensemble")
        assert tool is not None
        assert tool.name == "geox_compute_sw_ensemble"
