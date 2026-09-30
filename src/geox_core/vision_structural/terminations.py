"""Axis D — Superposition: reflection terminations and cross-cutting chronology.

CONTRACT.md §4 (Axis D) — `detect_terminations`, `build_cross_cutting_table`.

Two principles live here, and they are NOT the same principle
-------------------------------------------------------------
1. **Stratigraphic superposition / cross-cutting** — *Steno 1669, Hutton 1795,
   Lyell 1830*: a feature is YOUNGER than the youngest horizon it offsets and OLDER
   than the oldest horizon that drapes it without offset. That is the relative
   chronology this module builds.
2. **Walther's Law** (Walther 1894) — conformable vertical facies succession implies
   laterally adjacent environments. It governs *facies* transitions, NOT cross-cutting
   relations.

Conflating the two is a known and repeated error in automated stratigraphic reasoning;
`K-REGIME-XCUT` in `tools/structure_gates/tectonic_regime.py` records the correction
explicitly. Nothing in this module tests Walther's Law.

A bare gradient edge is NOT a termination
-----------------------------------------
Seismic reflections are laterally continuous wavelets. An edge map lights up along
every reflector flank and along every acquisition footprint, so "there is a gradient
here" carries no stratigraphic information at all. A *termination* is a place where a
reflection STOPS. `detect_terminations` therefore requires, in order:

  1. a reflector body — a connected component of the thresholded amplitude envelope;
  2. an interior medial-axis (skeleton) ENDPOINT of that body — the lateral end of the
     reflection. An endpoint on the array border is edge-of-data, not geology;
  3. a measurable LATERAL DECAY along the bed's own axis. A bed that continues to the
     edge of the data, or whose envelope never falls away, is not a termination.

The onlap / truncation split is a GEOMETRIC PROXY
-------------------------------------------------
For each candidate the taper angle is measured directly from the local geometry:

    taper_length L = envelope_peak / max |d envelope / d s|   (s along the bed axis)
    contact_angle  = atan(local_perpendicular_bed_thickness / L)

A thin bed that loses its reflection over a long run has a small taper angle — it thins
tangentially against the surface (onlap-style pinch-out). A bed at full thickness right
up to a discordant face has a large taper angle (truncation-style cut).

That is a proxy. The real classification (which surface is the OLDER one the young beds
onlap onto, versus which old beds are CUT) requires the horizon mask: **a candidate must
be combined with a `horizon_mask` before onlap-vs-truncation is a stratigraphic
statement.** The returned ``caveat`` key says so in words, so the caveat survives the
wire even if a caller never reads this docstring.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import ndimage as ndi
from skimage import filters as skfilters
from skimage import measure as skmeasure
from skimage import morphology as skmorph

__all__ = ["detect_terminations", "build_cross_cutting_table"]

# Gradient-magnitude filters available in scikit-image (NOT OpenCV — cv2 is absent by
# contract and must never be imported in this layer). `laplace` is deliberately absent:
# it is a second derivative, not a gradient magnitude.
_GRADIENT_FILTERS: dict[str, Any] = {
    name: getattr(skfilters, name)
    for name in ("sobel", "prewitt", "scharr", "roberts", "farid")
    if callable(getattr(skfilters, name, None))
}

CAVEAT_HORIZON_MASK = (
    "CANDIDATE contacts only. A termination candidate is a place where a reflector "
    "body ends abruptly against a measurable gradient. Onlap (younger beds terminate "
    "AGAINST an older surface) versus truncation (older beds are CUT by a younger "
    "surface) is a statement about which horizon is older at that point, so the "
    "onlap_contacts / truncation_contacts split returned here is a GEOMETRIC PROXY "
    "(angular discordance between the bed and the counter-surface found beyond its "
    "termination). Combine these candidates with a horizon_mask before treating the "
    "split as stratigraphic. A bare gradient edge is not a termination; neither is a "
    "bare amplitude-mask boundary."
)


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────


def _orientation_mod180(dx: float, dy: float) -> float:
    """Orientation of a line (dx, dy) in [0,180) degrees, x = trace, y = sample.

    Image y increases DOWNWARD, so this is not a map azimuth — it is a section
    orientation. Only acute angles BETWEEN two such orientations are used downstream,
    and the mirror introduced by the y-flip preserves acute angles.
    """
    return float(np.degrees(np.arctan2(dx, dy)) % 180.0)


def _robust_amplitude_gate(amp: np.ndarray, *, k: float, frac: float) -> float:
    """max(median + k * 1.4826 * MAD, frac * P99) — a declared, reproducible threshold.

    The MAD term tracks a noisy background; the P99 term keeps the gate sane on sparse
    synthetic sections where the median and the MAD are both ~0 (a MAD-only gate would
    let every float-rounding tail into the mask).

    On a section where reflectors cover less than 1 % of the pixels P99 can be exactly 0,
    which would collapse the gate to the MAD term and let every smoothed tail into the
    mask; the reference peak then falls back to the extreme value.
    """
    med = float(np.median(amp))
    mad = float(np.median(np.abs(amp - med)))
    p99 = float(np.percentile(amp, 99.0))
    reference_peak = p99 if p99 > 0.0 else float(amp.max())
    return max(med + float(k) * 1.4826 * mad, float(frac) * reference_peak)


def _body_elongation(body: np.ndarray) -> float:
    """sqrt(major/second minor eigenvalue) of the body's pixel scatter, x = trace.

    A seismic reflection is a laterally continuous BAND: elongated by construction. A
    single bright sample or an isotropic amplitude anomaly is not a reflection at all,
    so it can have no lateral termination — this gate is what stops a lone spike from
    producing two "contacts".
    """
    rows, cols = np.nonzero(body)
    if rows.size < 3:
        return 0.0
    pts = np.column_stack([cols, rows]).astype(float)
    centred = pts - pts.mean(axis=0, keepdims=True)
    cov = (centred.T @ centred) / float(pts.shape[0])
    vals = np.linalg.eigvalsh(cov)
    if vals[0] <= 1e-12:
        return float("inf")
    return float(np.sqrt(vals[1] / vals[0]))


def _skeleton_endpoints(skel: np.ndarray) -> list[tuple[int, int]]:
    """(row, col) of every skeleton pixel with exactly one 8-connected neighbour."""
    kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)
    counts = ndi.convolve(skel.astype(np.uint8), kernel, mode="constant", cval=0)
    rows, cols = np.nonzero(skel & (counts == 1))
    return [(int(r), int(c)) for r, c in zip(rows, cols)]


def _walk_tangent(
    skel: np.ndarray, start: tuple[int, int], steps: int
) -> tuple[float, float, float, float] | None:
    """Walk a skeleton from an endpoint; return (orientation_deg, length_px, ux, uy).

    (ux, uy) is the unit vector pointing INWARD along the bed axis (from the endpoint
    into the reflector body). Returns None when the endpoint has no walkable neighbour.
    """
    visited = {start}
    path = [start]
    current = start
    for _ in range(int(steps)):
        r, c = current
        nxt = None
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < skel.shape[0] and 0 <= cc < skel.shape[1]:
                    if skel[rr, cc] and (rr, cc) not in visited:
                        nxt = (rr, cc)
                        break
            if nxt is not None:
                break
        if nxt is None:
            break
        visited.add(nxt)
        path.append(nxt)
        current = nxt

    if len(path) < 2:
        return None
    dy = float(path[-1][0] - path[0][0])
    dx = float(path[-1][1] - path[0][1])
    length = float(np.hypot(dx, dy))
    if length <= 0.0:
        return None
    return _orientation_mod180(dx, dy), length, dx / length, dy / length


def _ray_profile(
    field: np.ndarray,
    endpoint: tuple[int, int],
    ox: float,
    oy: float,
    steps: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Bilinearly sample `field` along the OUTWARD ray from an endpoint.

    (ox, oy) is the unit vector pointing AWAY from the reflector body (opposite the
    inward tangent): sample t = 0, 1, ... steps at ``endpoint + t * (ox, oy)``. Returns
    (values, inside) where `inside` is False for samples that fall outside the section.
    """
    t = np.arange(int(steps) + 1, dtype=float)
    rows = endpoint[0] + t * oy
    cols = endpoint[1] + t * ox
    coords = np.vstack([rows, cols])
    vals = ndi.map_coordinates(field, coords, order=1, mode="constant", cval=0.0)
    inside = (
        (coords[0] >= 0.0)
        & (coords[0] <= field.shape[0] - 1)
        & (coords[1] >= 0.0)
        & (coords[1] <= field.shape[1] - 1)
    )
    return np.asarray(vals, dtype=float), np.asarray(inside, dtype=bool)


def _local_perpendicular_thickness(
    label_map: np.ndarray, endpoint: tuple[int, int], own_label: int, ux: float
) -> float:
    """Perpendicular bed thickness (px) at an endpoint from the body's column height.

    A body of true thickness T dipping by alpha has column height T / cos(alpha), so
    T = column_height * |ux| with ux the x-component of the unit tangent (|ux| = 1 for a
    flat bed, -> 0 as the bed approaches vertical). Floored at 1 px so the taper angle
    stays defined for a skeleton that ends in a single-pixel column.
    """
    col = int(endpoint[1])
    if not (0 <= col < label_map.shape[1]):
        return 1.0
    height = float(np.count_nonzero(label_map[:, col] == own_label))
    return max(height * abs(float(ux)), 1.0)


def _taper_estimate(
    amp: np.ndarray,
    gx: np.ndarray,
    gz: np.ndarray,
    label_map: np.ndarray,
    endpoint: tuple[int, int],
    ux: float,
    uy: float,
    own_label: int,
    *,
    max_taper_px: int,
    decay_frac: float,
    edge_frac: float,
) -> tuple[float | None, float | None, float | None, str]:
    """Estimate the taper angle at a lateral termination.

    Model: a laterally thinning bed of thickness T that loses its reflection over a run
    L has its upper/lower surfaces converging at ``atan(T / L)``. That angle is the
    taper angle between the bed and the surface it dies against:

      * small angle -> the bed thins tangentially to nothing  -> onlap-style pinch-out;
      * large angle -> the bed is at full thickness right up to a discordant face the
        smoothing kernel reduces to 1-2 px                     -> truncation-style cut.

    L is measured from the envelope profile along the bed axis, using the projected
    gradient (`skimage.filters` sobel) as the linearised decay rate:
    ``L = envelope_peak / max|d envelope / d s|``.

    Returns (contact_angle_deg | None, taper_length_px | None, local_thickness_px |
    None, reason). The reason string is the audit trail for the None case.
    """
    outward_x, outward_y = -float(ux), -float(uy)
    vals, inside = _ray_profile(amp, endpoint, outward_x, outward_y, int(max_taper_px))
    n_inside = int(inside.sum())
    if n_inside < 3:
        return None, None, None, "ray leaves the section immediately — candidate at the data edge"
    vals_in = vals[:n_inside]
    peak = float(max(vals_in[0], float(vals_in[:3].max())))
    if peak <= 0.0:
        return None, None, None, "zero envelope at the endpoint"

    if float(vals_in[-1]) >= float(edge_frac) * peak:
        return (
            None,
            None,
            None,
            "the reflection is still at >= "
            f"{float(edge_frac):.2f} of peak where the section ends — the bed continues "
            "off the data, so this endpoint is edge-of-data, not a termination",
        )

    below = np.nonzero(vals_in < float(decay_frac) * peak)[0]
    if below.size == 0:
        return (
            None,
            None,
            None,
            f"envelope never falls below {float(decay_frac):.2f} * peak within "
            f"{int(max_taper_px)} px along the bed axis — medial-axis endpoint without a "
            "lateral end (no termination)",
        )
    t_zero = float(below[0])
    window = np.arange(0, int(min(n_inside, t_zero + 3)), dtype=float)
    gx_s, _ = _ray_profile(gx, endpoint, outward_x, outward_y, int(max_taper_px))
    gz_s, _ = _ray_profile(gz, endpoint, outward_x, outward_y, int(max_taper_px))
    proj = np.abs(gx_s[: window.size] * outward_x + gz_s[: window.size] * outward_y)
    slope = float(proj.max()) if proj.size else 0.0
    if slope <= 0.0:
        return None, None, None, "no measurable gradient along the bed axis"
    taper_length = peak / slope
    thickness = _local_perpendicular_thickness(label_map, endpoint, own_label, ux)
    angle = float(np.degrees(np.arctan2(thickness, max(taper_length, 1e-6))))
    angle = float(min(max(angle, 0.0), 90.0))
    return angle, float(taper_length), float(thickness), (
        f"taper angle {angle:.2f} deg from atan(thickness {thickness:.2f} px / "
        f"taper length {taper_length:.2f} px); envelope decays to "
        f"{float(decay_frac):.2f} * peak at {t_zero:.0f} px"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Axis D.1 — termination candidates
# ─────────────────────────────────────────────────────────────────────────────


def detect_terminations(
    section: np.ndarray,
    *,
    do_smoothing: bool = True,
    method: str = "sobel",
    sigma: float = 1.0,
    amplitude_frac: float = 0.25,
    amplitude_k: float = 3.0,
    min_component_px: int = 12,
    min_body_elongation: float = 3.0,
    border_margin_px: int = 1,
    tangent_steps: int = 6,
    max_taper_px: int = 40,
    decay_frac: float = 0.1,
    edge_frac: float = 0.5,
    angular_threshold_deg: float = 25.0,
) -> dict[str, Any]:
    """Candidate reflection terminations from amplitude-envelope medial-axis endpoints.

    Returns (CONTRACT.md §4 keys, exactly)
    --------------------------------------
    ``"onlap_contacts"``      list[(x, y)] — trace index x, sample index y. Candidates
                              whose bed meets the counter-surface at a LOW taper angle
                              (tangential death).
    ``"truncation_contacts"`` list[(x, y)] — candidates meeting it at a HIGH angle
                              (beds cut across).
    ``"n_candidates"``        int — len(onlap) + len(truncation).
    ``"method"``              str — the algorithm actually run, named (CONTRACT.md §3:
                              a method string is a receipt, not a decoration).

    Audit keys (additive)
    ---------------------
    ``"candidates"``     list[dict] — per-candidate: x, y, class, contact_angle_deg,
                         taper_length_px, local_thickness_px, tangent_azimuth_deg,
                         tangent_length_px, component_id, class_reason.
    ``"n_unclassified"`` int — endpoints rejected because no taper angle was
                         measurable. Both reject buckets are reported separately:
                         ``n_border_endpoints_rejected`` (endpoint on the data edge) and
                         ``n_no_lateral_end_rejected`` (the reflection does not decay —
                         not a lateral end at all).
    ``"caveat"``         str — the horizon-mask requirement, in words, on the wire.
    ``"parameters"``     dict — every knob actually used, plus the derived amplitude
                         gate and the gradient decomposition actually applied.

    Method (deterministic; no randomness, no cv2, no torch)
    ------------------------------------------------------
    1. Gaussian smoothing unless ``do_smoothing=False``;
    2. amplitude envelope gate ``|sm| > max(median + k*1.4826*MAD, frac*P99)``;
    3. label reflector bodies, drop bodies smaller than ``min_component_px``;
    4. skeletonise; interior skeleton endpoints = lateral ends of reflections;
    5. walk each endpoint's skeleton inward for the bed tangent, then sample the
       envelope and the projected gradient OUTWARD along that axis:
       ``taper_length = envelope_peak / max|d envelope/ds|``;
    6. ``contact_angle = atan(local_perpendicular_thickness / taper_length)`` — the
       geometric taper angle between the bed and the surface it dies against.

    Scale caveat: ``taper_length_px`` and ``local_thickness_px`` are in SAMPLES/TRACES,
    so ``angular_threshold_deg`` is a resolution-dependent convention of this layer, not
    a physical measurement. Convert with ``dx_m``/``dz_m`` before making a geological
    claim; until then the onlap/truncation split is a screening proxy.

    The returned onlap_contacts / truncation_contacts split is a GEOMETRIC PROXY, never a
    stratigraphic statement: combine the candidates with a ``horizon_mask`` before
    asserting which surface the young beds onlap onto and which old beds are cut.

    Scope note (honest limitation): a reflection that is OFFSET across a fault and
    resumes on the other side is NOT detected here — the amplitude envelope does not
    decay, so no candidate is produced. Detecting that requires correlating reflections
    across the fault, which is fault-offset picking, not termination detection.

    Edge cases are returned, not crashed on: a constant or all-zero section has no
    reflector bodies and yields zero candidates; a reflector spanning the full trace
    range continues off the data and yields zero candidates (edge-of-data, not geology).
    """
    if method not in _GRADIENT_FILTERS:
        raise ValueError(
            f"unknown gradient method {method!r}; available: {sorted(_GRADIENT_FILTERS)}"
        )

    img = np.asarray(section, dtype=float)
    if img.ndim != 2:
        raise ValueError(f"section must be 2-D (n_samples_z, n_traces), got {img.shape}")
    if img.size == 0:
        raise ValueError("section is empty")

    params: dict[str, Any] = {
        "do_smoothing": bool(do_smoothing),
        "method": method,
        "sigma": float(sigma),
        "amplitude_frac": float(amplitude_frac),
        "amplitude_k": float(amplitude_k),
        "min_component_px": int(min_component_px),
        "min_body_elongation": float(min_body_elongation),
        "border_margin_px": int(border_margin_px),
        "tangent_steps": int(tangent_steps),
        "max_taper_px": int(max_taper_px),
        "decay_frac": float(decay_frac),
        "edge_frac": float(edge_frac),
        "angular_threshold_deg": float(angular_threshold_deg),
    }
    method_string = (
        f"amplitude_envelope_gate(max(median+{amplitude_k:g}*1.4826*MAD,"
        f"{amplitude_frac:g}*P99)) + skimage.measure.label + "
        f"skimage.morphology.skeletonize endpoints + skimage.filters.{method} "
        f"projected-gradient taper length + atan(thickness/taper_length) classifier "
        f"(threshold={angular_threshold_deg:g}deg)"
    )
    if do_smoothing:
        method_string = f"gaussian(sigma={sigma:g}) + " + method_string

    def _empty() -> dict[str, Any]:
        return {
            "onlap_contacts": [],
            "truncation_contacts": [],
            "n_candidates": 0,
            "method": method_string,
            "candidates": [],
            "n_unclassified": 0,
            "n_components": 0,
            "n_border_endpoints_rejected": 0,
            "n_no_lateral_end_rejected": 0,
            "n_non_reflector_bodies_rejected": 0,
            "caveat": CAVEAT_HORIZON_MASK,
            "parameters": params,
        }

    working = skfilters.gaussian(img, sigma=float(sigma)) if do_smoothing else img
    amp = np.abs(working)
    peak = float(amp.max())
    if not np.isfinite(peak) or peak <= 0.0:
        # Perfectly flat (or all-NaN) section: no reflector bodies exist at all.
        return _empty()

    gate = _robust_amplitude_gate(amp, k=amplitude_k, frac=amplitude_frac)
    mask = amp > gate
    if not bool(mask.any()):
        return _empty()

    # Directional gradient components of the chosen filter. skimage's *_h
    # differentiates along axis 0 (sample/z), *_v along axis 1 (trace/x). `roberts` has
    # no directional decomposition, so it falls back to sobel and says so in `params`.
    _h = getattr(skfilters, f"{method}_h", None)
    _v = getattr(skfilters, f"{method}_v", None)
    if callable(_h) and callable(_v):
        gz = np.asarray(_h(working), dtype=float)
        gx = np.asarray(_v(working), dtype=float)
        params["gradient_components"] = f"skimage.filters.{method}_h / {method}_v"
    else:
        gz = np.asarray(skfilters.sobel_h(working), dtype=float)
        gx = np.asarray(skfilters.sobel_v(working), dtype=float)
        params["gradient_components"] = (
            f"skimage.filters.{method} has no directional decomposition — fell back to "
            "sobel_h / sobel_v for the taper-length measurement"
        )
    params["amplitude_gate"] = float(gate)

    labels = skmeasure.label(mask, connectivity=2)
    n_components = int(labels.max())

    candidates: list[dict[str, Any]] = []
    n_border_rejected = 0
    n_no_lateral_end = 0
    n_non_reflector = 0
    for comp_id in range(1, n_components + 1):
        body = labels == comp_id
        if int(body.sum()) < int(min_component_px):
            continue
        if _body_elongation(body) < float(min_body_elongation):
            # Isotropic amplitude anomaly, not a laterally continuous reflection.
            n_non_reflector += 1
            continue
        skel = skmorph.skeletonize(body)
        for r, c in _skeleton_endpoints(skel):
            if (
                r < int(border_margin_px)
                or c < int(border_margin_px)
                or r >= img.shape[0] - int(border_margin_px)
                or c >= img.shape[1] - int(border_margin_px)
            ):
                n_border_rejected += 1
                continue
            tangent = _walk_tangent(skel, (r, c), int(tangent_steps))
            if tangent is None:
                continue
            tangent_deg, tangent_len, ux, uy = tangent
            angle, taper_length, thickness, reason = _taper_estimate(
                amp,
                gx,
                gz,
                labels,
                (r, c),
                ux,
                uy,
                comp_id,
                max_taper_px=int(max_taper_px),
                decay_frac=float(decay_frac),
                edge_frac=float(edge_frac),
            )
            if angle is None:
                # No lateral end: the reflection either continues off the data or never
                # decays. That is not a termination and is NOT counted as a candidate.
                n_no_lateral_end += 1
                continue
            record: dict[str, Any] = {
                "x": float(c),
                "y": float(r),
                "component_id": int(comp_id),
                "tangent_azimuth_deg": float(tangent_deg),
                "tangent_length_px": float(tangent_len),
                "taper_length_px": float(taper_length),
                "local_thickness_px": float(thickness),
                "contact_angle_deg": float(angle),
                "class": (
                    "truncation" if angle >= float(angular_threshold_deg) else "onlap"
                ),
                "class_reason": (
                    f"{reason}; threshold {float(angular_threshold_deg):.2f} deg — "
                    "geometric proxy only, horizon_mask required to stratigraphically "
                    "separate onlap from truncation"
                ),
            }
            candidates.append(record)

    onlap = [(c["x"], c["y"]) for c in candidates if c["class"] == "onlap"]
    truncation = [(c["x"], c["y"]) for c in candidates if c["class"] == "truncation"]

    return {
        "onlap_contacts": onlap,
        "truncation_contacts": truncation,
        "n_candidates": len(onlap) + len(truncation),
        "method": method_string,
        "candidates": candidates,
        "n_unclassified": n_no_lateral_end,
        "n_components": n_components,
        "n_border_endpoints_rejected": n_border_rejected,
        "n_no_lateral_end_rejected": n_no_lateral_end,
        "n_non_reflector_bodies_rejected": n_non_reflector,
        "caveat": CAVEAT_HORIZON_MASK,
        "parameters": params,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Axis D.2 — cross-cutting table
# ─────────────────────────────────────────────────────────────────────────────

PRINCIPLE = (
    "CROSS-CUTTING / SUPERPOSITION principle (Steno 1669, Hutton 1795, Lyell 1830): a "
    "feature is YOUNGER than the youngest horizon it offsets, and OLDER than the oldest "
    "horizon that drapes it without offset. This is NOT Walther's Law (Walther 1894), "
    "which governs conformable facies succession — vertically stacked conformable facies "
    "were laterally adjacent environments. Different principle, different author set. "
    "Conflating them is a known error."
)

DRAPE_CAVEAT = (
    "A drape observation dates the fault LOCALLY, not the system: fault tips and relay "
    "zones drape in one place while offsetting the same horizon along strike. The "
    "older_than bound is therefore scoped LOCAL and must not be promoted to a regional "
    "fault age."
)

_HORIZON_SCHEMA = (
    "horizons[] entries are dicts: {'id': str (required), 'rank': int = 1 is the "
    "YOUNGEST (required unless every horizon supplies 'age_ma'), 'age_ma': float|None "
    "(Ma before present; younger = smaller), 'offset_by': [feature_id, ...] (features "
    "observed to OFFSET this horizon), 'draped_by': [feature_id, ...] (features this "
    "horizon DRAPES without offset), 'mask': bool ndarray|None (optional; used only to "
    "test whether termination candidates fall inside this horizon's footprint)}"
)


def _rank_key(horizons: list[dict[str, Any]]) -> dict[str, int]:
    """Map horizon id -> rank, where rank 1 is the YOUNGEST horizon.

    All-explicit `rank`, or all-`age_ma` (derived ordering) — a mixture is refused rather
    than guessed, because a partially specified stratigraphic order cannot be
    reconstructed without inventing correlations.
    """
    have_rank = [h.get("rank") is not None for h in horizons]
    have_age = [isinstance(h.get("age_ma"), (int, float)) for h in horizons]
    if all(have_rank):
        return {str(h["id"]): int(h["rank"]) for h in horizons}
    if all(have_age):
        order = sorted(horizons, key=lambda h: float(h["age_ma"]))
        return {str(h["id"]): i + 1 for i, h in enumerate(order)}
    raise ValueError(
        "horizons must ALL declare 'rank' (1 = youngest) or ALL declare 'age_ma' — "
        "a mixed or missing stratigraphic ordering cannot be resolved without guessing"
    )


def _contacts_in_mask(horizon: dict[str, Any], candidates: list[dict[str, Any]]) -> int:
    """Count termination candidates falling inside a horizon mask (dilated by 1 px)."""
    mask = horizon.get("mask")
    if mask is None or not candidates:
        return 0
    arr = np.asarray(mask, dtype=bool)
    if arr.ndim != 2:
        return 0
    dilated = ndi.binary_dilation(arr, iterations=1)
    n = 0
    for cand in candidates:
        r = int(round(float(cand["y"])))
        c = int(round(float(cand["x"])))
        if 0 <= r < dilated.shape[0] and 0 <= c < dilated.shape[1] and dilated[r, c]:
            n += 1
    return n


def build_cross_cutting_table(
    terminations: dict[str, Any],
    horizons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Relative chronology table from terminations + horizon observations.

    Returns ``{"relations": list[dict], "n": int}`` (CONTRACT.md §4) plus additive audit
    keys (``n_features``, ``n_candidates_available``, ``unconstrained_features``,
    ``principle``, ``caveats``, ``schema``).

    The rule, stated once and used exactly
    -------------------------------------
    For each feature F:

      * ``younger_than`` = the YOUNGEST horizon F offsets (min rank among offsets) — F
        must post-date it.
      * ``older_than``   = the OLDEST horizon that drapes F (max rank among drapes) — F
        must pre-date it.

    Horizons strictly between those bounds that neither offset nor drape F are
    UNDETERMINED against F (listed in ``undetermined_horizon_ids``, not guessed).
    Horizons outside the bounds follow by transitivity and are not listed.

    ``consistent`` is the falsification check: the age interval is non-empty iff
    ``rank(younger_than) > rank(older_than)`` (rank 1 = youngest). ``consistent=False``
    means the supplied observations contradict each other — a finding to report, never an
    exception to swallow and never silently repaired.

    This is the CROSS-CUTTING / superposition principle (Steno 1669, Hutton 1795, Lyell
    1830). It is explicitly **NOT Walther's Law** (Walther 1894), which governs
    conformable facies succession — vertically stacked conformable facies were laterally
    adjacent environments. These are two separate principles and conflating them is a
    known error (mirrored in `K-REGIME-XCUT`, `tools/structure_gates/tectonic_regime.py`).
    Walther's Law is not tested anywhere in this module.

    Caveat carried on every relation: a drape observation dates the feature LOCALLY —
    fault tips and relay zones drape in one place while offsetting the same horizon along
    strike — so ``older_than`` is a local bound and ``scope`` says so.

    The ``terminations`` argument is consumed, not decorative: the candidate counts (and
    any candidates falling inside a horizon's optional ``mask``) are recorded in every
    relation's ``evidence``, so a relation supported by annotation alone is visibly
    labelled as such.
    """
    term = terminations or {}
    cands = list(term.get("candidates") or [])
    n_candidates_available = int(term.get("n_candidates") or (len(cands) if cands else 0))
    n_onlap = len(term.get("onlap_contacts") or [])
    n_truncation = len(term.get("truncation_contacts") or [])
    method = str(term.get("method") or "")

    hz = [h for h in (horizons or []) if isinstance(h, dict)]
    if hz:
        missing = [i for i, h in enumerate(hz) if not h.get("id")]
        if missing:
            raise ValueError(f"horizons[{missing}] missing required 'id'")
    ranks = _rank_key(hz) if hz else {}

    def _members(horizon: dict[str, Any], key: str) -> list[str]:
        return [str(v) for v in (horizon.get(key) or [])]

    feature_ids = sorted(
        {fid for h in hz for fid in (_members(h, "offset_by") + _members(h, "draped_by"))}
    )

    relations: list[dict[str, Any]] = []
    unconstrained: list[str] = []

    for fid in feature_ids:
        offset_horizons = [h for h in hz if fid in _members(h, "offset_by")]
        drape_horizons = [h for h in hz if fid in _members(h, "draped_by")]
        if not offset_horizons and not drape_horizons:
            unconstrained.append(fid)
            continue

        younger_h = (
            min(offset_horizons, key=lambda h: ranks[str(h["id"])])
            if offset_horizons
            else None
        )
        older_h = (
            max(drape_horizons, key=lambda h: ranks[str(h["id"])])
            if drape_horizons
            else None
        )

        def _bound(h: dict[str, Any] | None) -> dict[str, Any] | None:
            if h is None:
                return None
            hid = str(h["id"])
            return {"horizon_id": hid, "rank": int(ranks[hid]), "age_ma": h.get("age_ma")}

        younger_bound, older_bound = _bound(younger_h), _bound(older_h)

        consistent: bool | None = None
        undetermined: list[str] = []
        if younger_bound and older_bound:
            consistent = bool(younger_bound["rank"] > older_bound["rank"])
            lo, hi = older_bound["rank"], younger_bound["rank"]
            undetermined = sorted(
                (hid for hid, rk in ranks.items() if lo < rk < hi),
                key=lambda hid: ranks[hid],
            )

        if younger_bound and older_bound:
            statement = (
                f"{fid} is younger than {younger_bound['horizon_id']} (the youngest "
                f"horizon it offsets) and older than {older_bound['horizon_id']} (the "
                "oldest horizon that drapes it locally)"
            )
        elif younger_bound:
            statement = (
                f"{fid} is younger than {younger_bound['horizon_id']}; no drape "
                "observation bounds it from above"
            )
        else:
            statement = (
                f"{fid} is older than {older_bound['horizon_id']} (local drape); no "
                "offset observation bounds it from below"
            )
        if consistent is False:
            statement += (
                " — CONTRADICTION: the supplied offset and drape observations give an "
                "empty age interval"
            )

        evidence: dict[str, Any] = {
            "n_candidates": n_candidates_available,
            "n_onlap_contacts": n_onlap,
            "n_truncation_contacts": n_truncation,
            "detect_terminations_method": method,
            "n_horizons_supplied": len(hz),
        }
        contacts_in_masks: dict[str, int] = {}
        for h in hz:
            n_in = _contacts_in_mask(h, cands)
            if n_in > 0:
                contacts_in_masks[str(h["id"])] = n_in
        if contacts_in_masks:
            evidence["n_candidates_inside_horizon_mask"] = contacts_in_masks
        if not cands:
            evidence["note"] = (
                "no termination candidates supplied — the relation rests on the explicit "
                "offset_by / draped_by annotations alone and is not geometry-supported"
            )

        relations.append(
            {
                "feature": fid,
                "younger_than": younger_bound,
                "older_than": older_bound,
                "n_offset_horizons": len(offset_horizons),
                "n_drape_horizons": len(drape_horizons),
                "offset_horizon_ids": [str(h["id"]) for h in offset_horizons],
                "drape_horizon_ids": [str(h["id"]) for h in drape_horizons],
                "consistent": consistent,
                "scope": "LOCAL" if drape_horizons else "REGIONAL",
                "undetermined_horizon_ids": undetermined,
                "n_undetermined": len(undetermined),
                "statement": statement,
                "caveat": DRAPE_CAVEAT,
                "principle": "cross_cutting_superposition",
                "evidence": evidence,
            }
        )

    seen_features = {r["feature"] for r in relations}
    unconstrained.extend(
        str(h["id"])
        for h in hz
        if str(h["id"]) not in seen_features
        and not _members(h, "offset_by")
        and not _members(h, "draped_by")
    )

    return {
        "relations": relations,
        "n": len(relations),
        "n_features": len(feature_ids),
        "n_candidates_available": n_candidates_available,
        "unconstrained_features": sorted(set(unconstrained)),
        "principle": PRINCIPLE,
        "caveats": [DRAPE_CAVEAT, CAVEAT_HORIZON_MASK],
        "schema": _HORIZON_SCHEMA,
    }
