"""
tests/test_authority_label_hygiene.py
Unit tests for check_authority_label_hygiene.py
Task 6: Authority label hygiene in documents.
"""

import sys
sys.path.insert(0, "/root/scripts")

from check_authority_label_hygiene import check_authority_label_hygiene


def test_reject_external_ai_conflated_with_f13():
    bad_doc = "Dokumen ini melalui semakan F13: Claude 3.5 Sonnet pada tarikh 2026-11-02."
    clean, violations = check_authority_label_hygiene(bad_doc)
    assert not clean
    assert any("conflated" in v for v in violations)


def test_reject_bare_f13_without_receipt():
    bad_doc = "Laporan ini diluluskan di bawah semakan F13 tanpa resit atau tandatangan."
    clean, violations = check_authority_label_hygiene(bad_doc)
    assert not clean
    assert any("signed F13/SEAL receipt ID" in v for v in violations)


def test_accept_external_reviewer_named_honestly():
    good_doc = "Dokumen ini melalui semakan luar: Claude pada 2026-11-02. Pengesahan teknikal bebas."
    clean, violations = check_authority_label_hygiene(good_doc)
    assert clean
    assert len(violations) == 0


def test_accept_f13_with_signed_receipt():
    good_doc = (
        "Dokumen ini dimeterai di bawah semakan F13.\n"
        "Receipt ID: F13-98fe81ab23cd45ef (ditandatangani oleh Sovereign Arif)."
    )
    clean, violations = check_authority_label_hygiene(good_doc)
    assert clean
    assert len(violations) == 0
