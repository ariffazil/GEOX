import numpy as np

def estimate_thomsen_parameters(vp: np.ndarray, vsh: np.ndarray) -> dict[str, np.ndarray]:
    """
    Empirical estimation of Thomsen parameters (epsilon, delta) based on Vp and Vsh.
    Ref: Simplified regional relationships for shaly sand sequences.
    
    Epsilon (P-wave anisotropy) often scales with shale volume.
    Delta (Wavefront shape) controls near-vertical velocity variation.
    """
    # Epsilon: Zero for clean sand, up to ~0.15-0.2 for pure shale
    # Rough linear approximation: epsilon = 0.2 * Vsh
    epsilon = 0.2 * vsh
    
    # Delta: Often follows epsilon but is typically smaller. 
    # Can be negative in some rocks, but usually 0.05-0.1 for shales.
    # Rough approximation: delta = 0.5 * epsilon
    delta = 0.1 * vsh
    
    return {
        "epsilon": epsilon,
        "delta": delta,
        "gamma": 0.15 * vsh # S-wave anisotropy proxy
    }

def apply_anisotropic_velocity_correction(vp_vertical: np.ndarray, theta_deg: float, epsilon: np.ndarray, delta: np.ndarray) -> np.ndarray:
    """
    Thomsen weak anisotropy approximation for P-wave velocity at angle theta.
    Vp(theta) = Vp_vertical * (1 + delta * sin^2(theta)cos^2(theta) + epsilon * sin^4(theta))
    """
    theta_rad = np.deg2rad(theta_deg)
    sin2 = np.sin(theta_rad)**2
    cos2 = np.cos(theta_rad)**2
    sin4 = np.sin(theta_rad)**4
    
    vp_theta = vp_vertical * (1 + delta * sin2 * cos2 + epsilon * sin4)
    return vp_theta
