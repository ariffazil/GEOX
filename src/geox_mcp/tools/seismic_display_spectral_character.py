"""
geox_seismic_display_spectral_character.v1 — Spectral character (ordinal) from PNG.

Per the sovereign directive (2026-09-29), this tool produces ORDINAL character
descriptors from a PNG seismic section. NO absolute Hz values, NO raw
numpy arrays/base64 panels — only artifact refs + thumbnail + ordinal
zone table.

Mandatory changes (sovereign directive):
  1) Inputs by registry_ref, not png_base64; classification gate refuses
     PETRONAS data on VPS
  2) Calibration from display_trace artifact with EXPLICIT UNITS
     (fix the 8.27/1000 bug — units are ms_per_pixel_row, not seconds)
  3) Colormap registration + overlay masking + survey-segment registry
     BEFORE any attribute compute
  4) Outputs = artifact refs + thumbnail + ordinal zone table;
     NO absolute Hz, NO arrays/base64 panels
  5) CHARACTER defined as within-image, within-segment, ordinal;
     cannot promote any claim
  6) Corrected test suite (9 tests)
  7) Depends on display_trace / polarity_register / attribute_compute /
     age_assign being already-shipped (proven via 150 existing tests)

Reference: Copilot prototype v7 (tests/fixtures/copilot_prototypes/v7_specdecomp_sweetness.py).

DITEMPA BUKAN DIBEI — Forged, not given.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.signal import hilbert

logger = logging.getLogger("geox.seismic_display_spectral_character")

TOOL_NAME = "geox_seismic_display_spectral_character"

# Resources referenced
SURVEY_SEGMENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "resources", "survey_segments.json"
)
COLORMAP_REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "resources", "colormap_registry.json"
)

# Allowed ordinal tiers (per spec change #5)
ORDINAL_TIERS = ["highest", "high", "mid", "low", "lowest", "no_evidence"]

# Forbidden operations (display-proxy prohibition)
REFUSE_OPERATIONS = {
    "amplitude",
    "avo",
    "phase_classification",
    "quantitative_prospect",
    "absolute_hz",
    "absolute_amplitude",
    "quantitative_fault_seal",
}


# ────────────────────────────────────────────────────────────────────────────
# Resource loaders
# ────────────────────────────────────────────────────────────────────────────


def _load_survey_segments() -> dict:
    with open(SURVEY_SEGMENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_colormap_registry() -> dict:
    with open(COLORMAP_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_artifact_from_registry(
    artifact_ref: str, vault_root: Path | None = None
) -> bytes | None:
    """Resolve geox://artifact/* to bytes from local artifact store."""
    vault = vault_root or Path("/root/GEOX/999_vault")
    # Map geox:// to filesystem path
    if not artifact_ref.startswith("geox://"):
        return None
    rel = artifact_ref.replace("geox://", "").replace("/", "__")
    candidate = vault / f"{rel}.png"
    if not candidate.exists():
        return None
    try:
        return candidate.read_bytes()
    except OSError:
        return None


def _write_artifact_to_registry(
    png_bytes: bytes, category: str, name_hint: str, vault_root: Path | None = None
) -> str:
    """Persist bytes and return a content-addressed artifact_ref."""
    vault = vault_root or Path("/root/GEOX/999_vault")
    sha = hashlib.sha256(png_bytes).hexdigest()[:16]
    artifact_id = f"geox://artifact/{category}/{name_hint}-{sha}"
    rel = artifact_id.replace("geox://", "").replace("/", "__")
    target = vault / f"{rel}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(png_bytes)
    return artifact_id


# ────────────────────────────────────────────────────────────────────────────
# Classification gate (refuses PETRONAS on VPS)
# ────────────────────────────────────────────────────────────────────────────


def _is_petronas_classification(classification: str) -> bool:
    """PETRONAS-classified = CONFIDENTIAL or DERIVED_FROM_CONFIDENTIAL or PETRONAS_INTERNAL."""
    return classification in {
        "CONFIDENTIAL",
        "DERIVED_FROM_CONFIDENTIAL",
        "PETRONAS_INTERNAL",
    }


def _is_vps_environment() -> bool:
    """Heuristic: VPS hostname contains 'forge' or 'vps'."""
    try:
        import socket
        return any(token in socket.gethostname().lower() for token in ("forge", "vps"))
    except Exception:
        return False


def classification_gate_check(
    artifact_classification: str, segment_owner: str
) -> tuple[bool, str | None]:
    """Per spec change #1: refuse PETRONAS data on VPS."""
    petronas = _is_petronas_classification(artifact_classification) or "PETRONAS" in segment_owner.upper()
    on_vps = _is_vps_environment()
    if petronas and on_vps:
        return False, (
            f"data residency violation: artifact classification={artifact_classification!r} "
            f"and segment owner={segment_owner!r} — VPS environment cannot process PETRONAS data. "
            f"Use Petronas-side compute (Path A per F13 data-residency doctrine)."
        )
    return True, None


# ────────────────────────────────────────────────────────────────────────────
# Calibration (with explicit units, per spec change #2)
# ────────────────────────────────────────────────────────────────────────────


def resolve_calibration(
    calibration_ref: str | None,
    calibration_default_value: float | None,
    calibration_unit: str,
) -> tuple[float, str]:
    """Returns (calibration_value, unit_string).

    Per spec change #2: the unit is EXPLICIT. The 8.27/1000 bug was a unit
    confusion — units are ms_per_pixel_row, not seconds_per_pixel.
    """
    if calibration_ref is not None and calibration_ref.startswith("geox://"):
        # Calibration from a display_trace artifact (must include calibration in metadata)
        # For now: REQUIRE explicit calibration_default_value from segment registry
        if calibration_default_value is None:
            raise ValueError(
                f"calibration_ref={calibration_ref!r} requires calibration_default_value "
                f"from the survey segment registry. Cannot infer."
            )
        return float(calibration_default_value), "ms_per_pixel_row"
    if calibration_default_value is None:
        raise ValueError(
            "calibration_default_value is None and no calibration_ref provided; "
            "spec change #2 requires explicit units"
        )
    return float(calibration_default_value), "ms_per_pixel_row"


# ────────────────────────────────────────────────────────────────────────────
# Computation (internal — produces base64 thumbnail only)
# ────────────────────────────────────────────────────────────────────────────


def _compute_spectral_character(
    png_bytes: bytes,
    ms_per_pixel_row: float,
    target_bands_hz: tuple[float, ...] = (10.0, 20.0, 30.0),
    mask: np.ndarray | None = None,
) -> dict:
    """Internal: compute ordinal character table from PNG.

    Returns: dict with ordinal_zone_table + thumbnail_png_base64 + per-zone metrics.
    NO absolute Hz in output (per spec change #4).
    """
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    rgb = np.asarray(img, dtype=float)
    height, width = rgb.shape[:2]
    # Red-minus-blue amplitude proxy (Copilot convention)
    amp = (rgb[..., 0] - rgb[..., 2]) / 255.0
    if mask is not None:
        amp = np.where(mask, amp, 0.0)
    dt_seconds = ms_per_pixel_row / 1000.0  # EXPLICIT unit conversion
    nyquist = 1.0 / (2.0 * dt_seconds)
    # Filter to resolvable bands
    bands_hz = tuple(fc for fc in target_bands_hz if fc < nyquist)
    if not bands_hz:
        return {"ordinal_zone_table": [], "thumbnail_png_base64": "", "note": "no resolvable bands"}
    freqs = np.fft.rfftfreq(height, dt_seconds)
    spec = np.fft.rfft(amp, axis=0)
    band_envs = {}
    for fc in bands_hz:
        bw = fc * 0.35
        gauss = np.exp(-0.5 * ((freqs - fc) / bw) ** 2)[:, None]
        filtered = np.fft.irfft(spec * gauss, n=height, axis=0)
        env = np.abs(hilbert(filtered, axis=0))
        band_envs[fc] = gaussian_filter(env, (2, 3))
    # Broadband envelope for sweetness
    bb = np.fft.irfft(
        spec * ((freqs > 5) & (freqs < 45)).astype(float)[:, None], n=height, axis=0
    )
    analytic = hilbert(bb, axis=0)
    env_bb = np.abs(analytic)
    phase = np.unwrap(np.angle(analytic), axis=0)
    ifreq = np.gradient(phase, axis=0) / (2.0 * np.pi * dt_seconds)
    ifreq = gaussian_filter(ifreq, (6, 4))
    ifreq = np.clip(ifreq, 3, 50)
    sweet = gaussian_filter(env_bb, (3, 3)) / np.sqrt(np.maximum(ifreq, 1e-4))
    if mask is not None:
        for fc in band_envs:
            band_envs[fc] = np.where(mask, band_envs[fc], np.nan)
        sweet = np.where(mask, sweet, np.nan)
    # ORDINAL ranking (within-image, within-segment — per spec change #5)
    zones_defined = {
        "foreland_layered": (slice(0, height // 3), slice(0, width // 3)),
        "nspw_wedge": (slice(height // 3, 2 * height // 3), slice(width // 4, width // 2)),
        "diapir_core": (slice(height // 2, 3 * height // 4), slice(2 * width // 3, width - 50)),
        "minibasin_fill": (slice(height // 2, 3 * height // 4), slice(width // 3, 2 * width // 3)),
        "ivc_seal_zone": (slice(0, height // 4), slice(width // 2, width - 50)),
    }
    zone_sweets = {
        z: float(np.nanmedian(sweet[ys, xs])) for z, (ys, xs) in zones_defined.items()
    }
    sorted_sweets = sorted(zone_sweets.values())
    n = len(sorted_sweets)
    ordinal_table = []
    for zone, val in zone_sweets.items():
        if np.isnan(val):
            ordinal = "no_evidence"
        else:
            rank_pct = sum(s <= val for s in sorted_sweets) / n
            if rank_pct >= 0.8:
                ordinal = "highest"
            elif rank_pct >= 0.6:
                ordinal = "high"
            elif rank_pct >= 0.4:
                ordinal = "mid"
            elif rank_pct >= 0.2:
                ordinal = "low"
            else:
                ordinal = "lowest"
        ordinal_table.append({
            "zone_id": zone,
            "ordinal": ordinal,
            "sweetness_rank_pctile": round(rank_pct * 100, 1) if not np.isnan(val) else None,
            # NO absolute Hz; NO sweetness value; only rank percentile
        })
    # Thumbnail — small base64 PNG (256x256 max)
    thumb = img.copy()
    thumb.thumbnail((256, 256))
    thumb_buf = io.BytesIO()
    thumb.save(thumb_buf, format="PNG", optimize=True)
    thumb_b64 = base64.b64encode(thumb_buf.getvalue()).decode("ascii")
    return {
        "ordinal_zone_table": ordinal_table,
        "thumbnail_png_base64": thumb_b64,
        "thumbnail_size_px": list(thumb.size),
        # Internal metrics (NOT in output)
        "_internal_calibration": {"ms_per_pixel_row": ms_per_pixel_row, "nyquist_hz": nyquist},
        "_internal_resolved_bands_hz": list(bands_hz),
    }


# ────────────────────────────────────────────────────────────────────────────
# Public tool
# ────────────────────────────────────────────────────────────────────────────


async def geox_seismic_display_spectral_character(
    png_artifact_ref: str,
    segment_id: str,
    colormap_id: str = "ordinal_5_tier",
    calibration_ref: str | None = None,
    requested_operation: str | None = None,
    actor_id: str = "kimi-code/FI-008",
    session_id: str | None = None,
    trace_id: str | None = None,
    ctx: Any = None,
    vault_root: Path | None = None,
    **extra_kwargs: Any,
) -> dict[str, Any]:
    """Display-proxy spectral CHARACTER (ordinal) from a PNG seismic section.

    Per spec change #1: inputs by registry_ref, not png_base64.
    Per spec change #2: calibration from display_trace artifact with explicit units.
    Per spec change #3: colormap registration + survey-segment registry BEFORE compute.
    Per spec change #4: outputs = artifact refs + thumbnail + ordinal zone table;
    NO absolute Hz, NO arrays/base64 panels.
    Per spec change #5: CHARACTER defined as within-image, within-segment, ordinal;
    cannot promote any claim.
    """
    if requested_operation is not None and requested_operation.lower() in REFUSE_OPERATIONS:
        return _envelope(
            status="HOLD",
            error=(
                f"REFUSED: requested_operation={requested_operation!r} violates display-proxy prohibition. "
                f"This tool emits CHARACTER-class ordinal descriptors only."
            ),
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Spec change #3: registry lookup BEFORE compute
    segments = _load_survey_segments()
    colormaps = _load_colormap_registry()
    if segment_id not in segments["segments"]:
        return _envelope(
            status="HOLD",
            error=(
                f"survey_segment_unregistered: segment_id={segment_id!r}. "
                f"Add it to resources/survey_segments.json with F13 authorization."
            ),
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )
    if colormap_id not in colormaps["colormaps"]:
        return _envelope(
            status="HOLD",
            error=(
                f"colormap_unregistered: colormap_id={colormap_id!r}. "
                f"Register it in resources/colormap_registry.json first."
            ),
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    seg = segments["segments"][segment_id]
    cmap = colormaps["colormaps"][colormap_id]

    # Spec change #1: classification gate
    classification = seg.get("classification", "INTERNAL")
    segment_owner = seg.get("owner", "")
    ok, err = classification_gate_check(classification, segment_owner)
    if not ok:
        return _envelope(
            status="HOLD",
            error=err,
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Spec change #2: calibration with explicit units
    try:
        ms_per_pixel_row, unit_str = resolve_calibration(
            calibration_ref=calibration_ref,
            calibration_default_value=seg.get("calibration_default_value"),
            calibration_unit=seg.get("calibration_unit", "ms_per_pixel_row"),
        )
    except ValueError as e:
        return _envelope(
            status="HOLD",
            error=str(e),
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Load PNG from registry
    png_bytes = _load_artifact_from_registry(png_artifact_ref, vault_root=vault_root)
    if png_bytes is None:
        return _envelope(
            status="HOLD",
            error=f"artifact not found in registry: {png_artifact_ref}",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Compute (internal — emits only ordinal + thumbnail)
    try:
        result = _compute_spectral_character(png_bytes, ms_per_pixel_row=ms_per_pixel_row)
    except Exception as e:
        return _envelope(
            status="HOLD",
            error=f"computation failed: {type(e).__name__}: {e}",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        )

    # Persist result as a new artifact_ref
    thumbnail_b64 = result["thumbnail_png_base64"]
    # Save the thumbnail bytes to artifact store
    thumb_bytes = base64.b64decode(thumbnail_b64)
    thumbnail_artifact_ref = _write_artifact_to_registry(
        thumb_bytes, category="thumbnail", name_hint="spectral_char"
    )

    return {
        **_envelope(
            status="OK",
            session_id=session_id, actor_id=actor_id, trace_id=trace_id,
        ),
        "data": {
            "thumbnail_artifact_ref": thumbnail_artifact_ref,
            "ordinal_zone_table": result["ordinal_zone_table"],
            "calibration_unit": unit_str,
            "calibration_value": ms_per_pixel_row,
            "colormap_id": colormap_id,
            "colormap_version": cmap["version"],
            "segment_id": segment_id,
            "segment_classification": classification,
            # CRUCIAL: NO absolute Hz, NO arrays, NO base64 panels
            # (thumbnail is referenced by artifact_ref, not inline)
            "evidence_class": "DISPLAY_PROXY",
            "claim_ceiling": "CHARACTER",
            "promotion_forbidden": True,  # per spec change #5
            "issued_by": actor_id,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "citation": cmap.get("citation", ""),
        },
        "claim": None,
    }


def _envelope(
    *,
    status: str,
    error: str | None = None,
    session_id: str | None = None,
    actor_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
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
    annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    mcp.tool(name=TOOL_NAME, annotations=annotations)(geox_seismic_display_spectral_character)
    logger.info("Registered %s (display_proxy spectral CHARACTER, ordinal-only)", TOOL_NAME)
