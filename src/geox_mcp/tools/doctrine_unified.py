"""
geox_doctrine — Unified Doctrine Guardrails (Phase 2)
═════════════════════════════════════════════════════
Absorbs: geox_doctrine_anti_beautiful_one, geox_doctrine_assumption_register,
         geox_doctrine_godel_review, geox_abstraction_guard,
         geox_biostrat_constraint, geox_prithvi_eo_inference

Modes: anti_beautiful_one, assumption_register, godel_review,
       abstraction_guard, biostrat, prithvi_eo

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""
from __future__ import annotations
from typing import Any, Literal

async def geox_doctrine(
    mode: Literal["anti_beautiful_one", "assumption_register", "godel_review",
                  "abstraction_guard", "biostrat", "prithvi_eo"] = "anti_beautiful_one",
    introduced_by: str = "",
    rung_origin: int = 0,
    description: str | None = None,
    parent_assumption_id: str | None = None,
    inherited_from: str | None = None,
    epistemic_label: str = "DER",
    claim_id: str = "",
    action: str = "review",
    void_reason: str | None = None,
    rung: int | None = None,
    depends_on_assumption_ids: list[str] | None = None,
    concept: str = "",
    query: str = "",
    state: dict[str, Any] | None = None,
    age_ma: float = 0,
    tile_id: str = "",
    task: str = "land_cover",
    bands: list[str] | None = None,
    time_range_start: str = "2024-01-01",
    time_range_end: str = "2024-12-31",
    cloud_cover_max: float = 0.2,
    source_uri: str | None = None,
    text: str = "",
    grounding_evidence_count: int = 0,
    grounding_evidence_rungs: list[int] | None = None,
    threshold: float = 1.5,
    include_decomposition: bool = True,
) -> dict[str, Any]:
    """GEOX doctrine — constitutional guardrails on interpretation quality.

    Modes:
      anti_beautiful_one  - Anti-Beautiful-One audit (Gap 3)
      assumption_register - Register assumption in doctrine lineage (Gap X)
      godel_review        - Gödel Wall review/seal/void (Gap 5)
      abstraction_guard   - Non-geological abstraction guard
      biostrat            - Biostratigraphic zonation constraint
      prithvi_eo          - Prithvi-EO-2.0 land cover inference
    """
    kwargs = locals().copy()
    if mode == "assumption_register":
        from geox_mcp.tools.doctrine import geox_doctrine_assumption_register as _impl, AssumptionRegisterRequest
        req = AssumptionRegisterRequest(
            introduced_by=kwargs.get("introduced_by", ""),
            rung_origin=kwargs.get("rung_origin", 0),
            description=kwargs.get("description", ""),
            parent_assumption_id=kwargs.get("parent_assumption_id"),
            inherited_from=kwargs.get("inherited_from"),
            epistemic_label=kwargs.get("epistemic_label", "DER"),
        )
        return (await _impl(req)).model_dump(mode="json")

    if mode == "godel_review":
        from geox_mcp.tools.doctrine import geox_doctrine_godel_review as _impl
        return await _impl(
            claim_id=kwargs.get("claim_id", ""),
            action=kwargs.get("action", "review"),
            void_reason=kwargs.get("void_reason"),
            rung=kwargs.get("rung"),
            description=kwargs.get("description"),
            depends_on_assumption_ids=kwargs.get("depends_on_assumption_ids"),
        )

    if mode == "abstraction_guard":
        from geox_mcp.tools.basin import geox_abstraction_guard as _impl
        return await _impl(
            concept=kwargs.get("concept", ""),
            query=kwargs.get("query", ""),
        )

    if mode == "biostrat":
        from geox_mcp.tools.multi_physics import geox_biostrat_constraint as _impl
        return await _impl(
            state=kwargs.get("state", {}),
            age_ma=kwargs.get("age_ma", 0),
        )

    if mode == "prithvi_eo":
        from geox_mcp.tools.earth_obs import geox_prithvi_eo_inference as _impl
        return await _impl(
            tile_id=kwargs.get("tile_id", ""),
            task=kwargs.get("task", "land_cover"),
            bands=kwargs.get("bands"),
            time_range_start=kwargs.get("time_range_start", "2024-01-01"),
            time_range_end=kwargs.get("time_range_end", "2024-12-31"),
            cloud_cover_max=kwargs.get("cloud_cover_max", 0.2),
            source_uri=kwargs.get("source_uri"),
        )

    # Default: anti_beautiful_one
    from geox_mcp.tools.doctrine import geox_doctrine_anti_beautiful_one as _impl, BeautyAuditRequest
    req = BeautyAuditRequest(
        text=kwargs.get("text", ""),
        grounding_evidence_count=kwargs.get("grounding_evidence_count", 0),
        grounding_evidence_rungs=kwargs.get("grounding_evidence_rungs"),
        threshold=kwargs.get("threshold", 1.5),
        include_decomposition=kwargs.get("include_decomposition", True),
    )
    return (await _impl(req)).model_dump(mode="json")
