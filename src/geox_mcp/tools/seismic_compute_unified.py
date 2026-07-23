"""
geox_seismic_compute — Unified Seismic Computation (Phase 2)
════════════════════════════════════════════════════════════
Absorbs: geox_seismic_compute, geox_seismic_compute_attribute_tool, geox_seismic_inversion

Modes: synthetic, well_tie, time_depth_anchor, anomalous_contrast, attribute, inversion

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal


async def geox_seismic_compute(
    mode: Literal["synthetic", "well_tie", "time_depth_anchor", "anomalous_contrast", "attribute", "inversion"] = "synthetic",
    volume_ref: str | None = None,
    attribute: str = "rms",
    frame_index: int | None = None,
    orientation: str = "inline",
    window_size: int = 11,
    provenance: str = "fixture",
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
    # F1 zen section inputs (attribute mode)
    image_path: str | None = None,
    amplitude_grid: list[list[float]] | None = None,
    volume_inline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unified seismic computation.

    Modes:
      synthetic          - Forward model S = w * r + n
      well_tie           - Seismic-to-well tie with cross-correlation
      time_depth_anchor  - Checkshot/VSP anchoring
      anomalous_contrast - AVO class I-IV anomalous contrast detection
      attribute          - F1 zen: rms/coherence/discontinuity/dip on 2D section
      inversion          - 1D post-stack PINN seismic inversion
    """
    kwargs = locals().copy()
    if mode == "attribute":
        # F1 zen: real 2D section attributes (rms/coherence/dip). Volume-only
        # refs without a frame still HOLD honestly.
        from geox_mcp.tools.seismic_zen_f1 import zen_attribute

        return await zen_attribute(
            attribute=str(kwargs.get("attribute") or "coherence"),
            window_size=int(kwargs.get("window_size") or 11),
            volume_ref=kwargs.get("volume_ref") or None,
            volume_inline=kwargs.get("volume_inline"),
            image_path=kwargs.get("image_path"),
            amplitude_grid=kwargs.get("amplitude_grid"),
            provenance=str(kwargs.get("provenance") or "fixture"),
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

    # Default: delegate to the canonical geox_seismic_compute implementation (all other modes)
    import inspect

    from geox_mcp.tools.seismic_compute import geox_seismic_compute as _impl

    kwargs.setdefault("mode", mode)
    # Filter kwargs to only pass params the impl accepts
    impl_params = set(inspect.signature(_impl).parameters.keys())
    filtered = {k: v for k, v in kwargs.items() if k in impl_params}
    return await _impl(**filtered)
