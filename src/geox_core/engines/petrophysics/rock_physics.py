import numpy as np

def gardner_density(vp: np.ndarray, alpha: float = 310, beta: float = 0.25) -> np.ndarray:
    """
    Predict density from P-wave velocity using Gardner's equation.
    rho = alpha * (Vp)^beta
    
    Default alpha=310, beta=0.25 (standard for mixed lithologies, Vp in m/s, rho in kg/m3).
    If using Vp in ft/s and rho in g/cc, alpha is usually 0.23.
    """
    return alpha * (vp ** beta)

def bellotti_velocity_from_density(rho: np.ndarray) -> np.ndarray:
    """Fallback: Predict Vp from density (empirical)."""
    # Inverse Gardner as a starting point
    # Vp = (rho / 310) ** 4
    return (rho / 310) ** 4

def faust_velocity(depth: np.ndarray, resistivity: np.ndarray, l: float = 2.288, m: float = 1.0/6.0) -> np.ndarray:
    """
    Faust's equation: Vp = l * (Z * Rt)^(1/6)
    Predicts velocity from depth (Z) and resistivity (Rt).
    """
    return l * (depth * resistivity) ** m
