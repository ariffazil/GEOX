"""
Vision JSON extraction — tolerant parsing of free-form model output
═══════════════════════════════════════════════════════════════════
2026-11-04 (333-AGI). The Earth Witness vision backend used to extract JSON by
taking everything from the first "{" to the LAST "}". A vision model that emits
two JSON objects (or a JSON object followed by prose containing braces) produced a
merged substring that fails json.loads with "Extra data" — and the organ reported
a FATAL INTERNAL_ERROR "server bug" for a recoverable model-output shape.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json

from geox_core.earth_witness.vision_backend import (
    _iter_json_objects,
    extract_observation_json,
)

OBS = {
    "modality": "seismic_display",
    "visible_features": [{"feature_id": "feat_01", "label": "reflector"}],
    "ocr_text": [],
    "measurements": [],
    "hypotheses": [],
    "limitations": {"image_cannot_determine": []},
}


def test_plain_json_object():
    out = extract_observation_json(json.dumps(OBS))
    assert out == OBS


def test_markdown_fenced_json():
    text = "```json\n" + json.dumps(OBS) + "\n```"
    out = extract_observation_json(text)
    assert out is not None
    assert out["modality"] == "seismic_display"


def test_prose_before_and_after():
    text = "Sure! Here is the analysis:\n" + json.dumps(OBS) + "\nLet me know if you need more."
    out = extract_observation_json(text)
    assert out is not None
    assert out["modality"] == "seismic_display"


def test_two_concatenated_json_objects_first_wins():
    """The exact live failure: model emitted two blocks; naive merge broke it."""
    first = json.dumps(OBS)
    second = json.dumps({"note": "second block", "visible_features": []})
    out = extract_observation_json(first + second)
    assert out is not None
    assert out["modality"] == "seismic_display", "must take the observation payload, not the merge"


def test_two_objects_and_the_second_carries_the_contract_keys():
    first = json.dumps({"unrelated": {"a": 1}})
    second = json.dumps(OBS)
    out = extract_observation_json(first + second)
    assert out is not None
    assert out["modality"] == "seismic_display"


def test_braces_inside_strings_do_not_break_balancing():
    payload = dict(OBS)
    payload["visible_features"] = [{"feature_id": "feat_01", "label": "brace", "description": "a } brace and a { brace"}]
    text = "prose " + json.dumps(payload) + " trailing { unbalanced"
    out = extract_observation_json(text)
    assert out is not None
    assert out["visible_features"][0]["description"].startswith("a } brace")


def test_escaped_quotes_inside_strings():
    payload = dict(OBS)
    payload["visible_features"] = [{"feature_id": "f", "label": "quote", "description": 'he said "hi" loudly'}]
    out = extract_observation_json(json.dumps(payload))
    assert out is not None
    assert out["visible_features"][0]["description"] == 'he said "hi" loudly'


def test_non_json_text_returns_none():
    assert extract_observation_json("I cannot determine this from the image.") is None
    assert extract_observation_json("") is None
    assert extract_observation_json("   ") is None


def test_iter_yields_each_object_separately():
    a, b = '{"a":1}', '{"b":2}'
    got = list(_iter_json_objects(a + " " + b))
    assert len(got) == 2
    assert json.loads(got[0]) == {"a": 1}
    assert json.loads(got[1]) == {"b": 2}


def test_unparsable_model_output_is_not_reported_as_a_server_bug():
    from geox_mcp.federation_safety import classify_error

    err = ValueError("federation vision returned no parsable JSON (content_len=800, reasoning_len=179, finish=stop)")
    r = classify_error(err, source_tool="geox_observe", source_organ="geox")
    assert r["severity"] == "RECOVERABLE"
    assert r["suspected_layer"] == "downstream_model"
    assert "server bug" not in r["next_action"]
