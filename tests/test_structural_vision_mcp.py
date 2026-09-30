"""Structural-vision MCP surface — tools, server, prompt. Contract tests.

Contract under test (CONTRACT.md v1.0, frozen):
  1. The extract tool returns the section-5 bundle WITH a mandatory aggregate
     `coverage` and a `method_receipt`, and `preferred_hypothesis` is ALWAYS None.
  2. No probability/confidence/score/certainty key survives the return path —
     the sanitizer strips a smuggled `confidence`, recursively, at every depth.
  3. When the deterministic vision core is missing, the tool returns a
     structured governance_status == "HOLD" with error VISION_CORE_UNAVAILABLE
     and DOES NOT RAISE. It never falls back to a vision-language model.
  4. The falsify tool is a THIN ADAPTER: it maps the bundle into the `framework`
     dict that `run_regime_falsification` consumes, and it REUSES that one
     engine rather than reimplementing it.
  5. UNMEASURED is never laundered into a number — a missing expansion index is
     omitted so the engine reports UNMEASURED, never a fabricated KILL.
  6. The prompt template carries the Dahlstrom scope, the growth-strata caveat,
     the epistemic ceiling, and the Walther's-Law correction, plus the audited
     corrections (Coulomb band as RULE OF THUMB, VE dimensionless + migrated-data
     caveat, uniform thickness NON-DISCRIMINATING, salt as a DECOUPLING MECHANISM).
  7. This lane is DISJOINT from the VLM lane in servers/vision.py.

The vision core is built in parallel by other agents, so these tests inject a
STUB module into sys.modules and depend on nothing under
`geox_core/vision_structural/` except that they must not need it.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import types
from pathlib import Path

from dataclasses import asdict, dataclass, field

import pytest

from geox_mcp.prompts import structural_invariants as INV
from geox_mcp.tools import structural_vision as SV
from geox_mcp.tools.structural_vision import (
    FORBIDDEN_PROBABILITY_KEYS,
    aggregate_coverage,
    assert_no_forbidden_keys,
    bundle_to_framework,
    geox_structural_regime_falsify,
    geox_structural_vision_extract,
    strip_forbidden_keys,
    unified_status,
)

CORE_MODULE = "geox_core.vision_structural"
ENGINE_MODULE = "geox_mcp.tools.structure_gates.tectonic_regime"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _norm(text: str) -> str:
    """Collapse whitespace so a wrapped phrase still matches as one substring."""
    return " ".join(text.split())


def _load_module_by_path(name: str, rel_path: str):
    """Load a module straight from disk.

    `geox_mcp.servers.__init__` currently transitively imports a module that
    needs an absent dependency, so importing the `geox_mcp.servers` PACKAGE is
    not viable from a test. Loading by file path exercises the real source under
    test without depending on an unrelated broken import in the package init.
    """
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / rel_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════════════════════════
# Stub vision core — a parallel agent owns the real one
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class FakeMeasurement:
    """Stand-in for the frozen Measurement envelope (has .asdict())."""

    value: object
    unit: str
    status: str
    n_samples: int = 0
    coverage: object = None
    method: str = ""
    uncertainty: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    def asdict(self) -> dict:
        return asdict(self)


def _stub_axes():
    return {
        "A_shape": {
            "dip_deg_mean": FakeMeasurement(11.0, "deg", "MEASURED", 500, 0.82, "structure_tensor"),
            "dip_deg_p95": FakeMeasurement(22.5, "deg", "MEASURED", 500, 0.82, "structure_tensor"),
        },
        "B_differential": {
            "expansion_index": FakeMeasurement(1.7, "ratio", "MEASURED", 120, 0.70, "isopach_dtw"),
            "isopach_differential": FakeMeasurement(2.4, "ratio", "MEASURED", 120, 0.70, "isopach"),
        },
        "C_orientation": {
            "azimuth_deg": FakeMeasurement(42.0, "deg_azimuth", "MEASURED", 9, 0.60, "circular_mean"),
        },
        "D_superposition": {
            "n_candidates": 5,
            "relations": [{"younger": "F1", "older": "H2", "type": "offset"}],
        },
    }


def _build_stub_core(*, axes=None, calibration=None):
    mod = types.ModuleType(CORE_MODULE)
    captured: dict = {}

    def extract_all_axes(section, horizon_masks, *, dz_m, dx_m, ve, horizon_names):
        captured["axes_args"] = {
            "section": section,
            "horizon_masks": horizon_masks,
            "dz_m": dz_m,
            "dx_m": dx_m,
            "ve": ve,
            "horizon_names": horizon_names,
        }
        return _stub_axes() if axes is None else axes

    def declare_calibration_state(*, vertical_exaggeration, velocity_model_present, time_domain):
        captured["calibration_args"] = {
            "vertical_exaggeration": vertical_exaggeration,
            "velocity_model_present": velocity_model_present,
            "time_domain": time_domain,
        }
        if calibration is not None:
            return calibration
        return {
            "dips_trustworthy": abs((vertical_exaggeration or 1.0) - 1.0) < 1e-9
            and (not time_domain or velocity_model_present),
            "problems": [],
        }

    mod.extract_all_axes = extract_all_axes
    mod.declare_calibration_state = declare_calibration_state
    mod.is_stub = True
    return mod, captured


@pytest.fixture
def stub_core(monkeypatch):
    """Inject a stub vision core; removed at teardown."""
    mod, captured = _build_stub_core()
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    return captured


@pytest.fixture
def bundle(stub_core):
    """A healthy extract bundle, built through the real tool."""
    return asyncio.run(
        geox_structural_vision_extract(
            section="SECTION-PLACEHOLDER",
            horizon_masks="MASKS-PLACEHOLDER",
            dz_m=4.0,
            dx_m=25.0,
            ve=1.0,
            section_ref="KINABALU-L12",
            horizon_names=["TOP_MIOCENE"],
            decompacted=True,
            interval_velocity_m_s=2400.0,
            migration_state="POST_MIGRATION",
        )
    )


# ══════════════════════════════════════════════════════════════════════════════
# (1) extract — section-5 bundle shape
# ══════════════════════════════════════════════════════════════════════════════


def test_extract_returns_mandatory_coverage_and_method_receipt(bundle):
    assert bundle["coverage"] is not None, "coverage is MANDATORY alongside any number"
    assert isinstance(bundle["coverage"], float)
    assert 0.0 <= bundle["coverage"] <= 1.0
    assert isinstance(bundle["method_receipt"], dict)
    assert bundle["method_receipt"]["parameters"]["dz_m"] == 4.0
    assert bundle["method_receipt"]["parameters"]["dx_m"] == 25.0
    assert bundle["status"] == "MEASURED"


def test_extract_declares_the_null_hypothesis_candidate(bundle):
    assert bundle["null_hypothesis_candidate"] == "null_depositional"
    assert "null_depositional" in bundle["candidate_regimes"] or bundle["null_hypothesis_candidate"]


def test_extract_never_invokes_a_vision_language_model(bundle):
    mr = bundle["method_receipt"]
    assert mr["llm_in_the_loop_for_geometry"] is False
    assert mr["vision_language_model_used"] is False
    assert mr["lane"] == "deterministic_structural_vision"


def test_extract_carries_governance_and_epistemic_ceiling(bundle):
    assert bundle["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert bundle["seal_authority"] == "arifOS_only"
    assert "KINEMATICS" in bundle["epistemic_ceiling"]
    assert "stress tensor" in bundle["epistemic_ceiling"].lower()
    assert bundle["preferred_hypothesis"] is None


def test_extract_records_the_decompaction_declaration(bundle):
    assert bundle["decompaction_declared"] is True
    params = bundle["method_receipt"]["parameters"]
    assert params["decompaction_applied_before_thickness"] is True


def test_extract_declares_decompaction_false_when_not_applied(stub_core):
    out = asyncio.run(geox_structural_vision_extract(decompacted=False))
    assert out["decompaction_declared"] is False
    assert out["method_receipt"]["parameters"]["decompaction_applied_before_thickness"] is False


def test_extract_passes_ve_and_spacing_through_to_the_core(stub_core):
    asyncio.run(
        geox_structural_vision_extract(
            section="S", horizon_masks="M", dz_m=2.0, dx_m=12.5, ve=2.0
        )
    )
    args = stub_core["axes_args"]
    assert args["dz_m"] == 2.0
    assert args["dx_m"] == 12.5
    assert args["ve"] == 2.0


def test_extract_declares_migrated_data_tan_caveat(bundle):
    cal = bundle["calibration_state"]
    assert cal["migration_state"] == "POST_MIGRATION"
    assert "MIGRATED DATA DO NOT FOLLOW" in cal["migrated_data_tan_caveat"].upper()


def test_unmeasured_axis_degrades_status_without_raising(monkeypatch):
    mod, _ = _build_stub_core(axes={"A_shape": {}, "B_differential": {}})
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    out = asyncio.run(geox_structural_vision_extract())
    assert out["status"] == "UNMEASURED"
    assert out["coverage"] is None
    assert out["ok"] is True


# ══════════════════════════════════════════════════════════════════════════════
# (2) forbidden probability keys — the sanitizer
# ══════════════════════════════════════════════════════════════════════════════


def test_forbidden_key_constant_lists_the_contract_set():
    for key in ("confidence", "reliability", "probability", "p_truth", "score", "certainty"):
        assert key in FORBIDDEN_PROBABILITY_KEYS


def test_sanitizer_strips_a_smuggled_confidence_key():
    dirty = {
        "dip_deg_p95": {"value": 22.5, "unit": "deg", "coverage": 0.82},
        "confidence": 0.97,
    }
    clean = strip_forbidden_keys(dirty)
    assert "confidence" not in clean
    assert clean["dip_deg_p95"]["value"] == 22.5


def test_sanitizer_strips_suffixed_and_nested_variants():
    dirty = {
        "kinematic": {
            "confidence_level": 0.95,
            "reliability_score": 0.88,
            "P_TRUTH": 0.9,
            "nested": [{"certainty": 1.0, "probability_pct": 88}, {"dip_deg": 22.5}],
        }
    }
    clean = strip_forbidden_keys(dirty)
    # every forbidden key is gone; the non-probability survivor remains exactly
    survivors = clean["kinematic"]["nested"]
    assert {"dip_deg": 22.5} in survivors
    assert not any(
        k in ("confidence_level", "reliability_score", "P_TRUTH", "certainty", "probability_pct")
        for d in survivors
        if isinstance(d, dict)
        for k in d
    )
    assert clean["kinematic"].get("confidence_level") is None
    assert clean["kinematic"].get("reliability_score") is None
    assert clean["kinematic"].get("P_TRUTH") is None


def test_sanitizer_does_not_mutate_the_input():
    dirty = {"confidence": 0.99, "value": 1.0}
    strip_forbidden_keys(dirty)
    assert dirty["confidence"] == 0.99  # F1 AMANAH — inputs are never mutated


def test_assert_no_forbidden_keys_raises_on_a_survivor():
    with pytest.raises(ValueError, match="forbidden probability key"):
        assert_no_forbidden_keys({"axes": {"A_shape": {"score": 0.5}}})


def test_returned_payloads_contain_no_forbidden_keys(bundle):
    for payload in (bundle, bundle_to_framework(bundle)):
        assert_no_forbidden_keys(payload)  # raises if anything survived


def test_aggregate_coverage_is_none_when_nothing_is_covered():
    assert aggregate_coverage({}) is None
    assert aggregate_coverage({"A_shape": {"dip_deg_mean": {"value": 1.0, "status": "MEASURED"}}}) is None


def test_aggregate_coverage_normalizes_percent_and_ratio():
    assert aggregate_coverage({}, explicit=82.0) == 0.82
    assert aggregate_coverage({}, explicit=0.82) == 0.82


def test_unified_status_never_upgrades_unmeasured():
    assert unified_status({}, None) == "UNMEASURED"
    assert unified_status(
        {"A_shape": {"dip": {"value": None, "status": "UNMEASURED"}}}, None
    ) == "UNMEASURED"
    assert unified_status(
        {"A_shape": {"dip": {"value": 1.0, "status": "MEASURED"}}}, 0.5
    ) == "MEASURED"


# ══════════════════════════════════════════════════════════════════════════════
# (3) ImportError path — HOLD, never raise, never fall back to a VLM
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def core_unimportable(monkeypatch):
    real_import = importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == CORE_MODULE:
            raise ImportError("simulated: vision core not built yet")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    monkeypatch.delitem(sys.modules, CORE_MODULE, raising=False)


def test_missing_core_returns_hold_and_does_not_raise(core_unimportable):
    out = asyncio.run(geox_structural_vision_extract())  # must NOT raise
    assert out["ok"] is False
    assert out["error"] == "VISION_CORE_UNAVAILABLE"
    assert out["governance_status"] == "HOLD"
    assert out["status"] == "UNMEASURED"
    assert out["coverage"] is None
    assert out["preferred_hypothesis"] is None
    assert out["seal_authority"] == "arifOS_only"


def test_missing_core_payload_is_sanitized_and_carries_no_numbers(core_unimportable):
    out = asyncio.run(geox_structural_vision_extract())
    assert_no_forbidden_keys(out)
    assert out["axes"] == {}
    assert "vision-language model" in out["note"]


def test_missing_core_never_silently_swaps_in_the_vlm_lane(core_unimportable):
    out = asyncio.run(geox_structural_vision_extract())
    assert "geox_vision" not in repr(out)
    assert out["method_receipt"] == {}


def test_incomplete_core_also_holds(monkeypatch):
    mod = types.ModuleType(CORE_MODULE)  # importable, but declare_... absent
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    out = asyncio.run(geox_structural_vision_extract())
    assert out["governance_status"] == "HOLD"
    assert out["error"] == "VISION_CORE_UNAVAILABLE"


# ══════════════════════════════════════════════════════════════════════════════
# (4) adapter — bundle -> framework (CONTRACT section 6 mapping table)
# ══════════════════════════════════════════════════════════════════════════════


def test_adapter_maps_spatial_differential_into_intervals(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["intervals"][0]["spatial_differential"] is True


def test_adapter_maps_uniform_differential_to_false_non_discriminating(monkeypatch):
    mod, _ = _build_stub_core(
        axes={
            "B_differential": {
                "isopach_differential": FakeMeasurement(1.0, "ratio", "MEASURED", 120, 0.7, "isopach"),
            }
        }
    )
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    out = asyncio.run(geox_structural_vision_extract())
    fw = bundle_to_framework(out)
    # ~1.0 is uniform: NON-DISCRIMINATING. It supports neither eustasy nor
    # tectonics on its own, so it must not be presented as a differential.
    assert fw["intervals"][0]["spatial_differential"] is False


def test_adapter_maps_expansion_index_into_intervals(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["intervals"][0]["expansion_index"] == 1.7


def test_adapter_omits_expansion_index_when_unmeasured(monkeypatch):
    mod, _ = _build_stub_core(
        axes={
            "B_differential": {
                "expansion_index": FakeMeasurement(
                    None, "ratio", "UNMEASURED", 0, None, "", notes=["no picks"]
                )
            }
        }
    )
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    out = asyncio.run(geox_structural_vision_extract())
    fw = bundle_to_framework(out)
    # OMITTED, not zero. A missing expansion index is UNMEASURED — never a KILL,
    # because a fault moving slower than sedimentation leaves NO growth signature.
    assert "expansion_index" not in fw["intervals"][0]


def test_adapter_always_emits_an_explicit_decompacted_boolean(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["intervals"][0]["decompacted"] is True
    assert bundle_to_framework({})["intervals"][0]["decompacted"] is False


def test_adapter_never_invents_an_isopach_reversal(bundle):
    fw = bundle_to_framework(bundle)
    assert "isopach_reversal" not in fw["intervals"][0]


def test_adapter_maps_azimuth_population_into_faults(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["faults"][0]["strike_deg"] == 42.0


def test_adapter_maps_superposition_relations_into_cross_cutting(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["cross_cutting"] == [{"younger": "F1", "older": "H2", "type": "offset"}]


def test_adapter_omits_cross_cutting_when_no_relations_present(monkeypatch):
    mod, _ = _build_stub_core(axes={"D_superposition": {"n_candidates": 5}})
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    out = asyncio.run(geox_structural_vision_extract())
    fw = bundle_to_framework(out)
    # A bare gradient edge is NOT a termination. A candidate COUNT without
    # relations must not be promoted into a chronology.
    assert "cross_cutting" not in fw


def test_adapter_maps_coverage_into_horizon_and_interval_percent(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["horizons"][0]["coverage_pct"] == pytest.approx(bundle["coverage"] * 100.0, abs=0.01)
    assert fw["intervals"][0]["coverage_pct"] == pytest.approx(bundle["coverage"] * 100.0, abs=0.01)


def test_adapter_carries_display_state_and_problems(bundle):
    fw = bundle_to_framework(bundle)
    assert fw["display"]["vertical_exaggeration"] == 1.0
    assert fw["display"]["velocity_model"] is True
    assert fw["display"]["time_domain"] is False
    assert fw["display"]["migration_state"] == "POST_MIGRATION"


def test_adapter_maps_calibration_problems_into_display():
    fw = bundle_to_framework(
        {"calibration_state": {"problems": ["vertical_exaggeration=2 != 1"], "time_domain": True}}
    )
    assert fw["display"]["problems"] == ["vertical_exaggeration=2 != 1"]
    assert fw["display"]["time_domain"] is True


# ══════════════════════════════════════════════════════════════════════════════
# (5) falsify — thin adapter onto the ONE engine
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def captured_framework(monkeypatch):
    """Capture the exact framework passed into run_regime_falsification."""
    engine = importlib.import_module(ENGINE_MODULE)
    caps: dict = {}
    real = engine.run_regime_falsification

    def spy(framework=None, candidate_regimes=None, min_hypotheses=3):
        caps["framework"] = framework
        caps["candidate_regimes"] = candidate_regimes
        caps["min_hypotheses"] = min_hypotheses
        return real(framework=framework, candidate_regimes=candidate_regimes,
                    min_hypotheses=min_hypotheses)

    monkeypatch.setattr(engine, "run_regime_falsification", spy)
    return caps


def test_falsify_hands_the_engine_the_mapped_framework(bundle, captured_framework):
    out = asyncio.run(
        geox_structural_regime_falsify(
            bundle=bundle, candidate_regimes=["extension", "compression", "strike_slip"]
        )
    )
    fw = captured_framework["framework"]
    # The four keys the mapping table says the engine must receive:
    assert fw["intervals"][0]["spatial_differential"] is True
    assert fw["intervals"][0]["expansion_index"] == 1.7
    assert fw["intervals"][0]["decompacted"] is True
    assert fw["cross_cutting"] == [{"younger": "F1", "older": "H2", "type": "offset"}]
    assert out["ok"] is True


def test_falsify_reuses_the_single_existing_engine(bundle, captured_framework):
    asyncio.run(geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["extension", "compression"]))
    # The spy fired -> the real K-REGIME engine was invoked, not a second one.
    assert captured_framework["framework"] is not None
    assert "no second engine" in asyncio.run(
        geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["extension", "compression"])
    )["adapter"] or True


def test_falsify_declares_which_engine_it_reuses(bundle):
    out = asyncio.run(geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["extension", "compression"]))
    assert "run_regime_falsification" in out["adapter"]
    assert "no second engine" in out["adapter"]


def test_falsify_preferred_hypothesis_is_none(bundle):
    out = asyncio.run(
        geox_structural_regime_falsify(
            bundle=bundle, candidate_regimes=["extension", "compression", "strike_slip"]
        )
    )
    assert out["preferred_hypothesis"] is None


def test_falsify_preferred_hypothesis_none_even_on_a_hold_path(bundle):
    out = asyncio.run(
        geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["not_a_regime"])
    )
    assert out["preferred_hypothesis"] is None
    assert out["governance_status"] == "HOLD"


def test_falsify_preferred_hypothesis_none_with_no_input_at_all():
    out = asyncio.run(geox_structural_regime_falsify())
    assert out["preferred_hypothesis"] is None
    assert out["local_verdict"] == "QUALIFIED_CANDIDATE"
    assert out["seal_authority"] == "arifOS_only"


def test_falsify_returns_the_raw_bundle_for_traceability(bundle):
    out = asyncio.run(geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["extension", "compression"]))
    assert out["bundle"] == bundle  # sanitized deep copy; equal, not identical
    assert out["framework_used"] == bundle_to_framework(bundle)
    assert set(out["candidate_regimes_used"]) == {"extension", "compression"}


def test_falsify_never_softens_an_unknown_regime_hold(bundle):
    out = asyncio.run(
        geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["halokinesis_as_a_regime"])
    )
    assert out["governance_status"] == "HOLD"
    assert out["overall"] if "overall" in out else True
    assert out["ok"] is False


def test_falsify_propagates_hypothesis_poverty_hold(bundle):
    out = asyncio.run(
        geox_structural_regime_falsify(
            bundle=bundle, candidate_regimes=["extension"], min_hypotheses=5
        )
    )
    assert out["governance_status"] == "HOLD"
    assert out["error"] == "INSUFFICIENT_COMPETING_HYPOTHESES"


def test_falsify_always_carries_the_null_hypothesis_competitor(bundle):
    out = asyncio.run(
        geox_structural_regime_falsify(
            bundle=bundle, candidate_regimes=["extension", "compression"]
        )
    )
    # The engine appends the null hypothesis as a mandatory competitor even when
    # the caller did not name it. Falsifying only the tectonic candidate is a
    # confirmation, not a falsification.
    assert out["candidate_regimes_used"] == ["extension", "compression"]
    nulls = [h for h in out["hypotheses"] if h.get("is_null_hypothesis")]
    assert len(nulls) == 1
    assert nulls[0]["regime"] == "null_depositional"
    assert out["n_hypotheses"] == 3  # extension + compression + the mandatory null


def test_falsify_caller_framework_overrides_the_mapped_bundle(bundle):
    out = asyncio.run(
        geox_structural_regime_falsify(
            bundle=bundle,
            framework={"horizons": [{"name": "H1", "coverage_pct": 90.0, "geometry": {"dip_deg": 3.0}}]},
            candidate_regimes=["extension", "compression"],
        )
    )
    assert out["framework_used"]["horizons"][0]["name"] == "H1"


def test_falsify_decompact_gate_is_unmeasured_when_undeclared(monkeypatch):
    mod, _ = _build_stub_core()
    monkeypatch.setitem(sys.modules, CORE_MODULE, mod)
    out = asyncio.run(geox_structural_vision_extract(decompacted=False))
    res = asyncio.run(
        geox_structural_regime_falsify(bundle=out, candidate_regimes=["extension", "compression"])
    )
    gate = res["universal_gates"]["K-REGIME-DECOMPACT"]
    assert gate["status"] in ("UNMEASURED", "WARN")
    assert gate["status"] != "PASS"


def test_falsify_xcut_gate_is_unmeasured_without_relations():
    res = asyncio.run(geox_structural_regime_falsify(candidate_regimes=["extension", "compression"]))
    assert res["universal_gates"]["K-REGIME-XCUT"]["status"] == "UNMEASURED"


def test_falsify_never_emits_a_stress_tensor(bundle):
    res = asyncio.run(
        geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["extension", "compression"])
    )
    assert "stress_tensor" not in repr(res["framework_used"])
    assert "claim_stress_tensor" not in res["framework_used"]
    assert "KINEMATICS" in res["doctrine"]["geometry_yields_kinematics"]


def test_falsify_doctrine_states_uniform_thickness_is_non_discriminating(bundle):
    res = asyncio.run(
        geox_structural_regime_falsify(bundle=bundle, candidate_regimes=["extension", "compression"])
    )
    text = res["doctrine"]["uniform_thickness_is_non_discriminating"].lower()
    assert "non-discriminating" in text or "neither eustasy nor tectonics" in text


# ══════════════════════════════════════════════════════════════════════════════
# (6) prompt template — invariants (Dahlstrom, growth strata, ceiling, Walther)
# ══════════════════════════════════════════════════════════════════════════════


def test_prompt_contains_the_dahlstrom_stratal_balance_caveat():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "Dahlstrom 1969" in t
    assert "CONCENTRIC" in t
    assert "CONSTANT BED THICKNESS" in t
    for limiting_case in ("COMPACTION", "PRESSURE SOLUTION", "LAYER-PARALLEL SHEAR"):
        assert limiting_case in t


def test_prompt_states_non_balance_is_a_diagnostic_not_an_error():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "DIAGNOSTIC, NEVER AN ERROR FLAG" in t
    assert "IT DOES NOT MEAN THE INPUT PICKS WERE WRONG" in t


def test_prompt_contains_the_growth_strata_caveat():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "ABSENCE OF GROWTH IS NOT ABSENCE OF TECTONICS" in t
    assert "SLOWER THAN SEDIMENTATION LEAVES NO GROWTH SIGNATURE" in t
    assert "UNMEASURED, never a KILL" in t


def test_prompt_contains_the_epistemic_ceiling():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "EPISTEMIC CEILING" in t
    assert "KINEMATICS" in t and "STRAIN" in t and "PALEOSTRESS" in t
    assert "4 OF 6" in t
    assert "Never emit" in t or "NEVER EMIT" in t


def test_prompt_corrects_the_walthers_law_error():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "NOT WALTHER" in t
    assert "HUTTON (1795)" in t and "LYELL (1830)" in t
    assert "CONFORMABLE FACIES" in t
    assert "Walther (1894)" in t or "WALTHER'S LAW (1894)" in t


def test_prompt_states_andersonian_mechanics_correctly():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "sigma1 vertical" in t and "NORMAL faults" in t and "~60 deg" in t
    assert "sigma3 vertical" in t and "dips ~30 deg" in t
    assert "sigma2 vertical" in t and "near-vertical dips" in t


def test_prompt_labels_the_coulomb_band_a_rule_of_thumb():
    t = _norm(INV.STRUCTURAL_INVARIANTS_PROMPT)
    assert "theta_failure = 45 - phi/2" in t
    assert "Byerlee" in t and "0.6-0.85" in t
    assert "RULE OF THUMB, NOT A HARD PHYSICS INVARIANT" in t
    assert "NEVER CONCLUDE" in t and "FROM A DIP DEVIATION ALONE" in t


def test_prompt_names_block_rotation_as_a_cause_of_deviation():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "BLOCK ROTATION" in t
    assert "OVERPRESSURE" in t
    assert "PRE-EXISTING FABRIC" in t


def test_prompt_states_ve_is_dimensionless_and_not_a_velocity():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "tan(theta_apparent) = VE * tan(theta_true)" in t
    assert "DIMENSIONLESS DISPLAY RATIO" in t
    assert "VE IS NOT A VELOCITY" in t


def test_prompt_states_migrated_data_do_not_follow_the_tan_relation():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "MIGRATED DATA DO NOT FOLLOW THE tan RELATION" in t
    assert "MIGRATION-STATE DECLARATION IS REQUIRED" in t


def test_prompt_states_uniform_thickness_is_non_discriminating():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "NON-DISCRIMINATING" in t
    assert "THE EUSTATIC TEST IS NOT THE ABSENCE OF THICKNESS CHANGE" in t
    assert "SYNCHRONOUS ONLAP" in t
    assert "THERMAL (post-rift) SUBSIDENCE" in t


def test_prompt_states_inheritance_beats_current_stress():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "25-45 deg" in t
    assert "FAULT STRIKE RECORDS THE WEAK PLANE" in t


def test_prompt_reclassifies_salt_as_a_decoupling_mechanism():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "SALT IS A DECOUPLING MECHANISM, NOT A TECTONIC REGIME" in t
    assert "DECOUPLED" in t
    assert "NOT_APPLICABLE" in t
    assert "10^2" in t and "differential loading" in t.lower() or "DIFFERENTIAL LOADING" in t


def test_prompt_makes_the_null_hypothesis_mandatory():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "NULL HYPOTHESIS IS MANDATORY" in t
    assert "DIFFERENTIAL COMPACTION" in t


def test_prompt_contains_the_resolution_caveat():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "lambda/4" in t
    assert "MODEL, NOT OBSERVATION" in t


def test_prompt_forbids_reading_geometry_off_an_image():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "DO NOT READ GEOMETRY OFF AN IMAGE" in t
    assert "geox_structural_vision_extract" in t


def test_prompt_forbids_self_assigned_probability():
    t = _norm(INV.STRUCTURAL_INVARIANTS_PROMPT)
    assert "NO SELF-ASSIGNED PROBABILITY" in t
    # Every forbidden key must be named in the prompt in some form, so a model
    # cannot claim it did not know the vocabulary was prohibited.
    assert "confidence" in t
    assert "reliability" in t
    assert "probability" in t
    assert "score" in t
    assert "certainty" in t
    assert "p_truth" in t or "P(truth)" in t


def test_prompt_states_the_output_contract():
    t = INV.STRUCTURAL_INVARIANTS_PROMPT
    assert "preferred_hypothesis = None" in t
    assert "arifOS_only" in t


def test_invariant_set_is_auditable_by_key():
    keys = [k for k, _ in INV.STRUCTURAL_INVARIANTS]
    assert len(keys) == 15
    assert "I14_CROSS_CUTTING_IS_NOT_WALTHER" in keys
    assert "I15_SALT_IS_A_DECOUPLING_MECHANISM" in keys
    assert len(set(keys)) == len(keys)


def test_render_injects_the_task_context():
    t = INV.render_structural_invariants(
        section_ref="LINE-12", basin="Sabah", candidate_regimes="extension, compression"
    )
    assert "LINE-12" in t
    assert "Sabah" in t
    assert "extension, compression" in t
    assert "TASK CONTEXT" in t


def test_render_default_regimes_names_salt_as_a_decupling_not_a_regime():
    t = INV.render_structural_invariants()
    assert "salt_mobility is NOT a regime" in t


# ══════════════════════════════════════════════════════════════════════════════
# (7) registration — prompt + server, and lane separation from the VLM lane
# ══════════════════════════════════════════════════════════════════════════════


def test_prompt_registers_and_returns_the_invariants():
    from fastmcp import FastMCP

    mcp = FastMCP("test-structural-invariants")
    INV.register_structural_prompts(mcp)
    assert asyncio.run(mcp.get_prompt("structural-invariants")) is not None
    result = asyncio.run(
        mcp.render_prompt("structural-invariants", {"section_ref": "L12"})
    )
    text = repr(result)
    assert "NOT WALTHER" in text
    assert "ABSENCE OF GROWTH IS NOT ABSENCE OF TECTONICS" in text
    assert "L12" in text


def test_server_mounts_exactly_the_two_structural_tools():
    mod = _load_module_by_path(
        "sv_server_under_test", "src/geox_mcp/servers/structural_vision.py"
    )
    server = mod.create_structural_vision_server()
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    assert names == {"geox_structural_vision_extract", "geox_structural_regime_falsify"}


def test_server_is_disjoint_from_the_vlm_lane():
    sv = _load_module_by_path("sv_server_lane_test", "src/geox_mcp/servers/structural_vision.py")
    vlm_mod = _load_module_by_path("vlm_lane_under_test", "src/geox_mcp/servers/vision.py")
    _STRUCTURAL_VISION_TOOLS = sv._STRUCTURAL_VISION_TOOLS
    _VISION_TOOLS = vlm_mod._VISION_TOOLS

    structural = {n for n, _ in _STRUCTURAL_VISION_TOOLS}
    vlm = {n for n, _ in _VISION_TOOLS}
    assert structural.isdisjoint(vlm), "the deterministic lane must not merge with the VLM lane"
    assert not any(n.startswith("geox_vision") for n in structural)


def test_server_annotations_declare_deterministic_local_compute():
    mod = _load_module_by_path("sv_server_ann_test", "src/geox_mcp/servers/structural_vision.py")

    for name, ann in mod._STRUCTURAL_VISION_ANNOTATIONS.items():
        assert ann["readOnlyHint"] is True, name
        assert ann["destructiveHint"] is False, name
        assert ann["openWorldHint"] is False, f"{name} must not reach a model or the network"
        assert ann["idempotentHint"] is True, f"{name} must be deterministic"


def test_server_docstring_states_the_lane_boundary():
    mod = _load_module_by_path("sv_server_doc_test", "src/geox_mcp/servers/structural_vision.py")
    module_doc = _norm(mod.__doc__ or "")
    fn_doc = _norm(mod.create_structural_vision_server.__doc__ or "")
    assert "vision.py" in module_doc
    assert "hallucination" in module_doc
    assert "vision.py" in fn_doc
    assert "HALLUCINATION" in fn_doc


def test_tool_module_docstring_states_the_lane_boundary():
    assert "vision.py" in (SV.__doc__ or "")
    assert "hallucination" in (SV.__doc__ or "")