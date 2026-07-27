"""
geox_seismic_ingest — Seismic Data I/O (Phase 2)
═════════════════════════════════════════════════
Absorbs: geox_segy_export_tool, seismic mode of geox_data_ingest_bundle

Modes: inspect_segy, export_segy, inspect_seismic_meta

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any, Literal


async def geox_seismic_ingest(
    mode: Literal["inspect_segy", "export_segy", "inspect_seismic_meta"] = "inspect_segy",
    # SEG-Y params
    volume_ref: str | None = None,
    output_path: str | None = None,
    sample_interval_ms: float = 4,
    textual_header: str = "",
    overwrite: bool = False,
    provenance: str = "fixture",
    segy_metadata: dict[str, Any] | None = None,
    seismic_metadata: dict[str, Any] | None = None,
    # ingest params
    source_uri: str | None = None,
    source_type: str = "seismic",
    well_id: str | None = None,
) -> dict[str, Any]:
    """Seismic data ingest and export.

    Modes:
      inspect_segy         - Inspect SEG-Y binary/text headers
      export_segy          - Export seismic volume to SEG-Y format
      inspect_seismic_meta - Inspect seismic volume metadata
    """
    if mode == "export_segy":
        if not volume_ref or not output_path:
            return {"status": "INVALID", "errors": ["volume_ref and output_path required for export_segy"]}
        from geox_mcp.tools.paleoscan_forge import geox_segy_export_tool as _impl

        return await _impl(
            volume_ref=volume_ref,
            output_path=output_path,
            sample_interval_ms=sample_interval_ms,
            textual_header=textual_header,
            overwrite=overwrite,
            provenance=provenance,
        )

    if mode == "inspect_seismic_meta":
        if not seismic_metadata:
            return {"status": "INVALID", "errors": ["seismic_metadata required for inspect_seismic_meta"]}
        from geox_mcp.tools.ingestion import geox_seismic_inspect as _impl

        return await _impl(seismic_metadata=seismic_metadata)

    # Default: inspect_segy
    if segy_metadata:
        from geox_mcp.tools.ingestion import geox_seismic_segy_inspect as _impl

        return await _impl(segy_metadata=segy_metadata)

    if source_uri:
        # ── FORGED 2026-07-27 (FI-008 · GEOX dispatch fix) ──
        # When source_uri is provided AND source_type is seismic/segy, the
        # previous behavior routed through geox_data_ingest_bundle which
        # tried to parse SEG-Y as LAS — a clear dispatch bug. Now: read
        # the SEG-Y header with segyio (if available) and route to the
        # proper SEG-Y inspector. Falls back to bundle only for non-seismic
        # types or when segyio is unavailable.
        is_seismic_type = (source_type or "").lower() in ("seismic", "segy", "auto")
        segy_ext = source_uri.lower().endswith((".segy", ".sgy"))
        if is_seismic_type and segy_ext:
            try:
                import os as _os
                import segyio as _segyio
                import numpy as _np
                # Allow file:// prefix; materialize to local path
                local = source_uri.removeprefix("file://")
                if not _os.path.exists(local):
                    return {
                        "status": "INVALID",
                        "errors": [f"SEG-Y file not found at {local}; copy to /data or /app/fixtures for server access."],
                    }
                with _segyio.open(local, "r", strict=False, ignore_geometry=True) as _f:
                    _n_traces = int(_f.tracecount)
                    _n_samples = int(_f.samples.size)
                    _si_us = int(_f.bin[_segyio.BinField.Interval]) if hasattr(_f, "bin") else 4000
                    _fmt = int(_f.bin[_segyio.BinField.Format]) if hasattr(_f, "bin") else 1
                    # Sample first 200 traces for amplitude stats
                    _samp_traces = []
                    for _ti in range(min(_n_traces, 200)):
                        _tr = _f.trace[_ti]
                        if _np.max(_np.abs(_tr)) > 0:
                            _samp_traces.append(_tr)
                    if _samp_traces:
                        _all = _np.concatenate(_samp_traces)
                        _amp_min, _amp_max, _amp_mean, _amp_std = (
                            float(_all.min()),
                            float(_all.max()),
                            float(_all.mean()),
                            float(_all.std()),
                        )
                    else:
                        _amp_min = _amp_max = _amp_mean = _amp_std = 0.0
                    # Map raw format int → schema enum
                    _fmt_map = {0: "UNKNOWN", 1: "IBM_FLOAT", 2: "INT32", 3: "INT16",
                                 4: "IEEE_FLOAT", 5: "IEEE_DOUBLE", 6: "INT24", 7: "INT64", 8: "INT8"}
                    _fmt_enum = {"IBM_FLOAT": "SEG_Y_REV1", "INT32": "SEG_Y_REV1",
                                  "IEEE_FLOAT": "SEG_Y_REV2", "IEEE_DOUBLE": "SEG_Y_REV2",
                                  "INT16": "SEG_Y_REV1", "INT24": "SEG_Y_REV1"}.get(
                                  _fmt_map.get(_fmt, ""), "SEG_Y_REV1")
                    _md = {
                        "filename": _os.path.basename(local),
                        "format": _fmt_enum,
                        "encoding": _fmt_map.get(_fmt, "UNKNOWN"),
                        "trace_count": _n_traces,
                        "sample_count": _n_samples,
                        "sample_interval_ms": _si_us / 1000.0,
                        "coordinate_units": "length_meters",
                        "sample_format": f"{_fmt_map.get(_fmt, 'UNKNOWN')} 4-byte",
                        "file_size_bytes": _os.path.getsize(local),
                        "file_path": local,
                        "file_hash_sha256": _os.popen(f"sha256sum {local} 2>/dev/null | head -c 64").read().strip() or None,
                        "amplitude_min": _amp_min,
                        "amplitude_max": _amp_max,
                        "amplitude_mean": _amp_mean,
                        "amplitude_std": _amp_std,
                        "nonzero_sampled_traces": len(_samp_traces),
                        "inline_start": 1, "inline_end": 1,
                        "crossline_start": 1, "crossline_end": _n_traces,
                        "coordinate_system": "EPSG:4326",
                    }
                from geox_mcp.tools.ingestion import geox_seismic_segy_inspect as _impl
                return await _impl(segy_metadata=_md)
            except ImportError:
                # segyio not available — fall through to bundle
                pass
            except Exception as _exc:
                return {
                    "status": "INVALID",
                    "errors": [f"SEG-Y inspection failed: {type(_exc).__name__}: {_exc}"],
                }
        from geox_mcp.tools.data import geox_data_ingest_bundle as _impl

        return await _impl(source_uri=source_uri, source_type=source_type, well_id=well_id)

    return {"status": "INVALID", "errors": ["Provide segy_metadata, seismic_metadata, or source_uri"]}
