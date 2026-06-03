"""
geox_core.physics.td_methods — exports
"""

from geox_core.physics.td_methods.base import TDFitResult
from geox_core.physics.td_methods.linear import fit_linear
from geox_core.physics.td_methods.polynomial import fit_polynomial
from geox_core.physics.td_methods.vo_k import fit_vo_k
from geox_core.physics.td_methods.layer_cake import fit_layer_cake


def fit_td(
    method: str,
    checkshot_data: list,
    depth_array,
    **kwargs,
) -> TDFitResult:
    """Unified dispatcher. `method` is one of: linear, polynomial, vo_k, layer_cake.

    Defaults preserve the original behaviour: linear, fail-closed, piecewise.
    """
    if method == "linear":
        return fit_linear(checkshot_data, depth_array)
    if method == "polynomial":
        return fit_polynomial(checkshot_data, depth_array, **kwargs)
    if method in ("vo_k_linear", "vo_k_exponential", "vo_k"):
        mode = kwargs.pop("mode", "linear") if method == "vo_k" else method.split("_")[-1]
        return fit_vo_k(checkshot_data, depth_array, mode=mode, **kwargs)
    if method == "layer_cake":
        return fit_layer_cake(checkshot_data, depth_array, **kwargs)
    raise ValueError(f"Unknown T-D method '{method}'. Supported: linear, polynomial, vo_k, layer_cake.")


__all__ = [
    "TDFitResult",
    "fit_linear",
    "fit_polynomial",
    "fit_vo_k",
    "fit_layer_cake",
    "fit_td",
]
