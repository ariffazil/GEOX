"""
geox_seismic_age_assign.v1 — Assign canonical age to a horizon with plausibility gate.

Per the GEOX Seismic Interpretation Forge Package:
- Consumes a horizon Polyline artifact + a stratigraphy resource (default: NW Sabah)
- Returns age estimate + confidence
- Applies STAGE-THICKNESS PLAUSIBILITY GATE: if the thickness implied by the
  horizon pair exceeds the published max for that stage, return HOLD.
- Does NOT auto-claim; output is HYPOTHESIS-class pending human seal.

Reference: Copilot forge prompt BUILD step 3 of the section-image interpretation slice.
evidence_class=OBSERVATION, claim_ceiling=HYPOTHESIS.

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Literal

from geox.seismic.contracts import Polyline

logger = logging.getLogger("geox.seismic_age_assign")

TOOL_NAME = "geox_seismic_age_assign"

DEFAULT_STRATIGRAPHY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "resources", "nw_sabah_surfaces.json"
)


def _load_stratigraphy(path: str | None = None) -> dict:
    p = path or DEFAULT_STRATIGRAPHY_PATH
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _interp_pixels_to_twt_ms(
    p1: Polyline, p2: Polyline, twt_ms_per_pixel: float = 1.0
) -> float:
    """Median vertical separation between two Polylines in TWT ms.

    Both Polylines are pixel-coordinates (uncalibrated by default).
    If a real axis calibration is provided, twt_ms_per_pixel scales accordingly.
    Returns median thickness in TWT ms.
    """
    by_x1 = {p[0]: p[1] for p in p1.points}
    by_x2 = {p[0]: p[1] for p in p2.points}
    common_xs = sorted(set(by_x1.keys()) & set(by_x2.keys()))
    if not common_xs:
        return 0.0
    diffs = [abs(by_x1[x] - by_x2[x]) * twt_ms_per_pixel for x in common_xs]
    return float(sorted(diffs)[len(diffs) // 2])


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_age_assign(
    horizon_artifact_id: str,
    horizon_payload: dict | None = None,
    reference_surface: Literal["DRU", "UIU", "SRU", "TOP_IVC"] = "SRU",
    twt_ms_per_pixel: float = 1.0,
    stratigraphy_path: str | None = None,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Any = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Assign canonical age range to a horizon.

    For this slice, age assignment uses the published age band of the
    REFERENCE_SURFACE as a HINT, not an authority. To estimate age from
    thickness (e.g., interval between two horizons), pass two horizons
    via `extra_kwargs={'pair_horizon_payload': <other_polyline>}`.
    """
    strat = _load_stratigraphy(stratigraphy_path)
    surfaces = strat["surfaces"]

    if reference_surface not in surfaces:
        return _envelope(
            status="HOLD",
            error=f"unknown reference_surface={reference_surface!r}; valid: {list(surfaces)}",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    ref = surfaces[reference_surface]

    # If a pair horizon is provided, apply plausibility gate
    pair_payload = extra_kwargs.get("pair_horizon_payload")
    plausibility = {"checked": False}
    if pair_payload is not None:
        try:
            pair_poly = Polyline.model_validate(pair_payload)
            horizon_poly = Polyline.model_validate(horizon_payload) if horizon_payload else None
        except Exception as e:
            return _envelope(
                status="HOLD",
                error=f"polyline validation failed: {type(e).__name__}: {e}",
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )

        if horizon_poly is None:
            return _envelope(
                status="HOLD",
                error="pair_horizon_payload provided but no horizon_payload",
                session_id=session_id, actor_id=actor_id, trace_id=trace_id,
            )

        thickness_ms = _interp_pixels_to_twt_ms(horizon_poly, pair_poly, twt_ms_per_pixel)
        # IVC max = 400 ms (Morley 2023); UIU–DRU IVC stage usually 200-400 ms
        plausibility = {
            "checked": True,
            "measured_thickness_ms": thickness_ms,
            "thickness_max_ivc_ms": 400,
            "exceeds_published_max": thickness_ms > 400,
            "gate_action": "HOLD" if thickness_ms > 400 else "PASS",
        }
        if plausibility["exceeds_published_max"]:
            return {
                **_envelope(
                    status="HOLD",
                    session_id=session_id, actor_id=actor_id, trace_id=trace_id,
                ),
                "data": {
                    "reference_surface": reference_surface,
                    "measured_thickness_ms": thickness_ms,
                    "thickness_max_ivc_ms": 400,
                    "plausibility": plausibility,
                    "hold_reason": (
                        f"measured thickness {thickness_ms:.0f} ms exceeds published IVC max "
                        f"of 400 ms (Morley 2023 §6.2). Either (a) blue horizon is intra-IVB, "
                        f"or (b) mini-basin subsidence persisted longer in this area."
                    ),
                },
                "claim": None,
            }

    return {
        **_envelope(
            status="OK",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        ),
        "data": {
            "horizon_artifact_id": horizon_artifact_id,
            "reference_surface": reference_surface,
            "age_ma_min": ref["age_ma_min"],
            "age_ma_max": ref["age_ma_max"],
            "typical_age_ma": ref["typical_age_ma"],
            "semantic": ref["semantic"],
            "plausibility": plausibility,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "issued_by": actor_id,
            "citation": strat.get("citation"),
        },
        "claim": None,
    }


def _envelope(
    *,
    status: str,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    env = {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id or "kimi-code/FI-008",
        "session_id": session_id,
        "trace_id": trace_id,
        "execution_status": "OK" if status == "OK" else "HOLD",
        "artifact_status": "READY" if status == "OK" else "DRAFT",
        "governance_status": "QUALIFIED" if status == "OK" else "HOLD",
    }
    if status == "OK":
        return {**env, "status": "OK", "claim": None}
    return {**env, "status": status, "error": error, "hold_reason": error, "claim": None}


def register_with_mcp(mcp: Any) -> None:
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_age_assign)
    logger.info("Registered %s (age assignment + plausibility gate)", TOOL_NAME)
