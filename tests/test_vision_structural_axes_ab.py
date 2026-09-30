"""Axis A (shape) + Axis B (differential) + calibration — real pytest coverage.

Every fixture here is a synthetic numpy array built in-file, so an assertion can be checked
against arithmetic rather than against a previous run of the same code. The synthetic
sections are *exact* planes and curves, which is the point: the structure-tensor estimate is
machine-precise on a plane, so a dip test can ask for 1e-2 deg and mean it.

Doctrine assertions live alongside the numeric ones, because the doctrine is the part that
gets lost through a wire: UNMEASURED is never 0.0/1.0, DTW never becomes a thickness, a
geometry class is only ever emitted by a named rule, and a masked isopach gap is never
interpolated.
"""

from __future__ import annotations

import numpy as np
import pytest

from geox_core.vision_structural import (
    DTW_WARP_ONLY_WARNING,
    GEOMETRY_RULES,
    MIGRATION_STATES,
    RULE_KINKED,
    RULE_LISTRIC,
    RULE_PLANAR,
    Measurement,
    apply_ve_correction,
    compute_dip_field,
    compute_isopach,
    declare_calibration_state,
    dtw_align_traces,
    expansion_index,
    extract_axis_a,
    isopach_differential,
    measured,
    time_to_depth,
    trace_thickness_profile,
    unmeasured,
)
from geox_core.vision_structural import types as vs_types
from geox_core.vision_structural.structure_tensor import MIN_COVERAGE_FOR_MEASURED

DZ_M = 10.0
DX_M = 25.0
DIP_TRUE_DEG = 15.0
PLANE_ROWS_PER_COL = np.tan(np.radians(DIP_TRUE_DEG)) * DX_M / DZ_M
PLANE_NZ, PLANE_NX, PLANE_ROW0 = 150, 60, 70


# ── synthetic builders ─────────────────────────────────────────────────────────────────
def plane_section(
    dip_deg: float = DIP_TRUE_DEG,
    *,
    ve: float = 1.0,
    nz: int = PLANE_NZ,
    nx: int = PLANE_NX,
    row0: int = PLANE_ROW0,
) -> np.ndarray:
    """A section whose level sets are perfectly planar beds dipping at ``dip_deg``.

    ``ve`` is the display stretch applied when the section was drawn: a true dip of
    ``dip_deg`` displayed at ``ve`` has an apparent dip of ``atan(ve * tan(dip_deg))``.
    """
    rows_per_col = np.tan(np.radians(dip_deg)) * ve * DX_M / DZ_M
    r = np.arange(nz)[:, None]
    c = np.arange(nx)[None, :]
    return (r - row0) - rows_per_col * c


def level_mask(section: np.ndarray, tol: float = 0.5) -> np.ndarray:
    """Pick the horizon: the samples of the section inside a tolerance band of a level set."""
    return np.abs(section) <= tol


def curve_section(z_rows: np.ndarray, *, nz: int = PLANE_NZ) -> np.ndarray:
    """A section whose level sets follow the curve ``z_rows(column)`` (in row units)."""
    r = np.arange(nz)[:, None]
    return r - np.asarray(z_rows, dtype=float)[None, :]


def listric_z_rows(nx: int = PLANE_NX, *, row0: int = 70) -> np.ndarray:
    """Dip increasing systematically with depth: 10 deg at the left, 25 deg at the right."""
    x = np.arange(nx) * DX_M
    return (np.tan(np.radians(10.0)) * x + 9.83e-5 * x**2) / DZ_M + row0


def kinked_z_rows(nx: int = PLANE_NX, *, x0: float = 725.0, row0: int = 70) -> np.ndarray:
    """Two discrete dip domains (10 deg then 25 deg) meeting at ``x0``."""
    x = np.arange(nx) * DX_M
    z = np.where(
        x < x0,
        np.tan(np.radians(10.0)) * x,
        np.tan(np.radians(10.0)) * x0 + np.tan(np.radians(25.0)) * (x - x0),
    )
    return z / DZ_M + row0


def horizon_mask_from_rows(sec: np.ndarray) -> np.ndarray:
    return np.abs(sec) <= 0.5


def assert_measurement_invariants(out: dict[str, Measurement]) -> None:
    for key, m in out.items():
        assert isinstance(m, Measurement), f"{key} is not a Measurement"
        if m.status == "MEASURED":
            assert m.value is not None and m.coverage is not None
        if m.status == "UNMEASURED":
            assert m.value is None
        if m.status == "PARTIAL":
            assert m.notes


def assert_no_probability_keys(obj: object) -> None:
    """No self-assigned probability may ride inside a vision payload (CONTRACT §5)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert str(k).lower() not in vs_types.FORBIDDEN_PROBABILITY_KEYS, f"forbidden key {k!r}"
            assert_no_probability_keys(v)
    elif isinstance(obj, list | tuple):
        for v in obj:
            assert_no_probability_keys(v)


# ── (e) Measurement invariants ─────────────────────────────────────────────────────────
def test_measurement_measured_without_coverage_raises() -> None:
    with pytest.raises(ValueError, match="coverage"):
        Measurement(value=12.0, unit="deg", status="MEASURED")
    with pytest.raises(ValueError, match="value"):
        Measurement(value=None, unit="deg", status="MEASURED")


def test_measurement_unmeasured_must_not_carry_a_value() -> None:
    with pytest.raises(ValueError, match="UNMEASURED"):
        Measurement(value=1.0, unit="ratio", status="UNMEASURED")
    assert unmeasured("ratio", reason="no data").value is None
    assert unmeasured("ratio", reason="no data").status == "UNMEASURED"


def test_measurement_partial_requires_notes_and_coverage() -> None:
    with pytest.raises(ValueError, match="PARTIAL"):
        Measurement(value=1.0, unit="ratio", status="PARTIAL", coverage=0.5)
    ok = Measurement(value=1.0, unit="ratio", status="PARTIAL", coverage=0.5, notes=["half covered"])
    assert ok.status == "PARTIAL" and ok.is_usable and ok.to_framework() == 1.0


def test_unmeasured_is_never_served_as_zero_to_a_downstream_gate() -> None:
    m = unmeasured("ratio", reason="no valid pair")
    assert m.to_framework() is None
    assert m.is_usable is False


# ── calibration ────────────────────────────────────────────────────────────────────────
def test_apply_ve_correction_is_identity_at_ve_one() -> None:
    for dip in (-42.5, -3.0, 0.0, 7.25, 61.0):
        assert apply_ve_correction(dip, 1.0) == pytest.approx(dip, abs=1e-12)


def test_apply_ve_correction_inverts_the_tan_relation() -> None:
    for dip_true, ve in ((20.0, 2.0), (5.0, 3.0), (35.0, 1.5), (-12.0, 2.0)):
        apparent = np.degrees(np.arctan(ve * np.tan(np.radians(dip_true))))
        assert apply_ve_correction(apparent, ve) == pytest.approx(dip_true, abs=1e-9)


def test_apply_ve_correction_roundtrip() -> None:
    apparent = np.degrees(np.arctan(2.0 * np.tan(np.radians(30.0))))
    corrected = apply_ve_correction(apparent, 2.0)
    assert corrected == pytest.approx(30.0, abs=1e-9)
    assert abs(apparent) > abs(corrected)  # exaggeration inflates, correction deflates


@pytest.mark.parametrize("ve", [0.0, -1.0, -2.5, float("nan"), float("inf")])
def test_apply_ve_correction_rejects_invalid_display_ratio(ve: float) -> None:
    with pytest.raises(ValueError, match="display ratio"):
        apply_ve_correction(10.0, ve)


@pytest.mark.parametrize("dip", [90.0, -90.0, 100.0, float("nan")])
def test_apply_ve_correction_rejects_vertical_or_nonfinite_dip(dip: float) -> None:
    with pytest.raises(ValueError):
        apply_ve_correction(dip, 2.0)


def test_apply_ve_correction_docstring_states_ve_is_not_a_velocity() -> None:
    doc = apply_ve_correction.__doc__ or ""
    assert "NOT a velocity" in doc and "DIMENSIONLESS" in doc.upper()


def test_time_to_depth_halves_the_two_way_time() -> None:
    # 2.0 s two-way at 2000 m/s -> 2000 m of one-way path.
    assert time_to_depth(2000.0, 2000.0) == pytest.approx(2000.0)
    assert time_to_depth(1000.0, 3000.0) == pytest.approx(1500.0)
    arr = time_to_depth(np.array([0.0, 1000.0, 2000.0]), 2000.0)
    assert isinstance(arr, np.ndarray)
    np.testing.assert_allclose(arr, [0.0, 1000.0, 2000.0])
    assert isinstance(time_to_depth(500.0, 2000.0), float)


@pytest.mark.parametrize("vel", [0.0, -1500.0, float("nan"), float("inf")])
def test_time_to_depth_rejects_non_positive_or_nonfinite_velocity(vel: float) -> None:
    with pytest.raises(ValueError, match="interval_velocity"):
        time_to_depth(1500.0, vel)


def test_time_to_depth_rejects_negative_or_nonfinite_time() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        time_to_depth(-10.0, 2000.0)
    with pytest.raises(ValueError, match="non-finite"):
        time_to_depth(float("nan"), 2000.0)


def test_declare_calibration_state_clean_section_is_trustworthy() -> None:
    state = declare_calibration_state(
        vertical_exaggeration=1.0,
        velocity_model_present=True,
        time_domain=False,
        migration_state="unmigrated",
    )
    assert state["dips_trustworthy"] is True
    assert state["problems"] == []
    assert state["migration_state"] == "unmigrated"


def test_declare_calibration_state_flags_unity_ve_and_undeclared_ve() -> None:
    stretched = declare_calibration_state(
        vertical_exaggeration=2.0,
        velocity_model_present=True,
        time_domain=False,
        migration_state="unmigrated",
    )
    assert stretched["dips_trustworthy"] is False
    assert any("vertical_exaggeration=2.0" in p for p in stretched["problems"])

    unknown = declare_calibration_state(
        vertical_exaggeration=None,
        velocity_model_present=True,
        time_domain=False,
        migration_state="unmigrated",
    )
    assert unknown["dips_trustworthy"] is False
    assert any("unknown" in p and "NOT a velocity" in p for p in unknown["problems"])


def test_declare_calibration_state_accepts_a_declared_correction() -> None:
    state = declare_calibration_state(
        vertical_exaggeration=2.0,
        velocity_model_present=True,
        time_domain=False,
        migration_state="unmigrated",
        ve_corrected=True,
    )
    assert state["dips_trustworthy"] is True
    assert state["problems"] == []


def test_declare_calibration_state_time_domain_requires_a_velocity_model() -> None:
    no_vel = declare_calibration_state(
        vertical_exaggeration=1.0,
        velocity_model_present=False,
        time_domain=True,
        migration_state="unmigrated",
    )
    assert no_vel["dips_trustworthy"] is False
    assert any("interval-velocity model" in p for p in no_vel["problems"])

    with_vel = declare_calibration_state(
        vertical_exaggeration=1.0,
        velocity_model_present=True,
        time_domain=True,
        migration_state="unmigrated",
    )
    assert with_vel["dips_trustworthy"] is True


def test_declare_calibration_state_unknown_migration_is_not_trustworthy() -> None:
    default = declare_calibration_state(
        vertical_exaggeration=1.0, velocity_model_present=True, time_domain=False
    )
    assert default["migration_state"] == "unknown"
    assert default["dips_trustworthy"] is False
    assert any("migration_state unknown" in p for p in default["problems"])

    named = declare_calibration_state(
        vertical_exaggeration=1.0,
        velocity_model_present=True,
        time_domain=False,
        migration_state="unknown",
    )
    assert named["dips_trustworthy"] is False


def test_declare_calibration_state_migrated_records_the_problem() -> None:
    state = declare_calibration_state(
        vertical_exaggeration=1.0,
        velocity_model_present=True,
        time_domain=False,
        migration_state="migrated",
    )
    assert state["migration_state"] == "migrated"
    assert any("migrated" in p and "tan(theta_apparent)" in p for p in state["problems"])


def test_declare_calibration_state_rejects_an_invented_migration_state() -> None:
    with pytest.raises(ValueError, match="migration_state must be one of"):
        declare_calibration_state(
            vertical_exaggeration=1.0,
            velocity_model_present=True,
            time_domain=False,
            migration_state="probably-unmigrated",
        )
    assert "unknown" in MIGRATION_STATES


# ── (a) Axis A: a synthetic dipping plane recovers the dip we put in ────────────────────
def test_planar_horizon_recovers_its_dip() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    field = compute_dip_field(sec, dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    assert field["dip_deg"].value == pytest.approx(DIP_TRUE_DEG, abs=0.05)
    assert field["dip_deg"].status == "MEASURED"

    axis_a = extract_axis_a(sec, level_mask(sec), dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    assert axis_a["dip_deg_mean"].value == pytest.approx(DIP_TRUE_DEG, abs=0.05)
    assert axis_a["dip_deg_p95"].value == pytest.approx(DIP_TRUE_DEG, abs=0.01)
    assert axis_a["curvature_mean"].value == pytest.approx(0.0, abs=1e-6)
    assert axis_a["dip_azimuth_deg"].value == pytest.approx(0.0, abs=1e-9)
    assert axis_a["dip_deg_mean"].coverage == pytest.approx(0.8333, abs=1e-3)
    assert axis_a["dip_deg_mean"].n_samples == 50
    for key, m in axis_a.items():
        if key == "geometry_class_fired":
            assert m.method == RULE_PLANAR  # a rule name, not free text
            continue
        assert m.method.startswith("A/structure_tensor")
        assert "tan(theta_true)=tan(theta_app)/ve" in m.method or "VE correction" in m.method


def test_planar_section_curvature_is_zero_to_machine_precision() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    field = compute_dip_field(sec, dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    assert abs(field["curvature"].value) < 1e-12  # no curvature invented out of a zero-fill
    assert field["curvature"].status == "MEASURED"


def test_horizon_dipping_left_reports_the_opposite_azimuth() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    sec = np.ascontiguousarray(sec[:, ::-1])  # level sets now deepen toward -x
    axis_a = extract_axis_a(sec, level_mask(sec), dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    assert axis_a["dip_deg_mean"].value == pytest.approx(DIP_TRUE_DEG, abs=0.05)
    assert axis_a["dip_azimuth_deg"].value == pytest.approx(180.0, abs=1e-6)


def test_flat_horizon_dip_is_a_measured_zero_but_azimuth_is_unmeasured() -> None:
    r = np.arange(PLANE_NZ)[:, None]
    sec = (r - 70) * np.ones((1, PLANE_NX))
    axis_a = extract_axis_a(sec, level_mask(sec), dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    assert axis_a["dip_deg_mean"].value == pytest.approx(0.0, abs=1e-9)
    assert axis_a["dip_deg_mean"].status == "MEASURED"
    azimuth = axis_a["dip_azimuth_deg"]
    assert azimuth.status == "UNMEASURED"
    assert azimuth.value is None  # NOT 0.0: a flat horizon has no azimuth to report
    assert any("no dip direction" in n for n in azimuth.notes)


def test_coverage_is_reported_and_gaps_are_counted_not_interpolated() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    full = np.ones(sec.shape, dtype=bool)
    axis_a = extract_axis_a(sec, full, dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    n_mask = full.size
    n_valid = int(axis_a["dip_deg_mean"].n_samples)
    assert n_valid == 140 * 50  # interior only: guard = ceil(3*sigma) + 2
    assert axis_a["dip_deg_mean"].coverage == pytest.approx(n_valid / n_mask)
    assert n_mask - n_valid == 2000
    assert any(f"{n_mask - n_valid} of {n_mask}" in n for n in axis_a["dip_deg_mean"].notes)
    assert any("never interpolated" in n for n in axis_a["dip_deg_mean"].notes)


def test_extract_axis_a_rejects_mask_shape_mismatch_and_junk_input() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    with pytest.raises(ValueError, match="does not match"):
        extract_axis_a(sec, np.zeros((3, 3), dtype=bool), dz_m=DZ_M, dx_m=DX_M)
    with pytest.raises(ValueError, match="non-finite"):
        compute_dip_field(sec * np.nan, dz_m=DZ_M, dx_m=DX_M)
    with pytest.raises(ValueError, match="dz_m"):
        compute_dip_field(sec, dz_m=0.0, dx_m=DX_M)
    with pytest.raises(ValueError, match="ndim"):
        compute_dip_field(np.zeros((4, 4, 4)), dz_m=DZ_M, dx_m=DX_M)


def test_empty_horizon_mask_is_unmeasured_everywhere() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    axis_a = extract_axis_a(sec, np.zeros(sec.shape, dtype=bool), dz_m=DZ_M, dx_m=DX_M)
    assert set(axis_a) == {
        "dip_deg_mean",
        "dip_deg_p95",
        "curvature_mean",
        "dip_azimuth_deg",
        "geometry_class_fired",
    }
    for m in axis_a.values():
        assert m.status == "UNMEASURED" and m.value is None
    assert_measurement_invariants(axis_a)


# ── (b) a VE of 2.0 inflates apparent dip; the correction recovers the truth ────────────
def test_ve_of_two_inflates_apparent_dip_and_correction_recovers_the_true_value() -> None:
    dip_true = 20.0
    sec = plane_section(dip_true, ve=2.0, nz=220, nx=60, row0=130)
    mask = level_mask(sec)

    uncorrected = extract_axis_a(sec, mask, dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    corrected = extract_axis_a(sec, mask, dz_m=DZ_M, dx_m=DX_M, ve=2.0)
    expected_apparent = float(np.degrees(np.arctan(2.0 * np.tan(np.radians(dip_true)))))

    assert expected_apparent == pytest.approx(36.05, abs=0.01)
    assert uncorrected["dip_deg_mean"].value == pytest.approx(expected_apparent, abs=0.05)
    assert corrected["dip_deg_mean"].value == pytest.approx(dip_true, abs=0.05)
    assert uncorrected["dip_deg_mean"].value > corrected["dip_deg_mean"].value + 15.0
    assert corrected["dip_azimuth_deg"].value == pytest.approx(0.0, abs=1e-6)

    field_uncorrected = compute_dip_field(sec, dz_m=DZ_M, dx_m=DX_M, ve=1.0)
    field_corrected = compute_dip_field(sec, dz_m=DZ_M, dx_m=DX_M, ve=2.0)
    assert field_corrected["dip_deg"].value == pytest.approx(dip_true, abs=0.05)
    assert field_uncorrected["dip_deg"].value == pytest.approx(expected_apparent, abs=0.05)
    assert apply_ve_correction(field_uncorrected["dip_deg"].value, 2.0) == pytest.approx(
        dip_true, abs=0.05
    )


# ── geometry classification: declared rules only ───────────────────────────────────────
def test_geometry_rule_planar_fires_with_a_named_rule() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    fired = extract_axis_a(sec, level_mask(sec), dz_m=DZ_M, dx_m=DX_M)["geometry_class_fired"]
    assert fired.status == "MEASURED"
    assert fired.value == 1.0
    assert fired.method == RULE_PLANAR
    assert fired.method in GEOMETRY_RULES
    assert fired.uncertainty["class"] == "PLANAR"
    assert fired.uncertainty["declared_predicate"]
    assert any("geometry_class=PLANAR" in n for n in fired.notes)


def test_geometry_rule_listric_fires_on_a_dip_increasing_with_depth() -> None:
    sec = curve_section(listric_z_rows())
    axis_a = extract_axis_a(sec, horizon_mask_from_rows(sec), dz_m=DZ_M, dx_m=DX_M)
    fired = axis_a["geometry_class_fired"]
    assert fired.status == "MEASURED" and fired.value == 1.0
    assert fired.method == RULE_LISTRIC
    assert fired.uncertainty["class"] == "LISTRIC"
    assert fired.uncertainty["listric"]["spearman_rho"] >= 0.9
    assert axis_a["dip_deg_p95"].value - axis_a["dip_deg_mean"].value > 3.0
    # the class name is an interpretation carried by a rule, never a bare method string
    assert fired.method != "listric"
    assert "INTERPRETATION" in GEOMETRY_RULES[RULE_LISTRIC]["declared"]
    assert "not a raw CV output" in GEOMETRY_RULES[RULE_LISTRIC]["declared"]


def test_geometry_rule_kinked_fires_on_a_discrete_dip_domain_boundary() -> None:
    sec = curve_section(kinked_z_rows())
    fired = extract_axis_a(sec, horizon_mask_from_rows(sec), dz_m=DZ_M, dx_m=DX_M)[
        "geometry_class_fired"
    ]
    assert fired.status == "MEASURED" and fired.value == 1.0
    assert fired.method == RULE_KINKED
    assert fired.uncertainty["class"] == "KINKED"
    kink = fired.uncertainty["kink"]
    assert kink["x_boundary_m"] == pytest.approx(725.0, abs=1.0)
    assert kink["jump_deg"] == pytest.approx(15.0, abs=0.5)
    assert kink["lo_spread_deg"] < 4.0 and kink["hi_spread_deg"] < 4.0
    # a kink outranks the trend rule that would otherwise also fire
    assert any("KINKED" in n for n in fired.notes)


def test_geometry_class_is_unmeasured_when_the_decision_inputs_are_only_partial() -> None:
    r = np.arange(PLANE_NZ)[:, None]
    c = np.arange(PLANE_NX)[None, :]
    # left corner carries a real plane; everything past column 20 is a constant (no gradient)
    sec = np.where(c < 20, (r - 70) - PLANE_ROWS_PER_COL * c, 0.0)
    mask = np.zeros(sec.shape, dtype=bool)
    for col in range(5, 20):
        mask[int(round(70 + PLANE_ROWS_PER_COL * col)), col] = True
    mask[90, 30:60] = True

    axis_a = extract_axis_a(sec, mask, dz_m=DZ_M, dx_m=DX_M)
    assert axis_a["dip_deg_mean"].status == "PARTIAL"
    assert axis_a["dip_deg_mean"].coverage < MIN_COVERAGE_FOR_MEASURED
    fired = axis_a["geometry_class_fired"]
    assert fired.status == "UNMEASURED" and fired.value is None
    assert "geometry-rule-set[" in fired.method
    assert any("not MEASURED" in n for n in fired.notes)
    assert_measurement_invariants(axis_a)


def test_geometry_class_is_unmeasured_when_no_rule_fires() -> None:
    sec = curve_section(listric_z_rows())
    z_rows = listric_z_rows()
    mask = np.zeros(sec.shape, dtype=bool)
    for col in (5, 14, 23, 32, 41, 50):  # six samples: too few for the trend, too few for a kink
        mask[int(round(z_rows[col])), col] = True
    fired = extract_axis_a(sec, mask, dz_m=DZ_M, dx_m=DX_M)["geometry_class_fired"]
    assert fired.status == "UNMEASURED" and fired.value is None
    assert "no declared geometry rule fired" in " ".join(fired.notes)
    evaluations = fired.uncertainty["rule_evaluations"]
    assert evaluations and all("not fired" in e for e in evaluations)
    assert set(fired.uncertainty["rule_precedence"]) == set(GEOMETRY_RULES)


def test_axis_a_outputs_are_clean_of_probability_keys_and_invariant_safe() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    axis_a = extract_axis_a(sec, level_mask(sec), dz_m=DZ_M, dx_m=DX_M)
    assert_measurement_invariants(axis_a)
    assert_no_probability_keys({k: m.asdict() for k, m in axis_a.items()})
    field = compute_dip_field(sec, dz_m=DZ_M, dx_m=DX_M)
    assert_measurement_invariants(field)
    assert_no_probability_keys({k: m.asdict() for k, m in field.items()})


# ── Axis B: DTW ────────────────────────────────────────────────────────────────────────
def test_dtw_identity_path_is_the_diagonal() -> None:
    ramp = np.arange(100, dtype=float)  # strictly monotone: only i == j costs zero
    out = dtw_align_traces(ramp, ramp)
    assert out["distance"] == pytest.approx(0.0, abs=1e-12)
    np.testing.assert_array_equal(out["path"][:, 0], out["path"][:, 1])
    assert out["path"].shape == (100, 2)
    assert set(out) == {"path", "distance", "warp_stretch_profile", "band"}


def test_dtw_path_is_monotone_and_anchored() -> None:
    a = np.sin(np.linspace(0, 6 * np.pi, 80)) + np.linspace(0, 2, 80)
    b = np.sin(np.linspace(0, 5 * np.pi, 65)) + np.linspace(0, 1.5, 65)
    out = dtw_align_traces(a, b)
    path = out["path"]
    assert tuple(path[0]) == (0, 0)
    assert tuple(path[-1]) == (len(a) - 1, len(b) - 1)
    assert np.all(np.diff(path, axis=0) >= 0)
    assert out["warp_stretch_profile"].shape == (path.shape[0],)
    assert out["distance"] > 0.0
    assert out["band"] == max(len(a), len(b))


def test_dtw_recovers_a_known_stretch_factor() -> None:
    n = 100
    a = np.sin(2 * np.pi * 3 * np.linspace(0, 1, n)) + 2 * np.linspace(0, 1, n)
    # b advances through the same waveform twice as fast in a's index
    b = np.sin(2 * np.pi * 3 * (np.arange(n) / (2.0 * n))) + 2.0 * (np.arange(n) / (2.0 * n))
    out = dtw_align_traces(a, b)
    profile = out["warp_stretch_profile"]
    assert float(np.median(profile[: n // 3])) == pytest.approx(2.0, abs=0.15)
    assert float(np.median(profile[: n // 3])) != pytest.approx(1.0, abs=0.2)


def test_dtw_band_constrains_the_path_and_costs_more() -> None:
    n = 100
    a = np.sin(2 * np.pi * 3 * np.linspace(0, 1, n)) + 2 * np.linspace(0, 1, n)
    b = np.sin(2 * np.pi * 3 * (np.arange(n) / (2.0 * n))) + 2.0 * (np.arange(n) / (2.0 * n))
    full = dtw_align_traces(a, b)
    banded = dtw_align_traces(a, b, band=3)
    assert banded["band"] == 3
    assert np.max(np.abs(banded["path"][:, 0] - banded["path"][:, 1])) <= 3
    assert banded["distance"] >= full["distance"]


def test_dtw_band_wider_than_the_length_gap_is_raised_not_crashed() -> None:
    a = np.arange(20, dtype=float)
    b = np.arange(12, dtype=float)
    out = dtw_align_traces(a, b, band=1)
    assert out["band"] == abs(len(a) - len(b))
    assert tuple(out["path"][-1]) == (19, 11)


def test_dtw_measures_warp_not_thickness() -> None:
    """Same shape alignment at every amplitude: a warp profile is not a thickness."""
    n = 60
    a = np.sin(np.linspace(0, 4 * np.pi, n))
    b = np.sin(np.linspace(0, 4 * np.pi, n) * 1.5)
    small = dtw_align_traces(a, b)
    big = dtw_align_traces(3.0 * a, 3.0 * b)
    np.testing.assert_allclose(
        small["warp_stretch_profile"], big["warp_stretch_profile"], rtol=1e-9
    )
    assert big["distance"] == pytest.approx(3.0 * small["distance"], rel=1e-9)
    assert "thickness" not in {k.lower() for k in small}
    assert "NOT thickness" in DTW_WARP_ONLY_WARNING
    assert "does NOT measure thickness" in (dtw_align_traces.__doc__ or "")
    assert "compute_isopach" in (dtw_align_traces.__doc__ or "")


@pytest.mark.parametrize(
    "a,b",
    [
        (np.zeros((2, 2)), np.zeros(4)),
        (np.zeros(0), np.zeros(4)),
        (np.array([1.0, np.nan]), np.array([1.0, 2.0])),
    ],
)
def test_dtw_rejects_malformed_traces(a: np.ndarray, b: np.ndarray) -> None:
    with pytest.raises(ValueError):
        dtw_align_traces(a, b)


# ── Axis B: isopach ───────────────────────────────────────────────────────────────────
def _picked_horizons(
    nz: int = 120, nx: int = 40, top_row: int = 30, bot_row: int = 50
) -> tuple[np.ndarray, np.ndarray]:
    top = np.zeros((nz, nx), dtype=bool)
    bot = np.zeros((nz, nx), dtype=bool)
    top[top_row, :] = True
    bot[bot_row, :] = True
    return top, bot


def test_compute_isopach_reads_constant_thickness_off_two_picks() -> None:
    top, bot = _picked_horizons()
    out = compute_isopach(top, bot, dz_m=10.0)
    assert set(out) == {"thickness_m", "coverage"}
    assert out["thickness_m"].value == pytest.approx(200.0)
    assert out["thickness_m"].status == "MEASURED"
    assert out["thickness_m"].coverage == pytest.approx(1.0)
    assert out["coverage"].value == pytest.approx(1.0)
    assert any("no decompaction applied" in n for n in out["thickness_m"].notes)
    assert out["thickness_m"].uncertainty["decompaction_applied"] is False
    assert_measurement_invariants(out)


def test_compute_isopach_returns_unmeasured_over_a_masked_gap() -> None:
    top, bot = _picked_horizons()
    top[30, 10:20] = False  # the top pick is missing on ten traces
    profile = trace_thickness_profile(top, bot, dz_m=10.0)
    assert int(np.isnan(profile).sum()) == 10

    out = compute_isopach(top, bot, dz_m=10.0)
    measured_traces = profile[np.isfinite(profile)]
    assert out["thickness_m"].value == pytest.approx(float(np.mean(measured_traces)))
    assert out["thickness_m"].value == pytest.approx(200.0)  # NOT 150: gaps are not zeros
    assert out["thickness_m"].n_samples == 30
    assert out["thickness_m"].coverage == pytest.approx(0.75)
    assert out["thickness_m"].status == "PARTIAL"
    assert out["coverage"].value == pytest.approx(0.75)
    notes = " ".join(out["thickness_m"].notes)
    assert "10 of 40 traces" in notes
    assert "first at trace 10" in notes and "last at 19" in notes
    assert "never interpolated" in notes
    report = out["thickness_m"].uncertainty["gap_report"]
    assert report["n_traces_missing_either"] == 10
    assert report["n_traces_missing_top"] == 10 and report["n_traces_missing_bottom"] == 0
    assert_measurement_invariants(out)


def test_compute_isopach_is_unmeasured_when_every_trace_has_a_gap() -> None:
    top, bot = _picked_horizons()
    top[30, :] = False
    out = compute_isopach(top, bot, dz_m=10.0)
    assert out["thickness_m"].status == "UNMEASURED"
    assert out["thickness_m"].value is None  # not 0.0: an unmeasured interval is not thin
    assert out["coverage"].value == pytest.approx(0.0)
    assert out["coverage"].status == "MEASURED"  # the count of covered traces IS measured


def test_compute_isopach_treats_crossed_picks_as_unmeasured_not_negative() -> None:
    top, bot = _picked_horizons(top_row=60, bot_row=40)
    out = compute_isopach(top, bot, dz_m=10.0)
    assert out["thickness_m"].status == "UNMEASURED"
    assert out["thickness_m"].value is None
    assert out["thickness_m"].uncertainty["crossed_picks"] == 40
    assert any("pick-order" in n for n in out["thickness_m"].notes)


def test_compute_isopach_validates_its_inputs() -> None:
    top, bot = _picked_horizons()
    with pytest.raises(ValueError, match="same shape"):
        compute_isopach(top, bot[:, :10], dz_m=10.0)
    with pytest.raises(ValueError, match="dz_m"):
        compute_isopach(top, bot, dz_m=-1.0)


# ── (c) expansion index: UNMEASURED, never 1.0 and never 0.0 ───────────────────────────
@pytest.mark.parametrize(
    "hw,fw",
    [
        (np.array([np.nan, np.nan, np.nan]), np.array([np.nan, np.nan, np.nan])),
        (np.array([np.nan, np.nan]), np.array([10.0, 20.0])),
        (np.array([10.0, 20.0]), np.array([np.nan, np.nan])),
        (np.zeros(3), np.zeros(3)),  # footwall thickness of zero cannot form a ratio
    ],
)
def test_expansion_index_is_unmeasured_when_a_side_is_empty(hw: np.ndarray, fw: np.ndarray) -> None:
    out = expansion_index(hw, fw)
    ei = out["expansion_index"]
    assert ei.status == "UNMEASURED"
    assert ei.value is None
    assert ei.value != 1.0 and ei.value != 0.0  # the two fabricated answers, refused
    assert out["n_pairs"].value == 0.0
    assert out["n_pairs"].status == "MEASURED"
    assert any("NOT 1.0" in n or "not 1.0" in n for n in ei.notes)
    assert_measurement_invariants(out)


def test_expansion_index_reduces_by_median_over_valid_pairs() -> None:
    hw = np.array([100.0, 120.0, np.nan, 200.0])
    fw = np.array([50.0, 60.0, 40.0, 100.0])
    out = expansion_index(hw, fw)
    ei = out["expansion_index"]
    assert ei.value == pytest.approx(2.0)  # per-trace EI = [2, 2, 5] -> median 2
    assert out["n_pairs"].value == 3.0
    assert ei.coverage == pytest.approx(0.75)
    assert ei.status == "PARTIAL"
    assert ei.uncertainty["n_hangingwall_unmeasured"] == 1
    assert ei.uncertainty["median_ratio"] == pytest.approx(2.0)
    assert "median" in ei.uncertainty["reduction"]


def test_expansion_index_at_or_below_one_is_scoped_not_a_kill() -> None:
    out = expansion_index(np.array([50.0]), np.array([100.0]))
    ei = out["expansion_index"]
    assert ei.value == pytest.approx(0.5)
    doctrine = " ".join(ei.notes)
    assert "SYN-TECTONIC TIMING" in doctrine
    assert "not a kill of extension" in doctrine
    assert "slower than the sedimentation rate" in doctrine


def test_expansion_index_rejects_mismatched_array_lengths() -> None:
    with pytest.raises(ValueError, match="equal length"):
        expansion_index(np.zeros(3), np.zeros(5))


# ── Axis B: isopach differential (the tectonic test) ───────────────────────────────────
def test_isopach_differential_of_a_uniform_map_favours_the_null() -> None:
    out = isopach_differential(np.full((5, 6), 100.0))
    ratio = out["differential_ratio"]
    assert set(out) == {"differential_ratio"}
    assert ratio.value == pytest.approx(1.0)
    assert ratio.status == "MEASURED"
    notes = " ".join(ratio.notes)
    assert "0/0" in notes and "declared 0/0 convention" in notes
    assert "null depositional hypothesis" in notes
    assert_measurement_invariants(out)


def test_isopach_differential_separates_across_from_along_structure() -> None:
    rows = np.arange(5)[:, None]
    cols = np.arange(6)[None, :]
    across_dominant = 100.0 + 10.0 * rows + 0.1 * cols  # thickens across the structure
    d1 = isopach_differential(across_dominant, structure_axis=1)["differential_ratio"]
    assert d1.status == "MEASURED"
    assert d1.value > 2.0
    assert d1.uncertainty["S_across_m"] > d1.uncertainty["S_along_m"]
    assert any("ACROSS the structure" in n for n in d1.notes)

    d0 = isopach_differential(across_dominant.T, structure_axis=0)["differential_ratio"]
    assert d0.status == "MEASURED" and d0.value > 2.0


def test_isopach_differential_is_below_one_when_variation_runs_along_the_structure() -> None:
    cols = np.arange(6)[None, :]
    along_only = 100.0 + 0.1 * cols * np.ones((5, 1))
    ratio = isopach_differential(along_only, structure_axis=1)["differential_ratio"]
    assert ratio.status == "MEASURED"
    assert ratio.value == pytest.approx(0.0)
    assert any("ALONG the structure" in n for n in ratio.notes)


def test_isopach_differential_is_unmeasured_when_the_ratio_is_unbounded() -> None:
    along_flat = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
    ratio = isopach_differential(along_flat, structure_axis=1)["differential_ratio"]
    assert ratio.status == "UNMEASURED" and ratio.value is None
    assert "unbounded" in " ".join(ratio.notes)


def test_isopach_differential_needs_two_dimensions() -> None:
    ratio = isopach_differential(np.array([1.0, 2.0, 3.0]))["differential_ratio"]
    assert ratio.status == "UNMEASURED" and ratio.value is None
    all_nan = np.full((4, 4), np.nan)
    assert isopach_differential(all_nan)["differential_ratio"].status == "UNMEASURED"
    with pytest.raises(ValueError, match="structure_axis"):
        isopach_differential(np.zeros((4, 4)), structure_axis=5)


def test_isopach_differential_skips_nan_cells_without_filling_them() -> None:
    rows = np.arange(5)[:, None]
    cols = np.arange(6)[None, :]
    tmap = 100.0 + 10.0 * rows + 0.1 * cols
    holed = tmap.copy()
    holed[1:3, 2:4] = np.nan  # a masked-out patch
    out = isopach_differential(holed)["differential_ratio"]
    assert out.status == "MEASURED"
    assert out.uncertainty["n_valid_cells"] == 26  # 30 cells minus the 2x2 masked patch
    assert out.coverage == pytest.approx(26 / 30)
    assert out.value > 1.5


# ── cross-cutting: contract surfaces ───────────────────────────────────────────────────
def test_public_functions_return_exactly_the_contract_keys() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    mask = level_mask(sec)
    top, bot = _picked_horizons()
    assert set(compute_dip_field(sec, dz_m=DZ_M, dx_m=DX_M)) == {
        "dip_deg",
        "dip_azimuth_deg",
        "curvature",
    }
    assert set(extract_axis_a(sec, mask, dz_m=DZ_M, dx_m=DX_M)) == {
        "dip_deg_mean",
        "dip_deg_p95",
        "curvature_mean",
        "dip_azimuth_deg",
        "geometry_class_fired",
    }
    assert set(compute_isopach(top, bot, dz_m=10.0)) == {"thickness_m", "coverage"}
    assert set(expansion_index(np.ones(4), np.ones(4))) == {"expansion_index", "n_pairs"}
    assert set(isopach_differential(np.ones((4, 4)))) == {"differential_ratio"}
    assert set(dtw_align_traces(np.arange(6.0), np.arange(6.0))) == {
        "path",
        "distance",
        "warp_stretch_profile",
        "band",
    }
    assert set(declare_calibration_state(
        vertical_exaggeration=1.0, velocity_model_present=True, time_domain=False
    )) == {"dips_trustworthy", "problems", "migration_state"}


def test_units_are_declared_on_every_measurement() -> None:
    sec = plane_section(DIP_TRUE_DEG)
    axis_a = extract_axis_a(sec, level_mask(sec), dz_m=DZ_M, dx_m=DX_M)
    assert axis_a["dip_deg_mean"].unit == "deg"
    assert axis_a["dip_deg_p95"].unit == "deg"
    assert axis_a["curvature_mean"].unit == "1/m"
    assert axis_a["dip_azimuth_deg"].unit == "deg_azimuth"
    assert axis_a["geometry_class_fired"].unit == "count"
    top, bot = _picked_horizons()
    assert compute_isopach(top, bot, dz_m=10.0)["thickness_m"].unit == "m"
    assert expansion_index(np.ones(2), np.ones(2))["expansion_index"].unit == "ratio"


def test_measured_helper_requires_the_evidence_envelope() -> None:
    with pytest.raises(TypeError):
        measured(1.0, "deg")  # coverage / n_samples / method are mandatory
    m = measured(1.0, "deg", coverage=1.0, n_samples=10, method="named-method")
    assert m.status == "MEASURED" and m.coverage == 1.0
