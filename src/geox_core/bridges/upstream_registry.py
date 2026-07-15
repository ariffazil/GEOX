"""
upstream_registry.py — GEOX upstream bridge registry

Every external data source GEOX depends on registers here:
  • Macrostrat (surface geology, columns, units)
  • USGS, BGS, GPlates (future)
  • Any upstream Earth-data MCP server

Option B enforcement: upstream data enters GEOX through the constitutional
gate (claim_envelope.py), never as a federation peer.

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger("geox.upstream_registry")


# ── Types ─────────────────────────────────────────────────────────────────────


class TrustClass(Enum):
    """Epistemic trust class for upstream sources."""

    EXTERNAL_AUTHORITATIVE = "external_authoritative"  # peer-reviewed DB, official survey
    EXTERNAL_REFERENCE = "external_reference"  # secondary compilation, community
    EXTERNAL_OPINION = "external_opinion"  # model output, derived
    SOVEREIGN = "sovereign"  # GEOX own physics — not upstream


class StalenessBand(Enum):
    """Data freshness band, WELL-style."""

    GREEN = "GREEN"  # < 24h — fresh
    YELLOW = "YELLOW"  # < 7d — stale but usable
    RED = "RED"  # > 7d — actively stale; warn in envelope


@dataclass
class CircuitBreaker:
    """Simple circuit breaker for upstream calls.

    State machine: CLOSED → OPEN (on N consecutive failures) → HALF_OPEN (after cooldown)
    """

    failures: int = 3  # consecutive failures before opening
    cooldown_s: float = 120.0  # seconds before trying again
    _failure_count: int = 0
    _last_failure_time: float = 0.0
    _state: str = "CLOSED"  # CLOSED | OPEN | HALF_OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failures:
            self._state = "OPEN"
            logger.warning("Circuit OPEN after %d consecutive failures", self._failure_count)

    @property
    def state(self) -> str:
        if self._state == "OPEN" and time.time() - self._last_failure_time > self.cooldown_s:
            self._state = "HALF_OPEN"
            logger.info("Circuit HALF_OPEN — cooldown elapsed")
        return self._state

    @property
    def is_allowed(self) -> bool:
        return self.state != "OPEN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "failure_count": self._failure_count,
            "last_failure_ts": self._last_failure_time,
            "cooldown_remaining_s": max(0.0, self.cooldown_s - (time.time() - self._last_failure_time))
            if self._state == "OPEN"
            else 0.0,
        }


@dataclass
class UpstreamSpec:
    """Specification for an upstream data source."""

    name: str  # e.g. "macrostrat"
    transport: str  # "streamable_http" | "stdio" | "rest_api"
    url: Optional[str] = None  # endpoint URL (http/stdio command)
    auth: Optional[dict[str, Any]] = None  # auth config (None = public)
    staleness_band: str = "GREEN<24h|YELLOW<7d|RED>7d"
    trust_class: TrustClass = TrustClass.EXTERNAL_AUTHORITATIVE
    allowed_tools: list[str] = field(default_factory=lambda: ["*"])
    timeout_s: float = 15.0
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    # REST API specific (when transport="rest_api")
    base_url: Optional[str] = None
    api_key_env: Optional[str] = None

    def staleness_band_for(self, age_hours: float) -> StalenessBand:
        if age_hours < 24:
            return StalenessBand.GREEN
        elif age_hours < 168:  # 7 days
            return StalenessBand.YELLOW
        else:
            return StalenessBand.RED


# ── Registry ──────────────────────────────────────────────────────────────────


class UpstreamRegistry:
    """Central registry for all GEOX upstream dependencies.

    One registry, one gate. Every upstream call routes through here.
    """

    def __init__(self) -> None:
        self._specs: dict[str, UpstreamSpec] = {}
        self._clients: dict[str, Any] = {}  # lazy-connected MCP clients or REST sessions

    def register(self, spec: UpstreamSpec) -> None:
        if spec.name in self._specs:
            logger.warning("Upstream '%s' already registered — overwriting", spec.name)
        self._specs[spec.name] = spec
        logger.info("Registered upstream: %s (%s, %s)", spec.name, spec.transport, spec.trust_class.value)

    def get_spec(self, name: str) -> UpstreamSpec:
        spec = self._specs.get(name)
        if spec is None:
            raise KeyError(f"Upstream '{name}' not registered. Available: {list(self._specs.keys())}")
        return spec

    def list_registered(self) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "transport": spec.transport,
                "trust_class": spec.trust_class.value,
                "circuit": spec.circuit_breaker.to_dict(),
                "staleness_band": spec.staleness_band,
            }
            for name, spec in self._specs.items()
        }

    def health(self) -> dict[str, Any]:
        """Return structured health for all upstreams. Exposed via geox_surface_status."""
        return {
            "upstream_count": len(self._specs),
            "upstreams": {
                name: {
                    "registered": True,
                    "circuit": spec.circuit_breaker.to_dict(),
                    "has_client": name in self._clients,
                }
                for name, spec in self._specs.items()
            },
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_REGISTRY: Optional[UpstreamRegistry] = None


def get_registry() -> UpstreamRegistry:
    """Get the singleton upstream registry."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = UpstreamRegistry()
    return _REGISTRY


def reset_registry() -> None:
    """Reset the registry (test isolation)."""
    global _REGISTRY
    _REGISTRY = None


# ── Default registrations ─────────────────────────────────────────────────────


def register_defaults() -> UpstreamRegistry:
    """Register all canonical upstream sources. Called at GEOX server boot."""
    registry = get_registry()

    registry.register(
        UpstreamSpec(
            name="macrostrat",
            transport="rest_api",  # will migrate to "streamable_http" when macrostrat-mcp is deployed
            base_url="https://macrostrat.org/api/v2",
            staleness_band="GREEN<24h|YELLOW<7d|RED>7d",
            trust_class=TrustClass.EXTERNAL_AUTHORITATIVE,
            allowed_tools=["units", "columns", "defs", "fossils", "sources", "measurements", "tiles"],
            timeout_s=15.0,
            circuit_breaker=CircuitBreaker(failures=3, cooldown_s=120),
        )
    )

    logger.info("Default upstreams registered: %s", list(registry._specs.keys()))
    return registry
