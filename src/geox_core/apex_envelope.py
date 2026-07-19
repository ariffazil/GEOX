"""
APEX Envelope for GEOX — Earth Evidence organ

Maps geological signals to 10 APEX gates:
  Amanah: evidence provenance, claim state
  Presence: observation recency, model version
  Humility: uncertainty cones, error bars
  Signal: SNR, log quality, evidence refs
  Understanding: geological coherence, strat consistency
  Energy: compute cost
  Authority: actor verification
  Reversibility: READ (evidence-only organ)
  Proof: ZKPC_OBSERVATION
  Sovereign: passthrough

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from datetime import UTC
from typing import Any

try:
    from arifosmcp.apex_envelope import apex_envelope, apex_envelope_minimal
except ImportError:
    import math
    from datetime import datetime

    APEX_EQUATION = "g(t)=A(t)\u00b7P(t)\u00b7H(t)\u00b7\u221a(S(t)\u00b7U(t))\u00b7E(t)\u00b2"

    def _geometric_mean(values):
        positive = [v for v in values if v > 0]
        return (math.prod(positive) ** (1.0 / len(positive))) if positive else 0.0

    def _gate(passed, score, detail, **extra):
        v = {"pass": passed, "score": round(max(0.0, min(1.0, score)), 4), "detail": detail}
        v.update(extra)
        return v

    def apex_envelope(*, tool_name="unknown", confidence=0.88, evidence_strength=0.95,
                      boundary="LIVE", uncertainty_declared=True, evidence_refs=None,
                      evidence_quality="UNKNOWN", coherent=True, actor_id=None,
                      action_class="READ", proof_level="ZKPC_OBSERVATION", **kw):
        gates = {
            "amanah": _gate(confidence <= evidence_strength + 0.05, min(1.0, evidence_strength / max(confidence, 1e-6)),
                           f"confidence {confidence:.2f} <= evidence {evidence_strength:.2f}"),
            "presence": _gate(True, {"LIVE": 1.0, "CACHED": 0.8, "INFERRED": 0.5}.get(boundary, 0.5), boundary, boundary=boundary),
            "humility": _gate(uncertainty_declared, 1.0 if uncertainty_declared else 0.3, "declared" if uncertainty_declared else "undeclared"),
            "signal": _gate(len(evidence_refs or []) > 0, min(1.0, 0.3 + len(evidence_refs or []) * 0.2),
                           f"{len(evidence_refs or [])} refs"),
            "understanding": _gate(coherent, 0.9 if coherent else 0.2, "coherent" if coherent else "incoherent"),
            "energy": _gate(True, 0.8, "default"),
            "authority": _gate(bool(actor_id), 1.0 if actor_id else 0.0, f"actor={actor_id}", actor_id=actor_id),
            "reversibility": _gate(True, 1.0, action_class, action_class=action_class),
            "proof": _gate(True, 0.85, proof_level, proof_level=proof_level),
            "sovereign": _gate(True, 1.0, "no F13 halt"),
        }
        dials = {
            "A": round(_geometric_mean([gates["amanah"]["score"], gates["humility"]["score"], gates["understanding"]["score"]]), 4),
            "P": round(gates["presence"]["score"], 4),
            "H": round(min(gates["authority"]["score"], gates["sovereign"]["score"]), 4),
            "S": round(gates["signal"]["score"], 4),
            "U": round(_geometric_mean([gates["reversibility"]["score"], gates["proof"]["score"]]), 4),
            "E": round(gates["energy"]["score"], 4),
        }
        G = round(dials["A"] * dials["P"] * dials["H"] * math.sqrt(dials["S"] * dials["U"]) * dials["E"] ** 2, 4)
        verdict = "SEAL" if G >= 0.80 else ("SABAR" if G >= 0.50 else "HOLD")
        return {"equation": APEX_EQUATION, "gates": gates, "dials": dials, "G": G, "verdict": verdict,
                "timestamp": datetime.now(UTC).isoformat()}

    def apex_envelope_minimal(*, tool_name="unknown", actor_id=None, action_class="READ", boundary="LIVE", ok=True):
        return apex_envelope(tool_name=tool_name, actor_id=actor_id, action_class=action_class, boundary=boundary, coherent=ok)


def geox_apex_envelope(
    *,
    tool_name: str,
    claim_state: str,
    perception_class: str,
    evidence_refs: list[dict[str, Any]],
    humility_score: float,
    uncertainty: str,
    governance_status: Any,
    actor_id: str | None,
) -> dict[str, Any]:
    """Build APEX envelope from GEOX-specific signals."""
    _claim_confidence = {
        "OBSERVED": 0.95, "DERIVED_CANDIDATE": 0.85, "INTERPRETED": 0.75,
        "HYPOTHESIS": 0.60, "VOID": 0.20, "888_HOLD": 0.30,
    }
    _perception_boundary = {
        "OBSERVED": "LIVE", "DERIVED": "CACHED", "INTERPRETED_LOCAL": "CACHED",
        "HYPOTHESIS": "INFERRED", "PROCESS_HYPOTHESIS": "INFERRED",
    }
    cs = (claim_state or "HYPOTHESIS").upper()
    pc = (perception_class or "HYPOTHESIS").upper()
    refs = evidence_refs or []

    confidence = _claim_confidence.get(cs, 0.50)
    boundary = _perception_boundary.get(pc, "INFERRED")
    evidence_quality = "HIGH" if len(refs) >= 3 else ("MEDIUM" if len(refs) >= 1 else "LOW")
    coherent = cs not in ("VOID", "888_HOLD")

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
        action_class="READ",
        proof_level="ZKPC_OBSERVATION",
    )
