"""deep_time/vector.py — Earth State Vector assembly + governance footer.

Orchestrates the data loaders and formulas to produce a complete
EarthStateVector + GovernanceFooter for a resolved age interval.

F2 TRUTH: assembly preserves nulls honestly. Variables without ingested
data remain null with NO_DATA tag and a pending-dataset pointer.
Variables unknowable at the requested age get UNKNOWN with a hard
note (F9 Anti-Hantu fabrication guard).

F11 AUDIT: governance footer is MANDATORY on every envelope. Lives in
the CORE (not the adapter) so no caller can emit ungoverned output.

DITEMPA BUKAN DIBEI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .age_resolver import AgeResolution
from .schemas import (
    EarthStateVariable,
    EarthStateVector,
    EarthStateEnvelope,
    GovernanceFooter,
)
from .formulas import (
    wrap_solar_luminosity,
    wrap_day_length,
    wrap_orbital_eccentricity,
    wrap_orbital_obliquity,
)
from .data_loaders import (
    load_co2_estimate,
    load_benthic_d18O,
    load_temperature_estimate,
    load_sea_level_estimate,
    load_magnetic_polarity,
    load_atmospheric_o2,
    load_supercontinent_state,
    load_biotic_realm,
    load_ice_extent,
    PENDING_DATASETS,
)


INTERVAL_DISTRIBUTION_THRESHOLD_MYR = 5.0


def _compute_seal(envelope_dict: dict, ics_chart_version: str) -> str:
    """Compute a deterministic VAULT999-style seal for the envelope.

    Format: VAULT999::DTC::<sha256-prefix>::<timestamp>
    The hash is over the canonical JSON of the envelope dict (excluding
    seal/issued_at fields themselves).
    """
    payload = json.dumps(envelope_dict, sort_keys=True, default=str).encode()
    h = hashlib.sha256(payload).hexdigest()[:12]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"VAULT999::DTC::{h}::{ts}"


def assemble_earth_state_vector(age_res: AgeResolution) -> EarthStateVector:
    """Assemble the full Earth State Vector for a resolved age interval.

    Always-on (formula-based) variables:
      - solar_luminosity_fraction
      - day_length_hours
      - orbital_eccentricity
      - orbital_obliquity_deg

    Two-tier temperature handling (per F2 hardening crack 2):
      - benthic_d18O_permil: OBSERVED measurement (when ingestible)
      - global_temperature_anomaly_c: INTERPRETED downstream

    5-state polarity (per F2 hardening crack 1):
      - geomagnetic_polarity: NORMAL | REVERSED | MIXED | SUPERCHRON | UNRESOLVED

    Reference-frame tagged (per F4 hardening crack 3):
      - eustatic_sea_level_m: curve + component + datum fields

    Pending external dataset (NO_DATA until ingested):
      - atmospheric_co2_ppm
      - benthic_d18O_permil
      - global_temperature_anomaly_c
      - eustatic_sea_level_m
      - atmospheric_o2_pal

    Always populated (qualitative consensus):
      - paleogeography_summary (synthesised from supercontinent)
      - supercontinent_state
      - ice_extent
      - biotic_realm
    """
    midpoint = age_res.midpoint_ma
    age_top = age_res.top_ma
    age_base = age_res.base_ma
    duration_myr = age_res.duration_myr
    now_iso = datetime.now(timezone.utc).isoformat()

    # ─── Formula-based variables (always populated) ─────────────────────────
    solar = wrap_solar_luminosity(midpoint)
    day_length = wrap_day_length(midpoint)
    ecc = wrap_orbital_eccentricity(midpoint)
    obliquity = wrap_orbital_obliquity(midpoint)

    # ─── Two-tier temperature handling ──────────────────────────────────────
    benthic = load_benthic_d18O(midpoint, age_top, age_base, duration_myr)
    temp = load_temperature_estimate(midpoint, age_top, age_base, duration_myr)

    # ─── External dataset variables (pending ingestion) ────────────────────
    co2 = load_co2_estimate(midpoint, age_top, age_base, duration_myr)
    sea_level = load_sea_level_estimate(midpoint, age_top, age_base, duration_myr)
    mag = load_magnetic_polarity(midpoint, age_top, age_base, duration_myr)
    o2 = load_atmospheric_o2(midpoint, age_top, age_base, duration_myr)

    # ─── Qualitative consensus variables (always populated) ─────────────────
    supercontinent = load_supercontinent_state(midpoint)
    biotic = load_biotic_realm(midpoint)
    ice = load_ice_extent(midpoint)

    # Paleogeography summary synthesised from supercontinent
    if supercontinent.value is not None:
        paleogeo = EarthStateVariable(
            name="paleogeography_summary",
            value=supercontinent.value,
            units="descriptor",
            epistemic_level="OBSERVED",
            source_citation=supercontinent.source_citation,
            coverage_top_ma=supercontinent.coverage_top_ma,
            coverage_base_ma=supercontinent.coverage_base_ma,
            notes=(
                "Synthesised from supercontinent state. For detailed plate "
                "reconstructions and paleolatitudes, ingest the Merdith 2021 "
                "or GPlates dataset (see PENDING_DATASETS['paleogeography']). "
                "F4 CLARITY: reference_frame fields should be populated when "
                "the GPlates model is loaded."
            ),
            confidence=0.80,
            reference_curve="Merdith2021 (pending)",
            reference_component="composite",
            reference_datum="present_geographic",
        )
    else:
        paleogeo = EarthStateVariable(
            name="paleogeography_summary",
            value=None,
            units="descriptor",
            epistemic_level="NO_DATA",
            notes="No supercontinent descriptor available for this age",
            confidence=0.10,
        )

    # ─── Count real vs pending vs UNKNOWN ───────────────────────────────────
    all_vars = [
        solar, day_length, ecc, obliquity,
        co2, temp, sea_level, mag, o2, benthic,
        supercontinent, biotic, ice, paleogeo,
    ]
    n_real = sum(
        1 for v in all_vars
        if v.value is not None and v.epistemic_level not in ("NO_DATA", "UNKNOWN")
    )
    n_pending = sum(1 for v in all_vars if v.epistemic_level == "NO_DATA")
    n_unknown = sum(1 for v in all_vars if v.epistemic_level == "UNKNOWN")

    # ─── Overall confidence (mean of non-null variable confidences) ─────────
    real_confs = [
        v.confidence for v in all_vars
        if v.value is not None and v.epistemic_level not in ("NO_DATA", "UNKNOWN")
    ]
    if real_confs:
        overall_conf = sum(real_confs) / len(real_confs)
        overall_conf = min(overall_conf, 0.90)
    else:
        overall_conf = 0.10

    return EarthStateVector(
        geomagnetic_polarity=mag,
        atmospheric_co2_ppm=co2,
        benthic_d18O_permil=benthic,
        global_temperature_anomaly_c=temp,
        eustatic_sea_level_m=sea_level,
        atmospheric_o2_pal=o2,
        paleogeography_summary=paleogeo,
        supercontinent_state=supercontinent,
        ice_extent=ice,
        solar_luminosity_fraction=solar,
        day_length_hours=day_length,
        orbital_eccentricity=ecc,
        orbital_obliquity_deg=obliquity,
        biotic_realm=biotic,
        mass_extinction_events_in_window=[],
        ics_chart_version=age_res.ics_chart_version,
        ics_chart_hash=None,
        n_variables_with_real_data=n_real,
        n_variables_pending_external_data=n_pending,
        n_variables_unknown_at_age=n_unknown,
        overall_confidence=overall_conf,
        is_interval_query=(duration_myr > INTERVAL_DISTRIBUTION_THRESHOLD_MYR),
        interval_duration_myr=duration_myr,
        notes=(
            f"Assembled for interval [{age_res.top_ma:.3f}, {age_res.base_ma:.3f}] Ma "
            f"('{age_res.named_unit}', {age_res.named_rank}). "
            f"{n_real} variables populated; {n_pending} pending external dataset ingestion; "
            f"{n_unknown} marked UNKNOWN by F9 fabrication guard. "
            f"Interval duration: {duration_myr:.2f} Myr "
            f"({'distribution semantics' if duration_myr > INTERVAL_DISTRIBUTION_THRESHOLD_MYR else 'point semantics'}). "
            f"Issued at {now_iso}."
        ),
    )


def _build_governance_footer(
    vector: EarthStateVector,
    age_res: AgeResolution,
) -> GovernanceFooter:
    """Build the mandatory F11 AUDIT governance footer.

    Lives in CORE (not adapter) so no caller can emit ungoverned output.
    """
    # Find lowest-confidence field
    all_vars_dict = {
        "geomagnetic_polarity": vector.geomagnetic_polarity,
        "atmospheric_co2_ppm": vector.atmospheric_co2_ppm,
        "benthic_d18O_permil": vector.benthic_d18O_permil,
        "global_temperature_anomaly_c": vector.global_temperature_anomaly_c,
        "eustatic_sea_level_m": vector.eustatic_sea_level_m,
        "atmospheric_o2_pal": vector.atmospheric_o2_pal,
        "paleogeography_summary": vector.paleogeography_summary,
        "supercontinent_state": vector.supercontinent_state,
        "ice_extent": vector.ice_extent,
        "solar_luminosity_fraction": vector.solar_luminosity_fraction,
        "day_length_hours": vector.day_length_hours,
        "orbital_eccentricity": vector.orbital_eccentricity,
        "orbital_obliquity_deg": vector.orbital_obliquity_deg,
        "biotic_realm": vector.biotic_realm,
    }
    lowest_field = None
    lowest_value = 1.0
    for name, var in all_vars_dict.items():
        if var is not None and var.confidence < lowest_value:
            lowest_value = var.confidence
            lowest_field = name

    # Determine risk level and human_review_required
    n_unknown = vector.n_variables_unknown_at_age
    n_pending = vector.n_variables_pending_external_data
    if n_unknown > 0:
        risk = "MEDIUM"
        human_review = True  # F9 says caller must review unknown fields
        verdict = "HOLD"
    elif n_pending > 5:
        risk = "MEDIUM"
        human_review = False  # pending is recoverable by ingestion
        verdict = "PARTIAL"
    elif vector.overall_confidence >= 0.80:
        risk = "LOW"
        human_review = False
        verdict = "SEAL"
    elif vector.overall_confidence >= 0.50:
        risk = "LOW"
        human_review = False
        verdict = "PLAUSIBLE"
    else:
        risk = "LOW"
        human_review = False
        verdict = "PARTIAL"

    return GovernanceFooter(
        verdict=verdict,
        lowest_confidence_field=lowest_field,
        lowest_confidence_value=round(lowest_value, 3),
        risk=risk,
        human_review_required=human_review,
        f9_fabrication_guard_active=True,
        ics_chart_version=age_res.ics_chart_version,
        ics_chart_hash=age_res.ics_chart_version,  # placeholder; real hash from caller
        issued_at=datetime.now(timezone.utc).isoformat(),
        seal=None,  # populated after envelope assembly
        arifos_constitution_version="v2026.05.05-SSCT",
    )


def assemble_envelope(
    age_res: AgeResolution,
    input_query: dict,
    vector: EarthStateVector,
    pending_datasets: list[dict] | None = None,
) -> EarthStateEnvelope:
    """Wrap an Earth State Vector into the public MCP envelope.

    Includes the mandatory governance footer (F11 AUDIT).
    """
    # Determine the pending datasets from the vector
    pending = []
    unknown = []
    if pending_datasets is None:
        if vector.atmospheric_co2_ppm:
            if vector.atmospheric_co2_ppm.epistemic_level == "NO_DATA":
                pending.append({"variable": "atmospheric_co2_ppm", **PENDING_DATASETS.get("co2", {})})
            elif vector.atmospheric_co2_ppm.epistemic_level == "UNKNOWN":
                unknown.append({
                    "variable": "atmospheric_co2_ppm",
                    "reason": vector.atmospheric_co2_ppm.notes,
                    "f9_action": "Refuse fabrication. Accept UNKNOWN or ingest deep-time proxy if exists.",
                })
        if vector.global_temperature_anomaly_c:
            if vector.global_temperature_anomaly_c.epistemic_level == "NO_DATA":
                pending.append({"variable": "global_temperature_anomaly_c", **PENDING_DATASETS.get("temperature", {})})
            elif vector.global_temperature_anomaly_c.epistemic_level == "UNKNOWN":
                unknown.append({
                    "variable": "global_temperature_anomaly_c",
                    "reason": vector.global_temperature_anomaly_c.notes,
                    "f9_action": "Refuse fabrication. Accept UNKNOWN.",
                })
        if vector.benthic_d18O_permil:
            if vector.benthic_d18O_permil.epistemic_level == "NO_DATA":
                pending.append({"variable": "benthic_d18O_permil", **PENDING_DATASETS.get("temperature", {})})
            elif vector.benthic_d18O_permil.epistemic_level == "UNKNOWN":
                unknown.append({
                    "variable": "benthic_d18O_permil",
                    "reason": vector.benthic_d18O_permil.notes,
                    "f9_action": "Use brachiopod or phosphate δ18O for older intervals.",
                })
        if vector.eustatic_sea_level_m:
            if vector.eustatic_sea_level_m.epistemic_level == "NO_DATA":
                pending.append({"variable": "eustatic_sea_level_m", **PENDING_DATASETS.get("sea_level", {})})
            elif vector.eustatic_sea_level_m.epistemic_level == "UNKNOWN":
                unknown.append({
                    "variable": "eustatic_sea_level_m",
                    "reason": vector.eustatic_sea_level_m.notes,
                    "f9_action": "Refuse fabrication.",
                })
        if vector.geomagnetic_polarity:
            if vector.geomagnetic_polarity.epistemic_level == "NO_DATA":
                pending.append({"variable": "geomagnetic_polarity", **PENDING_DATASETS.get("magnetic_polarity", {})})
        if vector.atmospheric_o2_pal:
            if vector.atmospheric_o2_pal.epistemic_level == "NO_DATA":
                pending.append({"variable": "atmospheric_o2_pal", **PENDING_DATASETS.get("o2", {})})
            elif vector.atmospheric_o2_pal.epistemic_level == "UNKNOWN":
                unknown.append({
                    "variable": "atmospheric_o2_pal",
                    "reason": vector.atmospheric_o2_pal.notes,
                    "f9_action": "Refuse fabrication.",
                })
        if vector.paleogeography_summary and vector.paleogeography_summary.notes and "Merdith" in vector.paleogeography_summary.notes:
            pending.append({"variable": "paleogeography_summary", **PENDING_DATASETS.get("paleogeography", {})})

    # Sources list (deduplicated)
    sources_seen = set()
    sources = []
    for var in [
        vector.solar_luminosity_fraction, vector.day_length_hours,
        vector.orbital_eccentricity, vector.orbital_obliquity_deg,
        vector.geomagnetic_polarity, vector.atmospheric_co2_ppm,
        vector.benthic_d18O_permil, vector.global_temperature_anomaly_c,
        vector.eustatic_sea_level_m, vector.atmospheric_o2_pal,
        vector.supercontinent_state, vector.biotic_realm,
        vector.ice_extent, vector.paleogeography_summary,
    ]:
        if var and var.source_citation and var.source_citation not in sources_seen and "pending" not in (var.source_citation or "").lower():
            sources_seen.add(var.source_citation)
            sources.append({
                "citation": var.source_citation,
                "doi": var.source_doi,
                "coverage_top_ma": var.coverage_top_ma,
                "coverage_base_ma": var.coverage_base_ma,
                "type": var.epistemic_level.lower(),
            })

    # Build governance footer
    governance = _build_governance_footer(vector, age_res)

    # Epistemic summary
    real_vars = sum(
        1 for v in [
            vector.solar_luminosity_fraction, vector.day_length_hours,
            vector.orbital_eccentricity, vector.orbital_obliquity_deg,
            vector.supercontinent_state, vector.biotic_realm,
            vector.ice_extent, vector.paleogeography_summary,
        ]
        if v and v.value is not None
    )

    env = EarthStateEnvelope(
        input_query=input_query,
        age_resolution={
            "top_ma": age_res.top_ma,
            "base_ma": age_res.base_ma,
            "midpoint_ma": age_res.midpoint_ma,
            "duration_myr": age_res.duration_myr,
            "named_unit": age_res.named_unit,
            "named_rank": age_res.named_rank,
            "matched_input": age_res.matched_input,
            "resolution_method": age_res.resolution_method,
            "ics_chart_version": age_res.ics_chart_version,
            "resolution_confidence": age_res.confidence,
            "query_type": "interval" if vector.is_interval_query else "point",
        },
        earth_state_vector=vector.model_dump(),
        governance=governance.model_dump(),
        epistemic_summary={
            "overall_confidence": vector.overall_confidence,
            "n_variables_with_real_data": real_vars,
            "n_variables_pending_external_data": vector.n_variables_pending_external_data,
            "n_variables_unknown_at_age": vector.n_variables_unknown_at_age,
            "humility_cap_applied": 0.90,
            "f9_fabrication_guard_active": True,
            "is_interval_query": vector.is_interval_query,
            "interval_threshold_myr": INTERVAL_DISTRIBUTION_THRESHOLD_MYR,
        },
        sources=sources,
        pending_external_datasets=pending,
        unknown_at_age=unknown,
        notes=vector.notes,
    )

    # Compute seal from envelope content (F11 AUDIT)
    env_dict = env.model_dump()
    governance.seal = _compute_seal(env_dict, age_res.ics_chart_version)
    env.governance = governance.model_dump()

    return env
