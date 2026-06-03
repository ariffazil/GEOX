"""
geox_core.avo — Eureka 9: Impedance Contrast IS Fluid (AVO)

E9 is the fluid twin of E8:
  E8: Vp(x,y,z0) -> 2D structure map
  E9: {Vp, Vs, rho}(x,y,z) -> Zoeppritz/Shuey -> AVO class + LMR fluid map

Three primitives (no new MCP tools, F13 honored):

  zoeppritz_rpp   — Bortfeld closed-form, exact at normal incidence
  shuey_avo      — 2-term linearised, valid theta < 30 deg
  lmr_decompose  — Goodway 1997, exact algebra (lambda-rho, mu-rho)

DITEMPA BUKAN DIBERI
"""

from geox_core.avo.avo_forward import (
    zoeppritz_rpp,
    shuey_avo,
    lmr_decompose,
    synth_gather,
    AVOResult,
    LMRResult,
)

__all__ = [
    "zoeppritz_rpp",
    "shuey_avo",
    "lmr_decompose",
    "synth_gather",
    "AVOResult",
    "LMRResult",
]
