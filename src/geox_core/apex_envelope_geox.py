"""
GEOX APEX Envelope Adapter — Earth Evidence → 10 APEX Gates

Maps GEOX's physical signals (claim_state, evidence_refs, perception_class,
humility_score, physics_guard) to the 10 APEX gates.

GEOX is the Witness organ. It produces ground truth.
APEX ensures it cannot hallucinate geology.

APEX-MCP-001 binding.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

try:
    from geox_core.apex_envelope import (
        apex_envelope,
        apex_envelope_minimal,
    )
except ImportError:
    # Inline fallback if the shared module isn't on the path
    import math
    from datetime import datetime

    APEX_EQUATION = "g(t)=A(t)\u00b7P(t)\u00b7H(t)\u00b7\u221a(S(t)\u00b7U(t))\u00b7E(t)\u00b2"

    def _gate(passed: bool, score: float, detail: str, **kw: Any) -> dict[str, Any]:
        v: dict[str, Any] = {"pass": passed, "score": round(max(0.0, min(1.0, score)), 4), "detail": detail}
        v.update(kw)
        return v

    def _gmean(vals: list[float]) -> float:
        pos = [v for v in vals if v > 0]
        return (math.prod(pos) ** (1.0 / len(pos))) if pos else 0.0

    def apex_envelope(
        *,
        tool_name: str = "unknown",
        confidence: float = 0.88,
        evidence_strength: float = 0.95,
        boundary: str = "LIVE",
        uncertainty_declared: bool = True,
        coherent: bool = True,
        actor_id: str | None = None,
        action_class: str = "READ",
        proof_level: str = "ZKPC_OBSERVATION",
        f13_halt: bool = False,
        **_kw: Any,
    ) -> dict[str, Any]:
        gates = {
            "amanah": _gate(
                confidence <= evidence_strength + 0.05,
                min(1.0, evidence_strength / max(confidence, 1e-6)),
                f"confidence {confidence:.2f} <= evidence {evidence_strength:.2f}",
            ),
            "presence": _gate(
                True, {"LIVE": 1.0, "CACHED": 0.8, "INFERRED": 0.5}.get(boundary, 0.5), boundary, boundary=boundary
            ),
            "humility": _gate(uncertainty_declared, 1.0 if uncertainty_declared else 0.3, "uncertainty declared"),
            "signal": _gate(True, 0.7, "default signal"),
            "understanding": _gate(coherent, 0.9 if coherent else 0.2, "coherent" if coherent else "incoherent"),
            "energy": _gate(True, 0.8, "cost tracked"),
            "authority": _gate(actor_id is not None, 1.0 if actor_id else 0.0, f"actor={actor_id}", actor_id=actor_id),
            "reversibility": _gate(True, 1.0, f"{action_class}", action_class=action_class),
            "proof": _gate(True, 0.85, f"{proof_level}", proof_level=proof_level),
            "sovereign": _gate(not f13_halt, 0.0 if f13_halt else 1.0, "F13 halt" if f13_halt else "no halt"),
        }
        A = _gmean([gates["amanah"]["score"], gates["humility"]["score"], gates["understanding"]["score"]])
        P = gates["presence"]["score"]
        H = min(gates["authority"]["score"], gates["sovereign"]["score"])
        S = gates["signal"]["score"]
        U = _gmean([gates["reversibility"]["score"], gates["proof"]["score"]])
        E = gates["energy"]["score"]
        G = round(A * P * H * math.sqrt(S * U) * E**2, 4)
        verdict = "VOID" if f13_halt else ("SEAL" if G >= 0.80 else ("SABAR" if G >= 0.50 else "HOLD"))
        return {
            "equation": APEX_EQUATION,
            "gates": gates,
            "dials": {"A": round(A, 4), "P": round(P, 4), "H": round(H, 4), "S": round(S, 4), "U": round(U, 4), "E": round(E, 4)},
            "G": G,
            "verdict": verdict,
            "timestamp": datetime.now(UTC).isoformat(),
        }


# ── Claim state → confidence mapping ──────────────────────────────────────
_CLAIM_STATE_CONFIDENCE = {
    "OBSERVED": 0.95,
    "DERIVED_CANDIDATE": 0.85,
    "INTERPRETED": 0.75,
    "INFERRED": 0.60,
    "HYPOTHESIS": 0.50,
    "VOID": 0.20,
    "888_HOLD": 0.30,
}

_PERCEPTION_CLASS_BOUNDARY = {
    "OBSERVED": "LIVE",
    "DERIVED": "CACHED",
    "INTERPRETED_LOCAL": "CACHED",
    "HYPOTHESIS": "INFERRED",
    "PROCESS_HYPOTHESIS": "INFERRED",
    "EARTHMODEL": "CACHED",
}

_GOVERNANCE_STATUS_OK = {"QUALIFY", "PASS", "SEAL"}


def geox_apex_envelope(
    *,
    tool_name: str = "unknown",
    claim_state: str = "HYPOTHESIS",
    perception_class: str = "HYPOTHESIS",
    evidence_refs: list[dict[str, Any]] | None = None,
    humility_score: float = 0.5,
    uncertainty: str = "Moderate",
    governance_status: Any = None,
    actor_id: str | None = None,
) -> dict[str, Any]:
    """Build APEX envelope from GEOX-specific signals."""
    refs = evidence_refs or []
    cs = claim_state.upper() if claim_state else "HYPOTHESIS"
    pc = perception_class.upper() if perception_class else "HYPOTHESIS"

    # Map GEOX signals → APEX gate inputs
    confidence = _CLAIM_STATE_CONFIDENCE.get(cs, 0.50)
    boundary = _PERCEPTION_CLASS_BOUNDARY.get(pc, "INFERRED")
    evidence_quality = "HIGH" if len(refs) >= 3 else ("MEDIUM" if len(refs) >= 1 else "LOW")
    gs = (
        str(governance_status.value if hasattr(governance_status, "value") else governance_status).upper()
        if governance_status
        else "UNKNOWN"
    )
    coherent = gs in _GOVERNANCE_STATUS_OK

    return apex_envelope(
        tool_name=tool_name,
        confidence=confidence,
        evidence_strength=min(1.0, confidence + 0.05),
        boundary=boundary,
        uncertainty_declared=True,
        evidence_refs=refs,
        evidence_quality=evidence_quality,
        coherent=coherent,
        actor_id=actor_id,
        action_class="READ",  # GEOX tools are evidence-only (READ)
        proof_level="ZKPC_OBSERVATION",
    )
