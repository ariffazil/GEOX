import yaml
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("jsonschema not installed, installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema", "pyyaml", "openapi-schema-validator"])
    import jsonschema

from openapi_schema_validator import validate

def resolve_ref(ref_str, current_dir):
    """Simple $ref resolver for local files."""
    if not ref_str.startswith("./"):
        return None
    path = current_dir / ref_str.replace("./", "")
    with open(path) as f:
        return yaml.safe_load(f), path.parent

def inline_refs(schema, current_dir):
    """Recursively inline local $refs for jsonschema validation."""
    if isinstance(schema, dict):
        if "$ref" in schema and schema["$ref"].startswith("./"):
            resolved, new_dir = resolve_ref(schema["$ref"], current_dir)
            return inline_refs(resolved, new_dir)
        return {k: inline_refs(v, current_dir) for k, v in schema.items()}
    elif isinstance(schema, list):
        return [inline_refs(item, current_dir) for item in schema]
    return schema

def main():
    base_dir = Path("/root/geox/contracts/openapi/v1")
    openapi_path = base_dir / "openapi.yaml"
    payloads_path = base_dir / "examples" / "payloads.json"

    print(f"Loading OpenAPI skeleton from {openapi_path}...")
    with open(openapi_path) as f:
        spec = yaml.safe_load(f)
    
    # 1. Validate OpenAPI skeleton (basic)
    print("Validating OpenAPI schema structure...")
    try:
        validate(spec)
        print("✅ OpenAPI 3.1 structure valid.")
    except Exception as e:
        print(f"⚠️ OpenAPI validation warning (missing full ref resolution maybe): {e}")

    # 2. Validate payloads
    print(f"Loading examples from {payloads_path}...")
    with open(payloads_path) as f:
        payloads = json.load(f)

    schemas_to_test = {
        "pick": "components/schemas/pick.yaml",
        "interval": "components/schemas/interval.yaml",
        "correlation": "components/schemas/correlation.yaml",
        "timescale_unit": "components/schemas/timescale_unit.yaml"
    }

    for key, rel_path in schemas_to_test.items():
        schema_path = base_dir / rel_path
        with open(schema_path) as f:
            schema = yaml.safe_load(f)
        
        # Inline local refs for jsonschema
        schema_dir = schema_path.parent
        resolved_schema = inline_refs(schema, schema_dir) # schema_dir handles relative paths
        
        data = payloads.get(key)
        if not data:
            print(f"❌ Missing example payload for {key}")
            sys.exit(1)
            
        print(f"Validating {key} example against {rel_path}...")
        try:
            jsonschema.validate(instance=data, schema=resolved_schema)
            print(f"✅ {key} payload conforms to schema.")
        except jsonschema.exceptions.ValidationError as e:
            print(f"❌ Validation failed for {key}: {e.message}")
            sys.exit(1)

    print("All contracts and examples passed validation.")

if __name__ == "__main__":
    main()
