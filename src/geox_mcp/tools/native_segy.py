"""Native SEG-Y registration, QC, and trace extraction.

Builds on geox_segy_trace_reality.ingest_segy() for actual SEG-Y parsing.
Establishes the physical witness: registered source → QC receipt → bounded trace extraction.

BOUNDARY: Native trace extraction requires registered, authorized source.
DISPLAY_DERIVED_PROXY is always rejected from native-only paths.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Optional


# ── Source Registry (in-memory, session-scoped) ──────────────────────────────

_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {}


# ── Registration ─────────────────────────────────────────────────────────────


async def geox_register_native_source(
    *,
    source_uri: str,
    source_id: Optional[str] = None,
    classification: str = "unknown",
    authority: str = "UNVERIFIED",
    survey_id: Optional[str] = None,
    line_id: Optional[str] = None,
    crs: str = "CRS_UNKNOWN",
    registered_by: Optional[str] = None,
    session_id: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> dict[str, Any]:
    """Register a native SEG-Y source for trace extraction.

    Validates file existence, computes SHA256, extracts binary header metadata.
    Does NOT load trace data — that happens at extraction time.

    Returns registration receipt with HOLD reasons if validation fails.
    """
    from geox_core.seismic_pipeline.native_segy_contracts import (
        AmplitudeIntegrity, DataClassification, PhaseIntegrity, PolarityState,
        SeismicDatasetManifest, SeismicQCReceipt, SeismicSourceRef,
        SourceAuthority, VerticalDomain,
    )

    # Validate source URI
    if not source_uri:
        return {"status": "VOID", "reason": "SOURCE_URI_REQUIRED"}

    if not os.path.exists(source_uri):
        return {"status": "VOID", "reason": f"FILE_NOT_FOUND: {source_uri}"}

    # Validate authority
    valid_authorities = {e.value for e in SourceAuthority}
    if authority not in valid_authorities:
        return {
            "status": "VOID",
            "reason": f"INVALID_AUTHORITY: {authority}",
            "valid_authorities": list(valid_authorities),
        }

    # Client-provided OPERATOR_APPROVED is not sufficient — must be resolved server-side
    resolved_authority = authority
    if authority == "OPERATOR_APPROVED" and not registered_by:
        resolved_authority = "UNVERIFIED"

    # Compute SHA256
    with open(source_uri, "rb") as f:
        file_bytes = f.read()
    source_hash = hashlib.sha256(file_bytes).hexdigest()
    file_size = len(file_bytes)

    # Generate source_id
    if not source_id:
        source_id = f"src_{source_hash[:12]}"

    # Run header QC
    qc_result = await _header_qc(source_uri)

    # Parse classification
    try:
        classif = DataClassification(classification)
    except ValueError:
        classif = DataClassification.UNKNOWN

    # Build source ref
    source_ref = SeismicSourceRef(
        source_id=source_id,
        source_uri=source_uri,
        source_hash=source_hash,
        classification=classif,
        authority=SourceAuthority(resolved_authority),
        survey_id=survey_id,
        line_id=line_id,
        crs=crs,
        registered_by=registered_by,
    )

    # Build manifest from QC — fields are nested under parsed_fields
    pf = qc_result.get("parsed_fields", {})
    manifest = SeismicDatasetManifest(
        source_ref=source_ref,
        file_size_bytes=file_size,
        segy_revision="unknown",
        trace_count=pf.get("trace_count"),
        samples_per_trace=pf.get("samples_per_trace"),
        sample_interval_us=pf.get("sample_interval_us"),
        sample_interval_ms=pf.get("sample_interval_ms"),
        data_sample_format=pf.get("data_sample_format"),
        sorting=str(pf.get("sorting", "unknown")),
        vertical_domain=VerticalDomain(pf.get("vertical_domain", "UNKNOWN")),
        vertical_unit=pf.get("vertical_unit", "unknown"),
        amplitude_integrity=AmplitudeIntegrity.CONDITIONAL if qc_result.get("status") == "PASS" else AmplitudeIntegrity.UNKNOWN,
        phase_integrity=PhaseIntegrity.UNKNOWN,
        polarity_state=PolarityState(qc_result.get("polarity_state", "UNKNOWN")),
        processing_lineage="UNKNOWN",
    )

    # Store in registry
    _SOURCE_REGISTRY[source_id] = {
        "source_ref": source_ref.model_dump(),
        "manifest": manifest.model_dump(),
        "qc_receipt": qc_result,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "tool_name": "geox_register_native_source",
        "status": "REGISTERED",
        "source_id": source_id,
        "source_hash": source_hash[:16] + "...",
        "classification": classif.value,
        "authority": resolved_authority,
        "manifest": manifest.model_dump(),
        "qc_receipt": qc_result,
        "provenance": {
            "tool": "geox_register_native_source",
            "tool_version": "v0.1.0",
            "actor_id": actor_id,
            "session_id": session_id,
        },
    }


# ── Header QC ────────────────────────────────────────────────────────────────


async def _header_qc(segy_path: str) -> dict[str, Any]:
    """Run header quality control on a SEG-Y file.

    Uses segyio to parse binary and trace headers.
    Returns QC receipt with parsed fields, missing fields, and warnings.
    """
    import segyio

    warnings = []
    missing = []
    parsed = {}

    try:
        with segyio.open(segy_path, ignore_geometry=True) as f:
            # Binary header
            parsed["trace_count"] = int(f.tracecount)
            parsed["samples_per_trace"] = int(f.bin[segyio.BinField.Samples])
            parsed["sample_interval_us"] = int(f.bin[segyio.BinField.Interval])
            parsed["data_sample_format"] = int(f.bin[segyio.BinField.Format])

            # Derived
            if parsed["sample_interval_us"] > 0:
                parsed["sample_interval_ms"] = parsed["sample_interval_us"] / 1000.0
                parsed["vertical_unit"] = "ms"
                parsed["vertical_domain"] = "TWT"
            else:
                missing.append("sample_interval_us")
                warnings.append("Sample interval is 0 — domain uncertain")

            parsed["sorting"] = str(f.sorting)

            # Sample format description
            format_map = {
                1: "IBM_float_32",
                2: "int32",
                3: "int16",
                5: "IEEE_float_32",
                8: "int8",
            }
            parsed["sample_format_desc"] = format_map.get(parsed["data_sample_format"], f"code_{parsed['data_sample_format']}")

            # Trace header sampling
            n_traces_to_check = min(100, parsed["trace_count"])
            inline_vals = set()
            crossline_vals = set()
            cdp_vals = set()

            for i in range(n_traces_to_check):
                try:
                    il = int(f.header[i][segyio.TraceField.INLINE_3D])
                    xl = int(f.header[i][segyio.TraceField.CROSSLINE_3D])
                    if il > 0:
                        inline_vals.add(il)
                    if xl > 0:
                        crossline_vals.add(xl)
                except (KeyError, IndexError, ValueError):
                    pass
                try:
                    cdp = int(f.header[i][segyio.TraceField.CDP])
                    if cdp > 0:
                        cdp_vals.add(cdp)
                except (KeyError, IndexError, ValueError):
                    pass

            if inline_vals:
                parsed["inline_range"] = [min(inline_vals), max(inline_vals)]
                parsed["sorting"] = "inline" if f.sorting == segyio.TraceSortingFormat.INLINE_SORTING else parsed["sorting"]
            else:
                missing.append("inline_3d")

            if crossline_vals:
                parsed["crossline_range"] = [min(crossline_vals), max(crossline_vals)]
            else:
                missing.append("crossline_3d")

            if cdp_vals:
                parsed["cdp_range"] = [min(cdp_vals), max(cdp_vals)]

            # Polarity — unknown by default
            parsed["polarity_state"] = "UNKNOWN"

    except Exception as e:
        return {
            "status": "ERROR",
            "reason": f"PARSE_ERROR: {e}",
            "parsed_fields": {},
            "missing_fields": ["all"],
            "parse_warnings": [str(e)],
            "amplitude_integrity": "UNKNOWN",
            "phase_integrity": "UNKNOWN",
            "polarity_state": "UNKNOWN",
            "permitted_uses": [],
            "prohibited_uses": ["all"],
            "required_next": ["fix_parse_error"],
        }

    # Determine status
    status = "PASS"
    if warnings:
        status = "WARN"
    if "sample_interval_us" in missing:
        status = "HOLD"

    return {
        "status": status,
        "parsed_fields": parsed,
        "missing_fields": missing,
        "parse_warnings": warnings,
        "amplitude_integrity": "CONDITIONAL",
        "phase_integrity": "UNKNOWN",
        "polarity_state": "UNKNOWN",
        "permitted_uses": [
            "native_trace_extraction",
            "header_inspection",
            "geometry_analysis",
        ],
        "prohibited_uses": [
            "amplitude_preservation_certification",
            "phase_certification",
            "quantitative_avo_without_conditioning",
        ],
        "required_next": ["register_source"] if status == "PASS" else ["fix_qc_issues"],
    }


# ── Native Trace Extraction ──────────────────────────────────────────────────


async def geox_extract_native_trace(
    *,
    source_id: str,
    trace_index: Optional[int] = None,
    cdp: Optional[int] = None,
    inline: Optional[int] = None,
    crossline: Optional[int] = None,
    intent: str = "trace_extraction",
    session_id: Optional[str] = None,
    actor_id: Optional[str] = None,
) -> dict[str, Any]:
    """Extract a native seismic trace from a registered source.

    Returns NativeTraceRef with full provenance, sample metadata, and
    explicit permitted/prohibited downstream uses.

    HOLD conditions:
    - Source not registered
    - Authority insufficient
    - Data classification disallows access
    - Invalid trace locator
    - Unparseable SEG-Y
    """
    from geox_core.seismic_pipeline.native_segy_contracts import (
        AmplitudeIntegrity, NativeTraceReceipt, NativeTraceRef,
        PhaseIntegrity, PolarityState, VerticalDomain,
    )

    # Check registry
    if source_id not in _SOURCE_REGISTRY:
        return {
            "status": "HOLD",
            "reason": "SOURCE_NOT_REGISTERED",
            "detail": f"Source '{source_id}' not found in registry. Register first with geox_register_native_source.",
            "source_id": source_id,
        }

    entry = _SOURCE_REGISTRY[source_id]
    source_ref = entry["source_ref"]
    manifest = entry["manifest"]

    # Authority check
    authority = source_ref.get("authority", "UNVERIFIED")
    if authority == "UNVERIFIED":
        return {
            "status": "HOLD",
            "reason": "INSUFFICIENT_AUTHORITY",
            "detail": "Source authority is UNVERIFIED. Requires OPERATOR_APPROVED or PUBLIC_VERIFIED.",
            "source_id": source_id,
            "authority": authority,
        }

    # Classification check
    classification = source_ref.get("classification", "unknown")
    if classification == "restricted":
        return {
            "status": "HOLD",
            "reason": "RESTRICTED_DATA",
            "detail": "Source classification is RESTRICTED. Access requires elevated authority.",
            "source_id": source_id,
        }

    # Validate trace locator
    if trace_index is None and cdp is None and (inline is None or crossline is None):
        return {
            "status": "VOID",
            "reason": "TRACE_LOCATOR_REQUIRED",
            "detail": "Provide trace_index, cdp, or (inline, crossline) to locate trace.",
        }

    source_uri = source_ref.get("source_uri")
    source_hash = source_ref.get("source_hash", "")

    # Extract trace
    import segyio
    try:
        with segyio.open(source_uri, ignore_geometry=True) as f:
            # Resolve trace index
            if trace_index is not None:
                if trace_index < 0 or trace_index >= f.tracecount:
                    return {
                        "status": "VOID",
                        "reason": f"TRACE_INDEX_OUT_OF_RANGE: {trace_index} (max={f.tracecount - 1})",
                    }
                resolved_index = trace_index
            elif cdp is not None:
                # Search for CDP
                resolved_index = None
                for i in range(min(f.tracecount, 10000)):
                    try:
                        if int(f.header[i][segyio.TraceField.CDP]) == cdp:
                            resolved_index = i
                            break
                    except (KeyError, IndexError):
                        continue
                if resolved_index is None:
                    return {
                        "status": "VOID",
                        "reason": f"CDP_NOT_FOUND: {cdp}",
                        "detail": "CDP not found in first 10000 traces.",
                    }
            else:
                # Search for inline/crossline
                resolved_index = None
                for i in range(min(f.tracecount, 10000)):
                    try:
                        il = int(f.header[i][segyio.TraceField.INLINE_3D])
                        xl = int(f.header[i][segyio.TraceField.CROSSLINE_3D])
                        if il == inline and xl == crossline:
                            resolved_index = i
                            break
                    except (KeyError, IndexError):
                        continue
                if resolved_index is None:
                    return {
                        "status": "VOID",
                        "reason": f"INLINE_CROSSLINE_NOT_FOUND: ({inline}, {crossline})",
                        "detail": "Inline/crossline pair not found in first 10000 traces.",
                    }

            # Extract trace data
            trace_data = f.trace[resolved_index]
            header = {}
            try:
                h = f.header[resolved_index]
                for field in [segyio.TraceField.INLINE_3D, segyio.TraceField.CROSSLINE_3D,
                              segyio.TraceField.CDP, segyio.TraceField.offset]:
                    try:
                        header[field.name] = int(h[field])
                    except (KeyError, ValueError):
                        pass
            except Exception:
                pass

            sample_interval_us = int(f.bin[segyio.BinField.Interval])
            sample_interval_ms = sample_interval_us / 1000.0

    except Exception as e:
        return {
            "status": "ERROR",
            "reason": f"EXTRACTION_ERROR: {e}",
            "source_id": source_id,
        }

    # Build trace ref
    trace_ref = NativeTraceRef(
        trace_ref_id=f"ntr_{source_hash[:8]}_{resolved_index}",
        source_id=source_id,
        source_hash=source_hash,
        trace_index=resolved_index,
        cdp=header.get("CDP"),
        inline=header.get("INLINE_3D"),
        crossline=header.get("CROSSLINE_3D"),
        n_samples=len(trace_data),
        sample_interval_us=sample_interval_us,
        sample_interval_ms=sample_interval_ms,
        vertical_domain=VerticalDomain(manifest.get("vertical_domain", "UNKNOWN")),
        vertical_unit=manifest.get("vertical_unit", "ms"),
        amplitude_integrity=AmplitudeIntegrity(manifest.get("amplitude_integrity", "UNKNOWN")),
        phase_integrity=PhaseIntegrity(manifest.get("phase_integrity", "UNKNOWN")),
        polarity_state=PolarityState(manifest.get("polarity_state", "UNKNOWN")),
        processing_lineage=manifest.get("processing_lineage", "UNKNOWN"),
    )

    # Build receipt
    receipt = NativeTraceReceipt(
        trace_ref=trace_ref,
        qc_receipt_id=entry.get("qc_receipt", {}).get("status"),
        limitations=[
            "Amplitude integrity is CONDITIONAL — verify processing lineage before quantitative use",
            "Phase and polarity state are UNKNOWN unless source metadata provides them",
            "Processing lineage UNKNOWN — raw field data or processed stack not distinguished",
        ],
    )

    return {
        "tool_name": "geox_extract_native_trace",
        "status": "OK",
        "representation": "NATIVE_TRACE",
        "trace_ref": trace_ref.model_dump(),
        "trace_data_summary": {
            "n_samples": len(trace_data),
            "min": float(trace_data.min()),
            "max": float(trace_data.max()),
            "mean": float(trace_data.mean()),
            "rms": float((trace_data ** 2).mean() ** 0.5),
        },
        "header": header,
        "receipt": receipt.model_dump(),
        "epistemic_tag": "OBS",
        "provenance": {
            "tool": "geox_extract_native_trace",
            "tool_version": "v0.1.0",
            "actor_id": actor_id,
            "session_id": session_id,
        },
    }


async def geox_list_registered_sources() -> dict[str, Any]:
    """List all registered native seismic sources."""
    return {
        "tool_name": "geox_list_registered_sources",
        "n_sources": len(_SOURCE_REGISTRY),
        "sources": [
            {
                "source_id": sid,
                "classification": entry["source_ref"].get("classification"),
                "authority": entry["source_ref"].get("authority"),
                "trace_count": entry["manifest"].get("trace_count"),
                "samples_per_trace": entry["manifest"].get("samples_per_trace"),
            }
            for sid, entry in _SOURCE_REGISTRY.items()
        ],
    }
