"""
ext_witness_stamp — P1 GEOX Ext_witness honesty (2026-07-25).

Every GEOX tool result that agents may treat as Earth evidence must carry:

  mode: live | offline_stub | cached | opendap | synthetic | derived | unknown
  ext_witness_ready: bool   # True only when mode is live (or live-equivalent)

Policy (G-fold / H7 / F2 TRUTH):
  - offline_stub must never silently promote to Φ Ext for SEAL geometry
  - GEOX_REQUIRE_LIVE=1 → fail closed on offline_stub
  - Constitutional G is never minted here (read apex only elsewhere)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("geox_mcp.ext_witness_stamp")

# Modes that count as Ext_witness-ready Earth measurement.
LIVE_EQUIVALENT_MODES: frozenset[str] = frozenset(
    {
        "live",
        "gws_live",
        "opendap",  # network-backed measurement stream
    }
)

# Explicit non-live modes (stubs / synthetic / derived computation).
NON_LIVE_MODES: frozenset[str] = frozenset(
    {
        "offline_stub",
        "stub",
        "cached",
        "synthetic",
        "derived",
        "mock",
        "demo",
        "fixture",
    }
)

MODE_ALIASES: dict[str, str] = {
    "offline": "offline_stub",
    "stub": "offline_stub",
    "offline-stub": "offline_stub",
    "gws": "gws_live",
}


class RequireLiveError(Exception):
    """Raised when GEOX_REQUIRE_LIVE=1 and result mode is offline_stub."""

    def __init__(self, tool_name: str, mode: str, detail: str = "") -> None:
        self.tool_name = tool_name
        self.mode = mode
        self.detail = detail
        msg = (
            f"REQUIRE_LIVE_FAIL: tool={tool_name} mode={mode} "
            f"(GEOX_REQUIRE_LIVE=1 rejects offline_stub Ext). {detail}"
        ).strip()
        super().__init__(msg)


def require_live_enabled() -> bool:
    """True when GEOX_REQUIRE_LIVE is truthy (1/true/yes/on)."""
    raw = (os.environ.get("GEOX_REQUIRE_LIVE") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def normalize_mode(raw: Any) -> str:
    """Canonicalize a mode token. Unknown non-empty → lowercased as-is."""
    if raw is None:
        return "unknown"
    if not isinstance(raw, str):
        return "unknown"
    token = raw.strip().lower()
    if not token:
        return "unknown"
    return MODE_ALIASES.get(token, token)


def is_ext_witness_ready(mode: str) -> bool:
    """Ext_witness ready only for live-equivalent modes."""
    m = normalize_mode(mode)
    return m in LIVE_EQUIVALENT_MODES


def extract_mode(result: dict[str, Any]) -> str | None:
    """Pull mode from common GEOX result shapes.

    Priority:
      1. top-level mode when it is a data-source mode
      2. provenance.mode / evidence.mode / envelope.mode
      3. nested data.mode / fetch.mode
    """
    candidates: list[Any] = [
        result.get("mode"),
        result.get("data_mode"),
        result.get("fetch_mode"),
        result.get("io_mode"),
    ]
    prov = result.get("provenance")
    if isinstance(prov, dict):
        candidates.append(prov.get("mode"))
        candidates.append(prov.get("data_mode"))
    evidence = result.get("evidence")
    if isinstance(evidence, dict):
        candidates.append(evidence.get("mode"))
    env = result.get("envelope")
    if isinstance(env, dict):
        candidates.append(env.get("mode"))
    data = result.get("data")
    if isinstance(data, dict):
        candidates.append(data.get("mode"))
    fetch = result.get("fetch")
    if isinstance(fetch, dict):
        candidates.append(fetch.get("mode"))

    # Tool-operation "mode" (e.g. interpret_section) is NOT a data source mode.
    # Prefer tokens that look like data-source modes when multiple exist.
    data_source_hits: list[str] = []
    any_hits: list[str] = []
    for c in candidates:
        if not isinstance(c, str) or not c.strip():
            continue
        n = normalize_mode(c)
        any_hits.append(n)
        if n in LIVE_EQUIVALENT_MODES or n in NON_LIVE_MODES:
            data_source_hits.append(n)
    if data_source_hits:
        return data_source_hits[0]
    return None


def infer_mode(tool_name: str, result: dict[str, Any]) -> str:
    """Infer mode when the tool body did not set a data-source mode.

    Heuristics (honest defaults, F7):
      - offline_stub if note/message mentions offline
      - synthetic if fixture/demo/synthetic flags
      - derived for pure computation tools without external fetch
      - unknown otherwise (never invent live)
    """
    extracted = extract_mode(result)
    if extracted is not None:
        return extracted

    blob_parts: list[str] = []
    for k in ("note", "message", "warning", "status_note", "epistemic_status"):
        v = result.get(k)
        if isinstance(v, str):
            blob_parts.append(v.lower())
    blob = " ".join(blob_parts)

    if "offline_stub" in blob or "offline mode" in blob or "offline_stub" in str(result.get("status", "")).lower():
        return "offline_stub"
    if any(x in blob for x in ("synthetic", "fixture", "demo only", "mock")):
        return "synthetic"
    if result.get("synthetic") is True or result.get("is_synthetic") is True:
        return "synthetic"
    if result.get("offline") is True:
        return "offline_stub"

    # Earth surface / IO tool names default honest when silent
    tn = (tool_name or "").lower()
    if any(
        s in tn
        for s in (
            "earthquake",
            "relief",
            "bathymetry",
            "emag2",
            "grace",
            "era5",
            "landsat",
            "onegeology",
            "usgs",
            "gebco",
            "etopo",
            "heatflow",
            "gplates",
            "copernicus",
            "earthchem",
            "erddap",
            "wsm",
            "paleomag",
            "noaa",
        )
    ):
        # These fetchers default offline_stub when env offline — if no mode, assume stub.
        return "offline_stub"

    # Pure interpretation / compute without external fetch → derived
    if any(
        s in tn
        for s in (
            "interpret",
            "petrophysics",
            "structure_validate",
            "prospect",
            "falsify",
            "claim",
            "qc",
            "volumetric",
        )
    ):
        return "derived"

    return "unknown"


def _as_dict(result: Any) -> dict[str, Any] | None:
    """Coerce tool results to a plain dict when possible."""
    if isinstance(result, dict):
        return result
    dump = getattr(result, "model_dump", None)
    if callable(dump):
        try:
            d = dump(mode="json")
            return d if isinstance(d, dict) else None
        except TypeError:
            try:
                d = dump()
                return d if isinstance(d, dict) else None
            except Exception:  # noqa: BLE001
                return None
        except Exception:  # noqa: BLE001
            return None
    try:
        import dataclasses

        if dataclasses.is_dataclass(result) and not isinstance(result, type):
            return dataclasses.asdict(result)
    except Exception:  # noqa: BLE001
        pass
    return None


def stamp_ext_witness(
    result: Any,
    *,
    tool_name: str = "",
    force_mode: str | None = None,
) -> Any:
    """Stamp mode + ext_witness_ready on a tool result dict.

    Non-dict / non-model results pass through unchanged.
    Existing explicit data-source mode is preserved (normalized).
    Never invents mode=live.
    """
    base = _as_dict(result)
    if base is None:
        return result

    out = dict(base)
    if force_mode:
        data_mode = normalize_mode(force_mode)
    else:
        data_mode = infer_mode(tool_name, out)

    ready = is_ext_witness_ready(data_mode)
    out["data_mode"] = data_mode
    out["ext_witness_ready"] = ready

    # Preserve tool-operation mode (e.g. interpret_section) when present and
    # not a data-source token; always surface data_mode for Ext_witness policy.
    top = normalize_mode(out.get("mode")) if out.get("mode") is not None else ""
    if not top or top == "unknown" or top in LIVE_EQUIVALENT_MODES or top in NON_LIVE_MODES:
        out["mode"] = data_mode
    # else: keep tool operation mode; data_mode holds Ext_witness truth

    if not ready:
        out.setdefault(
            "ext_witness_note",
            f"mode={data_mode} is not Ext_witness-ready for SEAL geometry (need live)",
        )

    prov = out.get("provenance")
    prov = dict(prov) if isinstance(prov, dict) else {}
    prov.setdefault("organ", "geox")
    prov["mode"] = data_mode
    prov["ext_witness_ready"] = ready
    out["provenance"] = prov

    return out


def enforce_require_live(result: Any, *, tool_name: str) -> Any:
    """If GEOX_REQUIRE_LIVE=1 and mode is offline_stub → raise RequireLiveError.

    Call after stamp_ext_witness. Passes through when flag unset.
    """
    if not require_live_enabled():
        return result
    if not isinstance(result, dict):
        return result

    mode = normalize_mode(result.get("data_mode") or result.get("mode"))
    if mode in ("offline_stub", "stub", "mock"):
        raise RequireLiveError(
            tool_name=tool_name,
            mode=mode,
            detail=str(result.get("note") or result.get("ext_witness_note") or ""),
        )
    return result


def stamp_and_gate(result: Any, *, tool_name: str) -> Any:
    """Stamp then enforce require_live. Single entry for middleware."""
    stamped = stamp_ext_witness(result, tool_name=tool_name)
    return enforce_require_live(stamped, tool_name=tool_name)
