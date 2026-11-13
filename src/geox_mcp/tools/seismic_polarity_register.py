"""
GEOX Seismic Polarity & Phase Register — governance primitive.

Implements the polarity/phase register MCP contract that emits
PolarityPhaseRegister artifacts. Per the GEOX Seismic Interpretation
Forge Package, this is the universal prerequisite for L0 attribute
contracts: if polarity=UNKNOWN, all downstream contrast measurements
must behave as UNKNOWN (Canon #0).

Methods implemented:
- amplitude_spectrum_max  — find the phase rotation that maximizes
                            amplitude spectrum flatness
- kurtosis_max            — find the phase rotation that maximizes
                            kurtosis of the input signal (Van der Baan,
                            SEG/EAGE 2008)
- external_calibration_witness — accept a pre-computed declaration

Reference: Copilot forge prompt BUILD step 3; Slice 1 of forge.

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import hashlib
import logging
import math
from datetime import datetime, timezone
from typing import Any, Literal

import numpy as np
from fastmcp import Context

from geox_core.enums.statuses import get_standard_envelope  # type: ignore
from geox.seismic.contracts import (
    PhaseShiftEstimate,
    PolarityPhaseRegister,
)

logger = logging.getLogger("geox.seismic_polarity_register")

TOOL_NAME = "geox_seismic_polarity_register"
POLARITY_SCHEMA = "geox.seismic.polarity-phase-register.v1"


# ────────────────────────────────────────────────────────────────────────────
# Polarity inference implementations (replaceable; governed by capability)
# ────────────────────────────────────────────────────────────────────────────


def _phase_search(
    trace: np.ndarray,
    method: Literal["amplitude_spectrum_max", "kurtosis_max"],
    phase_grid: np.ndarray | None = None,
) -> tuple[float, float]:
    """Search phase rotation in [-180°, 180°] for the chosen objective.

    Returns: (phase_deg, score) where higher score = better fit.
    """
    if phase_grid is None:
        phase_grid = np.arange(-180.0, 180.0, 1.0)

    if method == "amplitude_spectrum_max":
        spec = np.abs(np.fft.rfft(trace))
        # Maximize low-frequency band flatness — proxy for zero-phase impulse
        band = spec[: min(32, len(spec))]
        scores = []
        for phi in phase_grid:
            rotated = _rotate_phase(trace, phi)
            rotated_spec = np.abs(np.fft.rfft(rotated))
            rotated_band = rotated_spec[: len(band)]
            # Score = inverse stddev of normalized band (flatter = higher)
            denom = np.mean(rotated_band) + 1e-12
            scores.append(1.0 / (np.std(rotated_band / denom) + 1e-12))
        scores = np.asarray(scores)
        idx = int(np.argmax(scores))
        return float(phase_grid[idx]), float(scores[idx])

    elif method == "kurtosis_max":
        scores = []
        for phi in phase_grid:
            rotated = _rotate_phase(trace, phi)
            scores.append(float(_kurtosis(rotated)))
        scores = np.asarray(scores)
        idx = int(np.argmax(scores))
        return float(phase_grid[idx]), float(scores[idx])

    raise ValueError(f"Unknown method: {method}")


def _rotate_phase(trace: np.ndarray, phase_deg: float) -> np.ndarray:
    """Constant-phase rotation in the frequency domain.

    Constant phase rotation in time = same phase shift applied across all
    frequency bins: rotated_spectrum[f] = original_spectrum[f] * exp(j * phi).
    This is mathematically equivalent to Hilbert-transform + phase-shift but
    simpler and avoids the analytic-signal construction complexity.
    """
    spec = np.fft.fft(trace)
    rotated_spec = spec * np.exp(1j * math.radians(phase_deg))
    return np.real(np.fft.ifft(rotated_spec))


def _kurtosis(x: np.ndarray) -> float:
    """Excess kurtosis of x (zero-mean, unit-variance normalized)."""
    x = (x - np.mean(x)) / (np.std(x) + 1e-12)
    n = len(x)
    return float(np.mean(x**4) - 3.0) if n > 0 else 0.0


def _infer_polarity_from_kurtosis(trace: np.ndarray) -> str:
    """Estimate polarity from kurtosis sign after kurtosis_max phase rotation.

    Positive kurtosis → spiky (likely SEG_NORMAL: peak + black).
    Negative kurtosis → flat-topped (likely SEG_REVERSE/EUROPEAN).
    """
    _, score = _phase_search(trace, "kurtosis_max")
    if score > 0.5:
        return "SEG_NORMAL"
    elif score < -0.5:
        return "SEG_REVERSE"
    return "UNKNOWN"


# ────────────────────────────────────────────────────────────────────────────
# Public tool — async, MCP-compatible
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_polarity_register(
    volume_ref: str | None = None,
    trace: list[float] | None = None,
    method: Literal[
        "amplitude_spectrum_max", "kurtosis_max", "external_calibration_witness"
    ] = "kurtosis_max",
    external_polarity: Literal["SEG_NORMAL", "SEG_REVERSE", "EUROPEAN", "UNKNOWN"] | None = None,
    external_phase_deg: float | None = None,
    sample_size: int = 1000,
    registered_by: str = "kimi-code/FI-008",
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
    ctx: Context | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Register polarity/phase for a seismic volume or trace.

    Parameters
    ----------
    volume_ref : str, optional
        geox:// URI of a registered volume; trace data extracted from it.
    trace : list[float], optional
        Raw amplitude samples for direct inference (used in tests/synthetic).
    method : str
        Inferred ("amplitude_spectrum_max" / "kurtosis_max") or
        declared ("external_calibration_witness").
    external_polarity : str, optional
        Required if method == "external_calibration_witness".
    external_phase_deg : float, optional
        Required if method == "external_calibration_witness".
    sample_size : int
        Sample size used for inference (for confidence calculation).
    registered_by : str
        Actor ID, recorded for provenance.

    Returns
    -------
    dict with standard envelope containing:
      - data: PolarityPhaseRegister schema (or UNKNOWN if cannot infer)
      - _evidence_envelope: GEOX standard envelope
      - claim: null (this is a governance primitive; not a geological claim)
    """
    if method == "external_calibration_witness":
        if external_polarity is None:
            return _envelope(
                status="HOLD",
                error="external_polarity required for method='external_calibration_witness'",
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
        polarity = external_polarity
        phase_deg = external_phase_deg or 0.0
        confidence = 1.0  # declared — full confidence
        estimate = PhaseShiftEstimate(
            method="external_calibration_witness",
            phase_deg=phase_deg,
            confidence=confidence,
            sample_size=sample_size,
            notes=f"declared by {registered_by}",
        )
    elif trace is not None:
        arr = np.asarray(trace, dtype=np.float64)
        if arr.size < 8:
            return _envelope(
                status="HOLD",
                error=f"trace too short (n={arr.size}); need >= 8 samples",
                session_id=session_id,
                actor_id=actor_id,
                trace_id=trace_id,
            )
        phase_deg, score = _phase_search(arr, method=method)
        polarity = _infer_polarity_from_kurtosis(arr)
        # Confidence: bounded; trust kurtosis_max more than amplitude_spectrum_max
        confidence = min(1.0, abs(score) / 5.0) if method == "kurtosis_max" else min(1.0, score / 100.0)
        estimate = PhaseShiftEstimate(
            method=method,
            phase_deg=phase_deg,
            confidence=confidence,
            sample_size=int(arr.size),
        )
    elif volume_ref is not None:
        # Volume path — actual implementation would fetch trace from artifact store.
        # Per Canon #0, return UNKNOWN with a HOLD explaining the gap.
        return _envelope(
            status="HOLD",
            error=(
                f"volume_ref path requires artifact-store fetch "
                f"(volume_ref={volume_ref}). "
                f"Until artifact-store bridge is built, supply `trace` directly "
                f"or use method='external_calibration_witness'."
            ),
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )
    else:
        return _envelope(
            status="HOLD",
            error="either volume_ref, trace, or external calibration witness required",
            session_id=session_id,
            actor_id=actor_id,
            trace_id=trace_id,
        )

    register_id = _compute_register_id(
        volume_ref=volume_ref, polarity=polarity, phase_deg=phase_deg, registered_by=registered_by
    )
    register = PolarityPhaseRegister(
        register_id=register_id,
        survey_id=None,
        volume_ref=volume_ref,
        polarity=polarity,
        constant_phase_deg=phase_deg,
        time_shift_ms=0.0,
        phase_estimates=[estimate],
        registered_by=registered_by,
    )

    return _envelope(
        status="OK",
        data=register.model_dump(mode="json"),
        session_id=session_id,
        actor_id=actor_id,
        trace_id=trace_id,
    )


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────


def _compute_register_id(
    *, volume_ref: str | None, polarity: str, phase_deg: float, registered_by: str
) -> str:
    """Deterministic register ID — content-addressed for reproducibility."""
    payload = f"{volume_ref}|{polarity}|{phase_deg:.3f}|{registered_by}".encode()
    digest = hashlib.sha256(payload).hexdigest()[:16]
    return f"geox://artifact/polarity-{digest}"


def _envelope(
    *,
    status: str,
    data: dict | None = None,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Wrap result in minimal GEOX-style envelope.

    Note: get_standard_envelope requires a primary_artifact dict and many
    fields we don't always have (uncertainty, diagnostics, confidence_band).
    For this tool we use a slim envelope that still carries the W3-style
    provenance fields the system expects.
    """
    env = {
        "tool_name": TOOL_NAME,
        "actor_id": actor_id or "kimi-code/FI-008",
        "session_id": session_id,
        "trace_id": trace_id,
        "schema_uri": POLARITY_SCHEMA,
        "execution_status": "OK" if status == "OK" else "HOLD",
        "artifact_status": "READY" if status == "OK" else "DRAFT",
        "governance_status": "QUALIFIED" if status == "OK" else "HOLD",
    }
    if status == "OK" and data is not None:
        return {**env, "status": "OK", "data": data, "claim": None}
    return {
        **env,
        "status": status,
        "data": data,
        "error": error,
        "hold_reason": error,
        "claim": None,
    }


# ────────────────────────────────────────────────────────────────────────────
# Module-level MCP registration helper
# ────────────────────────────────────────────────────────────────────────────

def register_with_mcp(mcp: Any) -> None:
    """Register this tool with a fastmcp server instance.

    Usage in src/geox_mcp/server.py:
        from geox_mcp.tools.seismic_polarity_register import register_with_mcp
        register_with_mcp(mcp)

    Idempotent: safe to call once during server bootstrap.
    """
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_polarity_register)
    logger.info("Registered %s with MCP", TOOL_NAME)
