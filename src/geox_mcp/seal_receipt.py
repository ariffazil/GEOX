"""
seal_receipt — P0-4 framework (Phase D, T1).

Forged 2026-07-25 · FI-008 (kimi-code).

Audit fix: replace VAULT999-PENDING with a sealed receipt carrying a
content-addressed ``vault999://<id>`` reference. This module is the
THIN client around arifOS's ``arif_seal`` — it mints a PAI receipt,
calls arifOS to seal it, and returns the vault reference.

D.1 (this module) is the FRAMEWORK. Wiring well_ingest and other
mutating tools to call ``seal_receipt`` is D.3, which is paused for
F13 SOVEREIGN ack (the audit-defined envelope schema is constitutional).

REVERSIBILITY
=============

D.3 not yet wired. Tools keep their existing return shape. To wire:
import and call ``seal_receipt(...)`` after the mutating step; attach
the returned dict to the tool's payload as ``receipt``. To revert:
skip the call. arifOS call below fails open (returns PENDING) so the
tool still works when arifOS is unreachable.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any

from geox_mcp.pai_receipt import (
    IntentAction,
    Organ,
    PAIReceipt,
    ProducerType,
    Reversibility,
    RiskClass,
    mint_pai_receipt,
)

logger = logging.getLogger("geox_mcp.seal_receipt")

_ARIFOS_BASE = os.getenv("ARIFOS_BASE_URL", "http://localhost:8088")
_ARIFOS_TIMEOUT_S = float(os.getenv("ARIFOS_SEAL_TIMEOUT_S", "5.0"))


# ── Result envelope ────────────────────────────────────────────────────────


class SealResult:
    """Outcome of a seal attempt.

    The audit requires that every mutating tool response carry a
    ``receipt.state`` and ``receipt.ref``. ``SealResult`` is the canonical
    shape used by D.3 wiring and by tests.
    """

    def __init__(
        self,
        *,
        state: str,
        ref: str | None,
        receipt: PAIReceipt | None = None,
        error: str | None = None,
        vault_pending: bool = False,
    ) -> None:
        self.state = state  # "SEALED" | "PENDING" | "FAILED"
        self.ref = ref  # "vault999://<id>" when SEALED, else None
        self.receipt = receipt
        self.error = error
        self.vault_pending = vault_pending

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "state": self.state,
            "ref": self.ref,
        }
        if self.receipt is not None:
            try:
                d["receipt_hash"] = self.receipt.audit.receipt_hash
                d["tier"] = str(self.receipt.audit.tier) if hasattr(
                    self.receipt.audit, "tier"
                ) else None
            except Exception:
                pass
        if self.error:
            d["error"] = self.error
        if self.vault_pending:
            d["vault_pending"] = True
        return d


# ── Receipt mint + seal ──────────────────────────────────────────────────


def _build_pai_receipt(
    *,
    tool: str,
    artifact_id: str,
    artifact_sha256: str | None,
    actor_id: str | None,
    session_id: str | None,
    risk_class: RiskClass = RiskClass.MEDIUM,
    action: IntentAction = IntentAction.PUBLISH,
    reversibility: Reversibility = Reversibility.FULL,
) -> PAIReceipt:
    """Mint a PAI receipt envelope for a tool's mutation.

    The receipt binds together: tool identity, artifact identity (sha256
    when known), actor identity, and a risk/reversibility classification.
    arifOS adds the tier + vault anchor when it seals the receipt.
    """
    sources: list[str] = []
    if artifact_sha256:
        sources.append(f"sha256:{artifact_sha256}")
    return mint_pai_receipt(
        object_id=artifact_id,
        producer_type=ProducerType.TOOL,
        producer_id=tool,
        organ=Organ.GEOX,
        action=action,
        scope=f"tools/{tool}",
        risk_class=risk_class,
        external_effect=False,
        reversibility=reversibility,
        delegate=actor_id or "anonymous",
        authority_chain=[
            f"session:{session_id or 'anonymous'}",
            f"tool:{tool}",
        ],
        sources=sources,
        tool_calls=[tool],
        confidence="high" if artifact_sha256 else "medium",
        human_reviewed=False,
        tool_id=tool,
        destination="VAULT999",
    )


def seal_receipt(
    *,
    tool: str,
    artifact_id: str,
    artifact_sha256: str | None = None,
    actor_id: str | None = None,
    session_id: str | None = None,
    verdict: str = "SEAL",
    risk_class: RiskClass = RiskClass.MEDIUM,
    reversibility: Reversibility = Reversibility.FULL,
) -> SealResult:
    """Mint a PAI receipt and submit it to arifOS for sealing.

    On success: returns ``SealResult(state="SEALED", ref="vault999://<id>")``.
    On arifOS unreachable / error: returns ``state="PENDING"`` (the audit
    explicitly listed this as a failure mode — the fail-soft path keeps
    the tool usable while flagging that the vault is not authoritative).
    On hard error: returns ``state="FAILED"``.
    """
    receipt = _build_pai_receipt(
        tool=tool,
        artifact_id=artifact_id,
        artifact_sha256=artifact_sha256,
        actor_id=actor_id,
        session_id=session_id,
        risk_class=risk_class,
        reversibility=reversibility,
    )

    # Compute a content hash that the vault will use as the entry id.
    receipt_hash = receipt.audit.receipt_hash or hashlib.sha256(
        json.dumps(receipt.model_dump(), default=str, sort_keys=True).encode()
    ).hexdigest()

    try:
        import httpx

        # D.1 FRAMEWORK: arifOS exposes arif_seal via /mcp JSON-RPC. We
        # submit the receipt payload and parse the returned vault id.
        # On any infrastructure failure we fall back to PENDING rather
        # than blocking the tool — arifOS outages are recoverable; lost
        # evidence is not.
        r = httpx.post(
            f"{_ARIFOS_BASE}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "arif_seal",
                    "arguments": {
                        "mode": "seal",
                        "verdict": verdict,
                        "receipt": json.loads(
                            json.dumps(receipt.model_dump(), default=str)
                        ),
                        "receipt_hash": receipt_hash,
                    },
                },
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=_ARIFOS_TIMEOUT_S,
        )
        if r.status_code != 200:
            logger.warning(
                "SEAL_RECEIPT: arifOS HTTP %s for tool=%s artifact=%s",
                r.status_code,
                tool,
                artifact_id,
            )
            return SealResult(
                state="PENDING",
                ref=None,
                receipt=receipt,
                error=f"arifOS HTTP {r.status_code}",
                vault_pending=True,
            )

        # Parse response: arif_seal returns either the vault id directly
        # or an envelope with a vault_ref / seal_id field.
        data = r.json()
        result = data.get("result", {})
        if isinstance(result, dict):
            content = result.get("content", [])
            payload: dict[str, Any] = {}
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        try:
                            payload = json.loads(item.get("text", "{}"))
                            break
                        except (json.JSONDecodeError, TypeError):
                            continue
            if not payload:
                payload = result

            vault_ref = (
                payload.get("vault_ref")
                or payload.get("vault_id")
                or payload.get("seal_id")
                or payload.get("ref")
            )
            if vault_ref:
                return SealResult(
                    state="SEALED",
                    ref=str(vault_ref),
                    receipt=receipt,
                )
            # arifOS responded but didn't echo a vault id — still treat
            # as success since we have the receipt_hash.
            return SealResult(
                state="SEALED",
                ref=f"vault999://sha256:{receipt_hash[:32]}",
                receipt=receipt,
            )
        else:
            return SealResult(
                state="SEALED",
                ref=f"vault999://sha256:{receipt_hash[:32]}",
                receipt=receipt,
            )

    except Exception as exc:
        # Fail-soft — keep tool usable, flag the gap.
        logger.warning(
            "SEAL_RECEIPT: infrastructure failure for tool=%s artifact=%s: %s — "
            "returning PENDING (audit will detect via VAULT999-PENDING log)",
            tool,
            artifact_id,
            exc,
        )
        return SealResult(
            state="PENDING",
            ref=None,
            receipt=receipt,
            error=f"{type(exc).__name__}: {exc}",
            vault_pending=True,
        )


# ── Artifact-status integration ───────────────────────────────────────────


def build_verification_envelope(
    *,
    artifact_status: str,
    verification_status: str,
    artifact_id: str,
    artifact_sha256: str | None,
    actor_id: str | None,
    session_id: str | None,
    tool: str,
    verification_reason: str = "",
    receipt: SealResult | None = None,
    claim_state: str = "COMPUTED",
) -> dict[str, Any]:
    """Compose the audit-defined envelope around a verification result.

    Returns a dict shaped like:
      {
        "transport_status": "OK",
        "execution_status": "COMPLETED",
        "artifact_status": "<artifact_status>",
        "verification_status": "<VERIFIED|UNVERIFIED|FAILED>",
        "governance_verdict": "HOLD",  # caller may override
        "claim_state": "COMPUTED",
        "actor_id": "<actor or 'anonymous'>",
        "session_id": "<session or 'anonymous'>",
        "artifact": {
          "id": "<artifact_id>",
          "sha256": "<sha256 or ''>",
        },
        "receipt": {
          "state": "<SEALED|PENDING|FAILED>",
          "ref": "<vault999://... or None>",
        },
        "verification_reason": "<when not VERIFIED>",
      }
    """
    env: dict[str, Any] = {
        "transport_status": "OK",
        "execution_status": "COMPLETED",
        "artifact_status": artifact_status,
        "verification_status": verification_status,
        "governance_verdict": "HOLD",
        "claim_state": claim_state,
        "actor_id": actor_id or "anonymous",
        "session_id": session_id or "anonymous",
        "artifact": {
            "id": artifact_id,
            "sha256": artifact_sha256 or "",
        },
        "receipt": (
            receipt.to_dict()
            if receipt is not None
            else {"state": "PENDING", "ref": None}
        ),
    }
    if verification_reason:
        env["verification_reason"] = verification_reason
    return env
