# GEOX Earth Schemas

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
