import json
import os
import pytest
import jsonschema
from jsonschema import validate, RefResolver

SCHEMA_DIR = "/root/geox/schemas/earth"

def load_schema(filename):
    with open(os.path.join(SCHEMA_DIR, filename), 'r') as f:
        return json.load(f)

def get_resolver(schema):
    store = {}
    for f in os.listdir(SCHEMA_DIR):
        if f.endswith('.json') and f != 'sample_sealed_interpretation_claim.json':
            s = load_schema(f)
            if "$id" in s:
                store[s["$id"]] = s
            store[f] = s
    return RefResolver(base_uri="file://" + SCHEMA_DIR + "/", referrer=schema, store=store)

def get_schemas_to_test():
    return [
        'earth_claim.json',
        'measurement.json',
        'dataset_manifest.json',
        'well_header.json',
        'well_log_curve.json',
        'seismic_volume_metadata.json',
        'horizon.json',
        'fault.json',
        'interpretation_claim.json',
        'uncertainty.json'
    ]

def test_schemas_have_required_fields():
    for f in get_schemas_to_test():
        schema = load_schema(f)
        assert "schema_id" in schema, f"{f} missing schema_id"
        assert "schema_version" in schema, f"{f} missing schema_version"
        assert "changelog" in schema, f"{f} missing changelog"
        assert "examples" in schema, f"{f} missing examples"
        assert "invalid_examples" in schema, f"{f} missing invalid_examples"
        assert "required" in schema, f"{f} missing required"

def test_valid_examples():
    for f in get_schemas_to_test():
        schema = load_schema(f)
        resolver = get_resolver(schema)
        for example in schema.get("examples", []):
            validate(instance=example, schema=schema, resolver=resolver)

def test_invalid_examples():
    for f in get_schemas_to_test():
        schema = load_schema(f)
        resolver = get_resolver(schema)
        for example in schema.get("invalid_examples", []):
            with pytest.raises(jsonschema.exceptions.ValidationError):
                validate(instance=example, schema=schema, resolver=resolver)

def test_sample_interpretation_claim():
    schema = load_schema('interpretation_claim.json')
    resolver = get_resolver(schema)
    with open(os.path.join(SCHEMA_DIR, "sample_sealed_interpretation_claim.json"), 'r') as f:
        sample = json.load(f)
    validate(instance=sample, schema=schema, resolver=resolver)
