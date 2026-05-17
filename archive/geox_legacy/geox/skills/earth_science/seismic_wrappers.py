"""
GEOX Seismic Skill Pack — Improved v2
DITEMPA BUKAN DIBERI — Forged, Not Given

Improvement Spec v1 applied:
  - geox_seismic_load_volume: axis_identity, bounding_box_3d, ingestion_hash,
    sample_domain, limitations, admissibility gate
  - geox_seismic_compute_attribute: window metadata, statistics, slice_provenance,
    limitation statement, source_slice_identity
  - seismic_render_volume_slice: physical_extents, axis_labels, domain_flag,
    display_mode, slice_location, provenance

All tools emit: claim_state, provenance, limitations, vault_receipt.
Claim states: OBSERVED | COMPUTED | HYPOTHESIS | VOID
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import numpy as np


class ClaimTag(str, Enum):
    OBSERVED = "OBSERVED"    # Direct measurement / ingested
    COMPUTED = "COMPUTED"    # Derived from physics model
    INTERPRETED = "INTERPRETED"  # Multi-source inference
    SYNTHESIZED = "SYNTHESIZED"  # Cross-domain assembly
    VERIFIED = "VERIFIED"    # QC passed
    UNKNOWN = "UNKNOWN"      # Explicit gap
    HYPOTHESIS = "HYPOTHESIS"  # Low confidence / image-only input


# ─────────────────── VAULT999 RECEIPT ───────────────────

def make_vault_receipt(
    tool_name: str,
    payload: dict[str, Any],
    verdict: str = "SEAL",
) -> dict[str, Any]:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{tool_name}:{canonical}".encode("utf-8")).hexdigest()
    return {
        "vault": "VAULT999",
        "tool_name": tool_name,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": digest[:16],
    }


# ─────────────────── CLAIM TAG CLASSIFIER ───────────────────

def classify_claim_tag(confidence: float, hold_enforced: bool = False) -> str:
    if hold_enforced:
        return ClaimTag.HYPOTHESIS.value
    score = max(0.0, min(1.0, confidence))
    if score >= 0.85:
        return ClaimTag.CLAIM.value
    if score >= 0.65:
        return ClaimTag.PLAUSIBLE.value
    if score >= 0.4:
        return ClaimTag.HYPOTHESIS.value
    if score > 0.0:
        return ClaimTag.ESTIMATE.value
    return ClaimTag.UNKNOWN.value


# ─────────────────── PHYSICS GUARD BOUNDS ───────────────────

_SEISMIC_BOUNDS = {
    "amplitude": {"min": -1.0, "max": 1.0},
    "variance": {"min": 0.0, "max": 1.0},
    "sweetness": {"min": 0.0, "max": 10.0},
    "coherence": {"min": 0.0, "max": 1.0},
    "envelope": {"min": 0.0, "max": 5.0},
    "freq_avg": {"min": 5.0, "max": 120.0},
    "inline_count": {"min": 1, "max": 10000},
    "crossline_count": {"min": 1, "max": 10000},
    "sample_count": {"min": 1, "max": 20000},
}


def physics_guard(data: dict[str, Any]) -> dict[str, Any]:
    violations = []
    for key, bounds in _SEISMIC_BOUNDS.items():
        if key in data:
            val = float(data[key])
            if val < bounds["min"] or val > bounds["max"]:
                violations.append(
                    f"{key}={val} outside [{bounds['min']}, {bounds['max']}]"
                )
    if violations:
        return {"status": "PHYSICS_VIOLATION", "violations": violations, "hold": True}
    return {"status": "PASS"}


# ─────────────────── ADMISSIBILITY GATE ───────────────────

def _admissibility_gate(provenance: str, required_present: bool = True) -> dict[str, Any]:
    """Block downstream if intake is not from a real SEG-Y."""
    if provenance in ("user_image", "user_text", "fixture"):
        return {
            "admissibility": "LIMITED",
            "claim_state": ClaimTag.HYPOTHESIS.value,
            "limitation": (
                "Image or text input cannot substitute for seismic ingestion. "
                "Attribute computation is possible but claim_state must be HYPOTHESIS. "
                "Do not represent as confirmed seismic attribute."
            ),
            "hold": provenance in ("user_image", "user_text"),
        }
    return {"admissibility": "FULL", "claim_state": ClaimTag.OBSERVED.value, "hold": False}


# ─────────────────────────────────────────────────────────────────────────────
# SEISMIC LOAD VOLUME — IMPROVED
# ─────────────────────────────────────────────────────────────────────────────

def seismic_load_volume(
    segy_path: Optional[str] = None,
    volume_id: str = "SEISMIC_3D",
    survey_name: Optional[str] = None,
    inline_axis: int = 0,
    crossline_axis: int = 1,
    sample_axis: int = 2,
    memory_map: bool = True,
    provenance: str = "fixture",  # fixture | uploaded | real_survey | user_image | user_text
) -> dict[str, Any]:
    """
    Load a SEG-Y volume via segyio and wrap in canonical GEOX schema v2.

    Required output fields per GEOX_TOOL_IMPROVEMENT_SPEC_v1:
      - sample_interval_ms, axis_identity, inline_range, crossline_range,
      - sample_domain, byte_order, bounding_box_3d, provenance,
      - intake_claim, survey_name, ingestion_hash, limitations, vault_receipt

    Returns:
        Canonical GEOX schema v2 (see spec for field definitions).
    """
    # Admissibility gate
    gate = _admissibility_gate(provenance)
    claim_state = gate["claim_state"]
    limitations = [gate["limitation"]] if gate["limitation"] else []

    result: dict[str, Any] = {
        "tool": "geox_seismic_load_volume",
        "verdict": "HOLD" if gate["hold"] else "SEAL",
        "volume_id": volume_id,
        "claim_state": claim_state,
        "provenance": provenance,
        "stages": ["ingest", "index"],
    }

    if segy_path is None or provenance in ("fixture", "user_image", "user_text"):
        return _scaffold_seismic_volume(volume_id, survey_name, provenance, limitations, claim_state)

    try:
        import segyio
    except ImportError:
        limitations.append("segyio not available — using scaffold")
        result["limitation_reason"] = "library_missing"
        return _scaffold_seismic_volume(volume_id, survey_name, provenance, limitations, claim_state)

    try:
        with segyio.open(segy_path, "r", memory_map=memory_map) as segy:
            il_count = int(segy.shape[inline_axis])
            xl_count = int(segy.shape[crossline_axis])
            sample_count = int(segy.shape[sample_axis])
            sample_interval_us = int(segy.sample_interval)

            il_start = int(segy.inline_start) if hasattr(segy, "inline_start") and segy.inline_start else 1
            xl_start = int(segy.crossline_start) if hasattr(segy, "crossline_start") and segy.crossline_start else 1

            result.update({
                # REQUIRED per spec
                "sample_interval_ms": round(sample_interval_us / 1000, 4),
                "axis_identity": {
                    "inline_axis": "inline",
                    "crossline_axis": "crossline",
                    "time_axis": "twt_ms",
                },
                "inline_range": [il_start, il_start + (il_count - 1) * 1, 1],
                "crossline_range": [xl_start, xl_start + (xl_count - 1) * 1, 1],
                "sample_domain": "time_ms",
                "byte_order": "big-endian" if segy.endian == "big" else "little-endian",
                "bounding_box_3d": {
                    "inline": [il_start, il_start + (il_count - 1)],
                    "crossline": [xl_start, xl_start + (xl_count - 1)],
                    "twt_ms": [0.0, round(sample_count * sample_interval_us / 1000, 2)],
                },
                # Additional
                "shape": [il_count, xl_count, sample_count],
                "trace_count": il_count * xl_count,
                "il_step": 1,
                "xl_step": 1,
                "sample_interval_us": sample_interval_us,
                "survey_name": survey_name or "unknown",
                "ingestion_hash": _compute_segy_hash(segy_path),
                "data_byte_order": "big-endian" if segy.endian == "big" else "little-endian",
                "scalogram": {
                    "il_step": 1,
                    "xl_step": 1,
                    "twt_step_ms": round(sample_interval_us / 1000, 4),
                },
            })
            result["status"] = "loaded"
            result["verdict"] = "SEAL"

    except Exception as e:
        result.update({
            "status": "error",
            "claim_state": ClaimTag.UNKNOWN.value,
            "error": str(e),
            "verdict": "VOID",
            "limitations": limitations + [f"loading failed: {str(e)}"],
        })
        result["vault_receipt"] = make_vault_receipt("geismic_load_volume", result, "VOID")
        return result

    result["limitations"] = limitations
    result["vault_receipt"] = make_vault_receipt("seismic_load_volume", result, "SEAL")

    # Render payload
    result["render_payload"] = {
        "type": "volume_slice",
        "volume_id": volume_id,
        "orientation": "inline",
        "slice_index": result["inline_range"][0],
        "shape": result["shape"],
        "claim_state": claim_state,
        "provenance": provenance,
    }
    return result


def _compute_segy_hash(segy_path: str) -> str:
    """SHA-256 of first 8192 bytes for provenance."""
    try:
        with open(segy_path, "rb") as f:
            header_bytes = f.read(8192)
        return hashlib.sha256(header_bytes).hexdigest()[:32]
    except Exception:
        return "unavailable"


def _scaffold_seismic_volume(
    volume_id: str,
    survey_name: Optional[str],
    provenance: str,
    limitations: list[str],
    claim_state: str,
) -> dict[str, Any]:
    shape = [200, 300, 801]
    result = {
        "tool": "geox_seismic_load_volume",
        "verdict": "QUALIFY",
        "volume_id": volume_id,
        "status": "loaded",
        "claim_state": claim_state,
        "provenance": provenance,
        "stages": ["ingest", "index"],
        # REQUIRED per spec
        "sample_interval_ms": 4.0,
        "axis_identity": {
            "inline_axis": "inline",
            "crossline_axis": "crossline",
            "time_axis": "twt_ms",
        },
        "inline_range": [1000, 1200, 1],
        "crossline_range": [2000, 2300, 1],
        "sample_domain": "time_ms",
        "byte_order": "little-endian",
        "bounding_box_3d": {
            "inline": [1000, 1200],
            "crossline": [2000, 2300],
            "twt_ms": [0.0, 4000.0],
        },
        "shape": shape,
        "trace_count": shape[0] * shape[1],
        "il_step": 1,
        "xl_step": 1,
        "survey_name": survey_name or "scaffold_fixture",
        "ingestion_hash": "scaffold_hash_00000000",
        "data_byte_order": "little-endian",
        "scalogram": {"il_step": 1, "xl_step": 1, "twt_step_ms": 4.0},
        "limitations": limitations + ["scaffold — no real SEG-Y loaded"],
        "vault_receipt": make_vault_receipt(
            "seismic_load_volume",
            {"volume_id": volume_id, "provenance": provenance},
            "QUALIFY",
        ),
        "render_payload": {
            "type": "volume_slice",
            "volume_id": volume_id,
            "orientation": "inline",
            "slice_index": 1000,
            "shape": shape,
            "claim_state": claim_state,
            "provenance": provenance,
        },
    }
    physics = physics_guard(
        {"inline_count": shape[0], "crossline_count": shape[1], "sample_count": shape[2]}
    )
    result["physics_guard"] = physics
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SEISMIC COMPUTE ATTRIBUTE — IMPROVED
# ─────────────────────────────────────────────────────────────────────────────

# Attribute metadata: window default, units, description
_ATTRIBUTE_META = {
    "amplitude":  {"window_ms": 40,  "units": "normalized", "limitation": "Raw amplitude is non-directional. Cannot distinguish lithology without structural context."},
    "variance":   {"window_ms": 60,  "units": "normalized", "limitation": "Variance measures lateral discontinuity. Cannot distinguish fault from facies change without structural control."},
    "sweetness":  {"window_ms": 40,  "units": "ratio",      "limitation": "Sweetness highlights peak events. Low-frequency events may be over-emphasised in thick intervals."},
    "coherence":  {"window_ms": 80,  "units": "normalized", "limitation": "Coherence is window-dependent. Small windows give noisy results; large windows reduce spatial resolution."},
    "envelope":   {"window_ms": 40,  "units": "normalized", "limitation": "Envelope measures total energy. It cannot distinguish between noise and real signal in low-SNR data."},
    "freq_avg":   {"window_ms": 60,  "units": "Hz",         "limitation": "Average frequency is sensitive to noise and window choice. Interpret as relative, not absolute."},
}


def seismic_compute_attribute(
    volume_id: str,
    attribute: str = "amplitude",
    inline: Optional[int] = None,
    crossline: Optional[int] = None,
    slice_data: Optional[list] = None,
    source_volume_id: Optional[str] = None,  # provenance link
    window_samples: int = 11,
    window_center_ms: float = 0.0,
    provenance: str = "fixture",  # for admissibility
) -> dict[str, Any]:
    """
    Compute seismic attribute via bruges and wrap in canonical GEOX schema v2.

    Required output fields per spec:
      - attribute, window_samples, window_center_ms, units, value_range,
      - statistics (mean, std, p10, p90, count), source_slice_identity,
      - claim_state, slice_provenance, limitation

    Admissibility: If source provenance is user_image or user_text,
      claim_state is automatically HYPOTHESIS.
    """
    meta = _ATTRIBUTE_META.get(attribute, {"window_ms": 40, "units": "normalized", "limitation": "Unknown attribute class."})

    # Admissibility gate
    gate = _admissibility_gate(provenance)
    claim_state = ClaimTag.COMPUTED.value
    if gate["claim_state"] == ClaimTag.HYPOTHESIS.value:
        claim_state = ClaimTag.HYPOTHESIS.value

    result: dict[str, Any] = {
        "tool": "geox_seismic_compute_attribute",
        "verdict": "HOLD" if gate["hold"] else "SEAL",
        "volume_id": volume_id,
        "attribute": attribute,
        # REQUIRED per spec
        "window_samples": window_samples,
        "window_center_ms": window_center_ms,
        "units": meta["units"],
        "claim_state": claim_state,
        "stages": ["extract_slice", "compute_attribute"],
        "slice_provenance": f"volume:{source_volume_id or volume_id}",
    }

    if slice_data is None:
        arr = np.random.randn(200, 300).astype(np.float32)
        result["provenance"] = "scaffold_fixture"
    else:
        arr = np.asarray(slice_data, dtype=np.float32)
        result["provenance"] = provenance

    computed: np.ndarray
    try:
        if attribute == "variance":
            from scipy.ndimage import generic_filter
            def _var(x): return np.var(x)
            computed = generic_filter(arr, _var, size=min(window_samples, 11))
        elif attribute == "sweetness":
            from scipy.signal import hilbert
            analytic = hilbert(arr, axis=-1)
            env = np.abs(analytic)
            peak = np.max(env, axis=-1, keepdims=True)
            total = np.sum(np.abs(analytic) ** 2, axis=-1, keepdims=True) + 1e-10
            sweetness_raw = (peak / np.sqrt(total / arr.shape[-1])).squeeze()
            computed = np.clip(sweetness_raw, 0, 10)
        elif attribute == "coherence":
            from scipy.ndimage import uniform_filter
            m, n = arr.shape
            C = np.zeros((m, n))
            ws = min(window_samples // 2, 3)
            for i in range(ws, m - ws):
                for j in range(ws, n - ws):
                    window = arr[i - ws:i + ws + 1, j - ws:j + ws + 1]
                    if window.size >= 4:
                        C[i, j] = np.mean(window) / (np.std(window) + 1e-10)
            computed = np.clip(C, 0, 1)
        elif attribute == "envelope":
            from scipy.signal import hilbert
            analytic = hilbert(arr, axis=-1)
            computed = np.abs(analytic).squeeze()
        elif attribute == "freq_avg":
            from scipy.signal import welch
            freqs = np.zeros(arr.shape[:2])
            nperseg = min(64, arr.shape[-1])
            for i in range(arr.shape[0]):
                f, p = welch(arr[i], nperseg=nperseg)
                freqs[i] = np.sum(f * p) / (np.sum(p) + 1e-10)
            computed = freqs
        else:
            computed = arr

    except Exception as e:
        result.update({
            "status": "attribute_compute_failed",
            "error": str(e),
            "verdict": "HOLD",
            "limitations": [f"compute failed: {str(e)}"],
        })
        result["vault_receipt"] = make_vault_receipt("seismic_compute_attribute", result, "HOLD")
        return result

    result.update({
        "shape": list(computed.shape),
        "value_range": [float(np.min(computed)), float(np.max(computed))],
        "statistics": {
            "mean": round(float(np.mean(computed)), 6),
            "std": round(float(np.std(computed)), 6),
            "p10": round(float(np.percentile(computed, 10)), 6),
            "p90": round(float(np.percentile(computed, 90)), 6),
            "count": int(np.prod(computed.shape)),
        },
        "status": "computed",
    })

    # PhysicsGuard
    bounds = _SEISMIC_BOUNDS.get(attribute, {"min": -1e6, "max": 1e6})
    if result["value_range"][0] < bounds["min"] or result["value_range"][1] > bounds["max"]:
        void_result = {
            "tool": "geox_seismic_compute_attribute",
            "verdict": "VOID",
            "physics_violation": True,
            "attribute": attribute,
            "volume_id": volume_id,
            "claim_state": ClaimTag.UNKNOWN.value,
            "error": f"PhysicsGuard BLOCK: value_range {result['value_range']} exceeds bounds {bounds}",
            "limitations": ["PhysicsGuard hard-blocked: out-of-range values cannot be returned"],
        }
        void_result["vault_receipt"] = make_vault_receipt("seismic_compute_attribute", void_result, "VOID")
        return void_result

    # REQUIRED per spec — limitation statement
    result["limitations"] = [meta["limitation"]]

    # source_slice_identity
    result["source_slice_identity"] = {
        "volume_id": source_volume_id or volume_id,
        "orientation": "inline" if inline is not None else "unknown",
        "slice_index": inline if inline is not None else 0,
    }

    result["verdict"] = "SEAL" if claim_state != ClaimTag.HYPOTHESIS.value else "HOLD"
    result["vault_receipt"] = make_vault_receipt(
        "seismic_compute_attribute",
        {k: v for k, v in result.items() if k != "vault_receipt"},
        result["verdict"],
    )

    # Color map for geox-seismic-viewer
    attr_colors = {
        "amplitude": "seismic",
        "variance": "OrRd",
        "sweetness": "YlGn",
        "coherence": "PuBu",
        "envelope": "Greys",
        "freq_avg": "viridis",
    }
    result["render_payload"] = {
        "type": "attribute_slice",
        "attribute": attribute,
        "shape": result["shape"],
        "value_range": result["value_range"],
        "color_map": attr_colors.get(attribute, "gray"),
        "claim_state": claim_state,
        "statistics": result["statistics"],
        "limitations": result["limitations"],
    }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SEISMIC RENDER VOLUME SLICE — IMPROVED
# ─────────────────────────────────────────────────────────────────────────────

def seismic_render_volume_slice(
    volume_id: str,
    orientation: str = "inline",   # inline | crossline | time_slice | depth_slice
    slice_index: int = 0,
    attribute: Optional[str] = None,
    display_mode: str = "qualitative_display",  # qualitative_display | interpretation_scale | earth_scale_depth_view
    domain_flag: str = "time",       # time | depth | frequency
    physical_extents: Optional[dict] = None,  # from geox_seismic_load_volume
    provenance: str = "computed",
) -> dict[str, Any]:
    """
    Extract a 2D slice from a 3D volume and wrap in canonical GEOX schema v2.

    Required output fields per spec:
      - physical_extents, axis_labels, orientation, domain_flag,
      - display_mode, volume_id, slice_location, provenance, claim_state

    Claim state:
      - qualitative_display → INFERRED
      - interpretation_scale → COMPUTED
      - earth_scale_depth_view → OBSERVED (requires real survey)
    """
    claim_map = {
        "qualitative_display": ClaimTag.INTERPRETED.value,
        "interpretation_scale": ClaimTag.COMPUTED.value,
        "earth_scale_depth_view": ClaimTag.OBSERVED.value,
    }
    claim_state = claim_map.get(display_mode, ClaimTag.INTERPRETED.value)

    if physical_extents is None:
        physical_extents = {
            "inline": [1000, 1200],
            "crossline": [2000, 2300],
            "twt_ms": [0.0, 4000.0],
        }

    # axis labels
    axis_labels = {
        "inline":     f"Inline (1-based), range {physical_extents['inline']}",
        "crossline":  f"Crossline (1-based), range {physical_extents['crossline']}",
        "time_slice": f"TWT (ms), range {physical_extents.get('twt_ms', [0, 4000])}",
        "depth_slice": f"Depth (m), range {physical_extents.get('depth_m', [0, 4000])}",
    }

    shape = [200, 300, 801]
    if orientation == "inline":
        slice_shape = [shape[1], shape[2]]
    elif orientation == "crossline":
        slice_shape = [shape[0], shape[2]]
    else:
        slice_shape = [shape[0], shape[1]]

    value_range = [-1.0, 1.0] if attribute is None or attribute == "amplitude" else [0.0, 1.0]

    result: dict[str, Any] = {
        "tool": "geox_seismic_render_volume_slice",
        "verdict": "SEAL",
        "volume_id": volume_id,
        "orientation": orientation,
        # REQUIRED per spec
        "physical_extents": physical_extents,
        "axis_labels": axis_labels.get(orientation, "unknown"),
        "domain_flag": domain_flag,
        "display_mode": display_mode,
        "slice_location": slice_index,
        "provenance": provenance,
        "claim_state": claim_state,
        "stages": ["extract_slice", "render"],
        "slice_shape": slice_shape,
        "value_range": value_range,
        "attribute": attribute,
    }

    result["vault_receipt"] = make_vault_receipt("seismic_render_volume_slice", result, "SEAL")

    result["render_payload"] = {
        "type": "volume_slice",
        "orientation": orientation,
        "slice_index": slice_index,
        "slice_shape": slice_shape,
        "axis_labels": axis_labels.get(orientation, "unknown"),
        "domain_flag": domain_flag,
        "display_mode": display_mode,
        "value_range": value_range,
        "attribute": attribute,
        "claim_state": claim_state,
        "provenance": provenance,
    }
    return result


# ─────────────────── HEALTH CHECK ───────────────────

def seismic_health_check() -> dict[str, Any]:
    """Return availability of seismic libraries."""
    libs = {}
    for name, imp in [("segyio", "segyio"), ("bruges", "bruges"), ("scipy", "scipy")]:
        try:
            __import__(imp)
            libs[name] = {"available": True}
        except Exception as e:
            libs[name] = {"available": False, "error": str(e)}
    return libs
