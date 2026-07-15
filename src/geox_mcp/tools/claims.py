"""
GEOX Claim Engine — Structured Interpretation Claims with Evidence & Seal
========================================================================

H5 of the GEOX Eureka Doctrine: The claim engine transforms raw Earth
evidence into sealed interpretation claims with:
- Truth class (FACT / INTERPRETATION / SPECULATION)
- Uncertainty band (P10/P50/P90)
- Evidence chain with provenance
- Challenge/alternative framework
- Vault999 seal via arifOS bridge

DITEMPA BUKAN DIBERI — Earth intelligence is forged, not given.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

import httpx

# ── Reality Ledger Bridge ───────────────────────────────────────────────────────
_LEDGER_AVAILABLE = True
try:
    from core.organ_ledger_bridge import record_geox_claim
except ImportError:
    _LEDGER_AVAILABLE = False

logger = logging.getLogger("geox.claims")

# ── Claim truth classes ────────────────────────────────────────────────────────
TruthClass = Literal["FACT", "INTERPRETATION", "SPECULATION"]

# ── Claim types ────────────────────────────────────────────────────────────────
ClaimType = Literal[
    "horizon",
    "fault",
    "trap",
    "reservoir",
    "seal",
    "charge",
    "source",
    "temperature",
    "pressure",
    "fluid_contact",
    "net_pay",
    "permeability",
    "porosity",
    "saturation",
    "thickness",
    "area",
    "depth",
    "structure",
    "stratigraphy",
    "lithology",
    "facies",
    "environment",
    "sequence",
    "other",
]

# ── Earth Memory Store (claim persistence) ────────────────────────────────────
_memory_store: Any = None


def _get_memory_store() -> Any:
    """Lazily initialized EarthMemoryStore instance."""
    global _memory_store
    if _memory_store is None:
        try:
            from geox_core.services.asset_memory import EarthMemoryStore

            _memory_store = EarthMemoryStore(db_path="/root/geox/earth_memory.db")
        except ImportError:
            logger.warning("EarthMemoryStore not available — claim persistence disabled")
            _memory_store = False  # sentinel: available but failed
    return _memory_store if _memory_store else None


# ── Internal helpers ──────────────────────────────────────────────────────────


def _hash_payload(payload: dict) -> str:
    """Create a content-addressable hash of a payload."""
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _build_claim_envelope(
    claim_id: str,
    claim_type: ClaimType,
    claim_text: str,
    truth_class: TruthClass,
    uncertainty: dict[str, Any] | None,
    evidence_ids: list[str],
    alternatives: list[dict[str, Any]] | None,
    provenance: str,
    authority: str = "GEOX_CLAIM_WORKER",
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a full earth_memory_envelope-compliant claim.

    Args:
        extra_metadata: Optional dict of supplementary metadata (e.g. epistemic_label,
            forbidden_uses, source_citation, category) merged into the payload.
            Added in Phase 2.5 for literature-to-claims extraction support.
    """
    payload = {
        "id": claim_id,
        "claim_type": claim_type,
        "claim_text": claim_text,
        "truth_class": truth_class,
        "uncertainty": uncertainty or {},
        "evidence_ids": evidence_ids,
        "alternatives": alternatives or [],
        "provenance": provenance,
        "authority": {
            "approval_state": "draft",
            "created_by": authority,
            "created_at": _now_iso(),
        },
        "seal": None,
        "challenges": [],
        "evidence_chain": [],
    }
    if extra_metadata:
        payload["extra_metadata"] = extra_metadata
    payload["_content_hash"] = _hash_payload(payload)
    return payload


async def _get_arifOS_health() -> bool:
    """Check if arifOS is available for sealing."""

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:8088/health")
            return r.status_code == 200
    except Exception as exc:
        logger.warning(f"arifOS health check failed: {exc}")
        return False


# ── Tool 1: geox_claim_create ────────────────────────────────────────────────


async def geox_claim_create(
    claim_text: str,
    claim_type: ClaimType,
    truth_class: TruthClass,
    evidence_ids: list[str],
    uncertainty_p10: float | None = None,
    uncertainty_p50: float | None = None,
    uncertainty_p90: float | None = None,
    uncertainty_distribution: str = "lognormal",
    alternatives: list[dict[str, Any]] | None = None,
    provenance: str = "GEOX Claim Engine",
    authority: str = "GEOX_CLAIM_WORKER",
    extra_metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create a structured Earth interpretation claim with full provenance chain.

    This is the primary tool for transforming raw Earth evidence into
    machine-checkable, sealable interpretation claims.

    Truth class rules:
    - FACT: Directly observed (log readings, core photos, seismic amplitudes)
    - INTERPRETATION: Derived from physics/consistency (depth-converted maps, PVT)
    - SPECULATION: Inferred from analogy/statistics (undrilled prospects)

    Args:
        claim_text: The core claim in plain language. Must be specific enough
            to be falsifiable.
        claim_type: Geological category (horizon, fault, trap, reservoir, etc.)
        truth_class: FACT | INTERPRETATION | SPECULATION
        evidence_ids: List of ingested artifact IDs supporting this claim.
        uncertainty_p10: P10 (optimistic) value if applicable.
        uncertainty_p50: P50 (median) value if applicable.
        uncertainty_p90: P90 (pessimistic) value if applicable.
        uncertainty_distribution: Distribution type (lognormal | normal | triangular).
        alternatives: List of alternative interpretations, each with
            'alternative_text' and 'alternative_evidence_ids'.
        provenance: Human-readable origin of this claim.
        authority: Which GEOX worker created this claim.
        extra_metadata: Optional supplementary metadata for literature-to-claims
            extraction. Supported keys: epistemic_label, forbidden_uses,
            source_citation, category.

    Returns:
        Structured claim envelope with claim_id, status, and next steps.
    """
    claim_id = f"clm_{uuid.uuid4().hex[:16]}"

    # Build uncertainty object
    uncertainty = None
    if any(v is not None for v in [uncertainty_p10, uncertainty_p50, uncertainty_p90]):
        uncertainty = {
            "p10": uncertainty_p10,
            "p50": uncertainty_p50,
            "p90": uncertainty_p90,
            "distribution": uncertainty_distribution,
            "type": "range",
        }

    payload = _build_claim_envelope(
        claim_id=claim_id,
        claim_type=claim_type,
        claim_text=claim_text,
        truth_class=truth_class,
        uncertainty=uncertainty,
        evidence_ids=evidence_ids,
        alternatives=alternatives,
        provenance=provenance,
        authority=authority,
        extra_metadata=extra_metadata,
    )

    # Persist to Earth Memory store
    store = _get_memory_store()
    if store:
        try:
            record_id = store.draft_claim(asset_id=claim_type, payload=payload)
            payload["_earth_memory_id"] = record_id
        except Exception as e:
            logger.warning(f"EarthMemoryStore write failed: {e}")

    # ── Record to Reality Ledger ────────────────────────────────────────────────
    if _LEDGER_AVAILABLE:
        try:
            ledger_id = record_geox_claim(
                claim_data={
                    "claim_type": claim_type,
                    "claim_text": claim_text,
                    "evidence_ids": evidence_ids,
                    "confidence": (uncertainty_p50 / 100 if uncertainty_p50 is not None else 0.5),
                },
                actor=authority,
            )
            logger.debug(f"Reality Ledger: {ledger_id}")
        except Exception as e:
            logger.warning(f"Reality Ledger write failed: {e}")

    return {
        "status": "CREATED",
        "claim_id": claim_id,
        "truth_class": truth_class,
        "claim_type": claim_type,
        "claim_text": claim_text,
        "uncertainty": uncertainty,
        "evidence_ids": evidence_ids,
        "alternatives_count": len(alternatives) if alternatives else 0,
        "provenance": provenance,
        "created_at": payload["authority"]["created_at"],
        "claim_state": "DRAFT",
        "extra_metadata": extra_metadata,
        "_content_hash": payload["_content_hash"],
        "next_steps": [
            {
                "action": "validate",
                "tool": "geox_claim_validate",
                "description": "Validate claim against earth_memory_envelope schema",
            },
            {
                "action": "evidence",
                "tool": "geox_evidence_attach",
                "description": "Attach additional evidence IDs to this claim",
            },
            {
                "action": "challenge",
                "tool": "geox_claim_challenge",
                "description": "Challenge this claim with alternative interpretation",
            },
            {
                "action": "seal",
                "tool": "geox_claim_seal",
                "description": "Request Vault999 seal via arifOS — requires ack_irreversible=True",
            },
        ],
    }


# ── Tool 2: geox_claim_validate ──────────────────────────────────────────────


async def geox_claim_validate(
    claim_id: str,
    session_id: str | None = None,
    actor_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Validate a draft claim against the 16-field earth_memory_envelope schema.
    Promotes claim from DRAFT → VALIDATED.

    Call geox_claim_create first to get a claim_id.

    Args:
        claim_id: The claim identifier returned by geox_claim_create.

    Returns:
        Validation result with schema compliance status.
    """
    if not _get_memory_store:
        return {
            "status": "UNAVAILABLE",
            "message": "EarthMemoryStore not available — validation skipped",
            "claim_id": claim_id,
        }

    store = _get_memory_store()
    try:
        store.validate_claim(claim_id)
        return {
            "status": "VALIDATED",
            "claim_id": claim_id,
            "claim_state": "VALIDATED",
            "validation_result": "PASSED",
            "message": "Claim is compliant with earth_memory_envelope schema.",
        }
    except ValueError as e:
        return {
            "status": "VALIDATION_FAILED",
            "claim_id": claim_id,
            "claim_state": "DRAFT",
            "validation_result": "FAILED",
            "error": str(e),
        }


# ── Tool 3: geox_claim_challenge ─────────────────────────────────────────────


async def geox_claim_challenge(
    claim_id: str,
    challenge_text: str,
    alternative_claim_text: str,
    alternative_evidence_ids: list[str],
    challenge_evidence_ids: list[str] | None = None,
    alternative_uncertainty: dict[str, Any] | None = None,
    challenger_provenance: str = "GEOX Claim Engine",
    session_id: str | None = None,
    actor_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Challenge an existing interpretation claim with an alternative interpretation.

    This is the core tool for the Multi-Discipline Self-Argument requirement
    (Eureka #4): geology must argue against geomechanics, drilling must
    challenge reservoir, etc.

    Challenge creates a competing claim and links it to the original.
    Neither is sealed until arifOS judges.

    Args:
        claim_id: ID of the claim being challenged.
        challenge_text: Description of why the original claim is questionable.
        alternative_claim_text: The alternative interpretation.
        alternative_evidence_ids: Evidence supporting the alternative.
        challenge_evidence_ids: Evidence undermining the original claim.
        alternative_uncertainty: Uncertainty band for the alternative.
        challenger_provenance: Origin of this challenge.

    Returns:
        Challenge result with linked challenge_id and alternative_id.
    """
    challenge_id = f"chl_{uuid.uuid4().hex[:16]}"
    alternative_id = f"alt_{uuid.uuid4().hex[:16]}"

    challenge_record = {
        "id": challenge_id,
        "type": "challenge",
        "challenged_claim_id": claim_id,
        "challenge_text": challenge_text,
        "alternative_claim_text": alternative_claim_text,
        "alternative_evidence_ids": alternative_evidence_ids,
        "challenge_evidence_ids": challenge_evidence_ids or [],
        "alternative_uncertainty": alternative_uncertainty,
        "challenge_state": "ACTIVE",
        "created_at": _now_iso(),
        "provenance": challenger_provenance,
    }
    challenge_record["_content_hash"] = _hash_payload(challenge_record)

    store = _get_memory_store()
    if store:
        try:
            # Attach challenge to the challenged claim
            with store._connect() as conn:
                existing = conn.execute(
                    "SELECT payload FROM earth_memory WHERE id = ?",
                    (claim_id,),
                ).fetchone()
                if existing:
                    payload = json.loads(existing[0])
                    payload["challenges"].append(challenge_id)
                    conn.execute(
                        "UPDATE earth_memory SET payload = ? WHERE id = ?",
                        (json.dumps(payload), claim_id),
                    )
        except Exception as e:
            logger.warning(f"Challenge link failed: {e}")

    return {
        "status": "CHALLENGE_CREATED",
        "challenge_id": challenge_id,
        "alternative_id": alternative_id,
        "challenged_claim_id": claim_id,
        "challenge_text": challenge_text,
        "alternative_claim_text": alternative_claim_text,
        "challenge_evidence_ids": challenge_evidence_ids or [],
        "alternative_evidence_ids": alternative_evidence_ids,
        "challenge_state": "ACTIVE",
        "created_at": challenge_record["created_at"],
        "next_steps": [
            {
                "action": "adjudicate",
                "tool": "geox_claim_seal",
                "description": "Submit both claims to arifOS for adjudication and seal",
            },
        ],
    }


# ── Tool 4: geox_evidence_attach ─────────────────────────────────────────────


async def geox_evidence_attach(
    claim_id: str,
    evidence_id: str,
    evidence_type: str = "supporting",
    provenance: str = "GEOX Claim Engine",
    session_id: str | None = None,
    actor_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Attach an evidence artifact to an existing claim.

    Evidence types:
    - supporting: Backs the claim (primary evidence)
    - contradicting: Undermines the claim
    - contextual: Provides background context
    - alternative: Supports an alternative interpretation

    Args:
        claim_id: ID of the claim to attach evidence to.
        evidence_id: ID of the evidence artifact (from ingest).
        evidence_type: supporting | contradicting | contextual | alternative
        provenance: Origin of this attachment.

    Returns:
        Attachment confirmation with updated evidence chain.
    """
    if evidence_type not in ("supporting", "contradicting", "contextual", "alternative"):
        return {
            "status": "INVALID",
            "error": f"Invalid evidence_type: {evidence_type}. "
            "Must be one of: supporting, contradicting, contextual, alternative",
            "claim_id": claim_id,
            "evidence_id": evidence_id,
        }

    attachment_id = f"att_{uuid.uuid4().hex[:16]}"
    attachment = {
        "id": attachment_id,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "attached_to": claim_id,
        "provenance": provenance,
        "attached_at": _now_iso(),
    }

    store = _get_memory_store()
    updated = False
    if store:
        try:
            with store._connect() as conn:
                row = conn.execute(
                    "SELECT payload FROM earth_memory WHERE id = ?",
                    (claim_id,),
                ).fetchone()
                if row:
                    payload = json.loads(row[0])
                    payload["evidence_chain"].append(attachment)
                    payload["evidence_ids"].append(evidence_id)
                    payload["_content_hash"] = _hash_payload(payload)
                    conn.execute(
                        "UPDATE earth_memory SET payload = ? WHERE id = ?",
                        (json.dumps(payload), claim_id),
                    )
                    updated = True
        except Exception as e:
            logger.warning(f"Evidence attach failed: {e}")

    return {
        "status": "ATTACHED",
        "attachment_id": attachment_id,
        "claim_id": claim_id,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "attached_at": attachment["attached_at"],
        "evidence_chain_updated": updated,
        "next_steps": [
            {
                "action": "seal",
                "tool": "geox_claim_seal",
                "description": "Submit claim with updated evidence for Vault999 seal",
            },
        ],
    }


# ── Tool 5: geox_claim_seal ─────────────────────────────────────────────────


async def geox_claim_seal(
    claim_id: str,
    ack_irreversible: bool = False,
    seal_verdict: Literal["SEAL", "SABAR", "VOID"] = "SEAL",
    session_id: str | None = None,
    actor_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Submit a validated claim to arifOS for Vault999 sealing.

    Routes to the arifOS kernel which performs final constitutional checks
    (F1 AMANAH gate, F13 SOVEREIGN veto) before writing to VAULT999.
    GEOX does not perform constitutional adjudication — it merely forwards
    the claim for arifOS to judge.

    SEAL: Claim is constitutionally approved, irreversibly sealed.
    SABAR: Claim is held — needs more evidence or human review.
    VOID: Claim is rejected or self-contradictory.

    Args:
        claim_id: ID of the validated claim to seal.
        ack_irreversible: Must be True for SEAL verdict. F1 AMANAH gate.
        seal_verdict: SEAL | SABAR | VOID — pre-adjudication recommendation.

    Returns:
        Seal receipt from Vault999 or hold/rejection reason.
    """
    if seal_verdict == "SEAL" and not ack_irreversible:
        return {
            "status": "HOLD",
            "error_code": "RT3_GUARD_F1_AMANAH",
            "message": (
                "SEAL verdict is a constitutional adjudication (irreversible). "
                "F1 AMANAH requires ack_irreversible=True. "
                "Provide ack_irreversible=True in the tool call to proceed."
            ),
            "guard": "RT3",
            "floor": "F1_AMANAH",
            "claim_id": claim_id,
            "required_action": "Set ack_irreversible=True to confirm irreversible seal.",
        }

    # Fetch claim from store
    store = _get_memory_store()
    claim_payload = None
    approval_state = "draft"
    challenges = []
    if store:
        try:
            with store._connect() as conn:
                row = conn.execute(
                    "SELECT payload, approval_state FROM earth_memory WHERE id = ?",
                    (claim_id,),
                ).fetchone()
                if row:
                    claim_payload = json.loads(row[0])
                    approval_state = row[1] or "draft"
                    challenges = claim_payload.get("challenges", [])
        except Exception as e:
            logger.warning(f"Claim fetch failed: {e}")

    # ── MANDATORY CONTRADICTION PRE-SEAL GATE (Federation Contract §5) ─────
    # Before SEAL: claim must be VALIDATED, must have been challenged or
    # contradiction-scanned, and must have integrity verified.
    if seal_verdict == "SEAL":
        pre_seal_checks = []

        # Gate 1: Claim must be VALIDATED
        if approval_state not in ("VALIDATED", "validated", "review_pending"):
            pre_seal_checks.append(
                {
                    "gate": "claim_validate_required",
                    "status": "FAILED",
                    "detail": f"Claim approval_state is '{approval_state}', not 'VALIDATED'. "
                    "Call geox_claim_validate before sealing.",
                    "recovery": "geox_claim_validate(claim_id='{claim_id}')",
                }
            )

        # Gate 2: Claim must have been challenged (contradiction discipline)
        if not challenges:
            pre_seal_checks.append(
                {
                    "gate": "contradiction_scan_required",
                    "status": "FAILED",
                    "detail": "Claim has no challenges recorded. Federation contract requires "
                    "geox_claim_challenge before SEAL (Multi-Discipline Self-Argument).",
                    "recovery": (
                        "geox_claim_challenge(claim_id='{claim_id}', "
                        "challenge_text='<why this might be wrong>', "
                        "alternative_claim_text='<alternative interpretation>', "
                        "alternative_evidence_ids=[])"
                    ),
                }
            )

        # Gate 3: Evidence integrity must be verified
        evidence_ids = claim_payload.get("evidence_ids", []) if claim_payload else []
        evidence_chain = claim_payload.get("evidence_chain", []) if claim_payload else []
        if not evidence_ids and not evidence_chain:
            pre_seal_checks.append(
                {
                    "gate": "evidence_integrity_required",
                    "status": "FAILED",
                    "detail": "Claim has no evidence attached. Federation contract requires geox_evidence_attach before SEAL.",
                    "recovery": "geox_evidence_attach(claim_id='{claim_id}', evidence_id='<id>')",
                }
            )

        # Gate 3b: ANTI-SINK — Synthetic/fixture provenance must not be sealed
        # F1 AMANAH + Anti-Behavioral-Sink: claims backed only by synthetic data
        # cannot be sealed as FACT or INTERPRETATION. They are SPECULATION at best.
        # This prevents the "closed loop over own outputs" failure mode.
        _SYNTHETIC_PROVENANCE = {"fixture", "scaffold_fixture", "synthetic", "generated"}
        if evidence_ids and claim_payload:
            synthetic_evidence_count = 0
            total_evidence = len(evidence_ids)
            # Check evidence_chain for provenance tags
            for ev in evidence_chain if isinstance(evidence_chain, list) else []:
                prov = str(ev.get("provenance", "")).lower()
                if any(s in prov for s in _SYNTHETIC_PROVENANCE):
                    synthetic_evidence_count += 1
            # Also check evidence_refs in payload
            for ev_id in evidence_ids:
                if isinstance(ev_id, str) and any(s in ev_id.lower() for s in _SYNTHETIC_PROVENANCE):
                    synthetic_evidence_count += 1
            if synthetic_evidence_count > 0 and synthetic_evidence_count == total_evidence:
                truth_class = claim_payload.get("truth_class", "INTERPRETATION")
                if truth_class in ("FACT", "INTERPRETATION"):
                    pre_seal_checks.append(
                        {
                            "gate": "anti_sink_synthetic_provenance_block",
                            "status": "FAILED",
                            "detail": (
                                f"All {total_evidence} evidence artifact(s) have synthetic/fixture provenance, "
                                f"but truth_class is '{truth_class}'. Federation Anti-Sink rule: claims backed "
                                "only by synthetic data cannot be sealed as FACT or INTERPRETATION. "
                                "Set truth_class='SPECULATION' or attach real-world evidence."
                            ),
                            "recovery": (
                                "geox_evidence_attach(claim_id='{claim_id}', evidence_id='<real_data_artifact_id>') "
                                "OR update claim truth_class to 'SPECULATION'."
                            ),
                            "floor": "F1_AMANAH",
                            "rule": "ANTI_SINK_v1",
                        }
                    )

        if pre_seal_checks:
            return {
                "status": "HOLD",
                "error_code": "PRE_SEAL_CONTRADICTION_GATE",
                "message": (
                    "Federation contract §5: Mandatory contradiction discipline before SEAL. "
                    f"{len(pre_seal_checks)} gate(s) failed."
                ),
                "claim_id": claim_id,
                "approval_state": approval_state,
                "challenge_count": len(challenges),
                "evidence_count": len(evidence_ids) if evidence_ids else 0,
                "failed_gates": pre_seal_checks,
                "required_actions": [g["recovery"] for g in pre_seal_checks],
                "next_steps": [
                    "1. Call geox_claim_validate to set approval_state=VALIDATED",
                    "2. Call geox_claim_challenge for mandatory contradiction scan",
                    "3. Call geox_evidence_attach to link evidence artifacts",
                    "4. Retry geox_claim_seal with ack_irreversible=True",
                ],
            }

    arifOS_available = await _get_arifOS_health()

    if not arifOS_available:
        # Self-seal with local receipt (degraded mode — no arifOS)
        seal_receipt = {
            "vault": "VAULT999-LOCAL",
            "verdict": seal_verdict,
            "claim_id": claim_id,
            "timestamp": _now_iso(),
            "hash": _hash_payload(claim_payload) if claim_payload else claim_id,
            "seal_source": "geox_claim_engine_local",
            "degraded_mode": True,
            "note": "arifOS not reachable — local seal only. Promote to Vault999 when arifOS is available.",
        }
        return {
            "status": "SEALED_LOCAL",
            "seal_receipt": seal_receipt,
            "claim_id": claim_id,
            "claim_state": "SEALED",
            "verdict": seal_verdict,
            "degraded_warning": "Seal is local only. arifOS must be available for canonical Vault999 seal.",
        }

    # arifOS is available — build seal request
    seal_request = {
        "source": "GEOX_CLAIM_ENGINE",
        "claim_id": claim_id,
        "payload": claim_payload,
        "verdict": seal_verdict,
        "ack_irreversible": ack_irreversible,
        "timestamp": _now_iso(),
    }

    # Attempt to route through arifOS vault bridge (MCP-native, not REST)
    # arifOS exposes /mcp (MCP protocol), not /vault/seal (REST).
    # The bridge does: initialize -> tools/call(arif_vault_seal).

    try:
        mcp_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. initialize MCP session
            init_resp = await client.post(
                "http://127.0.0.1:8088/mcp",
                headers=mcp_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "geox-bridge", "version": "1.0"},
                    },
                },
            )
            resolved_session = session_id or init_resp.headers.get("Mcp-Session-Id") or init_resp.headers.get("mcp-session-id") or ""

            # 2. tools/call arif_vault_seal
            call_headers = {**mcp_headers, "Mcp-Session-Id": resolved_session}
            call_resp = await client.post(
                "http://127.0.0.1:8088/mcp",
                headers=call_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_seal",
                        "arguments": {
                            "action": "SEAL",
                            "payload": json.dumps(seal_request),
                            "actor_id": actor_id or "geox-bridge",
                            "session_id": resolved_session,
                            "ack_irreversible": bool(ack_irreversible),
                        },
                    },
                },
            )
            result = call_resp.json()
            if "error" in result and result["error"]:
                raise RuntimeError(f"MCP error: {result['error']}")
            mcp_result = result.get("result") or {}
            if isinstance(mcp_result, dict) and "content" in mcp_result and isinstance(mcp_result["content"], list):
                for item in mcp_result["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "").strip()
                        if text.startswith("KERNEL_DENY") or text.startswith("ERROR") or text.startswith("HOLD"):
                            raise RuntimeError(f"arifOS error: {text}")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                mcp_result = parsed
                                break
                        except Exception:
                            mcp_result = {"text": text}
            return {
                "status": "SEALED",
                "seal_receipt": mcp_result,
                "claim_id": claim_id,
                "claim_state": "SEALED",
                "verdict": seal_verdict,
                "session_id": resolved_session,
                "actor_id": actor_id or "geox-bridge",
            }
    except Exception as e:
        error_msg = str(e)
        # Preserve the legacy HOLD shape for downstream consumers
        if hasattr(e, "code") and hasattr(e, "reason"):
            return {
                "status": "HOLD",
                "error_code": "ARIFOS_MCP_ERROR",
                "message": f"arifOS MCP error: {getattr(e, 'code', '?')} {getattr(e, 'reason', '?')}",
                "detail": error_msg,
                "claim_id": claim_id,
                "required_action": "Check arifOS health and /mcp readiness, then retry.",
                "session_id": session_id or "",
                "actor_id": actor_id or "geox-bridge",
            }
        return {
            "status": "HOLD",
            "error_code": "ARIFOS_MCP_ERROR",
            "message": "arifOS MCP bridge failed",
            "detail": error_msg,
            "claim_id": claim_id,
            "required_action": "Check arifOS /mcp endpoint and retry.",
            "session_id": session_id or "",
            "actor_id": actor_id or "geox-bridge",
        }


# ── Tool 6: geox_claim_query ─────────────────────────────────────────────────


async def geox_claim_query(
    claim_id: str | None = None,
    claim_type: ClaimType | None = None,
    truth_class: TruthClass | None = None,
    claim_state: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Query the Earth Memory store for claims matching filter criteria.

    Returns all fields including evidence chain, challenges, and seal receipt.

    Args:
        claim_id: Exact match on claim ID.
        claim_type: Filter by geological category.
        truth_class: Filter by FACT | INTERPRETATION | SPECULATION.
        claim_state: Filter by DRAFT | VALIDATED | REVIEWED | SEALED | VOID.
        limit: Maximum number of results (default 20).

    Returns:
        List of matching claims with full envelope data.
    """
    if not _get_memory_store:
        return {
            "status": "UNAVAILABLE",
            "message": "EarthMemoryStore not available",
            "results": [],
        }

    store = _get_memory_store()
    results = []

    try:
        with store._connect() as conn:
            query = "SELECT id, asset_id, memory_type, truth_class, approval_state, payload, timestamp FROM earth_memory WHERE memory_type = 'earth'"
            params: list[Any] = []

            if claim_id:
                query += " AND id = ?"
                params.append(claim_id)
            if claim_type:
                # asset_id stores claim_type in current design
                query += " AND asset_id = ?"
                params.append(claim_type)
            if truth_class:
                query += " AND truth_class = ?"
                params.append(truth_class)
            if claim_state:
                query += " AND approval_state = ?"
                params.append(claim_state)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            for row in rows:
                payload = json.loads(row[5])
                results.append(
                    {
                        "id": row[0],
                        "claim_type": row[1],
                        "memory_type": row[2],
                        "truth_class": row[3],
                        "claim_state": row[4],
                        "payload": payload,
                        "timestamp": row[6],
                    }
                )

    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "results": [],
        }

    return {
        "status": "OK",
        "count": len(results),
        "results": results,
    }
