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
            volume_ref=volume_ref, output_path=output_path,
            sample_interval_ms=sample_interval_ms,
            textual_header=textual_header, overwrite=overwrite, provenance=provenance,
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
        from geox_mcp.tools.data import geox_data_ingest_bundle as _impl
        return await _impl(source_uri=source_uri, source_type=source_type, well_id=well_id)

    return {"status": "INVALID", "errors": ["Provide segy_metadata, seismic_metadata, or source_uri"]}
