"""
geox_core.engines.modeling — Grid & Surface Modeling Engines
DITEMPA BUKAN DIBERI

Biharmonic interpolation:
  - biharmonic_adapter: 2D grid inpainting for sparse geological data
"""

from geox_core.engines.modeling.biharmonic_adapter import (
    biharmonic_inpaint_grid,
    BiharmonicResult,
    __version__,
)

__all__ = ["biharmonic_inpaint_grid", "BiharmonicResult", "__version__"]
__version__ = "2026.06.29"
