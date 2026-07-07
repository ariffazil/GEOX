"""
geox_seismic_compute — Unified Seismic Computation (Phase 2.8)
════════════════════════════════════════════════════════════════
Absorbs: geox_seismic_compute, geox_seismic_ingest, geox_seismic_interpret,
         geox_seismic_compute_attribute_tool, geox_seismic_inversion

Modes:
  synthetic           — Forward model S = w * r + n
  well_tie            — Seismic-to-well tie with cross-correlation
  time_depth_anchor   — Checkshot/VSP anchoring
  anomalous_contrast  — AVO class I-IV anomalous contrast detection
  attribute           — Seismic attribute computation
  inversion           — 1D post-stack PINN seismic inversion
  ingest / tengok     — Ingest seismic volume headers (was geox_seismic_ingest)
  interpret / agak    — Pick horizons and track faults (was geox_seismic_interpret)
  cabar               — anomalous contrast falsifier
  sahkan              — well tie validation check

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
from typing import Any, Literal
import inspect


async def geox_seismic_compute(
    mode: Literal[
        "synthetic",
        "well_tie",
        "time_depth_anchor",
        "anomalous_contrast",
        "attribute",
        "inversion",
        "ingest",
        "interpret",
        "tengok",
        "agak",
        "cabar",
        "sahkan",
    ] = "synthetic",
    volume_ref: str | None = None,
    attribute: str | None = None,
    frame_index: int | None = None,
    orientation: str | None = None,
    window_size: int = 11,
    provenance: str | None = None,
    reflectivity: list[float] | None = None,
    sample_interval_s: float = 0.002,
    initial_impedance: float = 7000000,
    depth_top_m: float = 0,
    resistivity_ohm_m: list[float] | None = None,
    well_id: str | None = None,
    vp: list[float] | None = None,
    rho: list[float] | None = None,
    depth: list[float] | None = None,
    wavelet_type: str = "ricker",
    wavelet_freq: float = 30.0,
    wavelet_params: dict[str, Any] | None = None,
    water_depth_m: float = 0.0,
    vp_water: float = 1500.0,
    dt_ms: float = 2.0,
    noise_db: float = 0.0,
    output_format: str = "json",
    # SEG-Y / Ingest parameters
    output_path: str | None = None,
    sample_interval_ms: float = 4,
    textual_header: str = "",
    overwrite: bool = False,
    segy_metadata: dict[str, Any] | None = None,
    seismic_metadata: dict[str, Any] | None = None,
    source_uri: str | None = None,
    source_type: str = "seismic",
    # Interpret parameters
    action: str = "get",
    image_data: str | None = None,
    blend_mode: str = "alpha",
    horizon_query: str = "unconformity",
    threshold: float = 0.5,
    confidence_cap: float = 0.9,
    cube_ref: str | None = None,
    volume_inline: dict[str, Any] | None = None,
    attribute_data: dict[str, list[float]] | None = None,
    # Well-tie / checkshot / anomalous contrast parameters
    extraction_window_ms: float = 100.0,
    frequency_band: tuple[float, float] = (10.0, 50.0),
    apply_gardner_fallback: bool = False,
    apply_anisotropy_correction: bool = False,
    q_factor: float = 100.0,
    checkshot_ref: str | None = None,
    drift_threshold_ms: float = 25.0,
    td_method: str = "checkshot",
    ai_profile: list[float] | None = None,
    ac_depth: list[float] | None = None,
    formation_tops: dict[str, float] | None = None,
    rc_threshold: float = 0.05,
    geological_boundary_tolerance_m: float = 5.0,
    ac_vp: list[float] | None = None,
    ac_rho: list[float] | None = None,
    volume_ref_attr: str | None = None,
) -> dict[str, Any]:
    """Unified seismic computation & exploration.

    Modes:
      synthetic          - Forward model S = w * r + n
      well_tie           - Seismic-to-well tie with cross-correlation
      time_depth_anchor  - Checkshot/VSP anchoring
      anomalous_contrast - AVO class I-IV anomalous contrast detection
      attribute          - Seismic attribute computation
      inversion          - 1D post-stack PINN seismic inversion
      ingest / tengok    - Ingest seismic volume headers
      interpret / agak   - Pick horizons and track faults
      cabar              - anomalous contrast falsifier
      sahkan             - well tie validation check
    """
    kwargs = locals().copy()

    # Convert empty strings to None to satisfy validate_tool_inputs
    for k, v in list(kwargs.items()):
        if v == "":
            kwargs[k] = None

    def _filter_args(func: Any, args_dict: dict[str, Any]) -> dict[str, Any]:
        sig = inspect.signature(func)
        has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if has_var_keyword:
            return args_dict
        return {k: v for k, v in args_dict.items() if k in sig.parameters}

    if mode in ("ingest", "tengok"):
        from geox_mcp.tools.seismic_ingest import geox_seismic_ingest as _impl

        if kwargs.get("mode") == "tengok":
            kwargs["mode"] = "inspect_segy"
        return await _impl(**_filter_args(_impl, kwargs))

    if mode in ("interpret", "agak"):
        from geox_mcp.tools.seismic_interpret import geox_seismic_interpret as _impl

        if kwargs.get("mode") == "agak":
            kwargs["mode"] = "horizon_contrast"
        return await _impl(**_filter_args(_impl, kwargs))

    if mode == "cabar":
        kwargs["mode"] = "anomalous_contrast"
        kwargs["ac_depth"] = kwargs.get("ac_depth") or kwargs.get("depth")
        kwargs["ac_vp"] = kwargs.get("ac_vp") or kwargs.get("vp")
        kwargs["ac_rho"] = kwargs.get("ac_rho") or kwargs.get("rho")
        from geox_mcp.tools.seismic_compute import geox_seismic_compute as _impl

        return await _impl(**_filter_args(_impl, kwargs))

    if mode == "sahkan":
        kwargs["mode"] = "well_tie"
        from geox_mcp.tools.seismic_compute import geox_seismic_compute as _impl

        return await _impl(**_filter_args(_impl, kwargs))

    if mode == "attribute":
        from geox_mcp.tools.paleoscan_forge import geox_seismic_compute_attribute_tool as _impl

        return await _impl(
            volume_ref=kwargs.get("volume_ref", ""),
            attribute_name=kwargs.get("attribute", "rms"),
            frame_index=kwargs.get("frame_index"),
            orientation=kwargs.get("orientation", "inline"),
            window_size=kwargs.get("window_size", 11),
            provenance=kwargs.get("provenance", "fixture"),
        )

    if mode == "inversion":
        from geox_mcp.tools.seismic_inversion import geox_seismic_inversion as _impl

        return await _impl(
            reflectivity=kwargs.get("reflectivity"),
            sample_interval_s=kwargs.get("sample_interval_s", 0.002),
            initial_impedance=kwargs.get("initial_impedance", 7000000),
            depth_top_m=kwargs.get("depth_top_m", 0),
            resistivity_ohm_m=kwargs.get("resistivity_ohm_m"),
        )

    # Default: delegate to the canonical geox_seismic_compute implementation
    from geox_mcp.tools.seismic_compute import geox_seismic_compute as _impl

    kwargs.setdefault("mode", mode)
    return await _impl(**_filter_args(_impl, kwargs))
