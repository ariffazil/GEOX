"""
Contradiction Scan Hardening Tests
═══════════════════════════════════════════════════════════════════════════════
Verify the red-team engine detects curve-based contradictions and
emits auto-888HOLD when safety thresholds are breached.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import pytest
from geox_mcp.tools.abduction import (
    _contradiction_scan,
    _derive_gr_lithology,
    _derive_rt_lithology,
    _extract_evidence_summary,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Derived lithology helpers
# ═══════════════════════════════════════════════════════════════════════════════

def test_derive_gr_lithology_sand():
    assert _derive_gr_lithology(50) == "sand"
    assert _derive_gr_lithology(74) == "sand"


def test_derive_gr_lithology_shale():
    assert _derive_gr_lithology(121) == "shale"
    assert _derive_gr_lithology(150) == "shale"


def test_derive_gr_lithology_interbedded():
    assert _derive_gr_lithology(90) == "interbedded"
    assert _derive_gr_lithology(120) == "interbedded"


def test_derive_gr_lithology_none():
    assert _derive_gr_lithology(None) is None


def test_derive_rt_lithology_resistive():
    assert _derive_rt_lithology(15) == "resistive"
    assert _derive_rt_lithology(10.1) == "resistive"


def test_derive_rt_lithology_conductive():
    assert _derive_rt_lithology(1.5) == "conductive"
    assert _derive_rt_lithology(0.5) == "conductive"


def test_derive_rt_lithology_intermediate():
    assert _derive_rt_lithology(5) == "intermediate"
    assert _derive_rt_lithology(2) == "intermediate"


# ═══════════════════════════════════════════════════════════════════════════════
# Core contradiction detectors
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def base_hypothesis():
    return {
        "process": "shoreface progradation",
        "mechanism": "sediment supply exceeded accommodation",
        "evidence_for": [],
        "evidence_against": [],
        "expected_additional_signatures": [],
        "missing_tests": [],
        "confidence": "moderate",
        "claim_state": "PROCESS_HYPOTHESIS",
    }


def test_c1_marine_shale_contradiction(base_hypothesis):
    """C1: Marine shale predicted but evidence says terrestrial."""
    hyp = {
        **base_hypothesis,
        "expected_additional_signatures": ["marine_shale_below"],
    }
    evidence = {"has_marine_shale_below": False}
    scan = _contradiction_scan([hyp], evidence)
    assert scan["max_penalty"] == pytest.approx(0.25, abs=0.01)
    assert any("C1" in i for i in scan["contradictions"][0]["issues"])


def test_c2_deepwater_in_shoreface(base_hypothesis):
    """C2: Deepwater process in shoreface context → auto_hold."""
    hyp = {**base_hypothesis, "process": "fan lobe progradation"}
    evidence = {"depo_context": "shoreface"}
    scan = _contradiction_scan([hyp], evidence)
    assert scan["auto_hold"] is True
    assert any(t["code"] == "C2" for t in scan["auto_hold_triggers"])


def test_c3_high_confidence_no_core(base_hypothesis):
    """C3: High confidence without core or biostrat."""
    hyp = {**base_hypothesis, "confidence": "high"}
    evidence = {"has_core": False, "has_biostrat": False}
    scan = _contradiction_scan([hyp], evidence)
    assert any("C3" in i for i in scan["contradictions"][0]["issues"])


def test_c4_incompatible_process_pair():
    """C4: Shoreface and deepwater fan are incompatible."""
    h1 = {
        "process": "shoreface progradation",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    h2 = {
        "process": "deepwater fan lobe",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    scan = _contradiction_scan([h1, h2], {})
    assert any("C4" in i for i in scan["contradictions"][0]["issues"])


# ═══════════════════════════════════════════════════════════════════════════════
# Hardened curve-based detectors (C5-C11)
# ═══════════════════════════════════════════════════════════════════════════════

def test_c5_gr_sand_vs_dn_shale_auto_hold():
    """C5: GR says sand, DN says shale → auto_888HOLD."""
    hyp = {
        "process": "shoreface progradation",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"gr_mean_api": 50, "dn_dominant_lithology": "shale"}
    scan = _contradiction_scan([hyp], evidence)
    assert scan["auto_hold"] is True
    assert any(t["code"] == "C5" for t in scan["auto_hold_triggers"])
    assert any("C5" in i for i in scan["contradictions"][0]["issues"])


def test_c5_gr_shale_vs_dn_sandstone():
    """C5: GR says shale, DN says sandstone → high penalty."""
    hyp = {
        "process": "fluvial channel",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"gr_mean_api": 140, "dn_dominant_lithology": "sandstone"}
    scan = _contradiction_scan([hyp], evidence)
    assert scan["max_penalty"] >= 0.30
    assert any("C5" in i for i in scan["contradictions"][0]["issues"])


def test_c6_gr_shale_vs_rt_resistive_auto_hold():
    """C6: GR says shale, RT says resistive → auto_hold."""
    hyp = {
        "process": "distal shelf",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"gr_mean_api": 130, "rt_mean_ohmm": 25}
    scan = _contradiction_scan([hyp], evidence)
    assert scan["auto_hold"] is True
    assert any(t["code"] == "C6" for t in scan["auto_hold_triggers"])


def test_c7_porosity_disagreement():
    """C7: Density vs sonic porosity disagree by >0.10."""
    hyp = {
        "process": "shoreface progradation",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"phi_density_mean": 0.30, "phi_sonic_mean": 0.15}
    scan = _contradiction_scan([hyp], evidence)
    assert any("C7" in i for i in scan["contradictions"][0]["issues"])


def test_c8_high_vsh_high_phi_auto_hold():
    """C8: Vsh > 0.5 and phi > 0.25 → auto_hold."""
    hyp = {
        "process": "delta front mouth bar",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"vsh_mean": 0.65, "phi_mean": 0.30}
    scan = _contradiction_scan([hyp], evidence)
    assert scan["auto_hold"] is True
    assert any(t["code"] == "C8" for t in scan["auto_hold_triggers"])


def test_c9_funnel_vs_increasing_gr():
    """C9: FUNNEL motif contradicts increasing GR trend."""
    hyp = {
        "process": "shoreface progradation",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"motif": "FUNNEL", "gr_trend": "increasing_upward"}
    scan = _contradiction_scan([hyp], evidence)
    assert any("C9" in i for i in scan["contradictions"][0]["issues"])


def test_c9_bell_vs_decreasing_gr():
    """C9: BELL motif contradicts decreasing GR trend."""
    hyp = {
        "process": "fluvial channel",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"motif": "BELL", "gr_trend": "decreasing_upward"}
    scan = _contradiction_scan([hyp], evidence)
    assert any("C9" in i for i in scan["contradictions"][0]["issues"])


def test_c10_thin_shoreface():
    """C10: Shoreface claimed in < 2m interval."""
    hyp = {
        "process": "shoreface progradation",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"thickness_m": 1.5}
    scan = _contradiction_scan([hyp], evidence)
    assert any("C10" in i for i in scan["contradictions"][0]["issues"])


def test_c11_discontinuous_shoreface():
    """C11: Shoreface incompatible with discontinuous lateral extent."""
    hyp = {
        "process": "shoreface progradation",
        "confidence": "moderate",
        "expected_additional_signatures": [],
    }
    evidence = {"lateral_extent": "discontinuous"}
    scan = _contradiction_scan([hyp], evidence)
    assert any("C11" in i for i in scan["contradictions"][0]["issues"])


def test_no_contradictions_clean_case(base_hypothesis):
    """Clean evidence should produce zero penalties and no auto_hold."""
    evidence = {
        "gr_mean_api": 50,
        "dn_dominant_lithology": "sandstone",
        "rt_mean_ohmm": 20,
        "vsh_mean": 0.15,
        "phi_mean": 0.25,
        "phi_density_mean": 0.24,
        "phi_sonic_mean": 0.25,
        "motif": "FUNNEL",
        "gr_trend": "decreasing_upward",
        "thickness_m": 15,
        "lateral_extent": "continuous",
        "has_core": True,
    }
    scan = _contradiction_scan([base_hypothesis], evidence)
    assert scan["max_penalty"] == pytest.approx(0.0, abs=0.01)
    assert scan["auto_hold"] is False
    assert scan["auto_hold_triggers"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# Evidence summary extraction
# ═══════════════════════════════════════════════════════════════════════════════

def test_extract_evidence_summary_hardened_fields():
    """Expanded evidence summary must capture curve-derived signals."""
    artifacts = [
        {
            "ref": "well_las:TEST-01",
            "metadata": {"has_core": True},
            "payload": {
                "gr_mean": 45,
                "motif": "FUNNEL",
                "dominant_lithology": "sandstone",
                "lithology_fractions": {"sandstone": 0.8},
                "vsh_mean": 0.12,
                "phi_mean": 0.28,
                "rt_mean": 25,
            },
        }
    ]
    summary = _extract_evidence_summary(artifacts)
    assert summary["gr_mean_api"] == 45
    assert summary["gr_motif_class"] == "FUNNEL"
    assert summary["dn_dominant_lithology"] == "sandstone"
    assert summary["vsh_mean"] == 0.12
    assert summary["phi_mean"] == 0.28
    assert summary["rt_mean_ohmm"] == 25
    assert summary["has_core"] is True
