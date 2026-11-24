"""Self-tests for the corpus generator — no GEOX dependency required."""

from __future__ import annotations

import hashlib

from geox_ugly_corpus.contracts import parse_las
from geox_ugly_corpus.generate import build_corpus, manifest_digest


def test_generation_is_deterministic(tmp_path):
    first = build_corpus(tmp_path / "a")
    second = build_corpus(tmp_path / "b")
    assert manifest_digest(first) == manifest_digest(second)
    assert [(f.name, f.sha256) for f in first] == [(f.name, f.sha256) for f in second]


def test_manifest_hashes_match_bytes(tmp_path):
    fixtures = build_corpus(tmp_path)
    assert len(fixtures) == 7
    for fixture in fixtures:
        assert hashlib.sha256(fixture.path.read_bytes()).hexdigest() == fixture.sha256


def test_every_fixture_is_parseable_and_stamped_synthetic(tmp_path):
    for fixture in build_corpus(tmp_path):
        curves, rows = parse_las(fixture.path)
        assert "DEPT" in curves
        assert rows, f"{fixture.name} has no data rows"
        text = fixture.path.read_text(encoding="ascii")
        assert "SYNTHETIC-UGLY-CORPUS" in text
        assert "SEED 20261124" in text
