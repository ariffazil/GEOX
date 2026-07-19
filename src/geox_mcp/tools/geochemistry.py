"""
geochemistry.py — The Causal Base Layer.
GeoChemState primitives -> RockPhysics13State outputs.
Models smectite-illite transformation and kerogen maturation.
"""
from pydantic import BaseModel


class GeochemRequest(BaseModel):
    initial_smectite_frac: float = 0.5
    T_C: float = 100.0  # Temperature
    time_ma: float = 10.0
    TOC_wt: float = 0.05
    kerogen_type: str = "II"

class GeochemResponse(BaseModel):
    illite_frac: float
    water_released_frac: float
    hydrocarbon_generated: float
    porosity_change: float
    geochem_status: str

async def geox_geochem_kinetics(req: GeochemRequest) -> GeochemResponse:
    # Smectite to illite kinetics (simplified Arrhenius proxy)
    # T > 70C starts conversion. 
    reaction_rate = max(0.0, (req.T_C - 70.0) * req.time_ma * 0.01)
    illite_conversion = min(1.0, reaction_rate)
    illite_frac = req.initial_smectite_frac * illite_conversion
    
    # Smectite dehydration releases bound water (expanding fluid volume)
    water_released_frac = illite_frac * 0.2
    
    # Kerogen maturation (oil window ~60-120C)
    hc_gen = 0.0
    if 60 <= req.T_C <= 120 and req.TOC_wt > 0:
        maturation = (req.T_C - 60) / 60.0
        hc_gen = req.TOC_wt * maturation
        
    # Porosity change (chemical compaction vs dissolution/fluid expansion)
    # Void budget feedback loop
    phi_change = water_released_frac + (hc_gen * 0.1)
    
    return GeochemResponse(
        illite_frac=illite_frac,
        water_released_frac=water_released_frac,
        hydrocarbon_generated=hc_gen,
        porosity_change=phi_change,
        geochem_status="REACTIVE_BASE_LAYER_EVALUATED"
    )
