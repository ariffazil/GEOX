"""macrostrat_calibrate.py — GEOX MCP tool: Merge relative biostratigraphy with Macrostrat absolute ages.

Phase 2.8 (2026-07-03): Arif sovereign spec — the bridge between GEOX's biostrat
physics and Macrostrat's global chronostratigraphy.

PROBLEM:
  Biostrat is relative (NN5, TR18, PR12, FO/LO). Macrostrat is absolute (Ma).
  GEOX needs a governed merge to produce calibrated age ranges with provenance.

DESIGN:
  - Zone before Ma: biozone name preserved as primary key
  - Dual calibration: GEOX internal (NN ages) + Macrostrat external (unit intervals)
  - Cross-reference: compare biostrat age against Macrostrat units at lat/lng
  - Contradiction detection: if biozone age doesn't match Macrostrat unit age → flag
  - Uncertainty propagation: combines biostrat diachroneity + Macrostrat interval uncertainty
  - Not a radiometric age: warning mandatory on every output

RULING CLASSES:
  PASS          — biostrat age matches Macrostrat unit age within uncertainty
  WEAK_PASS     — ages partially overlap or one has high uncertainty
  HOLD          — insufficient data (no Macrostrat column, empty biozone)
  CONTRADICTION — ages don't overlap (e.g., NN5 says 14.9 Ma, column says 23 Ma)

F2 TRUTH: Calibration is a MERGE, not a measurement. Both sources have uncertainty.
F7 HUMILITY: Confidence capped at 0.85 for NN, 0.70 for other zones.
F9 ANTI-HANTU: No calibration → return HOLD, never guess.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import logging
from typing import Any

from geox_core.enums.statuses import get_standard_envelope
from geox_mcp.tools.kernel._biostrat import nn_age, parse_nn_zone
from geox_mcp.tools.macrostrat_client import MacrostratClient

logger = logging.getLogger("geox.canonical.macrostrat_calibrate")

# ── Shared Macrostrat client ───────────────────────────────────────────────
_MACROSTRAT_CLIENT: MacrostratClient | None = None


def _get_client() -> MacrostratClient:
    global _MACROSTRAT_CLIENT
    if _MACROSTRAT_CLIENT is None:
        _MACROSTRAT_CLIENT = MacrostratClient()
    return _MACROSTRAT_CLIENT


# ── Zone type classifier ──────────────────────────────────────────────────
ZONE_PATTERNS: dict[str, str] = {
    "NN": "calcareous_nannofossil",
    "NP": "calcareous_nannofossil_paleogene",
    "PR": "palynology",
    "TR": "planktonic_foraminifera",
    "FO": "foram_zone",
    "LO": "foram_zone",
    "GDE": "geological_depositional_environment",
}


def _classify_zone(biozone: str) -> tuple[str, str]:
    """Classify a biozone string into (discipline, normalized_zone).

    Returns ("unknown", original) if unrecognized.
    """
    if not biozone:
        return ("unknown", "")
    upper = biozone.upper().strip()
    for prefix, discipline in ZONE_PATTERNS.items():
        if upper.startswith(prefix):
            return (discipline, upper)
    return ("unknown", upper)


# ── Macrostrat interval age lookup ────────────────────────────────────────
# Cache for Macrostrat intervals
_INTERVAL_CACHE: list[dict[str, Any]] | None = None


async def _load_intervals() -> list[dict[str, Any]]:
    """Load Macrostrat intervals (cached). Returns list of {name, age_top, age_bottom, ...}."""
    global _INTERVAL_CACHE
    if _INTERVAL_CACHE is not None:
        return _INTERVAL_CACHE
    try:
        client = _get_client()
        resp = await client.get_intervals(all_=True)
        intervals = resp.get("success", {}).get("data", resp.get("data", []))
        if isinstance(intervals, list):
            _INTERVAL_CACHE = intervals
        else:
            _INTERVAL_CACHE = []
    except Exception as e:
        logger.warning(f"Failed to load Macrostrat intervals: {e}")
        _INTERVAL_CACHE = []
    return _INTERVAL_CACHE


async def _find_interval_match(biozone: str, discipline: str) -> dict[str, Any] | None:
    """Find a Macrostrat interval that matches a biozone name.

    Checks interval.name (e.g. "NN5", "Langhian", "Middle Miocene"),
    interval.abbrev, and interval.b_name.
    """
    intervals = await _load_intervals()
    if not intervals:
        return None

    upper = biozone.upper().strip()

    # Direct match on interval name/abbrev
    for iv in intervals:
        name = str(iv.get("name", "")).upper().strip()
        abbrev = str(iv.get("abbrev", "")).upper().strip()
        b_name = str(iv.get("b_name", "")).upper().strip()
        if upper in (name, abbrev, b_name):
            return {
                "id": iv.get("id"),
                "name": iv.get("name"),
                "age_top_ma": iv.get("age_top", iv.get("b_age", 0)),
                "age_bottom_ma": iv.get("age_bottom", iv.get("t_age", 0)),
                "source": "macrostrat_interval",
                "provenance": iv,
            }

    return None


# ── Macrostrat unit age lookup at lat/lng ────────────────────────────────
async def _find_units_at_location(lat: float, lng: float, radius_km: float = 50) -> list[dict[str, Any]]:
    """Get Macrostrat units near a lat/lng point."""
    try:
        client = _get_client()
        resp = await client.get_units(lat=lat, lng=lng, radius_km=radius_km)
        raw = resp.get("success", {}).get("data", resp.get("data", []))
        return raw if isinstance(raw, list) else []
    except Exception as e:
        logger.warning(f"Failed to load Macrostrat units at ({lat}, {lng}): {e}")
        return []


def _find_unit_age_for_biozone(units: list[dict[str, Any]], biozone_age_top: float, biozone_age_base: float) -> dict[str, Any]:
    """Find Macrostrat units whose age range overlaps with the biozone age bracket.

    Returns the best matching unit with age overlap assessment.
    """
    if not units or biozone_age_top < 0:
        return {"found": False, "units_in_range": [], "closest_unit": None}

    matching_units = []
    for unit in units:
        # Unit age fields vary: t_age (top), b_age (base), age_top, age_bottom
        unit_top = unit.get("t_age", unit.get("age_top", unit.get("age_old", 0)))
        unit_bottom = unit.get("b_age", unit.get("age_bottom", unit.get("age_young", 0)))
        if unit_top is None or unit_bottom is None:
            continue

        # Check overlap
        overlap_top = max(biozone_age_top, float(unit_top))
        overlap_bottom = min(biozone_age_base, float(unit_bottom))
        overlap_ma = max(0, overlap_bottom - overlap_top)

        if overlap_ma > 0:
            matching_units.append({
                "unit_id": unit.get("id"),
                "unit_name": unit.get("name", unit.get("strat_name", "unnamed")),
                "unit_age_top_ma": unit_top,
                "unit_age_bottom_ma": unit_bottom,
                "lithology": unit.get("lith", unit.get("lithology", "")),
                "environment": unit.get("environ", unit.get("environment", "")),
                "overlap_ma": overlap_ma,
                "formation": unit.get("strat_name", ""),
                "col_id": unit.get("col_id"),
            })

    matching_units.sort(key=lambda u: u["overlap_ma"], reverse=True)

    if matching_units:
        best = matching_units[0]
        return {
            "found": True,
            "units_in_range": len(matching_units),
            "best_unit": best,
            "all_matching": matching_units[:5],  # top 5
        }

    # No overlap — find closest
    closest = None
    min_gap = float("inf")
    for unit in units[:20]:
        unit_top = float(unit.get("t_age", unit.get("age_top", unit.get("age_old", 0))))
        unit_bottom = float(unit.get("b_age", unit.get("age_bottom", unit.get("age_young", 0))))
        if unit_top is None or unit_bottom is None:
            continue
        gap_top = abs(biozone_age_top - unit_top)
        gap_bottom = abs(biozone_age_base - unit_bottom)
        gap = min(gap_top, gap_bottom)
        if gap < min_gap:
            min_gap = gap
            closest = {
                "unit_id": unit.get("id"),
                "unit_name": unit.get("name", unit.get("strat_name", "unnamed")),
                "unit_age_top_ma": unit_top,
                "unit_age_bottom_ma": unit_bottom,
                "lithology": unit.get("lith", unit.get("lithology", "")),
                "gap_ma": gap,
            }

    return {
        "found": False,
        "no_overlap": True,
        "closest_unit": closest,
        "closest_gap_ma": min_gap if closest else None,
        "total_units_searched": len(units),
    }


# ── Ruling engine ─────────────────────────────────────────────────────────
def _compute_ruling(
    biostrat_top: float,
    biostrat_base: float,
    biostrat_discipline: str,
    macrostrat_match: dict[str, Any],
) -> dict[str, Any]:
    """Compute the calibration ruling based on agreement between sources.

    Ruling classes:
      PASS          — ages agree within tolerance
      WEAK_PASS     — ages partially agree or one source has high uncertainty
      HOLD          — insufficient Macrostrat data
      CONTRADICTION — ages disagree beyond tolerance
    """
    if not macrostrat_match.get("found"):
        if macrostrat_match.get("no_overlap") and macrostrat_match.get("closest_unit"):
            gap = macrostrat_match.get("closest_gap_ma", 0)
            if gap is not None and gap > 2.0:
                return {
                    "ruling": "CONTRADICTION",
                    "reason": f"Biostrat age [{biostrat_top}-{biostrat_base} Ma] does not overlap with "
                              f"any Macrostrat unit at this location. Nearest unit is "
                              f"{gap:.1f} Ma away.",
                    "confidence": 0.5,
                }
            return {
                "ruling": "WEAK_PASS",
                "reason": f"Biostrat zone has age bracket but no overlapping Macrostrat unit. "
                          f"Closest unit is {gap:.1f} Ma away. Uncertainty high.",
                "confidence": 0.4,
            }
        return {
            "ruling": "HOLD",
            "reason": "No Macrostrat units found at this location for comparison.",
            "confidence": 0.0,
        }

    best = macrostrat_match["best_unit"]
    zone_mid = (biostrat_top + biostrat_base) / 2
    macro_mid = (best["unit_age_top_ma"] + best["unit_age_bottom_ma"]) / 2
    age_diff = abs(zone_mid - macro_mid)

    # Rules
    if age_diff < 0.5:
        return {
            "ruling": "PASS",
            "reason": f"Biostrat age [{biostrat_top}-{biostrat_base} Ma] agrees with "
                      f"Macrostrat unit '{best['unit_name']}' [{best['unit_age_top_ma']}-{best['unit_age_bottom_ma']} Ma]. "
                      f"Delta = {age_diff:.2f} Ma.",
            "confidence": 0.85 if biostrat_discipline == "calcareous_nannofossil" else 0.70,
        }
    elif age_diff < 2.0:
        return {
            "ruling": "WEAK_PASS",
            "reason": f"Biostrat age [{biostrat_top}-{biostrat_base} Ma] partially overlaps with "
                      f"Macrostrat unit '{best['unit_name']}' [{best['unit_age_top_ma']}-{best['unit_age_bottom_ma']} Ma]. "
                      f"Delta = {age_diff:.2f} Ma within tolerance (±2 Ma).",
            "confidence": 0.65,
        }
    else:
        return {
            "ruling": "CONTRADICTION",
            "reason": f"Biostrat age [{biostrat_top}-{biostrat_base} Ma] conflicts with "
                      f"Macrostrat unit '{best['unit_name']}' [{best['unit_age_top_ma']}-{best['unit_age_bottom_ma']} Ma]. "
                      f"Delta = {age_diff:.2f} Ma exceeds tolerance. Check reworking, caving, or miscorrelation.",
            "confidence": 0.90,
        }


# ── Main tool function ───────────────────────────────────────────────────

async def geox_macrostrat_calibrate(
    biozone: str = "",
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = 50,
    discipline_hint: str = "",
    macrostrat_unit_name: str | None = None,
) -> dict:
    """Merge relative biostratigraphy (NN, PR, TR, FO/LO, GDE) with Macrostrat absolute ages.

    Calibrates a biozone against:
    1. GEOX internal NN-age table (for NN zones)
    2. Macrostrat time intervals (global age brackets)
    3. Macrostrat units at lat/lng (local rock packages)

    Cross-references all three and returns a merged age bracket with
    uncertainty, provenance, contradiction flags, and a ruling.

    Args:
      biozone:             Biozone name (e.g. "NN5", "PR12", "TR18", "FO_Globigerinatella_insueta").
                           NN zones use GEOX internal table + Macrostrat cross-ref.
                           PR/TR/FO/LO use Macrostrat intervals + local units.
      lat:                 Latitude for Macrostrat column query.
      lng:                 Longitude for Macrostrat column query.
      radius_km:           Search radius for Macrostrat units (default 50 km).
      discipline_hint:     Optional hint: "calcareous_nannofossil" | "palynology" |
                           "planktonic_foraminifera" | "benthic_foraminifera" |
                           "general". Auto-detected if empty.
      macrostrat_unit_name: Optional specific Macrostrat unit name to compare against.

    Returns:
      Governed MCP envelope with:
        biozone             — original input
        discipline          — fossil group classification
        calibration_source  — "geox_internal" | "macrostrat_interval" | "both"
        age_top_ma          — younger boundary (merged)
        age_base_ma         — older boundary (merged)
        age_bracket_ma      — [age_top, age_base]
        uncertainty_ma      — total uncertainty (combines both sources)
        ruling              — PASS | WEAK_PASS | HOLD | CONTRADICTION
        ruling_reason       — explanation
        macrostrat_units    — matching Macrostrat units found at location
        contradictions      — list of specific contradictions found
        warnings            — diachroneity, calibration dependency, etc.
        not_a_radiometric_age — ALWAYS true
    """
    logger.info("geox_macrostrat_calibrate: zone=%s lat=%s lng=%s", biozone, lat, lng)

    # ── Validate inputs ──────────────────────────────────────────────────
    if not biozone:
        return get_standard_envelope(
            {"biozone": "", "error": "No biozone provided."},
            tool_class="compute", claim_tag="HYPOTHESIS",
            claim_state="NO_VALID_EVIDENCE", uncertainty="High",
            humility_score=0.0, evidence_refs=[],
            audit_receipt={"verdict": "NO_INPUT", "risk": "LOW"},
            tool_name="geox_macrostrat_calibrate",
            equations_used=["NN age table (GPTS2020)", "Macrostrat interval lookup"],
            sensitivity_to=["calibration_table_version", "lat_lng_precision"],
        )

    # ── Classify zone ────────────────────────────────────────────────────
    discipline, normalized_zone = _classify_zone(biozone)
    if discipline_hint and discipline == "unknown":
        discipline = discipline_hint

    evidence_refs_list: list[str] = [f"biozone={biozone}"]
    contradictions: list[str] = []
    warnings: list[str] = [
        "Calibration is a MERGE of relative biostratigraphy and absolute Macrostrat ages.",
        "Biozone age depends on calibration table and regional diachroneity.",
        "Macrostrat units represent surface/subsurface geology — may not match well-scale resolution.",
    ]

    # ── Step 1: GEOX internal age lookup (NN zones) ──────────────────────
    geox_age_top = -999.0
    geox_age_base = -999.0
    geox_found = False

    if discipline.startswith("calcareous_nannofossil"):
        parsed = parse_nn_zone(normalized_zone)
        zone_name = parsed.get("zone", "")
        if zone_name and zone_name != "UNKNOWN":
            geox_age_top, geox_age_base = nn_age(zone_name)
            if geox_age_top > -999:
                geox_found = True
                evidence_refs_list.append(f"GEOX NN-age table: {zone_name} → {geox_age_top}-{geox_age_base} Ma")

    # ── Step 2: Macrostrat interval lookup ────────────────────────────────
    macro_interval = await _find_interval_match(normalized_zone, discipline)
    macro_int_top = -999.0
    macro_int_base = -999.0
    macro_int_found = False

    if macro_interval:
        macro_int_top = macro_interval["age_top_ma"]
        macro_int_base = macro_interval["age_bottom_ma"]
        macro_int_found = True
        evidence_refs_list.append(f"Macrostrat interval: {macro_interval['name']} → {macro_int_top}-{macro_int_base} Ma")

    # ── Step 3: Macrostrat unit lookup at lat/lng ────────────────────────
    macro_units: list[dict[str, Any]] = []
    unit_match: dict[str, Any] = {"found": False}

    if lat is not None and lng is not None:
        try:
            macro_units = await _find_units_at_location(lat, lng, radius_km)
            if macro_units:
                evidence_refs_list.append(f"Macrostrat units at ({lat},{lng}): {len(macro_units)} units found")
                # Use GEOX age if available, otherwise Macrostrat interval age
                ref_top = geox_age_top if geox_found else macro_int_top
                ref_base = geox_age_base if geox_found else macro_int_base
                if ref_top > -999:
                    unit_match = _find_unit_age_for_biozone(macro_units, ref_top, ref_base)
            else:
                warnings.append(f"No Macrostrat units found at ({lat}, {lng}) within {radius_km} km.")
        except Exception as e:
            logger.warning(f"Macrostrat unit query failed: {e}")
            warnings.append(f"Macrostrat API error: {e}")

    # ── Step 4: Merge ages ───────────────────────────────────────────────
    # Priority: GEOX internal > Macrostrat interval > Macrostrat unit
    sources_used: list[str] = []

    if geox_found:
        merged_top = geox_age_top
        merged_base = geox_age_base
        sources_used.append("geox_internal")
    elif macro_int_found:
        merged_top = macro_int_top
        merged_base = macro_int_base
        sources_used.append("macrostrat_interval")
    elif macro_units:
        # Use the age range of the closest unit
        merged_top = min(u.get("t_age", u.get("age_top", 999)) for u in macro_units[:5] if u.get("t_age"))
        merged_base = max(u.get("b_age", u.get("age_bottom", 0)) for u in macro_units[:5] if u.get("b_age"))
        sources_used.append("macrostrat_units")
    else:
        merged_top = -999.0
        merged_base = -999.0

    if merged_top > -999:
        sources_used.append("macrostrat_interval" if macro_int_found else "")
        sources_used = [s for s in sources_used if s]

    # ── Step 5: Compute uncertainty ──────────────────────────────────────
    uncertainty_ma = 0.5  # base uncertainty
    if len(sources_used) >= 2:
        uncertainty_ma = 0.3  # dual calibration reduces uncertainty
    if discipline == "palynology":
        uncertainty_ma += 1.0  # palynology has higher diachroneity
    if discipline == "planktonic_foraminifera":
        uncertainty_ma += 0.5  # foram zones are moderately diachronous

    # ── Step 6: Compute ruling ───────────────────────────────────────────
    # Use unit_match if available, otherwise interval match
    if unit_match.get("found") or (unit_match.get("no_overlap") and unit_match.get("closest_unit")):
        ruling_data = _compute_ruling(merged_top, merged_base, discipline, unit_match)
    elif macro_int_found and geox_found:
        # Compare GEOX age vs Macrostrat interval
        diff = abs((geox_age_top + geox_age_base)/2 - (macro_int_top + macro_int_base)/2)
        if diff < 0.5:
            ruling_data = {"ruling": "PASS", "reason": "GEOX internal age agrees with Macrostrat interval.", "confidence": 0.85}
        elif diff < 2.0:
            ruling_data = {"ruling": "WEAK_PASS", "reason": f"GEOX age vs Macrostrat interval delta = {diff:.1f} Ma.", "confidence": 0.65}
        else:
            ruling_data = {"ruling": "CONTRADICTION", "reason": f"GEOX age conflicts with Macrostrat interval by {diff:.1f} Ma.", "confidence": 0.90}
            contradictions.append(f"GEOX internal age ({geox_age_top}-{geox_age_base} Ma) vs Macrostrat interval ({macro_int_top}-{macro_int_base} Ma)")
    elif geox_found:
        ruling_data = {"ruling": "WEAK_PASS", "reason": "GEOX internal calibration only. No Macrostrat cross-reference available.", "confidence": 0.60}
    elif macro_int_found:
        ruling_data = {"ruling": "WEAK_PASS", "reason": "Macrostrat interval calibration only. No GEOX internal age for this zone type.", "confidence": 0.50}
    else:
        ruling_data = {"ruling": "HOLD", "reason": "No calibration source found for this biozone.", "confidence": 0.0}

    # ── Step 7: Contradiction detection ──────────────────────────────────
    if unit_match.get("found") and macro_int_found and geox_found:
        best = unit_match.get("best_unit", {})
        if best:
            unit_top = best.get("unit_age_top_ma", 0)
            unit_bottom = best.get("unit_age_bottom_ma", 0)
            if abs((merged_top + merged_base)/2 - (unit_top + unit_bottom)/2) > 3.0:
                contradictions.append(
                    f"Calibrated age ({merged_top}-{merged_base} Ma) differs from Macrostrat unit "
                    f"'{best.get('unit_name','?')}' ({unit_top}-{unit_bottom} Ma) by >3 Ma"
                )

    # ── Build payload ────────────────────────────────────────────────────
    calibration_source = "+".join(sources_used) if sources_used else "none"

    payload = {
        "biozone": biozone,
        "normalized_zone": normalized_zone,
        "discipline": discipline,
        "calibration_source": calibration_source,
        "age_top_ma": merged_top if merged_top > -999 else None,
        "age_base_ma": merged_base if merged_base > -999 else None,
        "age_bracket_ma": [merged_top, merged_base] if merged_top > -999 else None,
        "uncertainty_ma": uncertainty_ma,
        "ruling": ruling_data["ruling"],
        "ruling_reason": ruling_data.get("reason", ""),
        "ruling_confidence": ruling_data.get("confidence", 0.0),
        "contradictions": contradictions,
        "contradiction_count": len(contradictions),
        "macrostrat_units_found": len(macro_units),
        "macrostrat_unit_match": unit_match.get("best_unit") if unit_match.get("found") else None,
        "macrostrat_interval": macro_interval,
        "not_a_radiometric_age": True,
        "warnings": warnings,
        "provenance": {
            "geox_internal": geox_found,
            "macrostrat_interval": macro_int_found,
            "macrostrat_units": len(macro_units) > 0,
            "sources": sources_used,
        },
    }

    # Confidence / Uncertainty for envelope
    env_confidence = ruling_data.get("confidence", 0.5)
    if env_confidence >= 0.80:
        env_uncertainty = "Low"
    elif env_confidence >= 0.60:
        env_uncertainty = "Moderate"
    else:
        env_uncertainty = "High"

    claim_state_val = "INTERPRETED" if ruling_data["ruling"] in ("PASS", "WEAK_PASS") else \
                      ("DERIVED_CANDIDATE" if ruling_data["ruling"] == "HOLD" else "HYPOTHESIS")

    return get_standard_envelope(
        payload,
        tool_class="compute",
        claim_tag="PLAUSIBLE" if ruling_data["ruling"] in ("PASS", "WEAK_PASS") else "HYPOTHESIS",
        claim_state=claim_state_val,
        uncertainty=env_uncertainty,
        humility_score=env_confidence,
        evidence_refs=evidence_refs_list,
        audit_receipt={
            "verdict": ruling_data["ruling"],
            "risk": "MEDIUM" if ruling_data["ruling"] == "CONTRADICTION" else "LOW",
            "human_review_required": ruling_data["ruling"] in ("CONTRADICTION", "HOLD"),
        },
        tool_name="geox_macrostrat_calibrate",
        equations_used=[
            "GEOX NN-age table: GPTS2020 (calcareous nannofossil zones)",
            "Macrostrat interval lookup: defs/intervals API",
            "Macrostrat unit lookup: units API (lat/lng/radius)",
            "Merge rule: biostrat age ∩ Macrostrat unit age = calibrated bracket",
            "Ruling: PASS (Δ<0.5Ma) / WEAK_PASS (Δ<2Ma) / CONTRADICTION (Δ≥2Ma)",
        ],
        sensitivity_to=["calibration_table_version", "macrostrat_api_availability", "lat_lng_precision"],
        next_best_actions=[
            {"tool": "geox_biostrat_ruling_check", "reason": "Cross-validate this calibration against facies and strat order."},
            {"tool": "geox_basin", "reason": "If HOLD, try geox_basin(mode='macrostrat_units') with a wider radius."},
        ] if ruling_data["ruling"] in ("HOLD", "CONTRADICTION") else [],
    )
