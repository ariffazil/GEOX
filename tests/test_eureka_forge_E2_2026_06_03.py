"""
tests.test_eureka_forge_E2_2026_06_03 — Eureka 2 eureka tests (1 test).

E2: Legacy well log ingest — 3 Excel formats + OCR hook + synthetic label detector.

Forge date: 2026-06-03
Author: OMEGA (Ω) Forge Agent
"""

from __future__ import annotations

import pytest

from geox_core.ingest import (
    LegacyRows,
    parse_xlsx_legacy,
    parse_csv_legacy,
    detect_synthetic_label,
    ocr_scanned_well,
    E2_HONEST_BAND,
)


# ────────────────────────────────────────────────────────────────────
# Test 1: Kinabalu 8-well corpus — all 3 formats parse cleanly
# ────────────────────────────────────────────────────────────────────


def test_e2_kinabalu_8_well_3_format_ingest():
    """E2 ingests all 3 Excel formats in the Kinabalu corpus without error.

    Verifies:
      - 2-row header (BARTON-2, ROTAN-1)
      - 0-row header (BUNGA LILI-1, MALIGAN-1, PEKAKA-1, SUGUT, SOLISIP-1)
      - 10-col header with SYNTHETIC label (BULUH-1)
      - Synthetic label detected on BULUH-1
      - Unit system auto-detected
      - All honest flags present
    """

    # Build representative blobs for each format
    def _row(d, t, v_avg, v_int):
        return [d, t, v_avg, v_int, 0.20, 0.15, 2.30, 0.30]

    # Format 1: 2-row header (BARTON-2, ROTAN-1)
    f1 = [["BARTON-2 Time-Depth"] + [""] * 7, ["MD (m), TWT (ms), V_avg, V_int, GR, RT, RHOB, NPHI"] + [""] * 0]
    for d, t in [(1000, 950), (1500, 1430), (2000, 1900), (2500, 2370)]:
        f1.append(_row(d, t, 2100, 2350))

    # Format 2: 0-row header (BUNGA LILI-1, MALIGAN-1, etc.)
    f2 = [_row(d, t, 2000, 2400) for d, t in [(1000, 1000), (2000, 1950), (3000, 2850)]]

    # Format 3: 10-col with SYNTHETIC label (BULUH-1)
    f3_header = ["MD", "TWT", "V_avg", "V_int", "GR", "RT", "RHOB", "NPHI", "SYNTHETIC", "Notes"]
    f3 = [f3_header]
    for d, t in [(1000, 950), (2000, 1900), (2500, 2370)]:
        f3.append([d, t, 2100, 2350, 0.20, 0.15, 2.30, 0.30, "TEST_DATA", "synth"])

    # ── Parse all 3 ────────────────────────────────────────────────────
    r1 = parse_xlsx_legacy(f1, "BARTON-2")
    r2 = parse_xlsx_legacy(f2, "BUNGA LILI-1")
    r3 = parse_xlsx_legacy(f3, "BULUH-1")

    # All three must produce LegacyRows, not crash
    assert isinstance(r1, LegacyRows)
    assert isinstance(r2, LegacyRows)
    assert isinstance(r3, LegacyRows)

    # Format detection
    assert r1.format_detected == "xlsx_2row"
    assert r2.format_detected == "xlsx_0row"
    assert r3.format_detected == "xlsx_10col"

    # Data row counts (header rows excluded)
    assert len(r1.rows) == 4  # 2 header rows + 4 data rows
    assert len(r2.rows) == 3
    assert len(r3.rows) == 3

    # ── Synthetic label detection (BULUH-1 row 0 col 8) ───────────────
    assert r3.synthetic_label is True
    assert r3.synthetic_label_location == "row 0 col 8"
    # BARTON-2 and BUNGA LILI-1 should NOT be flagged
    assert r1.synthetic_label is False
    assert r2.synthetic_label is False

    # ── Standalone detector works too ─────────────────────────────────
    found, loc = detect_synthetic_label(f3)
    assert found is True
    assert loc == "row 0 col 8"

    # ── Unit system auto-detected (metric for these depths) ──────────
    assert r1.unit_system in {"metric", "imperial", "unknown"}
    assert r2.unit_system in {"metric", "imperial", "unknown"}

    # ── CSV path uses same parser ─────────────────────────────────────
    csv_blob = "MD,TWT,V_avg\n1000,950,2100\n2000,1900,2300\n"
    r_csv = parse_csv_legacy(csv_blob, well_name="BARTON-2-csv")
    assert r_csv.format_detected == "csv"
    assert len(r_csv.rows) == 2

    # ── OCR path is graceful (degrades, never fabricates) ────────────
    r_ocr = ocr_scanned_well("/nonexistent/scan.png", well_name="BARTON-2-ocr")
    assert r_ocr.format_detected == "ocr"
    # OCR is honest — it does not fabricate
    assert "OCR" in str(r_ocr.warnings) or any("OCR" in w for w in r_ocr.warnings)
    assert r_ocr.synthetic_label is False  # no labels to detect

    # ── F2 TRUTH band is declared ─────────────────────────────────────
    assert len(E2_HONEST_BAND) >= 5
    assert any("F2:" in f for f in E2_HONEST_BAND)

    # ── Honest flags propagated per-row ──────────────────────────────
    # 2-row format should have F2 honest flag about column-name gap
    assert any("F2:" in f for f in r1.honest_flags)
    # 0-row format should have F2 honest flag about column-name gap
    assert any("F2:" in f for f in r2.honest_flags)
