"""K-REGIME — tectonic regime falsification tests.

Contract under test:
  1. preferred_hypothesis is ALWAYS None (GEOX proposes, arifOS seals).
  2. UNMEASURED is never silently upgraded to PASS.
  3. Absence of a growth wedge does NOT kill extension (no growth != no tectonics).
  4. A DYNAMIC (stress tensor) claim without fault-slip data is KILLED.
  5. EI <= 1 measured DOES kill the syn-tectonic timing claim (scoped).
  6. Non-balance is a diagnostic, never a "bad pick" verdict.
  7. Salt buoyancy-only driver with weak density contrast is KILLED.
  8. The null (depositional) hypothesis is always a mandatory competitor.
  9. Every gate carries epistemic_tier + receipt_hash.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from geox_mcp.tools.structure_gates.tectonic_regime import (
    REGIME_FALSIFIERS,
    falsify_regime,
    run_regime_falsification,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


def _full_extensional_bundle() -> dict:
    return {
        "horizons": [
            {"name": "H1", "coverage_pct": 80, "geometry": {"dip_deg": 12.0, "vergence": "SE"}},
            {"name": "H2", "coverage_pct": 75, "geometry": {"dip_deg": 18.0, "vergence": "SE"}},
        ],
        "intervals": [
            {"name": "syn-rift", "decompacted": True, "spatial_differential": True,
             "expansion_index": 1.8, "isopach_reversal": False},
            {"name": "post-rift", "decompacted": True, "spatial_differential": True,
             "expansion_index": 1.05, "isopach_reversal": False},
        ],
        "faults": [
            {"name": "F1", "dip_deg": 58.0, "slip_sense": "normal", "throw_m": 300.0,
             "heave_m": 200.0, "polarity_switch": True},
            {"name": "F2", "dip_deg": 62.0, "slip_sense": "normal", "throw_m": 250.0,
             "heave_m": 180.0},
        ],
        "display": {"vertical_exaggeration": 1.0, "velocity_model": True, "time_domain": False,
                    "migration_state": "migrated"},
        "resolution": {"tuning_thickness_lambda4": 25.0, "min_mapped_feature_thickness": 60.0},
        "cross_cutting": [{"younger": "F1", "older": "H2", "type": "offset"}],
        "restore": {"plane_strain": True, "decompacted": True,
                    "bed_length_before_m": 10000.0, "bed_length_after_m": 10000.0},
        "compaction": {"assessed": True},
    }


def _empty_bundle() -> dict:
    return {}


# ── Contract 1: never seal ───────────────────────────────────────────────────


def test_preferred_hypothesis_always_none():
    for fw in (_full_extensional_bundle(), _empty_bundle()):
        out = run_regime_falsification(fw)
        assert out["preferred_hypothesis"] is None
        assert out["seal_authority"] == "arifOS_only"
        assert out["local_verdict"] == "QUALIFIED_CANDIDATE"


def test_no_hypothesis_status_is_a_seal():
    out = run_regime_falsification(_full_extensional_bundle())
    for h in out["hypotheses"]:
        assert h["status"] in {
            "REJECTED", "SURVIVES_CURRENT_TESTS", "UNTESTED", "INCONCLUSIVE"
        }


# ── Contract 2: UNMEASURED != PASS ───────────────────────────────────────────


def test_empty_bundle_yields_no_survivors():
    out = run_regime_falsification(_empty_bundle())
    assert out["surviving"] == [], "empty input must not produce a surviving regime"
    assert out["overall"] in ("INSUFFICIENT_EVIDENCE", "ALL_CANDIDATES_REJECTED")
    assert out["governance_status"] == "HOLD"
    for h in out["hypotheses"]:
        assert h["status"] == "UNTESTED", f"{h['regime']} claimed {h['status']} with zero data"


def test_every_gate_carries_tier_and_hash():
    out = run_regime_falsification(_full_extensional_bundle())
    for receipt in out["universal_gates"].values():
        assert receipt["epistemic_tier"] in ("KINEMATIC", "STRAIN", "DYNAMIC")
        assert len(receipt["receipt_hash"]) == 64
    for h in out["hypotheses"]:
        for receipt in h["gates"].values():
            assert receipt["epistemic_tier"] in ("KINEMATIC", "STRAIN", "DYNAMIC")
            assert len(receipt["receipt_hash"]) == 64


# ── Contract 3: growth-strata blindness (the expensive bug) ──────────────────


def test_missing_growth_does_not_kill_extension():
    """A fault slower than sedimentation leaves NO growth wedge. Not evidence of absence."""
    fw = _full_extensional_bundle()
    fw.pop("intervals")
    fw["faults"] = [{"name": "F1", "dip_deg": 58.0, "slip_sense": "normal", "throw_m": 300.0,
                     "heave_m": 200.0, "polarity_switch": True}]
    result = falsify_regime("extension", fw)
    growth = result["gates"]["K-EXT-GROWTH"]
    assert growth["status"] == "UNMEASURED", (
        "absence of a growth wedge must be UNMEASURED, never KILL"
    )
    assert "K-EXT-GROWTH" not in result["kills"]
    assert "blind at both ends" in growth["reason"]


def test_measured_low_ei_kills_syn_tectonic_claim_only():
    fw = _full_extensional_bundle()
    fw["growth"] = {"expansion_index": 1.0}
    result = falsify_regime("extension", fw)
    g = result["gates"]["K-EXT-GROWTH"]
    assert g["status"] == "KILL"
    assert g["scope"] == "interval_syn_tectonic_claim", (
        "EI<=1 kills the TIMING claim, not extension itself"
    )


def test_high_ei_is_warn_not_pass():
    fw = _full_extensional_bundle()
    fw["growth"] = {"expansion_index": 2.4}
    g = falsify_regime("extension", fw)["gates"]["K-EXT-GROWTH"]
    assert g["status"] == "WARN", "EI>1 supports but never proves — mimic caveat applies"


# ── Contract 4: the epistemic ceiling ────────────────────────────────────────


def test_stress_tensor_claim_without_slip_data_is_killed():
    fw = _full_extensional_bundle()
    fw["claim"] = {"epistemic_tier": "DYNAMIC"}
    out = run_regime_falsification(fw)
    assert out["universal_gates"]["K-REGIME-CEILING"]["status"] == "KILL"
    assert out["overall"] == "HOLD"
    assert out["governance_status"] == "HOLD"


def test_stress_tensor_claim_permitted_with_slip_data():
    fw = _full_extensional_bundle()
    fw["claim"] = {"epistemic_tier": "DYNAMIC"}
    fw["fault_slip_data"] = [{"plane": 1}, {"plane": 2}, {"plane": 3}, {"plane": 4}]
    out = run_regime_falsification(fw)
    assert out["universal_gates"]["K-REGIME-CEILING"]["status"] == "PASS"


def test_zero_shortening_kills_compression():
    fw = _full_extensional_bundle()
    result = falsify_regime("compression", fw)
    assert result["gates"]["K-COMP-SHORTEN"]["status"] == "KILL"
    assert result["status"] == "REJECTED"


def test_nonzero_shortening_does_not_kill_compression():
    fw = _full_extensional_bundle()
    fw["restore"]["bed_length_after_m"] = 8000.0  # 2000 m shortening
    result = falsify_regime("compression", fw)
    assert result["gates"]["K-COMP-SHORTEN"]["status"] == "PASS"


# ── Contract 6: non-balance is a diagnostic ──────────────────────────────────


def test_compression_unmeasured_without_restoration():
    fw = _full_extensional_bundle()
    fw.pop("restore")
    g = falsify_regime("compression", fw)["gates"]["K-COMP-SHORTEN"]
    assert g["status"] == "UNMEASURED"
    assert "cannot be killed OR confirmed" in g["reason"]


# ── Contract 7: salt driver ──────────────────────────────────────────────────


def test_buoyancy_only_diapir_driver_killed_when_contrast_weak():
    fw = {"salt": {"present": True, "driver": "buoyancy", "density_contrast_kg_m3": 100.0}}
    g = falsify_regime("salt_mobility", fw)["gates"]["K-SALT-DRIVER"]
    assert g["status"] == "KILL"
    assert g["scope"] == "mechanism_claim"
    assert any("differential loading" in r for r in g["evidence_refs"])


def test_differential_loading_driver_passes():
    fw = {"salt": {"present": True, "driver": "differential_loading",
                   "density_contrast_kg_m3": 100.0}}
    assert falsify_regime("salt_mobility", fw)["gates"]["K-SALT-DRIVER"]["status"] == "PASS"


def test_salt_absent_is_not_applicable_not_kill():
    fw = {"salt": {"present": False}}
    assert falsify_regime("salt_mobility", fw)["gates"]["K-SALT-BODY"]["status"] == "NOT_APPLICABLE"


# ── Contract 8: null hypothesis + minimum competing hypotheses ───────────────


def test_null_hypothesis_always_present():
    out = run_regime_falsification(
        _full_extensional_bundle(), candidate_regimes=["extension"], min_hypotheses=2
    )
    regimes = [h["regime"] for h in out["hypotheses"]]
    assert "null_depositional" in regimes, "the null hypothesis must always compete"
    assert regimes != ["extension"], "null was not appended"


def test_null_hypothesis_registered_even_when_check_fails():
    out = run_regime_falsification(
        _full_extensional_bundle(), candidate_regimes=["extension"], min_hypotheses=3
    )
    assert out["ok"] is False
    assert "null_depositional" in out["candidates"], "null must be appended before the gate check"


def test_insufficient_competing_hypotheses_holds():
    out = run_regime_falsification(
        _full_extensional_bundle(), candidate_regimes=["extension"], min_hypotheses=3
    )
    # extension + null = 2 < 3
    assert out["ok"] is False
    assert out["error"] == "INSUFFICIENT_COMPETING_HYPOTHESES"
    assert out["governance_status"] == "HOLD"


def test_unknown_regime_holds():
    out = run_regime_falsification(_full_extensional_bundle(), candidate_regimes=["vibes"])
    assert out["ok"] is False
    assert out["error"] == "UNKNOWN_REGIME"
    assert out["governance_status"] == "HOLD"


# ── Contract 9: strike-slip diagnostics ──────────────────────────────────────


def test_facies_change_alone_is_not_strike_slip_evidence():
    fw = {"horizons": [{"name": "H1", "coverage_pct": 90, "geometry": {"dip_deg": 5.0}}]}
    g = falsify_regime("strike_slip", fw)["gates"]["K-SS-MARKER"]
    assert g["status"] == "UNMEASURED"
    assert "NOT a strike-slip diagnostic" in g["reason"]


def test_near_zero_throw_passes_strike_slip_signature():
    fw = {"faults": [{"name": "F1", "dip_deg": 88.0, "slip_sense": "strike_slip",
                      "throw_m": 5.0, "heave_m": 900.0}]}
    assert falsify_regime("strike_slip", fw)["gates"]["K-SS-THROW"]["status"] == "PASS"


# ── Contract 10: display / decompaction / resolution honesty ─────────────────


def test_display_gate_unmeasured_when_ve_unknown():
    fw = _full_extensional_bundle()
    fw.pop("display")
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-DISPLAY"]
    assert g["status"] == "UNMEASURED"
    assert "vertical_exaggeration unknown" in g["reason"]


def test_display_gate_unmeasured_when_ve_declared():
    fw = _full_extensional_bundle()
    fw["display"] = {"vertical_exaggeration": 3.0, "velocity_model": True}
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-DISPLAY"]
    assert g["status"] == "UNMEASURED"
    assert "apparent dips inflated" in g["reason"]


def test_decompaction_gate_unmeasured_without_flag():
    fw = {"intervals": [{"name": "I1", "expansion_index": 1.4}]}
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-DECOMPACT"]
    assert g["status"] == "UNMEASURED"


def test_sub_tuning_feature_warns():
    fw = _full_extensional_bundle()
    fw["resolution"] = {"tuning_thickness_lambda4": 40.0, "min_mapped_feature_thickness": 12.0}
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-RESOLUTION"]
    assert g["status"] == "WARN"


def test_uniform_isopach_is_non_discriminating_not_null_evidence():
    """Uniform thickness has many parents — it is NOT evidence for eustatic control."""
    fw = _full_extensional_bundle()
    for i in fw["intervals"]:
        i["spatial_differential"] = False
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-DIFFERENTIAL"]
    assert g["status"] == "WARN"
    assert g["calculated_result"]["discriminating"] is False
    alts = " ".join(g["calculated_result"]["alternatives_not_excluded"]).lower()
    assert "strike-slip" in alts, "pure strike-slip produces no thickness variation and must be listed"
    assert "thermal subsidence" in alts
    assert "favours" not in g["calculated_result"], (
        "uniform thickness must not be recorded as favouring the null hypothesis"
    )


def test_migration_state_unknown_blocks_dip_trust():
    fw = _full_extensional_bundle()
    fw["display"] = {"vertical_exaggeration": 1.0, "velocity_model": True,
                     "time_domain": False, "migration_state": "unknown"}
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-DISPLAY"]
    assert g["status"] == "UNMEASURED"
    assert "migration_state unknown" in g["reason"]


def test_migration_state_declared_permits_pass():
    fw = _full_extensional_bundle()
    fw["display"] = {"vertical_exaggeration": 1.0, "velocity_model": True,
                     "time_domain": False, "migration_state": "migrated"}
    g = run_regime_falsification(fw)["universal_gates"]["K-REGIME-DISPLAY"]
    assert g["status"] == "PASS"


def test_candidate_categories_are_ontologically_explicit():
    out = run_regime_falsification(_full_extensional_bundle())
    cats = {h["regime"]: h["category"] for h in out["hypotheses"]}
    assert cats["extension"] == "regime"
    assert cats["salt_mobility"] == "decoupling_mechanism", (
        "salt does not express the regional stress field — it masks it"
    )
    assert cats["null_depositional"] == "null_hypothesis"


def test_coulomb_deviation_never_kills_and_lists_block_rotation():
    fw = {"faults": [{"name": "F1", "dip_deg": 25.0, "slip_sense": "normal", "throw_m": 100.0,
                      "heave_m": 100.0}]}
    g = falsify_regime("extension", fw)["gates"]["K-EXT-DIP"]
    assert g["status"] == "WARN", "a dip deviation is a rule-of-thumb signal, never a KILL"
    alts = " ".join(g["exceptions_considered"]).lower()
    assert "block rotation" in alts, "block rotation preserves pure extension and must be listed"


# ── Contract 12: null point is local, never basin-wide ───────────────────────


def test_nullpoint_kill_does_not_generalise_basin_wide():
    fw = {"gravity": {"listric": True, "rollover": True, "toe_thrust": True,
                      "same_decollement": True, "coeval": True,
                      "total_extension_m": 5000.0, "total_shortening_m": 1200.0}}
    g = falsify_regime("gravity_tectonics", fw)["gates"]["K-GRAV-NULLPOINT"]
    assert g["status"] == "KILL"
    assert g["scope"] == "linked_system_only", (
        "a null-point failure kills the system, never the basin"
    )
    assert g["calculated_result"]["generalise_basin_wide"] is False


def test_nullpoint_unmeasured_when_balance_terms_absent():
    fw = {"gravity": {"listric": True, "rollover": True, "toe_thrust": True,
                      "same_decollement": True, "coeval": True}}
    g = falsify_regime("gravity_tectonics", fw)["gates"]["K-GRAV-NULLPOINT"]
    assert g["status"] == "UNMEASURED"
    assert g["scope"] == "linked_system_only"


def test_nullpoint_balanced_system_passes():
    fw = {"gravity": {"listric": True, "rollover": True, "toe_thrust": True,
                      "same_decollement": True, "coeval": True,
                      "total_extension_m": 5000.0, "total_shortening_m": 5000.0}}
    out = falsify_regime("gravity_tectonics", fw)
    assert out["gates"]["K-GRAV-NULLPOINT"]["status"] == "PASS"
    assert out["status"] == "SURVIVES_CURRENT_TESTS"


def test_gravity_incomplete_linkage_is_unmeasured_not_rejected():
    fw = {"gravity": {"listric": True, "rollover": True}}
    out = falsify_regime("gravity_tectonics", fw)
    assert out["gates"]["K-GRAV-LINKAGE"]["status"] == "UNMEASURED"
    assert out["status"] != "REJECTED"


# ── Contract 11: well-formed full bundle behaves ─────────────────────────────


def test_extensional_bundle_survives_and_reports_coverage():
    out = run_regime_falsification(_full_extensional_bundle())
    assert out["overall"] == "CANDIDATES_SURVIVE"
    assert "extension" in out["surviving"]
    assert out["falsification_coverage"] > 0
    assert out["n_hypotheses"] >= 7
    # verifiable: every regime has a registered falsifier set
    assert set(REGIME_FALSIFIERS) == {
        "extension", "compression", "strike_slip", "inversion",
        "salt_mobility", "gravity_tectonics", "null_depositional",
    }
