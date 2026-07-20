"""
geox_sequence — Sequence Stratigraphy (Phase 2)
═══════════════════════════════════════════════
Absorbs: geox_sequence_interpret (renamed, same API)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal


async def geox_sequence(
    workflow: Literal["single_well", "project", "preview", "section_correlation"] = "single_well",
    source: str | None = None,
    zone_top: float | None = None,
    zone_base: float | None = None,
    depo_env_code: str = "FLUVIAL",
    bin_size_m: float = 10.0,
    min_package_thickness_m: float = 20.0,
    p50_shift_api: float = 15.0,
    gr_cutoff_api: float = 75.0,
    detail_level: Literal["bins", "packages", "full"] = "full",
    project_yaml: str | None = None,
    output_dir: str | None = None,
    section_ref: str | None = None,
    well_refs: list[str] | None = None,
    mode: Literal["correlation", "gr_motif", "sequence_stratigraphy", "gde_trend", "well_tie"] = "correlation",
    well_las_paths: list[str] | None = None,
    tops: dict | None = None,
    zone_definitions: dict | None = None,
    strat_standard: dict | None = None,
    paleoenvironment_input: list[dict] | None = None,
    checkshot_ref: str | None = None,
    wavelet_mode: str = "ricker",
    wavelet_freq_hz: list[float] | None = None,
    phase_degrees: float = 0.0,
    polarity: str = "SEG_NORMAL",
    synthetics_output: bool = False,
) -> dict[str, Any]:
    """Sequence stratigraphy — GR binning, parasequence packages, systems tract inference.

    Delegates to geox_sequence_interpret implementation.
    """
    from geox_mcp.tools.sequence import geox_sequence_interpret as _impl

    return await _impl(
        workflow=workflow,
        source=source,
        zone_top=zone_top,
        zone_base=zone_base,
        depo_env_code=depo_env_code,
        bin_size_m=bin_size_m,
        min_package_thickness_m=min_package_thickness_m,
        p50_shift_api=p50_shift_api,
        gr_cutoff_api=gr_cutoff_api,
        detail_level=detail_level,
        project_yaml=project_yaml,
        output_dir=output_dir,
        section_ref=section_ref,
        well_refs=well_refs,
        mode=mode,
        well_las_paths=well_las_paths,
        tops=tops,
        zone_definitions=zone_definitions,
        strat_standard=strat_standard,
        paleoenvironment_input=paleoenvironment_input,
        checkshot_ref=checkshot_ref,
        wavelet_mode=wavelet_mode,
        wavelet_freq_hz=wavelet_freq_hz,
        phase_degrees=phase_degrees,
        polarity=polarity,
        synthetics_output=synthetics_output,
    )
