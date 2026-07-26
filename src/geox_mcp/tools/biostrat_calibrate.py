"""biostrat_calibrate.py — GEOX biostratigraphic age calibration engine.

Phase T2.6: Calibrate relative biostratigraphy (zones + taxa) into calibrated age brackets.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from geox_mcp.tools.biostrat.zones import zone_age
from geox_mcp.tools.biostrat_falsify import geox_biostrat_falsify

logger = logging.getLogger("geox.biostrat_calibrate")


@dataclass
class TaxonRecord:
    name: str
    accepted_name: str
    rank: str = "genus"
    first_occurrence_ma: float | None = None
    last_occurrence_ma: float | None = None
    pbdb_oid: str | None = None
    n_occurrences: int | None = None
    extant: bool | None = None
    mikrotax_url: str | None = None
    provenance: str = "PBDB"


async def resolve_taxon(taxon_name: str) -> TaxonRecord | None:
    """Resolve taxon via PBDB and Mikrotax APIs."""
    if not taxon_name.strip():
        return None

    name = taxon_name.strip()

    # Query PBDB
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"https://paleobiodb.org/data1.2/taxa/list.json?name={name}&show=app")
            if resp.status_code == 200:
                payload = resp.json()
                records = payload.get("records", [])
                if records:
                    rec = records[0]
                    fad = rec.get("fea") if rec.get("fea") is not None else rec.get("firstapp_ea")
                    lad = rec.get("lea") if rec.get("lea") is not None else rec.get("lastapp_ea")
                    first_occurrence_ma = float(fad) if fad is not None else None
                    last_occurrence_ma = float(lad) if lad is not None else None
                    return TaxonRecord(
                        name=name,
                        accepted_name=rec.get("nam", name),
                        rank="genus",
                        first_occurrence_ma=first_occurrence_ma,
                        last_occurrence_ma=last_occurrence_ma,
                        pbdb_oid=str(rec.get("oid", "")),
                        provenance=f"taxon:PBDB ({name})",
                    )
    except Exception as exc:
        logger.warning("PBDB resolve_taxon failed for %s: %s", name, exc)

    # Fallback to Mikrotax check
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            m_resp = await client.get(f"https://www.mikrotax.org/system/api?name={name}&db=main")
            if m_resp.status_code == 200 and bool(m_resp.text.strip()):
                return TaxonRecord(
                    name=name,
                    accepted_name=name,
                    rank="genus",
                    first_occurrence_ma=None,
                    last_occurrence_ma=None,
                    mikrotax_url=f"https://www.mikrotax.org/system/index.php?taxon={name}",
                    provenance="Mikrotax (web only — no structured data)",
                )
    except Exception as exc:
        logger.warning("Mikrotax resolve_taxon failed for %s: %s", name, exc)

    return TaxonRecord(
        name=name,
        accepted_name=name,
        rank="genus",
        first_occurrence_ma=None,
        last_occurrence_ma=None,
        provenance=f"taxon:{name} (unresolved)",
    )


async def geox_biostrat_calibrate(
    taxon_name: str = "",
    zone_code: str = "",
    scheme: str = "",
    fossil_group: str = "",
    lithology: str = "",
    environment: str = "",
    run_falsify: bool = False,
    claim: str = "",
    region: str = "",
    sample_type: str = "",
) -> dict[str, Any]:
    """Calibrate relative biostratigraphy into age brackets with evidence and audit receipt."""
    sources_used: list[str] = []
    evidence_for: list[str] = []
    evidence_against: list[str] = []
    uncertainty_notes: list[str] = []
    falsification_summary: dict[str, Any] | None = None

    if not taxon_name.strip() and not zone_code.strip():
        audit_payload = {
            "taxon_name": taxon_name,
            "zone_code": zone_code,
            "verdict": "UNKNOWN",
            "reason": "EMPTY_INPUTS",
        }
        receipt_hash = hashlib.sha256(json.dumps(audit_payload, sort_keys=True).encode("utf-8")).hexdigest()
        audit_receipt = {
            "tool": "geox_biostrat_calibrate",
            "phase": "T2.6",
            "verdict": "UNKNOWN",
            "confidence": "BLOCKED",
            "popper_rule_applied": False,
            "hash": receipt_hash,
        }
        return {
            "ok": False,
            "tool": "geox_biostrat_calibrate",
            "reason_code": "EMPTY_INPUTS",
            "error": "Either taxon_name or zone_code must be provided.",
            "data": {
                "calibrated_age_min_ma": None,
                "calibrated_age_max_ma": None,
                "best_age_label": "UNBOUNDED",
                "input_basis": "empty",
                "sources_used": [],
                "evidence_for": [],
                "evidence_against": ["Empty inputs provided"],
                "uncertainty_notes": ["No zone or taxon provided"],
                "falsification_summary": None,
                "confidence_tier": "BLOCKED",
                "verdict": "UNKNOWN",
                "audit_receipt": audit_receipt,
            },
        }

    zone_min: float | None = None
    zone_max: float | None = None
    taxon_min: float | None = None
    taxon_max: float | None = None

    # 1. Zone lookup
    if zone_code.strip():
        z_min, z_max = zone_age(zone_code.strip())
        if z_min is not None and z_max is not None:
            zone_min, zone_max = z_min, z_max
            sources_used.append(f"zone:{zone_code.strip()}")
            evidence_for.append(f"Zone {zone_code.strip()} canonical age: {zone_min}-{zone_max} Ma")
        else:
            uncertainty_notes.append(f"Unrecognized zone code: {zone_code}")
            evidence_against.append(f"Zone {zone_code} not found in canonical scheme registry")

    # 2. Taxon lookup via resolve_taxon
    rec: TaxonRecord | None = None
    if taxon_name.strip():
        rec = await resolve_taxon(taxon_name.strip())
        if rec:
            sources_used.append(rec.provenance)
            if rec.first_occurrence_ma is not None and rec.last_occurrence_ma is not None:
                taxon_min = rec.last_occurrence_ma   # younger / top
                taxon_max = rec.first_occurrence_ma  # older / base
                evidence_for.append(f"PBDB FAD/LAD for {taxon_name}: {taxon_min}-{taxon_max} Ma")
            elif "Mikrotax" in rec.provenance:
                evidence_against.append("Mikrotax empty record (web only — no structured FAD/LAD data)")
                uncertainty_notes.append("Mikrotax empty — no numerical age range")
            else:
                evidence_against.append(f"Taxon {taxon_name} not found or no FAD/LAD in PBDB/Mikrotax (could not resolve)")
                uncertainty_notes.append(f"Unresolved taxon range for {taxon_name}")

        uncertainty_notes.append("Diachronous taxon range — broad uncertainty applied")

    # 3. Falsification check
    is_falsified = False
    if run_falsify or (lithology and environment):
        fals_res = await geox_biostrat_falsify(
            fossil_group=fossil_group or "calcareous_nannofossil",
            lithology=lithology,
            environment=environment,
            claim=claim,
            region=region,
            sample_type=sample_type,
        )
        falsification_summary = fals_res
        if not fals_res.get("ok") or fals_res.get("data", {}).get("verdict") == "FALSIFIED":
            is_falsified = True
            evidence_against.append("Incompatible lithology/environment falsifies in situ preservation claim")

    # 4. Overlap & Verdict computation
    input_basis = "zone_only"
    if taxon_name.strip() and zone_code.strip():
        input_basis = "taxon_plus_zone"
    elif taxon_name.strip():
        input_basis = "taxon_only"

    cal_min: float | None = None
    cal_max: float | None = None
    has_contradiction = False

    if zone_min is not None and zone_max is not None and taxon_min is not None and taxon_max is not None:
        inter_top = max(zone_min, taxon_min)
        inter_base = min(zone_max, taxon_max)
        if inter_top <= inter_base:
            cal_min, cal_max = inter_top, inter_base
            evidence_for.append(f"Taxon + Zone overlap narrowed bracket to {cal_min:.2f}-{cal_max:.2f} Ma")
        else:
            # GEOLOGICAL CONTRADICTION: empty intersection! Never swap or manufacture non-existent overlap.
            has_contradiction = True
            cal_min, cal_max = None, None
            evidence_against.append(
                f"Geological contradiction: Zone bracket [{zone_min:.2f}-{zone_max:.2f} Ma] "
                f"and Taxon bracket [{taxon_min:.2f}-{taxon_max:.2f} Ma] have zero overlap."
            )
            uncertainty_notes.append("Empty intersection between zone age and taxon age")
    elif zone_min is not None and zone_max is not None:
        cal_min, cal_max = zone_min, zone_max
    elif taxon_min is not None and taxon_max is not None:
        cal_min, cal_max = taxon_min, taxon_max

    if is_falsified or has_contradiction:
        verdict = "VOID" if is_falsified else "HOLD"
        confidence_tier = "BLOCKED"
    elif input_basis == "taxon_only" and (rec is None or rec.first_occurrence_ma is None):
        verdict = "HOLD"
        confidence_tier = "LOW"
    elif cal_min is not None and cal_max is not None:
        verdict = "PARTIAL" if input_basis == "zone_only" else "SABAR"
        confidence_tier = "MED" if input_basis == "zone_only" else "HIGH"
    else:
        verdict = "UNKNOWN"
        confidence_tier = "LOW"

    label = f"{cal_min:.2f}-{cal_max:.2f} Ma" if (cal_min is not None and cal_max is not None) else "UNBOUNDED"

    hash_payload = {
        "taxon_name": taxon_name,
        "zone_code": zone_code,
        "scheme": scheme,
        "cal_min": cal_min,
        "cal_max": cal_max,
        "sources_used": sorted(sources_used),
        "evidence_for": sorted(evidence_for),
        "evidence_against": sorted(evidence_against),
        "verdict": verdict,
    }
    receipt_hash = hashlib.sha256(json.dumps(hash_payload, sort_keys=True).encode("utf-8")).hexdigest()

    audit_receipt = {
        "tool": "geox_biostrat_calibrate",
        "phase": "T2.6",
        "verdict": verdict,
        "confidence": confidence_tier,
        "popper_rule_applied": is_falsified or has_contradiction,
        "hash": receipt_hash,
    }

    return {
        "ok": True,
        "tool": "geox_biostrat_calibrate",
        "data": {
            "calibrated_age_min_ma": cal_min,
            "calibrated_age_max_ma": cal_max,
            "best_age_label": label,
            "input_basis": input_basis,
            "sources_used": sources_used,
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "uncertainty_notes": uncertainty_notes,
            "falsification_summary": falsification_summary,
            "confidence_tier": confidence_tier,
            "verdict": verdict,
            "audit_receipt": audit_receipt,
        },
    }
