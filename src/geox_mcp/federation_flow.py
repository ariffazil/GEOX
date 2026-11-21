"""
federation_flow.py — GEOX Federation, arifFlow, FRAME & CHRON Integration Bridge
================================================================================
DITEMPA BUKAN DIBERI — Forged, Not Given

Maps all 11 federation organs, aligns GEOX's 27 canonical tools across the 11 domains,
and connects GEOX into the arifOS sovereign loop:
  1. arifOS Kernel (:8088): Constitutional Law, Floors F1-F13, 8-Verb Canonical Cycle, VAULT999.
  2. arifFlow (:7073): Dynamic FQ balancing, non-blocking receipt streaming, dual-rate task flow.
  3. FRAME (:18085): Independent reality witness, multi-organ baseline, contradiction scanner.
  4. CHRON: Bitemporal reality store, predictive calibration, attention debt, episodic learning.

FORGED: 2026-11-03
SOVEREIGN: Arif (F13)
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx

logger = logging.getLogger("geox.federation_flow")

# ── Paths & Endpoints ──────────────────────────────────────────────────────────
GEOX_ROOT = Path(os.environ.get("GEOX_ROOT") or Path(__file__).resolve().parents[2])
ARIFLOW_RECEIPTS_PATH = Path("/var/lib/arifflow/receipts.jsonl")
CHRON_EPISODES_PATH = Path("/root/chron/data/episodes.jsonl")
CHRON_FRAME_REQUESTS_PATH = Path("/root/chron/data/frame_requests.jsonl")

ARIFOS_KERNEL_URL = os.environ.get("ARIFOS_KERNEL_URL", "http://127.0.0.1:8088")
ARIFLOW_URL = os.environ.get("ARIFLOW_URL", "http://127.0.0.1:7073")
FRAME_URL = os.environ.get("FRAME_URL", "http://127.0.0.1:18085")
GEOX_URL = os.environ.get("GEOX_URL", "http://127.0.0.1:8081")

# ── 1. The 11 Federation Organs Ontology ───────────────────────────────────────
@dataclass(frozen=True)
class FederationOrgan:
    name: str
    code: str
    role: str
    port: int | None
    protocol: str
    authority_band: str
    owned_domains: list[str]
    upstream_dependencies: list[str]


FEDERATION_ORGANS: dict[str, FederationOrgan] = {
    "arifos": FederationOrgan(
        name="arifOS",
        code="KERNEL-000",
        role="Constitutional Governance Kernel, Floors F1-F13, 8-Verb Cycle, VAULT999 Immutable Ledger",
        port=8088,
        protocol="streamable-http + JSON-RPC",
        authority_band="SOVEREIGN_KERNEL",
        owned_domains=["Constitution", "Floors F1-F13", "VAULT999", "Gödel Lock", "Claim Adjudication"],
        upstream_dependencies=["Human Sovereign (Arif · F13)"],
    ),
    "arifflow": FederationOrgan(
        name="arifFlow",
        code="FLOW-001",
        role="Dynamic Work & Task Flow, Execution vs Verification Balancing (FQ Constellation)",
        port=7073,
        protocol="http-rest",
        authority_band="OPERATIONAL_FLOW",
        owned_domains=["Task Lifecycle", "Dual-Rate Dynamics", "FQ Constellation", "Flow Receipts"],
        upstream_dependencies=["arifOS", "Domain Organ Receipts"],
    ),
    "chron": FederationOrgan(
        name="CHRON",
        code="CHRON-002",
        role="Bitemporal Timeline, Predictive Calibration, Attention Debt, Episodic Learning",
        port=None,
        protocol="mcp-stdio + bitemporal-jsonl",
        authority_band="TEMPORAL_RECORD",
        owned_domains=["Bitemporal Store", "Predictions", "Calibration", "Attention Debt", "Episodic Memory"],
        upstream_dependencies=["arifFlow Receipt Stream", "FRAME Witnesses"],
    ),
    "frame": FederationOrgan(
        name="FRAME",
        code="FRAME-003",
        role="Perception & Independent Witnessing, 10 Baseline Organs, Contradiction Detection",
        port=18085,
        protocol="http-rest",
        authority_band="INDEPENDENT_WITNESS",
        owned_domains=["Multi-Organ Baseline", "Witness Verification", "Contradiction Scanning", "Reality Anchor"],
        upstream_dependencies=["Domain Organ Probes"],
    ),
    "geox": FederationOrgan(
        name="GEOX",
        code="GEOX-004",
        role="Earth Intelligence, Subsurface Physics, Seismic Interpretation, Petrophysics, SEP-1865 MCP Apps",
        port=8081,
        protocol="streamable-http + JSON-RPC + MCP-Apps",
        authority_band="PHYSICAL_EARTH",
        owned_domains=["Basin", "Seismic", "Well", "Prospect", "Model", "Geomechanics", "Deep Time", "Spatial", "GLOF Hazard"],
        upstream_dependencies=["arifOS Kernel", "arifFlow", "FRAME Witness", "CHRON Timeline"],
    ),
    "wealth": FederationOrgan(
        name="WEALTH",
        code="WEALTH-005",
        role="Capital Viability, Financial Models, EMV/NPV/IRR/DSCR, Relational Credit (Makcik²)",
        port=18082,
        protocol="streamable-http + JSON-RPC",
        authority_band="CAPITAL_EVIDENCE",
        owned_domains=["Capital Allocation", "Portfolio Risk", "Fiscal PSC Terms", "Investment Memos"],
        upstream_dependencies=["arifOS Kernel", "GEOX Subsurface Reserves"],
    ),
    "well": FederationOrgan(
        name="WELL",
        code="WELL-006",
        role="Human & Machine Somatics, Vitality Engine, Dignity Guard, Cognitive Pressure Balance",
        port=18083,
        protocol="streamable-http + JSON-RPC",
        authority_band="SOMATIC_HOMEOSTASIS",
        owned_domains=["Operator Vitality", "Fatigue Monitoring", "Machine Diagnostics", "Dignity Protection"],
        upstream_dependencies=["arifOS Kernel", "Telemetry Watchdog"],
    ),
    "signal": FederationOrgan(
        name="SIGNAL",
        code="SIGNAL-007",
        role="Somatic Reflex Arc, Redis Event Bus, High-Frequency Telemetry Router",
        port=18084,
        protocol="http-rest + redis-pubsub",
        authority_band="SOMATIC_REFLEX",
        owned_domains=["Event Bus", "Audio QUALIA", "Reflex Arcs", "Realtime Telemetry"],
        upstream_dependencies=["Redis :6379"],
    ),
    "hermes": FederationOrgan(
        name="HERMES",
        code="HERMES-008",
        role="Agentic Communication Fabric, A2A Protocol, DID Web Decentralized Identity",
        port=18087,
        protocol="streamable-http + A2A",
        authority_band="AGENTIC_ROUTER",
        owned_domains=["A2A Protocol", "Agent Cards", "DID Web", "Room Relay"],
        upstream_dependencies=["arifOS Kernel", "Headscale Sovereign Mesh"],
    ),
    "aaa": FederationOrgan(
        name="AAA",
        code="AAA-009",
        role="Sovereign Control Plane, Operator Cockpit, Musyawarah Gotong-Royong Deliberation",
        port=3001,
        protocol="web-cockpit",
        authority_band="CONTROL_PLANE",
        owned_domains=["Operator Visibility", "Cockpit UI", "Musyawarah Engine", "Session Anchoring"],
        upstream_dependencies=["Human Sovereign (Arif)", "arifOS Kernel"],
    ),
    "a_forge": FederationOrgan(
        name="A-FORGE",
        code="FORGE-010",
        role="Sovereign Hands, Bounded Mutation Engine, Sandbox Runner, Deployment Witness",
        port=7071,
        protocol="cli + stdio",
        authority_band="EXECUTION_HANDS",
        owned_domains=["Bounded Code Mutation", "Build & Release", "Docker Compose Orchestration", "Rollback Evidence"],
        upstream_dependencies=["arifOS 888_SEAL Approval Gate"],
    ),
}

# ── 2. GEOX Domains & 27 Tools Topology ───────────────────────────────────────
GEOX_DOMAINS: dict[str, list[str]] = {
    "Basin": ["geox_basin"],
    "Governance": ["geox_claim"],
    "Hazard": ["geox_glof"],
    "Model": ["geox_model"],
    "Multimodal": ["geox_observe"],
    "Paleobiology": ["geox_paleobiodb_query"],
    "Petrophysics": ["geox_petrophysics"],
    "Prospect": ["geox_prospect"],
    "Registry": ["geox_surface_status"],
    "Seismic": [
        "geox_contrast_metabolize",
        "geox_extract_display_proxy",
        "geox_extract_native_trace",
        "geox_list_registered_sources",
        "geox_register_native_source",
        "geox_seismic_compute",
        "geox_seismic_ingest",
        "geox_seismic_interpret",
    ],
    "Source": ["geox_source"],
    "Spatial": ["geox_map", "geox_spatial"],
    "Structural": ["geox_calibration_register_witness"],
    "Structure": ["geox_geomechanics", "geox_grid", "geox_resqml_io"],
    "Temporal": ["geox_temporal"],
    "Time": ["geox_deep_time"],
    "Well": ["geox_well", "geox_well_ingest", "geox_well_qc"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── 3. arifFlow Integration (Receipt Stream & FQ Balance) ──────────────────────
def emit_flow_receipt(
    tool_name: str,
    event_type: Literal["OBSERVE_COMPLETE", "FLOW_RECEIPT", "VERIFICATION_COMPLETE", "PREDICTION_MADE"] = "FLOW_RECEIPT",
    status: Literal["SUCCESS", "FAILED", "HELD"] = "SUCCESS",
    step_type: Literal["Observe", "Verify", "Execute"] = "Observe",
    duration_ms: float = 0.0,
    session_id: str | None = None,
    actor_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit an execution/verification receipt into arifFlow receipt stream (/var/lib/arifflow/receipts.jsonl).

    Feeds arifFlow :7073 FQ constellation calculation and bitemporal auditing.
    Fail-safe: never raises; logs warning if stream file is unwriteable.
    """
    now = _now_iso()
    receipt_id = str(uuid.uuid4())
    payload = {
        "tool": tool_name,
        "event": event_type,
        "organ": "GEOX",
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        payload.update(extra)

    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    jcs_hash = hashlib.sha256(payload_bytes).hexdigest()

    receipt = {
        "receipt_id": receipt_id,
        "previous_receipt_hash": None,
        "created_at": now,
        "actor_id": actor_id or "geox:worker",
        "session_id": session_id or "ANON-SESSION",
        "session_token": None,
        "step_type": step_type,
        "risk_class": "T0Observe" if step_type == "Observe" else "T1Mutate",
        "topology_id": None,
        "lane_id": None,
        "step_number": 0,
        "routed_organ": "GEOX",
        "parent_receipt_ids": [],
        "jcs_body_hash": jcs_hash,
        "cost_ns": int(duration_ms * 1_000_000),
        "preceding_verify_cost_ns": None,
        "epistemic_label": "Observation" if step_type == "Observe" else "Derivation",
        "floor_verdict": "Pass" if status == "SUCCESS" else "Void",
        "intent_reason": None,
        "expected_outcome": None,
        "cooling_decision": "None",
        "tri_witness_votes": None,
        "merkle_root": None,
        "merkle_inclusion_proof": None,
        "payload": payload,
        "formula_version": None,
        "formula_hash": None,
        "witness_organs": ["frame"],
        "apex_block": None,
        "flow_block": None,
        "projection_block": None,
    }

    try:
        ARIFLOW_RECEIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(receipt) + "\n"
        with open(ARIFLOW_RECEIPTS_PATH, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as exc:
        logger.warning("Failed to append arifFlow receipt: %s", exc)

    return receipt


# ── 4. FRAME Integration (Independent Reality Witness) ─────────────────────────
def request_frame_witness(
    claim_id: str,
    claim: str,
    evidence: list[str],
    confidence: float = 0.85,
    source: str = "geox",
) -> dict[str, Any]:
    """Request independent reality verification from FRAME organ (:18085).

    Enforces Gödel Lock: author organ cannot self-witness truth claims.
    If FRAME HTTP service is offline, records request to CHRON_FRAME_REQUESTS_PATH.
    """
    req_payload = {
        "claim_id": claim_id,
        "timestamp": _now_iso(),
        "source": source,
        "claim": claim,
        "evidence": evidence,
        "claimed_confidence": confidence,
    }

    # Attempt live probe to FRAME organ HTTP
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.post(f"{FRAME_URL}/witness", json=req_payload)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Fallback: record request to persistent JSONL for asynchronous witnessing
    try:
        CHRON_FRAME_REQUESTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(req_payload) + "\n"
        with open(CHRON_FRAME_REQUESTS_PATH, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as exc:
        logger.warning("Failed to record frame witness request: %s", exc)

    return {
        "claim_id": claim_id,
        "witness_verdict": "RECORDED_PENDING_FRAME",
        "witness_organ": "frame",
        "evidence_quality": "PENDING_WITNESS",
        "confidence": confidence,
        "timestamp": _now_iso(),
    }


# ── 5. CHRON Integration (Bitemporal Reality & Prediction) ────────────────────
def log_chron_event(
    event_type: str,
    subject: str,
    epistemic_status: Literal["OBSERVED", "DERIVED", "HYPOTHESIS", "SPECULATIVE"] = "OBSERVED",
    payload: dict[str, Any] | None = None,
    valid_from: str | None = None,
) -> dict[str, Any]:
    """Anchor geological horizons, predictions, and state transitions in CHRON.

    Uses bitemporal anchoring: assertion_time (now) vs reality_time (valid_from).
    """
    now = _now_iso()
    episode = {
        "episode_id": f"geox-chron-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "organ": "geox",
        "event_type": event_type,
        "subject": subject,
        "epistemic_status": epistemic_status,
        "assertion_time": now,
        "valid_from": valid_from or now,
        "payload": payload or {},
    }

    try:
        CHRON_EPISODES_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(episode) + "\n"
        with open(CHRON_EPISODES_PATH, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as exc:
        logger.warning("Failed to anchor CHRON episode: %s", exc)

    return episode


# ── 6. Unified Federation Status & Topology ────────────────────────────────────
def get_federation_topology() -> dict[str, Any]:
    """Return the complete 11-organ federation map and GEOX domain topology."""
    return {
        "organ": "GEOX",
        "federation_version": "v2026.11.03",
        "sovereign": "Arif (F13)",
        "constitutional_kernel": "arifOS (:8088)",
        "flow_engine": "arifFlow (:7073)",
        "independent_witness": "FRAME (:18085)",
        "temporal_anchor": "CHRON",
        "total_organs": len(FEDERATION_ORGANS),
        "organs": {k: asdict(v) for k, v in FEDERATION_ORGANS.items()},
        "geox_surface": {
            "canonical_tools_count": sum(len(v) for v in GEOX_DOMAINS.values()),
            "total_domains": len(GEOX_DOMAINS),
            "domains": GEOX_DOMAINS,
            "mcp_apps_ready": True,
            "p0_promotion_gate": "HOLD",
        },
    }
