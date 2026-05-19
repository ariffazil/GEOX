import numpy as np
from scipy import signal

def calculate_acoustic_impedance(rho: np.ndarray, v_p: np.ndarray) -> np.ndarray:
    """F2: Z = rho * v. Validates input arrays match in dimension."""
    if rho.shape != v_p.shape:
        raise ValueError("HOLD: Density and Velocity arrays must match.")
    return rho * v_p

def calculate_reflectivity(z: np.ndarray) -> np.ndarray:
    """F2: R = (Z2 - Z1) / (Z2 + Z1)."""
    r = np.zeros_like(z)
    # R[i] is the reflection coefficient at the interface between layer i and i+1
    r[:-1] = (z[1:] - z[:-1]) / (z[1:] + z[:-1])
    return r

def generate_ricker(freq: float, dt: float, length: float = 0.2) -> np.ndarray:
    """Generates standard zero-phase Ricker wavelet for convolution."""
    t = np.arange(-length/2, (length+dt)/2, dt)
    y = (1.0 - 2.0*(np.pi**2)*(freq**2)*(t**2)) * np.exp(-(np.pi**2)*(freq**2)*(t**2))
    return y

def convolve_synthetic(reflectivity: np.ndarray, wavelet: np.ndarray) -> np.ndarray:
    """Deterministic 1D convolution of reflectivity series and wavelet."""
    # Use 'same' to keep output the same length as reflectivity
    return signal.convolve(reflectivity, wavelet, mode='same')
