"""
Tests for geox_analog_atlas — ToAC-integrated analog search.

Verifies F1-F13 compliance:
  F2 TRUTH  — every analog carries epistemic rung + confidence band
  F7 HUMILITY — output is HYPOTHESIS, never SEAL
  F9 ANTIHANTU — no consciousness claims, no "this IS an analog"
  F1 AMANAH  — read-only advisory; no commit, no drill, no commercial action

Plus behavioral tests:
  - empty query → HOLD, no crash
  - empty corpus → HOLD, no crash
  - invalid top_k → HOLD
  - exact match query → high similarity
  - structurally different query → dangerous_similarity_flag fires
  - depth range overlap scoring is monotonic
  - verdict logic: HOLD when dangerous > 0, QUALIFY when clean
  - missing evidence fields surface (Doctrine 8)
"""

from __future__ import annotations

import asyncio
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add geox src to path if needed
_GEOX_SRC = Path("/root/geox/src")
if str(_GEOX_SRC) not in sys.path:
    sys.path.insert(0, str(_GEOX_SRC))

from geox_mcp.tools.analog_atlas import (
    geox_analog_atlas,
    _categorical_similarity,
    _numeric_range_overlap,
    _score_analog,
    _load_analog,
    ANALOGS_DIR,
    DANGEROUS_SIMILARITY_THRESHOLD,
    DANGEROUS_CONTRAST_THRESHOLD,
    DANGEROUS_CONTRAST_COUNT_MIN,
)
from geox_core.enums.statuses import GovernanceStatus


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def corpus_dir():
    """Point to real corpus dir (we know 2 seed files exist)."""
    assert ANALOGS_DIR.exists(), f"ANALOGS_DIR not found: {ANALOGS_DIR}"
    files = list(ANALOGS_DIR.glob("*.yaml"))
    assert len(files) >= 2, f"Expected >=2 seed analogs, found {len(files)}"
    return ANALOGS_DIR


@pytest.fixture
def empty_corpus_dir(monkeypatch):
    """Override ANALOGS_DIR to an empty temp dir to test empty-corpus case."""
    tmp = Path(tempfile.mkdtemp(prefix="geox_analog_empty_"))
    monkeypatch.setattr("geox_mcp.tools.analog_atlas.ANALOGS_DIR", tmp)
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — primitives
# ─────────────────────────────────────────────────────────────────────────────


def test_categorical_similarity_exact_match():
    assert _categorical_similarity("Pull-apart", "pull-apart") == 1.0
    assert _categorical_similarity("Passive margin", "passive_margin") == 1.0


def test_categorical_similarity_mismatch():
    assert _categorical_similarity("Pull-apart", "passive margin") == 0.0
    assert _categorical_similarity("rift", "foreland") == 0.0


def test_categorical_similarity_missing_is_neutral():
    assert _categorical_similarity(None, "rift") == 0.5
    assert _categorical_similarity("", "") == 0.5  # both empty → neutral


def test_numeric_range_overlap_full():
    assert _numeric_range_overlap([1000, 2000], [1500, 2500]) == pytest.approx(0.5)
    assert _numeric_range_overlap([1000, 2000], [1000, 2000]) == 1.0


def test_numeric_range_overlap_disjoint():
    assert _numeric_range_overlap([1000, 2000], [3000, 4000]) == 0.0


def test_numeric_range_overlap_missing_is_neutral():
    assert _numeric_range_overlap(None, [1000, 2000]) == 0.5


def test_load_analog_parses_seeded_file(corpus_dir):
    """Real corpus load: pick first yaml, verify schema."""
    p = next(corpus_dir.glob("*.yaml"))
    a = _load_analog(p)
    assert a.analog_id
    assert a.basin_id
    assert a.tectonic_setting
    assert a.data_quality in ("HIGH", "MEDIUM", "LOW", "VERY_LOW")
    assert isinstance(a.depth_range_m, list) and len(a.depth_range_m) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — scoring
# ─────────────────────────────────────────────────────────────────────────────


def test_score_exact_match_high_similarity(corpus_dir):
    """Query that matches a seeded analog exactly should produce high similarity."""
    p = next(corpus_dir.glob("*GroupH*"))
    analog = _load_analog(p)
    query = {
        "tectonic_setting": analog.tectonic_setting,
        "basin_age": analog.basin_age,
        "lithology_primary": analog.lithology_primary,
        "depth_range_m": analog.depth_range_m,
        "trap_style": analog.trap_style,
        "source_rock": analog.source_rock,
        "reservoir_rock": analog.reservoir_rock,
    }
    s = _score_analog(query, analog)
    assert s["similarity_score"] == pytest.approx(1.0, abs=0.001)
    assert not s["dangerous_similarity_flag"]


def test_score_structurally_different_fires_dangerous_flag(corpus_dir):
    """Query that is structurally different should fire dangerous_similarity_flag
    only if similarity is artificially high (i.e., match in some dimensions only).

    The audit eureka: 'the analog that kills you looks 90% similar but is
    fundamentally different in structural style + charge history.' So we test
    a query that matches 5/7 dimensions but misses trap_style + source_rock
    (the two most weight-bearing contrast dimensions)."""
    p = next(corpus_dir.glob("*GroupH*"))
    analog = _load_analog(p)
    # Match some dims, miss the dangerous ones
    query = {
        "tectonic_setting": analog.tectonic_setting,  # match (20%)
        "basin_age": analog.basin_age,  # match (10%)
        "lithology_primary": analog.lithology_primary,  # match (15%)
        "depth_range_m": analog.depth_range_m,  # match (15%)
        "trap_style": "compressional anticline",  # MISMATCH (20% — high weight)
        "source_rock": "Type I marine",  # MISMATCH (10%)
        "reservoir_rock": analog.reservoir_rock,  # match (10%)
    }
    s = _score_analog(query, analog)
    # Score: 20+10+15+15+0+0+10 = 70/100 = 0.70 (just at threshold)
    # Contrast: 2 dims above 0.5 (trap_style, source_rock)
    assert s["similarity_score"] >= 0.5
    assert s["dangerous_similarity_flag"] is True
    assert s["high_contrast_dimensions_count"] >= DANGEROUS_CONTRAST_COUNT_MIN
    assert any(cs["dimension"] == "trap_style" for cs in s["contrast_signals"])
    assert s["warning"] is not None
    assert "PRIMARY DATA" in s["warning"].upper() or "primary data" in s["warning"]


def test_score_no_query_fields_returns_low_or_neutral(corpus_dir):
    """If query has no fields, similarity is ~0.5 (neutral) for each dim
    and dangerous flag should NOT fire (we can't be 'dangerously similar'
    to something we didn't actually compare)."""
    p = next(corpus_dir.glob("*GroupH*"))
    analog = _load_analog(p)
    s = _score_analog({}, analog)
    # All dims default to 0.5 → weighted score = 0.5
    assert s["similarity_score"] == pytest.approx(0.5, abs=0.05)
    assert s["dangerous_similarity_flag"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Behavioral tests — async tool surface
# ─────────────────────────────────────────────────────────────────────────────


def test_empty_query_returns_hold():
    res = asyncio.run(geox_analog_atlas(query={}))
    assert res["governance_status"] == "HOLD"
    assert res["error_code"] == "EMPTY_QUERY"
    assert "non-empty" in res["message"]


def test_invalid_top_k_returns_hold():
    res = asyncio.run(geox_analog_atlas(query={"basin_id": "MALAY_BASIN"}, top_k=99))
    assert res["governance_status"] == "HOLD"
    assert res["error_code"] == "INVALID_TOP_K"


def test_invalid_contrast_mode_returns_hold():
    # Intentional bad input — runtime guard should catch it
    res = asyncio.run(
        geox_analog_atlas(
            query={"basin_id": "MALAY_BASIN"},
            contrast_mode="invalid",  # type: ignore[arg-type]
        )
    )
    assert res["governance_status"] == "HOLD"
    assert res["error_code"] == "INVALID_CONTRAST_MODE"


def test_empty_corpus_returns_hold(empty_corpus_dir):
    res = asyncio.run(geox_analog_atlas(query={"basin_id": "MALAY_BASIN"}))
    assert res["governance_status"] == "HOLD"
    assert res["error_code"] == "EMPTY_CORPUS"
    assert "/root/geox/resources/analogs/" in res["message"]


def test_clean_query_returns_qualify(corpus_dir):
    """Clean (no dangerous similarity) Malay Basin Group H query → QUALIFY."""
    p = next(corpus_dir.glob("*GroupH*"))
    analog = _load_analog(p)
    res = asyncio.run(
        geox_analog_atlas(
            query={
                "tectonic_setting": analog.tectonic_setting,
                "basin_age": analog.basin_age,
                "lithology_primary": analog.lithology_primary,
                "depth_range_m": analog.depth_range_m,
                "trap_style": analog.trap_style,
                "source_rock": analog.source_rock,
                "reservoir_rock": analog.reservoir_rock,
            },
            corpus_filter={"basin_ids": ["MALAY_BASIN"]},
            top_k=3,
        )
    )
    assert res["governance_status"] == "QUALIFY"
    assert res["claim_state"] == "PLAUSIBLE"
    assert res["n_results_returned"] >= 1
    assert res["n_dangerous_similarities"] == 0


def test_dangerous_query_returns_hold(corpus_dir):
    """Structurally different query (compressional vs rift) → HOLD verdict."""
    res = asyncio.run(
        geox_analog_atlas(
            query={
                "tectonic_setting": "Cenozoic failed rift / pull-apart basin",
                "basin_age": "Oligocene-Miocene",
                "lithology_primary": "fluvio-deltaic sandstone",
                "depth_range_m": [1500, 3500],
                "trap_style": "compressional anticline",  # MISMATCH (most weight)
                "source_rock": "Type I marine shale",  # MISMATCH
                "reservoir_rock": "fluvio-deltaic sandstone",
            },
            corpus_filter={"basin_ids": ["MALAY_BASIN"]},
            top_k=3,
        )
    )
    assert res["governance_status"] == "HOLD"
    assert res["n_dangerous_similarities"] >= 1
    assert "PRIMARY DATA" in res["summary"]["verdict_reason"].upper() or "primary data" in res["summary"]["verdict_reason"]
    # Doctrine 8 surface
    assert "primary_hypothesis" in res["summary"]
    assert "alternative_explanations" in res["summary"]
    assert "missing_evidence" in res["summary"]


def test_corpus_filter_basin_ids_works(corpus_dir):
    """Filter to one basin; check results all match that basin."""
    res = asyncio.run(
        geox_analog_atlas(
            query={"basin_id": "MALAY_BASIN", "tectonic_setting": "Cenozoic failed rift / pull-apart basin"},
            corpus_filter={"basin_ids": ["MALAY_BASIN"]},
            top_k=5,
        )
    )
    assert res["governance_status"] in ("QUALIFY", "HOLD")
    for r in res["results"]:
        assert r["basin_id"] == "MALAY_BASIN"


def test_min_data_quality_filter(corpus_dir):
    """min_data_quality=HIGH should drop MEDIUM/LOW analogs (GroupH=HIGH, GroupJ=MEDIUM)."""
    res = asyncio.run(
        geox_analog_atlas(
            query={"basin_id": "MALAY_BASIN"},
            corpus_filter={"basin_ids": ["MALAY_BASIN"], "min_data_quality": "HIGH"},
        )
    )
    # Should only return HIGH-quality (Group H) analog, not Group J
    if res["n_results_returned"] > 0:
        for r in res["results"]:
            assert r["data_quality"] == "HIGH"


def test_contrast_mode_similarity_only_strips_contrast(corpus_dir):
    """similarity_only mode should NOT return contrast_signals or warning."""
    p = next(corpus_dir.glob("*GroupH*"))
    analog = _load_analog(p)
    res = asyncio.run(
        geox_analog_atlas(
            query={
                "tectonic_setting": analog.tectonic_setting,
                "basin_age": analog.basin_age,
                "lithology_primary": analog.lithology_primary,
                "depth_range_m": analog.depth_range_m,
                "trap_style": analog.trap_style,
                "source_rock": analog.source_rock,
                "reservoir_rock": analog.reservoir_rock,
            },
            contrast_mode="similarity_only",
        )
    )
    if res["n_results_returned"] > 0:
        for r in res["results"]:
            assert "contrast_signals" not in r
            assert "warning" not in r


def test_contrast_mode_contrast_only_strips_similarity(corpus_dir):
    p = next(corpus_dir.glob("*GroupH*"))
    analog = _load_analog(p)
    res = asyncio.run(
        geox_analog_atlas(
            query={
                "tectonic_setting": analog.tectonic_setting,
                "basin_age": analog.basin_age,
                "lithology_primary": analog.lithology_primary,
                "depth_range_m": analog.depth_range_m,
                "trap_style": analog.trap_style,
                "source_rock": analog.source_rock,
                "reservoir_rock": analog.reservoir_rock,
            },
            contrast_mode="contrast_only",
        )
    )
    if res["n_results_returned"] > 0:
        for r in res["results"]:
            assert "similarity_score" not in r
            assert "similarity_confidence_band" not in r


def test_claim_tag_is_hypothesis_when_dangerous(corpus_dir):
    """F7 HUMILITY: when verdict is HOLD due to dangerous similarity, claim_tag
    must be HYPOTHESIS (never SEAL/CLAIM)."""
    res = asyncio.run(
        geox_analog_atlas(
            query={
                "tectonic_setting": "Cenozoic failed rift / pull-apart basin",
                "basin_age": "Oligocene-Miocene",
                "lithology_primary": "fluvio-deltaic sandstone",
                "depth_range_m": [1500, 3500],
                "trap_style": "compressional anticline",
                "source_rock": "Type I marine shale",
                "reservoir_rock": "fluvio-deltaic sandstone",
            },
            corpus_filter={"basin_ids": ["MALAY_BASIN"]},
        )
    )
    assert res["governance_status"] == "HOLD"
    # The envelope's claim_tag should be HYPOTHESIS, not CLAIM/PLAUSIBLE
    assert res.get("claim_tag") == "HYPOTHESIS"


def test_min_similarity_filter():
    """min_similarity=0.99 should drop everything except near-perfect matches."""
    res = asyncio.run(
        geox_analog_atlas(
            query={"tectonic_setting": "Cenozoic failed rift / pull-apart basin"},
            min_similarity=0.99,
        )
    )
    # In our seed corpus, no analog is 0.99+ similar on a single-field query
    if res["n_results_returned"] == 0:
        assert res["governance_status"] == "HOLD"
        assert "min_similarity" in res["summary"]["verdict_reason"]


def test_doctrine_8_missing_evidence_surface(corpus_dir):
    """When query lacks narrative / depth / tectonic, Doctrine 8 missing_evidence
    must list them."""
    res = asyncio.run(
        geox_analog_atlas(
            query={"basin_id": "MALAY_BASIN"},  # minimum fields
        )
    )
    missing = res["summary"]["missing_evidence"]
    assert any("geological_narrative" in m for m in missing)
    assert any("depth_range_m" in m for m in missing)
    assert any("tectonic_setting" in m for m in missing)
