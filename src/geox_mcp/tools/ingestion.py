import json
import logging
import os
from typing import Any

import jsonschema

logger = logging.getLogger("geox.ingestion")

SCHEMA_DIR = "/root/geox/schemas/earth"


def load_schema(schema_name: str) -> dict:
    path = os.path.join(SCHEMA_DIR, schema_name)
    with open(path) as f:
        return json.load(f)


async def geox_las_inspect(las_metadata: dict[str, Any], las_curve_info: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Inspects LAS metadata and curve headers against GEOX Earth schemas before ingestion.
    """
    well_header_schema = load_schema("well_header.json")
    well_curve_schema = load_schema("well_log_curve.json")

    report = {"status": "VALID", "errors": [], "warnings": [], "metadata_validated": False, "curves_validated": 0}

    try:
        jsonschema.validate(instance=las_metadata, schema=well_header_schema)
        report["metadata_validated"] = True
    except jsonschema.exceptions.ValidationError as e:
        report["status"] = "INVALID"
        report["errors"].append(f"Header validation failed: {e.message}")

    for idx, curve in enumerate(las_curve_info):
        try:
            jsonschema.validate(instance=curve, schema=well_curve_schema)
            report["curves_validated"] += 1
        except jsonschema.exceptions.ValidationError as e:
            report["status"] = "INVALID"
            report["errors"].append(f"Curve {idx} validation failed: {e.message}")

    return report


async def geox_seismic_inspect(seismic_metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Inspects Seismic metadata against GEOX Earth schemas before ingestion.
    """
    seismic_schema = load_schema("seismic_volume_metadata.json")

    report = {"status": "VALID", "errors": [], "warnings": [], "metadata_validated": False}

    try:
        jsonschema.validate(instance=seismic_metadata, schema=seismic_schema)
        report["metadata_validated"] = True
    except jsonschema.exceptions.ValidationError as e:
        report["status"] = "INVALID"
        report["errors"].append(f"Seismic metadata validation failed: {e.message}")

    return report


async def geox_deviation_survey_inspect(deviation_metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Inspects deviation survey metadata against GEOX Earth schemas before ingestion.
    Enforces: depth unit, datum, MD increasing, TVD consistency.
    """
    schema = load_schema("deviation_survey.json")

    report = {"status": "VALID", "errors": [], "warnings": [], "metadata_validated": False, "checks": {}}

    try:
        jsonschema.validate(instance=deviation_metadata, schema=schema)
        report["metadata_validated"] = True
    except jsonschema.exceptions.ValidationError as e:
        report["status"] = "INVALID"
        report["errors"].append(f"Deviation survey validation failed: {e.message}")

    # Additional discipline checks
    md = deviation_metadata.get("md_values", [])
    tvd = deviation_metadata.get("tvd_values", [])

    # Check MD is monotonically increasing
    if md == sorted(md):
        report["checks"]["md_increasing"] = True
    else:
        report["status"] = "INVALID"
        report["errors"].append("MD values are not monotonically increasing")

    # Check MD and TVD arrays same length
    if len(md) == len(tvd):
        report["checks"]["depth_array_lengths_match"] = True
    else:
        report["status"] = "INVALID"
        report["errors"].append(f"MD ({len(md)}) and TVD ({len(tvd)}) arrays have different lengths")

    # Check TVD <= MD for each point
    violations = [i for i in range(len(md)) if tvd[i] > md[i]]
    if not violations:
        report["checks"]["tvd_le_md"] = True
    else:
        report["warnings"].append(f"TVD > MD at {len(violations)} points — possible data error")

    # Require unit and datum
    if not deviation_metadata.get("unit"):
        report["errors"].append("Missing depth unit — must specify 'm' or 'ft'")
    if not deviation_metadata.get("datum"):
        report["errors"].append("Missing datum — must specify KB, DF, GL, MSL, or other")

    return report


async def geox_tops_inspect(tops_metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Inspects well tops table metadata against GEOX Earth schemas before ingestion.
    Enforces: unit/datum consistency, positive thickness, confidence levels.
    """
    schema = load_schema("well_tops.json")

    report = {
        "status": "VALID",
        "errors": [],
        "warnings": [],
        "metadata_validated": False,
        "tops_validated": 0,
        "tops_with_negative_thickness": [],
    }

    try:
        jsonschema.validate(instance=tops_metadata, schema=schema)
        report["metadata_validated"] = True
    except jsonschema.exceptions.ValidationError as e:
        report["status"] = "INVALID"
        report["errors"].append(f"Tops table validation failed: {e.message}")

    tops = tops_metadata.get("tops", [])
    for i, top in enumerate(tops):
        report["tops_validated"] += 1

        # Check for negative thickness
        if top.get("base_md") and top.get("top_md"):
            if top["base_md"] <= top["top_md"]:
                report["tops_with_negative_thickness"].append(
                    {"marker": top.get("marker_name", f"top_{i}"), "top_md": top.get("top_md"), "base_md": top.get("base_md")}
                )
                report["warnings"].append(f"Marker '{top.get('marker_name')}': base <= top (possible logedit error)")

        # Flag low confidence picks
        if top.get("confidence", 1.0) < 0.5:
            report["warnings"].append(f"Marker '{top.get('marker_name')}' has low confidence: {top.get('confidence')}")

    # Require unit and datum at table level
    if not tops_metadata.get("unit"):
        report["errors"].append("Missing depth unit at table level")
    if not tops_metadata.get("datum"):
        report["errors"].append("Missing datum at table level")

    return report


async def geox_seismic_segy_inspect(segy_metadata: dict[str, Any]) -> dict[str, Any]:
    """
    Inspects SEG-Y file binary header metadata before ingestion.
    Inspect before ingest. Validate structure without mutating data.
    """
    schema = load_schema("segy_metadata.json")

    report = {"status": "VALID", "errors": [], "warnings": [], "metadata_validated": False, "checks": {}}

    try:
        jsonschema.validate(instance=segy_metadata, schema=schema)
        report["metadata_validated"] = True
    except jsonschema.exceptions.ValidationError as e:
        report["status"] = "INVALID"
        report["errors"].append(f"SEG-Y metadata validation failed: {e.message}")

    # Critical structural checks
    if not segy_metadata.get("coordinate_system"):
        report["warnings"].append("No CRS specified for CDP coordinates — may be unknown projection")

    if segy_metadata.get("coordinate_units") == "unknown":
        report["errors"].append("Coordinate units are unknown — cannot validate inline/xline scaling")

    if segy_metadata.get("format") == "UNKNOWN":
        report["errors"].append("SEG-Y format is unknown — cannot validate encoding")

    if segy_metadata.get("sample_interval_ms", 0) <= 0:
        report["errors"].append("Sample interval must be positive")

    if segy_metadata.get("trace_count", 0) <= 0:
        report["errors"].append("Trace count must be positive")

    if segy_metadata.get("inline_start") and segy_metadata.get("inline_end"):
        if segy_metadata["inline_end"] < segy_metadata["inline_start"]:
            report["errors"].append("inline_end < inline_start — coordinate range error")

    return report
