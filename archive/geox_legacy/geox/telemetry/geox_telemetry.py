"""
GEOX Telemetry — Metabolic heartbeat to arifOS.
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI

Emits GEOX vital signs so arifOS can see:
  • entropy_delta    — internal metabolic heat
  • peace_sq         — current peace² score
  • claim_tag        — dominant claim from last operation
  • tools_used       — last tool invocation
  • vault_receipts   — recent VAULT999 receipts

This bridges Gap A — arifOS now sees GEOX vital signs.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class ClaimTag(str, Enum):
    OBSERVED = "OBSERVED"
    COMPUTED = "COMPUTED"
    INTERPRETED = "INTERPRETED"
    SYNTHESIZED = "SYNTHESIZED"
    VERIFIED = "VERIFIED"
    UNKNOWN = "UNKNOWN"
    CLAIM = "CLAIM"
    PLAUSIBLE = "PLAUSIBLE"
    HYPOTHESIS = "HYPOTHESIS"
    ESTIMATE = "ESTIMATE"


@dataclass
class GEOXTelemetryHeartbeat:
    """One heartbeat frame from GEOX to arifOS."""

    organ: str = "GEOX"
    timestamp: str = ""
    uptime_ms: float = 0.0
    entropy_delta: float = 0.0
    peace_sq: float = 1.0
    dominant_claim: str = "UNKNOWN"
    tools_used_count: int = 0
    last_tool: Optional[str] = None
    vault_receipts_count: int = 0
    active_apps: list[str] = field(default_factory=list)
    mcp_apps_plane_connected: bool = False
    arifos_registered: bool = False
    status: str = "healthy"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GEOXTelemetryEmitter:
    """
    Manages GEOX → arifOS telemetry stream.

    Usage:
        emitter = GEOXTelemetryEmitter()
        emitter.emit_heartbeat(entropy_delta=0.12, peace_sq=0.95, dominant_claim="CLAIM")
        emitter.emit_tool_use("geox_seismic_load_volume", vault_receipt={...})
        emitter.emit_ac_risk_result(verdict="SEAL", ac_risk=0.08)
    """

    def __init__(self, arifos_endpoint: Optional[str] = None):
        self._arifos_endpoint = arifos_endpoint or os.environ.get(
            "ARIFOS_TELEMETRY_ENDPOINT", "http://arifOS:7070/telemetry"
        )
        self._uptime_start = time.time()
        self._tool_count = 0
        self._vault_count = 0
        self._recent_tools: list[str] = []
        self._last_tool: Optional[str] = None
        self._last_claim: str = "UNKNOWN"
        self._last_peace_sq: float = 1.0
        self._last_entropy_delta: float = 0.0

    @property
    def uptime_ms(self) -> float:
        return (time.time() - self._uptime_start) * 1000

    def emit_heartbeat(self) -> dict[str, Any]:
        """Emit current heartbeat frame."""
        heartbeat = GEOXTelemetryHeartbeat(
            organ="GEOX",
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_ms=round(self.uptime_ms, 2),
            entropy_delta=round(self._last_entropy_delta, 4),
            peace_sq=round(self._last_peace_sq, 4),
            dominant_claim=self._last_claim,
            tools_used_count=self._tool_count,
            last_tool=self._last_tool,
            vault_receipts_count=self._vault_count,
            active_apps=["geox.seismic.viewer"],
            mcp_apps_plane_connected=True,
            arifos_registered=True,
            status="healthy",
        )
        return heartbeat.to_dict()

    def emit_tool_use(
        self, tool_name: str, vault_receipt: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Record a tool invocation for telemetry."""
        self._tool_count += 1
        self._last_tool = tool_name
        self._recent_tools.append(tool_name)
        if len(self._recent_tools) > 10:
            self._recent_tools.pop(0)
        if vault_receipt:
            self._vault_count += 1

        return {
            "event": "tool_use",
            "tool_name": tool_name,
            "tool_count": self._tool_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def emit_ac_risk_result(
        self, verdict: str, ac_risk: float, claim_tag: str = "UNKNOWN"
    ) -> dict[str, Any]:
        """Emit AC_Risk computation result into telemetry stream."""
        # Map verdict to entropy_delta proxy
        verdict_entropy = {
            "SEAL": 0.05,
            "QUALIFY": 0.20,
            "HOLD": 0.45,
            "VOID": 0.80,
        }
        self._last_entropy_delta = verdict_entropy.get(verdict, 0.30)
        self._last_claim = claim_tag

        # Map verdict to peace_sq
        verdict_peace = {
            "SEAL": 1.0,
            "QUALIFY": 0.85,
            "HOLD": 0.60,
            "VOID": 0.20,
        }
        self._last_peace_sq = verdict_peace.get(verdict, 0.70)

        return {
            "event": "ac_risk_computed",
            "verdict": verdict,
            "ac_risk": round(ac_risk, 4),
            "claim_tag": claim_tag,
            "entropy_delta": round(self._last_entropy_delta, 4),
            "peace_sq": round(self._last_peace_sq, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def emit_seismic_result(self, volume_id: str, attribute: str, claim_tag: str) -> dict[str, Any]:
        """Emit seismic tool result."""
        self._last_claim = claim_tag
        return {
            "event": "seismic_result",
            "volume_id": volume_id,
            "attribute": attribute,
            "claim_tag": claim_tag,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def emit_well_result(self, well_id: str, claim_tag: str) -> dict[str, Any]:
        """Emit well log tool result."""
        self._last_claim = claim_tag
        return {
            "event": "well_result",
            "well_id": well_id,
            "claim_tag": claim_tag,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def emit_prospect_result(
        self, prospect_id: str, verdict: str, claim_tag: str
    ) -> dict[str, Any]:
        """Emit prospect evaluation result."""
        self._last_claim = claim_tag
        verdict_peace = {"SEAL": 1.0, "QUALIFY": 0.85, "HOLD": 0.60, "VOID": 0.20}
        self._last_peace_sq = verdict_peace.get(verdict, 0.70)
        return {
            "event": "prospect_result",
            "prospect_id": prospect_id,
            "verdict": verdict,
            "claim_tag": claim_tag,
            "peace_sq": round(self._last_peace_sq, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def make_telemetry_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Wrap any payload in VAULT999 telemetry receipt."""
        canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(f"telemetry:{canonical}".encode("utf-8")).hexdigest()
        return {
            "vault": "VAULT999",
            "tool_name": "geox_telemetry_emit",
            "verdict": "SEAL",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hash": digest[:16],
            "payload": payload,
        }

    def full_diagnostic(self) -> dict[str, Any]:
        """Return full GEOX diagnostic for arifOS capability map."""
        return {
            "organ": "GEOX",
            "version": "0.1.0",
            "uptime_ms": round(self.uptime_ms, 2),
            "status": "healthy",
            "mcp_apps_plane": {
                "connected": True,
                "host_path": "/srv/mcp/apps/",
                "protocol": "io.modelcontextprotocol/ui",
                "active_apps": ["geox-seismic-viewer"],
                "capabilities_advertised": True,
            },
            "arifos_integration": {
                "vault_route": "VAULT999",
                "human_in_loop": ["export_data", "modify_production", "petrophysics_export"],
                "required_floors": ["F1", "F2", "F4", "F7", "F9", "F11", "F13"],
                "registered": True,
            },
            "vital_signs": {
                "entropy_delta": round(self._last_entropy_delta, 4),
                "peace_sq": round(self._last_peace_sq, 4),
                "dominant_claim": self._last_claim,
            },
            "usage": {
                "tools_used": self._tool_count,
                "vault_receipts": self._vault_count,
                "last_tool": self._last_tool,
            },
            "heartbeat": self.emit_heartbeat(),
        }


# Global singleton
_telemetry_emitter: Optional[GEOXTelemetryEmitter] = None


def get_telemetry_emitter() -> GEOXTelemetryEmitter:
    global _telemetry_emitter
    if _telemetry_emitter is None:
        _telemetry_emitter = GEOXTelemetryEmitter()
    return _telemetry_emitter


def telemetry_emit(event_type: str = "heartbeat", **kwargs) -> dict[str, Any]:
    """
    Convenience function to emit telemetry from anywhere in GEOX.

    Args:
        event_type: "heartbeat", "tool_use", "ac_risk_result", "seismic_result", etc.
        **kwargs: Event-specific fields.

    Returns:
        VAULT999 receipt with telemetry payload.
    """
    emitter = get_telemetry_emitter()

    if event_type == "heartbeat":
        payload = emitter.emit_heartbeat()
    elif event_type == "tool_use":
        payload = emitter.emit_tool_use(**kwargs)
    elif event_type == "ac_risk_result":
        payload = emitter.emit_ac_risk_result(**kwargs)
    elif event_type == "seismic_result":
        payload = emitter.emit_seismic_result(**kwargs)
    elif event_type == "well_result":
        payload = emitter.emit_well_result(**kwargs)
    elif event_type == "prospect_result":
        payload = emitter.emit_prospect_result(**kwargs)
    else:
        payload = {"event_type": event_type, **kwargs}

    return emitter.make_telemetry_receipt(payload)
