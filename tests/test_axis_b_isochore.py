"""K-EI / Axis B — isochore (growth-wedge) expansion-index candidate extractor.

Contract under test
-------------------
1. A constant-thickness interval yields an EI candidate ~1.0 in the declared domain.
2. A synthetic growth wedge yields EI > 1 on the thick side and ~1.0 across the
   reference window (Thorsen-direction: hanging wall thicker than reference).
3. Missing surfaces -> UNMEASURED with the missing inputs named, and NEVER a number.
4. Wavelet phase-rotation contamination downgrades the QC verdict, and the verdict
   is emitted alongside the number — never the number alone.
5. TIME-domain picks with a DEPTH-domain request and no velocity model refuse to
   emit a depth EI (UNMEASURED, missing input named). Same for DEPTH-domain picks.
6. The lambda/8 absolute resolvability floor withholds the number (UNMEASURED).
7. Falsifier direction: a MEASURED EI <= 1 is contradiction evidence, the ABSENCE
   of a wedge is a deficit — the extractor NEVER returns KILL.
8. Every receipt carries epistemic tier, explicit sampling scales, equation,
   thresholds, exceptions, evidence refs and a receipt_hash; the hash is
   reproducible run-to-run.
9. No fabricated confidence (stays None) and no 'absolute' labelling anywhere.
10. A laterally varying velocity model changes a DEPTH EI that a constant velocity
    leaves invariant — which is why the domain and its provenance must travel with
    the number.

Scenario thresholds (phase drift, lambda/4 and lambda/8) were calibrated against the
deterministic synthetics built below; the calibration is reproducible by running this
file, not asserted from a claim.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import numpy as np
import pytest

from geox_mcp.tools.structure_gates.axis_b_isochore import (
    GATE_ID,
    axis_b_isochore,
    extract_expansion_index_candidate,
)

# ── Synthetic section builder (deterministic; no RNG anywhere) ───────────────

DT_MS = 2.0
N_SAMPLES = 400
N_TRACES = 40
TRACE_SPACING_M = 25.0
UPPER_SAMPLES = 120.0
WAVELET_F = 30.0
WAVELET_LEN = 41
WAVELET_HALF = WAVELET_LEN // 2

# beds inside the interval at fractional positions, with relative amplitudes
INTERVAL_BEDS = ((0.0, 1.0), (0.3, 0.7), (0.55, 0.9), (0.8, 0.6), (1.0, 1.0))
# fixed overburden markers (absolute sample positions) — the phase reference events
OVERBURDEN = ((20.0, 0.8), (45.0, 0.6), (70.0, 0.9))
# fixed substratum markers — the rigid block below the growth interval
SUBSTRATUM = ((300.0, 0.85), (325.0, 0.5), (350.0, 0.7))


def _ricker(n: int = WAVELET_LEN, f: float = WAVELET_F, dt_ms: float = DT_MS) -> np.ndarray:
    t = (np.arange(n) - (n - 1) / 2.0) * dt_ms / 1000.0
    a = (np.pi * f * t) ** 2
    return (1 - 2 * a) * np.exp(-a)


_W = _ricker()


def _add(amp: np.ndarray, x: int, z: float, a: float) -> None:
    centre = int(round(z))
    lo = centre - WAVELET_HALF
    for k in range(lo, centre + WAVELET_HALF + 1):
        if 0 <= k < amp.shape[0]:
            amp[k, x] += a * _W[k - lo]


def _section(thickness: np.ndarray, upper: np.ndarray, n_samples: int = N_SAMPLES) -> np.ndarray:
    """Build a 2D section: fixed overburden, a scaled bed suite in the interval, fixed substratum.

    The interval's internal beds scale with its thickness, so the interval waveform is
    genuinely stretched where the interval is thicker — which is what a correlation-based
    cross-check is supposed to detect (and what it must not be trusted as a measurement).
    """
    nt = int(thickness.size)
    amp = np.zeros((n_samples, nt), dtype=np.float64)
    for z0, a in OVERBURDEN:
        for x in range(nt):
            _add(amp, x, z0, a)
    for x in range(nt):
        zl = upper[x] + thickness[x]
        for frac, a in INTERVAL_BEDS:
            _add(amp, x, upper[x] + frac * (zl - upper[x]), a)
    for z0, a in SUBSTRATUM:
        for x in range(nt):
            _add(amp, x, z0, a)
    return amp


def _constant_interval(t_samples: float = 40.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    upper = np.full(N_TRACES, UPPER_SAMPLES)
    thickness = np.full(N_TRACES, t_samples)
    return _section(thickness, upper), upper, upper + thickness


def _growth_wedge(
    thin: float = 20.0, hinge: int = 10, rate: float = 1.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Flat `thin` interval left of the hinge, then a linear thickening wedge to the right."""
    x = np.arange(N_TRACES)
    thickness = np.where(x < hinge, thin, thin + rate * (x - hinge))
    upper = np.full(N_TRACES, UPPER_SAMPLES)
    return _section(thickness, upper), upper, upper + thickness


def _rotate_laterally(amp: np.ndarray, max_deg: float) -> np.ndarray:
    """Apply a laterally varying wavelet phase rotation (a processing artifact).

    Applied to the whole trace with the picks left untouched — exactly the situation
    the QC screen exists for: geometry says nothing changed, the wavelet did.
    """
    from scipy.signal import hilbert

    nt = amp.shape[1]
    out = np.zeros_like(amp)
    for x in range(nt):
        phi = np.deg2rad(max_deg * x / (nt - 1))
        out[:, x] = np.real(np.exp(1j * phi) * hilbert(amp[:, x]))
    return out


def _run(amp, upper, lower, **kw):
    kw.setdefault("domain", "TIME")
    kw.setdefault("sample_interval_ms", DT_MS)
    kw.setdefault("trace_spacing_m", TRACE_SPACING_M)
    return extract_expansion_index_candidate(amp, upper, lower, **kw)


# ── (a) constant thickness -> EI ~ 1.0 ───────────────────────────────────────


def test_constant_thickness_yields_unit_expansion_index():
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, lower)

    assert r["gate_id"] == GATE_ID
    assert r["status"] == "PASS", r["reason"]
    cr = r["calculated_result"]
    assert cr["expansion_index_domain"] == "TIME"
    assert cr["expansion_index_candidate"] == pytest.approx(1.0, abs=0.02)
    assert cr["expansion_index_max"] == pytest.approx(1.0, abs=0.02)
    assert cr["expansion_index_min"] == pytest.approx(1.0, abs=0.02)
    assert cr["qc_verdict"] == "CLEAN"
    assert cr["qc"]["contamination_flags"] == []
    # the ratio is a candidate observation about a picture, not about rock
    assert r["epistemic_tier"] == "KINEMATIC"
    assert cr["expansion_index_units"] == "dimensionless ratio of vertical thicknesses"


def test_unit_expansion_index_is_not_a_growth_verdict():
    """EI ~ 1.0 must not be reported as a growth verdict in either direction."""
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, lower)
    cr = r["calculated_result"]
    assert r["status"] != "KILL"
    assert "EXTRACTION QUALITY" in cr["status_semantics"]
    assert cr["falsifier"]["direction"] == "CONTRADICTION"  # measured EI <= 1 everywhere
    assert cr["falsifier"]["available"] is True
    assert "NEVER KILL" in cr["falsifier"]["rule"] or "never returns KILL" in cr["falsifier"]["rule"]


# ── (b) growth wedge -> EI > 1 on the thick side ─────────────────────────────


def test_growth_wedge_expands_on_the_thick_side():
    amp, upper, lower = _growth_wedge()
    ref = list(range(0, 10))  # the flat (reference / footwall-side) window
    r = _run(amp, upper, lower, reference_traces=ref)

    cr = r["calculated_result"]
    by_trace = cr["expansion_index_by_trace"]
    assert cr["expansion_index_domain"] == "TIME"

    assert cr["expansion_index_candidate"] > 1.0
    assert cr["expansion_index_candidate"] == cr["expansion_index_max"]
    # thick side expands, reference side stays ~1.0
    assert by_trace[-1] > 1.5
    assert by_trace[5] == pytest.approx(1.0, abs=0.05)
    assert cr["expansion_index_min"] == pytest.approx(1.0, abs=0.05)
    # monotone lateral increase across the wedge
    assert by_trace[-1] > by_trace[20] > by_trace[12]
    assert cr["falsifier"]["available"] is False
    # and the extractor still refuses to call it a geological verdict
    assert r["status"] in ("PASS", "WARN", "PARTIALLY_MEASURED")
    assert r["epistemic_tier"] == "KINEMATIC"
    assert r["expansion_index_domain"] == "TIME"


def test_reference_basis_is_declared_not_assumed():
    amp, upper, lower = _growth_wedge()
    with_ref = _run(amp, upper, lower, reference_traces=list(range(0, 10)))
    without_ref = _run(amp, upper, lower)

    assert "supplied_reference_window" in with_ref["calculated_result"]["reference_basis"]
    assert "NOT a fault-side footwall" in without_ref["calculated_result"]["reference_basis"]
    # a section-median reference is weaker evidence than a declared reference window
    assert without_ref["calculated_result"]["expansion_index_candidate"] < with_ref["calculated_result"][
        "expansion_index_candidate"
    ]


# ── (c) missing surfaces -> UNMEASURED, never a number ───────────────────────


def test_missing_surfaces_return_unmeasured_with_named_inputs():
    amp, upper, lower = _constant_interval()
    r = _run(amp, None, None)

    assert r["status"] == "UNMEASURED"
    assert r["verdict"] == "UNMEASURED"  # alias kept
    assert "horizon_upper" in r["missing_inputs"]
    assert "horizon_lower" in r["missing_inputs"]
    cr = r["calculated_result"]
    assert cr["expansion_index_candidate"] is None
    assert cr["expansion_index_max"] is None
    assert cr["expansion_index_domain"] is None
    assert r["claims_handoff"]["expansion_index"] is None
    assert r["claims_handoff"]["trust"] == "NOT_EMITTED"
    assert r["status"] != "PASS"


def test_missing_lower_surface_alone_is_named():
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, None)
    assert r["status"] == "UNMEASURED"
    assert "horizon_lower" in r["missing_inputs"]
    assert "horizon_upper" not in r["missing_inputs"]
    assert r["calculated_result"]["expansion_index_candidate"] is None


def test_missing_amplitude_is_named_and_never_measured():
    amp, upper, lower = _constant_interval()
    r = _run(None, upper, lower)
    assert r["status"] == "UNMEASURED"
    assert "amplitude" in r["missing_inputs"]
    assert r["calculated_result"]["expansion_index_candidate"] is None


def test_implicit_workspace_scales_are_refused():
    """Sample interval / bin spacing must be explicit — never silently inherited."""
    amp, upper, lower = _constant_interval()
    r = extract_expansion_index_candidate(amp, upper, lower, domain="TIME")
    assert r["status"] == "UNMEASURED"
    assert "sample_interval_ms" in r["missing_inputs"]
    assert "trace_spacing_m" in r["missing_inputs"]
    assert r["calculated_result"]["expansion_index_candidate"] is None


def test_misaligned_surfaces_are_refused_not_silently_fixed():
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper[:-3], lower)
    assert r["status"] == "UNMEASURED"
    assert any("aligned to the amplitude trace axis" in m for m in r["missing_inputs"])
    assert r["calculated_result"]["expansion_index_candidate"] is None


# ── (d) phase-rotation contamination downgrades the QC verdict ───────────────


def test_phase_rotation_contamination_downgrades_the_qc_verdict():
    amp, upper, lower = _growth_wedge()
    ref = list(range(0, 10))
    clean = _run(amp, upper, lower, reference_traces=ref)
    dirty = _run(_rotate_laterally(amp, 90.0), upper, lower, reference_traces=ref)

    clean_cr = clean["calculated_result"]
    dirty_cr = dirty["calculated_result"]

    # the clean section is clean ...
    assert clean_cr["qc_verdict"] == "CLEAN"
    assert clean_cr["qc"]["contamination_flags"] == []
    assert clean["status"] == "PASS"

    # ... the phase-rotated one is not, by a MEASURED drift
    assert dirty_cr["qc_verdict"] in ("CAVEATED", "CONTAMINATED")
    assert dirty["status"] in ("WARN", "PARTIALLY_MEASURED")
    assert dirty["status"] != "PASS"
    assert dirty["status"] != "KILL"
    assert any("phase" in f for f in dirty_cr["qc"]["contamination_flags"])

    phase_check = {c["name"]: c for c in dirty_cr["qc"]["checks"]}["wavelet_phase_rotation"]
    clean_check = {c["name"]: c for c in clean_cr["qc"]["checks"]}["wavelet_phase_rotation"]
    assert phase_check["measured"]["end_to_end_phase_drift_deg"] > (
        clean_check["measured"]["end_to_end_phase_drift_deg"] + 45.0
    )
    assert phase_check["verdict"] == "CONTAMINATED"

    # the number is emitted WITH the verdict, never alone
    assert dirty_cr["expansion_index_candidate"] is not None
    assert dirty_cr["qc_verdict"] != "CLEAN"
    assert dirty["claims_handoff"]["trust"] == "QC_CAVEATED"
    assert dirty["claims_handoff"]["qc_verdict"] == dirty_cr["qc_verdict"]
    assert dirty["claims_handoff"]["contamination_flags"]


def test_clean_and_contaminated_cases_are_distinguishable_by_the_qc_block():
    amp, upper, lower = _growth_wedge()
    ref = list(range(0, 10))
    clean = _run(amp, upper, lower, reference_traces=ref)
    dirty = _run(_rotate_laterally(amp, 90.0), upper, lower, reference_traces=ref)
    assert clean["calculated_result"]["qc"] != dirty["calculated_result"]["qc"]
    assert clean["receipt_hash"] != dirty["receipt_hash"]


# ── (e) domain discipline: TIME is not DEPTH ─────────────────────────────────


def test_time_input_refuses_to_emit_a_depth_expansion_index():
    amp, upper, lower = _constant_interval()
    r = extract_expansion_index_candidate(
        amp,
        upper,
        lower,
        domain="TIME",
        target_domain="DEPTH",
        sample_interval_ms=DT_MS,
        trace_spacing_m=TRACE_SPACING_M,
    )
    assert r["status"] == "UNMEASURED"
    assert any("velocity_model" in m for m in r["missing_inputs"])
    cr = r["calculated_result"]
    assert cr["expansion_index_candidate"] is None
    assert cr["expansion_index_domain"] is None
    assert "velocity" in r["reason"].lower() or "DEPTH" in r["reason"]
    assert r["input_domain"] == "TIME"
    assert r["expansion_index_domain"] is None


def test_depth_domain_picks_also_require_a_velocity_model():
    amp, upper, lower = _constant_interval()
    r = extract_expansion_index_candidate(
        amp, upper, lower, domain="DEPTH", sample_interval_m=2.0, trace_spacing_m=TRACE_SPACING_M
    )
    assert r["status"] == "UNMEASURED"
    assert "velocity_model" in r["missing_inputs"]
    assert r["calculated_result"]["expansion_index_candidate"] is None


@pytest.mark.parametrize(
    "bad_model",
    [
        None,
        {},
        {"velocity_model_id": "no-velocity"},
        {"interval_v_m_s": -100.0},
        {"interval_v_m_s": 99000.0},  # physically impossible
        {"interval_v_m_s_by_trace": [2500.0] * 7},  # wrong length for the trace axis
    ],
)
def test_unusable_velocity_model_is_refused_not_approximated(bad_model):
    amp, upper, lower = _constant_interval()
    r = extract_expansion_index_candidate(
        amp,
        upper,
        lower,
        domain="DEPTH",
        sample_interval_m=2.0,
        trace_spacing_m=TRACE_SPACING_M,
        velocity_model=bad_model,
    )
    assert r["status"] == "UNMEASURED"
    assert any("velocity_model" in m for m in r["missing_inputs"])
    assert r["calculated_result"]["expansion_index_candidate"] is None


def test_declared_velocity_emits_a_depth_domain_number():
    amp, upper, lower = _constant_interval()
    r = extract_expansion_index_candidate(
        amp,
        upper,
        lower,
        domain="DEPTH",
        sample_interval_m=2.0,
        trace_spacing_m=TRACE_SPACING_M,
        velocity_model={"interval_v_m_s": 2500.0, "velocity_model_id": "synthetic-const"},
    )
    cr = r["calculated_result"]
    assert r["status"] == "PASS"
    assert cr["expansion_index_domain"] == "DEPTH"
    assert cr["thickness_units"] == "m"
    assert cr["expansion_index_candidate"] == pytest.approx(1.0, abs=0.02)
    assert r["expansion_index_domain"] == "DEPTH"


def test_laterally_varying_velocity_changes_the_depth_ei_that_a_scalar_leaves_invariant():
    """Why the domain + its provenance must travel with the number.

    Same picks, same geometry. A scalar V leaves the ratio invariant; a laterally
    varying V manufactures a DEPTH-domain 'expansion' that the geology does not have.
    """
    amp, upper, lower = _constant_interval()
    time_only = _run(amp, upper, lower)
    scalar_v = extract_expansion_index_candidate(
        amp,
        upper,
        lower,
        domain="TIME",
        target_domain="DEPTH",
        sample_interval_ms=DT_MS,
        trace_spacing_m=TRACE_SPACING_M,
        velocity_model={"interval_v_m_s": 2500.0},
    )
    lateral_v = extract_expansion_index_candidate(
        amp,
        upper,
        lower,
        domain="TIME",
        target_domain="DEPTH",
        sample_interval_ms=DT_MS,
        trace_spacing_m=TRACE_SPACING_M,
        velocity_model={"interval_v_m_s_by_trace": np.linspace(2000.0, 3000.0, N_TRACES).tolist()},
    )

    t_max = time_only["calculated_result"]["expansion_index_max"]
    s_max = scalar_v["calculated_result"]["expansion_index_max"]
    l_max = lateral_v["calculated_result"]["expansion_index_max"]
    assert t_max == pytest.approx(1.0, abs=0.02)
    assert s_max == pytest.approx(t_max, abs=0.02)  # scalar V: ratio invariant
    assert scalar_v["calculated_result"]["domain_conversion"]["constant_velocity_invariance"] is True
    assert l_max > 1.1  # spurious depth 'expansion' from the velocity field alone
    assert lateral_v["calculated_result"]["expansion_index_domain"] == "DEPTH"


# ── tuning: lambda/4 caveat, lambda/8 absolute floor ─────────────────────────


def test_interval_below_lambda8_floor_withholds_the_number():
    amp, upper, lower = _constant_interval()  # median interval thickness 80 ms
    r = _run(amp, upper, lower, dominant_wavelength=1000.0)  # 80/1000 = 0.08 < 1/8

    assert r["status"] == "UNMEASURED"
    cr = r["calculated_result"]
    assert cr["expansion_index_candidate"] is None
    assert cr["expansion_index_domain"] is None
    assert cr["withheld"]["expansion_index"] == "withheld_below_lambda_8_absolute_floor"
    assert cr["resolution"]["thickness_over_lambda"] < 0.125
    assert any("lambda/8" in m for m in r["missing_inputs"])


def test_interval_between_lambda8_and_lambda4_is_caveated_not_clean():
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, lower, dominant_wavelength=400.0)  # 80/400 = 0.2 -> in [1/8, 1/4)

    cr = r["calculated_result"]
    assert r["status"] == "WARN"
    assert cr["qc_verdict"] == "CAVEATED"
    assert "tuning_risk_below_lambda4" in cr["qc"]["contamination_flags"]
    assert cr["expansion_index_candidate"] == pytest.approx(1.0, abs=0.02)  # number still travels, with the caveat


def test_declared_wavelength_is_reported_with_its_source():
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, lower, dominant_wavelength=400.0)
    tuning = {c["name"]: c for c in r["calculated_result"]["qc"]["checks"]}["tuning_resolution"]
    assert tuning["measured"]["dominant_wavelength"] == pytest.approx(400.0)
    assert "declared" in tuning["measured"]["wavelength_source"]

    r2 = _run(amp, upper, lower)
    tuning2 = {c["name"]: c for c in r2["calculated_result"]["qc"]["checks"]}["tuning_resolution"]
    assert tuning2["measured"]["dominant_wavelength"] > 0
    assert "estimated" in tuning2["measured"]["wavelength_source"]


# ── falsifier direction and the DTW slop constraint ──────────────────────────


def test_measured_ei_at_or_below_one_is_contradiction_not_kill():
    """A thinning interval relative to the reference is measured contradiction evidence."""
    x = np.arange(N_TRACES)
    thickness = np.where(x < 10, 50.0, 50.0 - 1.0 * (x - 10))
    upper = np.full(N_TRACES, UPPER_SAMPLES)
    amp = _section(thickness, upper)
    r = _run(amp, upper, upper + thickness, reference_traces=list(range(0, 10)))

    cr = r["calculated_result"]
    assert cr["expansion_index_max"] <= 1.0
    assert cr["expansion_index_min"] < 1.0
    assert cr["falsifier"]["direction"] == "CONTRADICTION"
    assert cr["falsifier"]["available"] is True
    # the extractor does NOT kill — the consuming gate owns that decision
    assert r["status"] != "KILL"


def test_wedge_absence_is_a_deficit_not_a_contradiction():
    """No detectable growth wedge must be UNMEASURED-or-clean, never KILL."""
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, lower)
    assert r["status"] != "KILL"
    assert r["calculated_result"]["qc_verdict"] == "CLEAN"
    assert "DEFICIT" in r["calculated_result"]["falsifier"]["rule"].replace("deficit", "DEFICIT").upper()


def test_warp_path_is_slop_bounded_and_only_a_crosscheck():
    amp, upper, lower = _growth_wedge()
    r = _run(amp, upper, lower, reference_traces=list(range(0, 10)))
    warp = r["calculated_result"]["warp_crosscheck"]

    assert warp["available"] is True
    assert warp["n_censored_by_band"] == 0
    assert warp["n_rejected_by_slop"] == 0
    assert warp["agreement_fraction"] == 1.0
    assert warp["implied_ratio_median"] == pytest.approx(warp["pick_ratio_median"], abs=0.05)
    assert warp["band_definition"].startswith("band_samples = ceil(")
    assert "CORRELATION artifact" in warp["note"]
    # the emitted index is the PICK-derived candidate, never the warp value
    assert r["calculated_result"]["expansion_index_statistic"].startswith("max of the median-filtered")
    assert r["thresholds"]["max_slop_fraction_per_trace_step"] == pytest.approx(0.25)


def test_slop_constraint_censors_a_warp_beyond_the_declared_maximum():
    """Tighten the slop below the true lateral change: the warp can no longer express it.

    The censored pairs must be DROPPED from the comparison (a path that rides the band
    edge is unconstrained, not informative) and the QC verdict must carry the flag.
    """
    amp, upper, lower = _growth_wedge()
    ref = list(range(0, 10))
    tight = _run(amp, upper, lower, reference_traces=ref, max_slop_fraction=0.02)
    warp = tight["calculated_result"]["warp_crosscheck"]

    assert tight["thresholds"]["max_slop_fraction_per_trace_step"] == pytest.approx(0.02)
    assert warp["n_censored_by_band"] > 0
    assert warp["n_pairs_compared"] < warp["n_pairs_sampled"]
    assert "dtw_warp_censored_by_band" in tight["calculated_result"]["qc"]["contamination_flags"]
    assert tight["status"] != "PASS"
    assert tight["status"] != "KILL"

    # the same data with the declared (looser) slop is fully compared
    loose = _run(amp, upper, lower, reference_traces=ref)
    assert loose["calculated_result"]["warp_crosscheck"]["n_censored_by_band"] == 0


def test_laterally_aliased_thickness_is_flagged_as_a_pick_correlation_conflict():
    """Erratic/aliased thickness: the picks and the waveform correspondence disagree.

    The extractor must NOT arbitrate silently between the two — it reports the conflict.
    """
    x = np.arange(N_TRACES)
    thickness = np.where(x % 2 == 0, 20.0, 45.0)  # lateral aliasing / mis-pick
    upper = np.full(N_TRACES, UPPER_SAMPLES)
    amp = _section(thickness, upper)
    r = _run(amp, upper, upper + thickness)

    warp = r["calculated_result"]["warp_crosscheck"]
    flags = r["calculated_result"]["qc"]["contamination_flags"]
    assert warp["agreement_fraction"] < 0.6
    assert "pick_correlation_conflict" in flags
    assert r["status"] in ("WARN", "PARTIALLY_MEASURED")
    assert r["calculated_result"]["qc_verdict"] in ("CAVEATED", "CONTAMINATED")
    # the number is still emitted, but never without the conflict flag
    assert r["calculated_result"]["expansion_index_candidate"] is not None
    assert r["calculated_result"]["qc_verdict"] != "CLEAN"


# ── receipt contract / determinism / anti-fabrication ────────────────────────


def test_receipt_contract_is_complete():
    amp, upper, lower = _growth_wedge()
    r = _run(amp, upper, lower, reference_traces=list(range(0, 10)))

    for key in (
        "gate",
        "gate_id",
        "status",
        "verdict",
        "equation",
        "thresholds",
        "calculated_result",
        "exceptions_considered",
        "evidence_refs",
        "receipt_hash",
        "epistemic_tier",
        "missing_inputs",
        "claims_handoff",
    ):
        assert key in r, key
    assert r["gate"] == GATE_ID == "K-EI"
    assert "EI_candidate" in r["equation"]
    assert len(r["receipt_hash"]) == 64
    assert r["thresholds"]["ei_growth_min"] == 1.0
    assert r["thresholds"]["tuning_fraction_lambda4"] == pytest.approx(0.25)
    assert r["thresholds"]["resolvability_floor_fraction_lambda8"] == pytest.approx(0.125)
    assert r["thresholds"]["min_coverage"] == pytest.approx(0.5)
    assert r["exceptions_considered"] and r["evidence_refs"]
    assert r["epistemic_tier"] == "KINEMATIC"
    assert "STRAIN" in r["epistemic_caveat"] and "DYNAMIC" in r["epistemic_caveat"]


def test_sampling_scales_are_echoed_explicitly():
    amp, upper, lower = _constant_interval()
    r = _run(amp, upper, lower)
    sampling = r["calculated_result"]["sampling"]
    assert sampling["vertical_sample_interval"] == pytest.approx(DT_MS)
    assert sampling["vertical_sample_interval_units"].startswith("ms")
    assert sampling["trace_spacing_m"] == pytest.approx(TRACE_SPACING_M)
    assert sampling["explicitly_supplied"] is True
    assert r["inputs"]["sample_interval_ms"] == pytest.approx(DT_MS)
    assert r["inputs"]["trace_spacing_m"] == pytest.approx(TRACE_SPACING_M)


def test_receipt_is_deterministic_and_input_identifying():
    amp, upper, lower = _growth_wedge()
    a = _run(amp, upper, lower, reference_traces=list(range(0, 10)))
    b = _run(amp.copy(), upper.copy(), lower.copy(), reference_traces=list(range(0, 10)))
    assert a["receipt_hash"] == b["receipt_hash"]
    assert a["inputs"]["artifact_sha256_amplitude"].startswith("sha256:")
    assert a["inputs"]["artifact_sha256_horizon_lower"].startswith("sha256:")
    assert a["inputs"]["artifact_sha256_amplitude"] in " ".join(a["evidence_refs"])

    c = _run(amp + 0.001, upper, lower, reference_traces=list(range(0, 10)))
    assert c["receipt_hash"] != a["receipt_hash"]


def test_no_fabricated_confidence_and_no_absolute_claim():
    amp, upper, lower = _growth_wedge()
    r = _run(amp, upper, lower, reference_traces=list(range(0, 10)))
    cr = r["calculated_result"]
    assert cr["confidence"] is None
    assert "validated benchmark receipt" in cr["confidence_note"]
    blob = repr(r).lower()
    assert "absolute" not in blob or "absolute floor" in blob or "absolute_resolvability" in blob
    assert "reliability" not in blob


def test_extractor_never_returns_kill_on_any_degenerate_input():
    amp, upper, lower = _constant_interval()
    cases = [
        _run(amp, None, None),
        _run(None, upper, lower),
        _run(amp, upper[:-3], lower),
        _run(amp, upper, lower, dominant_wavelength=1000.0),
        extract_expansion_index_candidate(amp, upper, lower, domain="wobble"),
        extract_expansion_index_candidate(
            amp, upper, lower, domain="TIME", target_domain="DEPTH",
            sample_interval_ms=DT_MS, trace_spacing_m=TRACE_SPACING_M,
        ),
        _run(amp, upper, lower, reference_traces=[0, 1]),
    ]
    for r in cases:
        assert r["status"] != "KILL"
        assert r["status"] in ("UNMEASURED", "WARN", "PASS", "PARTIALLY_MEASURED", "NOT_APPLICABLE", "COMPUTABLE")
        assert r["receipt_hash"]


def test_unmeasured_is_not_a_pass():
    amp, upper, lower = _constant_interval()
    r = _run(amp, None, None)
    assert r["status"] == "UNMEASURED"
    assert r["calculated_result"]["qc_verdict"] == "UNMEASURED"
    assert r["calculated_result"]["withheld"]["expansion_index"] == "not_measured"
    assert r["coverage"] is None


def test_alias_entry_point_is_the_same_function():
    assert axis_b_isochore is extract_expansion_index_candidate


def test_handoff_feeds_the_consuming_gate_without_ever_upgrading_unmeasured():
    """Axis B is only worth anything if the K-GROWTH consumer can read it.

    Two halves of the contract matter: a measured candidate reaches
    `claims.expansion_index`, and an UNMEASURED extraction hands off None so the
    consumer stays UNMEASURED instead of silently passing.
    """
    growth = pytest.importorskip("geox_mcp.tools.structure_gates.growth")

    amp, upper, lower = _growth_wedge()
    measured = _run(amp, upper, lower, reference_traces=list(range(0, 10)))
    handoff = measured["claims_handoff"]
    assert isinstance(handoff["expansion_index"], float)
    assert handoff["expansion_index_domain"] == "TIME"
    got = growth.gate_k_growth({"claims": {"growth": True, "expansion_index": handoff["expansion_index"]}})
    assert got["status"] in ("WARN", "PASS")  # EI > 1 supports growth; the mimic caveat applies
    assert got["status"] != "KILL"

    blank = _run(amp, None, None)
    assert blank["claims_handoff"]["expansion_index"] is None
    got_blank = growth.gate_k_growth({"claims": {"growth": True, "expansion_index": None}})
    assert got_blank["status"] == "UNMEASURED"
    assert got_blank["status"] != "PASS"


def test_peak_picking_primitives_are_reused_not_reimplemented():
    """The module must consume the shared primitives, not re-derive its own."""
    import geox_mcp.tools.structure_gates.axis_b_isochore as mod

    src_imports = mod.__dict__
    assert src_imports["semblance_coherence"] is not None
    assert src_imports["structure_tensor"] is not None
    assert src_imports["artifact_sha256"] is not None
    amp, upper, lower = _growth_wedge()
    r = _run(amp, upper, lower, reference_traces=list(range(0, 10)))
    checks = {c["name"] for c in r["calculated_result"]["qc"]["checks"]}
    assert "lateral_coherence" in checks  # from semblance_coherence
    assert "structural_context" in r["calculated_result"]  # from structure_tensor
