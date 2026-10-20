"""Fail-if tests for docs/VISION_TO_EVIDENCE_PROTOCOL.md (GEOX-VIS v1).

consumer: geox_extract_display_proxy / geox_extract_native_trace + VSS vision lanes
failure class: BEKANTAN-1 (visual output fabricating earth claims)
Rule under test: vision proposes, GEOX constrains; pixels never self-validate;
uncalibrated extraction is SPEC at best; SPEC/UNMEASURED never reaches SEAL.
"""

import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = json.load(open(os.path.join(ROOT, "docs", "visual_extraction.schema.json")))

try:
    import jsonschema

    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False


def epistemic_ceiling(rec):
    """The ladder. Native+lineage -> OBS/DER; calibrated proxy -> INT;
    uncalibrated screenshot/render -> SPEC. Never OBS from pixels alone."""
    vc = rec["visual_context"]
    cal = rec["calibration"]
    src = rec["source"]["source_type"]
    calibrated = (
        cal.get("coordinate_reference_system") not in (None, "", "unknown")
        and len(cal.get("calibration_points") or []) >= 2
        and cal.get("uncertainty_model")
    )
    if src == "screenshot" or vc.get("display_transform") == "unknown" and not calibrated:
        return "SPEC"
    if vc["native_or_display"] == "display_proxy":
        return "INT" if calibrated else "SPEC"
    return "OBS_DER_ALLOWED" if calibrated or src != "screenshot" else "SPEC"


def violations(rec):
    v = []
    if epistemic_ceiling(rec) == "SPEC" and rec["claim"]["epistemic_class"] in ("OBS", "DER"):
        v.append("pixel-claim exceeds epistemic ceiling (Bekantan class)")
    if rec["claim"].get("preferred_hypothesis") is not None:
        v.append("preferred_hypothesis must be null without human-gate receipt")
    if not rec["calibration"].get("uncertainty_model"):
        v.append("uncertainty absent")
    if rec["constraints"]["status"] in ("PASS",) and len(rec["calibration"].get("calibration_points") or []) < 2:
        v.append("PASS without >=2 calibration anchors per measured axis")
    if rec["claim"]["epistemic_class"] in ("SPEC",) or rec["constraints"]["status"] == "UNMEASURED":
        if rec["seal_eligibility"]["eligible_for_scientific_warrant"]:
            v.append("SPEC/UNMEASURED reached SEAL")
    if rec.get("_verify_source") and rec["_verify_source"] == rec["source"]["artifact_uri"]:
        v.append("visual source verifies itself")
    return v


def base(**over):
    rec = {
        "extraction_id": "GEOX-VIS-000001",
        "source": {
            "artifact_uri": "segy://line42.sgy",
            "artifact_sha256": "a" * 64,
            "source_type": "seismic_section",
            "source_owner": "public",
        },
        "visual_context": {
            "pixel_bounds": [0, 0, 100, 100],
            "native_or_display": "native",
            "extraction_method": "CV",
            "operator": "333-AGI",
        },
        "calibration": {
            "horizontal_axis": "distance_km",
            "vertical_axis": "TWT_ms",
            "coordinate_reference_system": "local_grid",
            "calibration_points": [{"pixel": [0, 0], "world": [0.0, 0.0]}, {"pixel": [100, 100], "world": [10.0, 2000.0]}],
            "rms_error": 1.2,
            "uncertainty_model": "rms-propagated",
        },
        "claim": {
            "assertion_id": "GEOX-ASSERT-000001",
            "proposition": "horizon A at 1.2s",
            "epistemic_class": "DER",
            "claim_scope": "line_section",
            "extracted_geometry": "polyline",
            "preferred_hypothesis": None,
        },
        "constraints": {"required_independent_checks": ["spatial", "physics"], "status": "WARN"},
        "seal_eligibility": {"eligible_for_scientific_warrant": False, "missing": ["independent_validation"]},
    }
    rec.update(over)
    return rec


def test_native_extract_passes():
    assert violations(base()) == []


def test_screenshot_as_obs_fails():
    rec = base(
        source={**base()["source"], "source_type": "screenshot"},
        visual_context={**base()["visual_context"], "native_or_display": "display_proxy", "display_transform": "unknown"},
        calibration={**base()["calibration"], "coordinate_reference_system": "unknown", "calibration_points": []},
        claim={**base()["claim"], "epistemic_class": "OBS"},
    )
    assert violations(rec), "screenshot classified OBS must fail"


def test_uncalibrated_proxy_exceeding_ceiling_fails():
    rec = base(
        visual_context={**base()["visual_context"], "native_or_display": "display_proxy"},
        calibration={**base()["calibration"], "calibration_points": [], "coordinate_reference_system": "unknown"},
        claim={**base()["claim"], "epistemic_class": "DER"},
    )
    assert violations(rec), "uncalibrated proxy claimed DER must fail"


def test_self_validation_fails():
    rec = base(_verify_source="segy://line42.sgy")
    assert any("verifies itself" in x for x in violations(rec))


def test_missing_uncertainty_fails():
    rec = base(calibration={**base()["calibration"], "uncertainty_model": ""})
    assert any("uncertainty" in x for x in violations(rec))


def test_preferred_hypothesis_nonnull_fails():
    rec = base(claim={**base()["claim"], "preferred_hypothesis": "horizon A is a channel"})
    assert any("preferred_hypothesis" in x for x in violations(rec))


def test_pass_without_calibration_anchors_fails():
    rec = base(
        calibration={**base()["calibration"], "calibration_points": []}, constraints={**base()["constraints"], "status": "PASS"}
    )
    assert any("calibration anchors" in x for x in violations(rec))


def test_spec_reaching_seal_fails():
    rec = base(
        claim={**base()["claim"], "epistemic_class": "SPEC"},
        seal_eligibility={"eligible_for_scientific_warrant": True, "missing": []},
    )
    assert any("SEAL" in x for x in violations(rec))


def test_schema_structural_and_allOf_rules():
    if not HAVE_JSONSCHEMA:
        print("jsonschema not installed — structural checks skipped (rule tests above still enforced)")
        return
    v = jsonschema.Draft202012Validator(SCHEMA)
    good = base()
    assert not list(v.iter_errors(good)), "valid native extraction must pass schema"
    bad_ceiling = base(
        visual_context={**base()["visual_context"], "native_or_display": "display_proxy"},
        claim={**base()["claim"], "epistemic_class": "OBS"},
    )
    assert list(v.iter_errors(bad_ceiling)), "display_proxy claimed OBS must violate schema"
    bad_seal = base(
        claim={**base()["claim"], "epistemic_class": "SPEC"},
        seal_eligibility={"eligible_for_scientific_warrant": True, "missing": []},
    )
    assert list(v.iter_errors(bad_seal)), "SPEC seal-eligible must violate schema"
