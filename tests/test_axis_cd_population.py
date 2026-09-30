"""AXIS C + AXIS D — fault-orientation population and stratal-termination tests.

Covers the mandated behaviours:
  (a) a synthetic conjugate normal-fault set at +/-30 deg about a known axis
      recovers that bisector within tolerance and flags conjugate presence;
  (b) a deliberately too-small population returns UNMEASURED (not a bisector);
  (c) the inheritance caveat string is present in the receipt;
  (d) a synthetic onlap geometry is classified as onlap;
  (e) a synthetic truncated surface is classified as truncation;
  (f) an abutting (zero-offset) horizon is NOT classified as younger than the fault;

plus the iron rules that make the extractors usable: epistemic ceilings, coverage
deficits, no fabricated confidence, determinism, and numpy-free JSON.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pytest

from geox_core.engines.seismic.axis_cd_population import (
    ABSOLUTE_AGE_REQUIREMENT,
    FAULT_ABUT_PITFALL,
    GEOMETRY_TYPE_ALIGNMENT,
    INHERITANCE_CAVEAT,
    MIN_POPULATION_N,
    RELATIVE_CHRONOLOGY_CAVEAT,
    TERMINATION_CLASSES,
    analyse_fault_orientation_population,
    classify_stratal_terminations,
    surfaces_from_amplitude_ridges,
)

# ── helpers ──────────────────────────────────────────────────────────────────

AXIS_DEG = 110.0
THETA_DEG = 30.0  # conjugate half-angle
DIP_DEG = 60.0    # Andersonian normal-fault dip


def axial_distance(a: float, b: float) -> float:
    """Unsigned separation of two axes (mod 180) in [0, 90] deg."""
    d = abs(a % 180.0 - b % 180.0) % 180.0
    return min(d, 180.0 - d)


def conjugate_faults(n_per_mode: int = 6, axis: float = AXIS_DEG, dip: float = DIP_DEG) -> list[dict]:
    """Sites carry an EVEN mode mix so the split-half rotation test is not confounded."""
    perturbation = [0.8, -0.5, 0.3, -0.7, 0.6, -0.2]
    sites = [(0.0, 0.0), (500.0, 200.0), (1000.0, 400.0)]
    rows: list[dict] = []
    per_site_per_mode = max(1, n_per_mode // len(sites))
    for si, (x, y) in enumerate(sites):
        for mode, offset in enumerate((-THETA_DEG, +THETA_DEG)):
            for k in range(per_site_per_mode):
                i = len(rows)
                rows.append({
                    "fault_id": f"F{i:03d}",
                    "strike_deg": axis + offset + perturbation[i % len(perturbation)],
                    "dip_deg": dip + 0.3 * math.sin(i),
                    "x": x + 10.0 * k,
                    "y": y + 10.0 * mode,
                })
    return rows


def ref_slope_deg(deg: float, x_max: float = 1000.0, n: int = 21) -> dict:
    """Reference surface dipping `deg` toward +x, anchored at the origin."""
    t = math.tan(math.radians(deg))
    return {
        "surface_id": "REF",
        "kind": "reference_surface",
        "points": [(float(x), float(t * x)) for x in np.linspace(0.0, x_max, n)],
    }


def shallow_ref(x_max: float = 400.0, n: int = 21) -> dict:
    return {
        "surface_id": "REF",
        "kind": "reference_surface",
        "points": [(float(x), float(100.0 + 0.05 * x)) for x in np.linspace(0.0, x_max, n)],
    }


# ══════════════════════════════════════════════════════════════════════════════
# AXIS C
# ══════════════════════════════════════════════════════════════════════════════


class TestAxisCConjugatePopulation:
    """(a) synthetic conjugate normal-fault set recovers the bisector."""

    def test_recovers_acute_bisector_and_flags_conjugate(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="depth")

        assert receipt["status"] == "PASS", receipt["reason"]
        cr = receipt["calculated_result"]
        conjugate = cr["conjugate"]
        assert conjugate["present"] is True
        assert conjugate["mode_separation_deg"] == pytest.approx(2 * THETA_DEG, abs=2.0)
        assert conjugate["valley_ratio"] is not None

        bisector = cr["acute_bisector_azimuth_deg"]
        assert bisector is not None
        assert axial_distance(bisector, AXIS_DEG) <= 3.0, (bisector, AXIS_DEG)
        assert cr["acute_bisector_half_angle_deg"] == pytest.approx(THETA_DEG, abs=2.0)

    def test_acute_bisector_is_the_across_angle_one(self):
        """The acute bisector must bisect the SHORT arc between the two modes."""
        cr = analyse_fault_orientation_population(conjugate_faults(), domain="depth")["calculated_result"]
        m1, m2 = cr["conjugate"]["mode_azimuths_deg"]
        acute = cr["acute_bisector_azimuth_deg"]
        obtuse = cr["obtuse_bisector_azimuth_deg"]
        assert axial_distance(acute, m1) <= 45.0
        assert axial_distance(acute, m2) <= 45.0
        assert axial_distance(obtuse, m1) == pytest.approx(90.0 - axial_distance(acute, m1), abs=0.5)
        assert axial_distance(acute, obtuse) == pytest.approx(90.0, abs=0.5)

    def test_strike_rose_is_binned_and_counts_every_measurement(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        cr = receipt["calculated_result"]
        rose = cr["strike_rose"]
        assert len(rose) == cr["n_bins"] == 18  # 180 / 10 deg
        assert sum(b["count"] for b in rose) == cr["n_measured"]
        assert all(b["bin_end_deg"] - b["bin_start_deg"] == pytest.approx(10.0) for b in rose)

    def test_candidate_sigma1_is_a_candidate_only(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        cr = receipt["calculated_result"]
        assert cr["regime_candidate"] == "normal"
        assert axial_distance(cr["candidate_sigma1_azimuth_deg"], AXIS_DEG) <= 3.0
        assert cr["candidate_sigma1_basis"] is not None
        # never a tensor, never DYNAMIC, never a confidence
        assert cr["stress_tensor_emitted"] is None
        assert receipt["epistemic_tier"] == "KINEMATIC"
        assert receipt["confidence"] is None

    def test_andersonian_deviation_enumerates_alternatives_not_regime_change(self):
        """Iron rule 6: beyond the tolerance the answer is alternatives, never 'regime changed'."""
        # 8 deg mean dip: outside every Andersonian reference (the only reachable
        # non-Andersonian population is a low-angle one).
        shallow = conjugate_faults(dip=8.0)
        receipt = analyse_fault_orientation_population(shallow, domain="depth")
        cr = receipt["calculated_result"]
        cross = cr["anderson_cross_check"]
        assert cross["within_tolerance"] is False
        assert cross["deviation_deg"] > 15.0
        assert cross["nearest_reference"] == "thrust"
        assert cross["reachability_note"]
        assert len(cross["alternatives_if_outside_tolerance"]) >= 4
        assert any("inherited" in a.lower() for a in cross["alternatives_if_outside_tolerance"])
        assert "not evidence that the regime changed" in json.dumps(cross).lower()
        assert cr["regime_candidate"] is None
        assert cr["candidate_sigma1_azimuth_deg"] is None
        assert receipt["status"] == "WARN"


class TestAxisCUnmeasured:
    """(b) too small a population is UNMEASURED, never a low-precision bisector."""

    def test_small_population_returns_unmeasured_and_no_bisector(self):
        small = conjugate_faults()[:4]
        receipt = analyse_fault_orientation_population(small, domain="depth")

        assert receipt["status"] == "UNMEASURED"
        cr = receipt["calculated_result"]
        assert cr["acute_bisector_azimuth_deg"] is None
        assert cr["candidate_sigma1_azimuth_deg"] is None
        assert cr["conjugate"] is None
        assert cr["insufficient_population"] is True

    def test_min_n_is_declared_with_its_justification(self):
        receipt = analyse_fault_orientation_population(conjugate_faults()[:4], domain="depth")
        thresholds = receipt["thresholds"]
        assert thresholds["min_population_n"] == MIN_POPULATION_N
        basis = thresholds["min_population_n_basis"]
        assert "sqrt" in basis and "precision" in basis.lower()
        assert receipt["missing_inputs"], "the missing input must be named"

    def test_unmeasured_is_not_a_pass_and_not_a_kill(self):
        receipt = analyse_fault_orientation_population([], domain="depth")
        assert receipt["status"] == "UNMEASURED"
        assert receipt["status"] not in ("PASS", "KILL")

    def test_no_faults_names_the_missing_input(self):
        receipt = analyse_fault_orientation_population(None, domain="depth")
        assert receipt["status"] == "UNMEASURED"
        assert "faults[].strike_deg" in receipt["missing_inputs"]


class TestAxisCCaveats:
    """(c) the inheritance caveat is carried in every receipt layer."""

    def test_inheritance_caveat_present_in_every_layer(self):
        good = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        small = analyse_fault_orientation_population(conjugate_faults()[:3], domain="depth")
        none_at_all = analyse_fault_orientation_population([], domain="depth")

        for receipt in (good, small, none_at_all):
            assert INHERITANCE_CAVEAT in receipt["caveats"]
            assert INHERITANCE_CAVEAT in receipt["calculated_result"]["interpretation_caveats"]
            assert INHERITANCE_CAVEAT in json.dumps(receipt)
            assert "INHERITED FABRIC" in json.dumps(receipt["findings"])

        blob = json.dumps(good).upper()
        assert "CURRENT STRESS INTERSECTED WITH INHERITED FABRIC" in blob
        assert "NOT A PURE STRESS INDICATOR" in blob
        assert "REACTIVATE" in blob


class TestAxisCIronRules:
    """Encoded refusals: DYNAMIC ceiling, time-domain calibration, coverage, Riedel."""

    def test_2d_can_never_enter_the_dynamic_tier(self):
        receipt = analyse_fault_orientation_population(
            conjugate_faults(), domain="depth", claim_stress_tensor=True
        )
        assert receipt["status"] == "KILL"
        assert receipt["sub_gates"]["C-CEILING"]["status"] == "KILL"
        assert receipt["calculated_result"]["stress_tensor_emitted"] is None
        assert "slip" in receipt["sub_gates"]["C-CEILING"]["reason"].lower()
        assert receipt["sub_gates"]["C-CEILING"]["missing_inputs"]

    def test_dynamic_tier_with_2d_slip_data_is_only_partially_measured(self):
        receipt = analyse_fault_orientation_population(
            conjugate_faults(),
            domain="depth",
            fault_slip_data=[{"rake_deg": 90.0}] * 6,
            cutoff_line_3d=False,
            claim_epistemic_tier="DYNAMIC",
        )
        ceiling = receipt["sub_gates"]["C-CEILING"]
        assert ceiling["status"] in ("KILL", "PARTIALLY_MEASURED")
        assert ceiling["calculated_result"]["dynamic_claim_permitted"] is False
        assert receipt["status"] != "PASS"

    def test_time_domain_without_velocity_withholds_every_azimuth(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="time")
        assert receipt["status"] == "UNMEASURED"
        cr = receipt["calculated_result"]
        assert cr["acute_bisector_azimuth_deg"] is None
        assert cr["candidate_sigma1_azimuth_deg"] is None
        assert cr["riedel"] is None
        assert "domain=depth OR velocity_model" in receipt["missing_inputs"]

    def test_time_domain_is_measurable_once_a_velocity_model_is_supplied(self):
        receipt = analyse_fault_orientation_population(
            conjugate_faults(), domain="time", velocity_model={"interval_velocity": 2200.0}
        )
        assert receipt["status"] == "PASS"
        assert receipt["sub_gates"]["C-CALIBRATION"]["status"] == "PASS"

    def test_coverage_deficit_downgrades_to_unmeasured(self):
        rows = conjugate_faults()
        for r in rows[:5]:  # strip 5 of 12 strikes -> coverage 7/12
            r.pop("strike_deg")
        receipt = analyse_fault_orientation_population(rows, domain="depth")
        assert receipt["status"] == "UNMEASURED"
        assert receipt["coverage"] < 0.7
        assert receipt["calculated_result"]["acute_bisector_azimuth_deg"] is None

    def test_absent_readings_never_kill(self):
        """A deficit may only return UNMEASURED — never KILL."""
        rows = conjugate_faults()
        assert analyse_fault_orientation_population(rows[:2], domain="depth")["status"] == "UNMEASURED"
        assert analyse_fault_orientation_population([], domain="depth")["status"] == "UNMEASURED"

    def test_unimodal_population_is_partial_not_a_bisector(self):
        unimodal = [
            {"fault_id": f"U{i}", "strike_deg": 90.0 + 0.4 * i, "dip_deg": 60.0} for i in range(14)
        ]
        receipt = analyse_fault_orientation_population(unimodal, domain="depth")
        assert receipt["status"] == "PARTIALLY_MEASURED"
        assert receipt["calculated_result"]["acute_bisector_azimuth_deg"] is None
        assert receipt["calculated_result"]["conjugate"]["present"] is False

    def test_riedel_relativity_against_a_master_azimuth(self):
        rows = [
            {"fault_id": "R-1", "strike_deg": 15.0, "dip_deg": 90.0},
            {"fault_id": "R-2", "strike_deg": 14.0, "dip_deg": 90.0},
            {"fault_id": "R-3", "strike_deg": 16.0, "dip_deg": 90.0},
            {"fault_id": "R-4", "strike_deg": 15.0, "dip_deg": 90.0},
            {"fault_id": "P-1", "strike_deg": 12.0, "dip_deg": 88.0},
            {"fault_id": "P-2", "strike_deg": 13.0, "dip_deg": 88.0},
            {"fault_id": "P-3", "strike_deg": 11.0, "dip_deg": 88.0},
            {"fault_id": "P-4", "strike_deg": 12.0, "dip_deg": 88.0},
            {"fault_id": "Rp-1", "strike_deg": 75.0, "dip_deg": 90.0},
            {"fault_id": "Rp-2", "strike_deg": 76.0, "dip_deg": 90.0},
            {"fault_id": "Rp-3", "strike_deg": 74.0, "dip_deg": 90.0},
            {"fault_id": "Rp-4", "strike_deg": 75.0, "dip_deg": 90.0},
        ]
        receipt = analyse_fault_orientation_population(rows, master_fault_azimuth_deg=0.0, domain="depth")
        riedel = receipt["sub_gates"]["C-RIEDEL"]
        counts = riedel["calculated_result"]["class_counts"]

        assert riedel["status"] == "PASS"
        assert counts["R_prime"] == 4, counts
        assert counts["P"] == 4, counts
        assert counts["R"] == 4, counts
        assert counts["unclassified"] == 0, counts
        per_fault = {r["fault_id"]: r for r in riedel["calculated_result"]["per_fault"]}
        assert per_fault["Rp-1"]["shear_relationship"] == "antithetic"
        assert per_fault["Rp-1"]["riedel_primary"] == "R_prime"
        assert per_fault["R-1"]["shear_relationship"] == "synthetic"
        assert per_fault["P-1"]["shear_relationship"] == "synthetic"

    def test_riedel_absent_is_unmeasured_not_kill(self):
        """No fault falls inside any Riedel window of this master (deltas 30 and 90 deg)."""
        receipt = analyse_fault_orientation_population(
            conjugate_faults(), master_fault_azimuth_deg=50.0, domain="depth"
        )
        riedel = receipt["sub_gates"]["C-RIEDEL"]
        assert riedel["status"] == "UNMEASURED"
        assert riedel["coverage"] == 0.0
        assert receipt["status"] != "KILL"

    def test_riedel_not_applicable_without_a_master(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        assert receipt["sub_gates"]["C-RIEDEL"]["status"] == "NOT_APPLICABLE"
        assert "master_fault_azimuth_deg" in receipt["sub_gates"]["C-RIEDEL"]["missing_inputs"]

    def test_no_fabricated_confidence_anywhere(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        assert receipt["confidence"] is None
        assert receipt["confidence_basis"] is None
        assert receipt["confidence_status"] == "NOT_ESTABLISHED_NO_VALIDATED_BENCHMARK"

        forbidden_keys = {"reliability", "probability", "confidence_score", "certainty", "likelihood"}
        found: list[str] = []

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    if str(k).lower() in forbidden_keys:
                        found.append(str(k))
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(receipt)
        assert found == [], f"fabricated confidence/probability keys present: {found}"

    def test_receipt_contract_and_json_cleanliness(self):
        receipt = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        assert len(receipt["receipt_hash"]) == 64
        json.dumps(receipt)  # no default=str: numpy must not leak into a receipt
        for required in ("equation", "thresholds", "calculated_result", "exceptions_considered",
                         "evidence_refs", "missing_inputs", "receipt_hash"):
            assert required in receipt, required

    def test_deterministic_reproducible_receipt_hash(self):
        a = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        b = analyse_fault_orientation_population(conjugate_faults(), domain="depth")
        assert a["receipt_hash"] == b["receipt_hash"]
        assert a == b


class TestAxisCRobustness:

    def test_axis_wraparound_is_treated_as_one_mode_not_two(self):
        """179.9 deg and 0.1 deg are one axial direction, 0.2 deg apart."""
        rows = [{"fault_id": f"W{i}", "strike_deg": 179.9 if i % 2 else 0.1, "dip_deg": 60.0} for i in range(12)]
        receipt = analyse_fault_orientation_population(rows, domain="depth")
        assert receipt["status"] == "PARTIALLY_MEASURED"
        assert receipt["calculated_result"]["acute_bisector_azimuth_deg"] is None

    def test_perpendicular_modes_have_no_unique_acute_bisector(self):
        rows = [{"fault_id": f"P{i}", "strike_deg": 0.0, "dip_deg": 90.0} for i in range(6)]
        rows += [{"fault_id": f"Q{i}", "strike_deg": 90.0, "dip_deg": 90.0} for i in range(6)]
        receipt = analyse_fault_orientation_population(rows, domain="depth")
        assert receipt["status"] == "PARTIALLY_MEASURED"
        assert receipt["calculated_result"]["acute_bisector_azimuth_deg"] is None
        assert any("perpendicular" in r for r in receipt["calculated_result"]["conjugate"]["reasons"])

    def test_strike_and_dip_aliases_are_accepted(self):
        rows = [{"id": f"S{i}", "strike": 80.0, "dip": 60.0} for i in range(6)]
        rows += [{"id": f"T{i}", "azimuth_deg": 140.0, "dip_deg": 60.0} for i in range(6)]
        receipt = analyse_fault_orientation_population(rows, domain="depth")
        assert receipt["status"] == "PASS"
        assert axial_distance(receipt["calculated_result"]["acute_bisector_azimuth_deg"], AXIS_DEG) <= 3.0

    def test_garbage_input_never_raises_and_never_fabricates(self):
        cases: Any = (
            [{}],
            [{"strike_deg": "abc"}],
            [{"strike_deg": float("nan")}] * 20,
            [None] * 12,
        )
        for rows in cases:
            receipt = analyse_fault_orientation_population(rows, domain="depth")
            assert receipt["status"] == "UNMEASURED"
            assert receipt["calculated_result"]["acute_bisector_azimuth_deg"] is None
            json.dumps(receipt)


# ══════════════════════════════════════════════════════════════════════════════
# AXIS D
# ══════════════════════════════════════════════════════════════════════════════


def onlap_inputs() -> tuple[dict, list[dict]]:
    """Horizontal beds above a 20 deg slope, each terminating at its UPDIP end."""
    ref = ref_slope_deg(20.0, x_max=1000.0)
    t = math.tan(math.radians(20.0))
    beds = []
    for sid, z0 in (("A", 100.0), ("B", 50.0)):
        x_terminate = z0 / t
        xs = np.linspace(x_terminate, 1000.0, 21)
        beds.append({
            "surface_id": sid,
            "kind": "strata",
            "points": [(float(x), float(z0)) for x in xs],
        })
    return ref, beds


def truncation_inputs() -> tuple[dict, list[dict]]:
    """Steep beds below a shallow surface, cut by it at a large angle."""
    ref = shallow_ref()
    xs = np.linspace(0.0, 400.0, 21)
    zs = 450.0 - (450.0 - 120.0) / 400.0 * xs
    zs[-1] = 100.0 + 0.05 * 400.0  # terminate exactly on the reference surface
    bed = {"surface_id": "C", "kind": "strata", "points": [(float(a), float(b)) for a, b in zip(xs, zs)]}
    return ref, [bed]


def abutting_horizon() -> dict:
    return {
        "surface_id": "H1",
        "kind": "strata",
        "points": [(0.0, 500.0), (255.0, 525.0), (510.0, 550.0)],
    }


def fault_trace(offset_m: float | None) -> dict:
    fault = {
        "surface_id": "F1",
        "kind": "fault",
        "points": [(510.0, -500.0), (510.0, 800.0)],
    }
    if offset_m is not None:
        fault["offset_m"] = offset_m
    return fault


class TestAxisDTerminationClasses:

    def test_onlap_geometry_is_classified_as_onlap(self):
        """(d) horizontal beds lapping onto an inclined surface, terminating updip."""
        ref, beds = onlap_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        cr = receipt["calculated_result"]

        assert receipt["status"] == "PASS", receipt["reason"]
        assert cr["classification_counts"].get("onlap") == 2, cr["classification_counts"]
        for entry in cr["terminations"]:
            assert entry["classification"] == "onlap"
            assert entry["side"] == "above"
            assert entry["relative_dip_deg"] < 0  # beds flatter than the surface in the dip sense
            x_t, z_t = entry["termination_xy"]
            assert z_t == pytest.approx(math.tan(math.radians(20.0)) * x_t, abs=1.0)

        for edge in cr["chronology_partial_order"]:
            assert edge["older"] == "REF"
            assert edge["relation"] == "HORIZON_YOUNGER_THAN_REFERENCE"
        assert cr["partial_order_acyclic"] is True

    def test_truncated_surface_is_classified_as_truncation(self):
        """(e) a surface cutting strata below at a large angle."""
        ref, beds = truncation_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        cr = receipt["calculated_result"]

        assert receipt["status"] == "PASS", receipt["reason"]
        entry = cr["terminations"][0]
        assert entry["classification"] == "truncation"
        assert entry["side"] == "below"
        assert entry["angle_to_reference_deg"] >= 15.0
        assert entry["termination_xy"] == pytest.approx([400.0, 120.0], abs=1e-6)
        assert entry["relative_chronology"]["relation"] == "HORIZON_OLDER_THAN_REFERENCE"
        assert cr["chronology_partial_order"][0]["older"] == "C"
        assert receipt["thresholds"]["toplap_max_angle_deg"] == 15.0
        assert entry["erosion_confirmed"] is False  # erosion is not proven from geometry

    def test_low_angle_top_termination_is_toplap_not_truncation(self):
        ref = shallow_ref()
        xs = np.linspace(0.0, 400.0, 21)
        zs = 155.0 - 0.0875 * xs  # ~5 deg strata below a ~2.9 deg surface => ~8 deg discordance
        zs[-1] = 100.0 + 0.05 * 400.0
        bed = {"surface_id": "T", "kind": "strata", "points": [(float(a), float(b)) for a, b in zip(xs, zs)]}
        receipt = classify_stratal_terminations(ref, [bed])
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "toplap"
        assert 3.0 < float(entry["angle_to_reference_deg"]) < 15.0

    def test_concordant_beds_are_offlap_concordant(self):
        t = math.tan(math.radians(10.0))
        ref = {"surface_id": "REF", "points": [(float(x), float(t * x)) for x in np.linspace(0.0, 1000.0, 21)]}
        bed = {
            "surface_id": "K",
            "kind": "strata",
            "points": [(float(x), float(t * x + 1.0)) for x in np.linspace(0.0, 1000.0, 21)],
        }
        receipt = classify_stratal_terminations(ref, [bed])
        entries = receipt["calculated_result"]["terminations"]
        assert len(entries) == 1
        assert entries[0]["classification"] == "offlap_concordant"
        assert entries[0]["ends"] == "whole"

    def test_downlap_with_a_map_dip_direction(self):
        ref = ref_slope_deg(1.0, x_max=2000.0, n=41)
        xs = np.linspace(0.0, 1850.0, 38)
        z0 = math.tan(math.radians(1.0)) * 1850.0 - math.tan(math.radians(10.0)) * 1850.0
        zs = z0 + math.tan(math.radians(10.0)) * xs
        zs[-1] = math.tan(math.radians(1.0)) * 1850.0
        bed = {
            "surface_id": "FRS",
            "kind": "foreset",
            "points": [(float(a), float(b)) for a, b in zip(xs, zs)],
            "dip_deg": 10.0,
            "dip_azimuth_deg": 90.0,
        }
        receipt = classify_stratal_terminations(ref, [bed], section_azimuth_deg=90.0)
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "downlap"
        assert entry["side"] == "above"
        assert entry["dip_consistency"]["consistent"] is True
        assert entry["map_dip_apparent_deg"] == pytest.approx(10.0, abs=0.5)

    def test_inconsistent_map_and_section_dip_withholds_the_classification(self):
        ref, beds = onlap_inputs()
        beds[0]["dip_deg"] = 60.0           # a section-invisible dip that contradicts the geometry
        beds[0]["dip_azimuth_deg"] = 90.0
        receipt = classify_stratal_terminations(ref, [beds[0]], section_azimuth_deg=90.0)
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "dip_inconsistent"
        assert entry["classification_candidate_geometry"] == "onlap"
        assert entry["dip_consistency"]["consistent"] is False
        # the geometry was covered, the class was withheld: partial, not UNMEASURED
        assert receipt["status"] == "PARTIALLY_MEASURED", receipt["reason"]
        assert receipt["calculated_result"]["classification_counts"] == {"dip_inconsistent": 1}
        assert receipt["calculated_result"]["n_withheld"] == 1


class TestAxisDFaultAbutPitfall:

    def test_zero_offset_abut_is_synchronous_never_younger(self):
        """(f) the mandated pitfall: abutment with zero offset == SYNCHRONOUS."""
        receipt = classify_stratal_terminations(shallow_ref(), [abutting_horizon()], faults=[fault_trace(0.0)])
        cr = receipt["calculated_result"]

        entry = cr["terminations"][0]
        assert entry["classification"] == "abut_synchronous"
        assert entry["contact_feature"] == "F1"
        assert entry["relative_chronology"]["relation"] == "SYNCHRONOUS"
        assert entry["pitfall_flag"] == "ZERO_OFFSET_ABUT_SYNCHRONOUS"

        # the pitfall: it must never be reported as younger than the fault
        assert "YOUNGER_THAN_FAULT" not in json.dumps(cr)
        assert receipt["pitfall_flags"]["zero_offset_abut_detected"] is True
        assert receipt["pitfall_flags"]["zero_offset_abut_never_younger"] is True
        assert FAULT_ABUT_PITFALL in receipt["caveats"]
        assert receipt["status"] == "WARN"  # classified, but the pitfall is carried as a caveat
        assert receipt["status"] != "UNMEASURED"

    def test_offset_abut_puts_the_horizon_older_than_the_fault(self):
        receipt = classify_stratal_terminations(shallow_ref(), [abutting_horizon()], faults=[fault_trace(25.0)])
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "abut_offset"
        assert entry["relative_chronology"]["relation"] == "HORIZON_OLDER_THAN_FAULT"
        assert entry["offset_at_contact_m"] == 25.0
        assert receipt["pitfall_flags"]["zero_offset_abut_detected"] is False

    def test_zero_offset_crossing_does_not_fix_the_fault_age(self):
        horizon = {
            "surface_id": "H2",
            "kind": "strata",
            "points": [(0.0, 500.0), (510.0, 550.0)],
            "present_both_sides": True,
        }
        receipt = classify_stratal_terminations(shallow_ref(), [horizon], faults=[fault_trace(0.0)])
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "crosses_fault_zero_offset"
        assert entry["relative_chronology"]["relation"] == "UNDETERMINED"
        assert len(entry["relative_chronology"]["alternatives"]) == 3

    def test_abutment_without_an_offset_value_is_unmeasured(self):
        receipt = classify_stratal_terminations(shallow_ref(), [abutting_horizon()], faults=[fault_trace(None)])
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "abut_undetermined"
        assert entry["relative_chronology"]["relation"] == "UNDETERMINED"


class TestAxisDChronologyAndRules:

    def test_relative_chronology_only_never_absolute_age(self):
        ref, beds = onlap_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        cr = receipt["calculated_result"]

        assert cr["absolute_age_permitted"] is False
        assert cr["chronology_kind"] == "RELATIVE_PARTIAL_ORDER"
        assert cr["absolute_age_requires"] == list(ABSOLUTE_AGE_REQUIREMENT)
        assert any("biostratigraphy" in r for r in cr["absolute_age_requires"])
        assert any("geochronology" in r for r in cr["absolute_age_requires"])
        assert RELATIVE_CHRONOLOGY_CAVEAT in receipt["caveats"]
        assert RELATIVE_CHRONOLOGY_CAVEAT in json.dumps(receipt)
        assert "age_ma" not in json.dumps(cr).lower()

    def test_no_termination_is_unmeasured_deficit_not_kill(self):
        far_bed = {"surface_id": "X", "kind": "strata", "points": [(0.0, 900.0), (400.0, 950.0)]}
        receipt = classify_stratal_terminations(shallow_ref(), [far_bed])
        assert receipt["status"] == "UNMEASURED"
        assert receipt["status"] != "KILL"
        assert receipt["coverage"] == 1.0
        assert receipt["calculated_result"]["classification_counts"] == {}
        assert receipt["missing_inputs"]

    def test_no_reference_surface_is_unmeasured(self):
        receipt = classify_stratal_terminations(None, [{"surface_id": "A", "points": [(0.0, 0.0), (10.0, 10.0)]}])
        assert receipt["status"] == "UNMEASURED"
        assert "reference_surface.points" in receipt["missing_inputs"]

    def test_no_confidence_and_full_receipt_contract(self):
        ref, beds = onlap_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        assert receipt["confidence"] is None
        assert receipt["confidence_status"] == "NOT_ESTABLISHED_NO_VALIDATED_BENCHMARK"
        assert len(receipt["receipt_hash"]) == 64
        for required in ("equation", "thresholds", "calculated_result", "exceptions_considered",
                         "evidence_refs", "missing_inputs", "receipt_hash"):
            assert required in receipt, required
        json.dumps(receipt)

    def test_deterministic_reproducible_receipt_hash(self):
        ref, beds = onlap_inputs()
        a = classify_stratal_terminations(ref, beds)
        b = classify_stratal_terminations(ref, beds)
        assert a["receipt_hash"] == b["receipt_hash"]
        assert a == b

    def test_termination_coordinates_are_reported_for_every_entry(self):
        ref, beds = truncation_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        for entry in receipt["calculated_result"]["terminations"]:
            assert isinstance(entry["termination_xy"], list)
            assert len(entry["termination_xy"]) == 2
            assert all(isinstance(v, float) for v in entry["termination_xy"])

    def test_amplitude_ridge_adapter_reuses_the_classical_primitives(self):
        image = np.zeros((120, 200), dtype=float)
        for x in range(200):
            for k in (30, 70):
                zc = int(k + 0.12 * x)
                image[max(0, zc - 2):zc + 3, x] = 1.0
        surfaces = surfaces_from_amplitude_ridges(image, sigma=1.0, threshold=0.3)
        assert surfaces, "ridge extraction returned nothing for a synthetic event"
        for s in surfaces:
            assert s["kind"] == "amplitude_ridge"
            assert s["points"]
            assert s["points_provenance"].startswith("ridge_extraction")
        json.dumps(surfaces)

    def test_termination_class_vocabulary_is_closed(self):
        ref, beds = onlap_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        allowed = {
            "onlap", "downlap", "toplap", "truncation", "offlap_concordant",
            "abut_synchronous", "abut_offset", "abut_undetermined",
            "crosses_fault_zero_offset", "onlap_or_downlap_ambiguous",
            "lap_undetermined", "undetermined", "dip_inconsistent",
        }
        for entry in receipt["calculated_result"]["terminations"]:
            assert entry["classification"] in allowed, entry["classification"]

    def test_sub_parallel_bed_that_never_reaches_the_reference_is_unmeasured(self):
        """A bed offset from the reference by more than the contact resolution is not a termination."""
        ref = {"surface_id": "REF", "points": [(float(x), 0.1 * x) for x in np.linspace(0.0, 1000.0, 21)]}
        bed = {
            "surface_id": "PAR",
            "kind": "strata",
            "points": [(float(x), 0.1 * x + 5.0) for x in np.linspace(0.0, 1000.0, 21)],
        }
        receipt = classify_stratal_terminations(ref, [bed])
        assert receipt["status"] == "UNMEASURED"
        assert receipt["calculated_result"]["classification_counts"] == {}
        assert receipt["calculated_result"]["unevaluable"]

    def test_contact_tolerance_can_be_supplied(self):
        ref = {"surface_id": "REF", "points": [(float(x), 0.1 * x) for x in np.linspace(0.0, 1000.0, 21)]}
        bed = {
            "surface_id": "PAR",
            "kind": "strata",
            "points": [(float(x), 0.1 * x + 1.0) for x in np.linspace(0.0, 1000.0, 21)],
        }
        receipt = classify_stratal_terminations(ref, [bed], contact_tolerance=2.0)
        entry = receipt["calculated_result"]["terminations"][0]
        assert entry["classification"] == "offlap_concordant"
        assert receipt["thresholds"]["contact_tolerance_source"] == "supplied"

    def test_coverage_floor_dominates_the_deficit_branch(self):
        """Below 0.7 coverage an unclassified set is UNMEASURED, and it is named as a coverage deficit."""
        ref = {"surface_id": "REF", "points": [(float(x), 0.1 * x) for x in np.linspace(0.0, 1000.0, 21)]}
        # the first bed overlaps the reference but never reaches it (no termination),
        # the other three lie wholly outside the reference x-range (unevaluable)
        beds = [{
            "surface_id": "IN",
            "kind": "strata",
            "points": [(float(x), 0.1 * x + 7.0) for x in np.linspace(0.0, 1000.0, 21)],
        }]
        for i in range(3):
            beds.append({
                "surface_id": f"OUT{i}",
                "kind": "strata",
                "points": [(float(x), 0.1 * x + 7.0) for x in np.linspace(2000.0, 3000.0, 11)],
            })
        receipt = classify_stratal_terminations(ref, beds)
        assert receipt["coverage"] == 0.25
        assert receipt["status"] == "UNMEASURED"
        assert receipt["status"] != "KILL"
        assert "0.7" in receipt["reason"]
        assert receipt["calculated_result"]["unevaluable"]

    def test_class_vocabulary_matches_the_stratigraphy_engine(self):
        """One vocabulary, not two: the labels must line up with GeometryType."""
        GeometryType = pytest.importorskip(
            "geox_core.engines.stratigraphy.surface_first"
        ).GeometryType
        for mine, theirs in GEOMETRY_TYPE_ALIGNMENT.items():
            assert GeometryType(theirs).value == theirs
            assert mine in TERMINATION_CLASSES or mine == "offlap_concordant"

        ref, beds = truncation_inputs()
        receipt = classify_stratal_terminations(ref, beds)
        assert receipt["calculated_result"]["class_vocabulary_alignment"] == GEOMETRY_TYPE_ALIGNMENT
        assert receipt["calculated_result"]["terminations"][0]["classification"] == GeometryType.TRUNCATION.value
