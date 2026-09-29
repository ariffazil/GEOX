"""
Copilot prototype v6 — v5 + regional interpretation + frequency proxy.

Original Copilot output: ROTAN1_regional_interpretation_v6.png + ROTAN1_frequency_proxy_v6.png
Algorithm: PNG → color-mask (R-G-B channels) → zero-crossing density as
**frequency proxy** (NOT true instantaneous frequency — explicitly acknowledged
limitation in Copilot output).

Three structural domains:
  1. Foreland (undeformed Dangerous Grounds basin fill)
  2. Thrust wedge (NW-verging NSPW slices)
  3. Mobile-shale province (mini-basins + diapirs, ROTAN-1 on D2 crest)

The frequency proxy principle (chaotic = low, layered = high) is what
`geox_seismic_display_spectral_character.v1` will formalize (forthcoming).

PUBLIC SYNTHETIC ONLY.
"""
from __future__ import annotations

from typing import Dict, List


# Frequency proxy readings from Copilot's v6 output (relabeled as ordinal tiers)
# Copilot emitted raw Hz values; we preserve them here ONLY as a record of what
# the prototype emitted. The NEW tool will produce ordinal tiers, not raw Hz.
COPILOT_V6_FREQ_PROXY: Dict[str, dict] = {
    "Foreland layered fill":  {"hz_proxy": 20, "ordinal": "highest"},
    "Top DG crust":           {"hz_proxy": 15, "ordinal": "high"},
    "NSPW wedge":             {"hz_proxy": 10, "ordinal": "low"},
    "D2 core":                {"hz_proxy": 11, "ordinal": "low"},
    "D3 core":                {"hz_proxy": 9.5, "ordinal": "lowest"},
    "MB-B fill":              {"hz_proxy": 17, "ordinal": "high"},
    "IVD-IVG drape":          {"hz_proxy": 15, "ordinal": "high"},
    "IVC @ ROTAN D2 crest":   {"hz_proxy": "broadband bright", "ordinal": "highest"},
    "IVC SE of D3":           {"hz_proxy": "dim", "ordinal": "lowest"},
    "Above D2 crest (chimney?)": {"hz_proxy": "no low-freq shadow", "ordinal": "no evidence"},
}


# Ordinal classification — what display_spectral_character.v1 will emit
ORDINAL_TIERS = ["highest", "high", "mid", "low", "lowest", "no_evidence"]


def classify_ordinal(proxy: float | str) -> str:
    """Map raw Hz proxy or text descriptor to ordinal tier.

    This is the FUNCTION that display_spectral_character.v1 will use.
    It NEVER returns absolute Hz — only ordinal tiers.
    """
    if isinstance(proxy, str):
        if "shadow" in proxy or "evidence" in proxy:
            return "no_evidence"
        if "broadband" in proxy or "dim" in proxy:
            return "mid"
        return "mid"
    if proxy >= 18:
        return "highest"
    if proxy >= 14:
        return "high"
    if proxy >= 11:
        return "mid"
    if proxy >= 8:
        return "low"
    return "lowest"


def ordinal_zone_table(proxy_table: Dict[str, dict] | None = None) -> List[dict]:
    """Generate the ordinal zone table — the canonical output of v1.

    Per the new tool spec: NO absolute Hz values, only ordinal tiers.
    """
    src = proxy_table or COPILOT_V6_FREQ_PROXY
    return [
        {"zone_id": zone, "ordinal": classify_ordinal(d["hz_proxy"]), "interpretation_key": zone}
        for zone, d in src.items()
    ]


if __name__ == "__main__":
    table = ordinal_zone_table()
    for row in table:
        print(row)
