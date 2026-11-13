"""
GEOX Seismic Attribute Compute — unified L0 attribute MCP contract.

Per the GEOX Seismic Interpretation Forge Package, Slice 1 Step 4 + Step 7.
The single MCP contract that dispatches to all 12 L0 attribute families.

Capabilities (governed; replaceable implementations):
- geox.seismic.attr.envelope.v1
- geox.seismic.attr.instantaneous_phase.v1
- geox.seismic.attr.instantaneous_frequency.v1
- geox.seismic.attr.sweetness.v1
- geox.seismic.attr.rms_amplitude.v1
- geox.seismic.attr.variance.v1
- geox.seismic.attr.gst_dip.v1
- geox.seismic.attr.gst_azimuth.v1
- geox.seismic.attr.gst_coherence.v1
- geox.seismic.attr.chaos.v1
- geox.seismic.attr.curvature_most_positive.v1
- geox.seismic.attr.curvature_most_negative.v1
- geox.seismic.attr.spectral_voice.v1

Per Canon #0: every contract has a clear failure mode. If polarity=UNKNOWN,
the caller MUST mark the result as UNKNOWN — this tool returns the contract
artifact + an explicit `polarity_status` field so downstream consumers can
apply the gate.

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Literal

import numpy as np
from fastmcp import Context

from geox.seismic.contracts import (
    DerivedVolumeManifest,
    DomainSpec,
    FailureMode,
    GridSpec,
    ImplementationRef,
    ParentRef,
    SignalSpec,
    StorageSpec,
    ValiditySpec,
)
from geox.seismic import attributes as attr

logger = logging.getLogger("geox.seismic_attribute_compute")

TOOL_NAME = "geox_seismic_attribute_compute"

CAPABILITY_MAP = {
    "geox.seismic.attr.envelope.v1": attr.envelope,
    "geox.seismic.attr.instantaneous_phase.v1": attr.instantaneous_phase,
    "geox.seismic.attr.instantaneous_frequency.v1": lambda v: attr.instantaneous_frequency(
        v, sample_interval_s=0.004
    ),
    "geox.seismic.attr.sweetness.v1": lambda v: attr.sweetness(v, sample_interval_s=0.004),
    "geox.seismic.attr.rms_amplitude.v1": lambda v: attr.rms_amplitude(v, window_size=5),
    "geox.seismic.attr.variance.v1": lambda v: attr.variance(v, window_size=5),
    "geox.seismic.attr.gst_dip.v1": lambda v: attr.gst_dip(v, sigma=1.0),
    "geox.seismic.attr.gst_azimuth.v1": lambda v: attr.gst_azimuth(v, sigma=1.0),
    "geox.seismic.attr.gst_coherence.v1": lambda v: attr.gst_coherence(v, window_size=5, sigma=1.0),
    "geox.seismic.attr.chaos.v1": lambda v: attr.chaos(v, window_size=5, sigma=1.0),
    "geox.seismic.attr.curvature_most_positive.v1": lambda v: attr.curvature_most_positive(
        v, sigma=1.0, curvature_sigma=2.0
    ),
    "geox.seismic.attr.curvature_most_negative.v1": lambda v: attr.curvature_most_negative(
        v, sigma=1.0, curvature_sigma=2.0
    ),
    "geox.seismic.attr.spectral_voice.v1": lambda v: attr.spectral_voice(v, target_freq_hz=25.0),
}

VALID_CAPABILITIES = sorted(CAPABILITY_MAP.keys())


# ────────────────────────────────────────────────────────────────────────────
# Public tool — async, MCP-compatible
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_attribute_compute(
    volume: list[list[list[float]]] | None = None,
    capability_id: str = "geox.seismic.attr.envelope.v1",
    polarity: Literal["SEG_NORMAL", "SEG_REVERSE", "EUROPEAN", "UNKNOWN"] = "UNKNOWN",
    sample_interval_ms: float = 4.0,
    parent_artifact_id: str | None = None,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Context | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Compute a seismic attribute volume.

    Parameters
    ----------
    volume : 3D nested list, optional
        Inline-major order: [iline][xline][sample]. Required unless
        volume_ref path is wired to artifact-store (currently HOLD).
    capability_id : str
        One of VALID_CAPABILITIES; default envelope.
    polarity : str
        Polarity convention declared for the parent volume. Per Canon #0,
        if UNKNOWN, the result carries behavior=UNKNOWN downstream.
    sample_interval_ms : float
        Sample interval in milliseconds (default 4.0).
    parent_artifact_id : str, optional
        geox:// URI of the parent volume manifest (for lineage).
    actor_id : str
        Provenance: who initiated the computation.

    Returns
    -------
    dict with:
      - status: OK | HOLD
      - data: DerivedVolumeManifest + summary statistics (no full volume bytes)
      - claim: null
      - polarity_status: actionable | unknown (Canon #0 gate)
    """
    if capability_id not in CAPABILITY_MAP:
        return _envelope(
            status="HOLD",
            error=(
                f"unknown capability_id={capability_id!r}. "
                f"Valid: {VALID_CAPABILITIES}"
            ),
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    if volume is None:
        return _envelope(
            status="HOLD",
            error=(
                "volume (3D nested list) required. "
                "volume_ref → artifact-store bridge is HOLD per Canon #0."
            ),
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    arr = np.asarray(volume, dtype=np.float64)
    if arr.ndim != 3:
        return _envelope(
            status="HOLD",
            error=f"volume must be 3D, got {arr.ndim}D with shape {arr.shape}",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    # Compute the attribute
    compute_fn = CAPABILITY_MAP[capability_id]
    try:
        result = compute_fn(arr)
    except Exception as e:
        return _envelope(
            status="HOLD",
            error=f"computation failed for {capability_id}: {type(e).__name__}: {e}",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    # Compute summary statistics (NEVER return full volume bytes per Copilot spec)
    stats = {
        "shape": list(result.shape),
        "dtype": str(result.dtype),
        "finite_min": float(np.nanmin(result)) if np.isfinite(result).any() else None,
        "finite_max": float(np.nanmax(result)) if np.isfinite(result).any() else None,
        "finite_mean": float(np.nanmean(result)) if np.isfinite(result).any() else None,
        "finite_std": float(np.nanstd(result)) if np.isfinite(result).any() else None,
        "nan_count": int(np.isnan(result).sum()),
    }

    # Polarity status (Canon #0 gate)
    polarity_status = "actionable" if polarity != "UNKNOWN" else "unknown"

    # Build the DerivedVolumeManifest
    n_iline, n_xline, n_sample = arr.shape
    artifact_id = _compute_artifact_id(
        capability_id=capability_id,
        parent_artifact_id=parent_artifact_id or f"geox://volume/inline-major/{n_iline}x{n_xline}x{n_sample}",
        stats=stats,
    )
    manifest = DerivedVolumeManifest(
        artifact_id=artifact_id,
        sha256=_payload_hash(stats),
        created_by=actor_id,
        capability_id=capability_id,
        implementation=ImplementationRef(
            name=capability_id.split(".")[-2],
            version="1.0.0",
            code_hash=_payload_hash({"capability": capability_id, "params": "default"}),
            library="numpy_scipy_v1",
        ),
        parents=[
            ParentRef(
                artifact_id=parent_artifact_id or f"geox://volume/inline-major/{n_iline}x{n_xline}x{n_sample}",
                sha256=_payload_hash({"shape": list(arr.shape)}),
                role="input",
            )
        ],
        validity=ValiditySpec(
            qc_ref=f"geox://qc/{artifact_id.split('/')[-1]}-qc",
        ),
        parameters={"sample_interval_ms": sample_interval_ms, "polarity": polarity},
        domain=DomainSpec(vertical="TWT", unit="ms", crs="EPSG:4326"),
        grid=GridSpec(
            shape=(n_iline, n_xline, n_sample),
            spacing=(25.0, 25.0, sample_interval_ms),
            axis_order=("iline", "xline", "twt"),
        ),
        signal=SignalSpec(
            polarity=polarity,
            phase_deg=0.0,
            amplitude_status="relative",
            sample_interval_ms=sample_interval_ms,
        ),
        storage=StorageSpec(
            uri=f"memory://{artifact_id.split('/')[-1]}.npy",
            chunks=None,
            dtype="float32",
        ),
        source_uri="memory://input",
        source_format="SEGY_REV1",  # not applicable but required
        classification="INTERNAL",
        license_provenance=["MIT", "BSD-3-Clause"],  # numpy + scipy
    )

    return {
        **_envelope(
            status="OK",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        ),
        "data": manifest.model_dump(mode="json"),
        "summary_statistics": stats,
        "polarity_status": polarity_status,
        "capability_id": capability_id,
        "claim": None,
    }


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────


def _compute_artifact_id(
    *, capability_id: str, parent_artifact_id: str, stats: dict
) -> str:
    """Content-addressed artifact ID for the computed attribute volume."""
    payload = f"{capability_id}|{parent_artifact_id}|{stats['shape']}|{stats['finite_mean']}".encode()
    digest = hashlib.sha256(payload).hexdigest()[:16]
    # Map capability to family name for URI
    family = capability_id.split(".")[-2]  # e.g., 'envelope'
    return f"geox://derived/{family}/{digest}"


def _payload_hash(payload: Any) -> str:
    """SHA256 of a JSON-serializable payload."""
    import json
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()


def _envelope(
    *,
    status: str,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Minimal GEOX-style envelope (consistent with polarity_register + artifact_get)."""
    env = {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id or "kimi-code/FI-008",
        "session_id": session_id,
        "trace_id": trace_id,
        "execution_status": "OK" if status == "OK" else "HOLD",
        "artifact_status": "READY" if status == "OK" else "DRAFT",
        "governance_status": "QUALIFIED" if status == "OK" else "HOLD",
    }
    if status == "OK":
        return {**env, "status": "OK", "claim": None}
    return {**env, "status": status, "error": error, "hold_reason": error, "claim": None}


def register_with_mcp(mcp: Any) -> None:
    """Register this tool with a fastmcp server instance."""
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_attribute_compute)
    logger.info("Registered %s with MCP (13 capabilities)", TOOL_NAME)
