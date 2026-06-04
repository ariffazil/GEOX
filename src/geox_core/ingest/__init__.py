"""
geox_core.ingest — Legacy well log ingestion (E2).

Public surface (3 parsers + 1 detector + 1 OCR hook):

  parse_xlsx_legacy(blob, well_name)  — auto-detect 3 Excel formats
  parse_csv_legacy(blob)               — CSV variant
  parse_las_legacy(path)               — LAS 1.2/2.0 variant
  detect_synthetic_label(rows)         — standalone detector
  ocr_scanned_well(path)               — tesseract hook (degrades gracefully)
  LegacyRows                           — result dataclass with honest flags
"""

from geox_core.ingest.legacy_ingest import (
    E2_HONEST_BAND,
    LegacyRows,
    detect_synthetic_label,
    ocr_scanned_well,
    parse_csv_legacy,
    parse_las_legacy,
    parse_xlsx_legacy,
)

__all__ = [
    "LegacyRows",
    "parse_xlsx_legacy",
    "parse_csv_legacy",
    "parse_las_legacy",
    "detect_synthetic_label",
    "ocr_scanned_well",
    "E2_HONEST_BAND",
]
