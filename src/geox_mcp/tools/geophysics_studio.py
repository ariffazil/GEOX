"""
geophysics_studio.py — GEOX GravMag Studio MCP App (Stage A: forward-only).

Constitutional MCP tool that:
1. Computes gravity or magnetic forward anomaly from a prism model
   via HarmonICAdapter (mock or live backend).
2. Returns MCP Apps payload + sandboxed iframe resource URI for
   visual heatmap rendering.
3. Carries Physics9 epistemic labels, F1 reversibility, F2 evidence,
   F7 confidence cap, F9 anti-hantu, F11 audit. Never SEALs — verdict
   is always QUALIFY (forward-only, no observed comparison yet).

DITEMPA BUKAN DIBERI — Forged, Not Given.

Stage A scope (per Path 1 / Phase A execution plan):
- Forward compute only (gravity or magnetic).
- Mock backend by default; live HarmonIC when GEOX_HARMONICA_LIVE=1.
- Single tool `geox_gravmag_studio_open` returns UI + structured payload.
- HTML resource at `ui://geox/gravmag-studio.html` is a passive Canvas2D
  heatmap renderer; state pushed by host per SEP-1865 ui/notifications.

Stage B (NOT in this file): add `geox_gravmag_studio_screen` with
gravity_screen integration + RMS misfit.
Stage C (NOT in this file): wrap SimPEG cross-gradient joint inversion.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, Literal

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from geox_core.engines.geophysics.harmonica_adapter import (
    GravityMagneticInput,
    HarmonICAdapter,
    NonseismicOutput,
    SurveyType,
)

logger = logging.getLogger("geox.tools.geophysics_studio")

# Stage A canonical surface — names are exposed in geox_tools.geo manifest.
TOOL_NAME = "geox_gravmag_studio_open"
UI_RESOURCE_URI = "ui://geox/gravmag-studio.html"
APP_ID = "geox.gravmag.studio"
APP_VERSION = "0.1.0"
UI_EVENT = "geox.gravmag.forward"

# Physics9: confidence cap per F5 HUMILITY (kept here for reference only;
# actual confidence is in NonseismicOutput.epistemic_provenance).
MAX_CONFIDENCE = 0.90


# ───────────────────────────── SCHEMAS ────────────────────────────────────────
class GravMagStudioRequest(BaseModel):
    """Input schema for geox_gravmag_studio_open."""

    survey_type: SurveyType = "gravity"
    prisms: list[dict] = Field(
        default_factory=list,
        description=(
            "Rectangular prisms. Each: {easting, northing, depth_top, depth_bottom, "
            "width_e, width_n, density (gravity) or susceptibility (magnetic)}. "
            "Empty list = flat zero anomaly."
        ),
    )
    magnetization_a_m: float = Field(
        default=0.0,
        description="Effective magnetization magnitude A/m (magnetic only).",
    )
    field_declination_deg: float = Field(default=0.0)
    field_inclination_deg: float = Field(default=0.0)
    grid_extent_m: float = Field(
        default=50000.0,
        gt=0,
        description="Half-extent of survey grid (m).",
    )
    grid_n: int = Field(
        default=40,
        ge=8,
        le=200,
        description="Grid samples per axis.",
    )
    backend: Literal["auto", "mock", "harmonica_live"] = Field(
        default="auto",
        description="auto = MockHarmonICBackend unless GEOX_HARMONICA_LIVE=1.",
    )

    model_config = {"extra": "forbid"}


class GravMagStudioResponse(BaseModel):
    """Output envelope — UI + structured payload + provenance."""

    tool_name: str = TOOL_NAME
    claim_tag: Literal["FACT", "INTERPRETATION", "SPECULATION"] = "SPECULATION"
    verdict: Literal["SEAL", "QUALIFY", "HOLD", "VOID", "888_HOLD"] = "QUALIFY"
    ui: dict[str, Any]
    vault_receipt: dict[str, Any]
    input: dict[str, Any]
    render_payload: dict[str, Any]
    arifos: dict[str, Any]
    provenance: str
    library: str
    library_version: str | None
    caveats: list[str]
    timestamp_utc: str

    model_config = {"extra": "forbid"}


# ───────────────────────────── CORE COMPUTE ────────────────────────────────────
def _build_grid(grid_extent_m: float, grid_n: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Symmetric grid centred at origin."""
    if grid_n < 2:
        raise ValueError("grid_n must be >= 2")
    step = (2.0 * grid_extent_m) / (grid_n - 1) if grid_n > 1 else 0.0
    easting = tuple(-grid_extent_m + i * step for i in range(grid_n))
    northing = tuple(-grid_extent_m + i * step for i in range(grid_n))
    return easting, northing


def _resolve_backend(backend: str) -> tuple[HarmonICAdapter, str]:
    """Return (adapter, library_label)."""
    if backend == "mock":
        # Force mock even when GEOX_HARMONICA_LIVE=1.
        return HarmonICAdapter(backend=_MockBackend()), "mock"
    if backend == "harmonica_live":
        return HarmonICAdapter(backend=_LiveBackend()), "harmonica"
    # auto
    return HarmonICAdapter(), os.environ.get("GEOX_HARMONICA_LIVE") == "1" and "harmonica" or "mock"


class _MockBackend:
    """Lightweight inline mock so 'auto' never depends on real HarmonIC import."""

    def __init__(self):
        from geox_core.engines.geophysics.harmonica_adapter import MockHarmonICBackend

        self._inner = MockHarmonICBackend()

    def is_available(self) -> bool:
        return self._inner.is_available()

    def forward(self, payload):
        return self._inner.forward(payload)


class _LiveBackend:
    """Inline live HarmonIC backend wrapper."""

    def __init__(self):
        from geox_core.engines.geophysics.harmonica_adapter import LiveHarmonICBackend

        self._inner = LiveHarmonICBackend()

    def is_available(self) -> bool:
        return self._inner.is_available()

    def forward(self, payload):
        return self._inner.forward(payload)


def _build_render_payload(
    out: NonseismicOutput,
    survey_type: str,
    backend: str,
    library_version: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Slice NonseismicOutput into render-payload shape + caveats."""
    values = list(out.anomaly_values)
    shape = list(out.grid_shape)  # (n_northing, n_easting) per HarmonICAdapter
    finite_vals = [v for v in values if v == v]  # filter NaN
    if finite_vals:
        vmin, vmax = min(finite_vals), max(finite_vals)
    else:
        vmin, vmax = 0.0, 0.0

    caveats = [
        "Stage A: forward-only — output is SPECULATION until compared with OBSERVED data (Stage B screen).",
        f"Backend: {backend}; library_version: {library_version or 'unknown'}.",
    ]
    if backend == "mock":
        caveats.append(
            "MockHarmonICBackend uses point-mass approximation. For real geophysics, "
            "set GEOX_HARMONICA_LIVE=1 and re-invoke with backend='harmonica_live'."
        )
    if out.epistemic_provenance.get("caveat"):
        caveats.append(str(out.epistemic_provenance["caveat"]))

    payload = {
        "type": "anomaly_grid",
        "survey_type": survey_type,
        "anomaly_values": values,
        "grid_shape": shape,
        "units": {"gravity": "mGal", "magnetic": "nT"},
        "value_range": [vmin, vmax],
        "backend": backend,
        "library_version": library_version,
        "epistemic_label": "SPEC",
        "caveats": caveats,
    }
    return payload, caveats


# ───────────────────────────── TOOL ENTRY ─────────────────────────────────────
async def geox_gravmag_studio_open(
    survey_type: SurveyType = "gravity",
    prisms: list[dict] | None = None,
    magnetization_a_m: float = 0.0,
    field_declination_deg: float = 0.0,
    field_inclination_deg: float = 0.0,
    grid_extent_m: float = 50000.0,
    grid_n: int = 40,
    backend: Literal["auto", "mock", "harmonica_live"] = "auto",
) -> dict[str, Any]:
    """Open GEOX GravMag Studio — forward-only MCP App.

    Computes gravity or magnetic anomaly from a rectangular-prism model
    via HarmonICAdapter (mock or live) and returns the MCP Apps payload
    for the studio iframe at ``ui://geox/gravmag-studio.html``.

    Returns a structured envelope with:
      - ``ui.resourceUri`` pointing to the studio iframe
      - ``render_payload`` baked with anomaly grid for the heatmap
      - ``vault_receipt`` (audit, NOT a SEAL)
      - ``input`` echo of all params for reproducibility
      - ``provenance`` origin string
      - ``caveats`` physics-honesty notes

    Verdict is always ``QUALIFY`` for Stage A (forward-only, no observed
    comparison). Never ``SEAL``.

    Args:
        survey_type: ``"gravity"`` or ``"magnetic"``.
        prisms: List of rectangular-prism dicts. Required for non-zero
            anomaly. Each must include ``easting``, ``northing``,
            ``depth_top``, ``depth_bottom``, ``width_e``, ``width_n``,
            and either ``density`` (kg/m^3 contrast, gravity) or
            ``susceptibility`` (SI, magnetic).
        magnetization_a_m: Effective magnetization magnitude (A/m),
            magnetic only.
        field_declination_deg: Earth's field declination (°), magnetic.
        field_inclination_deg: Earth's field inclination (°), magnetic.
        grid_extent_m: Half-extent of survey grid (m). Default 50 km.
        grid_n: Grid samples per axis. Default 40, max 200.
        backend: ``"auto"`` (mock unless env says otherwise),
            ``"mock"``, or ``"harmonica_live"``.

    Returns:
        dict conforming to geox_gravmag_studio_contract.json v0.1.0.
    """
    prisms = prisms or []
    if grid_n < 8 or grid_n > 200:
        return _error_envelope(
            f"grid_n must be in [8, 200]; got {grid_n}",
            survey_type=survey_type,
            backend=backend,
        )
    if grid_extent_m <= 0:
        return _error_envelope(
            f"grid_extent_m must be > 0; got {grid_extent_m}",
            survey_type=survey_type,
            backend=backend,
        )

    easting, northing = _build_grid(grid_extent_m, grid_n)

    try:
        adapter, lib_label = _resolve_backend(backend)
    except Exception as exc:
        logger.warning("Backend resolution failed; falling back to mock: %s", exc)
        adapter, lib_label = HarmonICAdapter(backend=_MockBackend()), "mock"

    library_version: str | None = None
    if adapter.mode == "live":
        try:
            library_version = adapter._backend._version  # type: ignore[attr-defined]
        except AttributeError:
            library_version = "unknown"

    input_payload = GravityMagneticInput(
        survey_type=survey_type,
        easting_m=easting,
        northing_m=northing,
        prisms=list(prisms),
        magnetization_a_m=magnetization_a_m,
        field_declination_deg=field_declination_deg,
        field_inclination_deg=field_inclination_deg,
    )

    try:
        out: NonseismicOutput = adapter.forward(input_payload)
    except Exception as exc:
        logger.exception("Forward compute failed")
        return _error_envelope(
            f"forward compute failed: {exc}",
            survey_type=survey_type,
            backend=lib_label,
        )

    render_payload, caveats = _build_render_payload(
        out=out,
        survey_type=survey_type,
        backend=lib_label,
        library_version=library_version,
    )

    timestamp = datetime.now(UTC).isoformat()
    input_dict = {
        "survey_type": survey_type,
        "prisms": prisms,
        "magnetization_a_m": magnetization_a_m,
        "field_declination_deg": field_declination_deg,
        "field_inclination_deg": field_inclination_deg,
        "grid_extent_m": grid_extent_m,
        "grid_n": grid_n,
        "backend": backend,
    }
    input_hash = hashlib.sha256(
        json.dumps(input_dict, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    response: dict[str, Any] = {
        "tool_name": TOOL_NAME,
        "claim_tag": "SPECULATION",
        "verdict": "QUALIFY",
        "ui": {
            "resourceUri": UI_RESOURCE_URI,
            "mode": "inline",
            "app_id": APP_ID,
            "version": APP_VERSION,
            "event": UI_EVENT,
        },
        "vault_receipt": {
            "vault": "VAULT999",
            "tool_name": TOOL_NAME,
            "verdict": "QUALIFY",
            "timestamp": timestamp,
            "hash": input_hash,
        },
        "input": input_dict,
        "render_payload": render_payload,
        "arifos": {
            "floors_required": ["F1", "F2", "F7", "F9", "F11"],
            "human_in_loop": ["interpret_recompute", "claim_seal"],
            "vault_route": "VAULT999",
        },
        "provenance": (
            f"harmonica:forward:{survey_type}:{len(prisms)}prisms:"
            f"{grid_n}x{grid_n}@±{grid_extent_m:.0f}m:{lib_label}"
        ),
        "library": lib_label,
        "library_version": library_version,
        "caveats": caveats,
        "timestamp_utc": timestamp,
    }
    return response


def _error_envelope(
    message: str,
    *,
    survey_type: str,
    backend: str,
) -> dict[str, Any]:
    """Stage A failure envelope — verdict downgrades to VOID."""
    timestamp = datetime.now(UTC).isoformat()
    return {
        "tool_name": TOOL_NAME,
        "claim_tag": "SPECULATION",
        "verdict": "VOID",
        "ui": {
            "resourceUri": UI_RESOURCE_URI,
            "mode": "inline",
            "app_id": APP_ID,
            "version": APP_VERSION,
        },
        "vault_receipt": {
            "vault": "VAULT999",
            "tool_name": TOOL_NAME,
            "verdict": "VOID",
            "timestamp": timestamp,
            "hash": hashlib.sha256(message.encode()).hexdigest()[:16],
        },
        "input": {"survey_type": survey_type, "backend": backend},
        "render_payload": {
            "type": "anomaly_grid",
            "survey_type": survey_type,
            "anomaly_values": [],
            "grid_shape": [0, 0],
            "units": {"gravity": "mGal", "magnetic": "nT"},
            "value_range": [0.0, 0.0],
            "backend": backend,
            "library_version": None,
            "epistemic_label": "SPEC",
            "caveats": [f"Stage A compute error: {message}"],
        },
        "arifos": {
            "floors_required": ["F1", "F2", "F9"],
            "human_in_loop": ["error_diagnose"],
            "vault_route": "VAULT999",
        },
        "provenance": f"harmonica:forward:ERROR:{message[:80]}",
        "library": backend,
        "library_version": None,
        "caveats": [f"Stage A compute error: {message}"],
        "timestamp_utc": timestamp,
    }


# ───────────────────────────── REGISTRATION ───────────────────────────────────
def register_gravmag_studio_tools(mcp: FastMCP) -> None:
    """Register geox_gravmag_studio_open as an MCP tool."""

    @mcp.tool(
        name=TOOL_NAME,
        description=(
            "GEOX GravMag Studio — forward-only MCP App. "
            "Computes gravity or magnetic anomaly from a prism model via "
            "HarmonICAdapter (mock or live) and returns the studio iframe "
            "payload at ui://geox/gravmag-studio.html. "
            "Verdict is always QUALIFY (never SEAL) — Stage A is forward-only."
        ),
        annotations={
            "read_only": True,
            "destructive": False,
            "idempotent": True,
        },
    )
    async def _tool(
        survey_type: SurveyType = "gravity",
        prisms: list[dict] | None = None,
        magnetization_a_m: float = 0.0,
        field_declination_deg: float = 0.0,
        field_inclination_deg: float = 0.0,
        grid_extent_m: float = 50000.0,
        grid_n: int = 40,
        backend: Literal["auto", "mock", "harmonica_live"] = "auto",
    ) -> dict[str, Any]:
        return await geox_gravmag_studio_open(
            survey_type=survey_type,
            prisms=prisms,
            magnetization_a_m=magnetization_a_m,
            field_declination_deg=field_declination_deg,
            field_inclination_deg=field_inclination_deg,
            grid_extent_m=grid_extent_m,
            grid_n=grid_n,
            backend=backend,
        )


__all__ = [
    "TOOL_NAME",
    "UI_RESOURCE_URI",
    "APP_ID",
    "APP_VERSION",
    "GravMagStudioRequest",
    "GravMagStudioResponse",
    "geox_gravmag_studio_open",
    "register_gravmag_studio_tools",
]
