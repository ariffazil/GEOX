"""
geox_core.engines.modeling — Grid & Surface Modeling Engines
DITEMPA BUKAN DIBERI

Biharmonic interpolation:
  - biharmonic_adapter: 2D grid inpainting for sparse geological data
"""

from geox_core.engines.modeling.biharmonic_adapter import (
    BiharmonicResult,
    __version__,
    biharmonic_inpaint_grid,
)

__all__ = ["biharmonic_inpaint_grid", "BiharmonicResult", "__version__"]
