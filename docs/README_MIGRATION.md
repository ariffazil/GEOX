# GEOX — Low-Entropy Reorganization (2026-05-17)

## New Structure

```text
src/
  geox_core/          # Core earth computation engines
  geox_mcp/           # Canonical MCP server + tools
resources/            # Agent knowledge: capabilities, playbooks, prompts, ontology, schemas, examples
apps/                 # Human UI surfaces
docs/                 # Documentation (moved from root)
tests/                # Test suites
scripts/              # Build / validation scripts
archive/              # Legacy surfaces, old servers, deprecated code
```

## Running the Server

```bash
cd /root/geox
PYTHONPATH=src python -m geox_mcp.server
```

Or with explicit transport:

```bash
PYTHONPATH=src python src/geox_mcp/server.py --transport streamable-http --host 0.0.0.0 --port 8081
```

## What Changed

- **Canonical server** moved from `server.py` → `src/geox_mcp/server.py`
- **MCP tools** moved from `contracts/tools/canonical/` → `src/geox_mcp/tools/`
- **Core engines** moved from `geox/` → `src/geox_core/`
- **Docs** moved from root → `docs/`
- **Legacy surfaces** moved to `archive/`
- **Resources** created fresh under `resources/`

## Package Names Changed

| Old import | New import |
|------------|-----------|
| `from contracts.canonical_registry import ...` | `from geox_mcp.registry import ...` |
| `from contracts.tools.canonical.ingest import ...` | `from geox_mcp.tools.data import ...` |
| `from contracts.enums.statuses import ...` | `from geox_core.enums.statuses import ...` |
| `from geox.services.las_ingestor import ...` | `from geox_core.services.las_ingestor import ...` |
| `from geox.well.mcp_tools import ...` | `from geox_mcp.tools.well import ...` |

## Next Steps

1. Verify all tools boot correctly
2. Expose `resources/` as MCP resources
3. Generate toolcards from `resources/capabilities/geox_capabilities.json`
4. Remove old code once transition is stable

DITEMPA BUKAN DIBERI.
