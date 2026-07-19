"""deep_time_state.py — GEOX MCP entry point for the Deep Time State tool.

Maps any user query about past deep geological time (numerical age,
named period, fuzzy phrase, or boundary event) to a canonical interval
via ICS Chart v2024/12, then assembles an Earth State Vector carrying:

  - geomagnetic_polarity          (5-state enum: NORMAL/REVERSED/MIXED/SUPERCHRON/UNRESOLVED)
  - benthic_d18O_permil           (OBSERVED measurement)
  - global_temperature_anomaly_c  (INTERPRETED downstream — split from δ18O per F2 crack 2)
  - atmospheric_co2_ppm
  - eustatic_sea_level_m           (with mandatory curve/component/datum refs per F4 crack 3)
  - atmospheric_o2_pal
  - paleogeography_summary
  - supercontinent_state
  - ice_extent
  - solar_luminosity_fraction
  - day_length_hours
  - orbital_eccentricity
  - orbital_obliquity_deg
  - biotic_realm

Each variable is tagged with epistemic status and uncertainty.
Variables that cannot be known at the requested age return UNKNOWN (F9).
Variables pending external dataset ingestion return NO_DATA + a pointer.

A governance footer is mandatory on every envelope (F11 AUDIT).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging

from geox_core.enums.statuses import get_standard_envelope

from .deep_time import (
    assemble_earth_state_vector,
    assemble_envelope,
    resolve_age_query,
)

logger = logging.getLogger("geox.canonical.deep_time_state")


async def geox_deep_time_state(
    age_ma: float | None = None,
    age_top_ma: float | None = None,
    age_bot_ma: float | None = None,
    period: str | None = None,
    query: str | None = None,
    biozone: str | None = None,
    include_pending_datasets: bool = True,
) -> dict:
    """Deep Time State — returns an Earth State Vector for the requested deep time.

    Args:
        age_ma:           Single point in Ma before present (e.g. 85.0 = Late Cretaceous)
        age_top_ma:       Range top (younger boundary) in Ma — pair with age_bot_ma
        age_bot_ma:       Range base (older boundary) in Ma — pair with age_top_ma
        period:           Named period/epoch/era (e.g. "Jurassic", "Late Cretaceous")
        query:            Free-text fuzzy query (e.g. "when dinosaurs ruled")
        biozone:          NN nannofossil zone (e.g. "NN5", "NN19-20"). Resolved via
                          Martini (1971) + GPTS2020 age table. Overrides age_ma/period
                          if both provided — biozone age bracket wins.
        include_pending_datasets:  If True, the envelope includes the
                                  pending_external_datasets list.

    Returns:
        A canonical MCP envelope (dict) carrying age_resolution,
        earth_state_vector, governance (footer), epistemic_summary,
        sources, pending_external_datasets, and unknown_at_age.

    Constitutional floors:
      F1 AMANAH  — read-only, no state mutation.
      F2 TRUTH   — every datapoint carries citation + uncertainty band;
                   nulls explicit with NO_DATA + pending-dataset pointer;
                   δ18O (OBSERVED) and temperature (INTERPRETED) split.
      F4 CLARITY — structured JSON; reference frames explicit on sea_level
                   and paleogeography (curve, component, datum).
      F7 HUMILITY — confidence hard-capped at 0.90 per variable.
      F9 ANTI-HANTU — fabrication guard: parameters unknowable at age
                   (e.g. CO2 in Hadean, δ18O pre-Triassic) return UNKNOWN.
      F11 AUDIT  — governance footer is mandatory on every envelope;
                   carries verdict, lowest-confidence field, risk,
                   human_review_required, and VAULT999 seal.

    Example:
        await geox_deep_time_state(age_ma=66.0)       # K-Pg boundary
        await geox_deep_time_state(period="Jurassic") # 201.4 - 145.0 Ma
        await geox_deep_time_state(query="when dinosaurs ruled")
        await geox_deep_time_state(biozone="NN5")     # 13.65 - 14.91 Ma (Serravallian)
    """
    logger.info(
        "geox_deep_time_state called: age_ma=%s age_top_ma=%s age_bot_ma=%s period=%s query=%s biozone=%s",
        age_ma,
        age_top_ma,
        age_bot_ma,
        period,
        query,
        biozone,
    )

    # Step 0 — Resolve biozone to age bracket (Phase 2.7, 2026-07-03)
    biozone_source = None
    if biozone:
        from geox_mcp.tools.kernel._biostrat import nn_age, parse_nn_zone

        parsed = parse_nn_zone(biozone)
        zone_name = parsed["zone"]
        if zone_name and zone_name != "UNKNOWN":
            zone_age_top, zone_age_base = nn_age(zone_name)
            if zone_age_top > -999 and zone_age_base > -999:
                age_top_ma = zone_age_top
                age_bot_ma = zone_age_base
                biozone_source = zone_name
                logger.info(
                    "biozone %s resolved to [%.2f, %.2f] Ma via Martini (1971) + GPTS2020",
                    zone_name,
                    zone_age_top,
                    zone_age_base,
                )
            else:
                logger.warning("biozone %s resolved but age lookup failed", zone_name)
        else:
            logger.warning("biozone '%s' could not be parsed as NN zone", biozone)

    # Step 1 — Resolve the age query to a canonical [top_ma, base_ma] interval
    age_res = resolve_age_query(
        age_ma=age_ma,
        age_top_ma=age_top_ma,
        age_bot_ma=age_bot_ma,
        period=period,
        query=query,
    )
    logger.info(
        "age resolved: %s [%s, %s] Ma via %s (confidence %.2f, query_type=%s)",
        age_res.named_unit,
        age_res.top_ma,
        age_res.base_ma,
        age_res.resolution_method,
        age_res.confidence,
        "interval" if age_res.duration_myr > 5.0 else "point",
    )

    # Step 2 — Assemble the Earth State Vector
    vector = assemble_earth_state_vector(age_res)

    # Step 3 — Build the public envelope (with mandatory governance footer)
    input_query = {
        "age_ma": age_ma,
        "age_top_ma": age_top_ma,
        "age_bot_ma": age_bot_ma,
        "period": period,
        "query": query,
        "biozone": biozone,
        "biozone_source": biozone_source,
    }
    pending_datasets = None if include_pending_datasets else []
    envelope = assemble_envelope(
        age_res=age_res,
        input_query=input_query,
        vector=vector,
        pending_datasets=pending_datasets,
    )

    # Step 4 — Apply GEOX canonical envelope (claim_tag, claim_state, etc.)
    envelope_dict = envelope.model_dump()

    # Choose claim_tag based on governance footer verdict
    governance_verdict = envelope_dict.get("governance", {}).get("verdict", "PARTIAL")
    risk = envelope_dict.get("governance", {}).get("risk", "LOW")
    n_unknown = envelope_dict["epistemic_summary"]["n_variables_unknown_at_age"]
    real_count = envelope_dict["epistemic_summary"]["n_variables_with_real_data"]
    pending_count = envelope_dict["epistemic_summary"]["n_variables_pending_external_data"]

    if governance_verdict == "HOLD" or n_unknown > 0:
        claim_tag = "HYPOTHESIS"
        claim_state = "INGESTED"
        uncertainty = "High"
    elif governance_verdict == "PARTIAL" or pending_count > real_count:
        claim_tag = "PLAUSIBLE"
        claim_state = "INTERPRETED"
        uncertainty = "Moderate"
    else:
        claim_tag = "PLAUSIBLE"
        claim_state = "INTERPRETED"
        uncertainty = "Low"

    humility_score = min(vector.overall_confidence, 0.90)

    # Build a concise audit receipt
    audit = {
        "tool_call_hash": envelope_dict.get("governance", {}).get("seal", ""),
        "issued_at": envelope_dict.get("governance", {}).get("issued_at", ""),
        "verdict": governance_verdict,
        "risk": risk,
        "human_review_required": envelope_dict.get("governance", {}).get("human_review_required", False),
    }

    return get_standard_envelope(
        envelope_dict,
        tool_class="compute",
        claim_tag=claim_tag,
        claim_state=claim_state,
        uncertainty=uncertainty,
        humility_score=humility_score,
        evidence_refs=[],
        audit_receipt=audit,
        tool_name="geox_deep_time_state",
        equations_used=[
            "Gough 1981: L/L0 = 1 / (1 + (2/5) * t/4600) [t = age before present]",
            "Day length empirical fit: 24 - 0.6 * (1 - exp(-age/200))",
            "Polarity 5-state enum (Ogg 2020 GTS2020 chrons + CNS/Kiaman)",
            "F9 fabrication guard (UNKNOWN for unknowable params)",
            "F11 governance footer (verdict, risk, human_review, seal)",
        ],
        sensitivity_to=["ics_chart_version", "pending_dataset_ingestion", "f9_guard_threshold"],
    )


# Legacy alias — matches the parity matrix slot provisioned in
# geox_core/parity/runtime_matrix.py as `geox_time4d_reconstruct_palo`.
async def geox_time4d_reconstruct_paleo(
    age_ma: float | None = None,
    age_top_ma: float | None = None,
    age_bot_ma: float | None = None,
    period: str | None = None,
    query: str | None = None,
    **kwargs,
) -> dict:
    """Legacy alias for geox_deep_time_state.

    Honors the parity matrix slot `geox_time4d_reconstruct_palo`.
    """
    return await geox_deep_time_state(
        age_ma=age_ma,
        age_top_ma=age_top_ma,
        age_bot_ma=age_bot_ma,
        period=period,
        query=query,
        **kwargs,
    )
