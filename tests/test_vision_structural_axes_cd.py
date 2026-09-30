"""Tests for CONTRACT.md §4 Axis C (orientation) and Axis D (superposition).

Every test builds its own synthetic numpy input — no fixtures from the repository, no
network, no cv2, no torch. The two doctrinal traps this file exists to catch:

  * Axis C: azimuths are CIRCULAR. Linear averaging of 350 deg and 10 deg gives 180 deg;
    the circular mean is 0 deg. `test_circular_mean_bug_is_caught` fails loudly if anyone
    ever "simplifies" the reduction to `np.mean`.
  * Axis D: cross-cutting/superposition (Steno/Hutton/Lyell) is NOT Walther's Law, and a
    termination candidate is NOT a bare gradient edge. Both are asserted as behaviour and
    as documentation, because a caveat that only exists in a docstring never reaches the
    caller.

Run: /root/GEOX/.venv/bin/python -m pytest tests/test_vision_structural_axes_cd.py -q
"""

from __future__ import annotations

import ast
import inspect
import math

import numpy as np
import pytest

from geox_core.vision_structural import orientation as orient
from geox_core.vision_structural import terminations as term
from geox_core.vision_structural.types import Measurement

# ─────────────────────────────────────────────────────────────────────────────
# synthetic section builders (deterministic — no RNG anywhere)
# ─────────────────────────────────────────────────────────────────────────────

NZ, NX = 64, 96


def ridge(
    nz: int,
    nx: int,
    z0: float,
    x0: float,
    x1: float,
    *,
    amp: float = 1.0,
    sz: float = 1.0,
    taper_x: float | None = None,
) -> np.ndarray:
    """One reflection: a Gaussian band in z, windowed in x.

    taper_x is None -> hard window (an abrupt lateral end, i.e. a discordant cut).
    taper_x = L    -> logistic decay with scale L (a lateral thinning / pinch-out).
    """
    z = np.arange(nz)[:, None]
    x = np.arange(nx)[None, :]
    band = amp * np.exp(-((z - z0) ** 2) / (2 * sz**2))
    if taper_x is None:
        window = ((x >= x0) & (x < x1)).astype(float)
    else:
        window = (1.0 / (1.0 + np.exp((x - x1) / float(taper_x)))) * (
            (x >= x0).astype(float)
        )
    return band * window


def abrupt_termination_section(
    *, end_x: float = 46.0, start_x: float = 0.0, spacing: int = 8
) -> np.ndarray:
    """Beds at full amplitude right up to a vertical face at end_x."""
    return sum(
        ridge(NZ, NX, z0, start_x, end_x) for z0 in range(8, 56, spacing)
    )


def pinchout_section(*, taper_x: float = 8.0, end_x: float = 46.0) -> np.ndarray:
    """Beds that lose their reflection gradually — a tangential lateral pinch-out."""
    return sum(
        ridge(NZ, NX, z0, 0.0, end_x, taper_x=taper_x) for z0 in range(8, 56, 8)
    )


def flat_full_width_section() -> np.ndarray:
    """Perfectly flat reflectors spanning the whole trace range (no lateral end)."""
    return sum(ridge(NZ, NX, z0, 0, NX) for z0 in range(8, 56, 8))


def parallel_polylines(n: int = 8, azimuth_deg: float = 45.0, length_m: float = 100.0):
    """n parallel fault traces, all digitised in the same direction."""
    dx = math.sin(math.radians(azimuth_deg)) * length_m
    dy = math.cos(math.radians(azimuth_deg)) * length_m
    return [
        np.array([[i * 10.0, 0.0], [i * 10.0 + dx, dy]], dtype=float) for i in range(n)
    ]


def scatter_polylines(n: int = 8, length_m: float = 100.0):
    """n fault traces with evenly spread azimuths (0, 45, 90, ... ) — isotropic."""
    out = []
    for i in range(n):
        az = 360.0 * i / n
        dx = math.sin(math.radians(az)) * length_m
        dy = math.cos(math.radians(az)) * length_m
        out.append(np.array([[0.0, 0.0], [dx, dy]], dtype=float))
    return out


def azimuth_of(start, end) -> float:
    return math.degrees(math.atan2(end[0] - start[0], end[1] - start[1])) % 360.0


def angular_difference(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


# ═════════════════════════════════════════════════════════════════════════════
# AXIS C — ORIENTATION
# ═════════════════════════════════════════════════════════════════════════════


def test_circular_mean_bug_is_caught():
    """350 deg and 10 deg: linear mean 180 deg (170 deg WRONG), circular mean ~0 deg."""
    azimuths = np.array([350.0, 10.0])

    linear_mean = float(np.mean(azimuths))
    assert abs(linear_mean - 180.0) < 1e-9, "control: numpy's linear mean really is 180"

    stats = orient.azimuth_population_stats(azimuths)
    circ = stats["circular_mean_deg"].value

    assert circ is not None
    assert angular_difference(circ, 0.0) < 1e-6, f"circular mean should be ~0, got {circ}"
    assert angular_difference(linear_mean, circ) > 170.0, "the linear answer is 170 deg off"
    assert 0.0 <= circ < 360.0, "azimuth must be reported inside [0, 360)"


def test_circular_mean_wraps_without_using_numpy_mean():
    cases = {
        (170.0, 190.0): 180.0,
        (355.0, 5.0): 0.0,
        (350.0, 10.0): 0.0,
        (90.0, 90.0): 90.0,
        (1.0, 359.0): 0.0,
    }
    for azimuths, expected in cases.items():
        mean, r = orient.circular_mean_deg(np.array(azimuths))
        assert angular_difference(mean, expected) < 1e-6, (azimuths, mean, expected)
        assert r <= 1.0
    # Identical azimuths must give a full resultant vector.
    mean, r = orient.circular_mean_deg(np.array([90.0, 90.0]))
    assert r == pytest.approx(1.0, abs=1e-9)
    # Two azimuths 20 deg apart give r = cos(10 deg), NOT 1 — concentration is real.
    _, r_pair = orient.circular_mean_deg(np.array([350.0, 10.0]))
    assert r_pair == pytest.approx(math.cos(math.radians(10.0)), abs=1e-9)
    # The reduction must not be a refactor call to the arithmetic mean. Scan the PARSED
    # CODE (not the docstring, which warns about exactly this bug) and flag any linear
    # mean applied to something named as an azimuth.
    tree = ast.parse(inspect.getsource(orient))
    offenders = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("mean", "average")
        ):
            continue
        segment = ast.get_source_segment(inspect.getsource(orient), node) or ""
        if "azimuth" in segment.lower():
            offenders.append(segment)
    assert not offenders, f"no linear averaging of azimuths is permitted: {offenders}"


def test_parallel_polylines_give_r_vector_length_near_one():
    out = orient.extract_fault_azimuths(parallel_polylines(8, 45.0))

    assert out["n_polylines"].value == 8.0
    assert angular_difference(out["azimuth_deg"].value, 45.0) < 1e-6
    assert out["r_vector_length"].value > 0.999
    assert len(out["azimuth_rosenbusch"]) == 8
    assert all(angular_difference(a, 45.0) < 1e-6 for a in out["azimuth_rosenbusch"])
    # Perfectly parallel traces have zero dispersion — and it must be +0.0, not -0.0.
    std = out["circular_std_deg"].value
    assert std == pytest.approx(0.0, abs=1e-9)
    assert math.copysign(1.0, std) == 1.0


def test_scattered_azimuths_give_r_vector_length_near_zero_and_say_so():
    out = orient.extract_fault_azimuths(scatter_polylines(8))
    r_meas = out["r_vector_length"]

    assert r_meas.value < 0.01, f"isotropic population should have R ~ 0, got {r_meas.value}"
    note_text = " ".join(r_meas.notes).upper()
    assert "NO PREFERRED ORIENTATION" in note_text
    assert out["population"]["preferred_orientation"].value == 0.0
    # The mean is still defined, but must not be read as a trend.
    assert out["azimuth_deg"].value is not None
    assert any("NO PREFERRED ORIENTATION" in n for n in out["azimuth_deg"].notes)


def test_extract_fault_azimuths_contract_keys_and_chord_convention():
    polylines = [
        np.array([[0.0, 0.0], [10.0, 0.0]]),        # due east  -> 90 deg
        np.array([[0.0, 0.0], [0.0, 10.0]]),        # due north -> 0 deg
        np.array([[0.0, 0.0], [10.0, 10.0]]),       # NE        -> 45 deg
    ]
    out = orient.extract_fault_azimuths(polylines)

    for key in ("azimuth_deg", "azimuth_rosenbusch", "n_polylines"):
        assert key in out, f"CONTRACT.md §4 Axis C requires key {key!r}"
    assert isinstance(out["azimuth_rosenbusch"], list)
    assert len(out["azimuth_rosenbusch"]) == 3
    assert angular_difference(out["azimuth_rosenbusch"][0], 90.0) < 1e-9
    assert angular_difference(out["azimuth_rosenbusch"][1], 0.0) < 1e-9
    assert angular_difference(out["azimuth_rosenbusch"][2], 45.0) < 1e-9
    assert isinstance(out["azimuth_deg"], Measurement)
    assert out["azimuth_deg"].unit in ("deg_azimuth", "deg")


def test_chord_azimuth_is_end_to_end_not_mean_of_segments():
    """A curving trace has one chord azimuth: first vertex to last vertex."""
    polyline = np.array([[0.0, 0.0], [50.0, 2.0], [100.0, 4.0]])   # chord ~ due east
    out = orient.extract_fault_azimuths([polyline])
    assert angular_difference(out["azimuth_rosenbusch"][0], 90.0) < 3.0
    assert angular_difference(out["azimuth_deg"].value, azimuth_of([0, 0], [100, 4])) < 1e-9


def test_degenerate_polylines_are_skipped_not_guessed():
    polylines = [
        np.array([[0.0, 0.0], [10.0, 0.0]]),       # valid
        np.array([[5.0, 5.0]]),                    # single vertex -> no chord
        np.array([[0.0, 0.0], [0.0, 0.0]]),        # zero-length chord
        np.array([[0.0, 0.0], [np.nan, 1.0]]),     # non-finite
    ]
    out = orient.extract_fault_azimuths(polylines)

    assert out["n_polylines"].value == 1.0
    assert out["n_polylines"].coverage == pytest.approx(0.25)
    assert len(out["azimuth_rosenbusch"]) == 1
    assert out["azimuth_deg"].status == "PARTIAL"
    assert any("skipped" in n for n in out["azimuth_deg"].notes)


def test_empty_polyline_input_is_unmeasured_not_zero():
    out = orient.extract_fault_azimuths([])

    assert out["n_polylines"].status == "UNMEASURED"
    assert out["n_polylines"].value is None
    assert out["azimuth_deg"].status == "UNMEASURED"
    assert out["azimuth_deg"].value is None
    assert out["azimuth_rosenbusch"] == []


def test_axial_mode_folds_digitising_direction():
    """Fault traces are lines: a reversed trace is the same fault."""
    forward = np.array([[0.0, 0.0], [10.0, 10.0]])
    reverse = np.array([[10.0, 10.0], [0.0, 0.0]])
    directed = orient.extract_fault_azimuths([forward, reverse])
    axial = orient.extract_fault_azimuths([forward, reverse], axial=True)

    assert directed["r_vector_length"].value < 0.01, "directed azimuths cancel at 180 deg"
    assert axial["r_vector_length"].value > 0.999, "axial folding removes the 180 deg split"
    assert angular_difference(axial["azimuth_deg"].value, 45.0) < 1e-6


def test_measurement_envelope_invariants_hold_on_every_returned_measurement():
    out = orient.extract_fault_azimuths(parallel_polylines(4))
    stats = orient.azimuth_population_stats(np.array([350.0, 10.0, 20.0]))

    for mapping in (out, stats):
        for key, value in mapping.items():
            if not isinstance(value, Measurement):
                continue
            if value.status == "MEASURED":
                assert value.value is not None
                assert value.coverage is not None, f"{key}: confidence without coverage"
            if value.status == "UNMEASURED":
                assert value.value is None
            if value.coverage is not None:
                assert 0.0 <= value.coverage <= 1.0


def test_population_stats_required_keys():
    stats = orient.azimuth_population_stats(np.array([10.0, 20.0, 30.0, 40.0]))
    for key in ("circular_mean_deg", "circular_std_deg", "r_vector_length", "n"):
        assert key in stats, f"CONTRACT.md §4 requires key {key!r}"
        assert isinstance(stats[key], Measurement)
    assert stats["n"].value == 4.0


def test_single_azimuth_is_partial_and_declares_why():
    stats = orient.azimuth_population_stats(np.array([123.0]))
    assert stats["circular_mean_deg"].status == "PARTIAL"
    assert stats["circular_mean_deg"].value == pytest.approx(123.0)
    assert stats["circular_mean_deg"].notes, "PARTIAL must declare what is missing"
    assert stats["r_vector_length"].status == "PARTIAL"
    assert stats["preferred_orientation"].status == "UNMEASURED"


def test_empty_population_is_unmeasured():
    stats = orient.azimuth_population_stats(np.array([]))
    assert stats["circular_mean_deg"].status == "UNMEASURED"
    assert stats["circular_mean_deg"].value is None
    assert stats["n"].value == 0.0


def test_uniform_population_reports_dispersion_as_declared_ceiling():
    stats = orient.azimuth_population_stats(np.arange(0.0, 360.0, 10.0))
    assert stats["r_vector_length"].value < 0.01
    std = stats["circular_std_deg"]
    assert std.value == pytest.approx(180.0)
    assert std.status == "PARTIAL"
    assert any("ceiling" in n for n in std.notes)
    assert any("NO PREFERRED ORIENTATION" in n for n in std.notes)


def test_conjugate_pair_detected_reports_bisector_and_dihedral():
    azimuths = np.array(
        [28.0, 30.0, 32.0, 29.0, 31.0, 30.0] + [88.0, 90.0, 92.0, 89.0, 91.0, 90.0]
    )
    result = orient.conjugate_pair_test(azimuths)

    assert result["pair_detected"] is True
    assert result["dihedral_acute_deg"] == pytest.approx(60.0, abs=0.5)
    assert result["bisector_acute_deg"] == pytest.approx(60.0, abs=0.5)
    assert "dihedral" in result["evidence"]


def test_conjugate_pair_returns_only_observation_and_no_stress_axis():
    azimuths = np.array(
        [28.0, 30.0, 32.0, 29.0, 31.0, 30.0] + [88.0, 90.0, 92.0, 89.0, 91.0, 90.0]
    )
    result = orient.conjugate_pair_test(azimuths)

    assert set(result) == {
        "pair_detected",
        "bisector_acute_deg",
        "dihedral_acute_deg",
        "evidence",
    }, "the observation contract is exactly four keys"

    forbidden = (
        "sigma",
        "shmax",
        "shmin",
        "stress",
        "s1",
        "principal",
        "paleostress",
        "paleo_stress",
        "tensor",
        "axis",
    )

    def walk(node, path="root"):
        if isinstance(node, dict):
            for key, value in node.items():
                lowered = str(key).lower()
                assert not any(tok in lowered for tok in forbidden), (
                    f"stress-axis key {key!r} at {path} — geometry may not emit a stress "
                    "state; that needs fault-slip inversion (arifOS)"
                )
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(result)
    assert "no stress axis" in result["evidence"].lower()


def test_conjugate_pair_unimodal_population_is_not_a_pair():
    azimuths = np.array([43.0, 45.0, 47.0, 44.0, 46.0, 45.0, 43.0, 45.0, 44.0, 46.0])
    result = orient.conjugate_pair_test(azimuths)

    assert result["pair_detected"] is False
    assert result["bisector_acute_deg"] is None
    assert result["dihedral_acute_deg"] is None
    assert result["evidence"]


def test_conjugate_pair_insufficient_sample_is_not_tested_not_failed():
    result = orient.conjugate_pair_test(np.array([10.0, 30.0, 50.0]))
    assert result["pair_detected"] is False
    assert "not tested" in result["evidence"].lower()


# ═════════════════════════════════════════════════════════════════════════════
# AXIS D — SUPERPOSITION
# ═════════════════════════════════════════════════════════════════════════════


def test_flat_and_constant_sections_yield_zero_candidates():
    for section in (np.zeros((NZ, NX)), np.full((NZ, NX), 3.0), np.full((NZ, NX), -2.5)):
        out = term.detect_terminations(section)
        assert out["n_candidates"] == 0, "a perfectly flat section has no terminations"
        assert out["onlap_contacts"] == []
        assert out["truncation_contacts"] == []
        assert isinstance(out["method"], str) and out["method"]


def test_full_width_reflectors_have_no_termination_only_data_edges():
    out = term.detect_terminations(flat_full_width_section())
    assert out["n_candidates"] == 0, (
        "reflectors running off the section are edge-of-data, not terminations"
    )
    assert out["n_no_lateral_end_rejected"] > 0


def test_bare_gradient_edge_is_not_a_termination():
    """A ramp has a large gradient everywhere and no reflector body at all."""
    ramp = np.tile(np.linspace(0.0, 5.0, NX)[None, :], (NZ, 1))
    out = term.detect_terminations(ramp)
    assert out["n_candidates"] == 0, "a bare gradient edge must not be reported as a contact"


def test_detect_terminations_finds_a_clear_lateral_termination():
    out = term.detect_terminations(abrupt_termination_section(end_x=46.0))
    assert out["n_candidates"] >= 2, "six beds ending at one trace must all be found"
    assert out["n_candidates"] == len(out["onlap_contacts"]) + len(out["truncation_contacts"])
    for x, y in out["onlap_contacts"] + out["truncation_contacts"]:
        assert 35.0 <= x <= 52.0, f"candidate x={x} is not at the terminating trace"
        assert 0 <= y < NZ


def test_detect_terminations_returns_exact_contract_keys():
    out = term.detect_terminations(abrupt_termination_section())
    for key in ("onlap_contacts", "truncation_contacts", "n_candidates", "method"):
        assert key in out, f"CONTRACT.md §4 Axis D requires key {key!r}"
    assert isinstance(out["n_candidates"], int)
    assert isinstance(out["onlap_contacts"], list)
    assert isinstance(out["truncation_contacts"], list)


def test_abrupt_cut_classifies_as_truncation_and_pinchout_as_onlap():
    abrupt = term.detect_terminations(abrupt_termination_section(end_x=46.0))
    pinch = term.detect_terminations(pinchout_section(taper_x=8.0, end_x=46.0))

    assert abrupt["n_candidates"] >= 2 and pinch["n_candidates"] >= 2
    abrupt_angles = [c["contact_angle_deg"] for c in abrupt["candidates"]]
    pinch_angles = [c["contact_angle_deg"] for c in pinch["candidates"]]

    assert min(abrupt_angles) > 25.0, f"an abrupt face is discordant: {abrupt_angles}"
    assert max(pinch_angles) < 25.0, f"a tangential pinch-out is not discordant: {pinch_angles}"
    assert all(c["class"] == "truncation" for c in abrupt["candidates"])
    assert all(c["class"] == "onlap" for c in pinch["candidates"])

    # Monotone in the physical pinch-out scale: a longer thinning run -> longer taper.
    abrupt_taper = float(np.median([c["taper_length_px"] for c in abrupt["candidates"]]))
    pinch_taper = float(np.median([c["taper_length_px"] for c in pinch["candidates"]]))
    assert pinch_taper > abrupt_taper


def test_candidates_carry_a_reproducible_audit_trail():
    out = term.detect_terminations(abrupt_termination_section())
    for cand in out["candidates"]:
        for key in (
            "x",
            "y",
            "class",
            "contact_angle_deg",
            "taper_length_px",
            "local_thickness_px",
            "tangent_azimuth_deg",
            "component_id",
            "class_reason",
        ):
            assert key in cand, f"candidate record missing {key!r}"
        assert cand["class"] in ("onlap", "truncation")
        assert 0.0 <= cand["contact_angle_deg"] <= 90.0
        assert cand["taper_length_px"] > 0.0
        assert cand["local_thickness_px"] >= 1.0
    assert out["parameters"]["amplitude_gate"] is not None


def test_caveat_and_docstring_require_the_horizon_mask():
    out = term.detect_terminations(abrupt_termination_section())
    caveat = out["caveat"].lower()
    assert "horizon_mask" in caveat
    assert "onlap" in caveat and "truncation" in caveat

    doc = " ".join((term.detect_terminations.__doc__ or "").split()).lower()
    assert "horizon_mask" in doc
    module_doc = " ".join((term.__doc__ or "").split()).lower()
    assert "a bare gradient edge is not a termination" in module_doc
    assert "must be combined with a `horizon_mask`" in module_doc


def test_method_parameter_selects_the_gradient_filter():
    prewitt = term.detect_terminations(abrupt_termination_section(), method="prewitt")
    assert "prewitt" in prewitt["method"]
    assert "prewitt_h" in prewitt["parameters"]["gradient_components"]

    roberts = term.detect_terminations(abrupt_termination_section(), method="roberts")
    assert "roberts" in roberts["method"]
    assert "fell back to" in roberts["parameters"]["gradient_components"]

    with pytest.raises(ValueError):
        term.detect_terminations(abrupt_termination_section(), method="cv2_fake")


def test_detect_terminations_input_validation_and_smoothing_toggle():
    with pytest.raises(ValueError):
        term.detect_terminations(np.zeros((4, 4, 4)))
    with pytest.raises(ValueError):
        term.detect_terminations(np.zeros((0, 0)))

    section = abrupt_termination_section()
    smooth = term.detect_terminations(section, do_smoothing=True)
    raw = term.detect_terminations(section, do_smoothing=False)
    for key in ("onlap_contacts", "truncation_contacts", "n_candidates", "method"):
        assert key in smooth and key in raw
    assert "gaussian" in smooth["method"]
    assert "gaussian" not in raw["method"]
    assert smooth["n_candidates"] > 0 and raw["n_candidates"] > 0


def test_min_component_and_elongation_gates_reject_non_reflectors():
    section = abrupt_termination_section()
    assert term.detect_terminations(section)["n_candidates"] > 0

    # Nothing survives a request for implausibly large bodies.
    huge = term.detect_terminations(section, min_component_px=10**6)
    assert huge["n_candidates"] == 0

    # A single bright sample is an isotropic amplitude anomaly, not a reflection band:
    # it has no lateral end and must not produce two "contacts".
    dot = np.zeros((NZ, NX))
    dot[30, 40] = 1.0
    out = term.detect_terminations(dot)
    assert out["n_candidates"] == 0
    assert out["n_non_reflector_bodies_rejected"] > 0


# ── cross-cutting table ──────────────────────────────────────────────────────

HORIZONS_FIVE = [
    {"id": "H1", "rank": 1},           # youngest
    {"id": "H2", "rank": 2},
    {"id": "H3", "rank": 3},
    {"id": "H4", "rank": 4},
    {"id": "H5", "rank": 5},           # oldest
]


def test_cross_cutting_gives_correct_younger_and_older_bounds():
    horizons = [
        {"id": "H1", "rank": 1},
        {"id": "H2", "rank": 2, "draped_by": ["F1"]},
        {"id": "H3", "rank": 3, "offset_by": ["F1"]},
        {"id": "H4", "rank": 4, "offset_by": ["F1"]},
        {"id": "H5", "rank": 5},
    ]
    table = term.build_cross_cutting_table(
        term.detect_terminations(abrupt_termination_section()), horizons
    )

    assert table["n"] == 1 == len(table["relations"])
    rel = table["relations"][0]
    assert rel["feature"] == "F1"
    # younger than the YOUNGEST horizon it offsets (H3, not H4)
    assert rel["younger_than"]["horizon_id"] == "H3"
    # older than the OLDEST horizon that drapes it (H2)
    assert rel["older_than"]["horizon_id"] == "H2"
    assert rel["consistent"] is True
    assert rel["scope"] == "LOCAL"
    assert "H3" in rel["statement"] and "H2" in rel["statement"]
    assert rel["n_offset_horizons"] == 2 and rel["n_drape_horizons"] == 1


def test_cross_cutting_flags_a_contradiction_instead_of_repairing_it():
    horizons = [
        {"id": "H1", "rank": 1, "offset_by": ["F1"]},   # claimed younger than H1
        {"id": "H4", "rank": 4, "draped_by": ["F1"]},   # and older than H4
    ]
    table = term.build_cross_cutting_table({}, horizons)
    rel = table["relations"][0]

    assert rel["consistent"] is False
    assert "CONTRADICTION" in rel["statement"]
    assert rel["younger_than"]["horizon_id"] == "H1"
    assert rel["older_than"]["horizon_id"] == "H4"


def test_cross_cutting_lists_undetermined_horizons_between_the_bounds():
    horizons = [
        {"id": "H1", "rank": 1, "draped_by": ["F1"]},
        {"id": "H2", "rank": 2},
        {"id": "H3", "rank": 3},
        {"id": "H4", "rank": 4, "offset_by": ["F1"]},
    ]
    table = term.build_cross_cutting_table({}, horizons)
    rel = table["relations"][0]

    assert rel["younger_than"]["horizon_id"] == "H4"
    assert rel["older_than"]["horizon_id"] == "H1"
    assert rel["consistent"] is True
    assert rel["undetermined_horizon_ids"] == ["H2", "H3"]
    assert rel["n_undetermined"] == 2


def test_cross_cutting_accepts_age_ma_ordering_and_refuses_a_mixed_order():
    by_age = [
        {"id": "A_young", "age_ma": 5.0, "draped_by": ["F1"]},
        {"id": "A_mid", "age_ma": 20.0, "offset_by": ["F1"]},
        {"id": "A_old", "age_ma": 40.0},
    ]
    table = term.build_cross_cutting_table({}, by_age)
    rel = table["relations"][0]
    assert rel["younger_than"]["horizon_id"] == "A_mid"
    assert rel["older_than"]["horizon_id"] == "A_young"
    assert rel["consistent"] is True

    mixed = [{"id": "X", "rank": 1}, {"id": "Y", "age_ma": 30.0}]
    with pytest.raises(ValueError):
        term.build_cross_cutting_table({}, mixed)

    with pytest.raises(ValueError):
        term.build_cross_cutting_table({}, [{"rank": 1, "offset_by": ["F"]}])


def test_cross_cutting_threads_termination_evidence_through():
    terminations = term.detect_terminations(abrupt_termination_section(end_x=46.0))
    assert terminations["n_candidates"] > 0
    horizons = [
        {"id": "H2", "rank": 2, "draped_by": ["F1"]},
        {"id": "H3", "rank": 3, "offset_by": ["F1"]},
    ]
    table = term.build_cross_cutting_table(terminations, horizons)
    evidence = table["relations"][0]["evidence"]

    assert evidence["n_candidates"] == terminations["n_candidates"]
    assert evidence["n_onlap_contacts"] == len(terminations["onlap_contacts"])
    assert evidence["n_truncation_contacts"] == len(terminations["truncation_contacts"])
    assert evidence["detect_terminations_method"] == terminations["method"]
    assert table["n_candidates_available"] == terminations["n_candidates"]

    # With no terminations supplied the relation is visibly annotation-only.
    bare = term.build_cross_cutting_table({}, horizons)
    assert "not geometry-supported" in bare["relations"][0]["evidence"]["note"]


def test_cross_cutting_is_steno_not_walther():
    table = term.build_cross_cutting_table({}, HORIZONS_FIVE)
    assert "Steno 1669" in table["principle"]
    assert "Hutton 1795" in table["principle"]
    assert "NOT Walther's Law" in table["principle"]

    doc = " ".join((term.build_cross_cutting_table.__doc__ or "").split())
    assert "NOT Walther's Law" in doc
    assert "conformable facies succession" in doc
    assert "Steno 1669" in doc and "Lyell 1830" in doc


def test_cross_cutting_drape_caveat_is_local_scope():
    horizons = [
        {"id": "H1", "rank": 1, "draped_by": ["F1"]},
        {"id": "H3", "rank": 3, "offset_by": ["F1"]},
    ]
    table = term.build_cross_cutting_table({}, horizons)
    rel = table["relations"][0]
    assert rel["scope"] == "LOCAL"
    assert "LOCALLY" in rel["caveat"]
    assert any("relay" in c for c in table["caveats"])
    assert any("horizon_mask" in c for c in table["caveats"])


def test_cross_cutting_reports_unconstrained_features_and_empty_input():
    empty = term.build_cross_cutting_table({}, HORIZONS_FIVE)
    assert empty["n"] == 0
    assert empty["relations"] == []
    assert set(empty["unconstrained_features"]) == {"H1", "H2", "H3", "H4", "H5"}

    horizons = [{"id": "H3", "rank": 3, "offset_by": ["F1", "F2"]}]
    table = term.build_cross_cutting_table({}, horizons)
    assert table["n"] == 2
    assert table["n_features"] == 2
    for rel in table["relations"]:
        assert rel["younger_than"]["horizon_id"] == "H3"
        assert rel["older_than"] is None
        assert rel["consistent"] is None
        assert rel["scope"] == "REGIONAL"
        assert "no drape observation" in rel["statement"]


def test_cross_cutting_counts_candidates_inside_a_horizon_mask():
    terminations = term.detect_terminations(abrupt_termination_section(end_x=46.0))
    mask = np.zeros((NZ, NX), dtype=bool)
    for cand in terminations["candidates"]:
        mask[int(cand["y"]), int(cand["x"])] = True
    horizons = [{"id": "H3", "rank": 3, "offset_by": ["F1"], "mask": mask}]
    table = term.build_cross_cutting_table(terminations, horizons)
    inside = table["relations"][0]["evidence"]["n_candidates_inside_horizon_mask"]

    assert inside["H3"] == terminations["n_candidates"]


def test_axis_d_methods_never_import_cv2_or_torch():
    source = inspect.getsource(term)
    for banned in ("import cv2", "import torch", "from cv2", "from torch"):
        assert banned not in source, f"{banned!r} is forbidden — those packages are absent"
