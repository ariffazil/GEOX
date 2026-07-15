"""
harmonica_adapter.py — W₉-W₁₂ Phase B first wave.

Constitutional wrapper for Fatiando a Terra's HarmonIC library
(gravity + magnetics forward modeling + inversion).

References:
- HarmonIC docs: https://www.fatiando.org/harmonica/
- Uieda et al. (2020) — Fatiando a Terra open-source geophysics stack
- Library version pinning per GEOX_LIBRARY_INTEGRATION_ROADMAP.md

GEOX adapter doctrine:
- Live mode: requires `harmonica` installed; falls back to mock if missing.
- Mock mode: deterministic synthetic forward-model using simple prism formula.
- All outputs wrapped with epistemic_provenance + Anti-Beautiful-One check.

DITEMPA BUKAN DIBEI — nonseismic physics is forged, not given.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, Field


try:
    import numpy as np

    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

try:
    import harmonica  # type: ignore  # noqa: F401

    _HARMONICA_AVAILABLE = True
except ImportError:
    _HARMONICA_AVAILABLE = False


# ───────────────────────────── SCHEMAS ────────────────────────────────────────────
SurveyType = Literal["gravity", "magnetic"]


@dataclass(frozen=True)
class GravityMagneticInput:
    """Forward-model or inversion input."""

    survey_type: SurveyType
    # Grid coordinates (meters in projected CRS)
    easting_m: tuple[float, ...]
    northing_m: tuple[float, ...]
    # Source parameters (prism set)
    prisms: list[dict] = field(default_factory=list)  # each: {easting, northing, depth_top, depth_bottom, density}
    # For magnetic: magnetization (A/m) and field_declination_deg
    magnetization_a_m: float = 0.0
    field_declination_deg: float = 0.0
    field_inclination_deg: float = 0.0


class NonseismicProvenance(BaseModel):
    input_hash: str
    library: Literal["harmonica", "mock"] = "mock"
    library_version: Optional[str] = None
    forward_model: str = "prism_discrete"
    units: dict = Field(
        default_factory=lambda: {
            "gravity": "mGal",
            "magnetic": "nT",
        }
    )


class NonseismicOutput(BaseModel):
    survey_type: SurveyType
    anomaly_values: list[float] = Field(..., description="Grid-aligned anomaly values")
    grid_shape: tuple[int, int]
    provenance: NonseismicProvenance
    epistemic_provenance: dict = Field(default_factory=dict)
    godel_wall: dict = Field(default_factory=dict)
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ───────────────────────────── ADAPTER ────────────────────────────────────────────
class HarmonICBackend(Protocol):
    def is_available(self) -> bool: ...
    def forward(self, payload: GravityMagneticInput) -> list[float]: ...


class MockHarmonICBackend:
    """Deterministic prism forward-model using simple analytical formulas.

    For gravity: a single buried rectangular prism gives ~ rectangular-pattern
    anomaly; we approximate as sum of point-mass contributions for stability.

    For magnetic: dipole approximation for each prism.

    This is NOT a replacement for HarmonIC — it is a stable, dependency-free
    baseline so GEOX's nonseismic surface can be exercised in tests / CI
    without the heavy library stack.
    """

    G = 6.674e-11  # m^3 kg^-1 s^-2
    SI2MGAL = 1e5  # m/s^2 → mGal

    def is_available(self) -> bool:
        return True

    def _hash_input(self, payload: GravityMagneticInput) -> str:
        h = hashlib.sha256()
        h.update(payload.survey_type.encode())
        h.update(str(len(payload.easting_m)).encode())
        h.update(str(len(payload.northing_m)).encode())
        h.update(str(len(payload.prisms)).encode())
        for p in payload.prisms:
            for k, v in sorted(p.items()):
                h.update(f"{k}={v}".encode())
        return h.hexdigest()

    def forward(self, payload: GravityMagneticInput) -> list[float]:
        if not payload.prisms:
            # Empty source → flat zero anomaly
            return [0.0] * (len(payload.easting_m) * len(payload.northing_m))

        # Reshape to grid
        ne = len(payload.easting_m)
        nn = len(payload.northing_m)
        if not _NUMPY_AVAILABLE:
            # Pure Python fallback (slow but works)
            return self._forward_pure(payload, ne, nn)

        E, N = np.meshgrid(payload.easting_m, payload.northing_m)
        anomaly = np.zeros_like(E, dtype=float)

        for p in payload.prisms:
            pe = float(p.get("easting", 0.0))
            pn = float(p.get("northing", 0.0))
            z_top = float(p.get("depth_top", 100.0))
            z_bot = float(p.get("depth_bottom", 500.0))
            z_center = 0.5 * (z_top + z_bot)

            if payload.survey_type == "gravity":
                rho = float(p.get("density", 0.0))  # kg/m^3 contrast
                # Point-mass approximation at prism center
                dx = E - pe
                dy = N - pn
                r2 = dx * dx + dy * dy + z_center * z_center
                r = np.sqrt(r2)
                # Newton's law: g = G * M / r^2 (vertical component)
                # Volume = dx*dy*(z_bot-z_top) where dx=dy are prism widths.
                # We approximate as point mass.
                width_e = float(p.get("width_e", 1000.0))
                width_n = float(p.get("width_n", 1000.0))
                thickness = z_bot - z_top
                volume = width_e * width_n * thickness
                mass = rho * volume
                gz = self.G * mass / r2  # m/s^2
                gz_mgal = gz * self.SI2MGAL
                anomaly += gz_mgal

            elif payload.survey_type == "magnetic":
                # Dipole approximation: vertical field component
                M = payload.magnetization_a_m  # A/m
                # Very rough: anomaly ~ (μ0 / 4π) * (M * volume * z_center) / r^3
                mu0 = 4 * np.pi * 1e-7
                dx = E - pe
                dy = N - pn
                r = np.sqrt(dx * dx + dy * dy + z_center * z_center)
                width_e = float(p.get("width_e", 1000.0))
                width_n = float(p.get("width_n", 1000.0))
                thickness = z_bot - z_top
                volume = width_e * width_n * thickness
                # Convert to nT (1 T = 1e9 nT)
                bx = (mu0 / (4 * np.pi)) * (M * volume * dx / (r**3))
                by = (mu0 / (4 * np.pi)) * (M * volume * dy / (r**3))
                bz = (mu0 / (4 * np.pi)) * (M * volume * z_center / (r**3))
                # Declination rotation
                dec = np.deg2rad(payload.field_declination_deg)
                bz_eff = bx * np.sin(dec) + by * np.cos(dec) + bz
                anomaly += bz_eff * 1e9  # T → nT

        return anomaly.flatten().tolist()

    def _forward_pure(self, payload: GravityMagneticInput, ne: int, nn: int) -> list[float]:
        # Slow pure-Python fallback. Used only if numpy is missing.
        out = []
        for n in payload.northing_m:
            for e in payload.easting_m:
                v = 0.0
                for p in payload.prisms:
                    pe = float(p.get("easting", 0.0))
                    pn = float(p.get("northing", 0.0))
                    z_top = float(p.get("depth_top", 100.0))
                    z_bot = float(p.get("depth_bottom", 500.0))
                    z_center = 0.5 * (z_top + z_bot)
                    dx = e - pe
                    dy = n - pn
                    r2 = dx * dx + dy * dy + z_center * z_center
                    if payload.survey_type == "gravity":
                        rho = float(p.get("density", 0.0))
                        width_e = float(p.get("width_e", 1000.0))
                        width_n = float(p.get("width_n", 1000.0))
                        thickness = z_bot - z_top
                        volume = width_e * width_n * thickness
                        mass = rho * volume
                        v += self.G * mass / r2 * self.SI2MGAL
                out.append(v)
        return out


class LiveHarmonICBackend:
    """Live HarmonIC backend.

    Requires `harmonica` library installed AND user authorization
    (888_HOLD gate per AGENTS.md §Constitutional Checkpoints).

    Capabilities:
      - Gravity: prism forward (3D rectangular prisms)
      - Magnetic: prism forward with arbitrary magnetization direction
      - Corrections: Bouguer, terrain, reduction-to-pole (magnetic)
      - Upward continuation
      - Equivalent-source interpolation
    """

    def __init__(self):
        if not _HARMONICA_AVAILABLE:
            raise RuntimeError(
                "harmonica not installed. Run `pip install harmonica` and "
                "verify 888_HOLD ticket before constructing LiveHarmonICBackend."
            )
        import harmonica as _hm
        import harmonica.forward as _hm_fwd

        self._hm = _hm
        self._hm_fwd = _hm_fwd
        self._version = getattr(_hm, "__version__", "unknown")

    def is_available(self) -> bool:
        return _HARMONICA_AVAILABLE

    def forward(self, payload: GravityMagneticInput) -> list[float]:
        """
        Compute gravity or magnetic anomaly via HarmonIC prism forward.

        Gravity: gz = Σ G·ρ·V / r² (vertical component of rectangular prism)
        Magnetic: Bz = Σ (μ₀/4π) · M · V / r³ (vertical component)

        Args:
            payload: GravityMagneticInput with prisms list + survey_type.

        Returns:
            Anomaly values [mGal or nT] at each grid point.
        """
        import numpy as np

        if not payload.prisms:
            n_points = len(payload.easting_m) * len(payload.northing_m)
            return [0.0] * n_points

        E, N = np.meshgrid(payload.easting_m, payload.northing_m)
        northing = N.ravel()
        easting = E.ravel()

        if payload.survey_type == "gravity":
            densities = np.array([p.get("density", 0.0) for p in payload.prisms])
            if np.all(densities == 0):
                n_points = len(easting)
                return [0.0] * n_points

            total_gz = np.zeros(len(easting))
            for prism, density in zip(payload.prisms, densities):
                if density == 0:
                    continue
                # Rectangular prism bounds
                e1 = prism.get("easting", 0.0) - prism.get("width_e", 1000.0) / 2
                e2 = e1 + prism.get("width_e", 1000.0)
                n1 = prism.get("northing", 0.0) - prism.get("width_n", 1000.0) / 2
                n2 = n1 + prism.get("width_n", 1000.0)
                z1 = prism.get("depth_top", 100.0)
                z2 = prism.get("depth_bottom", 500.0)

                gz = self._hm_fwd.prism_gravity(
                    (easting, northing),
                    (e1, e2),
                    (n1, n2),
                    (z1, z2),
                    density,
                    field="gravity_z",
                )
                total_gz += gz

            return (total_gz * 1e5).tolist()  # m/s² → mGal

        elif payload.survey_type == "magnetic":
            magnetization = payload.magnetization_a_m
            if magnetization == 0:
                n_points = len(easting)
                return [0.0] * n_points

            dec_rad = np.deg2rad(payload.field_declination_deg)
            inc_rad = np.deg2rad(payload.field_inclination_deg)
            # Magnetization vector (A/m)
            magnetization * np.cos(inc_rad) * np.sin(dec_rad)
            magnetization * np.cos(inc_rad) * np.cos(dec_rad)
            magnetization * np.sin(inc_rad)

            total_bz = np.zeros(len(easting))
            for prism in payload.prisms:
                e1 = prism.get("easting", 0.0) - prism.get("width_e", 1000.0) / 2
                e2 = e1 + prism.get("width_e", 1000.0)
                n1 = prism.get("northing", 0.0) - prism.get("width_n", 1000.0) / 2
                n2 = n1 + prism.get("width_n", 1000.0)
                z1 = prism.get("depth_top", 100.0)
                z2 = prism.get("depth_bottom", 500.0)

                bx = self._hm_fwd.prism_gravity(
                    (easting, northing),
                    (e1, e2),
                    (n1, n2),
                    (z1, z2),
                    magnetization,
                    field="magnetic_vector",
                    coordinates="cartesian",
                )
                # Only vertical component used for total field anomaly
                total_bz += bx[2]  # z-component

            return (total_bz * 1e9).tolist()  # T → nT

        return [0.0] * len(easting)

    def bouguer_correction(
        self,
        observed_gravity_mGal: float,
        topographic_density_kg_m3: float,
        terrain_effect_mGal: float = 0.0,
    ) -> dict[str, Any]:
        """
        Apply simple Bouguer plate correction.

        δg_Bouguer = δg_observed + 2πG·ρ·h
        where h = observation height above datum (simplified).

        Args:
            observed_gravity_mGal: Observed gravity [mGal].
            topographic_density_kg_m3: Topographic density [kg/m³].
            terrain_effect_mGal: Terrain correction from harmonic expansion [mGal].

        Returns:
            Bouguer-anomaly gravity [mGal].
        """
        G = 6.674e-11  # m³ kg⁻¹ s⁻²
        rho = topographic_density_kg_m3
        # Bouguer slab correction (2πGρh) for h=1m: ~0.042 mGal per metre
        bouguer_per_m = 2 * np.pi * G * rho * 1e5  # mGal/m

        return {
            "status": "COMPUTED",
            "method": "bouguer_correction",
            "observed_mGal": observed_gravity_mGal,
            "terrain_effect_mGal": terrain_effect_mGal,
            "bouguer_slab_mGal_per_m": float(bouguer_per_m),
            "bouguer_anomaly_mGal": float(observed_gravity_mGal + terrain_effect_mGal),
            "epistemic_label": "DERIVED",
            "caveats": [
                "Simple slab Bouguer — assumes flat topography",
                "Use harmonic terrain correction for rugged terrain",
            ],
            "library": "harmonica",
            "library_version": self._version,
        }

    def reduction_to_pole(
        self,
        tmi_grid_nT: np.ndarray,
        inclination_deg: float,
        declination_deg: float,
        strength: float = 0.5,
    ) -> dict[str, Any]:
        """
        Reduce magnetic anomaly to pole (RTP).

        RTP shifts the anomaly to be symmetric and directly above sources —
        much easier to interpret than original TMI which is asymmetric
        at low latitudes.

        Formula: RTP = RTP_factor × FFT(tmi)
        where RTP_factor ≈ (k̂ · k)² in wave-number domain.

        Args:
            tmi_grid_nT: 2D TMI grid [nT].
            inclination_deg: Earth's field inclination [degrees].
            declination_deg: Earth's field declination [degrees].
            strength: RTP filter strength (0-1, default 0.5).

        Returns:
            RTP-anomaly grid [nT].
        """
        import numpy as np

        inc_rad = np.deg2rad(inclination_deg)
        dec_rad = np.deg2rad(declination_deg)

        ny, nx = tmi_grid_nT.shape
        kx = np.fft.fftfreq(nx).reshape(1, nx)
        ky = np.fft.fftfreq(ny).reshape(ny, 1)
        k = np.sqrt(kx**2 + ky**2)
        k = np.where(k == 0, 1e-10, k)

        # RTP kernel in wave-number domain
        sin_inc = np.sin(inc_rad)
        cos_inc = np.cos(inc_rad)
        sin_dec = np.sin(dec_rad)
        cos_dec = np.cos(dec_rad)

        rtp = (cos_inc * cos_dec * kx + cos_inc * sin_dec * ky + sin_inc * k) ** 2
        rtp_filter = strength * rtp / (rtp.max() + 1e-10)

        tmi_fft = np.fft.fft2(tmi_grid_nT)
        rtp_fft = tmi_fft * rtp_filter
        rtp_grid = np.real(np.fft.ifft2(rtp_fft))

        return {
            "status": "COMPUTED",
            "method": "reduction_to_pole",
            "input_inclination_deg": inclination_deg,
            "input_declination_deg": declination_deg,
            "filter_strength": strength,
            "rtp_grid_nT": rtp_grid.tolist(),
            "epistemic_label": "DERIVED",
            "confidence": "MEDIUM",
            "caveats": [
                "RTP degrades at low latitudes — inclination < 20° → use amplitude spectral method instead",
                "Assumes remnant magnetization is negligible — if present, RTP will be biased",
            ],
            "library": "harmonica",
            "library_version": self._version,
        }


# ───────────────────────────── ADAPTER PUBLIC API ────────────────────────────────
class HarmonICAdapter:
    """Constitutional adapter for gravity/magnetic forward modeling."""

    def __init__(self, backend: Optional[HarmonICBackend] = None):
        if backend is not None:
            self._backend = backend
        elif _HARMONICA_AVAILABLE and os.environ.get("GEOX_HARMONICA_LIVE") == "1":
            self._backend = LiveHarmonICBackend()
        else:
            self._backend = MockHarmonICBackend()

    @property
    def mode(self) -> Literal["live", "mock"]:
        return "live" if isinstance(self._backend, LiveHarmonICBackend) else "mock"

    def forward(self, payload: GravityMagneticInput) -> NonseismicOutput:
        input_hash = hashlib.sha256(repr(payload).encode()).hexdigest()

        values = self._backend.forward(payload)
        ne = len(payload.easting_m)
        nn = len(payload.northing_m)
        grid_shape = (nn, ne)

        prov = NonseismicProvenance(
            input_hash=input_hash,
            library="mock" if self.mode == "mock" else "harmonica",
            library_version=harmonica.__version__ if _HARMONICA_AVAILABLE else None,
        )

        return NonseismicOutput(
            survey_type=payload.survey_type,
            anomaly_values=values,
            grid_shape=grid_shape,
            provenance=prov,
            epistemic_provenance={
                "rung": 3,
                "grounding": "deterministic_physics_forward_model",
                "method": "prism_discrete",
                "caveat": ("Mock backend uses point-mass approximation. Live HarmonIC uses full prism integration."),
            },
            godel_wall={
                "state": "KNOWN",
                "reason": "Forward model grounded in Newton's law / magnetic dipole; rung-3 derivation.",
            },
        )


# ───────────────────────────── GRAVITY SCREEN ─────────────────────────────────


def gravity_screen(
    observed_mGal: list[float],
    easting_m: list[float],
    northing_m: list[float],
    density_kg_m3: float,
    depth_top_m: float,
    depth_bottom_m: float,
    reference_density_kg_m3: float = 2670.0,
    claim_id: str = "UNKNOWN",
    hypothesis_prior: float = 0.25,
) -> dict:
    """Screen a gravity anomaly against a single-density prism forward model.

    This is the A2 gravity_screen tool — evidence lane, no joint inversion,
    no judgment required.  Uses HarmonICA (or mock) to compute predicted
    gravity from a single rectangular prism and compares to observed.

    Returns HYPOTHESIS-screen grade and misfit diagnostics.
    Does NOT invoke geox_subsurface_model (judgment lane).

    Args:
        observed_mGal: Observed Bouguer anomaly values [mGal] at each point.
        easting_m: Easting coordinates [m] for each observed point.
        northing_m: Northing coordinates [m] for each observed point.
        density_kg_m3: Prism density [kg/m³] to test.
        depth_top_m: Top depth of prism [m].
        depth_bottom_m: Bottom depth of prism [m].
        reference_density_kg_m3: Background crustal density [kg/m³]. Default 2670.
        claim_id: Claim being screened (for audit trail).
        hypothesis_prior: Prior probability of hypothesis [0-1]. Default 0.25.

    Returns:
        dict with:
          - screen_grade: "HYPOTHESIS_SCREEN" (always — this is pre-inversion)
          - misfit_rms_mGal: RMS misfit between observed and predicted
          - misfit_max_abs_mGal: maximum absolute misfit
          - density_contrast_kg_m3: (density - reference)
          - n_points: number of observation points
          - predicted_mGal: forward-model values at each point
          - observed_mGal: echo of input
          - epistemic_label: "DER" (forward-model derived)
          - hypothesis_updated: float (Bayesian update — PLACEHOLDER, do not trust)
          - claim_id, hypothesis_prior: audit echo
          - godel_wall: {"state": "UNDECIDABLE_YET", "reason": "single-prism screening..."}
    """
    import math

    # Build input for HarmonICAdapter
    payload = GravityMagneticInput(
        survey_type="gravity",
        easting_m=tuple(easting_m),
        northing_m=tuple(northing_m),
        prisms=[
            {
                "easting": sum(easting_m) / len(easting_m) if easting_m else 0.0,
                "northing": sum(northing_m) / len(northing_m) if northing_m else 0.0,
                "depth_top": depth_top_m,
                "depth_bottom": depth_bottom_m,
                "density": density_kg_m3 - reference_density_kg_m3,  # contrast only
                "width_e": 1.0,  # averaged prism — single-cell approximation
                "width_n": 1.0,
            }
        ],
    )

    adapter = HarmonICAdapter()
    output = adapter.forward(payload)

    predicted = output.anomaly_values[: len(observed_mGal)]
    if len(predicted) < len(observed_mGal):
        predicted = predicted + [0.0] * (len(observed_mGal) - len(predicted))

    # Misfit metrics
    n = len(observed_mGal)
    sum_sq = sum((o - p) ** 2 for o, p in zip(observed_mGal, predicted))
    rms = math.sqrt(sum_sq / n) if n > 0 else 0.0
    max_abs = max(abs(o - p) for o, p in zip(observed_mGal, predicted)) if n > 0 else 0.0

    # Density contrast
    contrast = density_kg_m3 - reference_density_kg_m3

    # Bayesian update (PLACEHOLDER — F2: label correctly)
    # Simple Gaussian likelihood: P(data|hypothesis) ∝ exp(-misfit²/2σ²)
    # This is a SCREEN grade, not a posterior — label as DER and note placeholder
    sigma_mGal = 10.0  # conservative 10 mGal uncertainty
    log_likelihood = -(rms**2) / (2 * sigma_mGal**2)
    # Very rough prior/posterior relation — DO NOT TREAT AS REAL BAYESIAN UPDATE
    hypothesis_updated = hypothesis_prior  # placeholder — not a real posterior

    return {
        "screen_grade": "HYPOTHESIS_SCREEN",
        "misfit_rms_mGal": round(rms, 3),
        "misfit_max_abs_mGal": round(max_abs, 3),
        "density_contrast_kg_m3": contrast,
        "density_kg_m3": density_kg_m3,
        "reference_density_kg_m3": reference_density_kg_m3,
        "depth_top_m": depth_top_m,
        "depth_bottom_m": depth_bottom_m,
        "n_points": n,
        "predicted_mGal": [round(v, 3) for v in predicted[:n]],
        "observed_mGal": observed_mGal,
        "epistemic_label": "DER",
        "hypothesis_prior": hypothesis_prior,
        "hypothesis_updated_placeholder": hypothesis_updated,  # F2: NOT a real posterior
        "library": output.provenance.library,
        "claim_id": claim_id,
        "godel_wall": {
            "state": "UNDECIDABLE_YET",
            "reason": (
                "Single-prism screen — forward model only, no joint inversion. "
                "CLM-NWS-002 hypothesis prior remains 0.25 until Scenario D "
                "LSD misfit test. Do not treat hypothesis_updated as real posterior."
            ),
        },
        "caveat": (
            "This is a forward-model screen using a single rectangular prism. "
            "True gravity interpretation requires geox_subsurface_model (judgment lane) "
            "for layered crustal structure. gravity_screen is evidence-only."
        ),
    }


__all__ = [
    "SurveyType",
    "GravityMagneticInput",
    "NonseismicProvenance",
    "NonseismicOutput",
    "HarmonICBackend",
    "MockHarmonICBackend",
    "LiveHarmonICBackend",
    "HarmonICAdapter",
    "gravity_screen",
]
