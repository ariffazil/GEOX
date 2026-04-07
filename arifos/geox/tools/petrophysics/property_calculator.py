"""
Property Calculator — Stub for Phase B
DITEMPA BUKAN DIBERI

Full implementation in Phase B: geox_compute_petrophysics tool.
"""

from arifos.geox.schemas.petrophysics.rock_state import RockFluidState

# In-memory store
_state_store: dict[str, RockFluidState] = {}


async def load_rock_state(well_id: str, top: float, base: float) -> RockFluidState | None:
    """Load rock state for interval."""
    key = f"{well_id}:{top}:{base}"
    return _state_store.get(key)


async def store_rock_state(state: RockFluidState) -> None:
    """Store rock state."""
    key = f"{state.well_id}:{state.interval_top_m}:{state.interval_base_m}"
    _state_store[key] = state


class PetrophysicsCalculator:
    """Stub for Phase B implementation."""
    
    def __init__(self, model_id: str, model_params: dict):
        self.model_id = model_id
        self.params = model_params
    
    async def compute(self, well_id: str, top: float, base: float, 
                      propagate_uncertainty: bool = True) -> RockFluidState:
        """Placeholder for petrophysics calculation."""
        raise NotImplementedError("Phase B: Full petrophysics calculation")
