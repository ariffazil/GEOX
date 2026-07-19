"""
geox_diagnose — Domain Evidence Gate
════════════════════════════════════
Pre-flight check before any GEOX analysis. Answers:
  "Does GEOX have relevant evidence for this question?"

Verdicts:
  NO_DOMAIN_EVIDENCE — nothing relevant; use ChatGPT for general knowledge
  PARTIAL            — some evidence exists but incomplete
  READY              — evidence package complete for analysis

F2 TRUTH: Every verdict is based on scanned evidence stores, not assumptions.
F7 HUMILITY: Unknown domains return NO_DOMAIN_EVIDENCE, not guesses.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Canonical evidence stores — scanned at init
_GEOX_ROOT = Path(__file__).resolve().parents[3]  # /root/geox
_BASIN_PROFILES: dict[str, Path] = {}
_LITERATURE_REFS: dict[str, list[str]] = {}
_EVIDENCE_STORES_SCANNED = False


def _scan_evidence_stores() -> None:
    """Scan GEOX resources for available evidence. Runs once."""
    global _BASIN_PROFILES, _LITERATURE_REFS, _EVIDENCE_STORES_SCANNED
    if _EVIDENCE_STORES_SCANNED:
        return

    basins_dir = _GEOX_ROOT / "resources" / "basins"
    if basins_dir.exists():
        for yaml_file in basins_dir.glob("*.yaml"):
            name = yaml_file.stem.replace("_", " ").title()
            _BASIN_PROFILES[name] = yaml_file
            # Quick parse for literature refs
            try:
                content = yaml_file.read_text()
                refs = []
                for line in content.splitlines():
                    if "citation:" in line or "- citation:" in line:
                        refs.append(line.strip())
                if refs:
                    _LITERATURE_REFS[name] = refs
            except Exception:
                pass

    # Check for well data
    well_dirs = [_GEOX_ROOT / "data" / "geox_las", _GEOX_ROOT / "data" / "real_wells"]
    for wd in well_dirs:
        if wd.exists():
            for _las in wd.glob("*.las"):
                _BASIN_PROFILES.setdefault("Well Data", wd)
                break

    _EVIDENCE_STORES_SCANNED = True


def diagnose(
    query: str = "",
    domain: str = "",
    location: str = "",
    basin: str = "",
    required_evidence: list[str] | None = None,
) -> dict[str, Any]:
    """
    Diagnose whether GEOX has domain evidence for a question.

    Args:
        query: Natural-language question (e.g. "What caused this unconformity?")
        domain: Domain hint (e.g. "stratigraphy", "seismic", "biostratigraphy")
        location: Geographic hint (e.g. "Sabah", "Malay Basin")
        basin: Specific basin name
        required_evidence: What evidence would be needed (wells, seismic, literature, etc.)

    Returns:
        Verdict with evidence stores found, missing, and recommendation
    """
    _scan_evidence_stores()

    found_basins: list[str] = []
    found_literature: list[str] = []
    found_wells: bool = False

    # Search by basin name
    search_terms = [basin.lower()] if basin else []
    if location:
        search_terms.append(location.lower())
    if query:
        search_terms.append(query.lower())

    for profile_name, path in _BASIN_PROFILES.items():
        for term in search_terms:
            if term in profile_name.lower() or term in str(path).lower():
                found_basins.append(profile_name)
                if profile_name in _LITERATURE_REFS:
                    found_literature.extend(_LITERATURE_REFS[profile_name])
                break

    # Check wells — only relevant if query/basin/location matches
    has_geo_query = any(t in str(_BASIN_PROFILES).lower() for t in search_terms if len(t) > 3)
    if "Well Data" in _BASIN_PROFILES and has_geo_query:
        found_wells = True

    # Determine verdict
    if not found_basins and not found_wells and not found_literature:
        verdict = "NO_DOMAIN_EVIDENCE"
        recommendation = (
            "GEOX has no basin profiles, literature, well data, or domain evidence "
            "relevant to this question. Use ChatGPT for general knowledge. "
            "If this question requires Earth evidence, provide data files or request "
            "a basin profile be created."
        )
        evidence_level = 0
    elif found_basins and found_literature:
        verdict = "READY"
        recommendation = (
            f"GEOX has basin profile(s): {', '.join(found_basins[:5])}. "
            f"{len(found_literature)} literature references found. "
            "Evidence package sufficient for analysis."
        )
        evidence_level = 2
    else:
        verdict = "PARTIAL"
        missing = []
        if not found_basins:
            missing.append("basin profiles")
        if not found_literature:
            missing.append("literature references")
        recommendation = (
            f"GEOX has partial evidence: {', '.join(found_basins) if found_basins else 'no basin profiles'}. "
            f"Missing: {', '.join(missing)}. Analysis possible but limited."
        )
        evidence_level = 1

    return {
        "verdict": verdict,
        "evidence_level": evidence_level,
        "found": {
            "basins": found_basins[:10],
            "literature_count": len(found_literature),
            "well_data": found_wells,
        },
        "missing": [
            m
            for m in ["basin data", "literature", "well data", "seismic data"]
            if m.split()[0] not in str(found_basins + found_literature).lower()
        ],
        "recommendation": recommendation,
        "routing": {
            "if_NO_DOMAIN_EVIDENCE": "Use ChatGPT or provide Earth data",
            "if_PARTIAL": "Proceed with caution; gaps are declared",
            "if_READY": "Proceed to geox_basin, geox_evidence, or geox_contrast_detect",
        },
        "_meta": {
            "evidence_class": "OBSERVED",
            "confidence_cap": 0.95,
            "scanned_stores": ["basin_profiles", "literature_references", "well_data"],
            "governance": "EVIDENCE_GATE — determines whether GEOX or ChatGPT should answer.",
        },
    }
