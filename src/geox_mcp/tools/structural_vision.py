"""
GEOX Structural Vision — DETERMINISTIC structural-metric lane
══════════════════════════════════════════════════════════════════════════
Forged 2026-09-18 · Authority: F13 Arif · Contract: CONTRACT.md v1.0 (frozen)
DITEMPA BUKAN DIBERI — Forged, Not Given

WHY THIS MODULE EXISTS
----------------------
An LLM must never read spatial metrics off a picture. Language models
hallucinate geometry. Here the agent calls a Tool; the Tool runs
DETERMINISTIC computer vision (scikit-image structure tensor, numpy DTW,
circular statistics) and returns NUMBERS WITH COVERAGE AND UNCERTAINTY.
The agent may only reason over returned numbers.

THE LLM NEVER READS GEOMETRY OFF AN IMAGE IN THIS LANE.

Two tools:

  1. geox_structural_vision_extract
        section + horizon_masks (+ calibration) -> the CONTRACT §5 bundle:
        axes A/B/C/D as Measurement dicts, a mandatory aggregate `coverage`,
        `calibration_state`, `decompaction_declared`, `method_receipt`.
        UNMEASURED is a first-class outcome and is never upgraded in transit
        — it means "not tested", never "zero" and never "pass".

  2. geox_structural_regime_falsify
        A THIN ADAPTER. It maps the extract bundle into the `framework` dict
        that `run_regime_falsification` (structure_gates/tectonic_regime.py)
        already consumes, then returns that engine's result PLUS the raw
        bundle for traceability. There is exactly ONE falsifier engine.

HARD PROHIBITIONS (CONTRACT §5, §7)
-----------------------------------
  * No probability, confidence, reliability, P(truth), score or certainty is
    ever emitted. A CV algorithm cannot emit P(truth). Any such key smuggled
    into a payload is STRIPPED by `strip_forbidden_keys` before return —
    recursively, at every depth. Confidence, if a caller needs it, comes from
    `coverage` + `n_samples` and is capped at 0.90 by F7 HUMILITY.
  * `preferred_hypothesis` is ALWAYS None. GEOX proposes geometry; arifOS seals.
  * Geometry yields KINEMATICS, never stress. Restoration yields STRAIN. Only
    fault-slip inversion yields (4 of 6) paleostress parameters. The engine's
    K-REGIME-CEILING gate is left to do its job; this module never injects a
    stress tensor.
  * The null hypothesis (depositional / eustatic / compaction control) is
    always carried as a competing candidate — the engine appends it, and this
    adapter never removes it.

SEPARATION FROM THE VLM LANE
----------------------------
This lane is SEPARATE from, and must NEVER be merged into, the VLM lane in
`geox_mcp/servers/vision.py`. A VLM reading spatial metrics from pixels is
exactly the hallucination failure this lane exists to prevent. The VLM lane is
a PERCEPTION lane (model-capped at 0.90); this is a DETERMINISTIC MEASUREMENT
lane. No shared registration, no shared server, no shared code path.

CONTRACT WIRING (CONTRACT.md §6) — the framework keys this adapter fills:

    A_shape.dip_deg_p95          -> horizons[].geometry.dip_deg
    B_differential.isopach_differential -> intervals[].spatial_differential
    B_differential.expansion_index      -> intervals[].expansion_index
    decompaction_declared               -> intervals[].decompacted
    C_orientation.azimuth_deg           -> faults[].strike_deg (population)
    D_superposition.relations           -> cross_cutting[]
    calibration_state.problems          -> display.*
    coverage                            -> horizons[].coverage_pct

Authority: GEOX (Earth evidence) prepares. arifOS judges. Arif (F13) decides.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("geox.canonical.structural_vision")


# ══════════════════════════════════════════════════════════════════════════════
# FORBIDDEN KEYS — the fabrications a deterministic lane may never emit
# ══════════════════════════════════════════════════════════════════════════════
#
# A CV algorithm measures. It does not know P(truth). Any of these keys in a
# payload is a fabricated probability (CONTRACT §5 "Forbidden in the bundle",
# CONTRACT §7 item 2 — "Kinematic_Reliability: 0.95 is a fabricated
# probability"). F7 HUMILITY caps any downstream confidence at 0.90, and that
# value must be derived from coverage + n_samples by the CONSUMER, never
# self-assigned by this lane.

FORBIDDEN_PROBABILITY_KEYS: tuple[str, ...] = (
    "confidence",
    "reliability",
    "probability",
    "p_truth",
    "score",
    "certainty",
)

# Governance constants mirrored from the frozen contract. Duplicated as plain
# literals so this surface never depends on the parallel-built core importing.
LOCAL_VERDICT = "QUALIFIED_CANDIDATE"
SEAL_AUTHORITY = "arifOS_only"
GOVERNANCE_HOLD = "HOLD"
VISION_CORE_UNAVAILABLE = "VISION_CORE_UNAVAILABLE"

# CONTRACT §0/§7 item 10 — the null hypothesis is mandatory in every bundle.
NULL_HYPOTHESIS = "null_depositional"
DEFAULT_CANDIDATE_REGIMES: tuple[str, ...] = (
    "extension",
    "compression",
    "strike_slip",
    "inversion",
    "salt_mobility",
    "gravity_tectonics",
)

# CONTRACT §7 item 3 — the SAME set governs the extraction surface. A framework
# key matching one of these must be an explicit boolean, never a probability.
_EVIDENCE_KEYS: frozenset[str] = frozenset(
    {"spatial_differential", "isopach_reversal", "preferred_hypothesis"}
)

# The falsifier engine module — absolute name, resolved lazily.
_TECTONIC_REGIME_MODULE = "geox_mcp.tools.structure_gates.tectonic_regime"


# ══════════════════════════════════════════════════════════════════════════════
# Sanitizer — recursive, strips fabricated confidence at every depth
# ══════════════════════════════════════════════════════════════════════════════


def _is_forbidden(key: Any) -> bool:
    """True if `key` is a forbidden probability key (case-insensitive, suffixed).

    Catches `confidence`, `Confidence`, `confidence_level`, `P_TRUTH`,
    `reliability_score` — the smuggled variants, not only the exact literals.
    """
    if not isinstance(key, str):
        return False
    k = key.strip().lower()
    return any(k == f or k.startswith(f + "_") or k.endswith("_" + f) for f in FORBIDDEN_PROBABILITY_KEYS)


def strip_forbidden_keys(payload: Any) -> Any:
    """Recursively remove every forbidden probability key from `payload`.

    Returns a NEW structure (no input mutation — F1 AMANAH). Lists, tuples and
    dicts are walked; scalars pass through unchanged. Tuples come back as lists
    because the result crosses a JSON boundary at the MCP edge anyway.
    """
    if isinstance(payload, dict):
        return {
            k: strip_forbidden_keys(v)
            for k, v in payload.items()
            if not _is_forbidden(k)
        }
    if isinstance(payload, (list, tuple)):
        return [strip_forbidden_keys(v) for v in payload]
    return payload


def assert_no_forbidden_keys(payload: Any, *, _path: str = "$") -> None:
    """Raise ValueError if any forbidden probability key survives in `payload`.

    Used as a self-check immediately before a payload leaves this module — a
    belt to the sanitizer's braces. If this ever fires, the sanitizer has a
    hole; fail loudly rather than shipping a fabricated confidence upstream.
    """
    if isinstance(payload, dict):
        for k, v in payload.items():
            if _is_forbidden(k):
                raise ValueError(
                    f"forbidden probability key {k!r} at {_path} — a deterministic "
                    "CV lane cannot emit P(truth) (CONTRACT §5, §7.2)"
                )
            assert_no_forbidden_keys(v, _path=f"{_path}.{k}")
    elif isinstance(payload, (list, tuple)):
        for i, v in enumerate(payload):
            assert_no_forbidden_keys(v, _path=f"{_path}[{i}]")


def _sanitize(payload: dict[str, Any]) -> dict[str, Any]:
    """Sanitize then assert. The single exit point for every returned payload."""
    clean = strip_forbidden_keys(payload)
    if not isinstance(clean, dict):  # pragma: no cover — dict in, dict out
        raise TypeError("payload must be a dict")
    assert_no_forbidden_keys(clean)
    return clean


# ══════════════════════════════════════════════════════════════════════════════
# Measurement projection + bundle scaffolding
# ══════════════════════════════════════════════════════════════════════════════


def _to_plain(obj: Any) -> Any:
    """Project a Measurement (or any dataclass-likes) to a plain dict.

    Accepts a Mapping, an object with `.asdict()`, or any object with the
    Measurement fields. Never invents a number: a MISSING attribute yields
    `None`/defaults, so a half-built core surfaces as UNMEASURED rather than
    as a fabricated zero.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return dict(obj)
    asdict_fn = getattr(obj, "asdict", None)
    if callable(asdict_fn):
        try:
            out = asdict_fn()
            if isinstance(out, dict):
                return out
        except Exception:  # pragma: no cover — defensive
            pass
    fields = ("value", "unit", "status", "n_samples", "coverage", "method",
              "uncertainty", "notes")
    if any(hasattr(obj, f) for f in fields):
        return {f: getattr(obj, f, None) for f in fields}
    return obj


def _plain_axes(raw: Any) -> dict[str, Any]:
    """Normalize the core's axis payload into `axis -> {measurement_name: dict}`."""
    if not isinstance(raw, dict):
        return {}
    axes: dict[str, Any] = {}
    for axis, content in raw.items():
        if isinstance(content, dict):
            axes[axis] = {k: _to_plain(v) for k, v in content.items()}
        elif isinstance(content, list):
            axes[axis] = [_to_plain(v) for v in content]
        else:
            axes[axis] = _to_plain(content)
    return axes


def _measurement_value(axes: dict[str, Any] | None, dotted: str) -> Any:
    """Read `A_shape.dip_deg_p95.value` out of the normalized axes tree.

    Accepts either the projected dict form or a bare scalar (a stub core may
    hand back plain numbers). Returns the RAW value — callers decide what
    a None means. A None here means NOT MEASURED, and the engine's gates read
    that as UNMEASURED, which is exactly the intent.
    """
    if not isinstance(axes, dict):
        return None
    cur: Any = axes
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    if isinstance(cur, dict):
        status = str(cur.get("status") or "").upper()
        if status == "UNMEASURED":
            return None  # never launder UNMEASURED into a number
        return cur.get("value")
    if isinstance(cur, list):
        return cur or None
    return cur


def _axis_coverage(axes: dict[str, Any]) -> list[float]:
    """Collect every `coverage` found in the axes tree (normalized 0..1)."""
    out: list[float] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            c = node.get("coverage")
            if isinstance(c, (int, float)) and not isinstance(c, bool):
                c = float(c)
                out.append(c / 100.0 if c > 1.0 else c)
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for v in node:
                _walk(v)

    _walk(axes)
    return out


def aggregate_coverage(axes: dict[str, Any], *, explicit: Any = None) -> float | None:
    """The mandatory aggregate `coverage` — CONTRACT §5.

    MANDATORY alongside any number: confidence without coverage is invalid.
    Returns None when nothing in the bundle carries coverage, which downstream
    reads as UNMEASURED (K-REGIME-COVERAGE UNMEASURED) — never as 0.0 and never
    as 1.0.
    """
    if isinstance(explicit, (int, float)) and not isinstance(explicit, bool):
        c = float(explicit)
        c = c / 100.0 if c > 1.0 else c
        return round(min(max(c, 0.0), 1.0), 4)
    covs = _axis_coverage(axes)
    if not covs:
        return None
    return round(min(max(sum(covs) / len(covs), 0.0), 1.0), 4)


def unified_status(axes: dict[str, Any], coverage: float | None) -> str:
    """MEASURED | PARTIAL | UNMEASURED for the bundle as a whole.

    Counts only quantities that structurally carry a `status`. Absence of any
    measurable quantity is UNMEASURED — not PARTIAL, not MEASURED.
    """
    stats = [str(m.get("status") or "").upper()
             for axis in axes.values()
             if isinstance(axis, dict)
             for m in axis.values()
             if isinstance(m, dict) and m.get("status")]
    if not stats:
        return "UNMEASURED"
    n_measured = sum(1 for s in stats if s == "MEASURED")
    n_any = sum(1 for s in stats if s in ("MEASURED", "PARTIAL"))
    if n_measured == len(stats) and coverage is not None:
        return "MEASURED"
    if n_any == 0:
        return "UNMEASURED"
    return "PARTIAL"


# ══════════════════════════════════════════════════════════════════════════════
# Tool 1 — deterministic extraction
# ══════════════════════════════════════════════════════════════════════════════


def _core_unavailable(reason: str) -> dict[str, Any]:
    """Structured HOLD for a missing/broken vision core. NEVER raises."""
    return _sanitize({
        "ok": False,
        "tool": "geox_structural_vision_extract",
        "error": VISION_CORE_UNAVAILABLE,
        "message": reason,
        "governance_status": GOVERNANCE_HOLD,
        "local_verdict": LOCAL_VERDICT,
        "seal_authority": SEAL_AUTHORITY,
        "axes": {},
        "coverage": None,
        "calibration_state": None,
        "decompaction_declared": False,
        "method_receipt": {},
        "status": "UNMEASURED",
        "preferred_hypothesis": None,
        "note": (
            "Deterministic structural-vision core is not importable. UNMEASURED, "
            "not FAILED: no geometry was measured, so nothing may be inferred. "
            "Do NOT substitute a vision-language model to fill the gap — reading "
            "spatial metrics from pixels is the failure this lane prevents."
        ),
    })


async def geox_structural_vision_extract(
    section: Any = None,
    horizon_masks: Any = None,
    calibration: dict[str, Any] | None = None,
    *,
    dz_m: float = 1.0,
    dx_m: float = 1.0,
    ve: float = 1.0,
    section_ref: str = "",
    horizon_names: list[str] | None = None,
    decompacted: bool = False,
    interval_velocity_m_s: float | None = None,
    time_domain: bool = False,
    migration_state: str = "",
    candidate_regimes: list[str] | None = None,
) -> dict[str, Any]:
    """DETERMINISTIC structural metrics from a seismic section. NOT a VLM call.

    Runs local computer vision (structure tensor / isopach / circular
    statistics / terminations) over `section` + `horizon_masks` and returns the
    CONTRACT §5 bundle: axes A_shape, B_differential, C_orientation,
    D_superposition, a MANDATORY aggregate `coverage`, `calibration_state`,
    `decompaction_declared` and `method_receipt`.

    The model does not look at the section. It reasons over the returned
    numbers, each of which carries `coverage`, `n_samples`, `method` and
    declared `uncertainty`, or is explicitly UNMEASURED (= not tested).

    Args:
        section: 2-D array (n_samples_z, n_traces) — amplitude, depth or time.
        horizon_masks: bool array (or list of them) marking picked horizon(s).
        calibration: caller-declared display state. Keys honoured:
            vertical_exaggeration, velocity_model_present, time_domain,
            migration_state, interval_velocity_m_s.
        dz_m: vertical sample spacing in metres.
        dx_m: trace spacing in metres.
        ve: vertical-exaggeration correction factor for true dip.
        section_ref: opaque reference for traceability (never a secret).
        horizon_names: optional names aligned to `horizon_masks`.
        decompacted: was decompaction applied BEFORE thickness? (CONTRACT §7.5)
        interval_velocity_m_s: interval velocity, required for time->depth.
        time_domain: is the section in time rather than depth?
        migration_state: pre-migrated / post-migrated declaration.
        candidate_regimes: competing regimes to carry forward, for traceability.

    Returns:
        CONTRACT §5 bundle. `preferred_hypothesis` is ALWAYS None.
        `governance_status` is "HOLD" when the deterministic core could not run.
    """
    cal = dict(calibration or {})
    cal.setdefault("vertical_exaggeration", ve)
    cal.setdefault("time_domain", bool(time_domain))
    if interval_velocity_m_s is not None:
        cal.setdefault("interval_velocity_m_s", interval_velocity_m_s)
    if migration_state:
        cal.setdefault("migration_state", migration_state)

    # ── Lazy import — the core is built in parallel by other agents ──────────
    try:
        core = importlib.import_module("geox_core.vision_structural")
    except Exception as exc:  # ImportError, ModuleNotFoundError, broken __init__
        logger.warning("vision_structural core unavailable: %s", exc)
        return _core_unavailable(f"import geox_core.vision_structural failed: {exc}")

    declared = getattr(core, "declare_calibration_state", None)
    if declared is None:
        return _core_unavailable(
            "geox_core.vision_structural is importable but incomplete: "
            "declare_calibration_state is absent"
        )

    import importlib.metadata as _md

    t0 = time.perf_counter()
    try:
        axes_raw = core.extract_all_axes(
            section,
            horizon_masks,
            dz_m=dz_m,
            dx_m=dx_m,
            ve=ve,
            horizon_names=horizon_names or [],
        )
    except Exception as exc:
        logger.warning("extract_all_axes failed: %s", exc)
        axes_raw = {}
        axes_error: str | None = f"extract_all_axes failed: {exc}"
    else:
        axes_error = None

    axes = _plain_axes(axes_raw)
    coverage = aggregate_coverage(axes, explicit=axes_raw.get("coverage") if isinstance(axes_raw, dict) else None)

    _velocity_model_present = bool(
        cal.get("velocity_model_present") or cal.get("interval_velocity_m_s")
    )
    try:
        calibration_state = declared(
            vertical_exaggeration=cal.get("vertical_exaggeration"),
            velocity_model_present=_velocity_model_present,
            time_domain=bool(cal.get("time_domain")),
        )
    except TypeError:
        # Tolerate a core that declares its calibration state without kwargs.
        calibration_state = declared(
            cal.get("vertical_exaggeration"),
            _velocity_model_present,
            bool(cal.get("time_domain")),
        )

    runtime_cal: dict[str, Any] = dict(calibration_state) if isinstance(calibration_state, dict) else {}
    # The tool DECLARED these parameters on the way in; if the core's calibration
    # state did not echo them, carry the declared values through rather than
    # letting the display gate read them as unknown. Core-declared values win.
    runtime_cal.setdefault("vertical_exaggeration", cal.get("vertical_exaggeration"))
    runtime_cal.setdefault("velocity_model_present", _velocity_model_present)
    runtime_cal.setdefault("time_domain", bool(cal.get("time_domain")))
    runtime_cal["migration_state"] = migration_state or cal.get("migration_state") or "UNSPECIFIED"
    runtime_cal["migrated_data_tan_caveat"] = (
        "MIGRATED data do not follow tan(theta_app) = VE * tan(theta_true). Migration "
        "changes apparent-dip behaviour, so a migration-state declaration is required; "
        "the tan relation alone is NOT sufficient for a migrated section."
    )

    status = unified_status(axes, coverage)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    # ── method_receipt — WHAT ran, WHICH version, WHICH parameters ──────────
    try:
        core_version = _md.version("arifos-geox")
    except Exception:
        core_version = "unknown"

    method_receipt = {
        "lane": "deterministic_structural_vision",
        "engine": "scikit-image structure tensor + numpy DTW + circular statistics",
        "llm_in_the_loop_for_geometry": False,
        "vision_language_model_used": False,
        "core_module": "geox_core.vision_structural",
        "arifos_geox_version": core_version,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "parameters": {
            "dz_m": dz_m,
            "dx_m": dx_m,
            "ve": ve,
            "time_domain": bool(cal.get("time_domain")),
            "interval_velocity_m_s": interval_velocity_m_s,
            "migration_state": migration_state or "UNSPECIFIED",
            "decompaction_applied_before_thickness": bool(decompacted),
        },
        "methods_run": sorted({
            str(m.get("method"))
            for axis in axes.values()
            if isinstance(axis, dict)
            for m in axis.values()
            if isinstance(m, dict) and m.get("method")
        }),
        "axes_extracted": sorted(axes.keys()),
        "elapsed_ms": elapsed_ms,
        "declared_at_iso": datetime.now(UTC).isoformat(),
        "core_error": axes_error,
    }

    payload = {
        "ok": axes_error is None,
        "tool": "geox_structural_vision_extract",
        "axes": axes,
        "coverage": coverage,
        "calibration_state": runtime_cal or None,
        "decompaction_declared": bool(decompacted),
        "method_receipt": method_receipt,
        "status": status,
        "local_verdict": LOCAL_VERDICT,
        "seal_authority": SEAL_AUTHORITY,
        "preferred_hypothesis": None,
        "candidate_regimes": list(candidate_regimes or DEFAULT_CANDIDATE_REGIMES),
        "section_ref": section_ref,
        "horizon_names": list(horizon_names or []),
        "epistemic_ceiling": (
            "Geometry yields KINEMATICS. Restoration yields STRAIN. Only fault-slip "
            "inversion yields paleostress — and even then only 4 of 6 tensor "
            "parameters. No stress tensor may be emitted from this lane."
        ),
        "doctrine": {
            "coverage_is_mandatory": "Confidence without coverage is invalid.",
            "unmeasured_is_not_a_pass": "UNMEASURED means NOT TESTED — never zero, never PASS.",
            "listric_is_interpretation": "Dip and curvature are measured; the classification needs a named rule.",
            "null_hypothesis_mandatory": "Every bundle carries depositional / eustatic / compaction control as a competitor.",
        },
        "null_hypothesis_candidate": NULL_HYPOTHESIS,
        "generated_at_iso": datetime.now(UTC).isoformat(),
    }

    if axes_error:
        payload["degraded"] = axes_error
        payload["governance_status"] = GOVERNANCE_HOLD
    else:
        payload["governance_status"] = "ALLOW_READ"

    return _sanitize(payload)


# ══════════════════════════════════════════════════════════════════════════════
# Tool 2 — thin adapter onto the ONE falsifier engine
# ══════════════════════════════════════════════════════════════════════════════


def bundle_to_framework(bundle: dict[str, Any] | None) -> dict[str, Any]:
    """Map a CONTRACT §5 extract bundle into a `run_regime_falsification` framework.

    The mapping table is CONTRACT §6 and is reproduced verbatim by the keys
    below. Nothing is invented: a quantity that is not measured is simply LEFT
    OUT, so the engine's gates read UNMEASURED rather than a fabricated zero.

        A_shape.dip_deg_p95                  -> horizons[].geometry.dip_deg
        B_differential.isopach_differential  -> intervals[].spatial_differential
        B_differential.expansion_index       -> intervals[].expansion_index
        decompaction_declared                -> intervals[].decompacted
        C_orientation.azimuth_deg            -> faults[].strike_deg (population)
        D_superposition.relations            -> cross_cutting[]
        calibration_state.problems           -> display.*
        coverage                             -> horizons[].coverage_pct

    Doctrine preserved through the wire (CONTRACT §7):
      * `expansion_index` omitted when UNMEASURED -> the engine reports
        UNMEASURED, NOT a kill. Absence of a growth wedge does not kill
        extension (a fault moving slower than sedimentation leaves no
        signature).
      * `spatial_differential` is emitted ONLY for a MEASURED differential
        ratio. ~1.0 (uniform) is false — non-discriminating, not evidence for
        the null; the engine WARNs rather than kills on that.
      * `isopach_reversal` is never emitted here — the extraction lane does not
        observe basin-scale truncation, and inventing it would fabricate an
        inversion.
      * `candidate_regimes` is NOT written into the framework: the engine does
        not consume it, and keeping the framework to engine-consumed keys only
        is what makes the returned `framework_used` a faithful audit record.
      * `decompacted` is an EXPLICIT boolean: False when the thickness
        argument was made on undecompacted isopach, which the engine reads as
        UNMEASURED (differential may be lithological).
      * `cross_cutting` is the Steno/Hutton/Lyell superposition table — NOT
        Walther's Law. A D_superposition axis emitted as a BARE `n_candidates`
        count produces no relations, because a bare gradient edge is not a
        termination (CONTRACT §4, Axis D).
    """
    b = bundle if isinstance(bundle, dict) else {}
    axes = b.get("axes") if isinstance(b.get("axes"), dict) else {}
    fw: dict[str, Any] = {}

    # ── horizons[] <- A_shape dips + aggregate coverage ─────────────────────
    dip = _measurement_value(axes, "A_shape.dip_deg_p95")
    if dip is None:
        dip = _measurement_value(axes, "A_shape.dip_deg_mean")
    cov = b.get("coverage")
    cov_pct = round(float(cov) * 100.0, 4) if isinstance(cov, (int, float)) and not isinstance(cov, bool) else None

    horizon: dict[str, Any] = {}
    if dip is not None:
        horizon["geometry"] = {"dip_deg": dip}
    if cov_pct is not None:
        horizon["coverage_pct"] = cov_pct
    if horizon:
        horizon["name"] = (b.get("horizon_names") or ["STRUCTURAL_VISION"])[0]
        fw["horizons"] = [horizon]

    # ── intervals[] <- B_differential + decompaction flag ───────────────────
    interval: dict[str, Any] = {"name": "structural_vision_interval"}

    ei = _measurement_value(axes, "B_differential.expansion_index")
    if ei is not None:
        interval["expansion_index"] = ei  # omitted when UNMEASURED -> engine UNMEASURED

    diff = _measurement_value(axes, "B_differential.isopach_differential")
    if diff is not None:
        # Spatial differential EXISTS only when the across-structure spread is
        # distinguishable from the along-structure spread. ~1.0 is uniform:
        # NON-DISCRIMINATING. Uniform thickness also arises from steady supply,
        # thermal subsidence, pure strike-slip and post-depositional sag — it is
        # not evidence of eustasy, and the engine WARNs rather than kills.
        interval["spatial_differential"] = bool(abs(float(diff) - 1.0) > 0.05)

    # An EXPLICIT boolean, always present: the absence of a decompaction flag is
    # itself the finding (K-REGIME-DECOMPACT reads a missing flag as UNMEASURED).
    interval["decompacted"] = bool(b.get("decompaction_declared"))
    if cov_pct is not None:
        interval["coverage_pct"] = cov_pct
    fw["intervals"] = [interval]

    # ── faults[] <- C_orientation azimuth population (population only) ──────
    azimuth = _measurement_value(axes, "C_orientation.azimuth_deg")
    if azimuth is None:
        azimuth = _measurement_value(axes, "C_orientation.population.circular_mean_deg")
    if azimuth is not None:
        # strike_deg is a POPULATION statistic (circular mean), never one
        # fault's azimuth dressed up as the population (CONTRACT §7.7).
        fw["faults"] = [{
            "name": "structural_vision_azimuth_population",
            "strike_deg": azimuth,
            "source": "circular_mean_of_polyline_chords",
        }]

    # ── cross_cutting[] <- D_superposition relations ────────────────────────
    d_axis = axes.get("D_superposition")
    relations: Any = None
    if isinstance(d_axis, dict):
        relations = d_axis.get("relations")
    if isinstance(relations, list) and relations:
        fw["cross_cutting"] = relations

    # ── display.* <- calibration_state (problems -> K-REGIME-DISPLAY) ───────
    cal = b.get("calibration_state") if isinstance(b.get("calibration_state"), dict) else {}
    fw["display"] = {
        "vertical_exaggeration": cal.get("vertical_exaggeration"),
        "velocity_model": bool(
            cal.get("velocity_model_present") or cal.get("interval_velocity_m_s")
        ),
        "time_domain": bool(cal.get("time_domain")),
    }
    if cal.get("problems"):
        fw["display"]["problems"] = list(cal["problems"])
    if cal.get("migration_state"):
        fw["display"]["migration_state"] = cal["migration_state"]

    # NOTE: `candidate_regimes` is deliberately NOT written into the framework.
    # The engine reads only the keys above; the candidate list is resolved by the
    # adapter from its explicit argument, falling back to the bundle. Keeping the
    # framework to engine-consumed keys only is what makes `framework_used` a
    # faithful audit record of the falsification that actually ran.

    return fw


async def geox_structural_regime_falsify(
    framework: dict[str, Any] | None = None,
    candidate_regimes: list[str] | None = None,
    min_hypotheses: int = 3,
    *,
    bundle: dict[str, Any] | None = None,
    horizons: list[dict[str, Any]] | None = None,
    intervals: list[dict[str, Any]] | None = None,
    faults: list[dict[str, Any]] | None = None,
    cross_cutting: list[dict[str, Any]] | None = None,
    display: dict[str, Any] | None = None,
    resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Falsify tectonic regimes against a structural-vision bundle.

    THIN ADAPTER ONLY. It maps the extract bundle into the `framework` dict that
    `run_regime_falsification` already consumes (CONTRACT §6) and returns that
    engine's result plus the raw bundle for traceability. There is exactly ONE
    falsifier engine in GEOX — this function must never grow a second one.

    Args:
        framework: caller-supplied framework dict (merged, caller wins).
        candidate_regimes: competing regimes to test. The engine appends the
            mandatory null hypothesis (`null_depositional`) if absent.
        min_hypotheses: engine floor on the number of competing hypotheses.
        bundle: the CONTRACT §5 bundle from geox_structural_vision_extract.
        horizons / intervals / faults / cross_cutting / display / resolution:
            optional caller-supplied framework overrides, passed through.

    Returns:
        The engine result, plus `bundle` (raw, for traceability) and
        `framework_used` (the exact mapped dict — falsifiable, auditable).
        `preferred_hypothesis` is ALWAYS None: GEOX proposes, arifOS seals.
        Unknown regimes and hypothesis-poverty propagate the engine's HOLD
        unchanged — this adapter never softens a HOLD into an ALLOW.
    """
    mapped = bundle_to_framework(bundle) if bundle else {}

    supplied = dict(framework or {})
    for key, value in (
        ("horizons", horizons),
        ("intervals", intervals),
        ("faults", faults),
        ("cross_cutting", cross_cutting),
        ("display", display),
        ("resolution", resolution),
    ):
        if value is not None:
            supplied[key] = value

    # Merge: mapped bundle is the BASE, explicit caller values override.
    merged: dict[str, Any] = dict(mapped)
    merged.update(supplied)

    bundle_regimes = (bundle or {}).get("candidate_regimes") if isinstance(bundle, dict) else None
    regimes = list(candidate_regimes or bundle_regimes or DEFAULT_CANDIDATE_REGIMES)

    engine = importlib.import_module(_TECTONIC_REGIME_MODULE)
    result = engine.run_regime_falsification(
        framework=merged,
        candidate_regimes=regimes,
        min_hypotheses=min_hypotheses,
    )
    out = dict(result) if isinstance(result, dict) else {"ok": False, "engine_result": result}

    # ── traceability: the raw bundle and the exact framework that was tested ─
    out["tool"] = "geox_structural_regime_falsify"
    out["adapter"] = "structural_vision -> run_regime_falsification (no second engine)"
    out["bundle"] = bundle if isinstance(bundle, dict) else None
    out["framework_used"] = merged
    out["candidate_regimes_used"] = regimes
    out["preferred_hypothesis"] = None  # NEVER populated by GEOX
    out["local_verdict"] = LOCAL_VERDICT
    out["seal_authority"] = SEAL_AUTHORITY
    out.setdefault("governance_status", GOVERNANCE_HOLD)
    out["doctrine"] = {
        "geometry_yields_kinematics": (
            "Geometry yields KINEMATICS. Restoration yields STRAIN. Only fault-slip "
            "inversion yields paleostress (4 of 6 parameters)."
        ),
        "unmeasured_is_not_a_kill": (
            "EI missing -> UNMEASURED. A fault moving slower than the sedimentation "
            "rate leaves no growth signature at all."
        ),
        "non_balance_is_a_diagnostic": (
            "Failure to restore means a structure is missing from the section — never "
            "that the picks were wrong."
        ),
        "uniform_thickness_is_non_discriminating": (
            "Uniform thickness favours neither eustasy nor tectonics on its own. The "
            "eustatic test is a regionally correlative surface with synchronous onlap."
        ),
        "cross_cutting_is_not_walther": (
            "Superposition is Steno 1669 / Hutton 1795 / Lyell 1830. Walther 1894 "
            "governs conformable facies succession."
        ),
    }
    return _sanitize(out)


__all__ = [
    "FORBIDDEN_PROBABILITY_KEYS",
    "aggregate_coverage",
    "assert_no_forbidden_keys",
    "bundle_to_framework",
    "geox_structural_regime_falsify",
    "geox_structural_vision_extract",
    "strip_forbidden_keys",
    "unified_status",
]