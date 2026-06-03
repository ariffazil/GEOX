from scipy.interpolate import interp1d
import numpy as np


def apply_td_anchor(tvd_log: np.ndarray, checkshot_tvd: np.ndarray, checkshot_twt: np.ndarray) -> np.ndarray:
    """
    Forces the depth-based log to map to Two-Way Time (TWT).
    Throws error if extrapolation goes beyond F2 empirical anchors.
    """
    # bounds_error=True ensures we don't hallucinate beyond anchor points
    td_function = interp1d(checkshot_tvd, checkshot_twt, bounds_error=True, fill_value=None)
    return td_function(tvd_log)


def integrate_sonic(dt_log: np.ndarray, dz: float) -> np.ndarray:
    """
    Integrate sonic log (transit time) to get Two-Way Time.
    dt_log in μs/ft or μs/m.
    """
    # Convert transit time to TWT increment per sample
    # TWT = 2 * cumulative_sum(dt * dz)
    # Assuming dt is in s/m if dz is in m, or similar consistent units
    twt = 2 * np.cumsum(dt_log * dz)
    return twt
