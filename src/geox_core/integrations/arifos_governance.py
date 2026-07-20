"""GEOX → arifOS Tight Integration Layer
DITEMPA BUKAN DIBERI — Governance is forged, not assumed.

This module provides the canonical bridge from GEOX domain tools to arifOS
constitutional infrastructure: arif_judge_deliberate and arif_vault_seal.

Architecture
-----------
GEOX tools build governed payloads → call arifOS judge (A2A HTTP) →
receive verdict (SEAL/HOLD/VOID/SABAR) → execute if SEAL → seal to VAULT999.

Design Principles
----------------
- GEOX remains the domain engine (subsurface intelligence).
- arifOS remains the constitutional governor (judge + vault + floors).
- GEOX tools PREPARE governed payloads; they never self-approve.
- Only arifOS judge verdict authorizes irreversible or material actions.
- All material outputs are sealed to the shared VAULT999 ledger.

Usage
-----
Inside any GEOX tool that may produce material output:

    from geox_core.integrations.arifos_governance import (
        build_governed_payload,
        call_judge,
        seal_to_vault,
        is_irreversible,
    )

    payload = build_governed_payload(
        tool_name="geox_prospect_evaluate",
        intent="Evaluate prospect for drilling decision",
        parameters={"prospect_ref": ref, "mode": "develop"},
        evidence_refs=[...],
        uncertainty={"band": "P10/P50/P90", "confidence": 0.78},
        irreversibility_flag=True,
    )

    verdict = await call_judge(payload)
    if verdict["verdict"] == "SEAL":
        result = await execute_internal_logic(...)
        receipt = await seal_to_vault(result, judge_state_hash=verdict["judge_state_hash"])
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import httpx

logger = logging.getLogger("geox.integrations.arifos_governance")

ARIFOS_JUDGE_ENDPOINT = "http://localhost:8080/mcp"
ARIFOS_VAULT_ENDPOINT = "http://localhost:8080/mcp"
ARIFOS_TIMEOUT_MS = 30_000

CONSTITUTION_HASH = "sha256:geox-constitutional-v2026.05.22"


class IrreversibilityLevel(StrEnum):
    """How irreversible is the action?"""

    REVERSIBLE = "reversible"  # No lasting consequence
    COSTLY = "costly"  # Financial/time cost, recoverable
    STRUCTURAL = "structural"  # Changes structure, hard to undo
    IRREVERSIBLE = "irreversible"  # Permanent: drilling, capital commit


@dataclass
class GovernedPayload:
    """Standard governed action payload for arifOS judge."""

    session_id: str
    actor: str
    tool_name: str
    intent: str
    parameters: dict[str, Any]
    evidence_refs: list[str]
    uncertainty: dict[str, Any]
    irreversibility: IrreversibilityLevel
    physics9_checks: dict[str, Any]
    proposed_verdict: str = "SEAL"
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    constitution_hash: str = CONSTITUTION_HASH

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "actor": self.actor,
            "tool_name": self.tool_name,
            "intent": self.intent,
            "parameters": self.parameters,
            "evidence_refs": self.evidence_refs,
            "uncertainty": self.uncertainty,
            "irreversibility": self.irreversibility.value,
            "physics9_checks": self.physics9_checks,
            "proposed_verdict": self.proposed_verdict,
            "timestamp": self.timestamp,
            "constitution_hash": self.constitution_hash,
        }


def build_governed_payload(
    tool_name: str,
    intent: str,
    parameters: dict[str, Any],
    evidence_refs: list[str],
    uncertainty: dict[str, Any],
    session_id: str = "geox-session",
    actor: str = "geox-organ",
    irreversibility: IrreversibilityLevel = IrreversibilityLevel.REVERSIBLE,
    physics9_checks: dict[str, Any] | None = None,
) -> GovernedPayload:
    """Build a standard governed action payload.

    Call this at the start of any GEOX tool that produces material output
    or requires constitutional review.

    Args:
        tool_name: Name of the GEOX tool (e.g. "geox_prospect_evaluate").
        intent: Human-readable description of what the tool intends to do.
        parameters: Tool parameters that led to this action.
        evidence_refs: List of artifact refs used as evidence.
        uncertainty: Uncertainty metadata (band, confidence, etc.).
        session_id: GEOX session ID (for traceability).
        actor: Calling organ identity (default: "geox-organ").
        irreversibility: How irreversible is this action?
        physics9_checks: Physics-9 compliance results if available.

    Returns:
        GovernedPayload ready for judge submission.
    """
    return GovernedPayload(
        session_id=session_id,
        actor=actor,
        tool_name=tool_name,
        intent=intent,
        parameters=parameters,
        evidence_refs=evidence_refs,
        uncertainty=uncertainty,
        irreversibility=irreversibility,
        physics9_checks=physics9_checks or {"passed": True, "checks": []},
    )


def is_irreversible(
    tool_name: str,
    mode: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> IrreversibilityLevel:
    """Determine irreversibility level for a GEOX tool call.

    This is the canonical lookup for GEOX tool irreversibility.
    Update this function when new tools are added or existing tools
    gain new irreversible modes.

    Args:
        tool_name: Name of the GEOX tool.
        mode: Operational mode if applicable.
        parameters: Full parameters dict if needed.

    Returns:
        IrreversibilityLevel enum value.
    """
    _irreversible_tools = {
        "geox_prospect_judge_seal": IrreversibilityLevel.STRUCTURAL,
        "geox_prospect_evaluate": IrreversibilityLevel.COSTLY,
    }

    _irreversible_modes = {
        ("geox_prospect_evaluate", "develop"): IrreversibilityLevel.STRUCTURAL,
        ("geox_prospect_evaluate", "seal"): IrreversibilityLevel.IRREVERSIBLE,
        ("geox_sequence_interpret", "project"): IrreversibilityLevel.COSTLY,
        ("geox_evidence_reason", "full"): IrreversibilityLevel.REVERSIBLE,
    }

    if (tool_name, mode) in _irreversible_modes:
        return _irreversible_modes[(tool_name, mode)]

    if tool_name in _irreversible_tools:
        return _irreversible_tools[tool_name]

    return IrreversibilityLevel.REVERSIBLE


async def call_judge(
    payload: GovernedPayload,
    judge_endpoint: str | None = None,
    timeout_ms: int = ARIFOS_TIMEOUT_MS,
) -> dict[str, Any]:
    """Call arifOS judge via A2A MCP HTTP.

    Submits a governed payload to arif_judge_deliberate and returns
    the verdict (SEAL/HOLD/VOID/SABAR).

    Args:
        payload: GovernedPayload prepared by build_governed_payload().
        judge_endpoint: Override for arifOS judge MCP endpoint.
        timeout_ms: Request timeout in milliseconds.

    Returns:
        Judge verdict dict with keys: verdict, judge_state_hash, reasons, etc.
        Returns {"verdict": "HOLD", "error": "..."} on failure (graceful degradation).

    Note:
        On failure (network error, judge unavailable), returns HOLD verdict
        rather than crashing. This is F5 PEACE compliant — graceful degradation
        rather than blocking the entire organ.
    """
    endpoint = judge_endpoint or ARIFOS_JUDGE_ENDPOINT

    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "arif_judge_deliberate",
            "arguments": {
                "mode": "judge",
                "candidate": payload.to_dict(),
                "session_id": payload.session_id,
                "actor_id": payload.actor,
                "constitutional_chain_id": payload.constitution_hash,
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000) as client:
            response = await client.post(endpoint, json=mcp_request)
            response.raise_for_status()
            result = response.json()

            if "result" in result:
                return result["result"]
            elif "error" in result:
                logger.error("arifOS judge returned error: %s", result["error"])
                return {
                    "verdict": "HOLD",
                    "error": result["error"].get("message", "Judge error"),
                    "fallback": True,
                }
            else:
                return {"verdict": "HOLD", "error": "Unexpected response shape"}

    except httpx.TimeoutException:
        logger.warning("arifOS judge timeout (>%dms). Degrading to HOLD.", timeout_ms)
        return {
            "verdict": "HOLD",
            "error": f"Judge timeout after {timeout_ms}ms",
            "fallback": True,
        }

    except httpx.ConnectError:
        logger.warning("Cannot connect to arifOS judge at %s. Degrading to HOLD.", endpoint)
        return {
            "verdict": "HOLD",
            "error": f"arifOS judge unavailable at {endpoint}",
            "fallback": True,
        }

    except Exception as exc:
        logger.exception("Unexpected error calling arifOS judge: %s", exc)
        return {
            "verdict": "HOLD",
            "error": str(exc),
            "fallback": True,
        }


async def seal_to_vault(
    result: dict[str, Any],
    judge_state_hash: str | None = None,
    session_id: str = "geox-session",
    actor: str = "geox-organ",
    vault_endpoint: str | None = None,
    ack_irreversible: bool = False,
    timeout_ms: int = ARIFOS_TIMEOUT_MS,
) -> dict[str, Any]:
    """Seal a GEOX tool result to VAULT999 via arifOS.

    Every material output from GEOX should be sealed here. The vault
    provides immutable audit trail for the constitutional ledger.

    Args:
        result: The GEOX tool result to seal.
        judge_state_hash: Hash from arifOS judge SEAL verdict (required for material outputs).
        session_id: GEOX session ID.
        actor: Calling organ identity.
        vault_endpoint: Override for arifOS vault MCP endpoint.
        ack_irreversible: If True, acknowledges this is an irreversible write.
        timeout_ms: Request timeout in milliseconds.

    Returns:
        Vault seal receipt dict with keys: entry_id, chain_hash, timestamp.
    """
    endpoint = vault_endpoint or ARIFOS_VAULT_ENDPOINT

    payload = {
        "session_id": session_id,
        "actor_id": actor,
        "tool_name": result.get("tool", "geox-unknown"),
        "result_summary": _summarize_for_vault(result),
        "full_result": result,
        "judge_state_hash": judge_state_hash,
        "timestamp": datetime.now(UTC).isoformat(),
        "constitution_hash": CONSTITUTION_HASH,
    }

    mcp_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "arif_vault_seal",
            "arguments": {
                "mode": "seal",
                "payload": json.dumps(payload, default=str, separators=(",", ":")),
                "session_id": session_id,
                "actor_id": actor,
                "ack_irreversible": ack_irreversible,
                "judge_state_hash": judge_state_hash,
                "constitutional_chain_id": CONSTITUTION_HASH,
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000) as client:
            response = await client.post(endpoint, json=mcp_request)
            response.raise_for_status()
            result = response.json()

            if "result" in result:
                return result["result"]
            elif "error" in result:
                logger.error("arifOS vault seal returned error: %s", result["error"])
                return {
                    "entry_id": None,
                    "chain_hash": None,
                    "error": result["error"].get("message", "Vault error"),
                    "fallback": True,
                }
            else:
                return {"entry_id": None, "chain_hash": None, "error": "Unexpected response"}

    except httpx.TimeoutException:
        logger.warning("arifOS vault timeout (>%dms).", timeout_ms)
        return {
            "entry_id": None,
            "chain_hash": None,
            "error": f"Vault timeout after {timeout_ms}ms",
            "fallback": True,
        }

    except httpx.ConnectError:
        logger.warning("Cannot connect to arifOS vault at %s.", endpoint)
        return {
            "entry_id": None,
            "chain_hash": None,
            "error": f"arifOS vault unavailable at {endpoint}",
            "fallback": True,
        }

    except Exception as exc:
        logger.exception("Unexpected error sealing to vault: %s", exc)
        return {
            "entry_id": None,
            "chain_hash": None,
            "error": str(exc),
            "fallback": True,
        }


def _summarize_for_vault(result: dict[str, Any]) -> dict[str, Any]:
    """Extract summary fields from a GEOX result for vault storage.

    Keeps the vault entry lean while preserving key metadata.
    Full result is stored in the payload.
    """
    return {
        "tool": result.get("tool", "unknown"),
        "status": result.get("status", result.get("claim_state", "unknown")),
        "verdict": result.get("verdict", result.get("governance_status", "unknown")),
        "n_evidence_refs": len(result.get("evidence_refs", [])),
        "uncertainty": result.get("uncertainty", result.get("confidence", {})),
        "processing_log_count": len(result.get("processing_log", [])),
    }


def compute_parameters_hash(params: dict[str, Any]) -> str:
    """Compute a canonical fingerprint of parameters for reproducibility."""
    canonical = json.dumps(params, sort_keys=True, default=str, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"
