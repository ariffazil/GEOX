"""
geox_seismic_alternative_interpret.v1 — Multi-hypothesis alternative interpreter.

Per the GEOX Seismic Interpretation Forge Package + the topo_x_strat EUREKA:
- Consumes horizon artifacts (Polylines) + discriminator resource
- Generates ≥3 hypotheses (A: mobile-shale diapir, B: thrust-cored anticline,
  C: mud-volcano/MIEC feeder)
- Each hypothesis carries: required_observations, falsifiers, best_test
- ALL hypotheses start at HOLD; no auto-verdict
- Output is HYPOTHESIS-class, requires human seal or hermes witness to VERIFY

Reference: Copilot forge prompt BUILD step 5 of the section-image interpretation slice.
DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from geox.seismic.contracts import Polyline

logger = logging.getLogger("geox.seismic_alternative_interpret")

TOOL_NAME = "geox_seismic_alternative_interpret"

DEFAULT_DISCRIMINATOR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "resources", "discriminators_north_sabah.json"
)


def _load_discriminator(path: str | None = None) -> dict:
    p = path or DEFAULT_DISCRIMINATOR_PATH
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_alternative_interpret(
    horizon_artifact_ids: list[str],
    horizon_payloads: list[dict] | None = None,
    survey_id: str | None = None,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    discriminator_path: str | None = None,
    ctx: Any = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Generate ≥3 alternative interpretations of a horizon set.

    Each hypothesis starts at HOLD. No auto-verdict.

    Returns
    -------
    dict with:
      - status: OK (hypotheses generated) | HOLD (input insufficient)
      - hypotheses: list of {id, summary, required_observations, falsifiers,
                             best_test, state='HOLD', provenance}
      - claim: null
    """
    if len(horizon_artifact_ids) == 0:
        return _envelope(
            status="HOLD",
            error="at least one horizon_artifact_id required",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    disc = _load_discriminator(discriminator_path)
    hypotheses_meta = disc["hypotheses"]

    if len(hypotheses_meta) < 3:
        return _envelope(
            status="HOLD",
            error=f"discriminator resource has only {len(hypotheses_meta)} hypotheses; need ≥3",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Validate horizons if payloads provided
    valid_horizons = []
    if horizon_payloads is not None:
        for payload in horizon_payloads:
            try:
                poly = Polyline.model_validate(payload)
                valid_horizons.append(poly)
            except Exception as e:
                return _envelope(
                    status="HOLD",
                    error=f"invalid Polyline payload: {type(e).__name__}: {e}",
                    session_id=session_id, actor_id=actor_id, trace_id=trace_id,
                )

    # Generate hypotheses — ALL start at HOLD
    issued_at = datetime.now(timezone.utc).isoformat()
    hypotheses = []
    for h in hypotheses_meta:
        hypotheses.append(
            {
                "id": h["id"],
                "summary": h["summary"],
                "required_observations": list(h.get("required_observations", [])),
                "falsifiers": list(h.get("falsifiers", [])),
                "best_test": h.get("best_test"),
                "reference": h.get("reference"),
                "state": "HOLD",
                "horizon_artifact_ids": list(horizon_artifact_ids),
                "survey_id": survey_id,
                "issued_by": actor_id,
                "issued_at": issued_at,
                "provenance": {
                    "discriminator_set": disc.get("name"),
                    "discriminator_version": disc.get("version"),
                    "citation": disc.get("citation"),
                    "evidence_class": disc.get("evidence_class"),
                    "claim_ceiling": disc.get("claim_ceiling"),
                },
            }
        )

    return {
        **_envelope(
            status="OK",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        ),
        "hypotheses": hypotheses,
        "n_horizons": len(horizon_artifact_ids),
        "discriminator_set": disc.get("name"),
        "discriminator_version": disc.get("version"),
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
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_alternative_interpret)
    logger.info("Registered %s (multi-hypothesis, no-auto-verdict)", TOOL_NAME)
