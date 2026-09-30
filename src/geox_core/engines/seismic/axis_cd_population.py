"""AXIS C + AXIS D — deterministic fault-orientation and stratal-termination extractors.

Two independently callable gates:

  AXIS C  ``analyse_fault_orientation_population``
          strike rose -> conjugate bimodality -> acute bisector (candidate azimuth)
          -> Riedel (synthetic / antithetic) relativity against a master fault.

  AXIS D  ``classify_stratal_terminations``
          reference surface + underlying surfaces/ridges -> onlap / downlap /
          toplap / truncation / offlap-concordant, WITH termination coordinates
          and a RELATIVE (partial-order) chronology.

Both are KINEMATIC. Neither produces a stress tensor, and neither produces an age.

Load-bearing doctrine
---------------------
1. **A fault azimuth population is CURRENT STRESS INTERSECTED WITH INHERITED
   FABRIC.** It is not a pure stress indicator. Pre-existing low-cohesion faults
   reactivate even when unfavourably oriented to the contemporary stress field.
   The caveat is stamped into every Axis C receipt, in every status, including
   UNMEASURED.

2. **UNMEASURED is not a pass and not a failure.** It means the observation
   window did not cover the question. A too-small population returns UNMEASURED
   and NO bisector — a bisector with a ~30 deg error bar is indistinguishable
   from inherited fabric, block rotation or oblique stress, so it must not be
   printed at all.

3. **A stress tensor cannot be derived from fault-plane orientation alone.** It
   requires slip vectors, and slip vectors require 3D cutoff-line geometry.
   2D data can NEVER enter the DYNAMIC tier. Gate C-CEILING encodes the refusal
   (KILL on the claim, never on the data).

4. **Terminations yield RELATIVE (partial-order) chronology ONLY.** Absolute age
   requires biostratigraphy or geochronology. Axis D returns
   ``absolute_age_permitted: False`` and names what would be required.

5. **A horizon that ABUTS a fault with zero offset is SYNCHRONOUS with that
   fault — it is not younger than it.** Abutment with zero offset is a
   growth-fault relationship: the horizon and the fault surface were both at the
   depositional surface. This pitfall is encoded and tested.

6. **Irreducible observables.** An azimuth read on a time section without a
   velocity model is meaningless; depth/velocity correction precedes any strike
   or azimuth claim (gate C-CALIBRATION). Andersonian reference geometry holds
   only for NEW faults in isotropic rock near the surface with a free surface —
   beyond 15 deg of deviation the correct output is an ENUMERATION of
   alternatives (inherited fabric, overpressure/weak substrate, block rotation,
   oblique stress), never "the regime changed".

7. **No fabricated numbers.** Every uncomputable field is None with status
   UNMEASURED and the missing inputs named. No confidence/probability is ever
   emitted: ``confidence`` stays None with
   ``confidence_status = NOT_ESTABLISHED_NO_VALIDATED_BENCHMARK``.

Determinism: no randomness, no clock dependence, no seeds. Identical inputs
produce an identical ``receipt_hash``. Determinism means REPRODUCIBLE, not
dimensionally TRUE.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt, receipt_hash

# ── Epistemic tiers ──────────────────────────────────────────────────────────

TIER_KINEMATIC = "KINEMATIC"  # directly readable from geometry
TIER_STRAIN = "STRAIN"        # requires restoration + plane-strain assumptions
TIER_DYNAMIC = "DYNAMIC"      # requires fault-slip inversion; 4 of 6 params at best

# ── Andersonian reference geometry (Anderson 1951; Byerlee 1978) ─────────────

ANDERSON_REFERENCE: dict[str, dict[str, Any]] = {
    "normal": {"expected_dip_deg": 60.0, "vertical_axis": "sigma1"},
    "thrust": {"expected_dip_deg": 30.0, "vertical_axis": "sigma3"},
    "strike_slip": {"expected_dip_deg": 90.0, "vertical_axis": "sigma2"},
}
COULOMB_TOLERANCE_DEG = 15.0  # beyond this: fabric / overpressure / rotation, NOT a new regime

# ── Axis C constants ─────────────────────────────────────────────────────────

DEFAULT_BIN_WIDTH_DEG = 10.0
DEFAULT_SMOOTHING_BINS = 1.0
MIN_POPULATION_N = 12
MIN_PER_MODE = 4
MIN_MODE_SEPARATION_DEG = 30.0
MIN_VALLEY_DEPTH = 0.25          # valley must dip to <= 75% of the smaller peak
MIN_HALF_DIP_FOR_STRATA_SENSE = 0.5
RIEDEL_REFERENCE_DEG = {"R": 15.0, "R_prime": 75.0, "P": 12.5}
RIEDEL_TOLERANCE_DEG = 10.0
ROTATION_TOLERANCE_DEG = 10.0

MIN_N_BASIS = (
    "Minimum N derived from bisector PRECISION, not from convention. The axial standard error of a "
    "circular (von Mises) mode is SE ~= sigma_rad / sqrt(n_mode) for concentration kappa ~= 1/sigma_rad^2 "
    "(Fisher 1993, Statistical Analysis of Circular Data). For a within-mode dispersion sigma ~= 23 deg "
    "(0.40 rad) and a target bisector precision of 10 deg (0.175 rad): 0.40/sqrt(n_mode) <= 0.175 "
    "-> n_mode >= 5.2 -> n_mode = 6, i.e. N = 12 for a two-mode conjugate set. The same 4-6 floor is "
    "what separates a genuine second mode from single-measurement noise in a 10 deg rose. Below N=12 the "
    "bisector is returned as UNMEASURED rather than as a low-precision number, because a bisector with a "
    "~30 deg error bar cannot be distinguished from the competing explanations (inherited fabric, block "
    "rotation, oblique stress) — printing it would manufacture a measurement."
)

INHERITANCE_CAVEAT = (
    "A fault azimuth population is CURRENT STRESS INTERSECTED WITH INHERITED FABRIC. It is NOT a pure "
    "stress indicator. Pre-existing low-cohesion faults reactivate even when unfavourably oriented to the "
    "contemporary stress field, so the observed population can be dominated by pre-existing planes rather "
    "than by the planes the current stress would create."
)

RIEDEL_CAVEAT = (
    "Riedel classification is a RELATIVITY statement about one measured population against a supplied "
    "master azimuth, not a shear-experiment replication. R (~15 deg) and P (~10-15 deg) windows overlap; "
    "R and P are synthetic (same shear sense as the master) and R' (~75 deg) is antithetic. Absence of "
    "Riedel shears is a DEFICIT and may only return UNMEASURED — never KILL."
)

# ── Axis D constants ─────────────────────────────────────────────────────────

DEFAULT_CONCORDANCE_TOLERANCE_DEG = 3.0
DEFAULT_TOPLAP_MAX_ANGLE_DEG = 15.0
DEFAULT_ZERO_OFFSET_THRESHOLD_M = 1.0

TERMINATION_CLASSES = (
    "onlap",
    "downlap",
    "toplap",
    "truncation",
    "offlap_concordant",
)

# Fault-contact classifications are equally valid classifications, but they are
# NOT termination classes — they are handled by the SYNCHRONOUS pitfall rule.
FAULT_CONTACT_CLASSES = ("abut_synchronous", "abut_offset")

# Classifications that force the gate to WARN rather than PASS.
CAVEAT_CLASSES = (
    "onlap_or_downlap_ambiguous",
    "lap_undetermined",
    "undetermined",
    "abut_undetermined",
    "crosses_fault_zero_offset",
    "dip_inconsistent",
)

DIP_CONSISTENCY_TOLERANCE_DEG = 10.0

# Class labels are aligned string-for-string with the stratigraphy engine so the
# federation keeps ONE termination vocabulary instead of minting a second one:
#   onlap / downlap / toplap / truncation == geox_core.engines.stratigraphy
#                                            .surface_first.GeometryType.{ONLAP,DOWNLAP,TOPLAP,TRUNCATION}
#   offlap_concordant                     == GeometryType.CONCORDANT (offlap geometry: no convergence)
GEOMETRY_TYPE_ALIGNMENT = {
    "onlap": "onlap",
    "downlap": "downlap",
    "toplap": "toplap",
    "truncation": "truncation",
    "offlap_concordant": "concordant",
}

RELATIVE_CHRONOLOGY_CAVEAT = (
    "Terminations yield RELATIVE (partial-order) chronology ONLY. Absolute age requires biostratigraphy "
    "(zonation) or geochronology (radiometric / U-Pb on an ash, magnetostratigraphy). Geometry can order "
    "events; it cannot date them."
)

ABSOLUTE_AGE_REQUIREMENT = (
    "biostratigraphy (zone assignment on a tied sample)",
    "geochronology (radiometric / U-Pb on an ash bed)",
    "magnetostratigraphy",
)

FAULT_ABUT_PITFALL = (
    "A horizon that ABUTS a fault with zero offset is SYNCHRONOUS with that fault, NOT younger than it. "
    "Zero measurable offset at an abutment is a growth-fault relationship: the horizon and the fault "
    "surface sat at the depositional surface together. It must never be converted into 'the horizon "
    "postdates the fault'."
)

EROSION_INTERPRETATION_CAVEAT = (
    "An angular discordance is a KINEMATIC observation. EROSION is an INTERPRETATION. Truncation "
    "classification here records the discordance (delta dip >= the toplap ceiling); it does NOT prove "
    "erosional removal, which needs regional/biostratigraphic evidence of missing section."
)

MAX_COVER_FRACTION = "coverage below 0.7 downgrades a deficit test to UNMEASURED (GEOX falsifier rule)"

# ── Result-type / coercion helpers ───────────────────────────────────────────


def _clean(obj: Any) -> Any:
    """Coerce to JSON-native so receipt hashing and json.dumps stay honest.

    numpy scalars, arrays and non-finite floats never leak into a receipt.
    """
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, np.ndarray):
        return [_clean(v) for v in obj.tolist()]
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, float):
        return float(obj) if math.isfinite(obj) else None
    if isinstance(obj, str):
        return obj
    return str(obj)


def _receipt(
    gate_id: str,
    status: str,
    *,
    tier: str,
    scope: str = "population",
    coverage: float | None = None,
    **kw: Any,
) -> dict[str, Any]:
    """make_gate_receipt + epistemic_tier/scope/coverage folded into the hash.

    `confidence` is present and ALWAYS None: no fabricated reliability. A
    confidence value may only be attached by a named, versioned, validated
    benchmark receipt, which this module never mints.
    """
    r = make_gate_receipt(gate_id, status, **kw)  # type: ignore[arg-type]
    r["epistemic_tier"] = tier
    r["scope"] = scope
    r["coverage"] = coverage
    r["confidence"] = None
    r["confidence_basis"] = None
    r["confidence_status"] = "NOT_ESTABLISHED_NO_VALIDATED_BENCHMARK"
    r["local_verdict"] = "QUALIFIED_CANDIDATE"
    r["seal_authority"] = "arifOS_only"
    r["receipt_hash"] = receipt_hash(r)
    return r


def _attach_caveats(receipt: dict[str, Any], caveats: list[str]) -> dict[str, Any]:
    """Stamp mandatory caveats into every layer of the receipt, then re-hash."""
    existing = list(receipt.get("caveats") or [])
    for c in caveats:
        if c not in existing:
            existing.append(c)
    receipt["caveats"] = existing

    cr = receipt.setdefault("calculated_result", {})
    if isinstance(cr, dict):
        cr_c = list(cr.get("interpretation_caveats") or [])
        for c in caveats:
            if c not in cr_c:
                cr_c.append(c)
        cr["interpretation_caveats"] = cr_c

    findings = list(receipt.get("findings") or [])
    have = {f.get("caveat") for f in findings if isinstance(f, dict)}
    for c in caveats:
        if c not in have:
            findings.append({"verdict": receipt.get("status"), "caveat": c})
    receipt["findings"] = findings

    receipt["receipt_hash"] = receipt_hash(receipt)
    return receipt


def _valid_float(v: Any) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _wrap180(a: float) -> float:
    return float(a) % 180.0


def _axial_diff_deg(a: float, b: float) -> float:
    """Unsigned axial (axis, not vector) separation in [0, 90] deg."""
    d = abs(_wrap180(a) - _wrap180(b)) % 180.0
    return float(min(d, 180.0 - d))


def _axial_mean_deg(azimuths: list[float]) -> tuple[float | None, float]:
    """Axial (mod-180) mean direction + resultant length R in [0, 1].

    Axial data are handled by doubling the angle (Mardia). R is a CONCENTRATION
    statistic — it is NOT a probability and NOT a confidence.
    """
    if not azimuths:
        return None, 0.0
    a = np.radians(np.asarray(azimuths, dtype=float) * 2.0)
    c = float(np.cos(a).mean())
    s = float(np.sin(a).mean())
    r_len = float(math.hypot(c, s))
    if r_len < 1e-12:
        return None, 0.0
    return _wrap180(math.degrees(math.atan2(s, c)) / 2.0), round(r_len, 6)


def _axial_mid_deg(a: float, b: float) -> float | None:
    """Mid-axis of two axes (mod 180). None when the axes are perpendicular."""
    v = math.radians(a * 2.0), math.radians(b * 2.0)
    sx = math.cos(v[0]) + math.cos(v[1])
    sy = math.sin(v[0]) + math.sin(v[1])
    if abs(sx) < 1e-12 and abs(sy) < 1e-12:
        return None
    return _wrap180(math.degrees(math.atan2(sy, sx)) / 2.0)


def _acute_bisector_deg(m1: float, m2: float) -> dict[str, Any]:
    """The ACUTE bisector of two mode axes: the one within 45 deg of both modes."""
    c1 = _axial_mid_deg(m1, m2)
    if c1 is None:
        return {
            "acute_bisector_azimuth_deg": None,
            "obtuse_bisector_azimuth_deg": None,
            "half_angle_deg": None,
            "note": "mode axes are perpendicular — each bisector encloses 90 deg; no unique acute bisector",
        }
    c2 = _wrap180(c1 + 90.0)
    d1 = _axial_diff_deg(c1, m1)
    d2 = _axial_diff_deg(c2, m1)
    acute, obtuse, half = (c1, c2, d1) if d1 <= d2 else (c2, c1, d2)
    return {
        "acute_bisector_azimuth_deg": round(acute, 4),
        "obtuse_bisector_azimuth_deg": round(obtuse, 4),
        "half_angle_deg": round(half, 4),
        "note": "acute bisector = the bisector within 45 deg of both mode axes",
    }


def _strike_rose(strikes: list[float], bin_width_deg: float) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Binned strike rose over [0, 180) — strikes are AXES, not vectors."""
    n_bins = int(round(180.0 / bin_width_deg))
    if n_bins < 2:
        n_bins = 2
    idx = np.floor(np.mod(np.asarray(strikes, dtype=float), 180.0) / bin_width_deg).astype(int) % n_bins
    counts = np.bincount(idx, minlength=n_bins).astype(int)
    total = int(counts.sum())
    bins = [
        {
            "bin_index": i,
            "bin_start_deg": round(i * bin_width_deg, 6),
            "bin_end_deg": round((i + 1) * bin_width_deg, 6),
            "bin_center_deg": round((i + 0.5) * bin_width_deg, 6),
            "count": int(counts[i]),
            "frequency": round(float(counts[i]) / total, 6) if total else None,
        }
        for i in range(n_bins)
    ]
    return bins, counts


def _circular_smooth(counts: np.ndarray, sigma_bins: float) -> np.ndarray:
    from scipy.ndimage import gaussian_filter1d

    return gaussian_filter1d(counts.astype(float), sigma=max(sigma_bins, 1e-6), mode="wrap")


def _peak_bins(smoothed: np.ndarray) -> list[int]:
    n = smoothed.size
    out: list[int] = []
    for i in range(n):
        if smoothed[i] > smoothed[(i - 1) % n] and smoothed[i] >= smoothed[(i + 1) % n]:
            out.append(i)
    return out


def _refine_peak_azimuth(strikes: list[float], center_deg: float, window_deg: float) -> tuple[float | None, int]:
    """Sub-bin peak refinement + the mode's SUPPORT.

    Returns (axial mean of the members inside +/- window, number of members).
    The member count is the honest mode-support statistic: a single bin's raw
    count is hostage to bin-edge effects, whereas the +/- 1 bin window is the
    angular support the mode actually has.
    """
    members = [s for s in strikes if _axial_diff_deg(s, center_deg) <= window_deg]
    m, _ = _axial_mean_deg(members)
    return m, len(members)


def _valley_ratio(smoothed: np.ndarray, i1: int, i2: int) -> tuple[float | None, float | None]:
    """Minimum smoothed count on the SHORT circular arc between two peak bins."""
    n = smoothed.size
    gap_fwd = (i2 - i1) % n
    gap_bwd = (i1 - i2) % n
    if gap_fwd <= gap_bwd:
        path = [(i1 + k) % n for k in range(1, gap_fwd)]
    else:
        path = [(i1 - k) % n for k in range(1, gap_bwd)]
    if not path:
        return None, None
    vals = [float(smoothed[i]) for i in path]
    vmin = min(vals)
    vbin = path[int(np.argmin(np.asarray(vals)))]
    return vmin, float((vbin + 0.5) * 180.0 / n)


def _classify_riedel(delta_deg: float, tolerance_deg: float) -> dict[str, Any]:
    """R / R' / P relativity for one fault against a master fault azimuth."""
    hits: list[str] = []
    for name, ref in RIEDEL_REFERENCE_DEG.items():
        if abs(delta_deg - ref) <= tolerance_deg:
            hits.append(name)
    primary: str | None = None
    residual: float | None = None
    if hits:
        primary = sorted(hits, key=lambda k: (abs(delta_deg - RIEDEL_REFERENCE_DEG[k]), list(RIEDEL_REFERENCE_DEG).index(k)))[0]
        residual = round(delta_deg - RIEDEL_REFERENCE_DEG[primary], 4)
    shear = {"R": "synthetic", "P": "synthetic", "R_prime": "antithetic"}.get(primary or "", None)
    return {
        "delta_from_master_deg": round(delta_deg, 4),
        "riedel_matches": hits,
        "riedel_primary": primary,
        "riedel_residual_deg": residual,
        "shear_relationship": shear,
        "unclassified": not hits,
    }


# ── AXIS C ───────────────────────────────────────────────────────────────────

_CEILING_EQUATION = (
    "KINEMATIC -> STRAIN -> DYNAMIC requires fault-slip inversion on 3D cutoff-line geometry; "
    "fault-plane ORIENTATION alone resolves zero of six independent tensor parameters"
)


def _gate_axis_c_ceiling(
    *,
    claim_epistemic_tier: str | None,
    claim_stress_tensor: bool,
    fault_slip_data: list[dict[str, Any]] | None,
    cutoff_line_3d: bool,
) -> dict[str, Any]:
    """C-CEILING — refuse DYNAMIC from 2D fault-plane orientation (category error)."""
    has_slip = bool(fault_slip_data)
    wants_dynamic = (str(claim_epistemic_tier or "").upper() == TIER_DYNAMIC) or bool(claim_stress_tensor)
    threshold_map: dict[str, Any] = {
        "min_slip_measurements_for_inversion": 4,
        "requires_3d_cutoff_line_geometry": True,
    }
    refs: list[str] = [
        "Anderson 1951 — The Dynamics of Faulting",
        "Wallace 1951 / Bott 1959 — fault-slip stress inversion",
        "Angelier 1979 — only 4 of 6 independent tensor parameters are resolvable from slip data",
        "Byerlee 1978 — friction of rock (sigma1-3 relations hold for NEW faults)",
    ]

    if wants_dynamic and not has_slip:
        return _receipt(
            "C-CEILING",
            "KILL",
            tier=TIER_DYNAMIC,
            scope="claim_only",
            reason=(
                "DYNAMIC (stress tensor) claim requested from fault-plane orientation with no "
                "fault_slip_data. Orientation is KINEMATIC. A tensor needs slip vectors, and slip "
                "vectors need 3D cutoff-line geometry. This is a category error, not a data deficit."
            ),
            equation=_CEILING_EQUATION,
            inputs={
                "fault_slip_data_present": False,
                "cutoff_line_3d_geometry": bool(cutoff_line_3d),
                "claimed_tier": claim_epistemic_tier or None,
                "claim_stress_tensor": bool(claim_stress_tensor),
            },
            thresholds=threshold_map,
            exceptions_considered=[
                "present-day stress from borehole breakouts / DIF / leak-off tests / focal mechanisms "
                "(independent measurement, not this population)",
                "core-based slip indicators (slickenlines) with a 3D orientation frame",
            ],
            evidence_refs=refs,
            calculated_result={
                "dynamic_claim_permitted": False,
                "stress_tensor_emitted": None,
                "refusal": "TENSOR_FROM_ORIENTATION_ALONE_REFUSED",
            },
            missing_inputs=["fault_slip_data[] (rake + slip sense)", "cutoff_line_3d_geometry (3D, not 2D)"],
            gate_type="hard_epistemic",
        )

    if wants_dynamic and has_slip and not cutoff_line_3d:
        return _receipt(
            "C-CEILING",
            "PARTIALLY_MEASURED",
            tier=TIER_DYNAMIC,
            scope="claim_only",
            reason=(
                "Slip data supplied but marked as NOT 3D cutoff-line geometry. 2D slip senses with "
                "2D trace geometry cannot be inverted for a tensor — they need dip/rake in 3D."
            ),
            equation=_CEILING_EQUATION,
            inputs={
                "fault_slip_data_present": True,
                "cutoff_line_3d_geometry": False,
                "claimed_tier": claim_epistemic_tier or None,
                "claim_stress_tensor": bool(claim_stress_tensor),
            },
            thresholds=threshold_map,
            evidence_refs=refs,
            calculated_result={"dynamic_claim_permitted": False, "stress_tensor_emitted": None},
            missing_inputs=["cutoff_line_3d_geometry (3D, not 2D)"],
            gate_type="hard_epistemic",
        )

    if has_slip and cutoff_line_3d:
        return _receipt(
            "C-CEILING",
            "PASS",
            tier=TIER_DYNAMIC,
            scope="claim_only",
            reason="Slip vectors in 3D cutoff-line geometry present — DYNAMIC tier permitted (4 of 6 parameters).",
            equation=_CEILING_EQUATION,
            inputs={"fault_slip_data_present": True, "cutoff_line_3d_geometry": True},
            thresholds=threshold_map,
            evidence_refs=refs,
            calculated_result={
                "dynamic_claim_permitted": True,
                "resolvable_tensor_parameters": 4,
                "total_tensor_parameters": 6,
                "stress_tensor_emitted": None,
                "note": "GEOX does not emit the tensor; it reports that the tier is reachable.",
            },
            gate_type="hard_epistemic",
        )

    return _receipt(
        "C-CEILING",
        "UNMEASURED",
        tier=TIER_DYNAMIC,
        scope="claim_only",
        reason=(
            "No DYNAMIC claim was made, and no slip vectors are present — the DYNAMIC question was "
            "not asked and could not be answered. Ceiling not breached."
        ),
        equation=_CEILING_EQUATION,
        inputs={
            "fault_slip_data_present": has_slip,
            "claimed_tier": claim_epistemic_tier or "unspecified",
        },
        thresholds=threshold_map,
        evidence_refs=refs,
        calculated_result={"dynamic_claim_permitted": False, "stress_tensor_emitted": None},
        gate_type="hard_epistemic",
    )


def _gate_axis_c_calibration(*, domain: str, velocity_model: dict[str, Any] | None) -> dict[str, Any]:
    """C-CALIBRATION — depth/velocity correction precedes ANY strike or azimuth claim."""
    dom = str(domain or "").strip().lower()
    vm = bool(velocity_model)
    permitted = (dom == "depth") or vm
    return _receipt(
        "C-CALIBRATION",
        "PASS" if permitted else "UNMEASURED",
        tier=TIER_KINEMATIC,
        scope="measurement",
        reason=(
            "depth domain and/or velocity model supplied — strike/azimuth claims permitted"
            if permitted
            else "Strikes were read on a TIME section with no velocity model. A strike read from a time "
                 "slice without velocity correction is meaningless: the time-to-depth mapping stretches "
                 "and rotates apparent geometry, so no azimuth claim may be emitted."
        ),
        equation="strike_claim permitted <=> (domain == depth) OR (velocity model applied); time != depth",
        inputs={"domain": dom or None, "velocity_model_present": vm},
        thresholds={"permitted_domains": ["depth"], "alternate_satisfier": "velocity_model"},
        evidence_refs=[
            "Time-to-depth conversion requires an interval velocity field",
            "Apparent dip: tan(theta_apparent) = tan(theta_true) * cos(angle to section)",
        ],
        missing_inputs=[] if permitted else ["domain=depth OR velocity_model"],
        calculated_result={"strike_claim_permitted": permitted},
        findings=[{
            "verdict": "PASS" if permitted else "UNMEASURED",
            "note": "Determinism is reproducibility; it is not dimensional truth. A reproducible "
                    "time-domain azimuth is still a wrong azimuth.",
        }],
        gate_type="hard_epistemic",
    )


def _spatial_rotation_subgate(
    measured: list[dict[str, Any]],
    *,
    min_per_half: int,
    rotation_tolerance_deg: float,
) -> dict[str, Any]:
    """C-SPATIAL — split-half mode azimuth comparison: a rotation detector, not a verdict."""
    eq = "split-half axial mean azimuth difference > tolerance => enumerate BLOCK ROTATION; never 'regime changed'"
    positioned = [f for f in measured if f.get("x") is not None]
    if len(positioned) < 2 * min_per_half:
        return _receipt(
            "C-SPATIAL",
            "UNMEASURED",
            tier=TIER_KINEMATIC,
            scope="population_spatial",
            coverage=round(len(positioned) / len(measured), 4) if measured else None,
            reason=(
                f"{len(positioned)} faults carry a spatial position; {2 * min_per_half} are required to "
                "split into two halves at the per-mode floor. Spatial azimuth variation untested."
            ),
            equation=eq,
            inputs={"n_positioned": len(positioned), "n_measured": len(measured)},
            thresholds={"min_per_half": min_per_half, "rotation_tolerance_deg": rotation_tolerance_deg},
            missing_inputs=["faults[].x (spatial position)"],
            evidence_refs=["Block rotation vs stress-axis rotation are kinematically equivalent on a rose"],
            gate_type="soft_conditional",
        )

    xs = sorted(f["x"] for f in positioned)
    mid = xs[len(xs) // 2]
    left = [f["strike_deg"] for f in positioned if f["x"] <= mid]
    right = [f["strike_deg"] for f in positioned if f["x"] > mid]
    if len(left) < min_per_half or len(right) < min_per_half:
        return _receipt(
            "C-SPATIAL",
            "UNMEASURED",
            tier=TIER_KINEMATIC,
            scope="population_spatial",
            reason=f"split-half counts {len(left)}/{len(right)} below the per-mode floor {min_per_half}",
            equation=eq,
            thresholds={"min_per_half": min_per_half, "rotation_tolerance_deg": rotation_tolerance_deg},
            missing_inputs=["more positioned faults"],
            gate_type="soft_conditional",
        )

    m_left, _ = _axial_mean_deg(left)
    m_right, _ = _axial_mean_deg(right)
    if m_left is None or m_right is None:
        return _receipt(
            "C-SPATIAL",
            "UNMEASURED",
            tier=TIER_KINEMATIC,
            scope="population_spatial",
            reason="a split-half axial mean is undefined (uniform half)",
            equation=eq,
            gate_type="soft_conditional",
        )
    delta = _axial_diff_deg(m_left, m_right)
    rotated = delta > rotation_tolerance_deg
    return _receipt(
        "C-SPATIAL",
        "WARN" if rotated else "PASS",
        tier=TIER_KINEMATIC,
        scope="population_spatial",
        reason=(
            f"split-half mode azimuths differ by {round(delta, 2)} deg (tolerance {rotation_tolerance_deg} deg) "
            "— possible BLOCK ROTATION"
            if rotated
            else f"split-half mode azimuths agree within {round(delta, 2)} deg — no spatial rotation detected"
        ),
        equation=eq,
        inputs={"left_mode_deg": round(m_left, 4), "right_mode_deg": round(m_right, 4), "split_at_x": mid},
        thresholds={"min_per_half": min_per_half, "rotation_tolerance_deg": rotation_tolerance_deg},
        calculated_result={
            "split_half_azimuth_delta_deg": round(delta, 4),
            "possible_block_rotation": rotated,
        },
        exceptions_considered=[
            "block rotation (a rigid body rotation of the sampled crust)",
            "stress-axis rotation",
            "sampling bias: the two halves may sample different structural domains",
        ],
        findings=[{
            "verdict": "WARN" if rotated else "PASS",
            "note": "A split-half azimuth difference ENUMERATES alternatives; it never concludes "
                    "'the regime changed'.",
        }],
        gate_type="soft_conditional",
    )


def analyse_fault_orientation_population(
    faults: list[dict[str, Any]] | None = None,
    *,
    master_fault_azimuth_deg: float | None = None,
    bin_width_deg: float = DEFAULT_BIN_WIDTH_DEG,
    smoothing_bins: float = DEFAULT_SMOOTHING_BINS,
    min_population_n: int = MIN_POPULATION_N,
    min_per_mode: int = MIN_PER_MODE,
    min_mode_separation_deg: float = MIN_MODE_SEPARATION_DEG,
    min_valley_depth: float = MIN_VALLEY_DEPTH,
    riedel_tolerance_deg: float = RIEDEL_TOLERANCE_DEG,
    rotation_tolerance_deg: float = ROTATION_TOLERANCE_DEG,
    domain: str = "time",
    velocity_model: dict[str, Any] | None = None,
    fault_slip_data: list[dict[str, Any]] | None = None,
    cutoff_line_3d: bool = False,
    claim_epistemic_tier: str | None = None,
    claim_stress_tensor: bool = False,
) -> dict[str, Any]:
    """AXIS C — fault-orientation population analyser.

    Fault record keys understood (aliases accepted):
      strike_deg | strike | azimuth_deg | fault_strike_deg   (mandatory, axial)
      dip_deg | dip                                          (optional)
      x, y                                                   (optional position)
      fault_id | id                                          (optional label)

    Returns a single gate receipt (gate_id ``C-POPULATION``) whose
    ``calculated_result`` carries the rose histogram, the conjugate test, the
    acute bisector, the Andersonian cross-check and the Riedel relativity, plus
    ``sub_gates`` (C-CEILING / C-CALIBRATION / C-RIEDEL / C-SPATIAL).
    """
    rows = list(faults or [])
    bin_width = _valid_float(bin_width_deg) or DEFAULT_BIN_WIDTH_DEG
    if bin_width <= 0 or bin_width > 90:
        bin_width = DEFAULT_BIN_WIDTH_DEG
    smoothing = _valid_float(smoothing_bins)
    smoothing = DEFAULT_SMOOTHING_BINS if smoothing is None or smoothing <= 0 else smoothing

    ceiling = _gate_axis_c_ceiling(
        claim_epistemic_tier=claim_epistemic_tier,
        claim_stress_tensor=claim_stress_tensor,
        fault_slip_data=fault_slip_data,
        cutoff_line_3d=cutoff_line_3d,
    )
    calibration = _gate_axis_c_calibration(domain=domain, velocity_model=velocity_model)
    strike_claim_permitted = bool(calibration["calculated_result"]["strike_claim_permitted"])

    # ── parse ────────────────────────────────────────────────────────────────
    measured: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for i, f in enumerate(rows):
        rec = f if isinstance(f, dict) else {}
        strike: float | None = None
        for key in ("strike_deg", "strike", "azimuth_deg", "fault_strike_deg"):
            strike = _valid_float(rec.get(key))
            if strike is not None:
                break
        dip: float | None = None
        for key in ("dip_deg", "dip"):
            dip = _valid_float(rec.get(key))
            if dip is not None:
                break
        if strike is None:
            skipped.append({"index": i, "fault_id": rec.get("fault_id") or rec.get("id"), "reason": "no usable strike"})
            continue
        x = _valid_float(rec.get("x", rec.get("x_m", rec.get("trace"))))
        y = _valid_float(rec.get("y", rec.get("y_m", rec.get("line"))))
        measured.append({
            "index": i,
            "fault_id": str(rec.get("fault_id") or rec.get("id") or f"F-{i:04d}"),
            "strike_deg": round(_wrap180(strike), 6),
            "dip_deg": round(dip, 6) if dip is not None else None,
            "x": x,
            "y": y,
        })

    n_supplied = len(rows)
    coverage = round(len(measured) / n_supplied, 6) if n_supplied else 0.0

    # ── preconditions ────────────────────────────────────────────────────────
    def _finish(receipt: dict[str, Any], *, riedel_sub: dict[str, Any] | None = None,
                spatial_sub: dict[str, Any] | None = None) -> dict[str, Any]:
        # NOTE: the top-level receipt IS C-POPULATION — it is never nested inside
        # sub_gates (that would be a self-reference and would break hashing/dumps).
        subs: dict[str, Any] = {
            "C-CEILING": ceiling,
            "C-CALIBRATION": calibration,
        }
        if riedel_sub is not None:
            subs["C-RIEDEL"] = riedel_sub
        if spatial_sub is not None:
            subs["C-SPATIAL"] = spatial_sub
        # Status precedence across the axes of the question:
        #   ceiling KILL          -> KILL (a category-error claim was made)
        #   calibration UNMEASURED-> UNMEASURED (azimuth claims not permitted)
        #   population UNMEASURED -> UNMEASURED (window did not cover the question)
        #   ceiling PARTIAL       -> PARTIALLY_MEASURED (a DYNAMIC claim was attempted and refused)
        #   else                  -> the population status
        final_status = receipt["status"]
        ceiling_status = str(ceiling["status"])
        if ceiling_status == "KILL":
            final_status = "KILL"
        elif calibration["status"] == "UNMEASURED":
            final_status = "UNMEASURED"
        elif final_status == "UNMEASURED":
            final_status = "UNMEASURED"
        elif ceiling_status == "PARTIALLY_MEASURED" and final_status == "PASS":
            final_status = "PARTIALLY_MEASURED"
        receipt["sub_gates"] = _clean(subs)
        receipt["status"] = final_status
        receipt["verdict"] = final_status
        receipt["dynamic_claim_permitted"] = bool(ceiling["calculated_result"].get("dynamic_claim_permitted"))
        receipt["epistemic_tier"] = TIER_KINEMATIC
        receipt["epistemic_ceiling"] = (
            "Axis C is KINEMATIC. 2D fault-plane orientation can NEVER enter the DYNAMIC tier: a stress "
            "tensor needs slip vectors, and slip vectors need 3D cutoff-line geometry."
        )
        receipt["caveats"] = [INHERITANCE_CAVEAT, RIEDEL_CAVEAT]
        receipt["determinism"] = {
            "method": "deterministic-counting-and-circular-statistics",
            "random_seed": None,
            "note": "no randomness, no clock dependence; identical inputs -> identical receipt_hash",
        }
        _attach_caveats(receipt, [INHERITANCE_CAVEAT, RIEDEL_CAVEAT])
        receipt["receipt_hash"] = receipt_hash(receipt)
        return receipt

    common_eq = (
        "axially doubled-angle circular statistics on binned strikes (Mardia); acute bisector = "
        "mid-axis of the two dominant modes; conjugate test = two modes with separation >= "
        "min_mode_separation, a valley <= (1 - min_valley_depth) of the smaller peak, and >= "
        "min_per_mode measurements per mode"
    )
    common_refs = [
        "Mardia 1972 — Statistics of Directional Data (axial / doubled-angle treatment)",
        "Fisher 1993 — Statistical Analysis of Circular Data (mode standard error)",
        "Anderson 1951 — The Dynamics of Faulting (new-fault reference geometry)",
        "Riedel 1929 — Zur Mechanik geologischer Brucherscheinungen (R / R' shear geometry)",
        "Byerlee 1978 — friction of rock",
    ]
    common_exceptions = [
        "inherited basement fabric reactivation (low-cohesion pre-existing planes slip under any stress)",
        "overpressure / weak detachment lowering the failure angle",
        "block rotation (rigid-body) vs stress-axis rotation — kinematically equivalent on a rose",
        "oblique (non-Andersonian) stress",
        "polyphase population sampled across two tectonic events",
        "sampling bias in the picked population (seismic resolution, interpreter attention, 2D lines)",
    ]

    if n_supplied == 0:
        r = _receipt(
            "C-POPULATION", "UNMEASURED", tier=TIER_KINEMATIC, coverage=0.0,
            reason="No fault records supplied — the population question was not covered.",
            equation=common_eq,
            inputs={"n_supplied": 0, "n_measured": 0},
            thresholds={"min_population_n": min_population_n, "min_population_n_basis": MIN_N_BASIS},
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=["faults[].strike_deg"],
            calculated_result={
                "n_supplied": 0, "n_measured": 0, "strike_rose": [], "conjugate": None,
                "acute_bisector_azimuth_deg": None, "candidate_sigma1_azimuth_deg": None,
                "riedel": None, "regime_candidate": None,
            },
            gate_type="hard_epistemic",
        )
        return _finish(r)

    if coverage < 0.7:
        r = _receipt(
            "C-POPULATION", "UNMEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason=(
                f"Only {len(measured)}/{n_supplied} supplied faults carry a usable strike "
                f"(coverage {coverage}). A DEFICIT test below the 0.7 coverage floor is UNMEASURED, "
                "never a pass and never a kill."
            ),
            equation=common_eq,
            inputs={"n_supplied": n_supplied, "n_measured": len(measured), "coverage": coverage},
            thresholds={
                "coverage_floor": 0.7, "min_population_n": min_population_n,
                "min_population_n_basis": MIN_N_BASIS,
                "coverage_rule": MAX_COVER_FRACTION,
            },
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=sorted({"faults[].strike_deg"} | {"faults[].strike_deg (unusable on record)"}),
            calculated_result={
                "n_supplied": n_supplied, "n_measured": len(measured), "coverage": coverage,
                "skipped": skipped, "strike_rose": [], "conjugate": None,
                "acute_bisector_azimuth_deg": None, "candidate_sigma1_azimuth_deg": None,
                "riedel": None, "regime_candidate": None,
            },
            gate_type="hard_epistemic",
        )
        return _finish(r)

    strikes = [f["strike_deg"] for f in measured]
    rose, counts = _strike_rose(strikes, bin_width)
    smoothed = _circular_smooth(counts, smoothing)
    n_bins = counts.size

    def _base_result() -> dict[str, Any]:
        return {
            "n_supplied": n_supplied,
            "n_measured": len(measured),
            "coverage": coverage,
            "skipped": skipped,
            "bin_width_deg": bin_width,
            "n_bins": n_bins,
            "strike_rose": rose,
            "faults": measured,
            "population_axial_mean_azimuth_deg": None,
            "axial_resultant_length": None,
            "smoothed_counts": [round(float(v), 6) for v in smoothed],
            "conjugate": None,
            "acute_bisector_azimuth_deg": None,
            "obtuse_bisector_azimuth_deg": None,
            "acute_bisector_half_angle_deg": None,
            "candidate_sigma1_azimuth_deg": None,
            "candidate_sigma1_basis": None,
            "anderson_cross_check": None,
            "regime_candidate": None,
            "riedel": None,
            "stress_tensor_emitted": None,
            "absolute_or_relative": "RELATIVE_POPULATION_STATISTIC",
        }

    base = _base_result()
    mean_az, r_len = _axial_mean_deg(strikes)
    base["population_axial_mean_azimuth_deg"] = round(mean_az, 4) if mean_az is not None else None
    base["axial_resultant_length"] = r_len
    base["axial_resultant_length_note"] = (
        "concentration statistic in [0,1] (like an R-value). NOT a probability and NOT a confidence."
    )

    if not strike_claim_permitted:
        r = _receipt(
            "C-POPULATION", "UNMEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason=(
                "Strikes are present but no depth correction / velocity model was supplied. The rose "
                "COUNTS are reported as a coverage descriptor; every azimuth-domain output (bisector, "
                "Riedel relativity, candidate stress azimuth) is withheld as UNMEASURED because an "
                "azimuth read on a time section without velocity correction is meaningless."
            ),
            equation=common_eq,
            inputs={"n_measured": len(measured), "domain": domain, "velocity_model_present": bool(velocity_model)},
            thresholds={
                "min_population_n": min_population_n, "min_population_n_basis": MIN_N_BASIS,
                "bin_width_deg": bin_width, "coverage_floor": 0.7,
            },
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=["domain=depth OR velocity_model"],
            calculated_result=base,
            gate_type="hard_epistemic",
        )
        return _finish(r)

    if len(measured) < min_population_n:
        base["insufficient_population"] = True
        r = _receipt(
            "C-POPULATION", "UNMEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason=(
                f"N={len(measured)} is below the minimum statistically meaningful population "
                f"(N_min={min_population_n}). No bisector is emitted: a bisector at this N has an error "
                "bar too large to separate the conjugate reading from inherited fabric, block rotation "
                "or oblique stress. UNMEASURED means the observation window did not cover the question."
            ),
            equation=common_eq,
            inputs={"n_measured": len(measured), "n_supplied": n_supplied, "coverage": coverage},
            thresholds={
                "min_population_n": min_population_n,
                "min_population_n_basis": MIN_N_BASIS,
                "min_per_mode": min_per_mode,
                "coverage_floor": 0.7,
            },
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=["faults[].strike_deg (more measurements required)"],
            calculated_result=base,
            gate_type="hard_epistemic",
        )
        return _finish(r)

    # ── conjugate bimodality ─────────────────────────────────────────────────
    peaks = _peak_bins(smoothed)
    peak_records = sorted(
        (
            {
                "bin_index": p,
                "peak_center_deg": round((p + 0.5) * bin_width, 4),
                "peak_count_smoothed": round(float(smoothed[p]), 6),
                "peak_count_raw": int(counts[p]),
            }
            for p in peaks
        ),
        key=lambda d: (-d["peak_count_smoothed"], d["bin_index"]),
    )

    conjugate: dict[str, Any] = {
        "present": False,
        "n_peaks": len(peak_records),
        "peaks": peak_records,
        "criteria": {},
        "mode_azimuths_deg": [None, None],
        "mode_separation_deg": None,
        "valley_ratio": None,
        "valley_azimuth_deg": None,
        "reasons": [],
    }

    if len(peak_records) < 2:
        conjugate["reasons"].append(
            "fewer than two rose modes — a unimodal population has no conjugate plane pair and no acute bisector"
        )
        base["conjugate"] = conjugate
        r = _receipt(
            "C-POPULATION", "PARTIALLY_MEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason=(
                "Strike population measured but UNIMODAL — no conjugate pair. The modal azimuth must NOT "
                "be re-read as a sigma1 azimuth; a single cluster is equally consistent with an inherited "
                "fabric of one orientation."
            ),
            equation=common_eq,
            inputs={"n_measured": len(measured), "n_modes": len(peak_records)},
            thresholds={
                "min_population_n": min_population_n, "min_per_mode": min_per_mode,
                "min_mode_separation_deg": min_mode_separation_deg, "min_valley_depth": min_valley_depth,
            },
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=["a second mode did not appear at this bin width / N"],
            calculated_result=base,
            gate_type="soft_conditional",
        )
        return _finish(r)

    m1_bin = peak_records[0]["bin_index"]
    m1_center = peak_records[0]["peak_center_deg"]
    m2_rec = None
    for rec in peak_records[1:]:
        if _axial_diff_deg(rec["peak_center_deg"], m1_center) >= min_mode_separation_deg:
            m2_rec = rec
            break

    if m2_rec is None:
        conjugate["reasons"].append(
            f"the second mode lies within {min_mode_separation_deg} deg of the first — separation is not "
            "resolvable at this bin width / N"
        )
        base["conjugate"] = conjugate
        r = _receipt(
            "C-POPULATION", "PARTIALLY_MEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason=(
                "Rose has more than one local maximum but no SECOND mode separated by the minimum "
                "angular distance. No conjugate set is resolvable — no bisector is emitted."
            ),
            equation=common_eq,
            inputs={"n_measured": len(measured), "n_modes": len(peak_records)},
            thresholds={
                "min_mode_separation_deg": min_mode_separation_deg, "min_per_mode": min_per_mode,
                "min_population_n": min_population_n,
            },
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=["larger N or finer bin width to resolve the second mode"],
            calculated_result=base,
            gate_type="soft_conditional",
        )
        return _finish(r)

    m1, n_m1 = _refine_peak_azimuth(strikes, m1_center, window_deg=bin_width)
    m2, n_m2 = _refine_peak_azimuth(strikes, m2_rec["peak_center_deg"], window_deg=bin_width)
    if m1 is None or m2 is None:
        conjugate["reasons"].append("mode refinement produced no members inside the peak window")
        base["conjugate"] = conjugate
        r = _receipt(
            "C-POPULATION", "PARTIALLY_MEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason="Mode refinement failed — the modes are not populated enough to refine. Bisector withheld.",
            equation=common_eq,
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            calculated_result=base,
            gate_type="soft_conditional",
        )
        return _finish(r)

    separation = _axial_diff_deg(m1, m2)
    vmin, v_az = _valley_ratio(smoothed, m1_bin, m2_rec["bin_index"])
    smaller_peak = min(peak_records[0]["peak_count_smoothed"], m2_rec["peak_count_smoothed"])
    valley_ratio = round(vmin / smaller_peak, 6) if (vmin is not None and smaller_peak > 0) else None
    # Decisive support statistic = measurements within +/- 1 bin of the peak (the mode's
    # angular support). A single bin's raw count is hostage to bin-edge effects, so it is
    # reported as a diagnostic rather than used as the gate criterion.
    counts_ok = n_m1 >= min_per_mode and n_m2 >= min_per_mode
    separation_ok = separation >= min_mode_separation_deg and separation < 90.0 - 1e-9
    valley_ok = valley_ratio is not None and valley_ratio <= (1.0 - min_valley_depth)

    conjugate.update({
        "mode_azimuths_deg": [round(m1, 4), round(m2, 4)],
        "mode_support_counts": [n_m1, n_m2],
        "mode_separation_deg": round(separation, 4),
        "valley_ratio": valley_ratio,
        "valley_azimuth_deg": round(v_az, 4) if v_az is not None else None,
        "criteria": {
            "separation_ge_min": {"value": round(separation, 4), "threshold": min_mode_separation_deg, "ok": separation_ok},
            "valley_le_threshold": {
                "value": valley_ratio, "threshold": round(1.0 - min_valley_depth, 4), "ok": valley_ok,
                "definition": "valley / smaller_peak on the short arc between the two modes",
            },
            "mode_support_ge_min_per_mode": {
                "value": sorted([n_m1, n_m2]), "threshold": min_per_mode, "ok": counts_ok,
                "definition": f"measurements within +/- {bin_width} deg of each refined mode azimuth",
            },
            "raw_peak_bin_counts_diagnostic": {
                "value": sorted([peak_records[0]["peak_count_raw"], m2_rec["peak_count_raw"]]),
                "note": "single-bin counts, reported for audit only — bin-edge effects make them a poor "
                        "support statistic at small N",
            },
        },
    })

    if not (separation_ok and valley_ok and counts_ok):
        if not separation_ok:
            conjugate["reasons"].append(
                "mode separation is either below the minimum or exactly perpendicular (90 deg), where no "
                "unique acute bisector exists"
            )
        if not valley_ok:
            conjugate["reasons"].append(
                "the valley between the modes does not fall to the required depth — the two maxima are not "
                "statistically separated at this N"
            )
        if not counts_ok:
            conjugate["reasons"].append(
                f"at least one mode carries fewer than {min_per_mode} measurements — a single-measurement "
                "'mode' is noise"
            )
        base["conjugate"] = conjugate
        r = _receipt(
            "C-POPULATION", "PARTIALLY_MEASURED", tier=TIER_KINEMATIC, coverage=coverage,
            reason=(
                "Population measured; the CONJUGATE test did not survive. No bisector is emitted — an "
                "unsurvived conjugate test is a DEFICIT, so it can never KILL, only return partial. "
                "Reasons: " + "; ".join(conjugate["reasons"])
            ),
            equation=common_eq,
            inputs={"n_measured": len(measured), "n_modes": len(peak_records), "coverage": coverage},
            thresholds={
                "min_mode_separation_deg": min_mode_separation_deg, "min_per_mode": min_per_mode,
                "min_valley_depth": min_valley_depth, "min_population_n": min_population_n,
            },
            exceptions_considered=common_exceptions,
            evidence_refs=common_refs,
            missing_inputs=["a second conjugate mode that survives separation + valley + count tests"],
            calculated_result=base,
            gate_type="soft_conditional",
        )
        return _finish(r)

    # ── bisector ─────────────────────────────────────────────────────────────
    bis = _acute_bisector_deg(m1, m2)
    conjugate["present"] = True
    base["conjugate"] = conjugate
    base["acute_bisector_azimuth_deg"] = bis["acute_bisector_azimuth_deg"]
    base["obtuse_bisector_azimuth_deg"] = bis["obtuse_bisector_azimuth_deg"]
    base["acute_bisector_half_angle_deg"] = bis["half_angle_deg"]
    base["acute_bisector_note"] = bis["note"]

    # ── Andersonian cross-check (regime candidate from dips) ────────────────
    dips = [f["dip_deg"] for f in measured if f["dip_deg"] is not None]
    regime_candidate: str | None = None
    anderson: dict[str, Any] = {
        "n_dips": len(dips),
        "mean_dip_deg": round(sum(dips) / len(dips), 4) if dips else None,
        "nearest_reference": None,
        "deviation_deg": None,
        "within_tolerance": None,
        "tolerance_deg": COULOMB_TOLERANCE_DEG,
        "reachability_note": (
            "The three Andersonian reference dips are 30 deg apart, so the distance to the NEAREST "
            "reference can never exceed 15 deg for a mean dip in [15, 105] deg. The only geometrically "
            "reachable non-Andersonian population is therefore a LOW-ANGLE one (mean dip below 15 deg) — "
            "which is exactly the detachment / weak-substrate / overpressure signature, not a different "
            "stress regime."
        ),
        "alternatives_if_outside_tolerance": [
            "inherited basement fabric (pre-existing planes), reactivated",
            "overpressure / weak substrate lowering the effective friction angle",
            "low-angle detachments — not new Andersonian faults in isotropic rock",
            "block rotation (rigid-body) rather than a new stress field",
            "oblique (non-Andersonian) stress",
            "apparent dips measured on a section oblique to the fault, or on an uncalibrated display",
        ],
    }
    if not dips:
        anderson["status"] = "UNMEASURED"
        anderson["missing_inputs"] = ["faults[].dip_deg"]
    else:
        mean_dip = anderson["mean_dip_deg"]
        nearest = min(ANDERSON_REFERENCE, key=lambda k: abs(mean_dip - ANDERSON_REFERENCE[k]["expected_dip_deg"]))
        dev = abs(mean_dip - ANDERSON_REFERENCE[nearest]["expected_dip_deg"])
        anderson["nearest_reference"] = nearest
        anderson["deviation_deg"] = round(dev, 4)
        anderson["within_tolerance"] = bool(dev <= COULOMB_TOLERANCE_DEG)
        if dev <= COULOMB_TOLERANCE_DEG:
            regime_candidate = nearest
            anderson["status"] = "PASS"
        else:
            anderson["status"] = "WARN"
            anderson["conclusion"] = (
                "the mean dip lies outside every Andersonian reference geometry. This is NOT evidence "
                "that the regime changed — it is evidence that this population is not a NEW-fault "
                "Andersonian one. Enumerate the alternatives; do not conclude 'regime changed'."
            )

    base["anderson_cross_check"] = anderson
    base["regime_candidate"] = regime_candidate

    modal_strike, _ = _axial_mean_deg(strikes)
    perp = _wrap180(modal_strike + 90.0) if modal_strike is not None else None
    mandate_applicable = regime_candidate in ("normal", "thrust")
    base["candidate_sigma1_azimuth_deg"] = (
        base["acute_bisector_azimuth_deg"] if mandate_applicable else None
    )
    base["candidate_sigma1_basis"] = (
        (
            "acute bisector azimuth of the conjugate strike population (map-view bisector). Reported as a "
            "CANDIDATE because a strike population constrains only the horizontal projection of the stress "
            "axes — it resolves no dip and no tensor."
        )
        if mandate_applicable
        else (
            "not emitted: no dip population supports a normal or thrust regime candidate "
            "(Andersonian reference geometry withheld)"
        )
    )
    anderson_relation: dict[str, Any] = {
        "modal_strike_azimuth_deg": round(modal_strike, 4) if modal_strike is not None else None,
        "strike_perpendicular_azimuth_deg": round(perp, 4) if perp is not None else None,
        "regime_candidate": regime_candidate,
        "per_regime_axis_readings": {
            "normal": {
                "derivation": "normal faults strike perpendicular to sigma3 (extension)",
                "constrained_axis": "sigma3 azimuth = modal strike +/- 90 deg",
                "sigma1": "vertical — no map-view azimuth exists for a vertical axis",
            },
            "thrust": {
                "derivation": "thrusts strike perpendicular to sigma1 (shortening)",
                "constrained_axis": "sigma1 azimuth = modal strike +/- 90 deg",
                "sigma3": "vertical",
            },
            "strike_slip": {
                "derivation": "conjugate vertical faults at ~+/-30 deg to sigma1",
                "constrained_axis": "sigma1 azimuth = acute bisector of the conjugate strike pair",
                "sigma2": "vertical",
            },
        },
        "divergence_note": (
            "The acute bisector of a MAP-VIEW strike pair is geometrically the sigma1 azimuth for a "
            "strike-slip conjugate system (sigma2 vertical). For a normal or thrust regime the conjugate "
            "pair is defined in the sigma1-sigma3 plane (opposing DIP directions), so the map-view strike "
            "bisector and the Andersonian axis reading are DIFFERENT constructions of the same geometry. "
            "Both are reported; neither is a tensor."
        ),
    }
    base["anderson_cross_check"] = {**anderson, "per_regime_axis_readings": anderson_relation["per_regime_axis_readings"],
                                    "modal_strike_azimuth_deg": anderson_relation["modal_strike_azimuth_deg"],
                                    "strike_perpendicular_azimuth_deg": anderson_relation["strike_perpendicular_azimuth_deg"],
                                    "divergence_note": anderson_relation["divergence_note"]}

    # ── Riedel relativity against a supplied master azimuth ─────────────────
    master = _valid_float(master_fault_azimuth_deg)
    riedel_sub: dict[str, Any] | None = None
    if master is None:
        riedel_sub = _receipt(
            "C-RIEDEL", "NOT_APPLICABLE", tier=TIER_KINEMATIC, scope="population_relativity",
            coverage=coverage,
            reason="No master_fault_azimuth_deg supplied — synthetic/antithetic relativity is undefined.",
            equation="delta = axial angle from master; R ~15 deg synthetic, P ~10-15 deg synthetic, R' ~75 deg antithetic",
            thresholds=dict(RIEDEL_REFERENCE_DEG, tolerance_deg=riedel_tolerance_deg),
            missing_inputs=["master_fault_azimuth_deg"],
            evidence_refs=["Riedel 1929 — shear experiments (R / R' / P shear geometry)"],
            gate_type="soft_conditional",
        )
    else:
        rows_out: list[dict[str, Any]] = []
        class_counts = {"R": 0, "R_prime": 0, "P": 0, "unclassified": 0}
        for f in measured:
            d = _axial_diff_deg(f["strike_deg"], master)
            cls = _classify_riedel(d, riedel_tolerance_deg)
            rows_out.append({"fault_id": f["fault_id"], "strike_deg": f["strike_deg"], **cls})
            if cls["riedel_primary"]:
                class_counts[cls["riedel_primary"]] += 1
            else:
                class_counts["unclassified"] += 1
        n_classified = len(measured) - class_counts["unclassified"]
        r_cov = round(n_classified / len(measured), 6) if measured else 0.0
        pattern_present = (class_counts["R"] > 0 and class_counts["R_prime"] > 0)
        if n_classified == 0:
            status, reason = "UNMEASURED", (
                "Master azimuth supplied but NO fault falls inside any Riedel window. This is a DEFICIT "
                "and may only return UNMEASURED — absence of Riedel shears never kills the structure."
            )
        elif n_classified == 1 or not pattern_present:
            status, reason = "PARTIALLY_MEASURED", (
                f"{n_classified}/{len(measured)} faults fall in a Riedel window (coverage {r_cov}); the "
                "conjugate synthetic+antithetic PAIR is not established. Coverage fraction carried; "
                "below the 0.7 floor this stays partial."
            )
        else:
            status, reason = "PASS", (
                f"{n_classified}/{len(measured)} faults fall in a Riedel window with both synthetic and "
                "antithetic families present (coverage {r_cov})."
            )
        riedel_sub = _receipt(
            "C-RIEDEL", status, tier=TIER_KINEMATIC, scope="population_relativity", coverage=r_cov,
            reason=reason,
            equation="delta = axial angular difference from the master azimuth; R ~15 deg (synthetic), P ~10-15 deg (synthetic), R' ~75 deg (antithetic)",
            inputs={
                "master_fault_azimuth_deg": round(_wrap180(master), 4),
                "n_measured": len(measured),
                "n_classified": n_classified,
                "class_counts": class_counts,
            },
            thresholds={**RIEDEL_REFERENCE_DEG, "tolerance_deg": riedel_tolerance_deg,
                        "coverage_floor": 0.7, "coverage_rule": MAX_COVER_FRACTION},
            exceptions_considered=[
                "R and P windows overlap at ~15 deg — both are synthetic and may be reported for one fault",
                "a Riedel family requires the master fault to be identified independently of this population",
                "inherited fabric can mimic the Riedel angles without a master-linked shear system",
            ],
            evidence_refs=["Riedel 1929 — shear experiments", "Wilcox, Harding & Seely 1973 — wrench tectonics"],
            missing_inputs=[] if n_classified else ["faults within a Riedel window of the master azimuth"],
            calculated_result={
                "master_fault_azimuth_deg": round(_wrap180(master), 4),
                "per_fault": rows_out,
                "class_counts": class_counts,
                "conjugate_pair_present": bool(pattern_present),
                "synthetic_vs_antithetic": {
                    "synthetic": ["R", "P"],
                    "antithetic": ["R_prime"],
                },
            },
            findings=[{"verdict": status, "caveat": RIEDEL_CAVEAT}],
            gate_type="soft_conditional",
        )
        base["riedel"] = {
            "master_fault_azimuth_deg": round(_wrap180(master), 4),
            "per_fault": rows_out,
            "class_counts": class_counts,
            "conjugate_pair_present": bool(pattern_present),
        }

    spatial_sub = _spatial_rotation_subgate(
        measured, min_per_half=max(3, min_per_mode), rotation_tolerance_deg=rotation_tolerance_deg
    )

    # ── status ───────────────────────────────────────────────────────────────
    if regime_candidate is None:
        status = "WARN"
        reason = (
            f"Conjugate set confirmed (modes {round(m1, 2)} / {round(m2, 2)} deg, separation "
            f"{round(separation, 2)} deg, valley ratio {valley_ratio}). Acute bisector azimuth = "
            f"{base['acute_bisector_azimuth_deg']} deg, half-angle {base['acute_bisector_half_angle_deg']} deg. "
            "WARN: no dip population supports a normal/thrust/thrust-slip regime candidate, or the mean dip "
            "deviates from the Andersonian reference beyond the Coulomb tolerance — the deviation is NOT "
            "evidence of a changed regime."
        )
    else:
        status = "PASS"
        reason = (
            f"Conjugate set confirmed (modes {round(m1, 2)} / {round(m2, 2)} deg, separation "
            f"{round(separation, 2)} deg, valley ratio {valley_ratio}) with a {regime_candidate} regime "
            f"candidate (mean dip {anderson['mean_dip_deg']} deg, deviation "
            f"{anderson['deviation_deg']} deg from the Andersonian reference). Acute bisector azimuth = "
            f"{base['acute_bisector_azimuth_deg']} deg. Carried as a CANDIDATE azimuth only."
        )

    r = _receipt(
        "C-POPULATION", status, tier=TIER_KINEMATIC, coverage=coverage,
        reason=reason,
        equation=common_eq,
        inputs={
            "n_measured": len(measured),
            "n_supplied": n_supplied,
            "bin_width_deg": bin_width,
            "smoothing_bins": smoothing,
            "domain": domain,
            "velocity_model_present": bool(velocity_model),
        },
        thresholds={
            "min_population_n": min_population_n,
            "min_population_n_basis": MIN_N_BASIS,
            "min_per_mode": min_per_mode,
            "min_mode_separation_deg": min_mode_separation_deg,
            "min_valley_depth": min_valley_depth,
            "coverage_floor": 0.7,
            "anderson_tolerance_deg": COULOMB_TOLERANCE_DEG,
            "riedel_reference_deg": RIEDEL_REFERENCE_DEG,
            "riedel_tolerance_deg": riedel_tolerance_deg,
        },
        exceptions_considered=common_exceptions,
        evidence_refs=common_refs,
        missing_inputs=(
            []
            if regime_candidate is not None
            else (["faults[].dip_deg"] if not dips else ["a dip population consistent with the Andersonian reference"])
        ),
        calculated_result=base,
        gate_type="soft_conditional",
    )
    return _finish(r, riedel_sub=riedel_sub, spatial_sub=spatial_sub)


# ── AXIS D ───────────────────────────────────────────────────────────────────

_BEDS = {"strata", "foreset", "amplitude_ridge", "ridge", "bed", None}
_FAULTS = {"fault", "fault_trace", "fault_plane"}


def _points_of(surface: dict[str, Any]) -> list[tuple[float, float]]:
    raw = surface.get("points") or surface.get("trace") or surface.get("path") or []
    pts: list[tuple[float, float]] = []
    for p in raw:
        if isinstance(p, dict):
            x = _valid_float(p.get("x", p.get("x_m")))
            z = _valid_float(p.get("z", p.get("z_m", p.get("y"))))
        else:
            try:
                x = _valid_float(p[0])
                z = _valid_float(p[1])
            except (TypeError, IndexError):
                x, z = None, None
        if x is None or z is None:
            continue
        pts.append((float(x), float(z)))
    pts.sort(key=lambda t: t[0])
    return pts


def _slope_deg(p1: tuple[float, float], p2: tuple[float, float]) -> float | None:
    dx = p2[0] - p1[0]
    if abs(dx) < 1e-12:
        return None
    return math.degrees(math.atan2(p2[1] - p1[1], dx))


def _terminal_dip_deg(pts: list[tuple[float, float]], end: str) -> float | None:
    """Section dip of the segment adjacent to the terminating end."""
    if len(pts) < 2:
        return None
    if end == "first":
        return _slope_deg(pts[0], pts[1])
    return _slope_deg(pts[-2], pts[-1])


def _ref_dip_at_deg(pts: list[tuple[float, float]], x: float) -> float | None:
    """Section dip of the reference surface in the segment nearest x."""
    if len(pts) < 2:
        return None
    best = None
    best_d = None
    for i in range(len(pts) - 1):
        x0, x1 = pts[i][0], pts[i + 1][0]
        lo, hi = min(x0, x1), max(x0, x1)
        d = 0.0 if lo <= x <= hi else min(abs(x - lo), abs(x - hi))
        if best_d is None or d < best_d:
            best_d = d
            best = _slope_deg(pts[i], pts[i + 1])
    return best


def _apparent_dip_deg(surface: dict[str, Any], section_azimuth_deg: float | None) -> tuple[float | None, str | None]:
    """Apparent dip in the section from a map dip + map dip direction (tangent approx).

    tan(apparent) = tan(true_dip) * cos(dip_azimuth - section_azimuth). The sign is the
    dip direction resolved along the section trace (+ means toward increasing x).
    """
    dip = _valid_float(surface.get("dip_deg", surface.get("dip")))
    az = _valid_float(surface.get("dip_azimuth_deg", surface.get("dip_direction_deg", surface.get("dip_azimuth"))))
    if dip is None or az is None or section_azimuth_deg is None:
        return None, None
    if abs(dip) >= 90.0:
        return None, "dip >= 90 deg is not a dip"
    ang = math.radians(az - section_azimuth_deg)
    app = math.degrees(math.atan(math.tan(math.radians(dip)) * math.cos(ang)))
    return app, "map dip + dip direction projected onto the section trace"


def _point_to_polyline_distance(p: tuple[float, float], pts: list[tuple[float, float]]) -> float | None:
    if len(pts) < 2:
        return None
    px, pz = p
    best = None
    for i in range(len(pts) - 1):
        x0, z0 = pts[i]
        x1, z1 = pts[i + 1]
        dx, dz = x1 - x0, z1 - z0
        den = dx * dx + dz * dz
        if den <= 0:
            continue
        t = ((px - x0) * dx + (pz - z0) * dz) / den
        t = min(1.0, max(0.0, t))
        cx, cz = x0 + t * dx, z0 + t * dz
        d = math.hypot(px - cx, pz - cz)
        if best is None or d < best:
            best = d
    return best


def _default_contact_tolerance(pts: list[tuple[float, float]]) -> float:
    """Half of the reference surface's median vertical sampling quantum.

    The vertical sample spacing is the physical contact resolution: two curves
    within half a sample are the same surface at this resolution. A caller who
    knows better passes contact_tolerance explicitly.
    """
    if len(pts) < 2:
        return 1e-6
    dz = [abs(pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    dz = [d for d in dz if d > 0]
    if not dz:
        return 1e-6
    return max(1e-9, 0.5 * float(np.median(dz)))


def _overlap_eval(
    bed: list[tuple[float, float]],
    ref: list[tuple[float, float]],
    contact_tol: float,
) -> dict[str, Any]:
    """Gap profile of a bed against a reference surface, in the section frame.

    gap(x) = z_ref(x) - z_bed(x).  gap > 0 => the bed lies ABOVE the reference.
    """
    rx = np.asarray([p[0] for p in ref], dtype=float)
    rz = np.asarray([p[1] for p in ref], dtype=float)
    bx = np.asarray([p[0] for p in bed], dtype=float)
    bz = np.asarray([p[1] for p in bed], dtype=float)
    if rx.size < 2 or bx.size < 2 or np.any(np.diff(rx) < 0):
        return {"ok": False, "reason": "reference surface is not x-monotone; gap profile undefined"}
    inside = (bx >= rx[0]) & (bx <= rx[-1])
    if int(inside.sum()) < 2:
        return {"ok": False, "reason": "bed does not overlap the reference x-range"}
    idx = np.where(inside)[0]
    i0, i1 = int(idx[0]), int(idx[-1])
    zr = np.interp(bx[i0:i1 + 1], rx, rz)
    gaps = zr - bz[i0:i1 + 1]
    return {
        "ok": True,
        "i0": i0,
        "i1": i1,
        "gaps": gaps,
        "x_sub": bx[i0:i1 + 1],
        "z_sub": bz[i0:i1 + 1],
        "z_ref_sub": zr,
        "max_abs_gap": float(np.max(np.abs(gaps))),
        "contact_tol": contact_tol,
    }


# ── AXIS D — amplitude-ridge adapter (reuses the classical primitives) ───────


def surfaces_from_amplitude_ridges(
    image: np.ndarray,
    *,
    sigma: float = 1.0,
    threshold: float = 0.5,
) -> list[dict[str, Any]]:
    """Adapt classical ridge_extraction + structure_tensor into Axis D surfaces.

    REUSE ONLY — the sampling, merging and dip primitives live in
    ``geox_mcp.tools.seismic_classical`` and are not reimplemented here. x = trace
    index, z = sample index, matching the [x, z] convention of Axis D.
    """
    from geox_mcp.tools.seismic_classical import ridge_extraction, structure_tensor

    tens = structure_tensor(np.asarray(image), sigma=sigma)
    dip = tens["dip_rad"]
    out: list[dict[str, Any]] = []
    for ridge in ridge_extraction(np.asarray(image), sigma=sigma, threshold=threshold):
        pts_raw = ridge.get("points") or []
        pts: list[tuple[float, float]] = []
        seg_dips: list[float] = []
        for p in pts_raw:
            x = int(min(max(round(float(p[0])), 0), dip.shape[1] - 1))
            z = int(min(max(round(float(p[1])), 0), dip.shape[0] - 1))
            pts.append((float(p[0]), float(p[1])))
            seg_dips.append(math.degrees(float(dip[z, x])))
        pts.sort(key=lambda t: t[0])
        out.append({
            "surface_id": str(ridge.get("ridge_id") or f"RIDGE-{len(out):04d}"),
            "kind": "amplitude_ridge",
            "points": pts,
            "points_provenance": "ridge_extraction (seismic_classical) — trace/sample indices",
            "structure_tensor_dip_deg": round(float(np.median(seg_dips)), 4) if seg_dips else None,
            "structure_tensor_dip_note": "local structure-tensor dip in SECTION coordinates, in degrees",
        })
    return out


def classify_stratal_terminations(
    reference_surface: dict[str, Any] | None = None,
    underlying_surfaces: list[dict[str, Any]] | None = None,
    *,
    faults: list[dict[str, Any]] | None = None,
    section_azimuth_deg: float | None = None,
    contact_tolerance: float | None = None,
    concordance_tolerance_deg: float = DEFAULT_CONCORDANCE_TOLERANCE_DEG,
    toplap_max_angle_deg: float = DEFAULT_TOPLAP_MAX_ANGLE_DEG,
    min_terminal_dip_deg: float = MIN_HALF_DIP_FOR_STRATA_SENSE,
    zero_offset_threshold_m: float = DEFAULT_ZERO_OFFSET_THRESHOLD_M,
    domain: str = "depth",
    velocity_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """AXIS D — stratal-termination classifier.

    Inputs
    ------
    reference_surface : the surface the strata terminate against (mandatory).
    underlying_surfaces : beds / foresets / amplitude ridges. Each record:
        surface_id, kind ("strata" | "foreset" | "amplitude_ridge"), points [[x, z], ...],
        and OPTIONALLY dip_deg + dip_azimuth_deg (the local dip direction, projected
        onto the section via ``section_azimuth_deg``).
    faults : fault traces (kind "fault"), each with points and offset_m / throw_m.
        A bed that abuts a fault is handled by the SYNCHRONOUS pitfall rule, never
        by the lap classifier.

    Returns a gate receipt (gate_id ``D-STRATAL-TERMINATION``) with per-termination
    classification, termination coordinates, and a RELATIVE partial-order chronology.
    Absolute age is never emitted.
    """
    ref = dict(reference_surface or {}) if isinstance(reference_surface, dict) else {}
    ref_pts = _points_of(ref)
    beds_in = [s for s in (underlying_surfaces or []) if isinstance(s, dict)]
    fault_in = [s for s in (faults or []) if isinstance(s, dict)]
    fault_in += [s for s in beds_in if str(s.get("kind", "")).lower() in _FAULTS and s not in fault_in]
    beds = [s for s in beds_in if str(s.get("kind", "")).lower() not in _FAULTS]

    ctol = _valid_float(contact_tolerance)
    if ctol is None or ctol <= 0:
        ctol = _default_contact_tolerance(ref_pts)
    ctol_source = "supplied" if _valid_float(contact_tolerance) else "derived: 0.5 x median |dz| of the reference surface (the vertical sampling quantum)"

    sec_az = _valid_float(section_azimuth_deg)

    base_eq = (
        "gap(x) = z_ref(x) - z_bed(x); side = sign(gap) inside the bed's range at the termination; "
        "t = sign(a_bed - a_ref) = the x-direction in which the bed converges; lap class = t vs the "
        "reference's dip direction d_ref; top class = |a_bed - a_ref| vs the concordance and toplap ceilings"
    )
    base_refs = [
        "Mitchum, Vail & Thompson 1977 — Seismic stratigraphy and global changes of sea level (lap taxonomy)",
        "Vail, Mitchum & Thompson 1977 — coastal onlap / downlap / toplap definitions",
        "Mitchum & Vail 1977 — erosional truncation and the type-1/type-2 sequence boundary usage",
        "Steno 1669 / Hutton 1795 / Lyell 1830 — superposition and cross-cutting for relative chronology",
        "Emery & Myers 1996 — Sequence Stratigraphy (toplap = low-angle non-erosional convergence)",
    ]
    base_exceptions = [
        "differential compaction producing lap-like convergence with zero depositional termination",
        "sideswipe / out-of-plane energy producing a false termination on a 2D line",
        "oblique section obliquity: a true downlap can appear concordant if the section runs along the dip",
        "fault drag / collapse causing an apparent angular discordance next to a fault plane",
        "picking bias: a tracker snapping to the wrong event at a convergence",
        "erosion vs non-deposition are geometrically identical (see the erosion caveat)",
    ]

    def _finish(receipt: dict[str, Any], *, pitfall: dict[str, Any] | None = None) -> dict[str, Any]:
        receipt["epistemic_tier"] = TIER_KINEMATIC
        receipt["epistemic_ceiling"] = (
            "Axis D is KINEMATIC. Terminations give a RELATIVE partial order only. Absolute age requires "
            "biostratigraphy or geochronology and is NEVER emitted from geometry."
        )
        receipt["caveats"] = [RELATIVE_CHRONOLOGY_CAVEAT, EROSION_INTERPRETATION_CAVEAT, FAULT_ABUT_PITFALL]
        receipt["determinism"] = {
            "method": "deterministic-polyline-contact-geometry",
            "random_seed": None,
            "note": "no randomness, no clock dependence; identical inputs -> identical receipt_hash",
        }
        if pitfall is not None:
            receipt["pitfall_flags"] = pitfall
        _attach_caveats(receipt, [RELATIVE_CHRONOLOGY_CAVEAT, EROSION_INTERPRETATION_CAVEAT, FAULT_ABUT_PITFALL])
        receipt["receipt_hash"] = receipt_hash(receipt)
        return receipt

    if len(ref_pts) < 2:
        r = _receipt(
            "D-STRATAL-TERMINATION", "UNMEASURED", tier=TIER_KINEMATIC, coverage=0.0,
            reason="No usable reference surface (>= 2 points required) — no termination can be measured.",
            equation=base_eq,
            inputs={"n_reference_points": len(ref_pts), "n_beds": len(beds), "n_faults": len(fault_in)},
            thresholds={"contact_tolerance": ctol, "contact_tolerance_source": ctol_source},
            exceptions_considered=base_exceptions,
            evidence_refs=base_refs,
            missing_inputs=["reference_surface.points"],
            calculated_result={
                "terminations": [], "classification_counts": {}, "chronology_partial_order": [],
                "absolute_age_permitted": False, "absolute_age_requires": list(ABSOLUTE_AGE_REQUIREMENT),
                "chronology_kind": "RELATIVE_PARTIAL_ORDER",
            },
            gate_type="hard_epistemic",
        )
        return _finish(r, pitfall={"zero_offset_abut_detected": False, "zero_offset_abut_never_younger": True})

    if not beds and not fault_in:
        r = _receipt(
            "D-STRATAL-TERMINATION", "UNMEASURED", tier=TIER_KINEMATIC, coverage=0.0,
            reason="Reference surface present but no underlying surfaces or faults supplied.",
            equation=base_eq,
            inputs={"n_reference_points": len(ref_pts), "n_beds": 0, "n_faults": 0},
            thresholds={"contact_tolerance": ctol, "contact_tolerance_source": ctol_source},
            exceptions_considered=base_exceptions,
            evidence_refs=base_refs,
            missing_inputs=["underlying_surfaces[].points"],
            calculated_result={
                "terminations": [], "classification_counts": {}, "chronology_partial_order": [],
                "absolute_age_permitted": False, "absolute_age_requires": list(ABSOLUTE_AGE_REQUIREMENT),
                "chronology_kind": "RELATIVE_PARTIAL_ORDER",
            },
            gate_type="hard_epistemic",
        )
        return _finish(r, pitfall={"zero_offset_abut_detected": False, "zero_offset_abut_never_younger": True})

    ref_id = str(ref.get("surface_id") or ref.get("id") or "REF")
    terminations: list[dict[str, Any]] = []
    chronology: list[dict[str, Any]] = []
    pitfall_rows: list[dict[str, Any]] = []
    evaluated_ids: set[str] = set()
    fault_consumed_ends: dict[str, set[str]] = {}
    unevaluable: list[dict[str, Any]] = []

    # ── fault abutments (the pitfall branch) ────────────────────────────────
    for bed in beds:
        sid = str(bed.get("surface_id") or bed.get("id") or f"BED-{len(terminations):04d}")
        pts = _points_of(bed)
        if len(pts) < 2:
            unevaluable.append({"surface_id": sid, "reason": "fewer than 2 points"})
            continue
        best: dict[str, Any] | None = None
        for ft in fault_in:
            fpts = _points_of(ft)
            if len(fpts) < 2:
                continue
            fid = str(ft.get("surface_id") or ft.get("id") or ft.get("fault_id") or "FAULT")
            for end, p in (("first", pts[0]), ("last", pts[-1])):
                d = _point_to_polyline_distance(p, fpts)
                if d is None or d > ctol:
                    continue
                if best is None or d < best["distance"]:
                    best = {"fault_id": fid, "distance": d, "end": end, "point": p, "fault": ft}
        if best is None:
            continue

        evaluated_ids.add(sid)
        fault_consumed_ends.setdefault(sid, set()).add(str(best["end"]))
        offset_raw = bed.get("offset_at_contact_m")
        offset = _valid_float(offset_raw)
        offset_source = "bed.offset_at_contact_m"
        if offset is None:
            fobj = best["fault"]
            for key in ("offset_m", "throw_m", "offset_at_contact_m"):
                offset = _valid_float(fobj.get(key))
                if offset is not None:
                    offset_source = f"fault.{key}"
                    break
        crosses = bool(bed.get("present_both_sides") or bed.get("crosses_fault"))

        entry: dict[str, Any] = {
            "surface_id": sid,
            "kind": str(bed.get("kind") or "strata"),
            "contact_feature": best["fault_id"],
            "contact_feature_kind": "fault",
            "distance_to_fault": round(best["distance"], 6),
            "termination_xy": [round(best["point"][0], 6), round(best["point"][1], 6)],
            "ends": best["end"],
        }

        if crosses:
            entry.update({
                "classification": "crosses_fault_zero_offset",
                "side": None,
                "relative_dip_deg": None,
                "angle_to_reference_deg": None,
                "relative_chronology": {
                    "horizon": sid, "feature": best["fault_id"],
                    "relation": "UNDETERMINED",
                    "alternatives": [
                        "fault is DEAD at this level (the horizon postdates faulting)",
                        "fault-tip / nucleation zone with no resolvable throw at this level",
                        "horizon and fault synchronous (the horizon crossed an active fault surface)",
                    ],
                },
                "note": "A horizon present on BOTH sides with no offset does not fix the fault age; the "
                        "alternatives are enumerated rather than collapsed.",
            })
        elif offset is None:
            entry.update({
                "classification": "abut_undetermined",
                "side": None,
                "relative_dip_deg": None,
                "angle_to_reference_deg": None,
                "relative_chronology": {
                    "horizon": sid, "feature": best["fault_id"], "relation": "UNDETERMINED",
                    "alternatives": ["zero offset (synchronous)", "measurable offset (the fault postdates the horizon)"],
                },
                "note": "No offset value at the contact — chronology cannot be decided from geometry alone.",
            })
        elif offset <= zero_offset_threshold_m:
            entry.update({
                "classification": "abut_synchronous",
                "side": None,
                "relative_dip_deg": None,
                "angle_to_reference_deg": None,
                "offset_at_contact_m": offset,
                "offset_source": offset_source,
                "relative_chronology": {
                    "horizon": sid, "feature": best["fault_id"],
                    "relation": "SYNCHRONOUS",
                    "means": (
                        "the horizon abutted the fault with ZERO measurable offset at the contact: the "
                        "horizon and the fault surface sat at the depositional surface together. The "
                        "horizon is NOT younger than the fault."
                    ),
                },
                "pitfall_flag": "ZERO_OFFSET_ABUT_SYNCHRONOUS",
            })
            pitfall_rows.append({"surface_id": sid, "fault_id": best["fault_id"], "relation": "SYNCHRONOUS"})
        else:
            entry.update({
                "classification": "abut_offset",
                "side": None,
                "relative_dip_deg": None,
                "angle_to_reference_deg": None,
                "offset_at_contact_m": offset,
                "offset_source": offset_source,
                "relative_chronology": {
                    "horizon": sid, "feature": best["fault_id"],
                    "relation": "HORIZON_OLDER_THAN_FAULT",
                    "means": f"the fault offsets the horizon by {offset} m at the contact — the fault postdates it",
                },
            })
        terminations.append(entry)
        if entry["relative_chronology"]["relation"] in ("SYNCHRONOUS", "HORIZON_OLDER_THAN_FAULT"):
            chronology.append({
                "older": sid if entry["relative_chronology"]["relation"] == "HORIZON_OLDER_THAN_FAULT" else best["fault_id"],
                "younger": best["fault_id"] if entry["relative_chronology"]["relation"] == "HORIZON_OLDER_THAN_FAULT" else None,
                "basis": "fault offset at contact" if entry["relative_chronology"]["relation"] == "HORIZON_OLDER_THAN_FAULT"
                         else "zero-offset abutment => synchronous (no ordering edge)",
                "relation": entry["relative_chronology"]["relation"],
            })

    # ── lap / top terminations against the reference surface ────────────────
    for bed in beds:
        sid = str(bed.get("surface_id") or bed.get("id") or f"BED-{len(terminations):04d}")
        consumed = fault_consumed_ends.get(sid, set())
        pts = _points_of(bed)
        if len(pts) < 2:
            unevaluable.append({"surface_id": sid, "reason": "fewer than 2 points"})
            continue

        ov = _overlap_eval(pts, ref_pts, ctol)
        if not ov.get("ok"):
            unevaluable.append({"surface_id": sid, "reason": ov.get("reason")})
            continue
        evaluated_ids.add(sid)

        gaps: np.ndarray = ov["gaps"]
        xs: np.ndarray = ov["x_sub"]
        zs: np.ndarray = ov["z_sub"]
        n_sub = gaps.size

        map_app, map_src = _apparent_dip_deg(bed, sec_az)

        concordant_within_tol = float(np.max(np.abs(gaps))) <= ctol
        if concordant_within_tol:
            x_t0 = float(xs[0])
            a_ref0 = _ref_dip_at_deg(ref_pts, x_t0)
            a_bed0 = _terminal_dip_deg(pts, "first")
            terminations.append({
                "surface_id": sid,
                "kind": str(bed.get("kind") or "strata"),
                "contact_feature": ref_id,
                "contact_feature_kind": "reference_surface",
                "ends": "whole",
                "termination_xy": [round(x_t0, 6), round(float(zs[0]), 6)],
                "side": None,
                "gap_inside": None,
                "gap_at_termination": round(float(gaps[0]), 6),
                "max_abs_gap_over_bed": round(float(np.max(np.abs(gaps))), 6),
                "terminal_dip_deg": round(a_bed0, 4) if a_bed0 is not None else None,
                "reference_dip_deg": round(a_ref0, 4) if a_ref0 is not None else None,
                "relative_dip_deg": round(a_bed0 - a_ref0, 4) if (a_bed0 is not None and a_ref0 is not None) else None,
                "angle_to_reference_deg": round(abs(a_bed0 - a_ref0), 4) if (a_bed0 is not None and a_ref0 is not None) else None,
                "dip_source": "section polyline geometry",
                "map_dip_apparent_deg": round(map_app, 4) if map_app is not None else None,
                "map_dip_provenance": map_src,
                "classification": "offlap_concordant",
                "classification_basis": (
                    "the bed tracks the reference surface within the contact tolerance over its WHOLE "
                    "extent — no convergence anywhere, so there is no termination point; this is "
                    "offlap-concordant"
                ),
                "boundary_contact": False,
                "relative_chronology": None,
            })
            continue

        ends_to_check: list[str] = []
        if abs(gaps[0]) <= ctol and "first" not in consumed:
            ends_to_check.append("first")
        if abs(gaps[-1]) <= ctol and n_sub > 1 and "last" not in consumed:
            ends_to_check.append("last")
        if not ends_to_check:
            unevaluable.append({
                "surface_id": sid,
                "reason": "the bed never reaches the reference surface within the contact tolerance "
                          "(no termination to classify)",
            })
            continue

        for end in ends_to_check:
            end_idx = 0 if end == "first" else n_sub - 1
            inside_idx = 1 if end == "first" else n_sub - 2
            gap_inside = float(gaps[inside_idx])
            side = "above" if gap_inside > 0 else ("below" if gap_inside < 0 else "indeterminate")
            a_bed = _terminal_dip_deg(pts, "first" if end == "first" else "last")
            if a_bed is None:
                a_bed = map_app
            x_t = float(xs[end_idx])
            a_ref = _ref_dip_at_deg(ref_pts, x_t)
            z_t = float(zs[end_idx])

            boundary_abut = abs(gap_inside) <= ctol
            entry = {
                "surface_id": sid,
                "kind": str(bed.get("kind") or "strata"),
                "contact_feature": ref_id,
                "contact_feature_kind": "reference_surface",
                "ends": end,
                "termination_xy": [round(x_t, 6), round(z_t, 6)],
                "side": side,
                "gap_inside": round(gap_inside, 6),
                "gap_at_termination": round(float(gaps[end_idx]), 6),
                "terminal_dip_deg": round(a_bed, 4) if a_bed is not None else None,
                "reference_dip_deg": round(a_ref, 4) if a_ref is not None else None,
                "relative_dip_deg": round(a_bed - a_ref, 4) if (a_bed is not None and a_ref is not None) else None,
                "angle_to_reference_deg": round(abs(a_bed - a_ref), 4) if (a_bed is not None and a_ref is not None) else None,
                "dip_source": "section polyline geometry",
                "map_dip_apparent_deg": round(map_app, 4) if map_app is not None else None,
                "map_dip_provenance": map_src,
                "classification": None,
                "classification_basis": None,
                "boundary_contact": boundary_abut,
                "relative_chronology": None,
            }

            if side == "above":
                # lap class: convergence direction vs the reference's dip direction
                dg_dx = float(gaps[min(n_sub - 1, end_idx + 1)] - gaps[max(0, end_idx - 1)]) if n_sub > 2 else \
                    float(gaps[-1] - gaps[0])
                if abs(dg_dx) < 1e-12:
                    t_dir = 0
                else:
                    t_dir = -1 if dg_dx > 0 else 1  # convergence runs opposite to gap growth
                d_ref = 0
                if a_ref is not None and abs(a_ref) >= min_terminal_dip_deg:
                    d_ref = 1 if a_ref > 0 else -1
                strata_dir = 0
                if abs(a_bed) >= min_terminal_dip_deg:
                    strata_dir = 1 if a_bed > 0 else -1
                elif map_app is not None and abs(map_app) >= min_terminal_dip_deg:
                    strata_dir = 1 if map_app > 0 else -1

                lap: str | None = None
                basis_used: str | None = None
                if d_ref != 0:
                    lap = "downlap" if t_dir == d_ref else "onlap"
                    basis_used = (
                        "convergence direction equals the reference surface's dip direction (downdip) "
                        "=> downlap" if lap == "downlap" else
                        "convergence runs opposite to the reference surface's dip direction (updip) "
                        "=> onlap"
                    )
                elif strata_dir != 0:
                    lap = "downlap" if t_dir == strata_dir else "onlap"
                    basis_used = (
                        "the reference surface is flat in section; convergence compared against the STRATA's "
                        "own dip sense => " + lap
                    )

                if lap is None:
                    entry["classification"] = "lap_undetermined"
                    entry["classification_basis"] = (
                        "both the reference surface and the strata are flat in section — the downdip "
                        "direction is not resolvable from this input"
                    )
                    unevaluable.append({
                        "surface_id": sid,
                        "reason": "flat reference and flat strata: add dip_deg + dip_azimuth_deg or "
                                  "section_azimuth_deg to resolve the downdip direction",
                    })
                    terminations.append(entry)
                    continue

                if strata_dir != 0 and d_ref != 0:
                    strata_reading = "downlap" if t_dir == strata_dir else "onlap"
                    if strata_reading != lap:
                        entry["classification"] = "onlap_or_downlap_ambiguous"
                        entry["classification_basis"] = (
                            "the surface-based and strata-based discriminators DISAGREE "
                            f"(surface => {lap}; strata dip sense => {strata_reading}). The section is "
                            "oblique or the two surfaces dip oppositely; the alternatives are enumerated "
                            "rather than collapsed."
                        )
                        entry["classification_alternatives"] = sorted({lap, strata_reading})
                        chron_ok = True
                        entry["relative_chronology"] = {
                            "horizon": sid, "feature": ref_id, "relation": "HORIZON_YOUNGER_THAN_REFERENCE",
                            "means": "beds that LAP onto the reference surface are younger than it (they "
                                     "were deposited onto an existing surface)",
                        }
                        terminations.append(entry)
                        continue

                entry["classification"] = lap
                entry["classification_basis"] = basis_used
                entry["relative_chronology"] = {
                    "horizon": sid, "feature": ref_id, "relation": "HORIZON_YOUNGER_THAN_REFERENCE",
                    "means": "beds that LAP onto the reference surface are younger than it (they were "
                             "deposited onto an existing surface)",
                }
                terminations.append(entry)
                chronology.append({
                    "older": ref_id, "younger": sid,
                    "basis": f"{lap} termination (lap beds postdate the surface they lap onto)",
                    "relation": "HORIZON_YOUNGER_THAN_REFERENCE",
                })
                continue

            # side == below or indeterminate
            if a_bed is None or a_ref is None:
                entry["classification"] = "undetermined"
                entry["classification_basis"] = "terminal dip or reference dip unresolved"
                unevaluable.append({"surface_id": sid, "reason": "terminal dip or reference dip unresolved"})
                terminations.append(entry)
                continue

            disc = abs(a_bed - a_ref)
            if disc <= concordance_tolerance_deg:
                entry["classification"] = "offlap_concordant"
                entry["classification_basis"] = (
                    f"strata below the reference are concordant within {concordance_tolerance_deg} deg "
                    f"(measured discordance {round(disc, 2)} deg) — offlap-concordant, no termination"
                )
                terminations.append(entry)
            elif disc < toplap_max_angle_deg:
                entry["classification"] = "toplap"
                entry["classification_basis"] = (
                    f"top termination below the reference with a LOW-angle discordance "
                    f"({round(disc, 2)} deg < toplap ceiling {toplap_max_angle_deg} deg): the strata built "
                    "up to the surface with no significant erosion"
                )
                entry["erosion_confirmed"] = False
                entry["relative_chronology"] = {
                    "horizon": sid, "feature": ref_id, "relation": "HORIZON_OLDER_THAN_REFERENCE",
                    "means": "strata terminating at their top below the surface predate that surface",
                }
                terminations.append(entry)
                chronology.append({
                    "older": sid, "younger": ref_id,
                    "basis": "toplap: strata below the surface terminate at their top",
                    "relation": "HORIZON_OLDER_THAN_REFERENCE",
                })
            else:
                entry["classification"] = "truncation"
                entry["classification_basis"] = (
                    f"angular discordance {round(disc, 2)} deg >= toplap ceiling {toplap_max_angle_deg} deg: "
                    "the surface cuts across the strata below (erosional truncation geometry)"
                )
                entry["erosion_confirmed"] = False
                entry["erosion_note"] = EROSION_INTERPRETATION_CAVEAT
                entry["relative_chronology"] = {
                    "horizon": sid, "feature": ref_id, "relation": "HORIZON_OLDER_THAN_REFERENCE",
                    "means": "truncated strata predate the surface that cuts them",
                }
                terminations.append(entry)
                chronology.append({
                    "older": sid, "younger": ref_id,
                    "basis": "truncation: the surface cuts the strata below",
                    "relation": "HORIZON_OLDER_THAN_REFERENCE",
                })

    # ── dip-consistency audit (map dip direction vs section geometry) ────────
    for t in terminations:
        geo = t.get("terminal_dip_deg")
        mapp = t.get("map_dip_apparent_deg")
        if geo is None or mapp is None:
            continue
        delta = abs(float(geo) - float(mapp))
        t["dip_consistency"] = {
            "geometry_deg": geo,
            "map_apparent_deg": mapp,
            "delta_deg": round(delta, 4),
            "tolerance_deg": DIP_CONSISTENCY_TOLERANCE_DEG,
            "consistent": bool(delta <= DIP_CONSISTENCY_TOLERANCE_DEG),
        }
        if delta > DIP_CONSISTENCY_TOLERANCE_DEG and t["classification"] not in CAVEAT_CLASSES:
            t["classification_candidate_geometry"] = t["classification"]
            t["classification"] = "dip_inconsistent"
            t["classification_basis"] = (
                f"the section geometry gives {geo} deg while the supplied map dip direction projects to "
                f"{mapp} deg — a {round(delta, 2)} deg disagreement beyond the "
                f"{DIP_CONSISTENCY_TOLERANCE_DEG} deg tolerance. Neither input is discarded; the "
                "classification is withheld rather than collapsed."
            )

    # ── lap-migration ordering (explicitly an INFERENCE, not geometry) ──────
    def _migration_order() -> dict[str, Any]:
        onlaps = [t for t in terminations if t.get("classification") == "onlap"]
        downlaps = [t for t in terminations if t.get("classification") == "downlap"]
        chosen = onlaps if len(onlaps) >= 2 else (downlaps if len(downlaps) >= 2 else [])
        if not chosen:
            return {"available": False, "reason": "fewer than two lap terminations of the same class"}
        d_ref = 0
        rr = _ref_dip_at_deg(ref_pts, chosen[0]["termination_xy"][0])
        if rr is not None and abs(rr) >= min_terminal_dip_deg:
            d_ref = 1 if rr > 0 else -1
        if d_ref == 0:
            return {
                "available": False,
                "reason": "the reference surface is flat in section — the downdip direction needed for a "
                          "migration ordering is not resolvable",
            }
        cls = "onlap" if chosen is onlaps else "downlap"
        key = (lambda t: t["termination_xy"][0] * d_ref)
        ordered = sorted(chosen, key=key)
        youngest_first = list(reversed(ordered)) if cls == "onlap" else ordered
        return {
            "available": True,
            "class": cls,
            "ordering_youngest_to_oldest": [t["surface_id"] for t in youngest_first],
            "assumption": (
                "INFERRED from the lap migration stacking pattern (transgression for onlap, progradation "
                "for downlap): the lap terminating farthest UPDIP is the youngest for coastal onlap; for "
                "downlap the one terminating farthest DOWNDIP is the youngest. This is an inference about "
                "process, NOT a geometric observation, and it carries no confidence value."
            ),
            "geometric_partial_order_unaffected": True,
        }

    counts: dict[str, int] = {}
    for t in terminations:
        counts[str(t["classification"])] = counts.get(str(t["classification"]), 0) + 1

    n_candidates = len(beds)
    evaluated = len(evaluated_ids)
    coverage = round(evaluated / n_candidates, 6) if n_candidates else 0.0
    n_classified = sum(
        v for k, v in counts.items() if k in (set(TERMINATION_CLASSES) | set(FAULT_CONTACT_CLASSES))
    )
    n_withheld = sum(v for k, v in counts.items() if k in CAVEAT_CLASSES)
    pitfall = {
        "zero_offset_abut_detected": bool(pitfall_rows),
        "zero_offset_abut_count": len(pitfall_rows),
        "zero_offset_abut_rows": pitfall_rows,
        "zero_offset_abut_never_younger": True,
        "rule": FAULT_ABUT_PITFALL,
    }

    if coverage < 0.7 and n_classified == 0:
        status = "UNMEASURED"
        reason = (
            f"coverage {coverage} of supplied surfaces was evaluable (below the 0.7 floor) and nothing "
            "was classified — a DEFICIT test below the coverage floor downgrades to UNMEASURED, never "
            "to a pass and never to a kill."
        )
    elif n_classified == 0 and n_withheld > 0:
        status = "PARTIALLY_MEASURED"
        reason = (
            f"{n_withheld} contact(s) were measured but NO class survived (withheld for ambiguity or "
            "input inconsistency). The geometry was covered; the class was withheld — that is partial, "
            "not UNMEASURED and not a failure."
        )
    elif n_classified == 0:
        status = "UNMEASURED"
        reason = (
            "No termination was classified. Absence of a termination is a DEFICIT, not a contradiction — "
            "it can never KILL. Either no bed reaches the reference surface within the contact tolerance, "
            "or the beds could not be evaluated (see unevaluable)."
        )
    elif coverage < 0.7:
        status = "UNMEASURED"
        reason = (
            f"coverage {coverage} of supplied surfaces was evaluable — below the 0.7 floor, so the "
            "classification set is downgraded to UNMEASURED (deficit rule)."
        )
    elif pitfall_rows or n_withheld > 0:
        status = "WARN"
        reason = (
            f"{n_classified} termination(s) classified, {n_withheld} withheld, with "
            f"{len(pitfall_rows)} zero-offset abutment(s) — caveats are carried per-termination "
            "(see CAVEAT_CLASSES entries and pitfall_flags)."
        )
    else:
        status = "PASS"
        reason = f"{n_classified} termination(s) classified against the reference surface without caveats."

    cr = {
        "reference_surface_id": ref_id,
        "section_azimuth_deg": round(sec_az, 4) if sec_az is not None else None,
        "domain": str(domain or "").lower() or None,
        "velocity_model_present": bool(velocity_model),
        "angle_basis": (
            "SECTION-APPARENT dips. Termination TOPOLOGY (which side, convergence direction) is invariant to a "
            "monotone vertical stretch; the ANGLE VALUES require depth conversion before any true-dip claim."
        ),
        "terminations": terminations,
        "n_terminations": len(terminations),
        "classification_counts": counts,
        "n_classified": n_classified,
        "n_withheld": n_withheld,
        "evaluated_surfaces": evaluated,
        "candidate_surfaces": n_candidates,
        "unevaluable": unevaluable,
        "chronology_kind": "RELATIVE_PARTIAL_ORDER",
        "chronology_partial_order": chronology,
        "partial_order_acyclic": _acyclic(chronology),
        "lap_migration_ordering": _migration_order(),
        "absolute_age_permitted": False,
        "absolute_age_requires": list(ABSOLUTE_AGE_REQUIREMENT),
        "absolute_age_note": RELATIVE_CHRONOLOGY_CAVEAT,
        "erosion_from_geometry_alone": False,
        "class_vocabulary_alignment": GEOMETRY_TYPE_ALIGNMENT,
        "time_domain_warning": (
            None
            if (str(domain or "").lower() == "depth" or velocity_model)
            else "time domain without a velocity model: section angles are NOT true dips (classification "
                 "topology still valid)"
        ),
    }

    r = _receipt(
        "D-STRATAL-TERMINATION", status, tier=TIER_KINEMATIC, coverage=coverage,
        reason=reason,
        equation=base_eq,
        inputs={
            "reference_surface_id": ref_id,
            "n_reference_points": len(ref_pts),
            "n_beds": len(beds),
            "n_faults": len(fault_in),
            "section_azimuth_deg": round(sec_az, 4) if sec_az is not None else None,
            "domain": str(domain or "").lower() or None,
        },
        thresholds={
            "contact_tolerance": round(ctol, 6),
            "contact_tolerance_source": ctol_source,
            "concordance_tolerance_deg": concordance_tolerance_deg,
            "toplap_max_angle_deg": toplap_max_angle_deg,
            "min_terminal_dip_deg": min_terminal_dip_deg,
            "zero_offset_threshold_m": zero_offset_threshold_m,
            "coverage_floor": 0.7,
        },
        exceptions_considered=base_exceptions,
        evidence_refs=base_refs,
        missing_inputs=(
            [] if status == "PASS"
            else sorted({u["reason"] for u in unevaluable}) or ["terminations reaching the reference surface"]
        ),
        calculated_result=cr,
        gate_type="soft_conditional",
    )
    return _finish(r, pitfall=pitfall)


def _acyclic(edges: list[dict[str, Any]]) -> bool:
    """Cycle check over the relative-chronology edges (older -> younger)."""
    graph: dict[str, set[str]] = {}
    for e in edges:
        older, younger = e.get("older"), e.get("younger")
        if not isinstance(older, str) or not isinstance(younger, str):
            continue
        graph.setdefault(older, set()).add(younger)

    WHITE, GREY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}
    for n in list(graph):
        for m in graph[n]:
            color.setdefault(m, WHITE)

    def visit(node: str) -> bool:
        color[node] = GREY
        for nxt in graph.get(node, ()):  # pragma: no branch
            if color.get(nxt, WHITE) == GREY:
                return False
            if color.get(nxt, WHITE) == WHITE and not visit(nxt):
                return False
        color[node] = BLACK
        return True

    for n in list(color):
        if color[n] == WHITE:
            if not visit(n):
                return False
    return True


__all__ = [
    "ABSOLUTE_AGE_REQUIREMENT",
    "ANDERSON_REFERENCE",
    "CAVEAT_CLASSES",
    "COULOMB_TOLERANCE_DEG",
    "FAULT_ABUT_PITFALL",
    "FAULT_CONTACT_CLASSES",
    "GEOMETRY_TYPE_ALIGNMENT",
    "INHERITANCE_CAVEAT",
    "MIN_N_BASIS",
    "MIN_POPULATION_N",
    "RELATIVE_CHRONOLOGY_CAVEAT",
    "TERMINATION_CLASSES",
    "analyse_fault_orientation_population",
    "classify_stratal_terminations",
    "surfaces_from_amplitude_ridges",
]