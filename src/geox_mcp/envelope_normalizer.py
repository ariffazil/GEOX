"""
envelope_normalizer — P0-4 D.4+D.5 (2026-07-25 · FI-008).

Middleware-side guarantee that every mutating tool's response carries
the audit-defined 5-status contract:

  transport_status, execution_status, artifact_status,
  verification_status, governance_verdict, claim_state

If the tool body did NOT produce an envelope (most legacy paths), this
module synthesizes one with ``verification_status=UNVERIFIED`` and
``receipt.state=PENDING`` so callers always see a complete contract.

D.5 floor enforcement: when the synthesized envelope has empty required
fields AND the original tool returned a ``status: OK`` claim, the
governance_verdict is DOWNGRADED from SEAL to HOLD and the tool's
returned ``status`` is rewritten to ``ENVELOPE_INCOMPLETE``.

REVERSIBILITY
=============

The middleware hook in ``geox_middleware.GeoxGovernanceMiddleware.on_call_tool``
calls ``normalize_envelope_for_mutation`` ONLY for tools whose manifest
action_class is MUTATE or whose mutating-arg overrides fire. Read-only
tool returns pass through untouched.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("geox_mcp.envelope_normalizer")

# Required envelope fields per the audit's "Required architecture correction".
REQUIRED_ENVELOPE_FIELDS: tuple[str, ...] = (
    "transport_status",
    "execution_status",
    "artifact_status",
    "verification_status",
    "governance_verdict",
    "claim_state",
)

# Fields the receipt block must carry.
REQUIRED_RECEIPT_FIELDS: tuple[str, ...] = ("state", "ref")


def envelope_is_complete(env: dict[str, Any]) -> bool:
    """Return True iff every required envelope field is present and non-empty."""
    if not isinstance(env, dict):
        return False
    for key in REQUIRED_ENVELOPE_FIELDS:
        val = env.get(key)
        if val is None or val == "" or val == {}:
            return False
    receipt = env.get("receipt")
    if not isinstance(receipt, dict):
        return False
    for key in REQUIRED_RECEIPT_FIELDS:
        if key not in receipt:
            return False
    return True


def synthesize_envelope(
    *,
    tool_name: str,
    result: Any,
    actor_id: str | None,
    session_id: str | None,
    verification_status: str = "UNVERIFIED",
    receipt_state: str = "PENDING",
    receipt_ref: str | None = None,
) -> dict[str, Any]:
    """Build the canonical envelope around a tool's result.

    Used when the tool body did NOT produce one. Defaults are the safe
    fail-soft values: UNVERIFIED verification, PENDING receipt.
    """
    # Detect execution_status from result content if possible.
    exec_status = "COMPLETED"
    artifact_status = "OK"
    if isinstance(result, dict):
        if result.get("status") == "INVALID":
            exec_status = "REJECTED"
            artifact_status = "REJECTED"
        elif result.get("status") == "ERROR":
            exec_status = "ERROR"
            artifact_status = "ERROR"
    claim_state = "COMPUTED" if exec_status == "COMPLETED" else "HYPOTHESIS"

    env: dict[str, Any] = {
        "transport_status": "OK",
        "execution_status": exec_status,
        "artifact_status": artifact_status,
        "verification_status": verification_status,
        "governance_verdict": "HOLD",  # never claim SEAL without verification
        "claim_state": claim_state,
        "actor_id": actor_id or "anonymous",
        "session_id": session_id or "anonymous",
        "artifact": {"id": "", "sha256": ""},
        "receipt": {"state": receipt_state, "ref": receipt_ref},
    }
    return env


def normalize_envelope_for_mutation(
    *,
    tool_name: str,
    result: Any,
    arguments: dict[str, Any] | None,
) -> Any:
    """If ``result`` lacks an envelope, synthesize one and downgrade verdict.

    Returns ``result`` unchanged for:
      - non-dict results
      - dicts that already carry a complete envelope (D.3 wired this in)
      - read-only tools (manifest action_class OBSERVE + no overrides)

    For mutating tools with incomplete envelopes, attaches an envelope
    and rewrites ``status`` to ENVELOPE_INCOMPLETE so the agent can't
    falsely claim SUCCESS.
    """
    from geox_mcp.registry import is_mutating_call

    if not isinstance(result, dict):
        return result
    if not is_mutating_call(tool_name, arguments or {}):
        return result

    existing = result.get("envelope")
    if isinstance(existing, dict) and envelope_is_complete(existing):
        # Already has a valid envelope — D.3 path. Pass through.
        return result

    # Tool body did NOT produce a complete envelope. Synthesize one.
    actor_id = (arguments or {}).get("actor_id") if isinstance(arguments, dict) else None
    session_id = (arguments or {}).get("session_id") if isinstance(arguments, dict) else None

    # If the tool produced some envelope-shaped data, preserve what we can.
    verification_status = "UNVERIFIED"
    receipt_state = "PENDING"
    receipt_ref: str | None = None
    if isinstance(existing, dict):
        verification_status = existing.get("verification_status") or verification_status
        receipt = existing.get("receipt")
        if isinstance(receipt, dict):
            receipt_state = receipt.get("state") or receipt_state
            receipt_ref = receipt.get("ref") or receipt_ref

    env = synthesize_envelope(
        tool_name=tool_name,
        result=result,
        actor_id=actor_id,
        session_id=session_id,
        verification_status=verification_status,
        receipt_state=receipt_state,
        receipt_ref=receipt_ref,
    )
    env["synthesized_by_middleware"] = True

    out = dict(result)
    out["envelope"] = env

    # D.5 floor enforcement: when the middleware had to SYNTHESIZE the
    # envelope (i.e. the tool body did not call seal_receipt/verify_artifact),
    # downgrade the tool's claim from OK/SUCCESS to ENVELOPE_INCOMPLETE.
    # The audit is explicit: "Final task success is impossible unless
    # required acceptance fields are non-empty" — synthesized defaults do
    # NOT count as authentic acceptance.
    if isinstance(out.get("status"), str) and out["status"] in ("OK", "SUCCESS"):
        out["status"] = "ENVELOPE_INCOMPLETE"
        env["governance_verdict"] = "HOLD"
        env["verification_reason"] = (
            "synthesized by middleware — tool body did not call "
            "seal_receipt / verify_artifact"
        )
        logger.warning(
            "ENVELOPE_INCOMPLETE: tool=%s returned status=%s without a "
            "complete envelope — downgraded to ENVELOPE_INCOMPLETE / HOLD",
            tool_name,
            result.get("status"),
        )

    return out
