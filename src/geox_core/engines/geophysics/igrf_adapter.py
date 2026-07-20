"""
geox_core.engines.geophysics.igrf_adapter — P2 HIGH
DITEMPA BUKAN DIBERI — Magnetic fields are forged, not given.

Constitutional wrapper for IGRF-14 (International Geomagnetic Reference Field).

ppigrf is the cleanest embed — pure Python, no Fortran compiler,
defaults to IGRF-14 (November 2024 coefficients), pip-installable.

F2 TRUTH: IGRF is a mathematical model of the Earth's main magnetic field.
  It does not capture lithospheric anomalies — those require EMAG2 subtraction.
F7 HUMILITY: IGRF accuracy degrades beyond 5 years from epoch.
  For 2026 use: IGRF-14 is valid through 2025.
F4 CLARITY: All outputs carry epoch, coordinate system, and field component.

Requires: ppigrf
Install: pip install ppigrf
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import numpy as np

logger = logging.getLogger("geox.engines.igrf_adapter")

_PPIGRF_VERSION: str | None = None
_PPIGRF_AVAILABLE: bool = False

try:
    import ppigrf as _pp

    _PPIGRF_VERSION = getattr(_pp, "__version__", "unknown")
    _PPIGRF_AVAILABLE = True
except ImportError:
    _PPIGRF_AVAILABLE = False


def _sha256_params(params: dict) -> str:
    canonical = json.dumps(params, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


class IGRFAdapter:
    """
    Canonical IGRF bridge for GEOX geomagnetic calculations.

    Supports:
      - IGRF-14 field components (Be, Bn, Bu = East, North, Up)
      - Magnetic declination (D) — essential for directional drilling
      - Magnetic inclination (I) — for MWD gyro checks
      - Total field intensity (F)
      - Horizontal intensity (H)
      - Secular variation (annual change rate)

    Canonical uses:
      W10 — Magnetic declination correction for seismic acquisition
      W10 — MWD gyro drift correction for deviated wells
      W13 — Magnetic anomaly stripping (observed TMI - IGRF = crustal anomaly)
    """

    def __init__(self) -> None:
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        if not _PPIGRF_AVAILABLE:
            raise ImportError("ppigrf is required for IGRF geomagnetic calculations. Install with: pip install ppigrf")

    def compute_igrf(
        self,
        latitude_deg: float,
        longitude_deg: float,
        altitude_m: float,
        epoch_year: float | None = None,
    ) -> dict[str, Any]:
        """
        Compute IGRF-14 field components at a given location and epoch.

        Args:
            latitude_deg: Geodetic latitude [degrees, WGS-84].
            longitude_deg: East longitude [degrees].
            altitude_m: Altitude above WGS-84 ellipsoid [m].
            epoch_year: Decimal year (e.g. 2026.5). If None → current date.

        Returns:
            IGRF field components: Be, Bn, Bu, D, I, F, H + secular variation.
        """
        import ppigrf as pp

        if epoch_year is None:
            import datetime

            now = datetime.datetime.now()
            epoch_year = now.year + (now.timetuple().tm_yday - 1) / 365.25

        # ppigrf.igrf returns (Be, Bn, Bu) in nanotesla
        Be, Bn, Bu = pp.igrf(latitude_deg, longitude_deg, altitude_m, epoch_year)

        # Derived quantities
        H = np.sqrt(Be**2 + Bn**2)  # horizontal intensity [nT]
        F = np.sqrt(H**2 + Bu**2)  # total intensity [nT]

        # Declination [degrees, positive east]
        D = np.arctan2(Be, Bn) * 180 / np.pi

        # Inclination [degrees, positive down]
        I = np.arctan2(Bu, H) * 180 / np.pi

        # Secular variation (annual change in field)
        dBe, dBn, dBu = pp.igrf(latitude_deg, longitude_deg, altitude_m, epoch_year + 1.0, isv=1, iextrap=0)
        dD = np.arctan2(dBe, dBn) * 180 / np.pi - D
        dI = np.arctan2(dBu, np.sqrt(dBe**2 + dBn**2)) * 180 / np.pi - I
        dF = np.sqrt(dBe**2 + dBn**2 + dBu**2) - F

        params_hash = _sha256_params(
            {
                "lat": latitude_deg,
                "lon": longitude_deg,
                "alt_m": altitude_m,
                "epoch": epoch_year,
                "model": "IGRF-14",
            }
        )

        return {
            "status": "COMPUTED",
            "method": "igrf_14",
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "altitude_m": altitude_m,
            "epoch_year": epoch_year,
            "field_components_nT": {
                "Be_east_nT": float(Be),
                "Bn_north_nT": float(Bn),
                "Bu_up_nT": float(Bu),
            },
            "declination_deg": float(D),
            "inclination_deg": float(I),
            "horizontal_intensity_nT": float(H),
            "total_intensity_nT": float(F),
            "secular_variation": {
                "dD_deg_per_yr": float(dD),
                "dI_deg_per_yr": float(dI),
                "dF_nT_per_yr": float(dF),
            },
            "epistemic_label": "CLAIM",
            "confidence": "HIGH",
            "caveats": [
                "IGRF models the core main field — NOT lithospheric anomalies",
                "Subtract IGRF from observed TMI to get crustal anomaly",
                "IGRF-14 valid through 2025 — extrapolate beyond with caution",
                "Accuracy degrades near geomagnetic poles",
            ],
            "library": "ppigrf",
            "library_version": _PPIGRF_VERSION,
            "params_hash": params_hash,
        }

    def magnetic_declination(
        self,
        latitude_deg: float,
        longitude_deg: float,
        altitude_m: float = 0.0,
        epoch_year: float | None = None,
    ) -> dict[str, Any]:
        """
        Magnetic declination D at a location.

        Critical for:
          - Seismic acquisition azimuth control
          - MWD (Measurement While Drilling) gyro correction
          - Structural azimuth referencing (fault strikes, fold axes)

        Args:
            latitude_deg: Latitude [degrees].
            longitude_deg: Longitude [degrees].
            altitude_m: Altitude [m above ellipsoid].
            epoch_year: Decimal year (None = now).

        Returns:
            Declination in degrees (positive = east, negative = west).
        """
        result = self.compute_igrf(latitude_deg, longitude_deg, altitude_m, epoch_year)
        declination = result["declination_deg"]

        return {
            "status": "COMPUTED",
            "method": "magnetic_declination",
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "altitude_m": altitude_m,
            "epoch_year": result["epoch_year"],
            "declination_deg": declination,
            "declination_cardinal": self._cardinal_direction(declination),
            "epistemic_label": "CLAIM",
            "confidence": "HIGH",
            "caveats": [
                "Use for survey correction only — not lithospheric interpretation",
                "Annual change rate: {:.3f} deg/yr".format(result["secular_variation"]["dD_deg_per_yr"]),
            ],
            "library": "ppigrf",
            "library_version": _PPIGRF_VERSION,
            "params_hash": result["params_hash"],
        }

    def strip_crustal_anomaly(
        self,
        observed_tmi_nT: float,
        latitude_deg: float,
        longitude_deg: float,
        altitude_m: float = 0.0,
        epoch_year: float | None = None,
    ) -> dict[str, Any]:
        """
        Strip IGRF main field from observed TMI to isolate crustal anomaly.

        Formula: ΔF_crustal = F_observed − F_IGRF

        This is the starting point for magnetic interpretation — the anomaly
        reflects magnetic mineral concentration (magnetite), fault/fold patterns,
        and intrusive bodies.

        Args:
            observed_tmi_nT: Total magnetic intensity observed at survey [nT].
            latitude_deg: Survey location latitude.
            longitude_deg: Survey location longitude.
            altitude_m: Survey altitude [m].
            epoch_year: Survey epoch (None = now).

        Returns:
            Crustal magnetic anomaly [nT] + IGRF reference.
        """
        igrf = self.compute_igrf(latitude_deg, longitude_deg, altitude_m, epoch_year)
        F_igrf = igrf["total_intensity_nT"]
        anomaly_nT = observed_tmi_nT - F_igrf

        return {
            "status": "COMPUTED",
            "method": "crustal_anomaly_stripped",
            "observed_tmi_nT": observed_tmi_nT,
            "igrf_reference_nT": float(F_igrf),
            "crustal_anomaly_nT": float(anomaly_nT),
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
            "altitude_m": altitude_m,
            "epoch_year": igrf["epoch_year"],
            "epistemic_label": "DERIVED",
            "confidence": "MEDIUM",
            "caveats": [
                "Assumes IGRF main field is correct — model errors propagate into anomaly",
                "Crustal anomaly still contains induced + remanent components — separate with Vector Magnetic data if possible",
                "High latitude (>60°): IGRF accuracy degrades",
            ],
            "library": "ppigrf",
            "library_version": _PPIGRF_VERSION,
            "params_hash": igrf["params_hash"],
        }

    @staticmethod
    def _cardinal_direction(declination_deg: float) -> str:
        """Convert declination to cardinal direction string."""
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = int((declination_deg % 360 + 11.25) / 22.5) % 16
        return dirs[ix]


def get_adapter() -> IGRFAdapter:
    """Factory."""
    return IGRFAdapter()
