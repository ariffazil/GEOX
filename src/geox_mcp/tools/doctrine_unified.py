"""
geox_doctrine — Unified Doctrine Guardrails (Phase 2)
═════════════════════════════════════════════════════
Absorbs: geox_doctrine_anti_beautiful_one, geox_doctrine_assumption_register,
         geox_doctrine_godel_review, geox_abstraction_guard,
         geox_biostrat_constraint, geox_prithvi_eo_inference

Modes: anti_beautiful_one, assumption_register, godel_review,
       abstraction_guard, biostrat, prithvi_eo, registry

Capability Spine Repair 2026-06-26: Added 'registry' mode that delegates to
geox_system_registry_status. Fixes the guard contradiction where the control
plane recommended geox_doctrine(mode='registry') but no such mode existed.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations
from typing import Any, Literal


async def geox_doctrine(
    mode: Literal[
        "anti_beautiful_one",
        "assumption_register",
        "godel_review",
        "abstraction_guard",
        "biostrat",
        "prithvi_eo",
        "registry",
        "margin_principle",
        "architecture",
    ] = "anti_beautiful_one",
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

    if mode == "registry":
        from geox_mcp.tools.registry import geox_system_registry_status as _impl

        return await _impl()

    if mode == "margin_principle":
        return {
            "verdict": "SEAL",
            "doctrine": "margin_principle",
            "statement": "Everything happens at the margins. The interior only records the result. Unconformities are made at margins, not in basin interiors.",
            "physics": "Every convergent margin strips its foreland. Every divergent margin uplifts its shoulder. Every transform margin re-routes the sediment. Every collision resets the local clock.",
            "sabah_application": "Sabah's four local unconformities (ROU, BU, MMU, SRU) are each a local margin event at a different time with a different mechanism. None global. Scaled across supercontinent cycles, this is the physics that made the Great Unconformity.",
            "great_unconformity_link": "The Great Unconformity is a compound surface: tectonic uplift + Snowball Earth glaciation + prolonged non-deposition + Cambrian marine transgression. Diachronous. Same physics. Same margin principle. Billion-year scale.",
            "epistemic_inversion": "The Great Unconformity looks like 'missing time' only if you assume the interior should have a continuous record. It shouldn't. The active record is at the margins. The interior never had one to begin with, because the margins kept taking it.",
            "closing": "The rock goes to the margin to die — or rather, to be reborn as someone else's sediment. The Sabah MMU is one such death. The Great Unconformity is a billion years of them, summed.",
            "references": ["Peters & Gaines 2012", "Tongkul 1991", "Sidek 2016", "Prabal 2024", "Morley 2022", "Gilligan 2026"],
            "_meta": {"evidence_class": "INTERPRETED", "confidence_cap": 0.90, "source": "SABAH_EUREKA_LEDGER::v1.0::2026-07-10"},
        }

    if mode == "architecture":
        return {
            "verdict": "SEAL",
            "doctrine": "geox_architecture",
            "stack": {
                "layer_4_sovereign": "ARIF — meaning, judgment, final veto",
                "layer_3_constitution": "arifOS — authority, evidence floors, routing, holds, audit",
                "layer_2_earth_evidence": "GEOX — Earth data, physics, competing interpretations",
                "layer_1_data": "DATA/EARTH — samples, logs, seismic, maps, ages, observations",
            },
            "operating_modes": {
                "knowledge": {"input": "Published primary literature", "output": "Cited scientific synthesis"},
                "evidence": {"input": "Actual geological data", "output": "Observations and computed results"},
                "hypothesis": {"input": "Evidence graph", "output": "Ranked competing explanations"},
                "contradiction": {"input": "Claims and alternatives", "output": "Evidence that attacks each claim"},
                "decision_support": {"input": "Verified evidence package", "output": "Options, uncertainty, consequences"},
            },
            "routing_rule": {
                "general_education": "ChatGPT answers directly",
                "scientific_verification": "Retrieve primary literature → GEOX structures evidence",
                "field_basin_well_dataset": "GEOX analyses it",
                "drilling_capital_safety_publication": "arifOS governs it",
                "irreversible_judgment": "Arif decides",
            },
            "design_principle": "ChatGPT proposes. GEOX tests against Earth. arifOS controls what may be trusted or acted upon. Arif determines meaning and consequence.",
            "domain_evidence_gate": "When GEOX has no relevant evidence, it returns NO_DOMAIN_EVIDENCE — use ChatGPT for general knowledge.",
            "_meta": {"evidence_class": "OBSERVED", "confidence_cap": 0.95},
        }

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
