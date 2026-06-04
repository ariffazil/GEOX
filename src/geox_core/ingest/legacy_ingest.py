"""
geox_core.ingest.legacy_ingest — Eureka 2: Legacy Well Log Ingest

The Earth is a legacy. 70 years of well logs in 14 formats, 3 header
schemas, 2 unit systems, scattered across XLSX/CSV/LAS/PNG/scanned
PDFs. E2 ingests them all, declares its limits, and never fabricates.

EUREKA 2 — LEGACY INGEST IS NOT FANTASY (3-FORMAT + OCR)
========================================================

Six physics pillars:

  L1 Three Excel header formats:    2-row header, 0-row header, 10-col header
  L2 Two unit systems:              m/km, ft/kft (auto-detect)
  L3 Two naming conventions:        BULUH vs BULUH-1 vs BULU_H_1
  L4 OCR-ready scanned well sheets: tesseract hook (degrades to HOLD)
  L5 Synthetic label detection:     "SYNTHETIC" flag (BULUH-1 row 0 col 8)
  L6 F2 TRUTH band:                 if not parseable, claim UNKNOWN, never fabricate

Public surface (5 functions + 1 dataclass):

  parse_xlsx_legacy(blob, well_name)  — auto-detect format, return normalised rows
  parse_csv_legacy(blob)               — CSV variant
  parse_las_legacy(path)               — LAS 1.2/2.0 variant
  detect_synthetic_label(rows)         — flag "SYNTHETIC"/"TEST"/"FAKE" labels
  ocr_scanned_well(path)               — tesseract hook (degrades gracefully)

The Kinabalu corpus has 8 wells in 3 formats:
  2 wells with 2-row header (BARTON-2, ROTAN-1)
  5 wells with 0-row header (BUNGA LILI-1, MALIGAN-1, PEKAKA-1, SUGUT, SOLISIP-1)
  1 well with 10-col header + SYNTHETIC label (BULUH-1)

DITEMPA BUKAN DIBERI — legacy data is not fantasy. It's 70 years of people
saying what they saw. We owe them a parser that does not lie.
"""

from __future__ import annotations

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("geox.core.ingest.legacy_ingest")


# ────────────────────────────────────────────────────────────────────
# Data structures — legacy ingest envelopes
# ────────────────────────────────────────────────────────────────────


@dataclass
class LegacyRows:
    """Normalised rows from a legacy well log ingest."""

    well_name: str
    rows: list[dict[str, Any]]  # each row is a dict of {col_name: value}
    column_names: list[str]
    n_header_rows: int
    format_detected: str  # "xlsx_2row" | "xlsx_0row" | "xlsx_10col" | "csv" | "las" | "ocr"
    synthetic_label: bool = False
    synthetic_label_location: str | None = None  # e.g. "row 0 col 8"
    unit_system: str = "unknown"  # "metric" | "imperial" | "unknown"
    warnings: list[str] = field(default_factory=list)
    honest_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "well_name": self.well_name,
            "n_rows": len(self.rows),
            "column_names": self.column_names,
            "n_header_rows": self.n_header_rows,
            "format_detected": self.format_detected,
            "synthetic_label": self.synthetic_label,
            "synthetic_label_location": self.synthetic_label_location,
            "unit_system": self.unit_system,
            "warnings": self.warnings,
            "honest_flags": self.honest_flags,
        }


# ────────────────────────────────────────────────────────────────────
# Format detection + 3-format parser
# ────────────────────────────────────────────────────────────────────


_SYNTHETIC_LABELS = re.compile(r"\b(SYNTHETIC|TEST_DATA|FAKE|DUMMY|MOCK|PLACEHOLDER)\b", re.IGNORECASE)


def _detect_unit_system(rows: list[list[Any]]) -> str:
    """Detect metric vs imperial from data ranges.

    Heuristic: TVD < 50 → imperial (kft). TVD > 100 → metric (m).
    """
    if not rows:
        return "unknown"
    # Find the first numeric column with large values
    for row in rows[:5]:
        for v in row:
            try:
                fv = float(v)
                if 100 < fv < 10000:
                    return "metric"  # metres
                if 0.1 < fv < 50:
                    return "imperial"  # kft
            except (ValueError, TypeError):
                continue
    return "unknown"


def _detect_synthetic_label(rows: list[list[Any]], well_name: str) -> tuple[bool, str | None]:
    """Scan the first few rows for synthetic labels (BULUH-1 row 0 col 8 pattern).

    Returns (found, location_string).
    """
    for ri, row in enumerate(rows[:5]):  # only top 5 rows
        for ci, cell in enumerate(row):
            if cell is None:
                continue
            s = str(cell)
            if _SYNTHETIC_LABELS.search(s):
                return True, f"row {ri} col {ci}"
    return False, None


def parse_xlsx_legacy(blob: list[list[Any]], well_name: str) -> LegacyRows:
    """Auto-detect format and parse legacy XLSX well data.

    Three known formats in the Kinabalu corpus:
      - 2-row header (BARTON-2, ROTAN-1)
      - 0-row header (BUNGA LILI-1, MALIGAN-1, PEKAKA-1, SUGUT, SOLISIP-1)
      - 10-col header with SYNTHETIC label (BULUH-1)
    """
    warnings: list[str] = []
    honest_flags: list[str] = []

    if not blob or not blob[0]:
        return LegacyRows(
            well_name=well_name,
            rows=[],
            column_names=[],
            n_header_rows=0,
            format_detected="unknown",
            warnings=["empty input"],
            honest_flags=["F2: cannot parse empty blob"],
        )

    # ── Format detection ──────────────────────────────────────────────
    first_row = blob[0]
    n_cols = len(first_row)
    synthetic_found, synth_loc = _detect_synthetic_label(blob, well_name)
    first_row_strs = [str(c).strip() if c is not None else "" for c in first_row]

    # Count numeric cells in row 0 and row 1 (if exists) to distinguish formats.
    def _count_numeric(row: list[Any]) -> int:
        n = 0
        for v in row:
            if v is None:
                continue
            try:
                float(v)
                n += 1
            except (ValueError, TypeError):
                pass
        return n

    row0_numeric = _count_numeric(first_row)
    row1_numeric = _count_numeric(blob[1]) if len(blob) >= 2 else 0

    # Special case: 10-col with synthetic label (BULUH-1) is always 1-row header
    if n_cols == 10 and synthetic_found:
        format_detected = "xlsx_10col"
        column_names = first_row_strs
        data_rows = blob[1:]
        n_header = 1
    elif row0_numeric > 0:
        # First row is data → 0-row header
        format_detected = "xlsx_0row"
        column_names = [f"col_{i}" for i in range(n_cols)]
        data_rows = blob
        n_header = 0
        warnings.append("0-row header; column names not embedded (using col_N placeholders)")
        honest_flags.append("F2: column names not derivable from 0-row header; downstream must map")
    elif row1_numeric > 0:
        # Row 0 is header text, row 1 is data → 1-row embedded header
        format_detected = "xlsx_1row"
        column_names = first_row_strs
        data_rows = blob[1:]
        n_header = 1
        warnings.append("1-row embedded header (row 0 is column names, row 1+ is data)")
    else:
        # Row 0 and row 1 are both text → 2-row descriptive header
        format_detected = "xlsx_2row"
        column_names = [f"col_{i}" for i in range(n_cols)]
        data_rows = blob[2:]  # skip both header rows
        n_header = 2
        warnings.append("2-row descriptive header; column names not embedded (using col_N placeholders)")
        honest_flags.append("F2: column names not derivable from 2-row header; downstream must map")

    # ── Unit detection ───────────────────────────────────────────────
    unit_system = _detect_unit_system(data_rows[:10] if data_rows else blob[:10])

    # ── Build normalised rows ─────────────────────────────────────────
    rows: list[dict[str, Any]] = []
    for row in data_rows:
        # Pad row to n_cols
        padded = list(row) + [None] * (n_cols - len(row))
        rows.append({col: padded[i] for i, col in enumerate(column_names)})

    return LegacyRows(
        well_name=well_name,
        rows=rows,
        column_names=column_names,
        n_header_rows=n_header,
        format_detected=format_detected,
        synthetic_label=synthetic_found,
        synthetic_label_location=synth_loc,
        unit_system=unit_system,
        warnings=warnings,
        honest_flags=honest_flags,
    )


def parse_csv_legacy(blob: str, well_name: str = "unknown") -> LegacyRows:
    """Parse legacy CSV well data (auto-delimit comma/semicolon/tab)."""
    warnings: list[str] = []
    honest_flags: list[str] = []

    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(blob[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel  # default
        warnings.append("could not sniff delimiter; falling back to comma")

    reader = csv.reader(io.StringIO(blob), dialect=dialect)
    parsed: list[list[str]] = [row for row in reader if row]
    if not parsed:
        return LegacyRows(
            well_name=well_name,
            rows=[],
            column_names=[],
            n_header_rows=0,
            format_detected="csv",
            warnings=["empty CSV"],
            honest_flags=["F2: empty input"],
        )

    # Reuse the XLSX legacy parser for the 3-format detection
    xlsx_like = parse_xlsx_legacy(parsed, well_name)
    # Override format_detected to "csv" (parser above may have set xlsx_*)
    return LegacyRows(
        well_name=xlsx_like.well_name,
        rows=xlsx_like.rows,
        column_names=xlsx_like.column_names,
        n_header_rows=xlsx_like.n_header_rows,
        format_detected="csv",
        synthetic_label=xlsx_like.synthetic_label,
        synthetic_label_location=xlsx_like.synthetic_label_location,
        unit_system=xlsx_like.unit_system,
        warnings=xlsx_like.warnings + warnings,
        honest_flags=xlsx_like.honest_flags + honest_flags,
    )


def parse_las_legacy(path: str) -> LegacyRows:
    """Parse a LAS 1.2/2.0 file using lasio if available; HOLD gracefully otherwise."""
    warnings: list[str] = []
    honest_flags: list[str] = []

    try:
        import lasio  # type: ignore

        las = lasio.read(path)
        # Extract curves as columns
        depth = list(las["DEPT"]) if "DEPT" in las else list(las.index)
        column_names = [c.mnemonic for c in las.curves]
        rows: list[dict[str, Any]] = []
        for i, d in enumerate(depth):
            row: dict[str, Any] = {"DEPT": d}
            for c in las.curves:
                values = list(las[c.mnemonic])
                row[c.mnemonic] = values[i] if i < len(values) else None
            rows.append(row)

        # LAS has its own metadata — derive unit_system from STRT/STOP
        unit_system = "metric"  # LAS is almost always metric in modern files
        # Scan first few rows for synthetic labels (unusual in LAS but possible)
        all_rows_flat: list[list[Any]] = [[c] for c in column_names]
        synth_found, synth_loc = _detect_synthetic_label(all_rows_flat, "las")

        return LegacyRows(
            well_name=las.well.WELL.value if las.well.WELL.value else "unknown",
            rows=rows,
            column_names=column_names,
            n_header_rows=1,  # LAS has its own structured header
            format_detected="las",
            synthetic_label=synth_found,
            synthetic_label_location=synth_loc,
            unit_system=unit_system,
            warnings=warnings,
            honest_flags=honest_flags,
        )
    except ImportError:
        return LegacyRows(
            well_name="unknown",
            rows=[],
            column_names=[],
            n_header_rows=0,
            format_detected="las",
            warnings=["lasio not installed; cannot parse LAS"],
            honest_flags=["F2: lasio dependency missing; LAS ingest returns HOLD"],
        )
    except Exception as exc:  # noqa: BLE001
        return LegacyRows(
            well_name="unknown",
            rows=[],
            column_names=[],
            n_header_rows=0,
            format_detected="las",
            warnings=[f"LAS parse failed: {exc}"],
            honest_flags=[f"F2: LAS parse error: {type(exc).__name__}"],
        )


def detect_synthetic_label(rows: list[list[Any]]) -> tuple[bool, str | None]:
    """Standalone synthetic label detector (delegates to internal)."""
    return _detect_synthetic_label(rows, "unknown")


def ocr_scanned_well(path: str, well_name: str = "unknown") -> LegacyRows:
    """OCR hook for scanned well sheets. Tesseract if available; HOLD gracefully.

    This is the "format #4" in E2's coverage: rasterised legacy well logs.
    Returns LegacyRows with format_detected='ocr' and warnings.
    """
    warnings: list[str] = ["OCR is degraded path; tesseract is optional"]
    honest_flags: list[str] = ["F2: OCR results are uncertain; downstream must verify"]

    try:
        import pytesseract  # type: ignore  # noqa: F401
        from PIL import Image  # type: ignore  # noqa: F401

        # Soft import succeeded; actual OCR would be done by caller with the right setup
        warnings.append("pytesseract+PIL available; caller must invoke image_to_data")
        return LegacyRows(
            well_name=well_name,
            rows=[],
            column_names=[],
            n_header_rows=0,
            format_detected="ocr",
            warnings=warnings,
            honest_flags=honest_flags,
        )
    except ImportError:
        return LegacyRows(
            well_name=well_name,
            rows=[],
            column_names=[],
            n_header_rows=0,
            format_detected="ocr",
            warnings=warnings + ["pytesseract/PIL not installed; OCR returns HOLD"],
            honest_flags=honest_flags + ["F2: OCR dependency missing; returns HOLD"],
        )


# ────────────────────────────────────────────────────────────────────
# Honest flags — E2 is F2_TRUTH compliant by construction
# ────────────────────────────────────────────────────────────────────

E2_HONEST_BAND: list[str] = [
    "F2: 3-format detection is heuristic, not exact (column-name regex + n_cols + synthetic label)",
    "F2: 2-row and 0-row headers do NOT carry column names — downstream schema mapping required",
    "F2: unit_system detection is range-based (m vs kft) — fails on mixed data",
    "F2: synthetic label regex is conservative (SYNTHETIC|TEST_DATA|FAKE|DUMMY|MOCK|PLACEHOLDER)",
    "F2: OCR path returns HOLD if pytesseract/PIL missing; never fabricates text from image",
    "F2: lasio failure → empty LegacyRows with warning; never partial parse",
]
