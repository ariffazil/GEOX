import json
import os

SCHEMA_DIR = "/root/geox/schemas/earth"
TEST_DIR = "/root/geox/tests"

os.makedirs(SCHEMA_DIR, exist_ok=True)
os.makedirs(TEST_DIR, exist_ok=True)

schemas = {}

# 1. Uncertainty
schemas['uncertainty.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/uncertainty.json",
    "title": "Uncertainty Schema",
    "description": "Defines uncertainty for a confidence metric",
    "schema_id": "uncertainty_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "value": {"type": "number"},
        "distribution": {"type": "string"},
        "p10": {"type": "number"},
        "p90": {"type": "number"}
    },
    "required": ["value"],
    "examples": [{"value": 0.1, "distribution": "normal"}],
    "invalid_examples": [{"distribution": "normal"}] # missing value
}

# 2. Measurement
schemas['measurement.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/measurement.json",
    "title": "Measurement Schema",
    "description": "A measurement with a unit",
    "schema_id": "measurement_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "value": {"type": "number"},
        "unit": {"type": "string"}
    },
    "required": ["value", "unit"],
    "examples": [{"value": 1500.5, "unit": "m"}],
    "invalid_examples": [{"value": 1500.5}]
}

# 3. Earth Claim
schemas['earth_claim.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/earth_claim.json",
    "title": "Earth Claim Schema",
    "description": "Base schema for a claim with evidence and seal",
    "schema_id": "earth_claim_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "claim_id": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "seal": {
            "type": "object",
            "properties": {
                "hash": {"type": "string"}
            },
            "required": ["hash"]
        }
    },
    "required": ["evidence", "seal"],
    "examples": [{
        "claim_id": "claim_001",
        "evidence": ["well_log_1", "core_sample_2"],
        "seal": {"hash": "abc123def456"}
    }],
    "invalid_examples": [{
        "claim_id": "claim_002",
        "evidence": [] # missing seal and empty array
    }]
}

# 4. Dataset Manifest
schemas['dataset_manifest.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/dataset_manifest.json",
    "title": "Dataset Manifest Schema",
    "description": "Manifest for a geological dataset",
    "schema_id": "dataset_manifest_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "dataset_name": {"type": "string"},
        "crs": {"type": "string"},
        "datum": {"type": "string"}
    },
    "required": ["dataset_name"],
    "examples": [{"dataset_name": "survey_xyz", "crs": "EPSG:4326"}],
    "invalid_examples": [{}] # missing name
}

# 5. Well Header
schemas['well_header.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/well_header.json",
    "title": "Well Header Schema",
    "description": "Header information for a well",
    "schema_id": "well_header_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "well_name": {"type": "string"},
        "coordinate": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "crs": {"type": "string"}
            },
            "required": ["x", "y", "crs"]
        },
        "depth": {
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "datum": {"type": "string"}
            },
            "required": ["value", "datum"]
        }
    },
    "required": ["well_name", "coordinate", "depth"],
    "examples": [{
        "well_name": "Well-1A",
        "coordinate": {"x": 100.0, "y": 200.0, "crs": "EPSG:32631"},
        "depth": {"value": 3000.0, "datum": "MSL"}
    }],
    "invalid_examples": [{
        "well_name": "Well-1A",
        "coordinate": {"x": 100.0, "y": 200.0}, 
        "depth": {"value": 3000.0, "datum": "MSL"}
    }]
}

# 6. Well Log Curve
schemas['well_log_curve.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/well_log_curve.json",
    "title": "Well Log Curve Schema",
    "description": "Metadata for a well log curve",
    "schema_id": "well_log_curve_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "curve_name": {"type": "string"},
        "unit": {"type": "string"},
        "well_id": {"type": "string"}
    },
    "required": ["curve_name", "unit"],
    "examples": [{"curve_name": "GR", "unit": "gAPI", "well_id": "Well-1A"}],
    "invalid_examples": [{"curve_name": "GR"}] 
}

# 7. Seismic Volume Metadata
schemas['seismic_volume_metadata.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/seismic_volume_metadata.json",
    "title": "Seismic Volume Metadata Schema",
    "description": "Metadata for a seismic volume",
    "schema_id": "seismic_volume_metadata_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "volume_name": {"type": "string"},
        "coordinate": {
            "type": "object",
            "properties": {
                "bbox": {"type": "array", "items": {"type": "number"}},
                "crs": {"type": "string"}
            },
            "required": ["crs"]
        },
        "datum": {"type": "string"}
    },
    "required": ["volume_name", "coordinate", "datum"],
    "examples": [{
        "volume_name": "Seismic-3D",
        "coordinate": {"bbox": [0, 0, 100, 100], "crs": "EPSG:32631"},
        "datum": "MSL"
    }],
    "invalid_examples": [{
        "volume_name": "Seismic-3D",
        "coordinate": {"bbox": [0, 0, 100, 100], "crs": "EPSG:32631"} 
    }]
}

# 8. Horizon
schemas['horizon.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/horizon.json",
    "title": "Horizon Schema",
    "description": "Metadata for a geological horizon",
    "schema_id": "horizon_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "horizon_name": {"type": "string"},
        "coordinate": {
            "type": "object",
            "properties": {
                "crs": {"type": "string"}
            },
            "required": ["crs"]
        },
        "datum": {"type": "string"}
    },
    "required": ["horizon_name", "coordinate", "datum"],
    "examples": [{
        "horizon_name": "Top-Jurassic",
        "coordinate": {"crs": "EPSG:32631"},
        "datum": "MSL"
    }],
    "invalid_examples": [{
        "horizon_name": "Top-Jurassic",
        "coordinate": {"crs": "EPSG:32631"} 
    }]
}

# 9. Fault
schemas['fault.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/fault.json",
    "title": "Fault Schema",
    "description": "Metadata for a geological fault",
    "schema_id": "fault_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "fault_name": {"type": "string"},
        "coordinate": {
            "type": "object",
            "properties": {
                "crs": {"type": "string"}
            },
            "required": ["crs"]
        }
    },
    "required": ["fault_name", "coordinate"],
    "examples": [{
        "fault_name": "Fault-F1",
        "coordinate": {"crs": "EPSG:32631"}
    }],
    "invalid_examples": [{
        "fault_name": "Fault-F1",
        "coordinate": {} 
    }]
}

# 10. Interpretation Claim
schemas['interpretation_claim.json'] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://geox.os/schemas/earth/interpretation_claim.json",
    "title": "Interpretation Claim Schema",
    "description": "An interpretation claim with provenance and confidence",
    "schema_id": "interpretation_claim_v1",
    "schema_version": "1.0.0",
    "changelog": ["1.0.0 - Initial release"],
    "type": "object",
    "properties": {
        "claim_id": {"type": "string"},
        "provenance": {"type": "string"},
        "confidence": {
            "type": "object",
            "properties": {
                "uncertainty": {
                    "$ref": "uncertainty.json"
                }
            },
            "required": ["uncertainty"]
        },
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1
        },
        "seal": {
            "type": "object",
            "properties": {
                "hash": {"type": "string"}
            },
            "required": ["hash"]
        }
    },
    "required": ["provenance", "confidence", "evidence", "seal"],
    "examples": [{
        "claim_id": "interp_001",
        "provenance": "Interpreter: Jane Doe, Tool: Petrel",
        "confidence": {
            "uncertainty": {
                "value": 0.8
            }
        },
        "evidence": ["seismic_volume_1"],
        "seal": {"hash": "4a5b6c7d8e9f"}
    }],
    "invalid_examples": [{
        "claim_id": "interp_001",
        "confidence": {
            "uncertainty": {
                "value": 0.8
            }
        },
        "evidence": ["seismic_volume_1"],
        "seal": {"hash": "4a5b6c7d8e9f"}
    }]
}

# Write schemas
for name, schema in schemas.items():
    with open(os.path.join(SCHEMA_DIR, name), 'w') as f:
        json.dump(schema, f, indent=2)

# Write sample sealed interpretation claim
sample_claim = {
    "claim_id": "interp_sample_01",
    "provenance": "GEOX Subsurface Auto-Interpreter Beta",
    "confidence": {
        "uncertainty": {
            "value": 0.85,
            "distribution": "normal"
        }
    },
    "evidence": ["synthetic_well_log_A", "synthetic_seismic_cube_B"],
    "seal": {
        "hash": "7a3f8b9d4c2e1a5f6b7c8d9e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b"
    }
}
with open(os.path.join(SCHEMA_DIR, "sample_sealed_interpretation_claim.json"), 'w') as f:
    json.dump(sample_claim, f, indent=2)

# Write test file
test_code = """import json
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

def test_schemas_have_required_fields():
    for f in os.listdir(SCHEMA_DIR):
        if not f.endswith('.json') or f == 'sample_sealed_interpretation_claim.json':
            continue
        schema = load_schema(f)
        assert "schema_id" in schema, f"{f} missing schema_id"
        assert "schema_version" in schema, f"{f} missing schema_version"
        assert "changelog" in schema, f"{f} missing changelog"
        assert "examples" in schema, f"{f} missing examples"
        assert "invalid_examples" in schema, f"{f} missing invalid_examples"
        assert "required" in schema, f"{f} missing required"

def test_valid_examples():
    for f in os.listdir(SCHEMA_DIR):
        if not f.endswith('.json') or f == 'sample_sealed_interpretation_claim.json':
            continue
        schema = load_schema(f)
        resolver = get_resolver(schema)
        for example in schema.get("examples", []):
            validate(instance=example, schema=schema, resolver=resolver)

def test_invalid_examples():
    for f in os.listdir(SCHEMA_DIR):
        if not f.endswith('.json') or f == 'sample_sealed_interpretation_claim.json':
            continue
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
"""

with open(os.path.join(TEST_DIR, "test_geox_schemas.py"), 'w') as f:
    f.write(test_code)

# Write README
readme_content = """# GEOX Earth Schemas

## Schema Validation Pipeline

The schemas are defined using JSON Schema (Draft 2020-12). They enforce hard geological and architectural laws:
- No coordinate without CRS.
- No depth without datum.
- No measurement without unit.
- No interpretation without provenance.
- No confidence without uncertainty.
- No claim without evidence array.
- No seal without hash.

### Testing and Validation
Validation is done via `jsonschema` in Python. We test:
1. That all schemas contain the required metadata (`schema_id`, `schema_version`, `changelog`, `examples`, `invalid_examples`).
2. That all provided `examples` pass validation against the schema.
3. That all `invalid_examples` correctly fail validation.

To run the pipeline:
```bash
pytest /root/geox/tests/test_geox_schemas.py
```
"""
with open(os.path.join(SCHEMA_DIR, "README.md"), 'w') as f:
    f.write(readme_content)

print("Generated schemas, tests, and README.")
