import numpy as np

def calculate_spectral_decay(f_initial: float, twt_s: float, q_factor: float) -> float:
    """
    Calculates the attenuated dominant frequency due to Q-factor.
    F_new = F_initial * exp(-pi * f * t / Q)
    
    Simplified linear approximation for dominant frequency shift:
    f_peak(t) = f_peak(0) / (1 + pi * f_peak(0) * t / Q)
    """
    if q_factor <= 0:
        return f_initial
    
    # Kjaer et al. (1991) approximation for dominant frequency shift
    f_decayed = f_initial / (1 + (np.pi * f_initial * twt_s) / q_factor)
    return max(5.0, f_decayed) # Floor at 5Hz to prevent unphysical dc shift

def get_time_variant_wavelet_params(f_initial: float, time_vector: np.ndarray, q_factor: float) -> np.ndarray:
    """Returns a vector of dominant frequencies shifting with TWT."""
    return np.array([calculate_spectral_decay(f_initial, t, q_factor) for t in time_vector])
