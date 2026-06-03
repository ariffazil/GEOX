"""
GEOX Well Stratigraphy — L3: Sequence Stratigraphy Inference
═══════════════════════════════════════════════════════════════

Infers systems tracts and sequence stratigraphic surfaces from
geological packages and GR motif stacking patterns.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from typing import Any

# Depositional environment codes and their sequence stratigraphic context
DEPO_ENV_SYSTEMS_TRACTS: dict[str, dict[str, Any]] = {
    "FLUVIAL": {
        "context": "nonmarine",
        "typical_packages": ["FINING_UPWARD", "AMALGAMATED"],
        "surfaces": ["SB", "MFS", "FS"],
    },
    "TIDAL": {
        "context": "marginal_marine",
        "typical_packages": ["HETEROLITHIC", "FINING_UPWARD"],
        "surfaces": ["TS", "MFS", "SB"],
    },
    "SHOREFACE": {
        "context": "shallow_marine",
        "typical_packages": ["COARSENING_UPWARD", "HETEROLITHIC"],
        "surfaces": ["MFS", "TS", "SB"],
    },
    "SHELF": {
        "context": "offshore_marine",
        "typical_packages": ["HETEROLITHIC", "MIXED"],
        "surfaces": ["MFS", "SB"],
    },
    "DEEPWATER": {
        "context": "deep_marine",
        "typical_packages": ["AMALGAMATED", "MIXED", "COARSENING_UPWARD"],
        "surfaces": ["MFS", "SB"],
    },
    "CARBONATE": {
        "context": "shallow_marine",
        "typical_packages": ["BLOCKY", "MIXED"],
        "surfaces": ["SB", "MFS"],
    },
}

SYSTEMS_TRACT_ORDER = ["LST", "TST", "HST", "FSST"]


def infer_seq_strat(
    packages: list[dict[str, Any]],
    depo_env_code: str = "FLUVIAL",
    gr_cutoff_api: float = 75.0,
) -> dict[str, Any]:
    """
    L3 Sequence Stratigraphy Inference.

    Given geological packages and a depositional environment, assign
    systems tracts and identify key surfaces (SB, TS, MFS).

    Parameters
    ----------
    packages : list[dict]
        Geological packages from build_packages().
    depo_env_code : str, default "FLUVIAL"
        Depositional environment code. Must be a key in DEPO_ENV_SYSTEMS_TRACTS.
    gr_cutoff_api : float, default 75.0
        GR cutoff for sand/shale discrimination.

    Returns
    -------
    dict with keys:
        - systems_tracts: list of assigned systems tracts with depth ranges
        - surfaces: identified sequence stratigraphic surfaces
        - motif_summary: overview of GR motifs per tract
        - claim_state: INTERPRETED
    """
    depo = DEPO_ENV_SYSTEMS_TRACTS.get(depo_env_code, DEPO_ENV_SYSTEMS_TRACTS["FLUVIAL"])

    if not packages:
        return {
            "systems_tracts": [],
            "surfaces": [],
            "motif_summary": {},
            "message": "No packages provided. Cannot infer sequence stratigraphy.",
            "claim_state": "INSUFFICIENT_DATA",
        }

    # Partition packages by GR trend + stacking pattern
    tracts = _assign_systems_tracts(packages, depo)

    # Surface identification
    surfaces = _identify_surfaces(packages, tracts, depo, gr_cutoff_api)

    # Motif summary per tract
    summary = {}
    for tract in tracts:
        tract_pkgs = tract["packages"]
        motifs = [p["dominant_motif"] for p in tract_pkgs]
        summary[tract["tract"]] = {
            "n_packages": len(tract_pkgs),
            "top": round(tract_pkgs[0]["top"], 2) if tract_pkgs else None,
            "base": round(tract_pkgs[-1]["base"], 2) if tract_pkgs else None,
            "dominant_motifs": list(set(motifs)) if motifs else [],
            "stacking_patterns": list(set(p["stacking_pattern"] for p in tract_pkgs)),
        }

    return {
        "systems_tracts": tracts,
        "surfaces": surfaces,
        "motif_summary": summary,
        "depo_env_code": depo_env_code,
        "depo_context": depo["context"],
        "claim_state": "INTERPRETED",
    }


def _assign_systems_tracts(
    packages: list[dict[str, Any]],
    depo: dict[str, Any],
) -> list[dict[str, Any]]:
    """Assign systems tracts to packages based on stacking patterns."""
    tracts: list[dict[str, Any]] = []
    current_tract: list[dict[str, Any]] = []
    tract_idx = 0

    # Scan through packages and partition by stacking pattern changes
    expected = SYSTEMS_TRACT_ORDER[tract_idx] if tract_idx < len(SYSTEMS_TRACT_ORDER) else "HST"

    for pkg in packages:
        pattern = pkg.get("stacking_pattern", "MIXED")
        motif = pkg.get("dominant_motif", "UNKNOWN")

        # Detect tract boundary on major pattern shift
        if _is_tract_boundary(pattern, motif, current_tract, expected, depo):
            if current_tract:
                tracts.append(
                    {
                        "tract": expected,
                        "packages": current_tract,
                        "top": current_tract[0]["top"],
                        "base": current_tract[-1]["base"],
                    }
                )
                current_tract = []
                tract_idx += 1
                expected = SYSTEMS_TRACT_ORDER[tract_idx] if tract_idx < len(SYSTEMS_TRACT_ORDER) else "HST"

        current_tract.append(pkg)

    if current_tract:
        tracts.append(
            {
                "tract": expected,
                "packages": current_tract,
                "top": current_tract[0]["top"],
                "base": current_tract[-1]["base"],
            }
        )

    return tracts


def _is_tract_boundary(
    pattern: str,
    motif: str,
    current_tract: list[dict[str, Any]],
    expected: str,
    depo: dict[str, Any],
) -> bool:
    """Detect if a package boundary represents a systems tract change."""
    if not current_tract:
        return False

    last = current_tract[-1]
    last_pattern = last.get("stacking_pattern", "MIXED")

    # LST -> TST: coarsening-upward changes to fining-upward
    if expected == "LST" and pattern == "FINING_UPWARD" and last_pattern == "COARSENING_UPWARD":
        return True

    # TST -> HST: fining-upward changes to coarsening-upward
    if expected == "TST" and pattern == "COARSENING_UPWARD" and last_pattern == "FINING_UPWARD":
        return True

    # HST -> FSST: coarsening-upward changes to heterolithic/mixed
    if expected == "HST" and pattern in ("HETEROLITHIC", "MIXED") and last_pattern in ("COARSENING_UPWARD", "AMALGAMATED"):
        return True

    # Sharp motif change also triggers boundary
    if motif != last.get("dominant_motif") and current_tract:
        if len(current_tract) >= 3:
            return True

    return False


def _identify_surfaces(
    packages: list[dict[str, Any]],
    tracts: list[dict[str, Any]],
    depo: dict[str, Any],
    gr_cutoff: float,
) -> list[dict[str, Any]]:
    """Identify sequence stratigraphic surfaces from tract boundaries."""
    surfaces: list[dict[str, Any]] = []

    for i, tract in enumerate(tracts):
        base_pkg = tract["packages"][0]
        base_depth = base_pkg["top"]

        # Tract boundary = surface
        if i == 0:
            # Base of section: could be SB or SB/TS composite
            surfaces.append(
                {
                    "surface": "SB",
                    "depth": round(base_depth, 2),
                    "type": "sequence_boundary",
                    "context": "base_of_section",
                    "confidence": 0.5,
                    "claim_state": "INTERPRETED",
                }
            )
        else:
            # Tract boundary = systems tract transition surface
            prev_tract = tracts[i - 1]
            prev_tract_name = prev_tract["tract"]
            curr_tract_name = tract["tract"]

            if prev_tract_name == "LST" and curr_tract_name == "TST":
                surfaces.append(
                    {
                        "surface": "TS",
                        "depth": round(base_depth, 2),
                        "type": "transgressive_surface",
                        "context": f"{prev_tract_name}_{curr_tract_name}",
                        "confidence": 0.6,
                        "claim_state": "INTERPRETED",
                    }
                )
            elif prev_tract_name == "TST" and curr_tract_name == "HST":
                surfaces.append(
                    {
                        "surface": "MFS",
                        "depth": round(base_depth, 2),
                        "type": "maximum_flooding_surface",
                        "context": f"{prev_tract_name}_{curr_tract_name}",
                        "confidence": 0.7,
                        "claim_state": "INTERPRETED",
                    }
                )
            elif prev_tract_name == "HST" and curr_tract_name == "FSST":
                surfaces.append(
                    {
                        "surface": "SB",
                        "depth": round(base_depth, 2),
                        "type": "sequence_boundary",
                        "context": f"{prev_tract_name}_{curr_tract_name}",
                        "confidence": 0.5,
                        "claim_state": "INTERPRETED",
                    }
                )
            else:
                surfaces.append(
                    {
                        "surface": "STACKING_TRANSITION",
                        "depth": round(base_depth, 2),
                        "type": "stacking_pattern_change",
                        "context": f"{prev_tract_name}_{curr_tract_name}",
                        "confidence": 0.4,
                        "claim_state": "INTERPRETED",
                    }
                )

    # Always include final surface at base of deepest tract
    if tracts:
        last_tract = tracts[-1]
        last_base = last_tract["packages"][-1]["base"]
        surfaces.append(
            {
                "surface": "BASE_SECTION",
                "depth": round(last_base, 2),
                "type": "base_of_section",
                "context": "end_of_data",
                "confidence": 0.5,
                "claim_state": "INTERPRETED",
            }
        )

    return surfaces
