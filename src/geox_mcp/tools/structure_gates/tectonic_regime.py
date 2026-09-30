"""K-REGIME — tectonic regime falsification from horizon geometry + orientation.

Purpose
-------
Decide, from a horizon-stack observation bundle, which tectonic regimes SURVIVE
falsification and which are REJECTED — and refuse to answer where the data does
not reach.

The load-bearing doctrine (three lines, everything else elaborates them):

1. **Epistemic ceiling.** Geometry yields KINEMATICS. Restoration yields STRAIN.
   Only fault-slip inversion (with assumptions) yields DYNAMICS, and even then
   only 4 of 6 tensor parameters are resolved. A DYNAMIC claim emitted from
   horizon geometry alone is a category error — gate K-REGIME-CEILING blocks it.

2. **UNMEASURED is not a pass, and KILL needs positive evidence.** A falsifier
   that was never measured returns UNMEASURED — never PASS, never KILL. In
   particular the *absence of a growth wedge does not kill extension*: a fault
   moving slower than the sediment supply leaves no growth signature at all.
   Only a *measured* expansion index <= 1 kills the syn-tectonic claim.

3. **Non-balance is a diagnostic, not an error flag.** Failure to restore means
   a structure is missing from the section, not that the interpretation is
   wrong. Never instruct an interpreter the other way — it produces picks bent
   until they balance, at the cost of the correct interpretation.

Statuses: PASS | WARN | KILL | UNMEASURED | NOT_APPLICABLE.
Every gate carries epistemic_tier, scope, coverage and a receipt_hash.
`preferred_hypothesis` is ALWAYS None — GEOX proposes, arifOS seals.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from typing import Any, Callable

from geox_mcp.domain.seismic_physics.receipts import make_gate_receipt, receipt_hash

# ── Epistemic tiers ──────────────────────────────────────────────────────────

TIER_KINEMATIC = "KINEMATIC"   # directly readable from geometry
TIER_STRAIN = "STRAIN"         # requires restoration + plane-strain/area assumptions
TIER_DYNAMIC = "DYNAMIC"       # requires fault-slip inversion + Anderson/Byerelee

_TIER_ORDER = {TIER_KINEMATIC: 0, TIER_STRAIN: 1, TIER_DYNAMIC: 2}

# Andersonian reference dips (Byerlee mu 0.6-0.85 -> phi ~30 deg)
_ANDERSON = {
    "normal": {"expected_dip": 60.0, "huber": "sigma1 vertical"},
    "reverse": {"expected_dip": 30.0, "huber": "sigma3 vertical"},
    "strike_slip": {"expected_dip": 90.0, "huber": "sigma2 vertical"},
}
# The deviation band is a RULE OF THUMB, not a hard physics invariant — no source fixes
# 15 deg, and legitimate causes include BLOCK ROTATION that preserves pure extension,
# weak detachments, overpressure, and inherited basement fabric. A deviation may therefore
# NEVER be read as "the regime changed". Gates below return WARN, never KILL, on deviation.
_COULOMB_TOLERANCE_DEG = 15.0
_DEVIATION_ALTERNATIVES = (
    "block rotation preserving pure extension",
    "weak detachment / substrate",
    "overpressure",
    "inherited basement fabric (inheritance beats current stress)",
)


# ── Receipt helper ───────────────────────────────────────────────────────────


def _receipt(
    gate_id: str,
    status: str,
    *,
    tier: str,
    scope: str = "regime",
    coverage: float | None = None,
    **kw: Any,
) -> dict[str, Any]:
    """make_gate_receipt + epistemic_tier/scope/coverage folded into the hash."""
    r = make_gate_receipt(gate_id, status, **kw)  # type: ignore[arg-type]
    r["epistemic_tier"] = tier
    r["scope"] = scope
    r["coverage"] = coverage
    r["receipt_hash"] = receipt_hash(r)
    return r


def _path(obj: Any, dotted: str, default: Any = None) -> Any:
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _num(v: Any) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _measured(v: Any) -> bool:
    """A value counts as measured only if present and non-null."""
    if v is None:
        return False
    if isinstance(v, str) and not v.strip():
        return False
    if isinstance(v, (list, dict)) and len(v) == 0:
        return False
    return True


def _first_measured(framework: dict[str, Any], paths: tuple[str, ...]) -> tuple[Any, str | None]:
    for p in paths:
        v = _path(framework, p)
        if _measured(v):
            return v, p
    return None, None


def _coverage_of(framework: dict[str, Any]) -> float | None:
    covs: list[float] = []
    for h in framework.get("horizons") or []:
        c = _num(_path(h, "coverage_pct", None))
        if c is not None:
            covs.append(c / 100.0 if c > 1 else c)
    for i in framework.get("intervals") or []:
        c = _num(_path(i, "coverage_pct", None))
        if c is not None:
            covs.append(c / 100.0 if c > 1 else c)
    if not covs:
        return None
    return round(sum(covs) / len(covs), 4)


# ── Universal gates (apply to every regime) ──────────────────────────────────


def gate_regime_ceiling(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-CEILING — hard block on DYNAMIC claims without fault-slip data."""
    slip = framework.get("fault_slip_data") or framework.get("stress_inversion") or []
    has_slip = bool(slip)
    claimed_tier = str(
        _path(framework, "claim.epistemic_tier", None)
        or framework.get("epistemic_tier")
        or ""
    ).upper()
    wants_dynamic = claimed_tier == TIER_DYNAMIC or bool(framework.get("claim_stress_tensor"))

    if wants_dynamic and not has_slip:
        return _receipt(
            "K-REGIME-CEILING",
            "KILL",
            tier=TIER_DYNAMIC,
            scope="claim_only",
            reason=(
                "DYNAMIC (stress tensor) claim requested with no fault_slip_data. "
                "Geometry cannot yield a stress tensor — it yields a displacement field."
            ),
            equation="KINEMATIC -> STRAIN -> DYNAMIC requires fault-slip inversion; geometry alone is insufficient",
            inputs={"fault_slip_data_present": False, "claimed_tier": claimed_tier or None},
            thresholds={"min_slip_measurements_for_inversion": 4},
            exceptions_considered=[
                "present-day sigma from borehole breakouts / DIF / LOT / focal mechanisms",
            ],
            evidence_refs=[
                "Anderson 1951 — The Dynamics of Faulting",
                "Wallace 1951 / Bott 1959 — fault-slip stress inversion",
                "Byerlee 1978 — friction of rock",
                "Angelier 1979 — 4 of 6 tensor parameters resolvable from slip data",
            ],
            calculated_result={"dynamic_claim_permitted": False},
            findings=[{
                "verdict": "KILL",
                "note": "Stress inversion resolves 4 of 6 independent parameters even WITH slip data. "
                        "From geometry alone it resolves zero.",
            }],
            gate_type="hard_epistemic",
        )

    return _receipt(
        "K-REGIME-CEILING",
        "UNMEASURED" if not has_slip else "PASS",
        tier=TIER_DYNAMIC,
        scope="claim_only",
        reason=(
            "No DYNAMIC claim made — ceiling not breached"
            if not has_slip
            else "fault_slip_data present — DYNAMIC tier permitted (4/6 parameters)"
        ),
        equation="KINEMATIC -> STRAIN -> DYNAMIC",
        inputs={"fault_slip_data_present": has_slip, "claimed_tier": claimed_tier or "unspecified"},
        thresholds={"min_slip_measurements_for_inversion": 4},
        evidence_refs=["Angelier 1979 — 4 of 6 tensor parameters resolvable"],
        calculated_result={"dynamic_claim_permitted": has_slip},
        gate_type="hard_epistemic",
    )


def gate_regime_differential(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-DIFFERENTIAL — the actual tectonic test (I12).

    Tectonic control is proven by the SPATIAL DIFFERENTIAL of the SAME interval:
    isopach / growth pattern changing across the structure through time.
    Uniform interval + uniform terminations = eustatic/supply control.
    """
    intervals = framework.get("intervals") or []
    measured_flags = [
        bool(_path(i, "spatial_differential", None))
        for i in intervals
        if _measured(_path(i, "spatial_differential", None))
    ]
    if not measured_flags:
        return _receipt(
            "K-REGIME-DIFFERENTIAL",
            "UNMEASURED",
            tier=TIER_STRAIN,
            coverage=_coverage_of(framework),
            reason="No per-interval spatial_differential flag — tectonic test not run",
            equation="tectonic control <=> spatial differential of the same interval ACROSS the structure",
            inputs={"n_intervals": len(intervals)},
            thresholds={"min_intervals_with_differential": 2},
            missing_inputs=["intervals[].spatial_differential"],
            evidence_refs=[
                "Differential-subsidence test — accommodation vs eustasy vs supply",
                "Walther 1894 (facies succession) is NOT this test; see K-REGIME-XCUT",
            ],
            gate_type="hard_epistemic",
        )

    n_diff = sum(1 for f in measured_flags if f)
    if n_diff == 0:
        return _receipt(
            "K-REGIME-DIFFERENTIAL",
            "WARN",
            tier=TIER_STRAIN,
            coverage=_coverage_of(framework),
            reason=(
                "Isopachs uniform across the structure in every measured interval — "
                "NON-DISCRIMINATING. Uniform thickness arises from steady sediment supply, "
                "thermal subsidence, pure strike-slip, and post-depositional sag just as it does "
                "from eustatic control. This result is NOT evidence for the null hypothesis."
            ),
            equation=(
                "the eustatic test is a regionally correlative surface with synchronous onlap — "
                "NOT the absence of thickness change"
            ),
            inputs={"n_measured": len(measured_flags), "n_with_differential": 0},
            thresholds={"min_intervals_with_differential": 2},
            evidence_refs=["Accommodation = tectonics + eustasy + supply (non-unique)"],
            calculated_result={
                "discriminating": False,
                "alternatives_not_excluded": [
                    "steady sediment supply",
                    "thermal subsidence",
                    "pure strike-slip (produces no thickness variation)",
                    "post-depositional sag",
                    "eustatic control",
                ],
            },
            findings=[{
                "verdict": "WARN",
                "note": (
                    "WARN, not KILL, and not evidence for the null: a uniform interval fails to "
                    "discriminate. Absence of differential is not absence of tectonics at "
                    "sub-resolution, and uniform thickness is not a eustatic diagnosis."
                ),
            }],
            gate_type="hard_epistemic",
        )

    status = "PASS" if n_diff >= 2 else "WARN"
    return _receipt(
        "K-REGIME-DIFFERENTIAL",
        status,
        tier=TIER_STRAIN,
        coverage=_coverage_of(framework),
        reason=f"{n_diff}/{len(measured_flags)} intervals show spatial differential across the structure",
        equation="tectonic control <=> spatial differential of the same interval ACROSS the structure",
        inputs={"n_measured": len(measured_flags), "n_with_differential": n_diff},
        thresholds={"min_intervals_with_differential": 2},
        evidence_refs=["Differential test — the only geometry-based tectonic discriminator"],
        calculated_result={"tectonic_control_supported": n_diff >= 2, "n_differential_intervals": n_diff},
        gate_type="hard_epistemic",
    )


def gate_regime_decompaction(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-DECOMPACT — isopach must be decompacted before any thickness argument."""
    flags = [
        bool(_path(i, "decompacted", None))
        for i in framework.get("intervals") or []
        if _measured(_path(i, "decompacted", None))
    ]
    used = bool(framework.get("intervals"))
    if not used:
        return _receipt(
            "K-REGIME-DECOMPACT", "NOT_APPLICABLE", tier=TIER_STRAIN,
            reason="No intervals supplied", gate_type="hard_epistemic",
        )
    if not flags:
        return _receipt(
            "K-REGIME-DECOMPACT", "UNMEASURED", tier=TIER_STRAIN,
            coverage=_coverage_of(framework),
            reason="Isopach thickness used without a decompaction flag — differential may be lithological",
            equation="t(depth) = t(initial) * compaction_factor(depth); 'constant thickness' means constant in TIME, not in DEPTH",
            inputs={"n_intervals": len(framework.get("intervals") or [])},
            missing_inputs=["intervals[].decompacted"],
            evidence_refs=["Backstripping / decompaction — Sclater & Christie 1980"],
            findings=[{"verdict": "UNMEASURED", "note": "Compaction thins parallel beds with zero tectonics; undiscompacted differential gets priced as growth."}],
            gate_type="hard_epistemic",
        )
    n_dec = sum(1 for f in flags if f)
    return _receipt(
        "K-REGIME-DECOMPACT",
        "PASS" if n_dec == len(flags) else "WARN",
        tier=TIER_STRAIN,
        coverage=_coverage_of(framework),
        reason=f"{n_dec}/{len(flags)} intervals carry a decompaction flag",
        equation="decompaction before thickness interpretation",
        inputs={"n_decompacted": n_dec, "n_intervals": len(flags)},
        evidence_refs=["Backstripping / decompaction — Sclater & Christie 1980"],
        gate_type="hard_epistemic",
    )


def gate_regime_display(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-DISPLAY — dips measured off a display or in time domain are not geometry.

    Two distinct distortions, often conflated:
      * Display: tan(theta_apparent) = VE * tan(theta_true), where VE is the DIMENSIONLESS
        ratio v_display / v_true — not a velocity. Writing it as a velocity equates a
        dimensionless quantity to m/s (dimensional error).
      * Migration: MIGRATED data do not follow the tan relation; migration changes the
        apparent-dip behaviour. A migration-state declaration is therefore also required.
    """
    ve = _num(_path(framework, "display.vertical_exaggeration", None))
    if ve is None:
        ve = _num(_path(framework, "measurement_context.geometry.vertical_exaggeration", None))
    vel = _path(framework, "display.velocity_model", None)
    td = _path(framework, "display.time_domain", None)
    migration = str(_path(framework, "display.migration_state", "unknown") or "unknown").lower()
    any_dip_used = bool(framework.get("horizons")) or bool(framework.get("faults"))

    if not any_dip_used:
        return _receipt("K-REGIME-DISPLAY", "NOT_APPLICABLE", tier=TIER_KINEMATIC,
                        reason="No dip-bearing input", gate_type="hard_epistemic")

    problems: list[str] = []
    if ve is None:
        problems.append("vertical_exaggeration unknown")
    elif abs(ve - 1.0) > 1e-9:
        problems.append(f"vertical_exaggeration={ve} != 1 — apparent dips inflated")
    if td and not vel:
        problems.append("time-domain dips without an interval-velocity model")
    if migration not in ("migrated", "unmigrated"):
        problems.append("migration_state unknown — migrated data do not follow the tan relation")

    if not problems:
        return _receipt(
            "K-REGIME-DISPLAY", "PASS", tier=TIER_KINEMATIC, coverage=_coverage_of(framework),
            reason="VE = 1 (or corrected), depth domain (or velocity model present), migration state declared",
            equation="tan(theta_apparent) = VE * tan(theta_true), VE dimensionless",
            inputs={"vertical_exaggeration": ve, "time_domain": td,
                    "velocity_model": bool(vel), "migration_state": migration},
            evidence_refs=[
                "tan(theta_app) = VE*tan(theta_true) — VE is a dimensionless ratio, not a velocity",
                "Migrated data do not follow the tan relation",
                "Time-to-depth requires an interval-velocity model",
            ],
            gate_type="hard_epistemic",
        )
    return _receipt(
        "K-REGIME-DISPLAY", "UNMEASURED", tier=TIER_KINEMATIC, coverage=_coverage_of(framework),
        reason="Dip cannot be trusted: " + "; ".join(problems),
        equation="tan(theta_apparent) = VE * tan(theta_true); time != depth; migrated != unmigrated",
        inputs={"vertical_exaggeration": ve, "time_domain": td,
                "velocity_model": bool(vel), "migration_state": migration},
        missing_inputs=[p for p in ("vertical_exaggeration",) if ve is None],
        evidence_refs=[
            "tan(theta_app) = VE*tan(theta_true)",
            "Interval-velocity model required for true dip",
        ],
        findings=[{"verdict": "UNMEASURED", "problems": problems,
                   "note": "'Geometry does not lie' is only true after the pick follows the wavelet, "
                           "the display is unexaggerated, and time has become depth."}],
        gate_type="hard_epistemic",
    )


def gate_regime_resolution(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-RESOLUTION — sub-tuning features are model, not observation."""
    lam4 = _num(_path(framework, "resolution.tuning_thickness_lambda4", None))
    feat = _num(_path(framework, "resolution.min_mapped_feature_thickness", None))
    if lam4 is None or feat is None:
        return _receipt(
            "K-REGIME-RESOLUTION", "UNMEASURED", tier=TIER_KINEMATIC,
            reason="Tuning limit and/or mapped-feature thickness not supplied",
            equation="Tuning thickness = lambda/4 at dominant frequency",
            missing_inputs=[k for k, v in (("resolution.tuning_thickness_lambda4", lam4),
                                           ("resolution.min_mapped_feature_thickness", feat)) if v is None],
            evidence_refs=["Widess 1973 — Rayleigh/tuning resolution"],
            gate_type="hard_epistemic",
        )
    if feat < lam4:
        return _receipt(
            "K-REGIME-RESOLUTION", "WARN", tier=TIER_KINEMATIC,
            reason=f"Mapped feature {feat} m is below tuning thickness {lam4} m — geometry is model, not observation",
            equation="feature >= lambda/4 required for thickness to be an observation",
            inputs={"tuning_thickness_lambda4": lam4, "min_mapped_feature_thickness": feat},
            thresholds={"tuning_thickness_lambda4": lam4},
            evidence_refs=["Widess 1973", "Sub-tuning faults appear as flexure/distortion, not as picks"],
            calculated_result={"sub_tuning": True},
            gate_type="hard_epistemic",
        )
    return _receipt(
        "K-REGIME-RESOLUTION", "PASS", tier=TIER_KINEMATIC,
        reason=f"Mapped feature {feat} m >= tuning thickness {lam4} m",
        equation="feature >= lambda/4",
        inputs={"tuning_thickness_lambda4": lam4, "min_mapped_feature_thickness": feat},
        evidence_refs=["Widess 1973"],
        gate_type="hard_epistemic",
    )


def gate_regime_xcut(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-XCUT — cross-cutting gives relative chronology (Steno/Hutton/Lyell).

    Explicitly NOT Walther's Law. Walther governs conformable facies succession
    (vertically stacked facies were laterally adjacent environments). Section order
    comes from cross-cutting relationships — a distinct stratigraphic principle.
    """
    xs = framework.get("cross_cutting") or []
    if not xs:
        return _receipt(
            "K-REGIME-XCUT", "UNMEASURED", tier=TIER_KINEMATIC,
            reason="No cross-cutting / terminations table — no relative chronology available",
            equation="a feature is younger than the youngest horizon it offsets, older than the oldest that drapes it",
            missing_inputs=["cross_cutting[]"],
            evidence_refs=["Steno 1669 — Dissertationis prodromus", "Hutton 1795", "Lyell 1830"],
            findings=[{"verdict": "UNMEASURED", "correction": "Cross-cutting is NOT Walther's Law. Different principle, different author set."}],
            gate_type="hard_epistemic",
        )
    return _receipt(
        "K-REGIME-XCUT", "PASS", tier=TIER_KINEMATIC,
        reason=f"{len(xs)} cross-cutting relations — relative chronology available",
        equation="younger than the youngest offset horizon; older than the oldest draping horizon",
        inputs={"n_relations": len(xs)},
        exceptions_considered=["Fault tips and relay zones drape in one place and offset the same horizon along strike"],
        evidence_refs=["Steno 1669", "Hutton 1795", "Lyell 1830"],
        findings=[{"verdict": "PASS", "caveat": "A drape observation dates the fault LOCALLY, not the system."}],
        gate_type="hard_epistemic",
    )


def gate_regime_coverage(framework: dict[str, Any]) -> dict[str, Any]:
    """K-REGIME-COVERAGE — confidence without coverage is invalid."""
    cov = _coverage_of(framework)
    if cov is None:
        return _receipt(
            "K-REGIME-COVERAGE", "UNMEASURED", tier=TIER_KINEMATIC, coverage=None,
            reason="No coverage reported on horizons/intervals — verdict cannot be carried",
            missing_inputs=["horizons[].coverage_pct"],
            evidence_refs=["Confidence without coverage is invalid (GEOX iron rule)"],
            gate_type="hard_epistemic",
        )
    status = "PASS" if cov >= 0.5 else "WARN"
    return _receipt(
        "K-REGIME-COVERAGE", status, tier=TIER_KINEMATIC, coverage=cov,
        reason=f"Mean coverage {cov:.2f} across horizons/intervals",
        thresholds={"min_mean_coverage": 0.5},
        inputs={"mean_coverage": cov},
        evidence_refs=["Confidence without coverage is invalid"],
        gate_type="hard_epistemic",
    )


# ── Regime-specific falsifiers ───────────────────────────────────────────────


def _falsifiers_extension(fw: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    dips = [_num(_path(f, "dip_deg", None)) for f in (fw.get("faults") or [])]
    dips = [d for d in dips if d is not None]
    if not dips:
        out.append(_receipt(
            "K-EXT-DIP", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No fault dips measured — Andersonian dip test not run",
            equation="theta_failure = 45 - phi/2; phi~30 => normal faults ~60 deg from horizontal",
            missing_inputs=["faults[].dip_deg"],
            evidence_refs=["Anderson 1951", "Byerlee 1978"],
            gate_type="physics",
        ))
    else:
        mean = sum(dips) / len(dips)
        dev = abs(mean - _ANDERSON["normal"]["expected_dip"])
        if dev <= _COULOMB_TOLERANCE_DEG:
            out.append(_receipt(
                "K-EXT-DIP", "PASS", tier=TIER_KINEMATIC, scope="regime",
                reason=f"Mean fault dip {mean:.1f} deg within {_COULOMB_TOLERANCE_DEG} deg of Andersonian 60 deg (n={len(dips)})",
                equation="theta_failure = 45 - phi/2", inputs={"mean_dip_deg": round(mean, 2), "n": len(dips)},
                thresholds={"expected_dip_deg": 60.0, "tolerance_deg": _COULOMB_TOLERANCE_DEG},
                evidence_refs=["Anderson 1951", "Byerlee 1978"],
                calculated_result={"deviation_deg": round(dev, 2)},
                gate_type="physics",
            ))
        else:
            out.append(_receipt(
                "K-EXT-DIP", "WARN", tier=TIER_KINEMATIC, scope="regime",
                reason=(
                    f"Mean fault dip {mean:.1f} deg deviates {dev:.1f} deg from Andersonian 60 deg — "
                    "WARN not KILL: the deviation band is a rule of thumb with no fixed source, and "
                    "deviation has several legitimate causes, none of which means 'the regime changed'"
                ),
                equation="theta_failure = 45 - phi/2", inputs={"mean_dip_deg": round(mean, 2), "n": len(dips)},
                thresholds={"expected_dip_deg": 60.0, "tolerance_deg": _COULOMB_TOLERANCE_DEG},
                exceptions_considered=list(_DEVIATION_ALTERNATIVES),
                evidence_refs=["Anderson 1951", "Byerlee 1978"],
                calculated_result={"deviation_deg": round(dev, 2), "regime_change_concluded": False},
                gate_type="physics",
            ))

    ei, ei_path = _first_measured(fw, ("growth.expansion_index", "expansion_index", "claims.expansion_index"))
    ei_f = _num(ei)
    if ei_f is None:
        out.append(_receipt(
            "K-EXT-GROWTH", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason=(
                "No expansion index measured. ABSENCE OF A GROWTH WEDGE DOES NOT KILL EXTENSION — "
                "a fault moving slower than the sediment supply leaves no growth signature, and "
                "growth onset lags fault initiation while parallel geometry resumes late at cessation. "
                "The kinematic clock is blind at both ends."
            ),
            equation="EI = hangingwall_thickness / footwall_thickness; syn-tectonic claim requires EI > 1",
            thresholds={"ei_min": 1.0}, missing_inputs=["growth.expansion_index"],
            evidence_refs=[
                "Thorsen 1963 — growth fault EI test",
                "Suppe et al. 1992 — growth strata geometry controlled by folding mechanism AND the "
                "relative rates of sedimentation and uplift (AAPG Wiki: Growth strata)",
                "Castelltort et al. — sedimentary vs tectonic mimic",
            ],
            exceptions_considered=["sedimentation outpaced fault slip (no signature)", "differential compaction mimic"],
            gate_type="soft_conditional",
        ))
    elif ei_f <= 1.0:
        out.append(_receipt(
            "K-EXT-GROWTH", "KILL", tier=TIER_KINEMATIC, scope="interval_syn_tectonic_claim",
            reason=f"EI={ei_f} <= 1 measured ({ei_path}) — syn-tectonic growth claim for that interval is dead",
            equation="EI = hangingwall_thickness / footwall_thickness; syn-tectonic requires EI > 1",
            inputs={"expansion_index": ei_f, "source": ei_path},
            thresholds={"ei_min": 1.0},
            evidence_refs=["Thorsen 1963 — growth fault EI test"],
            calculated_result={"expansion_index": ei_f},
            findings=[{"verdict": "KILL", "scope_note": "Kills the SYN-TECTONIC TIMING claim for that interval, not necessarily extension itself."}],
            gate_type="soft_conditional",
        ))
    else:
        out.append(_receipt(
            "K-EXT-GROWTH", "WARN", tier=TIER_KINEMATIC, scope="regime",
            reason=f"EI={ei_f} > 1 supports syn-tectonic growth (mimic caveat applies)",
            equation="EI = hangingwall_thickness / footwall_thickness",
            inputs={"expansion_index": ei_f, "source": ei_path}, thresholds={"ei_min": 1.0},
            exceptions_considered=["differential compaction over a buried high reproduces growth-like thinning (Chopra; Bubb & Hatledid 1979)"],
            evidence_refs=["Thorsen 1963", "Chopra — seismic attribute expression of differential compaction"],
            calculated_result={"expansion_index": ei_f},
            gate_type="soft_conditional",
        ))

    pol = _path(fw, "faults.0.polarity_switch", None)
    graft = _path(fw, "graben", None) or _path(fw, "half_graben", None)
    if _measured(pol) or _measured(graft):
        out.append(_receipt(
            "K-EXT-ARCH", "PASS", tier=TIER_KINEMATIC, scope="regime",
            reason="Half-graben polarity switch and/or graben architecture observed",
            equation="polarity switch along strike => extension (orthogonal or oblique rifting)",
            inputs={"polarity_switch": pol, "graben": bool(graft)},
            evidence_refs=["Orthogonal vs oblique rifting — en-echelon overlapping segments"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-EXT-ARCH", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No along-strike polarity / graben architecture reported",
            missing_inputs=["faults[].polarity_switch"], gate_type="physics",
        ))
    return out


def _falsifiers_compression(fw: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    short, spath = _first_measured(fw, ("restore.shortening_m", "restore.total_shortening_m"))
    length_before = _num(_path(fw, "restore.bed_length_before_m", None))
    length_after = _num(_path(fw, "restore.bed_length_after_m", None))
    if short is not None or (length_before is not None and length_after is not None):
        s = _num(short)
        if s is None and length_before is not None and length_after is not None:
            s = length_before - length_after
        if s is not None and abs(s) < 1e-9:
            out.append(_receipt(
                "K-COMP-SHORTEN", "KILL", tier=TIER_STRAIN, scope="regime",
                reason="Restoration measured ZERO shortening — compression claim is dead",
                equation="shortening = L_restored - L_deformed; compression requires > 0",
                inputs={"shortening_m": s, "source": spath or "bed_length delta"},
                thresholds={"min_shortening_m": 0.0},
                evidence_refs=["Dahlstrom 1969 — balanced cross sections (concentric, plane-strain)"],
                calculated_result={"shortening_m": s},
                gate_type="physics",
            ))
        else:
            out.append(_receipt(
                "K-COMP-SHORTEN", "PASS", tier=TIER_STRAIN, scope="regime",
                reason=f"Non-zero shortening measured: {s} m",
                equation="shortening = L_restored - L_deformed",
                inputs={"shortening_m": s},
                evidence_refs=["Dahlstrom 1969"],
                calculated_result={"shortening_m": s},
                gate_type="physics",
            ))
    else:
        out.append(_receipt(
            "K-COMP-SHORTEN", "UNMEASURED", tier=TIER_STRAIN, scope="regime",
            reason="No restoration shortening measured — compression cannot be killed OR confirmed without it",
            equation="shortening = L_restored - L_deformed",
            missing_inputs=["restore.shortening_m", "restore.bed_length_before_m/after_m"],
            evidence_refs=["Dahlstrom 1969"],
            gate_type="physics",
        ))

    verg = [_path(h, "geometry.vergence", None) for h in (fw.get("horizons") or [])]
    verg = [v for v in verg if _measured(v)]
    if verg:
        n_uniq = len({str(v) for v in verg})
        out.append(_receipt(
            "K-COMP-VERGENCE", "PASS" if n_uniq == 1 else "WARN", tier=TIER_KINEMATIC, scope="regime",
            reason=(
                f"Vergence consistent across {len(verg)} horizons — tectonic transport direction constrained"
                if n_uniq == 1 else
                f"{n_uniq} distinct vergence directions — possible backthrust, or a vergence flip to resolve"
            ),
            equation="vergence points toward the foreland; flips at a backthrust",
            inputs={"n_horizons": len(verg), "n_distinct_vergence": n_uniq},
            evidence_refs=["Fold-vergence method — forensic transport direction"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-COMP-VERGENCE", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No vergence reported on any horizon",
            missing_inputs=["horizons[].geometry.vergence"], gate_type="physics",
        ))

    ramps = [f for f in (fw.get("faults") or []) if _num(_path(f, "dip_deg", None)) is not None
             and str(_path(f, "slip_sense", "")).lower() in ("reverse", "thrust")]
    if ramps:
        dips = [_num(_path(f, "dip_deg", None)) for f in ramps]
        mean = sum(d for d in dips if d is not None) / len(dips)
        dev = abs(mean - 30.0)
        out.append(_receipt(
            "K-COMP-RAMPFLAT", "PASS" if dev <= _COULOMB_TOLERANCE_DEG else "WARN",
            tier=TIER_KINEMATIC, scope="regime",
            reason=f"Reverse-fault mean dip {mean:.1f} deg vs Andersonian 30 deg (deviation {dev:.1f} deg)",
            equation="theta_failure = 45 - phi/2; ~30 deg for thrusts (Anderson: sigma3 vertical)",
            inputs={"mean_reverse_dip_deg": round(mean, 2), "n": len(ramps)},
            thresholds={"expected_dip_deg": 30.0, "tolerance_deg": _COULOMB_TOLERANCE_DEG},
            exceptions_considered=list(_DEVIATION_ALTERNATIVES),
            evidence_refs=["Anderson 1951", "Byerlee 1978"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-COMP-RAMPFLAT", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No reverse/thrust-sense fault with a measured dip",
            missing_inputs=["faults[].slip_sense=reverse", "faults[].dip_deg"],
            gate_type="physics",
        ))
    return out


def _falsifiers_strike_slip(fw: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    ratios: list[float] = []
    for f in (fw.get("faults") or []):
        throw = _num(_path(f, "throw_m", None))
        heave = _num(_path(f, "heave_m", None))
        strike = _num(_path(f, "strike_extent_m", None))
        length = _num(_path(f, "length_km", None))
        if throw is None:
            continue
        denom = heave or strike or (length * 1000.0 if length else None)
        if denom:
            ratios.append(abs(throw) / denom)
    if ratios:
        mean = sum(ratios) / len(ratios)
        if mean < 0.05:
            out.append(_receipt(
                "K-SS-THROW", "PASS", tier=TIER_KINEMATIC, scope="regime",
                reason=f"Throw/heave ratio {mean:.3f} ~ 0 over long strike extent — the strike-slip signature",
                equation="strike-slip signature = lateral offset with LITTLE TO NO vertical offset",
                inputs={"mean_throw_ratio": round(mean, 4), "n": len(ratios)},
                thresholds={"max_ratio_for_pure_strike_slip": 0.05},
                evidence_refs=["Strike-slip fault signature property"],
                calculated_result={"mean_throw_ratio": round(mean, 4)},
                gate_type="physics",
            ))
        else:
            out.append(_receipt(
                "K-SS-THROW", "WARN", tier=TIER_KINEMATIC, scope="regime",
                reason=f"Throw/heave ratio {mean:.3f} is substantial — oblique slip or a different regime",
                equation="pure strike-slip => near-zero throw",
                inputs={"mean_throw_ratio": round(mean, 4), "n": len(ratios)},
                thresholds={"max_ratio_for_pure_strike_slip": 0.05},
                evidence_refs=["Strike-slip fault signature property"],
                calculated_result={"mean_throw_ratio": round(mean, 4)},
                gate_type="physics",
            ))
    else:
        out.append(_receipt(
            "K-SS-THROW", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No throw/heave ratio computable",
            missing_inputs=["faults[].throw_m", "faults[].heave_m|strike_extent_m|length_km"],
            gate_type="physics",
        ))

    markers = [m for m in (fw.get("markers") or [])
               if _num(_path(m, "lateral_offset_m", None)) is not None
               and _path(m, "both_sides_match", None)]
    if markers:
        out.append(_receipt(
            "K-SS-MARKER", "PASS", tier=TIER_KINEMATIC, scope="regime",
            reason=f"{len(markers)} marker(s) laterally offset with both sides matching — lateral displacement proven",
            equation="lateral offset of a marker that matches across the fault => strike-slip component",
            inputs={"n_offset_markers": len(markers)},
            evidence_refs=["Definitive strike-slip diagnostic"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-SS-MARKER", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason=(
                "No marker proving lateral offset. NOTE: abrupt facies/thickness change across a "
                "near-vertical fault is NOT a strike-slip diagnostic — that is more likely a transfer "
                "zone, lateral facies boundary, or inherited basin margin."
            ),
            missing_inputs=["markers[].lateral_offset_m", "markers[].both_sides_match"],
            evidence_refs=["Little-to-no throw with proven lateral offset is the signature"],
            gate_type="physics",
        ))

    ried = []
    for f in (fw.get("faults") or []):
        a = _num(_path(f, "riedel_angle_deg", None))
        if a is not None:
            ried.append(abs(a))
    if ried:
        ok = all(abs(x - 15.0) <= 15.0 or abs(x - 75.0) <= 15.0 for x in ried)
        out.append(_receipt(
            "K-SS-RIEDEL", "PASS" if ok else "WARN", tier=TIER_KINEMATIC, scope="regime",
            reason=("Riedel angles consistent with R~15 deg / R'~75 deg to the master fault"
                    if ok else "Riedel angles off the R~15 / R'~75 pattern"),
            equation="R synthetic ~15 deg to master; R' antithetic ~75 deg",
            inputs={"riedel_angles_deg": ried}, thresholds={"r_deg": 15.0, "r_prime_deg": 75.0},
            evidence_refs=["Riedel 1929 — shear experiments"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-SS-RIEDEL", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No Riedel shear angles measured", missing_inputs=["faults[].riedel_angle_deg"],
            gate_type="physics",
        ))

    flower = _path(fw, "flower", None)
    if _measured(flower):
        fl = str(flower).lower()
        interp = ("transpression (positive flower)" if "pos" in fl else
                  "transtension (negative flower)" if "neg" in fl else "unspecified polarity")
        out.append(_receipt(
            "K-SS-FLOWER", "PASS", tier=TIER_KINEMATIC, scope="regime",
            reason=f"Flower structure reported — {interp}",
            equation="positive (palm tree, upthrown core) = transpression; negative (tulip) = transtension",
            inputs={"flower": flower},
            evidence_refs=["Harding 1974 / Wilcox et al. 1973 — wrench tectonics"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-SS-FLOWER", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No flower geometry reported (cross-section evidence required)",
            missing_inputs=["flower"], gate_type="physics",
        ))
    return out


def _falsifiers_inversion(fw: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    reversals: list[str] = []
    for i in fw.get("intervals") or []:
        rev = _path(i, "isopach_reversal", None)
        if _measured(rev):
            if bool(rev):
                reversals.append(str(_path(i, "name", "unnamed")))
    measured_any = any(_measured(_path(i, "isopach_reversal", None)) for i in fw.get("intervals") or [])
    if not measured_any:
        out.append(_receipt(
            "K-INV-REVERSAL", "UNMEASURED", tier=TIER_STRAIN, scope="regime",
            reason="No interval carries an isopach_reversal flag — inversion untested",
            equation="isopach reversal: thick syn-rift interval truncated/thinned by later uplift",
            missing_inputs=["intervals[].isopach_reversal"],
            evidence_refs=["Positive inversion — earlier extensional geometry folded and truncated"],
            gate_type="physics",
        ))
    elif not reversals:
        out.append(_receipt(
            "K-INV-REVERSAL", "UNMEASURED", tier=TIER_STRAIN, scope="regime",
            reason="All measured intervals report NO isopach reversal — negative evidence, not a kill",
            equation="isopach reversal required for inversion",
            evidence_refs=["Positive inversion"],
            findings=[{"verdict": "UNMEASURED", "note": "Absence of a reversal where the section is not tied to well control is weak negative evidence, not proof of absence."}],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-INV-REVERSAL", "PASS", tier=TIER_STRAIN, scope="regime",
            reason=f"Isopach reversal measured in {len(reversals)} interval(s): {', '.join(reversals)}",
            equation="isopach reversal = rift-thick interval now truncated/thinned by uplift",
            inputs={"intervals_with_reversal": reversals},
            evidence_refs=["Positive inversion"],
            gate_type="physics",
        ))

    react = [f for f in (fw.get("faults") or [])
             if _path(f, "reactivated", None) and str(_path(f, "slip_sense", "")).lower() in ("reverse", "thrust")]
    if react:
        out.append(_receipt(
            "K-INV-REACT", "PASS", tier=TIER_KINEMATIC, scope="regime",
            reason=f"{len(react)} fault(s) show the same plane reactivated in the reverse sense",
            equation=("sigma1 and sigma3 EXCHANGE POSITIONS (sigma3 -> vertical, sigma2 stays horizontal). "
                      "A stress axis never becomes a different axis; the same fault plane is reactivated "
                      "under a swapped tensor. Inversion is not a separate stress regime."),
            inputs={"n_reactivated": len(react)},
            exceptions_considered=["strike-slip reactivation with a vertical sigma2 instead"],
            evidence_refs=["Positive inversion — same plane, opposite slip"],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-INV-REACT", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No fault flagged as reactivated with opposite slip sense",
            missing_inputs=["faults[].reactivated", "faults[].slip_sense"],
            gate_type="physics",
        ))
    return out


def _falsifiers_salt(fw: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    salt = fw.get("salt") or {}
    present = _path(salt, "present", None)
    if not _measured(present):
        out.append(_receipt(
            "K-SALT-BODY", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="Salt presence not established",
            equation="salt structures are identified by the salt body itself, not by the fold geometry it mimics",
            missing_inputs=["salt.present"], gate_type="physics",
        ))
        return out

    if not bool(present):
        out.append(_receipt(
            "K-SALT-BODY", "NOT_APPLICABLE", tier=TIER_KINEMATIC, scope="regime",
            reason="No salt in section",
            equation="no salt body -> halokinesis not a candidate",
            inputs={"salt_present": False}, gate_type="physics",
        ))
        return out

    out.append(_receipt(
        "K-SALT-BODY", "PASS", tier=TIER_KINEMATIC, scope="regime",
        reason="Salt body identified in section",
        equation="the salt body itself discriminates halokinesis from compressional folding",
        inputs={"salt_present": True},
        exceptions_considered=["forced folds above sills also mimic compressional folds — check for an igneous source body"],
        evidence_refs=["Halokinesis vs thin-skinned shortening"],
        gate_type="physics",
    ))

    driver = str(_path(salt, "driver", "") or "").lower()
    dc = _num(_path(salt, "density_contrast_kg_m3", None))
    if not driver:
        out.append(_receipt(
            "K-SALT-DRIVER", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="Diapir driver not specified",
            equation="diapirism is driven by differential-loading pressure gradient, basal slope and tectonic force — buoyancy alone is usually too weak",
            missing_inputs=["salt.driver"], gate_type="physics",
        ))
    elif "buoy" in driver and dc is not None and abs(dc) < 200:
        out.append(_receipt(
            "K-SALT-DRIVER", "KILL", tier=TIER_KINEMATIC, scope="mechanism_claim",
            reason=f"Buoyancy-only driver claimed with density contrast {dc} kg/m3 — too weak to initiate diapirism alone",
            equation="buoyancy alone with delta-rho ~1e2 kg/m3 does not initiate diapirs; differential loading / slope / tectonic force does",
            inputs={"driver": driver, "density_contrast_kg_m3": dc},
            thresholds={"min_buoyancy_only_density_contrast_kg_m3": 200},
            evidence_refs=[
                "Gaullier et al. — salt diapirism driven by differential loading (analogue modelling)",
                "Numerical modelling of salt diapirism: influence of the tectonic regime",
                "Dalhousie — salt tectonics driven by differential sediment loading (stability analysis)",
                "Geophysical Journal International 239 — active and passive salt diapirs: numerical study",
            ],
            calculated_result={"driver_permitted": False},
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-SALT-DRIVER", "PASS", tier=TIER_KINEMATIC, scope="regime",
            reason=f"Driver specified as '{driver}'" + (f" (density contrast {dc} kg/m3)" if dc is not None else ""),
            equation="differential loading / basal slope / tectonic force drive diapirism",
            inputs={"driver": driver, "density_contrast_kg_m3": dc},
            evidence_refs=["Gaullier et al. — differential loading analogue modelling"],
            gate_type="physics",
        ))
    return out


def _falsifiers_gravity(fw: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    g = fw.get("gravity") or {}
    keys = ("listric", "rollover", "toe_thrust", "same_decollement", "coeval")
    measured = {k: _path(g, k, None) for k in keys}
    have = {k: bool(v) for k, v in measured.items() if _measured(v)}
    if not have:
        return [_receipt(
            "K-GRAV-LINKAGE", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="Gravity-tectonics linkage flags not supplied",
            equation="gravity system = listric growth fault + rollover + toe thrust on ONE decollement, COEVAL",
            missing_inputs=[f"gravity.{k}" for k in keys], gate_type="physics",
        )]
    need = ("listric", "rollover", "toe_thrust", "same_decollement", "coeval")
    got = [k for k in need if have.get(k)]
    if len(got) == len(need):
        out.append(_receipt(
            "K-GRAV-LINKAGE", "PASS", tier=TIER_KINEMATIC, scope="regime",
            reason="Linked gravity system complete: listric + rollover + toe thrust on one decollement, coeval",
            equation="updip extension accommodated downdip on one decollement => gravity, not regional stress",
            inputs=measured, gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-GRAV-LINKAGE", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason=f"Linked gravity system incomplete — present: {', '.join(got)}; missing: {', '.join(k for k in need if k not in have)}",
            equation="all five linkage elements required; partial linkage is not evidence for gravity tectonics",
            inputs=measured, gate_type="physics",
        ))

    # ── Null-point / delta-system conservation (GRAVITY HYPOTHESIS ONLY) ─────
    # Updip extension must be accommodated downdip within ONE linked system: the
    # null point is where the two meet. SCOPE IS THE WHOLE POINT: failing the
    # equality kills the gravity hypothesis WITHIN that system — it must never be
    # generalised basin-wide. The equality presumes a single decollement of
    # constant thickness and a 2-D view; salt/mud systems flow material out of
    # section, 3-D displacement also goes along strike, and inversion has no such
    # balance at all.
    ext = _num(g.get("total_extension_m"))
    comp = _num(g.get("total_shortening_m"))
    if ext is None or comp is None:
        out.append(_receipt(
            "K-GRAV-NULLPOINT", "UNMEASURED", tier=TIER_STRAIN, scope="linked_system_only",
            reason="Updip extension and downdip shortening not both supplied — null point untested",
            equation="Delta_L_ext = Delta_L_comp within ONE linked system; the null point is where they meet",
            missing_inputs=["gravity.total_extension_m", "gravity.total_shortening_m"],
            exceptions_considered=[
                "single decollement of constant thickness required",
                "2-D view: 3-D displacement also goes along strike",
                "mobile unit in section flows material out of section",
            ],
            evidence_refs=["Gibbs 1984 — linked extensional/compressional systems and the null point"],
            gate_type="physics",
        ))
    else:
        denom = max(abs(ext), 1e-9)
        mismatch = abs(abs(ext) - abs(comp)) / denom
        if mismatch > 0.25 and have.get("same_decollement"):
            out.append(_receipt(
                "K-GRAV-NULLPOINT", "KILL", tier=TIER_STRAIN, scope="linked_system_only",
                reason=(
                    f"Extension ({ext} m) and shortening ({comp} m) mismatch by {mismatch:.0%} "
                    "within the linked system — the gravity hypothesis for THIS system is dead. "
                    "SCOPE: this kill does NOT generalise basin-wide."
                ),
                equation="Delta_L_ext = Delta_L_comp within one linked system",
                inputs={"total_extension_m": ext, "total_shortening_m": comp,
                        "mismatch_fraction": round(mismatch, 4)},
                thresholds={"max_mismatch_fraction": 0.25},
                exceptions_considered=[
                    "independent systems (check the null point location first)",
                    "material lost to out-of-plane flow",
                    "differential compaction not removed",
                ],
                evidence_refs=["Gibbs 1984 — null point in linked extensional/compressional systems"],
                calculated_result={"mismatch_fraction": round(mismatch, 4),
                                   "scope": "linked_system_only",
                                   "generalise_basin_wide": False},
                findings=[{"verdict": "KILL", "scope_note": (
                    "Fix the linkage accounting (a separate system, a missing fault, or out-of-plane "
                    "loss) before killing gravity as a mechanism for the basin."
                )}],
                gate_type="physics",
            ))
        else:
            out.append(_receipt(
                "K-GRAV-NULLPOINT", "PASS" if mismatch <= 0.25 else "WARN",
                tier=TIER_STRAIN, scope="linked_system_only",
                reason=f"Extension {ext} m vs shortening {comp} m — mismatch {mismatch:.0%}",
                equation="Delta_L_ext = Delta_L_comp within one linked system",
                inputs={"total_extension_m": ext, "total_shortening_m": comp,
                        "mismatch_fraction": round(mismatch, 4)},
                thresholds={"max_mismatch_fraction": 0.25},
                evidence_refs=["Gibbs 1984"],
                calculated_result={"mismatch_fraction": round(mismatch, 4),
                                   "scope": "linked_system_only",
                                   "generalise_basin_wide": False},
                gate_type="physics",
            ))
    return out


def _falsifiers_null(fw: dict[str, Any]) -> list[dict[str, Any]]:
    """The null hypothesis: depositional / eustatic control. The one people forget."""
    out: list[dict[str, Any]] = []
    dips = []
    for h in fw.get("horizons") or []:
        d = _num(_path(h, "geometry.dip_deg", None))
        if d is not None:
            dips.append(abs(d))
    if dips:
        steep = max(dips)
        null_ok = steep < 25.0
        out.append(_receipt(
            "K-NULL-DIP", "PASS" if null_ok else "WARN", tier=TIER_KINEMATIC, scope="regime",
            reason=(
                f"Max horizon dip {steep:.1f} deg within the angle-of-repose limit (<25 deg clastic) — "
                "depositional/compaction origin admissible"
                if null_ok else
                f"Max horizon dip {steep:.1f} deg exceeds the angle-of-repose limit — requires tectonic tilt or margin collapse"
            ),
            equation="primary clastic clinoform dips < 25 deg; carbonate < 30-35 deg",
            inputs={"max_horizon_dip_deg": round(steep, 2)},
            thresholds={"clastic_repose_deg": 25.0, "carbonate_repose_deg": 35.0},
            evidence_refs=["Angle-of-repose ceiling — primary depositional dip limit"],
            calculated_result={"null_admissible": null_ok},
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-NULL-DIP", "UNMEASURED", tier=TIER_KINEMATIC, scope="regime",
            reason="No horizon dips supplied", missing_inputs=["horizons[].geometry.dip_deg"],
            gate_type="physics",
        ))

    compaction = _path(fw, "compaction.assessed", None)
    if _measured(compaction) and bool(compaction):
        out.append(_receipt(
            "K-NULL-COMPACTION", "PASS", tier=TIER_STRAIN, scope="regime",
            reason="Differential compaction assessed as an alternative explanation for the geometry",
            equation="differential compaction over a buried high reproduces crestal thinning, curvature and onlap-like geometry with zero tectonics",
            inputs={"compaction_assessed": True},
            evidence_refs=[
                "Chopra — seismic attribute expression of differential compaction",
                "Bubb & Hatledid 1979 — differential compaction anomalies",
            ],
            gate_type="physics",
        ))
    else:
        out.append(_receipt(
            "K-NULL-COMPACTION", "UNMEASURED", tier=TIER_STRAIN, scope="regime",
            reason="Differential compaction not assessed — a zero-tectonics mimic of the same geometry remains open",
            equation="differential compaction mimic",
            missing_inputs=["compaction.assessed"],
            evidence_refs=["Chopra — differential compaction", "Bubb & Hatledid 1979"],
            findings=[{"verdict": "UNMEASURED", "note": "Crestal thinning is a correlation, not a diagnosis."}],
            gate_type="physics",
        ))
    return out


# ── Candidate registry ───────────────────────────────────────────────────────
#
# `category` is ontological, not cosmetic. Two errors it prevents:
#   * Salt is NOT a tectonic regime. Salt does not express the regional stress field — it
#     DECOUPLES and MASKS it, and buoyancy is not even the primary driver (differential
#     loading is). Treating halokinesis as a coequal "regime" invites reading a
#     salt-withdrawal structure as a tectonic event. Verdict class: DECOUPLED, and where
#     salt is in section the stress-regime tests become NOT_APPLICABLE rather than failing.
#   * The null (depositional/eustatic/compaction) candidate is not a regime either — it is
#     the hypothesis a tectonic claim has to beat. It is mandatory in every bundle.
REGIME_CATEGORIES: dict[str, str] = {
    "extension": "regime",
    "compression": "regime",
    "strike_slip": "regime",
    "inversion": "regime",
    "salt_mobility": "decoupling_mechanism",
    "gravity_tectonics": "gravity_mechanism",
    "null_depositional": "null_hypothesis",
}

REGIME_FALSIFIERS: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]] = {
    "extension": _falsifiers_extension,
    "compression": _falsifiers_compression,
    "strike_slip": _falsifiers_strike_slip,
    "inversion": _falsifiers_inversion,
    "salt_mobility": _falsifiers_salt,
    "gravity_tectonics": _falsifiers_gravity,
    "null_depositional": _falsifiers_null,  # NULL HYPOTHESIS — mandatory competitor
}

_NULL_HYPOTHESIS = "null_depositional"


# ── Falsification driver ─────────────────────────────────────────────────────


def falsify_regime(regime: str, framework: dict[str, Any]) -> dict[str, Any]:
    """Run one regime's falsifiers and aggregate to a hypothesis status."""
    fn = REGIME_FALSIFIERS.get(regime)
    if fn is None:
        return {
            "regime": regime,
            "status": "UNTESTED",
            "error": "UNKNOWN_REGIME",
            "known_regimes": sorted(REGIME_FALSIFIERS),
        }

    gates: dict[str, Any] = {}
    kills, passes, warns, unmeasured, na = [], [], [], [], []
    for r in fn(framework):
        gid = str(r.get("gate_id") or r.get("gate") or f"UNNAMED-{len(gates)}")
        gates[gid] = r
        v = r.get("status") or r.get("verdict") or "UNMEASURED"
        {"KILL": kills, "PASS": passes, "WARN": warns, "NOT_APPLICABLE": na}.get(v, unmeasured).append(gid)

    measured = len(passes) + len(warns) + len(kills)
    if kills:
        status = "REJECTED"
    elif measured == 0:
        status = "UNTESTED"
    else:
        status = "SURVIVES_CURRENT_TESTS"

    total = len(gates)
    discriminating_power = round(measured / total, 4) if total else 0.0
    if discriminating_power == 0.0 and status == "SURVIVES_CURRENT_TESTS":
        status = "UNTESTED"

    kill_scopes = sorted({str(gates[k].get("scope") or "regime") for k in kills})

    return {
        "regime": regime,
        "category": REGIME_CATEGORIES.get(regime, "unknown"),
        "is_null_hypothesis": regime == _NULL_HYPOTHESIS,
        "status": status,
        "gates": gates,
        "kills": kills,
        "passes": passes,
        "warns": warns,
        "unmeasured": unmeasured,
        "not_applicable": na,
        "kill_scopes": kill_scopes,
        "n_falsifiers": total,
        "n_measured": measured,
        "discriminating_power": discriminating_power,
        "max_tier_reached": max(
            (_TIER_ORDER.get(g.get("epistemic_tier") or TIER_KINEMATIC, 0) for g in gates.values()),
            default=0,
        ),
        "max_tier_name": sorted(
            {g.get("epistemic_tier") for g in gates.values() if g.get("epistemic_tier")},
            key=lambda t: _TIER_ORDER.get(t, 0),
        )[-1] if gates else None,
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
    }


def run_regime_falsification(
    framework: dict[str, Any] | None = None,
    candidate_regimes: list[str] | None = None,
    min_hypotheses: int = 3,
) -> dict[str, Any]:
    """Falsify every candidate regime against the horizon-stack bundle.

    `preferred_hypothesis` is ALWAYS None. GEOX proposes geometry; arifOS seals.
    """
    fw = dict(framework or {})

    regimes = list(candidate_regimes) if candidate_regimes else list(REGIME_FALSIFIERS)
    for r in regimes:
        if r not in REGIME_FALSIFIERS:
            return {
                "ok": False,
                "tool": "geox_regime_falsification",
                "error": "UNKNOWN_REGIME",
                "message": f"Unknown regime '{r}'",
                "known_regimes": sorted(REGIME_FALSIFIERS),
                "governance_status": "HOLD",
                "local_verdict": "QUALIFIED_CANDIDATE",
                "seal_authority": "arifOS_only",
            }

    # Every bundle must carry the null hypothesis as a competitor.
    if _NULL_HYPOTHESIS not in regimes:
        regimes.append(_NULL_HYPOTHESIS)

    if len(regimes) < min_hypotheses:
        return {
            "ok": False,
            "tool": "geox_regime_falsification",
            "error": "INSUFFICIENT_COMPETING_HYPOTHESES",
            "message": f"{len(regimes)} candidates < min_hypotheses={min_hypotheses}. "
                       "Collapsing to one hypothesis before testing is the core failure mode.",
            "candidates": regimes,
            "governance_status": "HOLD",
            "local_verdict": "QUALIFIED_CANDIDATE",
            "seal_authority": "arifOS_only",
        }

    universal = {
        "K-REGIME-CEILING": gate_regime_ceiling(fw),
        "K-REGIME-DIFFERENTIAL": gate_regime_differential(fw),
        "K-REGIME-DECOMPACT": gate_regime_decompaction(fw),
        "K-REGIME-DISPLAY": gate_regime_display(fw),
        "K-REGIME-RESOLUTION": gate_regime_resolution(fw),
        "K-REGIME-XCUT": gate_regime_xcut(fw),
        "K-REGIME-COVERAGE": gate_regime_coverage(fw),
    }

    hypotheses = [falsify_regime(r, fw) for r in regimes]

    ceiling_kill = universal["K-REGIME-CEILING"]["status"] == "KILL"
    surviving = [h["regime"] for h in hypotheses if h["status"] == "SURVIVES_CURRENT_TESTS"]
    rejected = [h["regime"] for h in hypotheses if h["status"] == "REJECTED"]
    untested = [h["regime"] for h in hypotheses if h["status"] == "UNTESTED"]

    if ceiling_kill:
        overall = "HOLD"
        governance = "HOLD"
    elif rejected and not surviving:
        overall = "ALL_CANDIDATES_REJECTED"
        governance = "HOLD"
    elif surviving:
        overall = "CANDIDATES_SURVIVE"
        governance = "ALLOW_READ"
    else:
        overall = "INSUFFICIENT_EVIDENCE"
        governance = "HOLD"

    total_falsifiers = sum(h["n_falsifiers"] for h in hypotheses)
    measured_falsifiers = sum(h["n_measured"] for h in hypotheses)

    return {
        "ok": True,
        "tool": "geox_regime_falsification",
        "universal_gates": universal,
        "hypotheses": hypotheses,
        "n_hypotheses": len(hypotheses),
        "surviving": surviving,
        "rejected": rejected,
        "untested": untested,
        "overall": overall,
        "governance_status": governance,
        "falsification_coverage": round(measured_falsifiers / total_falsifiers, 4) if total_falsifiers else 0.0,
        "n_falsifiers_run": total_falsifiers,
        "n_falsifiers_measured": measured_falsifiers,
        "preferred_hypothesis": None,  # NEVER populated by GEOX
        "local_verdict": "QUALIFIED_CANDIDATE",
        "seal_authority": "arifOS_only",
        "epistemic_map": {
            "KINEMATIC": "directly readable from geometry — strongest",
            "STRAIN": "requires restoration + plane-strain / area conservation assumptions — moderate",
            "DYNAMIC": "requires fault-slip inversion + Anderson + Byerlee; 4 of 6 tensor parameters — weakest",
        },
        "note": (
            "UNMEASURED is not a pass and not a kill. KILL requires positive measured contradiction. "
            "Absence of a growth wedge does NOT kill extension. Non-balance is a DIAGNOSTIC (a missing "
            "structure), not proof of a bad pick. Stress tensor is never emitted from geometry alone."
        ),
    }
