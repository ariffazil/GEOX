"""
geox_core.avo.castagna — Castagna mudrock line (1985) for Vp→Vs when DTS absent.

When dipole sonic (DTS) logs are unavailable — the most common case in legacy
wells — Vs must be predicted from Vp using empirical rock physics. The Castagna
mudrock line is the industry standard for water-saturated siliciclastic rocks:

  Vs = 0.862 · Vp - 1.172   (km/s)   [Castagna et al. 1985]

Equivalently:
  Vp = 1.16 · Vs + 1.36     (km/s)

CRITICAL LIMITATION: The mudrock line was derived for BRINE-saturated rocks.
In gas-charged zones, Vp drops dramatically but Vs barely moves (G invariance,
see Gassmann 1951 in avo_forward.py). Applying the mudrock line directly to
gas sands without correction would generate a phantom AVO anomaly.

GEOX workflow:
  1. Use Castagna to estimate Vs in brine-saturated zones (ACRisk 0.20)
  2. If gas suspected, apply Gassmann fluid substitution forward model
  3. Vs at gas ≈ Vs at brine (G invariance), so mudrock Vs is preserved to
     first order even in gas sands — but ACRisk climbs to 0.35

Reference: Castagna, J.P., Batzle, M.L., Eastwood, R.L. (1985).
"Relationships between compressional-wave and shear-wave velocities
in clastic silicate rocks." Geophysics 50(4), 571-581.

DITEMPA BUKAN DIBERI — Vp without Vs is a half-sentence. Castagna is the
empirical bridge, declared honestly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Union

import numpy as np


# ── Public surface ──────────────────────────────────────────────────


def castagna_mudrock_vp_to_vs(
    vp: Union[float, np.ndarray],
    unit: str = "m/s",
) -> Union[float, np.ndarray]:
    """Predict Vs from Vp using the Castagna mudrock line (brine-saturated).

    Args:
        vp: Vp in m/s (or km/s if unit="km/s")
        unit: "m/s" (default) or "km/s"

    Returns:
        Vs in same unit as input

    ACRisk: 0.20 (brine siliciclastic). 0.35 in gas zones (declare as flag).
    Validity: Vp in [1500, 6000] m/s. Outside range → flagged but computed.
    """
    if unit == "m/s":
        vp_km = np.asarray(vp) / 1000.0
    else:
        vp_km = np.asarray(vp)

    vs_km = 0.862 * vp_km - 1.172
    if unit == "m/s":
        return vs_km * 1000.0
    return vs_km


def castagna_mudrock_fallback(
    vp: Union[float, np.ndarray],
    fluid_zone: str = "brine",
    unit: str = "m/s",
) -> Dict[str, Any]:
    """Castagna fallback with explicit ACRisk and honest flags.

    Args:
        vp: Vp in m/s
        fluid_zone: "brine" (default) | "gas" | "oil" | "unknown"
            Affects the ACRisk (gas adds uncertainty because Vp drops but Vs barely changes)
        unit: "m/s" (default) or "km/s"

    Returns:
        Dict with keys: vs, acrisk, honest_flags, validity
    """
    vs = castagna_mudrock_vp_to_vs(vp, unit=unit)
    acrisk = 0.20
    honest_flags: list[str] = ["F2: Castagna mudrock line is empirical (brine siliciclastic)"]
    if fluid_zone == "gas":
        acrisk = 0.35
        honest_flags.append("F2: gas zone — Castagna may underestimate Vs (G invariance mitigates)")
    elif fluid_zone == "oil":
        acrisk = 0.28
    elif fluid_zone == "unknown":
        acrisk = 0.30
        honest_flags.append("F2: fluid unknown — assume worst case")

    return {
        "vs": vs,
        "acrisk": acrisk,
        "fluid_zone": fluid_zone,
        "honest_flags": honest_flags,
        "validity": "Vs ≈ 0.862·Vp − 1.172 (km/s), Castagna 1985",
    }


# ── Honest band ─────────────────────────────────────────────────────

CASTAGNA_HONEST_BAND: list[str] = [
    "F2: Castagna line is empirical, not derived from first principles",
    "F2: Valid for water-saturated siliciclastic rocks (sandstone + shale)",
    "F2: NOT valid for carbonates (use Greenberg-Castagna 1992 instead)",
    "F2: NOT valid for unconsolidated sands (use Hertz-Mindlin)",
    "F2: Vs < 100 m/s indicates fluid or no shear support — return HOLD",
    "F2: Always declare fluid_zone assumption in downstream envelopes",
]
