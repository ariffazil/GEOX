"""
macrostrat_unified.py — GEOX MCP tool: geox_query_macrostrat

Canonical upstream proxy for Macrostrat geological database.
Replaces: compat.geox_query_macrostrat (deprecated alias), basin_unified macrostrat mode.

Every response returns a structured dict with:
  ok, origin, reason_code, data, attribution, epistemic, staleness

DITEMPA BUKAN DIBERI — upstream data is governed, not inherited.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from geox_core.bridges.upstream_registry import get_registry, TrustClass
from geox_mcp.tools.macrostrat_client import MacrostratClient

logger = logging.getLogger("geox.macrostrat_unified")

# ── Explicit mode → tool map ─────────────────────────────────────────────────
# NO kwargs passthrough. Every mode declares its exact parameter set.
# Unknown kwargs are REJECTED loudly (not silently dropped).

MODE_TO_TOOL: dict[str, dict[str, Any]] = {
    "units": {
        "method": "get_units",
        "params": {
            "lat": {"type": "float", "required": False},
            "lng": {"type": "float", "required": False},
            "bbox": {"type": "array", "required": False},
            "radius_km": {"type": "float", "required": False},
            "col_id": {"type": "int", "required": False},
            "project_id": {"type": "int", "required": False},
            "lithology": {"type": "str", "required": False},
            "age_top": {"type": "float", "required": False},
            "age_bottom": {"type": "float", "required": False},
            "all_units": {"type": "bool", "required": False},
        },
    },
    "columns": {
        "method": "get_columns",
        "params": {
            "lat": {"type": "float", "required": False},
            "lng": {"type": "float", "required": False},
            "bbox": {"type": "array", "required": False},
            "radius_km": {"type": "float", "required": False},
            "col_id": {"type": "int", "required": False},
            "all_units": {"type": "bool", "required": False},
        },
    },
    "sources": {
        "method": "get_sources",
        "params": {},
    },
    "fossils": {
        "method": "get_fossils",
        "params": {},
    },
    "defs": {
        "method": "get_definitions",
        "params": {},
    },
    "measurements": {
        "method": "get_measurements",
        "params": {
            "lat": {"type": "float", "required": False},
            "lng": {"type": "float", "required": False},
            "radius_km": {"type": "float", "required": False},
        },
    },
    "lithologies": {
        "method": "get_lithologies",
        "params": {},
    },
    "environments": {
        "method": "get_environments",
        "params": {},
    },
    "intervals": {
        "method": "get_intervals",
        "params": {},
    },
    "strat_names": {
        "method": "get_strat_names",
        "params": {
            "lithology": {"type": "str", "required": False},
            "age_top": {"type": "float", "required": False},
            "age_bottom": {"type": "float", "required": False},
        },
    },
    "map_units": {
        "method": "get_geologic_units_map",
        "params": {
            "lat": {"type": "float", "required": True},
            "lng": {"type": "float", "required": True},
        },
    },
}

ALLOWED_MODES = sorted(MODE_TO_TOOL.keys())


def _error_envelope(
    reason_code: str,
    error: str,
    retryable: bool = False,
    circuit_state: dict | None = None,
) -> dict:
    """Build a structured error envelope — never a bare string, never null."""
    env: dict = {
        "ok": False,
        "tool": "geox_query_macrostrat",
        "origin": "UPSTREAM_MACROSTRAT",
        "reason_code": reason_code,
        "error": error,
        "retryable": retryable,
    }
    if circuit_state:
        env["circuit_state"] = circuit_state
    return env


async def geox_query_macrostrat(
    mode: str = "units",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    bbox: Optional[list[float]] = None,
    radius_km: Optional[float] = None,
    col_id: Optional[int] = None,
    project_id: Optional[int] = None,
    lithology: Optional[str] = None,
    age_top: Optional[float] = None,
    age_bottom: Optional[float] = None,
    all_units: bool = False,
    session_id: Optional[str] = None,
    **kwargs: Any,
) -> dict:
    """Query the Macrostrat geological database.

    Macrostrat provides regional surface geology — lithology, age, and
    stratigraphic columns derived from published geological maps.
    Data is rung 2 (PROCESS_HYPOTHESIS), not subsurface truth.

    Modes:
      units         — rock units near a point or bbox (richest endpoint)
      columns       — stratigraphic column sections
      sources       — data source bibliography
      fossils       — fossil occurrence data
      defs          — lookup definitions (lithologies, environments, etc.)
      measurements  — geochemical/geochronological measurements
      lithologies   — lithology lookup table
      environments  — depositional environment lookup
      intervals     — time interval definitions
      strat_names   — stratigraphic name dictionary
      map_units     — geologic map units at a point

    Attribution: CC-BY-4.0 — Peters et al. (2018) doi:10.17605/OSF.IO/YNAXW
    """
    # ── Validate mode ─────────────────────────────────────────────────────
    if mode not in MODE_TO_TOOL:
        return _error_envelope(
            reason_code="INVALID_MODE",
            error=f"Unknown mode '{mode}'. Allowed: {', '.join(ALLOWED_MODES)}",
        )

    # ── Reject unknown kwargs (the silent-swallow defense) ────────────────
    allowed_params = set(MODE_TO_TOOL[mode]["params"].keys())
    extra = set(kwargs.keys()) - allowed_params
    if extra:
        return _error_envelope(
            reason_code="UNKNOWN_PARAMETER",
            error=f"Unknown parameter(s) for mode '{mode}': {', '.join(sorted(extra))}. "
            f"Allowed: {', '.join(sorted(allowed_params)) if allowed_params else 'none'}",
        )

    # ── Registry check ──────────────────────────────────────────────────
    registry = get_registry()
    try:
        spec = registry.get_spec("macrostrat")
    except KeyError:
        return _error_envelope(
            reason_code="UPSTREAM_NOT_REGISTERED",
            error="Macrostrat is not registered in the upstream registry.",
        )

    # ── Circuit breaker ──────────────────────────────────────────────────
    cb = spec.circuit_breaker
    if not cb.is_allowed:
        return _error_envelope(
            reason_code="CIRCUIT_OPEN",
            error=f"Circuit is OPEN for macrostrat (cooldown {cb.to_dict()['cooldown_remaining_s']:.0f}s remaining)",
            retryable=True,
            circuit_state=cb.to_dict(),
        )

    # ── Execute ──────────────────────────────────────────────────────────
    try:
        client = MacrostratClient(
            base_url=spec.base_url or "https://macrostrat.org/api/v2",
            timeout=spec.timeout_s,
        )
        method_name = MODE_TO_TOOL[mode]["method"]
        method = getattr(client, method_name)

        # Build call params — only what the mapped mode declares
        call_params: dict[str, Any] = {}
        param_spec = MODE_TO_TOOL[mode]["params"]
        for pname in param_spec:
            val = locals().get(pname)
            if val is not None:
                call_params[pname] = val

        raw = await method(**call_params)
        cb.record_success()

        return {
            "ok": True,
            "tool": "geox_query_macrostrat",
            "mode": mode,
            "origin": "UPSTREAM_MACROSTRAT",
            "actor": "geox_mcp",
            "reason_code": "OK",
            "data": raw,
            "attribution": {
                "license": "CC-BY-4.0",
                "citation": "Peters et al. (2018) doi:10.17605/OSF.IO/YNAXW",
                "notice": "Contains Macrostrat data (c) UW-Madison CC-BY-4.0",
            },
            "epistemic": {
                "rung": 2,
                "grounding": "macrostrat_api_v2",
                "class": TrustClass.EXTERNAL_AUTHORITATIVE.value,
                "caveat": "Regional surface geology — not subsurface truth. Rung-2 only, never rung-3.",
            },
            "staleness_hours": 0.0,
            "circuit_state": cb.to_dict(),
        }

    except ImportError as exc:
        cb.record_failure()
        return _error_envelope(
            reason_code="UPSTREAM_CLIENT_ERROR",
            error=f"MacrostratClient import error: {exc}",
        )

    except Exception as exc:
        cb.record_failure()
        error_str = str(exc)
        # Classify error reason
        if "50" in error_str or "HTTP" in error_str or "500" in error_str or "502" in error_str:
            reason = "UPSTREAM_5XX"
        elif "Timeout" in error_str or "timeout" in error_str:
            reason = "UPSTREAM_TIMEOUT"
        else:
            reason = "UPSTREAM_ERROR"
        return _error_envelope(
            reason_code=reason,
            error=f"Macrostrat API call failed: {error_str}",
            retryable=True,
            circuit_state=cb.to_dict(),
        )
