"""
geox_core.avo — Eureka 9: Impedance Contrast IS Fluid (AVO) + Castagna fallback.

E9 is the fluid twin of E8:
  E8: Vp(x,y,z0) -> 2D structure map
  E9: {Vp, Vs, rho}(x,y,z) -> Zoeppritz/Shuey -> AVO class + LMR fluid map

Three AVO primitives (no new MCP tools, F13 honored):

  zoeppritz_rpp   — Bortfeld closed-form, exact at normal incidence
  shuey_avo       — 2-term linearised, valid theta < 30 deg
  lmr_decompose   — Goodway 1997, exact algebra (lambda-rho, mu-rho)

Plus Castagna mudrock line (when DTS absent):

  castagna_mudrock_vp_to_vs(vp)  — Vs ≈ 0.862·Vp − 1.172 (km/s) [Castagna 1985]
  castagna_mudrock_fallback(vp, fluid_zone) — with explicit ACRisk + honest flags

DITEMPA BUKAN DIBERI
"""

from geox_core.avo.avo_forward import (
    AVOResult,
    LMRResult,
    lmr_decompose,
    shuey_avo,
    synth_gather,
    zoeppritz_rpp,
)
from geox_core.avo.castagna import (
    CASTAGNA_HONEST_BAND,
    castagna_mudrock_fallback,
    castagna_mudrock_vp_to_vs,
)

__all__ = [
    # E9 keystone (AVO)
    "zoeppritz_rpp",
    "shuey_avo",
    "lmr_decompose",
    "synth_gather",
    "AVOResult",
    "LMRResult",
    # E9 fallback (Castagna)
    "castagna_mudrock_vp_to_vs",
    "castagna_mudrock_fallback",
    "CASTAGNA_HONEST_BAND",
]
