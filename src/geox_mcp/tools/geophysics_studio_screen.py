"""
geophysics_studio_screen.py — GEOX GravMag Studio Screen (Stage B).

Falsification lane: takes a candidate prism model + observed anomaly grid,
forward-predicts via Stage A (`geox_gravmag_studio_open`), computes misfit,
and returns a governed verdict (PASS_SCREEN / MARGINAL / FAIL_SCREEN / HOLD)
plus a structured abduction record.

Never SEALs. Confidence capped at 0.70 per F7 HUMILITY.
All epistemic labels exposed per `contracts/geox_gravmag_studio_contract.json` v0.2.0.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any, Literal

from fastmcp import FastMCP

from geox_mcp.tools.geophysics_studio import (
    TOOL_NAME as FORWARD_TOOL_NAME,
)
from geox_mcp.tools.geophysics_studio import (
    UI_RESOURCE_URI as GRAVMAG_STUDIO_URI,
)
from geox_mcp.tools.geophysics_studio import (
    geox_gravmag_studio_open,
)

# ───────────────────────────── DOCTRINE ────────────────────────────────────────
SCREEN_TOOL_NAME = "geox_gravmag_studio_screen"
APP_VERSION_SCREEN = "0.2.0"
SCREEN_GRADE = "HYPOTHESIS_SCREEN"
SCREEN_CONFIDENCE_CAP = 0.70  # F7 HUMILITY

_VERDICT_LABELS = ("PASS_SCREEN", "MARGINAL", "FAIL_SCREEN", "HOLD")

# Default abduction library — required by doctrine whenever alternatives_declared
# is absent. Keeps the falsification lane honest.
_DEFAULT_ALTERNATIVES_GRAVITY = (
    "oceanic crust / density inversion not modelled",
    "sediment-loading gravity low not modelled",
    "unmodelled acquisition height / datum offset",
    "regional trend not removed",
    "basement roughness aliasing",
)
_DEFAULT_ALTERNATIVES_MAGNETIC = (
    "oceanic crust / stripe-averaging remanence",
    "IGRF residual leakage",
    "regional trend not removed",
    "Curie isotherm unmodelled (magnetic bottom truncation)",
    "remanence direction flipped vs present field",
)
_DEFAULT_MISSING_TESTS = (
    "independent seismic constraint",
    "well density / susceptibility measurement",
    "regional tectonic plausibility",
    "Moho / Curie depth sanity check",
    "unit and datum audit",
)


# ───────────────────────────── MATH ────────────────────────────────────────────
def _finite(x: float) -> bool:
    """True iff x is a real number (not NaN, not inf)."""
    return x == x and x not in (float("inf"), float("-inf"))


# ───────────────────────────── SOURCE GUARDS (Commit 4) ────────────────────────
# Real-data sources — require survey_type coupling, may HOLD if fetcher unreachable.
OBSERVED_SOURCE_REAL = (
    "user_upload_csv",
    "user_upload_netcdf",
    "emag2v3",
    "icgem",
)

# Synthetic sources — always allowed; used for testing + the falsification lane itself.
OBSERVED_SOURCE_SYNTHETIC_PREFIXES = ("synthetic_",)


def _is_synthetic_source(observed_source: str) -> bool:
    return any(observed_source.startswith(p) for p in OBSERVED_SOURCE_SYNTHETIC_PREFIXES)


def _validate_observed_source(observed_source: str, survey_type: str) -> str | None:
    """Validate observed_source against whitelist + survey_type coupling.

    Returns HOLD reason string on mismatch, None on pass.

    - emag2v3 requires survey_type=magnetic (global magnetic anomaly grid).
    - icgem requires survey_type=gravity (global gravity field models).
    - synthetic_* prefixed names are always allowed (testing + falsification lane).
    - Bare ``test`` / arbitrary names are rejected — be explicit.
    """
    if _is_synthetic_source(observed_source):
        return None
    if observed_source in OBSERVED_SOURCE_REAL:
        if observed_source == "emag2v3" and survey_type != "magnetic":
            return f"emag2v3 requires survey_type=magnetic, got {survey_type!r}"
        if observed_source == "icgem" and survey_type != "gravity":
            return f"icgem requires survey_type=gravity, got {survey_type!r}"
        return None
    # Bare / unrecognised names
    allowed = ", ".join(OBSERVED_SOURCE_REAL) + ", or synthetic_*"
    return f"observed_source={observed_source!r} not in whitelist ({allowed})"


def _check_fetcher_availability(observed_source: str) -> str | None:
    """Probe real-data fetcher state. Returns HOLD reason or None.

    Honest MVP: we validate the fetcher is *reachable* but defer actual
    grid extraction into a ``grid_n × grid_n`` array to a future commit
    (Commit 4 spec explicitly notes this is operator-side for now). The
    HOLD reason names the limitation so downstream consumers see this is
    a real boundary, not a silent fallback.
    """
    if _is_synthetic_source(observed_source):
        return None
    if observed_source in ("user_upload_csv", "user_upload_netcdf"):
        return None

    try:
        if observed_source == "emag2v3":
            from geox_core.io.emag2_fetcher import EMAG2Fetcher  # noqa: PLC0415

            fetcher = EMAG2Fetcher()
            result = fetcher.fetch()
            if result.mode == "offline_stub":
                return (
                    "emag2v3 in offline_stub mode (GEOX_EMAG2_OFFLINE=1). "
                    "Operator must download grid locally; auto-fetch is "
                    "intentionally disabled to prevent 500 MB pulls."
                )
            if not result.ok or result.grid_path is None:
                return "emag2v3 live fetch failed: no local grid at expected path"
            return (
                "emag2v3 grid found locally but bbox→grid extraction not yet "
                "implemented in Studio (operator-side for now). Defer to "
                "live-backend integration."
            )
        if observed_source == "icgem":
            from geox_core.io.emag2_fetcher import ICGEMFetcher  # noqa: PLC0415

            fetcher = ICGEMFetcher()
            models = fetcher.list_models()
            if not models:
                return "icgem returned no models"
            return (
                "icgem models found but bbox→grid extraction not yet "
                "implemented in Studio (operator-side for now). Defer to "
                "live-backend integration."
            )
    except Exception as exc:  # noqa: BLE001
        return f"{observed_source} fetcher raised: {exc}"

    return None


def _rms_normalized_pure(obs_flat: list[float], pred_flat: list[float]) -> tuple[float, float, float]:
    """Return (rms, rms_normalized, correlation). rms_norm = rms / range(observed).

    Pre-condition: both lists are equal length, all finite. Caller guards
    NaN/non-finite values before calling.
    """
    import math

    n_pts = len(obs_flat)
    mean_o = sum(obs_flat) / n_pts
    mean_p = sum(pred_flat) / n_pts
    diff = [o - p for o, p in zip(obs_flat, pred_flat, strict=False)]
    sq_sum = sum(d * d for d in diff)
    rms = math.sqrt(sq_sum / n_pts)

    obs_min, obs_max = min(obs_flat), max(obs_flat)
    obs_range = obs_max - obs_min
    rms_norm = (rms / obs_range) if obs_range > 0 else float("inf")

    # Pearson correlation
    cov = sum((o - mean_o) * (p - mean_p) for o, p in zip(obs_flat, pred_flat, strict=False))
    var_o = sum((o - mean_o) ** 2 for o in obs_flat)
    var_p = sum((p - mean_p) ** 2 for p in pred_flat)
    denom = math.sqrt(var_o * var_p)
    corr = (cov / denom) if denom > 0 else float("nan")
    return (rms, rms_norm, corr)


def _classify(rms_norm: float, correlation: float) -> str:
    """Verdict rubric by-construction. Returns label string only.

    Confidence is applied separately via SCREEN_CONFIDENCE_CAP so this
    function cannot accidentally exceed it.
    """
    if correlation < 0.40 or rms_norm > 0.30:
        return "FAIL_SCREEN"
    if correlation < 0.70 or rms_norm > 0.15:
        return "MARGINAL"
    return "PASS_SCREEN"


def _evidence_for(rms_norm: float, correlation: float) -> list[str]:
    out: list[str] = []
    if correlation >= 0.70:
        out.append(f"correlation r={correlation:.2f} ≥ 0.70")
    if rms_norm <= 0.15:
        out.append(f"normalized RMS={rms_norm:.2f} ≤ 0.15")
    if not out:
        out.append("insufficient positive evidence at this resolution")
    return out


def _evidence_against(rms_norm: float, correlation: float) -> list[str]:
    out: list[str] = []
    if correlation < 0.40:
        out.append(f"weak correlation r={correlation:.2f} < 0.40")
    if rms_norm > 0.30:
        out.append(f"high normalized RMS={rms_norm:.2f} > 0.30")
    if not out:
        out.append("no strong falsifying signal at this resolution")
    return out


# ───────────────────────────── ENVELOPE BUILDERS ────────────────────────────────
def _hold_envelope(reason: str) -> dict[str, Any]:
    timestamp = datetime.now(UTC).isoformat()
    return {
        "tool_name": SCREEN_TOOL_NAME,
        "claim_tag": "HYPOTHESIS_SCREEN",
        "verdict": "HOLD",
        "_meta": {
            "ui": {
                "resourceUri": GRAVMAG_STUDIO_URI,
                "mode": "inline",
                "app_id": "geox.gravmag.studio",
                "version": APP_VERSION_SCREEN,
            },
            "epistemic": {
                "grade": SCREEN_GRADE,
                "confidence": 0.0,
                "backend": "unknown",
                "labels": ["DER-misfit", "no_inversion", "no_seal", "hold"],
            },
            "provenance": {
                "tool": SCREEN_TOOL_NAME,
                "reason": reason,
                "timestamp_utc": timestamp,
            },
        },
        "output": {
            "predicted_grid": None,
            "residual_grid": None,
            "rms": None,
            "rms_normalized": None,
            "correlation": None,
            "units": None,
        },
        "abduction": {
            "primary_hypothesis": "Cannot evaluate.",
            "evidence_for": [],
            "evidence_against": [],
            "alternatives": [],
            "missing_tests": list(_DEFAULT_MISSING_TESTS),
        },
        "governance": {
            "requires_888_hold": True,
            "verdict": "HOLD",
            "next_valid_actions": ["fix_input", "realign_units", "realign_grid"],
            "not_allowed_actions": ["seal_claim", "issue_drilling_recommendation"],
            "hold_reason": reason,
        },
    }


# ───────────────────────────── TOOL ENTRY ──────────────────────────────────────
async def geox_gravmag_studio_screen(
    survey_type: Literal["gravity", "magnetic"],
    prisms: list[dict],
    grid_extent_m: float,
    grid_n: int,
    observed_grid: list[list[float]],
    observed_units: Literal["mGal", "nT"],
    observed_source: str,
    magnetization_a_m: float = 0.0,
    field_declination_deg: float = 0.0,
    field_inclination_deg: float = 5.0,
    backend: Literal["auto", "mock", "harmonica_live"] = "auto",
    alternatives_declared: list[str] | None = None,
    observed_extent_m: float | None = None,
) -> dict[str, Any]:
    """GEOX GravMag Studio — Stage B screen (falsification lane).

    Forward-predicts via ``geox_gravmag_studio_open``, compares against
    ``observed_grid``, returns misfit stats + governed verdict + abduction
    discipline record.

    Falsification guardrails:
      * unit, grid shape, or grid extent mismatch → verdict ``HOLD``
      * confidence capped at 0.70 by construction (F7 HUMILITY)
      * never emits ``SEAL``
      * must attach at least one alternative model (auto-populated if absent)
      * ``missing_tests`` always non-empty
      * raw verdict inputs (rms, rms_normalized, correlation) recorded in provenance

    Args:
        survey_type: ``gravity`` or ``magnetic``.
        prisms: List of prism dicts (same shape as Stage A input).
        grid_extent_m: Half-extent of survey grid (m).
        grid_n: Grid samples per axis (must match ``observed_grid`` shape).
        observed_grid: 2D list-of-lists ``[ny][nx]`` of observed anomaly.
        observed_units: ``mGal`` (gravity) or ``nT`` (magnetic).
        observed_source: Provenance string e.g. ``"EMAG2v3"`` / ``"ICGEM"`` /
            ``"user_upload"``.
        magnetization_a_m: Effective magnetization (A/m), magnetic only.
        field_declination_deg: Earth's field declination (°), magnetic.
        field_inclination_deg: Earth's field inclination (°), magnetic.
        backend: ``auto`` / ``mock`` / ``harmonica_live``.
        alternatives_declared: Optional explicit alternative-Earth-models
            list. If absent, doctrine-default library is auto-attached.
        observed_extent_m: Optional half-extent (m) of the observed grid in
            metres. If supplied, must equal ``grid_extent_m`` within 1 m
            tolerance — silent extent mismatch is a common physics footgun.

    Returns:
        dict conforming to ``contracts/geox_gravmag_studio_contract.json``
        v0.2.0 with screen-mode fields populated.
    """
    timestamp = datetime.now(UTC).isoformat()

    # ── observed_source whitelist + survey-type guard (Commit 4) ──────────
    src_err = _validate_observed_source(observed_source, survey_type)
    if src_err:
        return _hold_envelope(reason=src_err)

    # ── Fetcher availability probe (Commit 4 — defer if not ready) ─────────
    fetch_err = _check_fetcher_availability(observed_source)
    if fetch_err:
        return _hold_envelope(reason=fetch_err)

    # ── Unit sanity gate (fail-closed) ──────────────────────────────────────
    expected_units = "mGal" if survey_type == "gravity" else "nT"
    if observed_units != expected_units:
        return _hold_envelope(reason=f"observed.units={observed_units} ≠ expected {expected_units} for survey_type={survey_type}")

    # ── Grid shape sanity gate (fail-closed) ───────────────────────────────
    if not observed_grid or not isinstance(observed_grid, list):
        return _hold_envelope(reason="observed_grid is empty or not a list")
    ny_obs = len(observed_grid)
    nx_obs = len(observed_grid[0]) if ny_obs > 0 else 0
    if ny_obs != grid_n or nx_obs != grid_n:
        return _hold_envelope(reason=f"observed_grid shape ({ny_obs}x{nx_obs}) ≠ grid_n² ({grid_n}x{grid_n})")
    # Verify rectangularity
    for row in observed_grid:
        if len(row) != nx_obs:
            return _hold_envelope(reason="observed_grid is not rectangular")

    # ── Grid extent sanity gate (fail-closed, tightening #3) ──────────────
    if observed_extent_m is not None and abs(observed_extent_m - grid_extent_m) > 1.0:
        return _hold_envelope(reason=f"observed extent {observed_extent_m} m ≠ predicted {grid_extent_m} m (tolerance 1 m)")

    # ── Forward predict via Stage A (reuse — no new physics) ───────────────
    forward_kwargs: dict[str, Any] = dict(
        survey_type=survey_type,
        prisms=prisms,
        grid_extent_m=grid_extent_m,
        grid_n=grid_n,
        backend=backend,
    )
    if survey_type == "magnetic":
        forward_kwargs.update(
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
        )

    try:
        forward_result = await geox_gravmag_studio_open(**forward_kwargs)
    except Exception as exc:  # noqa: BLE001 — fail-closed envelope on any engine error
        return _hold_envelope(reason=f"forward engine raised: {exc}")

    if forward_result.get("verdict") == "VOID":
        return _hold_envelope(reason=f"forward tool returned VOID: {forward_result.get('caveats', ['unknown'])[0]}")

    pred_flat = forward_result["render_payload"]["anomaly_values"]
    nx = forward_result["render_payload"]["grid_shape"][1]
    ny = forward_result["render_payload"]["grid_shape"][0]
    predicted_grid = [pred_flat[i * nx : (i + 1) * nx] for i in range(ny)]

    # ── Misfit math with explicit NaN guard (tightening #2) ────────────────
    obs_flat = []
    pred_flat_clean = []
    for o_row, p_row in zip(observed_grid, predicted_grid, strict=False):
        for o_v, p_v in zip(o_row, p_row, strict=False):
            try:
                of = float(o_v)
                pf = float(p_v)
            except (TypeError, ValueError):
                continue
            if not _finite(of) or not _finite(pf):
                continue
            obs_flat.append(of)
            pred_flat_clean.append(pf)
    if not obs_flat:
        return _hold_envelope(reason="all-NaN observed vs predicted overlap")
    rms, rms_norm, correlation = _rms_normalized_pure(obs_flat, pred_flat_clean)
    if not _finite(correlation):
        return _hold_envelope(reason="undefined correlation (zero variance grid)")
    if not _finite(rms_norm):
        return _hold_envelope(reason="undefined normalized RMS (zero-range observed grid)")

    # Verdict rubric by construction (tightening #4)
    label = _classify(rms_norm, correlation)
    # Confidence cap is SCREEN_CONFIDENCE_CAP itself (by-construction, no
    # path can exceed it because _classify no longer carries a confidence).
    capped_confidence = SCREEN_CONFIDENCE_CAP

    # NaN-safe residual
    residual_grid: list[list[float]] = []
    max_abs = 0.0
    for o_row, p_row in zip(observed_grid, predicted_grid, strict=False):
        res_row: list[float] = []
        for o_v, p_v in zip(o_row, p_row, strict=False):
            if o_v != o_v or p_v != p_v:
                res_row.append(float("nan"))
                continue
            r = float(o_v) - float(p_v)
            res_row.append(r)
            if abs(r) > max_abs:
                max_abs = abs(r)
        residual_grid.append(res_row)

    # ── Abduction discipline (auto-populate if absent) ────────────────────
    alternatives = (
        list(alternatives_declared)
        if alternatives_declared
        else (list(_DEFAULT_ALTERNATIVES_GRAVITY) if survey_type == "gravity" else list(_DEFAULT_ALTERNATIVES_MAGNETIC))
    )

    # ── Vault receipt (audit, not SEAL) ────────────────────────────────────
    input_payload = {
        "survey_type": survey_type,
        "prisms": prisms,
        "grid_extent_m": grid_extent_m,
        "grid_n": grid_n,
        "observed_units": observed_units,
        "observed_source": observed_source,
        "backend": backend,
    }
    input_hash = hashlib.sha256(
        # Lazy import of json — keep top of file minimal
        __import__("json").dumps(input_payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    response: dict[str, Any] = {
        "tool_name": SCREEN_TOOL_NAME,
        "claim_tag": "HYPOTHESIS_SCREEN",
        "verdict": label,
        "_meta": {
            "ui": {
                "resourceUri": GRAVMAG_STUDIO_URI,
                "mode": "inline",
                "app_id": "geox.gravmag.studio",
                "version": APP_VERSION_SCREEN,
                "event": "geox.gravmag.screen",
            },
            "epistemic": {
                "grade": SCREEN_GRADE,
                "confidence": capped_confidence,
                "backend": forward_result["render_payload"]["backend"],
                "labels": ["DER-misfit", "no_inversion", "no_seal"],
            },
            "provenance": {
                "tool": SCREEN_TOOL_NAME,
                "forward_tool": FORWARD_TOOL_NAME,
                "forward_version": forward_result.get("ui", {}).get("version", "unknown"),
                "observed_source": observed_source,
                "observed_units": observed_units,
                "timestamp_utc": timestamp,
                "input_hash": input_hash,
                "rms": rms,
                "rms_normalized": rms_norm,
                "correlation": correlation,
                "verdict": label,
            },
        },
        "output": {
            "predicted_grid": predicted_grid,
            "residual_grid": residual_grid,
            "rms": rms,
            "rms_normalized": rms_norm,
            "max_abs_residual": max_abs,
            "correlation": correlation,
            "units": expected_units,
            "grid_shape": [ny, nx],
        },
        "abduction": {
            "primary_hypothesis": "Candidate prism explains observed anomaly.",
            "evidence_for": _evidence_for(rms_norm, correlation),
            "evidence_against": _evidence_against(rms_norm, correlation),
            "alternatives": alternatives,
            "missing_tests": list(_DEFAULT_MISSING_TESTS),
        },
        "governance": {
            "requires_888_hold": True,
            "verdict": label,
            "next_valid_actions": [
                "attach_evidence",
                "propose_alternative_model",
                "escalate_to_joint_inversion",
            ],
            "not_allowed_actions": [
                "seal_claim",
                "issue_drilling_recommendation",
            ],
        },
    }
    return response


# ───────────────────────────── REGISTRATION ───────────────────────────────────
def register_gravmag_studio_screen_tools(mcp: FastMCP) -> None:
    """Register geox_gravmag_studio_screen as an MCP tool."""

    @mcp.tool(
        name=SCREEN_TOOL_NAME,
        description=(
            "GEOX GravMag Studio v0.2.0 — Screen mode (falsification lane). "
            "Forward-predicts via geox_gravmag_studio_open, compares against "
            "observed_grid, returns misfit + verdict (PASS_SCREEN / MARGINAL / "
            "FAIL_SCREEN / HOLD) + abduction discipline. Never SEALs. "
            "Confidence capped at 0.70 per F7 HUMILITY."
        ),
        annotations={
            "read_only": True,
            "destructive": False,
            "idempotent": True,
        },
    )
    async def _tool(
        survey_type: Literal["gravity", "magnetic"],
        prisms: list[dict],
        grid_extent_m: float,
        grid_n: int,
        observed_grid: list[list[float]],
        observed_units: Literal["mGal", "nT"],
        observed_source: str,
        magnetization_a_m: float = 0.0,
        field_declination_deg: float = 0.0,
        field_inclination_deg: float = 5.0,
        backend: Literal["auto", "mock", "harmonica_live"] = "auto",
        alternatives_declared: list[str] | None = None,
    ) -> dict[str, Any]:
        return await geox_gravmag_studio_screen(
            survey_type=survey_type,
            prisms=prisms,
            grid_extent_m=grid_extent_m,
            grid_n=grid_n,
            observed_grid=observed_grid,
            observed_units=observed_units,
            observed_source=observed_source,
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
            backend=backend,
            alternatives_declared=alternatives_declared,
        )


__all__ = [
    "SCREEN_TOOL_NAME",
    "APP_VERSION_SCREEN",
    "SCREEN_GRADE",
    "SCREEN_CONFIDENCE_CAP",
    "geox_gravmag_studio_screen",
    "register_gravmag_studio_screen_tools",
]
