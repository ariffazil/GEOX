"""K-EI / Axis B — isochore (growth-wedge) EXPANSION-INDEX CANDIDATE extractor.

Why this module exists
----------------------
``gate_k_growth`` (K-GROWTH) and ``K-EXT-GROWTH`` CONSUME ``claims.expansion_index``,
but nothing in GEOX PRODUCES one from seismic. This module is that producer — and
only a producer of a *candidate*: it never seals, never asserts growth.

The number, and the frame that must travel with it
--------------------------------------------------
The expansion index extracted here is the lateral thickness ratio of one picked
interval::

    EI(x) = T_smooth(x) / T_ref        T(x) = lower_pick(x) - upper_pick(x)

Three things are emitted WITH the number, never separately:

1. **Domain.** Thickness in TIME is an isochron, not a thickness. A TIME-domain EI
   is a ratio of two-way times. Declaring a DEPTH-domain EI requires a supplied
   velocity model; without one this module returns UNMEASURED and names the
   missing input instead of converting. Note also that a single scalar V leaves
   the *ratio* invariant — only a laterally varying V(t,x) changes EI — so a
   scalar V converts thickness but does not convert the EI claim.
2. **QC verdict.** Trace-to-trace correspondence is a CORRELATION artifact. The
   constrained-DTW warp path is used only as a bounded cross-check, and the whole
   extraction is screened for phase-rotation, tuning (lambda/4, absolute floor
   lambda/8) and lateral-amplitude contamination. A contaminated number is
   reported as contaminated (PARTIALLY_MEASURED) or withheld (UNMEASURED).
3. **Epistemic tier.** A 2D-section EI is at most KINEMATIC. It is NOT STRAIN
   (needs restoration + plane-strain assumptions) and NOT DYNAMIC (needs
   fault-slip inversion). PASS here means "the candidate was measured with a
   clean QC", never "growth is proven".

Falsifier direction (iron rule)
-------------------------------
A *measured* EI <= 1 is CONTRADICTION evidence against a syn-tectonic growth claim
for that interval. The mere ABSENCE of a detectable growth wedge is a DEFICIT —
sub-tuning growth is invisible and a fault moving slower than the sediment supply
leaves no signature at all. Therefore this module NEVER returns KILL; the
falsifier is exposed as a direction flag for the consuming gate, and a missing
wedge returns UNMEASURED.

Determinism
-----------
Reproducible, not dimensionally TRUE. Identical inputs + identical explicit scales
produce an identical ``receipt_hash``; no RNG, no wall-clock, no environment
inheritance. Vertical sample interval and trace spacing must be supplied
explicitly — a workspace scale is never silently inherited. Nothing here is
labelled absolute: an image-derived geometry is an observation about a picture,
not about rock.

Reused primitives (not reimplemented)
-------------------------------------
``artifact_sha256`` (input identity), ``semblance_coherence`` (lateral continuity),
``structure_tensor`` (independent apparent-dip context). ``dp_horizon_tracker`` and
``ridge_extraction`` are deliberately NOT used: this module CONSUMES supplied
picks, and re-picking here would be a second, silent interpretation.

No new dependencies (numpy + scipy only).

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt, receipt_hash
from geox_mcp.tools.seismic_classical import (
    artifact_sha256,
    semblance_coherence,
    structure_tensor,
)

# ── Identity / doctrine constants ────────────────────────────────────────────

GATE_ID = "K-EI"
TIER_KINEMATIC = "KINEMATIC"
SCOPE = "interval_isochore_candidate"

_EQUATION = (
    "EI_candidate(x) = T_smooth(x) / T_ref, with T(x) = lower_pick(x) - upper_pick(x) "
    "in the DECLARED domain (TIME -> ms of two-way time, DEPTH -> m); cross-checked by "
    "a slop-constrained DTW warp-path slope over the same interval"
)

# Declared thresholds. Values are the defaults; every one is echoed in the
# receipt `thresholds` block with the value actually used.
_LAMBDA4_TUNING_FRACTION = 1.0 / 4.0  # Kallweit & Wood 1982 — tuning limit
_LAMBDA8_FLOOR_FRACTION = 1.0 / 8.0  # Widess 1973 — absolute resolvability floor
_MAX_SLOP_FRACTION = 0.25  # max plausible |dT|/T per adjacent trace step
_PHASE_STEP_TOL_DEG = 15.0  # lateral instantaneous-phase step at the event
_PHASE_DRIFT_TOL_DEG = 45.0  # end-to-end lateral instantaneous-phase drift
_LATERAL_AMP_TOL_DB = 6.0  # per-step interval RMS change
_LATERAL_COHERENCE_FLOOR = 0.30  # lateral semblance inside the interval
_WARP_CENSORED_FRACTION_TOL = 0.25  # DTW paths riding the band edge
_WARP_AGREEMENT_TOL_REL = 0.25  # |warp - pick ratio| / pick ratio
_WARP_AGREEMENT_MIN_FRACTION = 0.60
_MIN_COVERAGE = 0.50
_MIN_VALID_TRACES = 8
_MIN_SERIES_SAMPLES = 4  # an interval thinner than this is not measurable
_DTW_MIN_WINDOW = 8

# Hard physical band for any supplied velocity (rock-physics sanity, not a prior).
_V_HARD_BOUNDS = (500.0, 9000.0)

# Deterministic cap on the number of adjacent-trace DTW pairs evaluated. Longer
# sections are uniformly strided (reported, never silent).
_MAX_DTW_PAIRS = 600

_EXCEPTIONS = [
    "sedimentary mimic — depositional thickening without fault activity (Castelltort caveat)",
    "differential compaction over a buried high reproduces growth-like thinning/wedging (Chopra)",
    "sedimentation outpaced fault slip — growth wedge invisible, no signature to find",
    "wavelet phase rotation mimicking an isochore change",
    "tuning — beds below lambda/4 unresolvable, lambda/8 absolute floor",
    "lateral amplitude/AGC variations distorting a correlation-based correspondence",
    "toe/thrust-side duplication or erosion truncating the interval",
]

_EVIDENCE = [
    "Thorsen 1963 — growth-fault expansion index (hanging-wall / footwall thickness ratio)",
    "Widess 1973 (Geophysics 38) — lambda/8 thin-bed resolvability floor",
    "Kallweit & Wood 1982 — tuning thickness at lambda/4",
    "Sakoe & Chiba 1978 — constrained dynamic time warping (slop / band constraint)",
    "Castelltort et al. — sedimentary vs tectonic mimic of growth geometry",
    "Chopra — seismic attribute expression of differential compaction",
    "Suppe et al. 1992 — growth strata geometry set by folding mechanism AND the relative rates "
    "of sedimentation and uplift",
]

_LIMITATIONS = [
    "A section-wide (laterally invariant) wavelet phase rotation is NOT detectable from the data "
    "alone — only a well-tie or a known source wavelet can resolve it. Only laterally varying "
    "phase is screened here.",
    "Time-domain thickness is not depth thickness. Any DEPTH-domain number requires a supplied "
    "velocity model; a scalar V leaves the EI ratio invariant.",
    "A 2D section gives no strike-direction control: EI here is an apparent (in-plane) ratio, "
    "never a 3D strain or a restored length balance.",
    "DTW warp paths are correlation artifacts. They are used only as a bounded consistency "
    "screen and never as the expansion index itself.",
]


# ── Receipt helper (house style: tier/scope/coverage folded into the hash) ────


def _receipt(
    gate_id: str,
    status: str,
    *,
    tier: str,
    scope: str = SCOPE,
    coverage: float | None = None,
    extras: dict[str, Any] | None = None,
    **kw: Any,
) -> dict[str, Any]:
    r = make_gate_receipt(gate_id, status, **kw)  # type: ignore[arg-type]
    r["epistemic_tier"] = tier
    r["scope"] = scope
    r["coverage"] = coverage
    if extras:
        r.update(extras)
    r["receipt_hash"] = receipt_hash(r)
    return r


def _empty_result(reason_kind: str) -> dict[str, Any]:
    return {
        "expansion_index_candidate": None,
        "expansion_index_domain": None,
        "expansion_index_units": None,
        "expansion_index_by_trace": None,
        "expansion_index_max": None,
        "expansion_index_min": None,
        "expansion_index_median": None,
        "qc_verdict": "UNMEASURED",
        "qc": {"verdict": "UNMEASURED", "checks": [], "contamination_flags": [], "limitations": _LIMITATIONS},
        "confidence": None,  # iron rule: no fabricated confidence, ever
        "withheld": {"expansion_index": reason_kind},
    }


def _unmeasured(
    reason: str,
    *,
    missing: Sequence[str],
    inputs: dict[str, Any] | None = None,
    thresholds: dict[str, Any] | None = None,
    coverage: float | None = None,
    result_extra: dict[str, Any] | None = None,
    input_domain: str | None = None,
    target_domain: str | None = None,
) -> dict[str, Any]:
    cr = _empty_result("not_measured")
    if result_extra:
        cr.update(result_extra)
    return _receipt(
        GATE_ID,
        "UNMEASURED",
        tier=TIER_KINEMATIC,
        coverage=coverage,
        reason=reason,
        equation=_EQUATION,
        inputs=inputs or {},
        thresholds=thresholds or _effective_thresholds(),
        measurement_units="dimensionless (ratio of vertical thicknesses in the declared domain)",
        calculated_result=cr,
        missing_inputs=list(missing),
        exceptions_considered=_EXCEPTIONS,
        evidence_refs=_EVIDENCE,
        gate_type="soft_conditional",
        extras={
            "input_domain": input_domain,
            "target_domain": target_domain,
            "expansion_index_domain": None,  # nothing emitted -> no domain claim
            "claims_handoff": {
                "expansion_index": None,
                "expansion_index_domain": None,
                "qc_verdict": "UNMEASURED",
                "source_gate": GATE_ID,
                "trust": "NOT_EMITTED",
            },
        },
    )


def _effective_thresholds(**over: Any) -> dict[str, Any]:
    t = {
        "ei_growth_min": 1.0,
        "tuning_fraction_lambda4": _LAMBDA4_TUNING_FRACTION,
        "resolvability_floor_fraction_lambda8": _LAMBDA8_FLOOR_FRACTION,
        "max_slop_fraction_per_trace_step": _MAX_SLOP_FRACTION,
        "phase_step_tol_deg": _PHASE_STEP_TOL_DEG,
        "phase_drift_tol_deg": _PHASE_DRIFT_TOL_DEG,
        "lateral_amplitude_tol_db": _LATERAL_AMP_TOL_DB,
        "lateral_coherence_floor": _LATERAL_COHERENCE_FLOOR,
        "warp_censored_fraction_tol": _WARP_CENSORED_FRACTION_TOL,
        "warp_agreement_tol_relative": _WARP_AGREEMENT_TOL_REL,
        "warp_agreement_min_fraction": _WARP_AGREEMENT_MIN_FRACTION,
        "min_coverage": _MIN_COVERAGE,
        "min_valid_traces": _MIN_VALID_TRACES,
    }
    t.update(over)
    return t


# ── Small numeric helpers ────────────────────────────────────────────────────


def _as_series(v: Any) -> np.ndarray | None:
    """Coerce a per-trace pick series (or 1-column pick array) to a 1D float array."""
    if v is None:
        return None
    try:
        a = np.asarray(v, dtype=float)
    except (TypeError, ValueError):
        return None
    a = np.squeeze(a)
    if a.ndim == 0:
        a = a.reshape(1)
    if a.ndim != 1:
        return None
    return a


def _round(v: Any, nd: int = 6) -> Any:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return round(f, nd)


def _circ_mean_deg(phi_deg: np.ndarray) -> float | None:
    if phi_deg.size == 0:
        return None
    rad = np.deg2rad(phi_deg)
    return float(np.rad2deg(np.arctan2(np.mean(np.sin(rad)), np.mean(np.cos(rad)))))


def _circ_diff_deg(a_deg: float, b_deg: float) -> float:
    return float((a_deg - b_deg + 180.0) % 360.0 - 180.0)


def _resolve_velocity(velocity_model: Any) -> tuple[np.ndarray | None, str | None]:
    """Return (velocity, provenance_note). Velocity is a scalar array or per-trace array.

    Only a declared, physically sane model is accepted. Nothing is inferred.
    """
    if not isinstance(velocity_model, dict):
        return None, None
    v = velocity_model.get("interval_v_m_s")
    by_trace = velocity_model.get("interval_v_m_s_by_trace")
    arr: np.ndarray | None = None
    if by_trace is not None:
        try:
            arr = np.asarray(by_trace, dtype=float).squeeze()
        except (TypeError, ValueError):
            return None, None
    elif v is not None:
        try:
            arr = np.asarray(float(v), dtype=float)
        except (TypeError, ValueError):
            return None, None
    if arr is None:
        return None, None
    if not np.all(np.isfinite(arr)) or np.any(arr <= 0):
        return None, None
    lo, hi = _V_HARD_BOUNDS
    if np.any(arr < lo) or np.any(arr > hi):
        return None, None
    src = str(velocity_model.get("velocity_model_id") or velocity_model.get("source") or "unspecified")
    kind = "per_trace" if arr.ndim == 1 else "scalar"
    return arr, f"declared velocity_model ({kind}, id={src})"


def _dominant_period(amp: np.ndarray, valid: np.ndarray, dt_ms: float | None) -> tuple[float | None, dict[str, Any]]:
    """Dominant vertical period (ms) from the pooled, Hann-windowed trace spectrum.

    Estimator: peak of the mean amplitude spectrum of the whole valid section,
    excluding DC. period = 1/f_peak. Reported so the reader can re-derive it.
    """
    n_s = amp.shape[0]
    sub = amp[:, valid]
    if sub.shape[1] == 0 or n_s < 8 or dt_ms is None or dt_ms <= 0:
        return None, {"estimator": "pooled_vertical_amplitude_spectrum", "available": False}
    sub = sub - np.mean(sub, axis=0, keepdims=True)
    win = np.hanning(n_s)[:, None]
    spec = np.abs(np.fft.rfft(sub * win, axis=0)).mean(axis=1)
    freqs = np.fft.rfftfreq(n_s, d=dt_ms / 1000.0)  # Hz
    if spec.size < 3:
        return None, {"estimator": "pooled_vertical_amplitude_spectrum", "available": False}
    k = int(np.argmax(spec[1:])) + 1
    f_pk = float(freqs[k])
    if f_pk <= 0:
        return None, {"estimator": "pooled_vertical_amplitude_spectrum", "available": False}
    period_ms = 1000.0 / f_pk
    return period_ms, {
        "estimator": "pooled_vertical_amplitude_spectrum_peak",
        "available": True,
        "peak_frequency_hz": _round(f_pk, 4),
        "period_ms": _round(period_ms, 4),
        "n_samples": int(n_s),
    }


# ── Constrained DTW (numpy only, deterministic) ──────────────────────────────


def _constrained_dtw(a: np.ndarray, b: np.ndarray, band: int) -> dict[str, Any]:
    """Sakoe-Chiba-banded DTW, diagonal-preferred tie-break. Deterministic.

    Returns the path, the accumulated cost and whether the path rides the band
    edge (censored = the optimum wanted more warp than the slop constraint allows).
    """
    n, m = int(a.size), int(b.size)
    if n < _DTW_MIN_WINDOW or m < _DTW_MIN_WINDOW:
        return {"path": [], "total_cost": None, "censored": True, "reachable": False, "band": int(band)}
    band = int(max(1, min(band, max(n, m))))
    inf = float("inf")
    cost = (a[:, None] - b[None, :]) ** 2
    D = np.full((n, m), inf, dtype=np.float64)
    bp = np.zeros((n, m), dtype=np.int8)  # 0=start, 1=diag, 2=up, 3=left
    for i in range(n):
        lo = max(0, i - band)
        hi = min(m - 1, i + band)
        for j in range(lo, hi + 1):
            c = float(cost[i, j])
            if i == 0 and j == 0:
                D[i, j] = c
                bp[i, j] = 0
                continue
            best = inf
            step = 0
            if i > 0 and j > 0 and D[i - 1, j - 1] < best:
                best = D[i - 1, j - 1]
                step = 1
            if i > 0 and D[i - 1, j] < best:
                best = D[i - 1, j]
                step = 2
            if j > 0 and D[i, j - 1] < best:
                best = D[i, j - 1]
                step = 3
            if step == 0:
                continue
            D[i, j] = c + best
            bp[i, j] = step
    if not np.isfinite(D[n - 1, m - 1]):
        return {"path": [], "total_cost": None, "censored": True, "reachable": False, "band": band}
    path: list[tuple[int, int]] = []
    i, j = n - 1, m - 1
    while True:
        path.append((i, j))
        if i == 0 and j == 0:
            break
        s = int(bp[i, j])
        if s == 1:
            i -= 1
            j -= 1
        elif s == 2:
            i -= 1
        elif s == 3:
            j -= 1
        else:  # pragma: no cover - defensive
            break
    path.reverse()
    band_binds = band < (min(n, m) - 1)
    edge_hits = sum(1 for (pi, pj) in path if abs(pi - pj) >= band)
    return {
        "path": path,
        "total_cost": float(D[n - 1, m - 1]),
        "censored": bool(band_binds and edge_hits > 0),
        "reachable": True,
        "band": band,
        "band_binds": bool(band_binds),
        "edge_hits": int(edge_hits),
    }


def _chord_ratio(path: Sequence[tuple[int, int]], i0: int, i1: int) -> float | None:
    """Local stretch of the alignment measured as the chord over the interval.

    A warp path is a CORRELATION artifact. The chord d(j)/d(i) across the picked
    interval is the warp-implied stretch factor for that interval — used only as a
    cross-check against the pick-derived thickness ratio.
    """
    if len(path) < 3 or i1 <= i0:
        return None
    pi = np.asarray([p[0] for p in path], dtype=np.float64)
    pj = np.asarray([p[1] for p in path], dtype=np.float64)
    jmax = np.full(int(pi.max()) + 1, -np.inf, dtype=np.float64)
    np.maximum.at(jmax, pi.astype(np.int64), pj)
    ok = np.isfinite(jmax)
    if int(ok.sum()) < 2:
        return None
    xs = np.arange(jmax.size, dtype=np.float64)
    j0 = float(np.interp(float(i0), xs[ok], jmax[ok]))
    j1 = float(np.interp(float(i1), xs[ok], jmax[ok]))
    return (j1 - j0) / float(i1 - i0)


# ── Instantaneous phase of the bounding events (lateral phase screen) ────────


def _reference_event_phase_deg(amp: np.ndarray, zu: np.ndarray, guard: int, min_rel_env: float = 0.2) -> np.ndarray:
    """Instantaneous phase (deg) of the strongest reference event ABOVE the interval.

    The event is taken at the envelope maximum of the whole overburden window
    ``[0, upper_pick - guard]``, so the interval's own tuning/interference cannot
    move the measurement (a guard band keeps clear of the upper pick's wavelet).
    A wavelet phase rotation rotates this phase; a lateral thickness change inside
    the interval does not. Traces whose reference event is too weak
    (envelope < ``min_rel_env`` x the section median) return NaN and are excluded,
    rather than contributing a phase read taken from noise.
    """
    from scipy.signal import hilbert

    n_s, n_t = amp.shape
    x = amp - np.mean(amp, axis=0, keepdims=True)
    analytic = hilbert(x, axis=0)
    env = np.abs(analytic)
    ph = np.angle(analytic)
    med_env = float(np.median(env)) if env.size else 0.0
    out = np.full(n_t, np.nan, dtype=np.float64)
    for t in range(n_t):
        z = zu[t]
        if not np.isfinite(z):
            continue
        hi = int(round(float(z))) - int(guard) - 1
        lo = 0
        if hi - lo < 2:
            continue
        k = lo + int(np.argmax(env[lo : hi + 1, t]))
        if med_env > 0 and float(env[k, t]) < float(min_rel_env) * med_env:
            continue
        val = float(ph[k, t])
        if np.isfinite(val):
            out[t] = float(np.rad2deg(val))
    return out


# ── Main entry point ─────────────────────────────────────────────────────────


def extract_expansion_index_candidate(
    amplitude: Any,
    horizon_upper: Any,
    horizon_lower: Any,
    *,
    domain: str = "TIME",
    target_domain: str | None = None,
    sample_interval_ms: float | None = None,
    sample_interval_m: float | None = None,
    trace_spacing_m: float | None = None,
    dominant_wavelength: float | None = None,
    velocity_model: dict[str, Any] | None = None,
    reference_traces: Sequence[int] | None = None,
    max_slop_fraction: float = _MAX_SLOP_FRACTION,
    dtw_window_pad_fraction: float = 0.35,
    phase_step_tol_deg: float = _PHASE_STEP_TOL_DEG,
    phase_drift_tol_deg: float = _PHASE_DRIFT_TOL_DEG,
    lateral_amplitude_tol_db: float = _LATERAL_AMP_TOL_DB,
    lateral_coherence_floor: float = _LATERAL_COHERENCE_FLOOR,
    warp_censored_fraction_tol: float = _WARP_CENSORED_FRACTION_TOL,
    warp_agreement_tol: float = _WARP_AGREEMENT_TOL_REL,
    warp_agreement_min_fraction: float = _WARP_AGREEMENT_MIN_FRACTION,
    min_coverage: float = _MIN_COVERAGE,
    min_valid_traces: int = _MIN_VALID_TRACES,
) -> dict[str, Any]:
    """Extract a CANDIDATE expansion index from one picked interval on a 2D section.

    Parameters
    ----------
    amplitude : 2D array (n_samples, n_traces)
        Seismic amplitude section. Used for QC (phase, lateral amplitude, lateral
        semblance, dominant period) and for the DTW cross-check.
    horizon_upper, horizon_lower : 1D array (n_traces,)
        Picked surfaces as per-trace sample indices (fractional allowed, NaN = gap).
    domain : {"TIME", "DEPTH"}
        Domain of the picks AND of the vertical sample interval. Must be declared.
    target_domain : {"TIME", "DEPTH", None}
        Domain in which an expansion index is requested. Defaults to `domain`.
        A DEPTH request requires a supplied `velocity_model`.
    sample_interval_ms / sample_interval_m
        Explicit vertical sample interval for the declared domain. Never inherited.
    trace_spacing_m : float
        Explicit lateral bin spacing. Never inherited.
    dominant_wavelength : float, optional
        Declared wavelet dominant wavelength in the vertical unit of `domain`
        (ms for TIME, m for DEPTH), e.g. from a source wavelet or a well tie. When
        omitted the wavelength is ESTIMATED from the pooled vertical spectrum and
        the estimator is named in the receipt.
    velocity_model : dict
        ``{"interval_v_m_s": float}`` or ``{"interval_v_m_s_by_trace": [...]}``
        (+ optional "velocity_model_id"). Required for any DEPTH-domain EI.
    reference_traces : sequence of int, optional
        Trace indices defining the reference (footwall-side) window. Supplying it
        upgrades the EI from a section-median isochore ratio to a Thorsen-style
        hanging-wall/reference ratio. Without it the reference basis is the section
        median and is named as such in the receipt.

    Returns
    -------
    dict
        A K-EI gate receipt: status, equation, thresholds, calculated_result
        (candidate, domain, QC verdict + checks), exceptions_considered,
        evidence_refs, missing_inputs, receipt_hash, plus a `claims_handoff` block
        for the K-GROWTH / K-EXT-GROWTH consumers.

    Status vocabulary used here: PASS | WARN | PARTIALLY_MEASURED | UNMEASURED.
    KILL is never emitted — see the falsifier-direction doctrine in the module
    docstring.
    """
    th = _effective_thresholds(
        max_slop_fraction_per_trace_step=max_slop_fraction,
        phase_step_tol_deg=phase_step_tol_deg,
        phase_drift_tol_deg=phase_drift_tol_deg,
        lateral_amplitude_tol_db=lateral_amplitude_tol_db,
        lateral_coherence_floor=lateral_coherence_floor,
        warp_censored_fraction_tol=warp_censored_fraction_tol,
        warp_agreement_tol_relative=warp_agreement_tol,
        min_coverage=min_coverage,
        min_valid_traces=min_valid_traces,
    )

    # ── 0. Domain declaration (never inferred from the data) ─────────────────
    dom = str(domain or "").strip().upper()
    if dom not in ("TIME", "DEPTH"):
        return _unmeasured(
            "Domain not declared as TIME or DEPTH. Thickness measured in time is not thickness "
            "in depth; this extractor refuses to guess which one the picks live in.",
            missing=["domain (TIME|DEPTH)"],
            inputs={"domain": domain},
            thresholds=th,
            input_domain=dom or None,
            target_domain=str(target_domain) if target_domain else None,
        )
    tdom = str(target_domain).strip().upper() if target_domain else dom
    if tdom not in ("TIME", "DEPTH"):
        return _unmeasured(
            f"target_domain={target_domain!r} is not TIME or DEPTH.",
            missing=["target_domain (TIME|DEPTH)"],
            inputs={"domain": dom, "target_domain": target_domain},
            thresholds=th,
            input_domain=dom,
            target_domain=tdom,
        )

    # ── 1. Presence of every required input (all missing named at once) ───────
    missing: list[str] = []
    amp = None
    if amplitude is None:
        missing.append("amplitude")
    else:
        try:
            amp = np.asarray(amplitude, dtype=np.float64)
        except (TypeError, ValueError):
            missing.append("amplitude (2D numeric array)")
        else:
            if amp.ndim != 2 or amp.size == 0:
                missing.append("amplitude (2D numeric array)")
                amp = None

    up = None
    if horizon_upper is None:
        missing.append("horizon_upper")
    else:
        up = _as_series(horizon_upper)
        if up is None:
            missing.append("horizon_upper (1D per-trace pick series)")
    lo_pick = None
    if horizon_lower is None:
        missing.append("horizon_lower")
    else:
        lo_pick = _as_series(horizon_lower)
        if lo_pick is None:
            missing.append("horizon_lower (1D per-trace pick series)")

    if dom == "TIME":
        if sample_interval_ms is None:
            missing.append("sample_interval_ms")
    else:
        if sample_interval_m is None:
            missing.append("sample_interval_m")
    if trace_spacing_m is None:
        missing.append("trace_spacing_m")

    vvals, vnote = _resolve_velocity(velocity_model)
    needs_velocity = tdom == "DEPTH" or dom == "DEPTH"
    if needs_velocity and vvals is None:
        missing.append("velocity_model")

    if missing:
        return _unmeasured(
            "Required input(s) absent: " + ", ".join(missing) + ". No expansion index is emitted — "
            "a coordinate cannot be measured from a missing surface, and a DEPTH-domain EI cannot be "
            "declared without the velocity model that defines the depth axis.",
            missing=missing,
            inputs={
                "domain": dom,
                "target_domain": tdom,
                "amplitude_provided": amplitude is not None,
                "horizon_upper_provided": horizon_upper is not None,
                "horizon_lower_provided": horizon_lower is not None,
                "sample_interval_ms": sample_interval_ms,
                "sample_interval_m": sample_interval_m,
                "trace_spacing_m": trace_spacing_m,
                "velocity_model_provided": velocity_model is not None,
            },
            thresholds=th,
            input_domain=dom,
            target_domain=tdom,
        )

    # ── 2. Shape consistency (never silently transpose or pad) ───────────────
    assert amp is not None and up is not None and lo_pick is not None
    n_samples, n_traces = int(amp.shape[0]), int(amp.shape[1])
    if up.size != n_traces or lo_pick.size != n_traces:
        return _unmeasured(
            f"Surface/amplitude axis mismatch: amplitude {amp.shape} (n_traces={n_traces}) but "
            f"horizon_upper has {up.size} samples and horizon_lower has {lo_pick.size}. Refusing to "
            "transpose or pad silently — align the picks to the trace axis first.",
            missing=["horizon_upper/horizon_lower aligned to the amplitude trace axis"],
            inputs={"amplitude_shape": [n_samples, n_traces], "n_upper": int(up.size), "n_lower": int(lo_pick.size)},
            thresholds=th,
            input_domain=dom,
            target_domain=tdom,
        )

    dt = float(sample_interval_ms if dom == "TIME" else sample_interval_m)  # vertical unit per sample
    if not np.isfinite(dt) or dt <= 0:
        return _unmeasured(
            f"sample interval for domain {dom} must be a positive finite number (got {dt}).",
            missing=["sample_interval_ms" if dom == "TIME" else "sample_interval_m"],
            thresholds=th,
            input_domain=dom,
            target_domain=tdom,
        )
    dx = float(trace_spacing_m)
    if not np.isfinite(dx) or dx <= 0:
        return _unmeasured(
            f"trace_spacing_m must be a positive finite number (got {trace_spacing_m}).",
            missing=["trace_spacing_m"],
            thresholds=th,
            input_domain=dom,
            target_domain=tdom,
        )

    v_per_trace: np.ndarray | None = None
    if needs_velocity and vvals is not None:
        if vvals.ndim == 1:
            if vvals.size != n_traces:
                return _unmeasured(
                    f"velocity_model per-trace length {vvals.size} does not match n_traces={n_traces}.",
                    missing=["velocity_model (per-trace velocity length does not match the trace axis)"],
                    thresholds=th,
                    input_domain=dom,
                    target_domain=tdom,
                )
            v_per_trace = vvals
        else:
            v_per_trace = np.full(n_traces, float(vvals), dtype=np.float64)

    amp_sha = artifact_sha256(amp)
    up_sha = artifact_sha256(up)
    lo_sha = artifact_sha256(lo_pick)

    base_inputs = {
        "domain": dom,
        "target_domain": tdom,
        "sample_interval_%s" % ("ms" if dom == "TIME" else "m"): _round(dt),
        "trace_spacing_m": _round(dx),
        "amplitude_shape": [n_samples, n_traces],
        "artifact_sha256_amplitude": amp_sha,
        "artifact_sha256_horizon_upper": up_sha,
        "artifact_sha256_horizon_lower": lo_sha,
        "velocity_model": vnote,
    }

    # ── 3. Per-trace thickness, validity, coverage ───────────────────────────
    thickness = (lo_pick - up) * dt  # in the declared vertical unit
    finite_amp = np.all(np.isfinite(amp), axis=0)
    valid = np.isfinite(thickness) & (thickness > 0) & np.isfinite(up) & np.isfinite(lo_pick) & finite_amp
    n_valid = int(np.count_nonzero(valid))
    coverage = float(n_valid) / float(n_traces) if n_traces else 0.0

    if n_valid < int(min_valid_traces) or coverage < float(min_coverage):
        return _unmeasured(
            f"Interval coverage too low to measure a lateral ratio: {n_valid}/{n_traces} valid traces "
            f"(coverage={coverage:.3f}, min_valid_traces={min_valid_traces}, min_coverage={min_coverage}). "
            "A lateral expansion index needs lateral control.",
            missing=["horizon coverage along the interval (valid picks inside the amplitude section)"],
            inputs={**base_inputs, "n_valid_traces": n_valid, "coverage": _round(coverage, 4)},
            thresholds=th,
            coverage=_round(coverage, 4),
            result_extra={"n_valid_traces": n_valid, "n_traces": n_traces},
            input_domain=dom,
            target_domain=tdom,
        )

    # ── 4. Tuning / resolvability screen (lambda/4 risk, lambda/8 floor) ─────
    lam: float | None = None
    lam_units: str | None = None
    lam_source = ""
    declared_lam: float | None = None
    if dominant_wavelength is not None:
        try:
            declared_lam = float(dominant_wavelength)
        except (TypeError, ValueError):
            declared_lam = None
        if declared_lam is not None and (not np.isfinite(declared_lam) or declared_lam <= 0):
            declared_lam = None
    if dom == "TIME":
        lam_units = "ms"
        if declared_lam is not None:
            lam = declared_lam
            lam_source = "declared by caller (source wavelet / well tie) — never inferred"
            period_meta: dict[str, Any] = {
                "estimator": "declared",
                "available": True,
                "lambda_definition": "lambda_time as supplied (ms, two-way time)",
            }
        else:
            period_ms, period_meta = _dominant_period(amp, valid, dt)
            lam = period_ms
            lam_source = "estimated from the pooled Hann-windowed vertical spectrum (peak frequency)"
            period_meta = {**period_meta, "lambda_definition": "lambda_time = 1 / f_peak (two-way time)"}
    else:
        lam_units = "m"
        if declared_lam is not None:
            lam = declared_lam
            lam_source = "declared by caller (source wavelet / well tie) — never inferred"
            period_meta = {
                "estimator": "declared",
                "available": True,
                "lambda_definition": "lambda_depth as supplied (m per cycle)",
            }
        else:
            k_dom = _dominant_vertical_wavenumber(amp, valid, dt)
            lam = (1.0 / k_dom) if k_dom else None
            lam_source = "estimated from the pooled vertical wavenumber peak of the depth section"
            period_meta = {
                "estimator": "pooled_vertical_wavenumber_peak (depth section — no time sampling available)",
                "available": k_dom is not None,
                "wavenumber_per_m": _round(k_dom, 8),
                "lambda_definition": "lambda_depth = 1 / k_peak (metres per cycle)",
            }

    t_med = float(np.median(thickness[valid]))
    tuning_ratio = (t_med / lam) if (lam and lam > 0) else None

    tuning_check: dict[str, Any] = {
        "name": "tuning_resolution",
        "measured": {
            "median_interval_thickness": _round(t_med),
            "thickness_units": lam_units or ("ms" if dom == "TIME" else "m"),
            "dominant_wavelength": _round(lam),
            "wavelength_source": lam_source or "not available",
            "thickness_over_lambda": _round(tuning_ratio, 4),
        },
        "threshold": {"lambda4_tuning": _LAMBDA4_TUNING_FRACTION, "lambda8_floor": _LAMBDA8_FLOOR_FRACTION},
        "estimator": period_meta,
        "verdict": "NOT_EVALUATED",
        "note": "",
    }

    if tuning_ratio is None:
        # No wavelength available (e.g. DEPTH without a usable wavenumber). The EI
        # can still be a valid geometric ratio, but the resolvability screen is
        # NOT_EVALUATED and the receipt says so instead of implying it passed.
        tuning_check["verdict"] = "NOT_EVALUATED"
        tuning_check["note"] = (
            "Dominant vertical wavelength could not be estimated for this domain — the "
            "tuning/resolvability screen is NOT_EVALUATED, not passed."
        )
    elif tuning_ratio < _LAMBDA8_FLOOR_FRACTION:
        tuning_check["verdict"] = "FAIL"
        tuning_check["note"] = (
            f"median interval thickness {t_med:.4g} is {tuning_ratio:.4f} of the dominant "
            f"wavelength — below the Widess lambda/8 absolute floor. The beds are not resolvable, "
            "so any lateral thickness change measured across them is a tuning artifact."
        )
        return _unmeasured(
            "Interval thickness is below the lambda/8 absolute resolvability floor — no expansion "
            "index is emitted (an unresolvable interval cannot carry a thickness ratio).",
            missing=["vertical resolution: interval thicker than lambda/8"],
            inputs={**base_inputs, "median_interval_thickness": _round(t_med), "dominant_wavelength": _round(lam)},
            thresholds=th,
            coverage=_round(coverage, 4),
            result_extra={
                "n_valid_traces": n_valid,
                "n_traces": n_traces,
                "resolution": {"median_interval_thickness": _round(t_med), "dominant_wavelength": _round(lam),
                               "thickness_over_lambda": _round(tuning_ratio, 4), "units": lam_units},
                "qc": {"verdict": "UNMEASURED", "checks": [tuning_check], "contamination_flags": [],
                       "limitations": _LIMITATIONS},
                "withheld": {"expansion_index": "withheld_below_lambda_8_absolute_floor"},
            },
            input_domain=dom,
            target_domain=tdom,
        )
    elif tuning_ratio < _LAMBDA4_TUNING_FRACTION:
        tuning_check["verdict"] = "CAVEAT"
        tuning_check["note"] = (
            f"median interval thickness is {tuning_ratio:.4f} of the dominant wavelength — above the "
            "lambda/8 floor but below the lambda/4 tuning limit, so the interval is only partially "
            "resolved and its apparent thickness is biased by tuning."
        )
    else:
        tuning_check["verdict"] = "PASS"
        tuning_check["note"] = (
            f"median interval thickness is {tuning_ratio:.4f} of the dominant wavelength — above the "
            "lambda/4 tuning limit."
        )

    # ── 5. Reference thickness and the EI series ─────────────────────────────
    idx = np.arange(n_traces, dtype=np.float64)
    gap_filled = np.interp(idx, idx[valid], thickness[valid])  # smoothing device only
    from scipy.ndimage import median_filter

    t_smooth = median_filter(gap_filled, size=3, mode="nearest")

    ref_basis: str
    if reference_traces is not None:
        ref_idx = np.asarray(list(reference_traces), dtype=int)
        ref_idx = ref_idx[(ref_idx >= 0) & (ref_idx < n_traces)]
        ref_sel = np.zeros(n_traces, dtype=bool)
        ref_sel[ref_idx] = True
        ref_sel &= valid
        if int(np.count_nonzero(ref_sel)) < 2:
            return _unmeasured(
                "reference_traces did not select at least 2 valid traces — cannot form a reference "
                "thickness for a hanging-wall/reference ratio. Omit reference_traces to use the "
                "declared section-median reference instead.",
                missing=["reference_traces (>=2 valid trace indices defining the reference window)"],
                inputs={**base_inputs, "reference_traces": list(map(int, ref_idx))},
                thresholds=th,
                coverage=_round(coverage, 4),
                input_domain=dom,
                target_domain=tdom,
            )
        t_ref = float(np.median(t_smooth[ref_sel]))
        ref_basis = "median_thickness_over_supplied_reference_window (Thorsen-style HW/reference ratio)"
    else:
        t_ref = float(np.median(t_smooth[valid]))
        ref_basis = (
            "median_thickness_over_all_valid_traces (section-median isochore ratio, NOT a fault-side "
            "footwall measurement — supply reference_traces for a Thorsen-style HW/FW ratio)"
        )

    if not np.isfinite(t_ref) or t_ref <= 0:
        return _unmeasured(
            "Reference thickness is non-positive — the interval pinches out over the whole valid "
            "window, which is a pick/interval definition failure, not an expansion index.",
            missing=["a positive reference thickness (check the interval definition)"],
            inputs={**base_inputs, "reference_thickness": _round(t_ref)},
            thresholds=th,
            coverage=_round(coverage, 4),
            input_domain=dom,
            target_domain=tdom,
        )

    ei_series = np.where(valid, t_smooth / t_ref, np.nan)

    # Domain handling for the emitted EI.
    input_thickness = t_smooth.copy()
    units = ("ms of two-way time" if dom == "TIME" else "m")
    emitted_domain = dom
    conversion: dict[str, Any] = {"applied": False, "reason": "EMITTED IN THE INPUT DOMAIN"}
    if tdom == "DEPTH":
        assert v_per_trace is not None  # guaranteed by the velocity gate
        if dom == "TIME":
            depth_series = (t_smooth / 1000.0) * v_per_trace / 2.0  # two-way time -> thickness
            ref_depth = (t_ref / 1000.0) * float(np.median(v_per_trace[valid])) / 2.0
            conversion = {
                "applied": True,
                "input_domain": "TIME",
                "output_domain": "DEPTH",
                "equation": "h = V * t_two_way / 2",
                "velocity_model": vnote,
                "constant_velocity_invariance": bool(v_per_trace is not None and np.allclose(v_per_trace, v_per_trace[0])),
                "note": (
                    "With a single constant V the EI RATIO is invariant (identical to the TIME EI); only a "
                    "laterally varying V(t,x) changes it. The depth thickness changes; the ratio does not."
                ),
            }
            input_thickness = depth_series
            t_ref = ref_depth
            units = "m"
            emitted_domain = "DEPTH"
            ei_series = np.where(valid, depth_series / t_ref, np.nan)
        else:
            conversion = {
                "applied": False,
                "input_domain": "DEPTH",
                "output_domain": "DEPTH",
                "velocity_model": vnote,
                "note": (
                    "Picks already in depth; the declared velocity model is required only to establish "
                    "the provenance of the depth axis, not to convert the picks."
                ),
            }

    ei_valid = ei_series[valid]
    ei_max = float(np.max(ei_valid)) if ei_valid.size else None
    ei_min = float(np.min(ei_valid)) if ei_valid.size else None
    ei_p50 = float(np.median(ei_valid)) if ei_valid.size else None
    ei_candidate = ei_max  # strongest lateral expansion found — a CANDIDATE

    # ── 6. Constrained DTW cross-check (slop-bounded, correlation-only) ──────
    zu = up.copy()
    zl = lo_pick.copy()
    pad = int(max(2, round(dtw_window_pad_fraction * float(np.median((zl - zu)[valid])))))
    slop_samples = float(max_slop_fraction) * float(np.median((zl - zu)[valid]))

    pair_list = [x for x in range(n_traces - 1) if valid[x] and valid[x + 1]]
    n_pairs_total = len(pair_list)
    if n_pairs_total > _MAX_DTW_PAIRS:
        step = int(np.ceil(n_pairs_total / _MAX_DTW_PAIRS))
        pair_list = pair_list[::step]
    n_sampled = len(pair_list)

    implied: list[float] = []
    pick_ratios: list[float] = []
    n_censored = 0
    n_slop_rejected = 0
    n_agree = 0
    n_compared = 0
    for x in pair_list:
        z0 = int(max(0, int(np.floor(zu[x])) - pad))
        z1 = int(min(n_samples - 1, int(np.ceil(zl[x])) + pad))
        if z1 - z0 + 1 < _DTW_MIN_WINDOW:
            continue
        a = amp[z0 : z1 + 1, x].astype(np.float64)
        b = amp[z0 : z1 + 1, x + 1].astype(np.float64)
        a = _zscore(a)
        b = _zscore(b)
        structural_shift = abs(float(zu[x + 1] - zu[x]))
        band = int(np.ceil(structural_shift + slop_samples))
        res = _constrained_dtw(a, b, band)
        if not res["reachable"]:
            n_censored += 1
            continue
        if res["censored"]:
            n_censored += 1
            continue
        ia0 = int(round(float(zu[x]))) - z0
        ia1 = int(round(float(zl[x]))) - z0
        chord = _chord_ratio(res["path"], ia0, ia1)
        if chord is None:
            continue
        t_a = float(zl[x] - zu[x])
        if t_a <= 0:
            continue
        # (a) explicit slop constraint on the RESULT, not just the DP band
        if abs(chord * t_a - t_a) > slop_samples:
            n_slop_rejected += 1
            continue
        pr = float((zl[x + 1] - zu[x + 1]) / t_a)
        implied.append(float(chord))
        pick_ratios.append(pr)
        n_compared += 1
        if pr > 0 and abs(chord - pr) <= float(warp_agreement_tol) * pr:
            n_agree += 1

    n_pairs_used = n_sampled
    censored_fraction = (n_censored / n_pairs_used) if n_pairs_used else None
    slop_rejected_fraction = (n_slop_rejected / n_pairs_used) if n_pairs_used else None
    agreement_fraction = (n_agree / n_compared) if n_compared else None
    warp = {
        "available": bool(n_compared > 0),
        "n_pairs_total": n_pairs_total,
        "n_pairs_sampled": n_sampled,
        "n_pairs_compared": n_compared,
        "n_censored_by_band": n_censored,
        "n_rejected_by_slop": n_slop_rejected,
        "censored_fraction": _round(censored_fraction, 4),
        "slop_rejected_fraction": _round(slop_rejected_fraction, 4),
        "implied_ratio_median": _round(float(np.median(implied)), 4) if implied else None,
        "pick_ratio_median": _round(float(np.median(pick_ratios)), 4) if pick_ratios else None,
        "agreement_fraction": _round(agreement_fraction, 4),
        "band_definition": (
            "band_samples = ceil(|structural_shift_per_trace_from_picks| + max_slop_fraction * "
            "median_interval_thickness_in_samples)"
        ),
        "slop_constraint_samples": _round(slop_samples, 3),
        "note": (
            "A DTW warp path is a CORRELATION artifact, not a thickness measurement. It is used here "
            "only as a slop-bounded consistency cross-check on the pick-derived ratio, and its value "
            "is never emitted as the expansion index."
        ),
    }

    # ── 7. QC screens: phase, lateral amplitude, lateral coherence, warp ─────
    checks: list[dict[str, Any]] = [tuning_check]
    flags: list[str] = []
    if tuning_check["verdict"] == "CAVEAT":
        flags.append("tuning_risk_below_lambda4")

    # 7a. Wavelet phase rotation (lateral instantaneous-phase behaviour of the
    #     reference event above the interval — deliberately NOT the interval event,
    #     whose apparent phase legitimately moves when the interval thickens)
    phase_guard = int(max(3, round(0.5 * float(np.median((zl - zu)[valid])))))
    ph = _reference_event_phase_deg(amp, zu, phase_guard)
    ph_ok = valid & np.isfinite(ph)
    phase_step = None
    phase_drift = None
    if int(np.count_nonzero(ph_ok)) >= max(4, int(min_valid_traces)):
        p = ph[ph_ok]
        diffs = [abs(_circ_diff_deg(float(p[i + 1]), float(p[i]))) for i in range(p.size - 1)]
        phase_step = float(np.median(diffs)) if diffs else None
        q = max(1, p.size // 4)
        early = _circ_mean_deg(p[:q])
        late = _circ_mean_deg(p[-q:])
        phase_drift = abs(_circ_diff_deg(late, early)) if (early is not None and late is not None) else None
    if phase_step is not None and phase_step > float(phase_step_tol_deg):
        flags.append("wavelet_phase_rotation:lateral_step")
    if phase_drift is not None and phase_drift > float(phase_drift_tol_deg):
        flags.append("wavelet_phase_rotation:lateral_drift")
    phase_verdict = (
        "NOT_EVALUATED"
        if phase_step is None and phase_drift is None
        else ("PASS" if not any(f.startswith("wavelet_phase_rotation") for f in flags) else "CONTAMINATED")
    )
    checks.append(
        {
            "name": "wavelet_phase_rotation",
            "measured": {"median_adjacent_trace_phase_step_deg": _round(phase_step, 3),
                         "end_to_end_phase_drift_deg": _round(phase_drift, 3),
                         "n_traces_measured": int(np.count_nonzero(ph_ok)),
                         "search_window_samples_above_upper_pick": phase_guard},
            "threshold": {"step_tol_deg": float(phase_step_tol_deg), "drift_tol_deg": float(phase_drift_tol_deg)},
            "verdict": phase_verdict,
            "note": (
                "Lateral instantaneous-phase behaviour of the strongest reference event ABOVE the "
                "interval: a laterally varying wavelet phase rotation drifts it, while a genuine "
                "lateral thickness change inside the interval does not. A section-wide uniform "
                "rotation is NOT detectable from the data alone (well-tie required)."
            ),
        }
    )

    # 7b. Lateral amplitude change inside the interval
    rms = np.full(n_traces, np.nan)
    for x in range(n_traces):
        if not valid[x]:
            continue
        zz0 = int(max(0, int(np.floor(zu[x]))))
        zz1 = int(min(n_samples - 1, int(np.ceil(zl[x]))))
        if zz1 <= zz0:
            continue
        seg = amp[zz0 : zz1 + 1, x]
        r = float(np.sqrt(np.mean(seg**2)))
        rms[x] = r
    amp_db: list[float] = []
    for x in pair_list:
        if np.isfinite(rms[x]) and np.isfinite(rms[x + 1]) and rms[x] > 0 and rms[x + 1] > 0:
            amp_db.append(abs(20.0 * np.log10(rms[x + 1] / rms[x])))
    amp_db_med = float(np.median(amp_db)) if amp_db else None
    amp_db_max = float(np.max(amp_db)) if amp_db else None
    if amp_db_med is not None and amp_db_max is not None:
        if amp_db_med > float(lateral_amplitude_tol_db) or amp_db_max > 3.0 * float(lateral_amplitude_tol_db):
            flags.append("lateral_amplitude_change")
    checks.append(
        {
            "name": "lateral_amplitude_change",
            "measured": {"median_adjacent_trace_rms_change_db": _round(amp_db_med, 3),
                         "max_adjacent_trace_rms_change_db": _round(amp_db_max, 3)},
            "threshold": {"median_tol_db": float(lateral_amplitude_tol_db), "max_tol_db": 3.0 * float(lateral_amplitude_tol_db)},
            "verdict": "PASS" if "lateral_amplitude_change" not in flags else "CONTAMINATED",
            "note": (
                "Large lateral amplitude change (AGC / acquisition footprint / focusing) makes a "
                "sample-to-sample correspondence amplitude-weighted and unreliable."
            ),
        }
    )

    # 7c. Lateral continuity of the interval waveform (primitive reuse: lateral semblance)
    coh_median = None
    coh_note = ""
    try:
        # semblance_coherence windows along axis 0, so transpose to measure LATERAL continuity
        with np.errstate(divide="ignore", invalid="ignore"):
            coh_map = semblance_coherence(amp.T, window=5).T
        vals = []
        for x in range(n_traces):
            if not valid[x]:
                continue
            zz0 = int(max(0, int(np.floor(zu[x]))))
            zz1 = int(min(n_samples - 1, int(np.ceil(zl[x]))))
            if zz1 > zz0:
                vals.append(float(np.median(coh_map[zz0 : zz1 + 1, x])))
        if vals:
            coh_median = float(np.median(vals))
    except Exception as exc:  # pragma: no cover - defensive
        coh_note = f"lateral semblance not evaluable: {type(exc).__name__}"
    if coh_median is not None and coh_median < float(lateral_coherence_floor):
        flags.append("low_lateral_coherence")
    checks.append(
        {
            "name": "lateral_coherence",
            "measured": {"median_interval_lateral_semblance": _round(coh_median, 4)},
            "threshold": {"floor": float(lateral_coherence_floor)},
            "verdict": ("NOT_EVALUATED" if coh_median is None else ("PASS" if "low_lateral_coherence" not in flags else "CONTAMINATED")),
            "note": coh_note
            or (
                "Lateral semblance across a 5-trace window inside the interval (semblance_coherence "
                "applied along the trace axis). Low continuity means the trace-to-trace correspondence "
                "is tracking noise."
            ),
        }
    )

    # 7d. Slop censoring / slop rejection of the warp paths
    if censored_fraction is not None and censored_fraction > float(warp_censored_fraction_tol):
        flags.append("dtw_warp_censored_by_band")
    if slop_rejected_fraction is not None and slop_rejected_fraction > float(warp_censored_fraction_tol):
        flags.append("dtw_warp_exceeds_slop_constraint")
    checks.append(
        {
            "name": "dtw_slop_constraint",
            "measured": {
                "censored_fraction": _round(censored_fraction, 4),
                "slop_rejected_fraction": _round(slop_rejected_fraction, 4),
                "n_pairs_total": n_pairs_total,
                "n_pairs_sampled": n_sampled,
            },
            "threshold": {"censored_fraction_tol": float(warp_censored_fraction_tol), "max_slop_fraction": float(max_slop_fraction)},
            "verdict": (
                "PASS"
                if not any(f.startswith("dtw_warp_") for f in flags)
                else "CONTAMINATED"
            ),
            "note": (
                "Warp paths that ride the band edge (or whose chord exceeds the maximum plausible "
                "per-trace thickness change) are censored/rejected: the optimum wanted more warp than "
                "geology allows, so that correspondence is unconstrained, not informative."
            ),
        }
    )

    # 7e. Pick-vs-correlation agreement
    if agreement_fraction is not None and agreement_fraction < float(warp_agreement_min_fraction):
        flags.append("pick_correlation_conflict")
    checks.append(
        {
            "name": "pick_correlation_consistency",
            "measured": {"agreement_fraction": _round(agreement_fraction, 4), "n_pairs_compared": n_compared},
            "threshold": {"relative_tol": float(warp_agreement_tol), "min_fraction": float(warp_agreement_min_fraction)},
            "verdict": "NOT_EVALUATED" if agreement_fraction is None else ("PASS" if "pick_correlation_conflict" not in flags else "CONTAMINATED"),
            "note": (
                "Fraction of adjacent-trace pairs where the slop-constrained warp-implied stretch agrees "
                "with the pick-derived thickness ratio within tolerance. Disagreement means either the "
                "picks or the correlation are wrong — the extractor will not arbitrate silently."
            ),
        }
    )

    # ── 8. Independent structural context (primitive reuse, informational) ───
    structural: dict[str, Any] = {"informational_only": True}
    try:
        with np.errstate(divide="ignore", invalid="ignore"):
            tens = structure_tensor(amp, sigma=1.0)
        m_pix = np.tan(tens["dip_rad"])
        pick_shift = np.abs(np.diff(zu))
        pick_shift_ok = pick_shift[np.isfinite(pick_shift)]
        m_sel = m_pix[:, valid]
        structural = {
            "informational_only": True,
            "attribute_apparent_dip_median_pixels_per_trace": _round(float(np.median(np.abs(m_sel))), 5) if m_sel.size else None,
            "pick_structural_shift_median_samples_per_trace": _round(float(np.median(pick_shift_ok)), 5) if pick_shift_ok.size else None,
            "note": (
                "structure_tensor gives an amplitude-derived apparent dip (pixels/trace) independent of "
                "the picks. Reported as context only — it is not a gate here and never modifies the EI."
            ),
        }
    except Exception as exc:  # pragma: no cover - defensive
        structural["note"] = f"structure_tensor not evaluable: {type(exc).__name__}"

    # ── 9. QC verdict → gate status ──────────────────────────────────────────
    qc_verdict = "CLEAN" if not flags else ("CAVEATED" if len(flags) == 1 else "CONTAMINATED")
    status = {"CLEAN": "PASS", "CAVEATED": "WARN", "CONTAMINATED": "PARTIALLY_MEASURED"}[qc_verdict]

    confidence_note = (
        "No confidence/probability is emitted. A confidence field would require a named, versioned, "
        "validated benchmark receipt; none is attached, so it stays None."
    )
    falsifier_available = bool(ei_max is not None and ei_max <= 1.0)
    calculated_result = {
        "expansion_index_candidate": _round(ei_candidate, 4),
        "expansion_index_domain": emitted_domain,
        "expansion_index_units": "dimensionless ratio of vertical thicknesses",
        "expansion_index_statistic": "max of the median-filtered per-trace EI series",
        "expansion_index_by_trace": [_round(v, 4) for v in ei_series.tolist()],
        "expansion_index_max": _round(ei_max, 4),
        "expansion_index_min": _round(ei_min, 4),
        "expansion_index_median": _round(ei_p50, 4),
        "thickness_units": units,
        "reference_thickness": _round(t_ref),
        "reference_basis": ref_basis,
        "domain_conversion": conversion,
        "sampling": {
            "vertical_sample_interval": _round(dt),
            "vertical_sample_interval_units": "ms (two-way time)" if dom == "TIME" else "m",
            "trace_spacing_m": _round(dx),
            "explicitly_supplied": True,
        },
        "structural_context": structural,
        "warp_crosscheck": warp,
        "qc_verdict": qc_verdict,
        "qc": {"verdict": qc_verdict, "checks": checks, "contamination_flags": flags, "limitations": _LIMITATIONS},
        "falsifier": {
            "direction": "CONTRADICTION" if falsifier_available else "NOT_AVAILABLE",
            "available": falsifier_available,
            "rule": (
                "A MEASURED expansion index <= 1 is contradiction evidence against a syn-tectonic growth "
                "claim for that interval. The ABSENCE of a detectable growth wedge is a DEFICIT, never a "
                "contradiction — sub-tuning growth is invisible and a fault moving slower than the "
                "sediment supply leaves no signature. This extractor therefore never returns KILL."
            ),
            "note": (
                "Available: every measured trace has EI <= 1, so a syn-tectonic claim for this interval "
                "is contradicted by measurement. Feed it to K-GROWTH/K-EXT-GROWTH as a measured EI."
                if falsifier_available
                else "Not available: at least one trace shows lateral expansion > 1 (or the section was "
                "not measurable). Absence of a wedge would still be UNMEASURED, not KILL."
            ),
        },
        "n_valid_traces": n_valid,
        "n_traces": n_traces,
        "coverage": _round(coverage, 4),
        "confidence": None,
        "confidence_note": confidence_note,
        "status_semantics": (
            "Status refers to EXTRACTION QUALITY (was a candidate measured with a clean QC), not to the "
            "geological verdict. PASS here does NOT imply syn-tectonic growth; it means the candidate "
            "was measured with no QC contamination flag."
        ),
    }

    findings = [
        {
            "verdict": status,
            "expansion_index_candidate": _round(ei_candidate, 4),
            "expansion_index_domain": emitted_domain,
            "qc_verdict": qc_verdict,
            "epistemic_tier": TIER_KINEMATIC,
        },
        {
            "verdict": "CANDIDATE_ONLY",
            "note": (
                "Candidate geometry for a growth claim. KINEMATIC tier — not strain (no restoration), "
                "not dynamics (no fault-slip inversion). GEOX proposes; arifOS seals."
            ),
        },
    ]
    if flags:
        findings.append({"verdict": "CONTAMINATION", "flags": list(flags)})

    return _receipt(
        GATE_ID,
        status,
        tier=TIER_KINEMATIC,
        coverage=_round(coverage, 4),
        reason=(
            f"Candidate EI={_round(ei_candidate, 4)} in {emitted_domain} domain from "
            f"{n_valid}/{n_traces} valid traces; QC verdict {qc_verdict}"
            + (f" (flags: {', '.join(flags)})" if flags else "")
        ),
        equation=_EQUATION,
        inputs={**base_inputs, "reference_traces": None if reference_traces is None else list(map(int, reference_traces))},
        thresholds=th,
        measurement_units="dimensionless (ratio of vertical thicknesses in the declared domain)",
        calculated_result=calculated_result,
        exceptions_considered=_EXCEPTIONS,
        evidence_refs=_EVIDENCE + [f"artifact_sha256(amplitude)={amp_sha}"],
        findings=findings,
        gate_type="soft_conditional",
        extras={
            "input_domain": dom,
            "expansion_index_domain": emitted_domain,
            "epistemic_caveat": (
                "KINEMATIC with QC caveat. A 2D-section isochore ratio is an observation about a "
                "picture; only calibrated, depth-converted geometry is an observation about rock. "
                "STRAIN requires restoration; DYNAMIC requires fault-slip inversion."
            ),
            "claims_handoff": {
                "expansion_index": _round(ei_candidate, 4) if status != "UNMEASURED" else None,
                "expansion_index_domain": emitted_domain,
                "qc_verdict": qc_verdict,
                "contamination_flags": list(flags),
                "source_gate": GATE_ID,
                "epistemic_tier": TIER_KINEMATIC,
                "trust": "QC_CLEAN" if qc_verdict == "CLEAN" else ("QC_CAVEATED" if qc_verdict == "CAVEATED" else "QC_CONTAMINATED"),
                "note": (
                    "Feed to claims.expansion_index (K-GROWTH / K-EXT-GROWTH) ONLY together with the QC "
                    "verdict and domain. Never the number alone."
                ),
            },
        },
    )


# ── Small internal utilities ─────────────────────────────────────────────────


def _zscore(v: np.ndarray) -> np.ndarray:
    """Zero-mean, unit-RMS — removes lateral amplitude change from the DTW cost."""
    m = float(np.mean(v))
    s = float(np.sqrt(np.mean((v - m) ** 2)))
    if s <= 1e-12:
        return v - m
    return (v - m) / s


def _dominant_vertical_wavenumber(amp: np.ndarray, valid: np.ndarray, dz: float) -> float | None:
    """Dominant vertical wavenumber (cycles per vertical unit) of the valid section."""
    n_s = amp.shape[0]
    sub = amp[:, valid]
    if sub.shape[1] == 0 or n_s < 8 or dz <= 0:
        return None
    sub = sub - np.mean(sub, axis=0, keepdims=True)
    win = np.hanning(n_s)[:, None]
    spec = np.abs(np.fft.rfft(sub * win, axis=0)).mean(axis=1)
    if spec.size < 3:
        return None
    k = int(np.argmax(spec[1:])) + 1
    freqs = np.fft.rfftfreq(n_s, d=dz)  # cycles per vertical unit (m)
    f_pk = float(freqs[k])
    return f_pk if f_pk > 0 else None


# Discoverable alias — Axis B is the isochore/expansion axis.
axis_b_isochore = extract_expansion_index_candidate

__all__ = [
    "GATE_ID",
    "TIER_KINEMATIC",
    "axis_b_isochore",
    "extract_expansion_index_candidate",
]
