"""
GEOX — Earth Intelligence Runtime Package
═══════════════════════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Forged, Not Given
Version: v2026.07.01-PHASE23 (34 canonical tools)

Runtime subpackages (live, imported by canonical server or tests):
  egs/         — Earth Graph System (claims, evidence, provenance, uncertainty)
  ingest/      — Data ingestion (LAS, CSV, Parquet, SEG-Y)
  plot_specs/  — Plot specification engines
  services/    — Asset memory, LAS ingestor
  skills/      — Earth science skill modules
  wealth/      — Capital intelligence bridge
  well/        — Well stratigraphy (L1-L3)
  core/        — Legacy core (AC risk, volumetrics, sensitivity) — used by tests

Canonical MCP server lives in src/geox_mcp/server.py (34 tools).
This package is the runtime backplane, not the tool surface.
"""

__version__ = "v2026.07.01-PHASE23"
__seal__ = "DITEMPA BUKAN DIBERI"

# Lazy imports — old core modules still used by test suite
# These will be migrated to src/geox_core/ in a future refactor
