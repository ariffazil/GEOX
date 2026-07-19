"""
geox_evidence — Unified Evidence Synthesis (Phase 2)
════════════════════════════════════════════════════
Absorbs: geox_evidence_discover, geox_evidence_reason, geox_literature_ingest

Modes: discover, synthesize, abduct, contradict, spatial_block, ingest_literature

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations

from typing import Any, Literal


async def geox_evidence(
    mode: Literal["discover", "synthesize", "abduct", "contradict", "spatial_block", "ingest_literature"] = "synthesize",
    query: str = "",
    scope: str = "all",
    permission_level: str = "authorized",
    file_path: str = "",
    basin_name: str | None = None,
    evidence_refs: list[str] | None = None,
    hypotheses: list[str] | None = None,
    scale: str = "parasequence",
    depo_context: str = "unknown",
    claim_strictness: str = "screen",
    reasoning_mode: str = "default",
    samples: list[dict[str, Any]] | None = None,
    block_size_km: float = 5.0,
    n_folds: int = 5,
    target_key: str = "value",
    feature_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Unified evidence — discover, synthesize, abduct, contradict, literature.

    Modes:
      discover          - Search SharePoint/OneDrive/local for geological evidence
      synthesize        - Cross-domain evidence graph synthesis
      abduct            - Generate competing geological process hypotheses
      contradict        - Attack hypotheses and surface contradictions
      spatial_block     - Spatial block-CV (Burlamaque 2026-06-04)
      ingest_literature - PDF literature ingest with claim scaffold
    """
    kwargs = locals().copy()
    if mode == "discover":
        from geox_mcp.tools.data import geox_evidence_discover as _impl
        return await _impl(
            query=kwargs.get("query", ""),
            scope=kwargs.get("scope", "all"),
            permission_level=kwargs.get("permission_level", "authorized"),
        )

    if mode == "ingest_literature":
        from geox_mcp.tools.basin import geox_literature_ingest as _impl
        return await _impl(
            file_path=kwargs.get("file_path", ""),
            basin_name=kwargs.get("basin_name"),
        )

    # Default: delegate to geox_evidence_reason for synthesize/abduct/contradict/spatial_block
    from geox_mcp.tools.evidence_reason import geox_evidence_reason as _impl
    return await _impl(
        phase=mode if mode != "synthesize" else "synthesize",
        evidence_refs=kwargs.get("evidence_refs"),
        hypotheses=kwargs.get("hypotheses"),
        scale=kwargs.get("scale", "parasequence"),
        depo_context=kwargs.get("depo_context", "unknown"),
        claim_strictness=kwargs.get("claim_strictness", "screen"),
        basin_name=kwargs.get("basin_name"),
        reasoning_mode=kwargs.get("reasoning_mode", "default"),
        samples=kwargs.get("samples"),
        block_size_km=kwargs.get("block_size_km", 5),
        n_folds=kwargs.get("n_folds", 5),
        target_key=kwargs.get("target_key", "value"),
        feature_keys=kwargs.get("feature_keys"),
    )
