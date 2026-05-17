"""
GEOX Legacy Substrate: Stratigraphy & Sequence Logic
Surgically extracted from geox/core/geox_data.py
"""
from typing import Any, List

def assign_layer(depth: float, stratigraphy: List[dict]) -> dict:
    """Matches a depth point to a named geological layer (Strata substrate)."""
    for layer in stratigraphy:
        if layer["top_md"] <= depth < layer["bot_md"]:
            return layer
    return stratigraphy[-1]

def compute_layer_thickness(layer: dict) -> float:
    """Calculates isochore/isopach component."""
    return layer["bot_md"] - layer["top_md"]
