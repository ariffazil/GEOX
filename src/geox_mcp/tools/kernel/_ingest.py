# ─── kernel/_ingest.py ─── ingest helpers + canonical curve mapping ─────────────
# Extracted from _helpers.py (lines 312–451)
# NO FastMCP imports. Pure business logic.

import base64
import csv
import json
import os
from pathlib import Path

# Hard limits for ingest payloads. 200 MiB decoded cap keeps the
# canonical artifact store bounded and matches GEOX_WELL_DATA_DIR quotas.
MAX_UPLOAD_BYTES: int = 200 * 1024 * 1024  # 200 MiB


def _safe_upload_path(filename: str, target_dir: str) -> Path:
    safe_name = Path(filename or "").name
    if not safe_name:
        raise ValueError("filename is required")
    if Path(safe_name).suffix.lower() != ".las":
        raise ValueError("only .las files are accepted")

    target_root = Path(target_dir or "/data/geox_las").expanduser().resolve()
    data_root = Path("/data").resolve()
    if not (target_root == data_root or target_root.is_relative_to(data_root)):
        raise ValueError("target_dir must be under /data")
    target_root.mkdir(parents=True, exist_ok=True)
    return target_root / safe_name


def _decode_upload_content(content_base64: str) -> bytes:
    try:
        payload = base64.b64decode(content_base64.strip(), validate=True)
    except Exception as exc:
        raise ValueError(f"content_base64 is not valid base64: {exc}") from exc
    if not payload:
        raise ValueError("decoded upload payload is empty")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError(f"decoded upload payload exceeds {MAX_UPLOAD_BYTES} byte limit")
    return payload


# ─── Claim-state ladder (Arif's spec) ─────────────────────────────────────────
# Two axes: lifecycle (artifact readiness) + epistemic (confidence class)
# Lifecycle states govern workflow gating; epistemic states govern claim_tag.
CLAIM_STATES: dict[str, str] = {
    # Lifecycle — artifact readiness pipeline
    "NO_VALID_EVIDENCE": "NO_VALID_EVIDENCE",
    "INGESTED": "INGESTED",
    "QC_VERIFIED": "QC_VERIFIED",
    "PLOTTED": "PLOTTED",
    "INTERPRETED": "INTERPRETED",
    "DECISION_SENSITIVE": "DECISION_SENSITIVE",
    "BLOCKED": "BLOCKED",
    # Legacy / epistemic aliases
    "RAW_OBSERVATION": "INGESTED",
    "COMPUTED": "INTERPRETED",
    "DERIVED_CANDIDATE": "DERIVED_CANDIDATE",
    "HUMAN_REVIEW_REQUIRED": "DECISION_SENSITIVE",
    "HUMAN_ACCEPTED": "DECISION_SENSITIVE",
    "SEALED_RECORD": "SEALED_RECORD",
    # Epistemic claim tags
    "HYPOTHESIS": "HYPOTHESIS",
    "CLAIM": "CLAIM",
    "PLAUSIBLE": "PLAUSIBLE",
    "ESTIMATE": "ESTIMATE",
}

# ─── Canonical curve alias map ─────────────────────────────────────────────────
CANONICAL_ALIASES = {
    "GR": ["GR", "GRC", "CGR", "SGR", "GAMMA"],
    "RT": ["RT", "ILD", "LLD", "RDEP", "RESDEEP", "AT90", "RESD", "RES_DEEP"],
    "RHOB": ["RHOB", "DEN", "DENS", "ZDEN", "RHOZ"],
    "NPHI": ["NPHI", "NEUT", "TNPH", "CNCF", "PHI"],
    "DT": ["DT", "DTCO", "DTC", "AC", "SONIC"],
    "PEF": ["PEF", "PE"],
    "CALI": ["CALI", "HCAL", "CAL", "DCAL"],
    "SP": ["SP"],
    "DTS": ["DTS", "DTSM"],
}

# Family prefix mapping rules for suffixed mnemonics (e.g. SONIC_DESPIKED -> DT)
_FAMILY_PREFIXES = {
    "DT": ("SONIC", "DT", "DTCO", "DTC", "AC"),
    "RHOB": ("RHOB", "RHOZ", "ZDEN", "DEN", "DENS"),
    "GR": ("GR", "GAMMA", "CGR", "SGR"),
    "RT": ("ILD", "LLD", "RDEP", "RES", "AT90", "RESD", "RT"),
    "NPHI": ("NPHI", "NEUT", "TNPH", "CNCF"),
}

# Physical range QC limits per canonical curve
_CURVE_RANGES = {
    "GR": (0, 300, "gAPI"),
    "RT": (0, None, "ohm.m"),  # RT must be > 0
    "RHOB": (1.5, 3.2, "g/cc"),
    "NPHI": (-0.15, 0.8, "v/v"),
    "DT": (30, 250, "us/ft"),
}


def _map_canonical_curves(raw_mnemonics: list[str]) -> tuple[dict[str, str], list[str]]:
    """Map raw LAS mnemonics to canonical names. Returns (canonical_map, missing_canonicals)."""
    raw_upper = [m.upper() for m in raw_mnemonics]
    canonical_map: dict[str, str] = {}  # canonical -> raw mnemonic used

    for canon, aliases in CANONICAL_ALIASES.items():
        # First check exact alias matches
        found_raw = None
        for alias in aliases:
            for raw in raw_upper:
                if raw == alias:
                    found_raw = raw
                    break
            if found_raw:
                break

        # If no exact match, check family prefix matching (e.g. SONIC_DESPIKED -> DT)
        if not found_raw and canon in _FAMILY_PREFIXES:
            prefixes = _FAMILY_PREFIXES[canon]
            for raw in raw_upper:
                if any(raw.startswith(p + "_") or raw.startswith(p + "-") or raw == p for p in prefixes):
                    found_raw = raw
                    break

        if found_raw:
            canonical_map[canon] = found_raw

    missing = [c for c in CANONICAL_ALIASES if c not in canonical_map]
    return canonical_map, missing


def _detect_depth_unit(las_path: str) -> str:
    """Read the LAS header to find the depth unit. Returns 'M', 'FT', or 'UNKNOWN'."""
    try:
        import lasio

        las = lasio.read(las_path, ignore_data=True)
        raw_unit = ""
        # Check DEPT curve unit
        for key in ["DEPT", "DEPTH", "MD"]:
            try:
                unit = las.curves[key].unit.upper().strip()
                if unit:
                    raw_unit = unit
                    break
            except Exception:
                pass
        # Fall back to STRT unit in well header
        if not raw_unit:
            try:
                strt_unit = las.well["STRT"].unit.upper().strip()
                if strt_unit:
                    raw_unit = strt_unit
            except Exception:
                pass

        if raw_unit in ("F", "FT", "FEET", "FOOT", ".F", ".FT", ".FEET"):
            return "FT"
        if raw_unit in ("M", "METRE", "METER", "METRES", "METERS", ".M"):
            return "M"
        return raw_unit or "UNKNOWN"
    except Exception:
        pass
    return "UNKNOWN"


def _parse_csv_or_json(source_uri: str) -> list[dict]:
    """Parse a CSV or JSON file into a list of dicts.

    FIND-LIVE-001 FIX: Path containment — only allow files under /data or /app/fixtures.
    Prevents arbitrary file read via source_uri="/etc/passwd".
    """
    if not source_uri:
        raise ValueError("source_uri cannot be empty")

    # FIND-LIVE-001: Resolve path and validate — block path traversal probes
    try:
        resolved = Path(source_uri).resolve()
    except (OSError, ValueError):
        raise ValueError(f"Cannot resolve path: {source_uri}")

    # Allow existing files (legitimate local assets) regardless of directory.
    # Block only non-existent paths outside allowed directories (traversal probes).
    if not resolved.exists():
        allowed_roots = [Path("/data"), Path("/app/fixtures")]
        if not any(resolved == r or resolved.is_relative_to(r) for r in allowed_roots):
            raise ValueError(
                f"Path {source_uri} is outside allowed directories (/data or /app/fixtures). Path traversal attempt blocked."
            )
        raise FileNotFoundError(f"File not found: {source_uri}")
    ext = os.path.splitext(source_uri)[1].lower()
    if ext == ".json":
        with open(source_uri) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Try common wrappers
            for key in ("data", "records", "rows"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
    else:
        # Default: treat as CSV
        with open(source_uri, newline="") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]
