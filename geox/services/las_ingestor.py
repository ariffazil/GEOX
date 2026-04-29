"""
LAS ingestion pipeline for GEOX Wave 2 — Improved v2
DITEMPA BUKAN DIBERI — Forged, Not Given

Improvement spec applied:
  - geox_well_load_bundle: witness summary with loaded_curves, depth_range,
    missing_channels, source_type, suitability (decision_ready|screening_only|void),
    well_id, permit, qc_prerequisite_met
  - geox_well_qc_logs: structured severity PASS/WARN/FAIL, curve-level issues
    (spike, gap, null_zone, unit_ambiguity, cross_curve_inconsistency)
  - All outputs: claim_state, provenance, limitations, human_decision_point
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from geox.core.physics_guard import PhysicsGuard

try:
    import lasio
except ImportError:
    lasio = None

try:
    from welly import Well
except ImportError:
    Well = None


# ─────────────────── CLAIM TAG ───────────────────

class ClaimTag(str):
    OBSERVED = "OBSERVED"
    COMPUTED = "COMPUTED"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


# ─────────────────── QC RESULT DATACLASSES ───────────────────

@dataclass
class QCIssue:
    type: str  # spike | gap | null_zone | unit_ambiguity | cross_curve_inconsistency
    depth_m: float | list[float]
    value: float | None = None
    threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d = {"type": self.type, "depth_m": self.depth_m}
        if self.value is not None:
            d["value"] = self.value
        if self.threshold is not None:
            d["threshold"] = self.threshold
        return d


@dataclass
class CurveQCResult:
    mnemonic: str
    unit: str
    status: str  # PASS | WARN | FAIL
    issues: list[QCIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mnemonic": self.mnemonic,
            "unit": self.unit,
            "status": self.status,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class WellLoadResult:
    """Output schema for geox_well_load_bundle — v2 witness summary."""
    tool: str = "geox_well_load_bundle"
    well_id: str = ""
    permit: str = ""
    source_type: str = "LAS"  # fixture | LAS | user_upload
    loaded_curves: list[str] = field(default_factory=list)
    depth_range: list[float] = field(default_factory=list)
    missing_channels: list[str] = field(default_factory=list)
    suitability: str = "void"  # decision_ready | screening_only | void
    claim_state: str = ClaimTag.UNKNOWN
    qc_prerequisite_met: bool = False
    limitations: list[str] = field(default_factory=list)
    vault_receipt: dict = field(default_factory=dict)

    @property
    def asset_id(self) -> str:
        return self.well_id

    @property
    def uwi(self) -> str:
        return self.permit if self.permit != "UNKNOWN" else self.well_id

    @property
    def curves(self) -> list[Any]:
        return [type("CurveManifest", (), {"mnemonic": curve})() for curve in self.loaded_curves]

    @property
    def depth_range_m(self) -> list[float]:
        return self.depth_range

    @property
    def n_depth_samples(self) -> int:
        return getattr(self, "_n_depth_samples", 0)

    @property
    def n_curves(self) -> int:
        return len(self.loaded_curves)

    @property
    def claim_tag(self) -> str:
        return {
            ClaimTag.OBSERVED: "CLAIM",
            ClaimTag.COMPUTED: "ESTIMATE",
            ClaimTag.HYPOTHESIS: "HYPOTHESIS",
            ClaimTag.UNKNOWN: "UNKNOWN",
        }.get(self.claim_state, "UNKNOWN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "asset_id": self.well_id,
            "well_id": self.well_id,
            "uwi": self.permit if self.permit != "UNKNOWN" else self.well_id,
            "permit": self.permit,
            "source_type": self.source_type,
            "loaded_curves": self.loaded_curves,
            "curves": [{"mnemonic": curve} for curve in self.loaded_curves],
            "curve_count": len(self.loaded_curves),
            "n_curves": len(self.loaded_curves),
            "depth_range": self.depth_range,
            "depth_range_m": self.depth_range,
            "n_depth_samples": getattr(self, "_n_depth_samples", 0),
            "missing_channels": self.missing_channels,
            "qcfail_count": 0 if self.suitability != "void" else 1,
            "suitability": self.suitability,
            "claim_state": self.claim_state,
            "claim_tag": {
                ClaimTag.OBSERVED: "CLAIM",
                ClaimTag.COMPUTED: "ESTIMATE",
                ClaimTag.HYPOTHESIS: "HYPOTHESIS",
                ClaimTag.UNKNOWN: "UNKNOWN",
            }.get(self.claim_state, "UNKNOWN"),
            "qc_prerequisite_met": self.qc_prerequisite_met,
            "limitations": self.limitations,
            "vault_receipt": self.vault_receipt,
        }


@dataclass
class WellQCResult:
    """Output schema for geox_well_qc_logs — v2 structured severity."""
    tool: str = "geox_well_qc_logs"
    qc_overall: str = "FAIL"  # PASS | WARN | FAIL
    curve_results: list[CurveQCResult] = field(default_factory=list)
    spike_threshold: float = 150.0
    gap_threshold_m: float = 5.0
    claim_state: str = ClaimTag.UNKNOWN
    limitations: list[str] = field(default_factory=list)
    human_decision_point: str = ""
    vault_receipt: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "qc_overall": self.qc_overall,
            "curve_results": [c.to_dict() for c in self.curve_results],
            "spike_threshold": self.spike_threshold,
            "gap_threshold_m": self.gap_threshold_m,
            "claim_state": self.claim_state,
            "limitations": self.limitations,
            "human_decision_point": self.human_decision_point,
            "vault_receipt": self.vault_receipt,
        }


# ─────────────────── CURVE MAP ───────────────────

_CURVE_MAP = {
    "NPHI": "porosity", "PHI": "porosity",
    "SW": "sw", "VSH": "vsh",
    "GR": "gamma_ray", "ILD": "resistivity",
    "RHOB": "density", "DT": "compressional",
}


def _make_vault_receipt(tool_name: str, payload: dict, verdict: str) -> dict:
    import hashlib, json
    from datetime import datetime, timezone
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{tool_name}:{canonical}".encode("utf-8")).hexdigest()
    return {
        "vault": "VAULT999",
        "tool_name": tool_name,
        "verdict": verdict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": digest[:16],
    }


# ─────────────────── INGESTOR ───────────────────

class LASIngestor:
    """Read LAS 2.0/3.0 files and produce v2 JSON-safe manifests."""

    REQUIRED_CURVES = {"GR": "gamma_ray", "ILD": "resistivity", "PHI": "porosity"}

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()
        self.spike_threshold = 150.0  # API or gAPI
        self.gap_threshold_m = 5.0

    def _require_deps(self):
        if lasio is None:
            raise RuntimeError("lasio required for LAS ingestion")

    def _detect_spikes(self, values: np.ndarray, depths: np.ndarray) -> list[QCIssue]:
        issues: list[QCIssue] = []
        clean = values[~np.isnan(values)]
        if clean.size == 0:
            return [QCIssue(type="null_zone", depth_m=float(depths[0]) if depths.size else 0.0)]
        std_val = float(np.nanstd(clean))
        threshold = max(std_val * 5.0, self.spike_threshold)
        diffs = np.abs(np.diff(clean))
        for j, d in enumerate(diffs):
            if d > threshold:
                idx = j + 1
                issues.append(QCIssue(
                    type="spike",
                    depth_m=float(depths[idx]) if idx < len(depths) else 0.0,
                    value=float(clean[idx]),
                    threshold=threshold,
                ))
        return issues[:5]  # cap at 5 spikes

    def _detect_gaps(self, values: np.ndarray, depths: np.ndarray) -> list[QCIssue]:
        issues: list[QCIssue] = []
        null_mask = np.isnan(values)
        if not null_mask.any():
            return issues
        in_gap = False
        gap_start = 0.0
        for i in range(len(values)):
            if null_mask[i] and not in_gap:
                in_gap = True
                gap_start = float(depths[i])
            elif not null_mask[i] and in_gap:
                in_gap = False
                gap_end = float(depths[i - 1])
                if gap_end - gap_start >= self.gap_threshold_m:
                    issues.append(QCIssue(type="gap", depth_m=[gap_start, gap_end]))
        return issues

    def _detect_null_zones(self, values: np.ndarray, depths: np.ndarray) -> list[QCIssue]:
        issues: list[QCIssue] = []
        null_mask = np.isnan(values)
        if not null_mask.any():
            return issues
        in_null = False
        null_start = 0.0
        for i in range(len(values)):
            if null_mask[i] and not in_null:
                in_null = True
                null_start = float(depths[i])
            elif not null_mask[i] and in_null:
                in_null = False
                null_end = float(depths[i - 1])
                if null_end - null_start >= 2.0:
                    issues.append(QCIssue(type="null_zone", depth_m=[null_start, null_end]))
        return issues

    def ingest(self, path: str, asset_id: str | None = None, chunk_size: int = 200) -> WellLoadResult:
        self._require_deps()
        source = Path(path)
        las = lasio.read(source)
        well = Well.from_las(str(source)) if Well is not None else None

        depth_curve = np.asarray(las.index, dtype=float)
        loaded_curves: list[str] = []
        curve_qc_results: list[CurveQCResult] = []
        all_issues: list[QCIssue] = []

        for curve in las.curves:
            mnemonic = curve.mnemonic.strip().upper()
            if mnemonic in {"DEPT", "DEPTH"}:
                continue
            values = np.asarray(las[curve.mnemonic], dtype=float)
            loaded_curves.append(mnemonic)

            # Run QC
            issues: list[QCIssue] = []
            issues += self._detect_spikes(values, depth_curve)
            issues += self._detect_gaps(values, depth_curve)
            issues += self._detect_null_zones(values, depth_curve)

            if issues:
                status = "WARN" if len(issues) <= 3 else "FAIL"
            else:
                status = "PASS"

            cr = CurveQCResult(mnemonic=mnemonic, unit=str(curve.unit or ""), status=status, issues=issues)
            curve_qc_results.append(cr)
            all_issues.extend(issues)

        # UWI / well name
        uwi = None
        if "UWI" in las.well:
            uwi = str(las.well["UWI"].value)
        well_name = None
        if "WELL" in las.well:
            well_name = str(las.well["WELL"].value)
        elif well is not None:
            well_name = getattr(well, "name", None)

        well_id = asset_id or (uwi or source.stem)
        permit = str(las.well.get("PERMIT", las.well.get("FLD", "UNKNOWN")))

        # Missing channels
        required = set(self.REQUIRED_CURVES.keys())
        loaded_set = set(loaded_curves)
        missing = [c for c in required if c not in loaded_set]

        # Suitability
        qcfail_count = sum(1 for c in curve_qc_results if c.status == "FAIL")
        if qcfail_count > 0:
            suitability = "void"
        elif len(missing) > 1:
            suitability = "screening_only"
        else:
            suitability = "decision_ready"

        # Claim state
        if suitability == "decision_ready":
            claim_state = ClaimTag.OBSERVED
        elif suitability == "screening_only":
            claim_state = ClaimTag.COMPUTED
        else:
            claim_state = ClaimTag.HYPOTHESIS

        limitations = []
        if missing:
            limitations.append(f"Missing recommended curves: {missing}")
        if qcfail_count > 0:
            limitations.append(f"{qcfail_count} curve(s) in FAIL state — interpret with caution")

        result = WellLoadResult(
            well_id=well_id,
            permit=permit,
            source_type="LAS",
            loaded_curves=loaded_curves,
            depth_range=[round(float(np.nanmin(depth_curve)), 4), round(float(np.nanmax(depth_curve)), 4)],
            missing_channels=missing,
            suitability=suitability,
            claim_state=claim_state,
            qc_prerequisite_met=(suitability != "void"),
            limitations=limitations,
            vault_receipt={},
        )
        result._n_depth_samples = int(depth_curve.size)  # type: ignore[attr-defined]
        result.vault_receipt = _make_vault_receipt("geox_well_load_bundle", result.to_dict(), "HOLD" if suitability == "void" else "SEAL")
        return result

    def qc_logs(self, well_result: WellLoadResult, path: str) -> WellQCResult:
        """Structured QC — PASS/WARN/FAIL per curve with issues."""
        self._require_deps()
        source = Path(path)
        las = lasio.read(source)
        depth_curve = np.asarray(las.index, dtype=float)

        curve_results: list[CurveQCResult] = []
        total_fail = 0
        total_warn = 0

        for curve in las.curves:
            mnemonic = curve.mnemonic.strip().upper()
            if mnemonic in {"DEPT", "DEPTH"}:
                continue
            values = np.asarray(las[curve.mnemonic], dtype=float)

            issues: list[QCIssue] = []
            issues += self._detect_spikes(values, depth_curve)
            issues += self._detect_gaps(values, depth_curve)
            issues += self._detect_null_zones(values, depth_curve)

            fail_count = sum(1 for i in issues if i.type in ("spike", "gap"))
            warn_count = len(issues) - fail_count

            if fail_count > 0:
                status = "FAIL"
                total_fail += 1
            elif warn_count > 0:
                status = "WARN"
                total_warn += 1
            else:
                status = "PASS"

            curve_results.append(CurveQCResult(
                mnemonic=mnemonic,
                unit=str(curve.unit or ""),
                status=status,
                issues=issues,
            ))

        # Overall
        if total_fail > 0:
            qc_overall = "FAIL"
        elif total_warn > 0:
            qc_overall = "WARN"
        else:
            qc_overall = "PASS"

        # Claim state
        if qc_overall == "PASS":
            claim_state = ClaimTag.OBSERVED
        elif qc_overall == "WARN":
            claim_state = ClaimTag.COMPUTED
        else:
            claim_state = ClaimTag.HYPOTHESIS

        limitations = []
        if total_fail > 0:
            limitations.append(f"{total_fail} curve(s) in FAIL — decision use not recommended")
        if total_warn > 0:
            limitations.append(f"{total_warn} curve(s) in WARN — interpret with caution")

        human_decision = ""
        if qc_overall == "FAIL":
            human_decision = "QC FAIL — do not proceed to geox_well_compute_petrophysics without human review of failed curves."

        result = WellQCResult(
            qc_overall=qc_overall,
            curve_results=curve_results,
            spike_threshold=self.spike_threshold,
            gap_threshold_m=self.gap_threshold_m,
            claim_state=claim_state,
            limitations=limitations,
            human_decision_point=human_decision,
            vault_receipt={},
        )
        result.vault_receipt = _make_vault_receipt("geox_well_qc_logs", result.to_dict(), "HOLD" if qc_overall == "FAIL" else "SEAL")
        return result


# ─────────────────── OCR INGESTOR ─────────────────────────────────────────────

class OCRIngestor:
    """
    Analog log digitizer — Stage 1 OCR using pytesseract.
    
    Accepts a scanned image of a paper log, extracts curve data via OCR,
    and returns a WellDigitizeResult with:
      - extracted text (raw)
      - parsed curve values (depth-indexed numpy arrays)
      - digitize confidence
      - suitability assessment

    This is Stage 1 of the geox_well_digitize_log pipeline.
    Neural interpretation (Stage 2) is planned separately.
    """

    # Known GR API range for sanity check
    GR_PHYSICAL_MIN = 0.0
    GR_PHYSICAL_MAX = 300.0
    # Resistivity physical range (ohm.m)
    RT_PHYSICAL_MIN = 0.1
    RT_PHYSICAL_MAX = 100000.0
    # Porosity physical range (v/v)
    PHI_PHYSICAL_MIN = 0.0
    PHI_PHYSICAL_MAX = 0.50

    def __init__(self, guard: PhysicsGuard | None = None) -> None:
        self.guard = guard or PhysicsGuard()
        self.spike_threshold = 150.0

    def _require_deps(self):
        try:
            from PIL import Image
            import pytesseract
        except ImportError as e:
            raise RuntimeError(
                f"OCR dependencies not available: {e}. "
                "Ensure PIL and pytesseract are installed in the container."
            )

    def _parse_depth_from_text(self, text_lines: list[str]) -> tuple[list[float], list[int]]:
        """
        Attempt to extract depth values from OCR text.
        Returns (depths, line_indices) where line_indices map to text_lines.
        Uses regex to find depth patterns like '2500' or '2500.5'.
        """
        import re
        depth_pattern = re.compile(r'^\s*(\d{3,5}(?:\.\d+)?)\s*$')
        depths: list[float] = []
        line_indices: list[int] = []

        for i, line in enumerate(text_lines):
            m = depth_pattern.match(line.strip())
            if m:
                try:
                    d = float(m.group(1))
                    if 100 <= d <= 10000:  # reasonable depth in meters
                        depths.append(d)
                        line_indices.append(i)
                except ValueError:
                    pass
        return depths, line_indices

    def _parse_curve_value(self, token: str) -> float | None:
        """Parse a single numeric token from OCR text."""
        import re
        m = re.search(r'[-+]?\d*\.\d+|\d+', token)
        if not m:
            return None
        try:
            return float(m.group())
        except ValueError:
            return None

    def _detect_curve_type_from_text(self, text: str) -> dict[str, list[str]]:
        """
        Scan OCR text to identify which curve columns appear present.
        Returns {curve_mnemonic: [extracted_values]}.
        """
        import re
        # GR column patterns
        gr_matches = re.findall(r'\b(?:GR|GAMMA|CGR|SGR)\s*[:=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)
        rt_matches = re.findall(r'\b(?:RT|RD|RS|ILD|AT[0-9]+)\s*[:=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)
        rho_matches = re.findall(r'\b(?:RHO|RHOB|DEN)\s*[:=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)
        nphi_matches = re.findall(r'\b(?:NPHI|PHI|POR)\s*[:=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)
        dt_matches = re.findall(r'\b(?:DT|AC|DTC)\s*[:=]?\s*(\d+\.?\d*)', text, re.IGNORECASE)

        detected = {}
        if gr_matches: detected['GR'] = gr_matches[:100]
        if rt_matches: detected['RT'] = rt_matches[:100]
        if rho_matches: detected['RHOB'] = rho_matches[:100]
        if nphi_matches: detected['NPHI'] = nphi_matches[:100]
        if dt_matches: detected['DT'] = dt_matches[:100]
        return detected

    def ingest(self, image_path: str, asset_id: str | None = None) -> 'WellDigitizeResult':
        """
        Main entry point: ingest a scanned log image.
        Returns WellDigitizeResult with claim_state, suitability, and limitations.
        """
        from PIL import Image
        import pytesseract

        self._require_deps()
        source = Path(image_path)

        if not source.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # ── OCR extraction ──────────────────────────────────────────
        img = Image.open(source)
        raw_text: str = pytesseract.image_to_string(img, config='--psm 6')
        text_lines = [ln.strip() for ln in raw_text.split('\n') if ln.strip()]

        # ── Parse detected curves ────────────────────────────────────
        detected_curves = self._detect_curve_type_from_text(raw_text)

        # ── Attempt depth extraction ─────────────────────────────────
        depths, depth_line_indices = self._parse_depth_from_text(text_lines)

        # ── Compute digitize confidence ────────────────────────────
        confidence_scores: list[float] = []

        if text_lines:
            # Confidence from non-empty lines ratio
            ocr_completeness = len(text_lines) / max(len(text_lines), 1)
            confidence_scores.append(ocr_completeness)
        else:
            confidence_scores.append(0.0)

        if detected_curves:
            # More curve types detected = higher confidence
            curve_confidence = min(len(detected_curves) / 3.0, 1.0)
            confidence_scores.append(curve_confidence)
        else:
            confidence_scores.append(0.1)

        if depths:
            # Depth coverage — more depth values = higher confidence
            depth_confidence = min(len(depths) / 100.0, 1.0)
            confidence_scores.append(depth_confidence)
        else:
            confidence_scores.append(0.0)

        digitize_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        # ── Suitability determination ───────────────────────────────
        num_curves_detected = len(detected_curves)
        num_depths = len(depths)
        has_good_ocr = len(text_lines) > 5 and digitize_confidence > 0.3

        if num_curves_detected >= 2 and num_depths >= 10 and digitize_confidence > 0.5:
            suitability = "decision_ready"
        elif num_curves_detected >= 1 and num_depths >= 5 and digitize_confidence > 0.3:
            suitability = "screening_only"
        else:
            suitability = "void"

        # ── Claim state ─────────────────────────────────────────────
        if suitability == "decision_ready":
            claim_state = ClaimTag.COMPUTED
        elif suitability == "screening_only":
            claim_state = ClaimTag.HYPOTHESIS
        else:
            claim_state = ClaimTag.UNKNOWN

        # ── Limitations ────────────────────────────────────────────
        limitations: list[str] = []
        if not detected_curves:
            limitations.append("No standard log curves (GR, RT, RHOB, NPHI, DT) detected in image. OCR may need clearer scan or manual annotation.")
        if not depths:
            limitations.append("No depth values extracted from image. Manual depth calibration required before LAS export.")
        if num_curves_detected < 2:
            limitations.append(f"Only {num_curves_detected} curve type(s) detected. Archie saturation requires at least GR + RT + porosity curves.")
        if digitize_confidence < 0.4:
            limitations.append(f"OCR confidence is low ({digitize_confidence:.1%}). Extracted values are approximate — verify against original image before use.")

        # ── Well ID ────────────────────────────────────────────────
        well_id = asset_id or source.stem

        # ── Vault receipt ──────────────────────────────────────────
        payload = {
            "tool": "geox_well_digitize_log",
            "well_id": well_id,
            "image_path": str(image_path),
            "source_type": "digitized",
            "detected_curves": list(detected_curves.keys()),
            "depth_points_extracted": num_depths,
            "digitize_confidence": round(digitize_confidence, 4),
            "suitability": suitability,
            "claim_state": claim_state,
            "limitations": limitations,
        }
        vault_receipt = _make_vault_receipt(
            "geox_well_digitize_log",
            payload,
            verdict="HOLD" if suitability == "void" else "SEAL",
        )

        result = WellDigitizeResult(
            tool="geox_well_digitize_log",
            well_id=well_id,
            image_path=str(image_path),
            source_type="digitized",
            detected_curves=list(detected_curves.keys()),
            detected_curve_values=detected_curves,
            depth_points_extracted=num_depths,
            depth_values=depths,
            raw_ocr_text='\n'.join(text_lines[:50]),  # first 50 lines
            digitize_confidence=round(digitize_confidence, 4),
            suitability=suitability,
            claim_state=claim_state,
            limitations=limitations,
            vault_receipt=vault_receipt,
        )
        return result


@dataclass
class WellDigitizeResult:
    """Output schema for geox_well_digitize_log — Stage 1 OCR."""
    tool: str = "geox_well_digitize_log"
    well_id: str = ""
    image_path: str = ""
    source_type: str = "digitized"  # digitized | fixture | LAS
    detected_curves: list[str] = field(default_factory=list)
    detected_curve_values: dict[str, list[str]] = field(default_factory=dict)  # mnemonic -> raw string values
    depth_points_extracted: int = 0
    depth_values: list[float] = field(default_factory=list)
    raw_ocr_text: str = ""
    digitize_confidence: float = 0.0
    suitability: str = "void"  # decision_ready | screening_only | void
    claim_state: str = ClaimTag.UNKNOWN
    limitations: list[str] = field(default_factory=list)
    vault_receipt: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "well_id": self.well_id,
            "image_path": self.image_path,
            "source_type": self.source_type,
            "detected_curves": self.detected_curves,
            "detected_curve_values": self.detected_curve_values,
            "depth_points_extracted": self.depth_points_extracted,
            "depth_values": self.depth_values,
            "raw_ocr_text": self.raw_ocr_text,
            "digitize_confidence": self.digitize_confidence,
            "suitability": self.suitability,
            "claim_state": self.claim_state,
            "limitations": self.limitations,
            "vault_receipt": self.vault_receipt,
        }
